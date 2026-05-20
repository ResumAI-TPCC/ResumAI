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

**本 roadmap 的范围**：用户记忆系统（数据持久化层 + 基于记忆的智能功能），并由本 roadmap 给出 **user system 的建表设计**，作为后续 user system 开发的 schema 基线。

**关于 user system**：本 roadmap 不实现完整 Auth/RBAC 业务逻辑，但负责定义 `users` / `user_sessions` 的表结构，确保 memory 模块和 user system 模块的 schema 一致、可对接。`current_user` 依赖注入由 user system 模块提供。

---

## 2. 模块总览

| 模块 | 子项 | 性质 |
|------|------|------|
| **User System 建表** | users / user_sessions schema | 基础设施（本 roadmap 输出，user system team 落地） |
| **Memory 存储底座** | SQL DB + Schema + ORM | 基础设施 |
| **Memory 沉淀** | 简历版本树 / 求职追踪 / 偏好学习 | 数据资产 |
| **Memory 应用** | 跨用户相似度推荐 | 业务功能 |
| **多轮对话**（暂缓） | conversations / messages | 当前未上线 chat 功能，整体延后 |
| **Memory × RAG** | per-user RAG collection（可选） | 智能化扩展 |
| **RAG 性能优化** | batch embed / 单例 + cache | 与 memory 解耦，并行进行 |
| **辅助数据** | 技能图谱 YAML | 独立项 |

---

## 3. SQL Schema 设计

底座是 PostgreSQL（推荐 Supabase 或 AWS RDS，见 §9 infra 决策）。表分为两组：

- **User System 表组**（users / user_sessions）：本 roadmap 出 schema，user system team 落地认证逻辑
- **Memory 业务表组**（resumes / applications / application_events / user_preferences）：本 roadmap 负责落地

```sql
-- =========================================================
-- 【User System 表组】本 roadmap 出 schema，user system 模块落地
-- =========================================================

-- 用户主表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash TEXT,                          -- 邮箱密码登录用；OAuth-only 用户为 NULL
    display_name TEXT,
    avatar_url TEXT,
    auth_provider TEXT NOT NULL,                 -- 'email' / 'google' / 'github' / ...
    auth_provider_id TEXT,                       -- OAuth 提供商返回的 user id；email 注册可为 NULL
    role TEXT NOT NULL DEFAULT 'user',           -- 'user' / 'admin'，RBAC 基础
    status TEXT NOT NULL DEFAULT 'active',       -- 'active' / 'suspended' / 'deleted'
    -- 职业画像（memory 模块写入，user system 读取展示）
    target_role TEXT,
    industry TEXT,
    seniority TEXT,
    career_goal TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ,
    UNIQUE (auth_provider, auth_provider_id)
);
CREATE INDEX idx_users_email ON users(email);

-- 会话 / 刷新令牌
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,            -- 只存 hash，不存明文
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,                      -- 主动撤销时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON user_sessions(refresh_token_hash);

-- =========================================================
-- 【Memory 业务表组】本 roadmap 负责落地
-- =========================================================

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
    status TEXT,           -- 'considering' / 'applied' / 'interview' / 'offer' / 'rejected'
    source TEXT,           -- 'manual' / 'jd_upload' / 'chat_extract'（见 §4 B.2 捕获策略）
    user_confirmed BOOLEAN DEFAULT FALSE,  -- AI 推断默认 false，用户确认后 true
    applied_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, company, role, resume_id)  -- 配合 L2/L3 的 upsert 去重
);
CREATE INDEX idx_apps_user_recent ON applications(user_id, applied_at DESC);

-- 申请事件流：记录状态变迁（manual / jd_upload 写入；L3 chat_extract 待 Phase C 启用后追加）
CREATE TABLE application_events (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,            -- 'considering' / 'applied' / 'interview' / 'offer' / 'rejected'
    source TEXT NOT NULL,                -- 'manual' / 'jd_upload' / 'chat_extract'
    confidence FLOAT,                    -- chat_extract 来源时的 LLM 置信度
    user_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_app_events_app ON application_events(application_id, created_at);

-- 对话历史（Phase C 暂缓，schema 预留，启用时再迁移）
-- CREATE TABLE conversations (...)
-- CREATE TABLE messages (...)
--   含 rag_sources JSONB / suggestion_applied BOOLEAN
--   Phase C 启用时同步给 application_events 加 raw_message_id UUID 字段

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

### Phase A：Memory 存储底座 + User System 建表（1-2 周）

**前置**：infra 团队提供 Postgres 实例（见 §9）。

**任务**：
- **DB instance**：Supabase 或 AWS RDS Postgres 申请 & 接通（详见 §9）
- **User System schema 输出**：把 §3 user system 表组的 DDL 同步给 user system team，对齐字段、命名、约束；约定 `users.id` 为跨模块外键基线
- **Memory schema 迁移**：Alembic 初始化 + Memory 业务表组迁移（resumes / applications / application_events / user_preferences）
- **SQLAlchemy ORM 模型 + Pydantic schema**（含 users 只读模型用于跨表 JOIN）
- **DB session FastAPI dependency**
- **基础 CRUD repository 抽象层**

**与 user system team 的协作边界**：
- 本 roadmap 出 schema、对齐字段；user system team 实现注册/登录/token 刷新等 API
- `current_user` 依赖注入由 user system 模块提供，memory 模块通过 `Depends(current_user)` 拿到 `users.id`
- `users` 表 INSERT/UPDATE 由 user system 模块独占，memory 模块只读 + 写画像列（`target_role` 等）

**完成标志**：可以通过 API 创建 user → 创建 resume → 创建 application，全部持久化到 Postgres。

### Phase B：Memory 沉淀（2-3 周）

**B.1 简历版本树**
- `POST /api/resumes` 创建新版本（可指定 `parent_resume_id`）
- `GET /api/resumes` 返回当前用户所有版本（树形）
- `GET /api/resumes/{id}/lineage` 返回某一版的完整祖先链
- 前端：版本切换 UI + 「这是从哪一版改的」标注

**B.2 求职追踪**

API 基础：
- `POST /api/applications` 记录一次申请（绑定 resume_id + JD）
- `GET /api/applications` 时间序列展示
- `PATCH /api/applications/{id}/status` 更新状态
- 前端：求职看板（按状态分列）

**捕获策略：三层被动捕获优先于手动填表**

用户主动记录"我投了哪家公司"动力低，靠表单数据稀疏不准。采用三层被动捕获组合：

| 层 | 触发来源 | 准确率 | 落地难度 | 阶段 |
|----|---------|--------|---------|------|
| **L1** 手动表单 | 用户主动填 | 高（但稀疏）| ⭐ 简单 | MVP 必备 |
| **L2** JD 上传 → 'considering' | 调 `/api/match` 或 `/api/optimize` 时自动 create | 中（用户上传不等于真投）| ⭐ 简单 | 跟 L1 一起做 |
| **L3** Chat 意图抽取 | Phase C 多轮对话里每条用户消息走 LLM 抽取 | 高（多信号交叉）| ⭐⭐ 中等 | **暂缓**（依赖 Phase C，当前无 chat 功能） |

**L2 实现**（跟 B.2 同期做）：

```python
@router.post("/api/match")
async def match_resume(req, user=Depends(current_user)):
    # ... 原匹配逻辑 ...
    company, role = await extract_company_role_from_jd(req.jd_text)
    await db.execute("""
        INSERT INTO applications (user_id, resume_id, company, role, jd_text, match_score, status, source)
        VALUES (?, ?, ?, ?, ?, ?, 'considering', 'jd_upload')
        ON CONFLICT (user_id, company, role, resume_id) DO NOTHING
    """, ...)
```

加 status `'considering'` 表示"在评估"，真投了升级到 `'applied'`。

**L3 实现**（暂缓 — 待 Phase C chat 上线后接入）：

每条用户聊天消息后台异步走一次轻量 LLM 抽取：

```
Extract job application activity from message. Return JSON:
{ has_activity, company, role, event_type, confidence }
event_type ∈ {considering, applied, interview, offer, rejected}
Only current activity, not past employment.
```

抽到高置信度事件（>0.7）后：
1. `find_or_create` 对应 application 记录
2. 写一条 `application_events`
3. **不直接落库**，前端弹浮窗让用户确认 → 用户确认后才 `user_confirmed = TRUE`

**Schema 依赖**：依赖 §3 中 `applications` 的 `source` / `user_confirmed` 列以及 `application_events` 表，已在 schema 设计阶段定义，B.2 不再需要额外迁移。

**关键工程点**:

1. **永远要求用户确认 AI 推断**：隐私 + 准确度双重考虑，不要默默写库
2. **区分"当前"vs"过去"动作**：用户说"5 年前在阿里"不是当前申请，prompt 里明确要求
3. **去重**：同一个用户多次提到"准备投 Apple SWE"应 update 同一条记录，用 `(user_id, company, role)` 做 dedup
4. **成本控制**：L3 每条消息都过 LLM 抽取会翻倍成本——先用关键词过滤（含"投/申请/面试/offer"才触发），或用 Gemini Flash 而非 Pro
5. **聚合查询**：分析时区分质量等级，关键决策只看 `WHERE user_confirmed = TRUE`

**B.3 偏好学习（基础版）**
- 用户在 `/api/optimize` 等接口上点击建议 Apply/Ignore 时，落一张轻量 `suggestion_feedback` 表（`user_id` / `suggestion_category` / `action` / `created_at`），避免依赖暂缓的 messages 表
- 每周 batch job：聚合每个用户「最常 ignore 的 category」写入 `user_preferences`
- 后续 RAG 检索时用作 negative filter
- Phase C 启用后，`messages.suggestion_applied` 接入同一聚合管线，无需改表结构

**完成标志**：用户登录后看到自己历次的简历和申请记录；AI 建议开始过滤用户明确不喜欢的类别。

### Phase C：多轮对话（**暂缓** — 当前产品无 chat 功能）

启用前提：产品规划确认引入 chat 形态。届时再展开以下设计：
- API: `POST /api/conversations`、`POST /api/conversations/{id}/messages`（SSE 流式）、`GET /api/conversations/{id}`
- LLM 调用流程: 收消息 → `retrieve_with_sources` 注入 RAG 上下文 → 拼 prompt → 流式返回 → 持久化 `messages`（含 `rag_sources`）
- 前端: Chat UI 组件（消息流 + 输入框 + RAG 来源标签）
- 启用同期把 §3 中暂缓的 `conversations` / `messages` 表迁移落库，并给 `application_events` 追加 `raw_message_id` 字段

预估工作量 3-4 周（含前端 Chat UI），届时单独排期。

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
[Infra: Postgres 实例]      [User System team: 落地 users/sessions DDL + current_user]
        │                              │
        └──────────────┬───────────────┘
                       ▼
                 ┌──────────┐
                 │ Phase A  │  存储底座 + user system 建表对齐
                 └─────┬────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      ┌──────┐    ┌──────┐    ┌──────┐
      │ B.1  │    │ B.2  │    │ B.3  │
      │版本树│    │求职  │    │偏好  │
      └──────┘    │L1+L2 │    └──────┘
                  └──────┘
                       │
                       ▼  （需数据积累）
                 ┌──────────┐
                 │ Phase D  │  跨用户推荐
                 └──────────┘

暂缓（依赖未来 chat 功能）：
  ┌─────────────┐
  │ Phase C     │  多轮对话 → 解锁 B.2 L3 chat 抽取
  └─────────────┘

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
| Phase A（存储底座 + user system 建表） | 1-2 周 | 依赖 infra 提供 Postgres 实例；与 user system team 对齐 schema |
| Phase B（数据沉淀） | 2-3 周 | B.1/B.2/B.3 可并行；B.2 仅覆盖 L1+L2 |
| Phase C（多轮对话） | **暂缓** | 当前无 chat 功能，待产品规划再启 |
| Phase D（跨用户推荐） | 1-2 周 | 但要等数据积累到一定量 |
| Phase E（per-user RAG） | 看验证 | 默认延后 |
| 技能图谱 | 2-3 天 | 主要成本在 YAML 内容 |

---

## 7. 跨团队依赖

Phase A kickoff 前必须落实的两项外部协作。

### 7.1 Infra：Postgres 实例

**需要 infra 给开一个虚拟机 / 托管 Postgres 实例**，二选一即可：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **AWS RDS Postgres**（自管实例） | 跟现有云资源同源、网络可控、备份/IAM 走团队既有流程 | 需要 infra 配 VPC / 安全组 / 备份策略，前期开通慢 |
| **Supabase**（托管 Postgres + Auth/Storage 一体） | 开通快、自带 dashboard、行级权限友好；user system 可顺便复用其 Auth | 数据出云、生产规模成本需评估 |

**对 infra 的具体请求**：
- Postgres 15+ 实例（dev / prod 至少各一个）
- 最小规格起步即可（dev: 1 vCPU / 2GB / 20GB；prod: 2 vCPU / 4GB / 50GB），后期按需扩
- 提供连接串（`DATABASE_URL`）并写入 secret manager
- 自动每日备份 + PITR 7 天
- IP 白名单或 VPC peering，禁止公网裸连

**期望产出**：infra 团队回填上述连接信息与凭证位置后，Phase A 立即可启动 Alembic 迁移。

### 7.2 User System team：建表结构对齐

由本 roadmap 提供 §3 的 user system 表组 DDL 作为基线，与 user system 开发协同收敛后落地。

**需要对齐的事项**：
1. **字段集与命名**：以 §3 `users` / `user_sessions` 为基线，确认 `auth_provider` 取值集、`role` 取值集、是否要补 OAuth 多账户绑定表
2. **写入权责**：`users` INSERT/UPDATE 由 user system 模块独占；memory 模块只读 + 写画像列（`target_role` / `industry` / `seniority` / `career_goal`）
3. **`current_user` 依赖契约**：user system 提供 FastAPI dependency，返回值至少包含 `id` / `email` / `role` / `status`
4. **跨模块 FK 基线**：所有业务表的 `user_id` 都 REFERENCES `users(id) ON DELETE CASCADE`，禁止跨库
5. **迁移分工**：user system 表组迁移由 user system team 在同一 Alembic env 下编写，避免两个 migration 历史分叉

**期望产出**：双方在 Phase A 第 1 周内 sign off 一版冻结的 DDL，作为后续业务表迁移的依赖前提。
