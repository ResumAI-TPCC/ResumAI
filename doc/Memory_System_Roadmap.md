# 用户记忆系统 Roadmap

**日期**: 2026-05-18
**负责人**: lin
**配套文档**: [PRD_Phase2_v2.md](PRD_Phase2_v2.md) · [RAG_Optimization_Review.md](RAG_Optimization_Review.md)

---

## 1. 背景与目标

产品当前是 **stateless** 一次性简历分析工具，下一阶段要演进成 **stateful 有用户记忆的产品**：
- 沉淀用户的简历版本、求职轨迹、偏好
- 通过持续记忆形成产品壁垒（用户数据资产越多，迁移成本越高）
- 为多轮对话、跨用户推荐等高级功能打基础

**本 roadmap 的范围**：用户记忆系统（数据持久化层 + 基于记忆的智能功能）。

**外部依赖**：用户认证由 [RA-72](https://tpcc-resumeai.atlassian.net/browse/RA-72)（Auth0 + RBAC）负责，本 roadmap 假设 `current_user` 已通过 FastAPI 依赖注入可用。

---

## 2. 模块总览

| 模块 | 子项 | 性质 |
|------|------|------|
| **Memory 存储底座** | SQL DB + Schema + ORM | 基础设施 |
| **Memory 沉淀** | 简历版本树 / 求职追踪 / 偏好学习 | 数据资产 |
| **Memory 应用** | 多轮对话 / 跨用户相似度推荐 | 业务功能 |
| **Memory × RAG** | per-user RAG collection（可选） | 智能化扩展 |
| **RAG 性能优化** | batch embed / 单例 + cache | 与 memory 解耦，并行进行 |
| **辅助数据** | 技能图谱 YAML | 独立项 |

---

## 3. SQL Schema 设计

底座是 PostgreSQL（推荐 Cloud SQL，与现有 GCP 同源）。五张核心表：

```sql
-- 用户主表（RA-72 负责创建基础列，本 roadmap 扩展画像列）
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ,
    -- 职业画像（与 PRD Sprint 8 重叠，由本 roadmap 落地）
    target_role TEXT,
    industry TEXT,
    seniority TEXT,
    career_goal TEXT
);

-- 简历版本树：核心锁定资产
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    version INT NOT NULL,
    parent_resume_id UUID REFERENCES resumes(id),  -- 从哪一版改来
    gcs_path TEXT,                                  -- PDF
    markdown_content TEXT,                          -- 可检索原文
    tagged_for TEXT,                                -- 用户自定义标签：'Apple SWE 申请专用'
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_resumes_user ON resumes(user_id, created_at DESC);

-- 求职追踪：强锁定数据
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id),
    company TEXT,
    role TEXT,
    jd_text TEXT,
    match_score FLOAT,
    status TEXT,    -- 'applied' / 'interview' / 'offer' / 'rejected'
    applied_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_apps_user_recent ON applications(user_id, applied_at DESC);

-- 对话历史
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,                  -- 'user' / 'assistant'
    content TEXT NOT NULL,
    rag_sources JSONB,                   -- 这次回答引用了哪些 RAG 文档 [{id, title}, ...]
    suggestion_applied BOOLEAN,          -- 用户是否采纳了 AI 建议
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at);

-- AI 学习到的用户偏好（锁定的智能化层）
CREATE TABLE user_preferences (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preference_type TEXT,    -- 'rejected_category' / 'preferred_tone' / 'avoid_keyword' ...
    value JSONB,
    confidence FLOAT,
    last_updated TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, preference_type)
);
```

迁移管理：Alembic（FastAPI 生态标配）。

---

## 4. 各阶段详细方案

### Phase 0：RAG 性能优化（与 memory 并行）

参考 [RAG_Optimization_Review.md](RAG_Optimization_Review.md)。

- **#1 embed_batch 真批量** — ~10 分钟
- **#2 GeminiEmbedder 单例 + LRU cache** — ~1 小时

完成标志：知识库 build 时间下降 10×；analyze + match + optimize 三次 retrieve 共享 cache。

### Phase A：Memory 存储底座（1-2 周）

**前置**：用户认证分支落地，`current_user` 可注入。

**任务**：
- Cloud SQL Postgres instance 开通
- Alembic 初始化 + 五张表迁移
- SQLAlchemy ORM 模型 + Pydantic schema
- DB session FastAPI dependency
- 基础 CRUD repository 抽象层

**完成标志**：可以通过 API 创建 user → 创建 resume → 创建 application，全部持久化到 Postgres。

### Phase B：Memory 沉淀（2-3 周）

**B.1 简历版本树**
- `POST /api/resumes` 创建新版本（可指定 `parent_resume_id`）
- `GET /api/resumes` 返回当前用户所有版本（树形）
- `GET /api/resumes/{id}/lineage` 返回某一版的完整祖先链
- 前端：版本切换 UI + 「这是从哪一版改的」标注

**B.2 求职追踪**
- `POST /api/applications` 记录一次申请（绑定 resume_id + JD）
- `GET /api/applications` 时间序列展示
- `PATCH /api/applications/{id}/status` 更新状态
- 前端：求职看板（按状态分列）

**B.3 偏好学习（基础版）**
- 用户点击建议 Apply/Ignore 时，记录到 `messages.suggestion_applied`
- 每周 batch job：聚合每个用户「最常 ignore 的 category」写入 `user_preferences`
- 后续 RAG 检索时用作 negative filter

**完成标志**：用户登录后看到自己历次的简历和申请记录；AI 建议开始过滤用户明确不喜欢的类别。

### Phase C：多轮对话（3-4 周）

**API 设计**：
- `POST /api/conversations` 开启新对话（绑定 resume_id）
- `POST /api/conversations/{id}/messages` 发消息（流式 SSE 返回）
- `GET /api/conversations/{id}` 查历史

**LLM 调用流程**：
```
1. 收到 user message
2. retrieve_with_sources(user message + 最近 N 条 context)  # 见 RAG review #3
3. 拼 prompt: system + 历史 messages + RAG context + 当前 message
4. 流式调 Gemini，token 一边写一边返回前端
5. 完成后存 messages 表（含 rag_sources）
```

**前端**：Chat UI 组件（消息流 + 输入框 + RAG 来源标签）

**完成标志**：用户可以对自己的简历追问"这段经历怎么改"并得到带知识库依据的回答；对话可被恢复继续。

### Phase D：跨用户相似度推荐（数据积累后）

**前提**：至少有 1000+ 活跃用户、5000+ applications 数据。

**架构**（方案 B：向量 + SQL 混合）：

1. **用户生成 profile vector**：
   ```python
   profile_text = f"Role: {target_role}\nSkills: {skills}\nExperience: {exp_summary}"
   profile_vector = embedder.embed(profile_text)
   # 存到 ChromaDB 新 collection: "users"
   ```

2. **Q1: 相似用户 → 他们的近期 applications**
   ```
   GET /api/users/me/similar-applications
   → ChromaDB 找 top-50 相似用户
   → SQL 聚合这 50 人近 30 天的 applications
   → 返回 top-10 公司/岗位
   ```

3. **Q2: 申请某岗位的人群技能画像**
   ```
   GET /api/jobs/{role}/common-skills
   → SQL 查 applications.role 匹配的用户
   → 聚合 users.skills 出现频率
   ```

**完成标志**：用户能看到「跟你技能相似的人最近在投这些岗位」、「投这个岗位的人都掌握这些技能」两类推荐。

### Phase E：per-user RAG collection（可选，需验证）

仅当 Phase B/C 后用户开始上传"参考简历""喜欢的句式"等私有内容时启用。

- ChromaDB 加 `user_{user_id}` collection
- 检索时合并 common KB（10 篇专家文档）+ user KB（用户私有）
- 用户私有内容**只对自己可见**，不进入跨用户推荐

**先不做**，等用户行为验证有价值再启动。

### 辅助：技能图谱 YAML（独立）

- `backend/data/skill_graph.yaml` 编写 ~500 个核心技能 + 关系
- 启动时加载到内存 dict
- 为 PRD Sprint 5「关键词差距」提供「相关技能推荐」能力

**重要**：**不引入 Neo4j**。500 个节点用内存 dict 处理，毫秒级查询。

---

## 5. 依赖与时序

```
[RA-72 Auth0 + RBAC] ──→ current_user 可用
                         │
                         ▼
                   ┌──────────┐
                   │ Phase A  │  存储底座（SQL + ORM）
                   └─────┬────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        ┌──────┐    ┌──────┐    ┌──────┐
        │ B.1  │    │ B.2  │    │ B.3  │
        │版本树 │    │求职  │    │偏好  │
        └──────┘    └──────┘    └──────┘
            │            │            │
            └────────────┼────────────┘
                         ▼
                   ┌──────────┐
                   │ Phase C  │  多轮对话
                   └─────┬────┘
                         │
                         ▼  （需数据积累）
                   ┌──────────┐
                   │ Phase D  │  跨用户推荐
                   └──────────┘

并行进行（无依赖）：
  ┌─────────────┐  ┌────────────┐
  │ RAG #1 #2   │  │ 技能图谱   │
  │ Phase 0     │  │ YAML       │
  └─────────────┘  └────────────┘
```

---

## 6. 时间预估

| 阶段 | 时间 | 备注 |
|------|------|------|
| Phase 0（RAG 优化） | 半天 | 不阻塞，立即可做 |
| Phase A（存储底座） | 1-2 周 | 等 RA-72 ready |
| Phase B（数据沉淀） | 2-3 周 | B.1/B.2/B.3 可并行 |
| Phase C（多轮对话） | 3-4 周 | 含前端 Chat UI |
| Phase D（跨用户推荐） | 1-2 周 | 但要等数据积累到一定量 |
| Phase E（per-user RAG） | 看验证 | 默认延后 |
| 技能图谱 | 2-3 天 | 主要成本在 YAML 内容 |

---

## 7. 明确不做的事

| 项 | 理由 |
|----|------|
| **Neo4j 图数据库** | 当前 + 可预见规模都用不上；100 万用户 + 真正多跳路径查询前不考虑 |
| **多模态记忆** | 简历是纯文本场景，不适用 |
| **SQLite 作为 RAG 存储** | ChromaDB 已覆盖；SQL DB 用 Postgres 处理产品数据 |
| **自训 embedding 模型** | Gemini embedding 够用，自训不划算 |
| **复杂 chunking 策略** | 当前知识库每篇文档都很短 |
| **Redis 作为 embedding cache 持久层** | YAGNI；进程内 LRU 已经够用，多 worker 共享是以后的事 |

---

## 8. 跟现有 PRD 的关系

| PRD Sprint | 与本 roadmap 的关系 |
|-----------|----------------------|
| Sprint 1 (RAG, 已完成) | 不动 |
| Sprint 2 (RAG 全覆盖 + 技术债) | 不冲突，并行 |
| Sprint 3 (RAG 来源可见) | Phase C 多轮对话依赖此 Sprint 的产物（rag_sources 字段） |
| Sprint 4 (动态可解释性) | 不冲突 |
| Sprint 5 (关键词差距) | 配合本 roadmap 的"技能图谱 YAML"使用 |
| Sprint 6 (建议可操作化) | 与 Phase B.3 偏好学习互补（Apply/Ignore 数据进 user_preferences）|
| Sprint 7 (反馈 + AI 评估) | Phase B/C 产生的数据是评估的输入 |
| Sprint 8 (用户画像 + 埋点) | 与 Phase A 的 `users` 表扩展列重叠，**建议合并到本 roadmap 落地** |

**建议**：PRD Sprint 8 的 user_profile 部分由本 roadmap 的 Phase A 覆盖；PRD Sprint 8 剩下的埋点 + Onboarding 单独保留。

---

## 9. 待定 / 需团队决策

1. **Postgres 部署方案**：Cloud SQL（推荐）vs Supabase vs Firebase Firestore（推荐前者）
2. **ORM 选型**：SQLAlchemy（推荐）vs SQLModel vs Tortoise ORM
3. **对话流式输出协议**：SSE（推荐，简单）vs WebSocket
4. **简历版本树展示形态**：Git 风格的 commit graph vs 简单的时间序列列表
5. **求职追踪是否需要导入第三方数据**（LinkedIn / Greenhouse API）

以上需要在 Phase A kickoff 前明确。
