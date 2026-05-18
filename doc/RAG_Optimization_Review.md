# RAG 模块优化建议（RA-73 review）

**日期**: 2026-05-18
**Reviewer**: lin
**对象**: [backend/app/services/rag/](../backend/app/services/rag/)（RA-73 交付）
**性质**: 建议清单，不修改源代码；RA-73 作者酌情采纳

参考资料：[hello-agents 第八章「记忆与检索」](https://datawhalechina.github.io/hello-agents/#/./chapter8/第八章%20记忆与检索)。本次只挑了**两项最值得优先做的优化**——其余可优化点放在文末"暂不建议改的项"里说明理由。

---

## 一览表

| # | 主题 | 文件 | 优先级 | 与 PRD 关系 |
|---|------|------|--------|-------------|
| 1 | 真正的 batch embedding API（一次打包传递） | `embedder.py:51-53` | 🔴 高 | PRD 未列 |
| 2 | 共享 embedder 单例 + LRU 缓存 | `embedder.py` + `retriever.py:44-45` | 🔴 高 | PRD 未列，Sprint 2 落地后收益最大 |

---

## 1. embed_batch 改成真正的批量调用（🔴 高优先级）

**位置**: [backend/app/services/rag/embedder.py:51-53](../backend/app/services/rag/embedder.py#L51-L53)

**现状**:
```python
def embed_batch(self, texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a list of texts."""
    return [self.embed(t) for t in texts]
```
这是 N 次串行 API 调用，不是批处理。

**建议**: google-genai SDK 的 `embed_content` 原生接受 `contents=list[str]`，一次调用拿到所有 embedding。

```python
def embed_batch(self, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    for t in texts:
        if not t or not t.strip():
            raise ValueError("Cannot embed empty text")
    result = self.client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )
    return [emb.values for emb in result.embeddings]
```

**为什么**: 知识库 build（10 篇文档）从 10 个 API 往返压缩到 1 个，速度 10×，成本同步下降。后续知识库扩到 50+ 篇时差距更明显。

**注意**: 这是 batch 而不是 parallel —— 客户端只发 1 个 HTTP 请求，body 里携带 N 条文本，Gemini 服务端一起处理。**不是 asyncio.gather 那种并发 N 个请求**。Batch 相比并发的优势：

| 方案 | 客户端请求数 | Rate-limit 风险 | 服务端调度效率 |
|------|------|------|------|
| 当前串行 | N | 低 | 低 |
| asyncio.gather 并发 | N（同时发） | 高（可能撞 RPM 限制） | 一般 |
| **batch（推荐）** | **1** | **无** | **高（API 内部 GPU batch）** |

**风险**: 极低。若 SDK 版本不接受 list 入参，测试会立刻失败，可退回 `asyncio.gather` 并行。

---

## 2. 共享 embedder 单例 + LRU 缓存（🔴 高优先级）

**位置**:
- [backend/app/services/rag/embedder.py:32-49](../backend/app/services/rag/embedder.py#L32-L49)（加 cache 和单例工厂）
- [backend/app/services/rag/retriever.py:44-45](../backend/app/services/rag/retriever.py#L44-L45)（改成用单例）

**先解释"embedding 缓存"是什么**:

整个 retrieve 流程拆开是两步：
```
embed(text) → 向量              [Step A，调 Gemini API，慢 + 花钱]
ChromaDB.query(向量) → top-K docs [Step B，本地查询，毫秒级，零成本]
```

这条建议只缓存 Step A：
- **key** = 传给 `embed()` 的原始文本字符串（简历 markdown）
- **value** = Gemini 返回的向量 `list[float]`（768 或 1024 维）

同一份文本第二次进来时，直接从 dict 拿向量，跳过 Gemini 调用。

**现状的两个问题**:
1. 每次调用 `embed(text)` 都打一次 Gemini API，没有任何缓存。
2. `retriever.py` 每次 retrieve 都 `embedder = GeminiEmbedder()` new 一个新实例 —— 这意味着如果只把 cache 挂在实例上，**跨 retrieve 调用根本共享不了**，缓存形同虚设。

所以这条改动必须**两步一起做**：先把 embedder 改成进程级单例，再加 cache。

### 2.1 把 `GeminiEmbedder` 改成模块级单例

在 [embedder.py](../backend/app/services/rag/embedder.py) 末尾加：

```python
_default_embedder: Optional["GeminiEmbedder"] = None

def get_default_embedder() -> "GeminiEmbedder":
    """Return the process-wide GeminiEmbedder singleton.

    Used by retriever and knowledge base builder so the embedding cache
    is shared across all RAG entry points (analyze / match / optimize).
    """
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = GeminiEmbedder()
    return _default_embedder
```

然后改 [retriever.py:44-45](../backend/app/services/rag/retriever.py#L44-L45)：

```python
if embedder is None:
    embedder = get_default_embedder()   # was: GeminiEmbedder()
```

`build_knowledge_base()` 里的 `if embedder is None: embedder = GeminiEmbedder()` 也同样改成 `get_default_embedder()`。

测试通过 `embedder=FakeEmbedder()` 显式注入，不走单例，所以单例改动不会影响测试隔离。

### 2.2 在 `GeminiEmbedder` 内加 LRU 缓存

```python
from collections import OrderedDict
_DEFAULT_CACHE_SIZE = 128

class GeminiEmbedder:
    def __init__(self, api_key=None, enable_cache: bool = True):
        # ... existing init ...
        self._cache: Optional[OrderedDict[str, list[float]]] = (
            OrderedDict() if enable_cache else None
        )
        self._cache_max_size = _DEFAULT_CACHE_SIZE

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        if self._cache is not None and text in self._cache:
            self._cache.move_to_end(text)         # LRU bump
            return self._cache[text]
        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
        )
        vector = result.embeddings[0].values
        if self._cache is not None:
            self._cache[text] = vector
            if len(self._cache) > self._cache_max_size:
                self._cache.popitem(last=False)   # evict oldest
        return vector
```

**为什么**: PRD Sprint 2 把 RAG 接入 analyze + match + optimize 之后，同一份简历 markdown 在一次用户操作里会进 3 次 retrieve 流程。配合单例 embedder，这三次会共享同一个 cache —— 第一次 cache miss 调 API，后两次 cache hit 零开销。

**Cache key 选择**: 直接用 text 字符串。如果担心内存，可以改成 `hashlib.sha256(text.encode()).hexdigest()`。简历 markdown 一般 2–5KB，128 条上限内存压力可忽略（≤1MB）。

**命中条件是"字符串完全相等"**: `"Hello"` 和 `"Hello "` 是两个 key；大小写、空格、换行不同都会 miss。在简历场景里 OK，因为同一份简历在一次 session 里不会变。

**单例的副作用 / 注意点**:
- 进程 fork 时 cache 不会共享（FastAPI + uvicorn workers 各自维护一份），可接受
- 进程重启 cache 清空；如果以后需要持久化（跨 deploy 复用 embedding），可改成 Redis backend，但目前 YAGNI
- 测试用 `reset_default_embedder()` 辅助函数清空单例（参考 `reset_knowledge_base()` 的模式）

### 2.3 没有 2.1 单独做 2.2 会怎样？

会**一点效果都没有**。因为每次 retrieve 都 new 一个新 embedder，cache 永远是空的。所以 #2.1 不是可选项，是 #2.2 的前置条件。

如果嫌 #2.1 改动大，可以退而求其次：把 cache 放成模块级全局 dict（脱离 embedder 实例）。但单例方案更干净，强烈推荐 2.1 + 2.2 一起做。

---

## 暂不建议改的项（理由备查）

下面这些技术点 hello-agents 第八章有提到，本次 review 评估后**不推荐这次动**，理由分别说明，留作未来参考：

| 技术点 | 不建议改的理由 |
|--------|----------------|
| **检索结果暴露 metadata（title/source_id/distance）** | PRD Sprint 3「来源可见」已经规划，让 RA-73 作者/Sprint 3 owner 一起做就行，不抢工作 |
| **HyDE 缩小 query/doc 语义鸿沟** | 收益依赖简历长度，需要 A/B 数据支撑（PRD Sprint 7 才有评估框架），现在做没法量化效果 |
| **候选池 + Rerank（4× top_k）** | 当前 KB 只有 10 篇，top-K=3 几乎不会漏召回；等 KB 扩到 30+ 篇再考虑 |
| **知识库外置成 `data/knowledge/*.md`** | YAGNI——10 篇时硬编码不痛；等"PM/运营要加文档"成为真实诉求再做 |
| **Chunking（结构感知 + Token + overlap）** | 当前文档都很短（200-400 字），不需要分块 |
| **多模态/感知记忆、四层 Agent memory** | 简历是无状态纯文本场景，不适用 |
| **Recall@K / MRR 评估、观测指标** | PRD Sprint 7 已经规划 |

---

## 推荐落地顺序

1. **建议 #1**（10 分钟）：最快见效，纯优化，无前置依赖
2. **建议 #2**（约 1 小时）：等 PRD Sprint 2 接入 match/optimize 时一起做最划算（那时候 cache 才真正派上用场）

两个建议互相独立，可以分别提 PR、分别 review。

---

## 与 Memory_System_Roadmap 的关系

这份 RAG review 跟同目录的 [Memory_System_Roadmap.md](Memory_System_Roadmap.md) 的 **Phase 0（RAG 性能优化）** 在内容上等价 —— roadmap 把这两条建议作为 memory 体系落地前的"清场工作"，而本文件是给 RA-73 作者的**模块级 review**视角。

**建议**：
- 如果想快速落地：直接照本文件做（不依赖 memory roadmap 的其他部分）
- 如果想跟 memory 工作统筹排期：放 roadmap 的 Phase 0 一起做

两个文档不冲突，只是受众和颗粒度不同。
