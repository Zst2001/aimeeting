# AI 智能会议纪要系统 SPEC v1.0

> 文档类型：Technical Specification / 技术规范  
> 产品阶段：V1 / MVP  
> 适用场景：公司内部腾讯会议会后 AI 会议纪要  
> 更新时间：2026-09-02

---

# 1. 文档目的

本文档用于定义 **AI 智能会议纪要系统 V1.0** 的技术实现规范。

本文档重点回答：

- 系统采用什么总体架构；
- 前后端采用什么技术栈；
- 腾讯会议如何接入；
- 外部 LLM 如何接入；
- 为什么 V1 不使用 Agent；
- 数据如何建模；
- API 如何设计；
- 异步任务如何执行；
- 权限如何控制；
- 项目目录如何组织；
- 系统如何部署；
- 如何保证安全、可靠性和可维护性。

本 SPEC 作为后续后端开发、前端开发、数据库设计、API 联调、腾讯会议接入、LLM 接入、测试和部署的统一技术基线。

---

# 2. V1 技术目标

V1 需要实现如下完整链路：

```text
腾讯会议
    ↓
会议基础信息同步
    ↓
主持人在内部 Web 开启 AI 会议纪要
    ↓
会议结束
    ↓
腾讯会议完成云录制 / 转写
    ↓
Webhook 通知系统
    ↓
后台异步获取 Transcript
    ↓
Transcript 标准化
    ↓
LLM Workflow
    ↓
结构化会议纪要
    ↓
保存 AI 原始版本
    ↓
生成当前可编辑版本
    ↓
站内通知
    ↓
用户查看 / 编辑 / 重新生成
```

V1 重点保证：

1. 腾讯会议数据能够稳定同步；
2. Webhook 重复推送不会重复处理；
3. AI 生成流程异步执行；
4. LLM 输出必须结构化；
5. AI 不得补全未明确出现的信息；
6. AI 原始版本必须可追溯；
7. 权限校验必须统一；
8. 系统管理员拥有全部权限；
9. 后续可替换 LLM；
10. 后续可以平滑扩展 RAG、企业知识库等能力。

---

# 3. 技术范围

## 3.1 V1 技术范围

V1 包含：

- Vue3 内部 Web；
- FastAPI 后端；
- 账号密码登录；
- JWT 身份认证；
- MySQL 数据存储；
- Redis；
- Celery 异步任务；
- 腾讯会议企业级自建应用；
- 腾讯会议 REST API；
- 腾讯会议 Webhook；
- 云录制状态同步；
- 录制转写获取；
- Transcript 标准化；
- 百炼平台 Qwen3.7；
- LLM Provider 抽象；
- 长会议分块总结；
- 结构化 JSON 输出；
- Pydantic Schema 校验；
- 会议权限；
- AI 纪要版本管理；
- 人工编辑；
- 重新生成；
- 站内通知；
- 管理后台；
- 操作审计；
- Docker 部署；
- Nginx 反向代理。

## 3.2 V1 不使用

V1 明确不引入：

- Agent；
- Multi-Agent；
- LangGraph Agent；
- LangChain Agent；
- RAG；
- Vector Database；
- Elasticsearch；
- MongoDB；
- Kafka；
- 自建 ASR；
- Whisper；
- vLLM；
- Kubernetes；
- 微服务拆分；
- 实时会议纪要；
- 实时字幕处理；
- 自建音视频会议。

---

# 4. 为什么 V1 不使用 Agent

V1 会议纪要属于 **确定性 LLM Workflow**。

会议纪要生成路径由程序提前定义：

```text
Transcript
    ↓
Normalize
    ↓
Length Check
    ↓
Short / Long 分支
    ↓
LLM Summary
    ↓
Structured Extraction
    ↓
Schema Validation
    ↓
Save
```

LLM 不需要根据当前状态自主决定：

- 下一步做什么；
- 调用哪个 Tool；
- 是否调用外部系统；
- 如何重新规划任务路径。

因此 V1 不需要 Agent。

V1 的设计原则：

> 能通过确定性 Workflow 解决的问题，不使用 Agent 增加额外复杂度。

Agent 后续适合用于：

- 自动创建 Jira / 禅道任务；
- 自动发送企业微信通知；
- 自动查询跨系统数据；
- 跨会议自主检索；
- 根据会议 TODO 自动执行后续动作。

---

# 5. 总体系统架构

## 5.1 架构模式

采用：

> **前后端分离 + 模块化单体后端 + 独立异步 Worker**

不是微服务。

FastAPI API 与 Celery Worker：

- 独立进程；
- 共享同一代码仓库；
- 共享同一数据库；
- 共享同一业务模块。

## 5.2 总体架构

```text
                           ┌─────────────────────┐
                           │      腾讯会议        │
                           │ REST API + Webhook  │
                           └──────────┬──────────┘
                                      │
                               HTTPS / Webhook
                                      │
                                      ▼
┌──────────────────┐          ┌─────────────────────┐
│    Vue3 Web      │  HTTPS   │     FastAPI API     │
│                  │◄────────►│                     │
│  公司内部会议系统 │          │ Auth / Meeting /    │
│                  │          │ Minutes / Admin     │
└──────────────────┘          └─────────┬───────────┘
                                       │
                         ┌─────────────┼──────────────┐
                         ▼             ▼              ▼
                      MySQL          Redis        Tencent
                                                   Adapter
                                       │
                                       ▼
                                 Celery Worker
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
              Fetch Transcript     Generate AI       Notification
                                       │
                                       ▼
                                LLM Provider Layer
                                       │
                                       ▼
                              百炼平台 Qwen3.7
```

---

# 6. 技术选型

| 层级 | 技术 |
|---|---|
| Frontend | Vue 3 |
| Frontend Language | TypeScript |
| Build Tool | Vite |
| UI | Element Plus |
| State Management | Pinia |
| HTTP Client | Axios |
| Backend | FastAPI |
| Backend Language | Python 3.12 |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| Migration | Alembic |
| Database | MySQL 8 |
| Cache / Broker | Redis 7 |
| Async Task | Celery |
| HTTP Client | HTTPX |
| Authentication | Username/Password + JWT |
| Password Hash | Argon2id / bcrypt |
| Tencent Meeting | REST API + Webhook |
| LLM | 百炼平台 Qwen3.7 |
| LLM Abstraction | Provider Pattern |
| Reverse Proxy | Nginx |
| Deployment | Docker / Docker Compose |
| Backend Test | Pytest |
| Frontend Test | Vitest |
| API Docs | OpenAPI / Swagger |

---

# 7. 部署拓扑

V1 面向中小公司内部使用，会议量级不大，不设计复杂分布式架构。

推荐 Docker Compose：

```text
ai-meeting-minutes
│
├── nginx
├── frontend
├── backend-api
├── backend-worker
├── redis
└── mysql
```

部署拓扑：

```text
                Nginx
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
     Vue Web             FastAPI
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
             MySQL        Redis      Tencent API
                            │
                            ▼
                      Celery Worker
                            │
                            ▼
                        LLM API
```

---

# 8. 用户认证设计

## 8.1 登录模式

公司没有现成 SSO。

V1 使用：

> 用户名 / 密码 + JWT

## 8.2 Token 类型

建议：

```text
Access Token
Refresh Token
```

### Access Token

建议有效期：

```text
30 分钟
```

### Refresh Token

建议有效期：

```text
7 天
```

实际时间通过环境变量配置。

## 8.3 密码存储

数据库不得保存明文密码。

优先使用：

- Argon2id；
- 或 bcrypt。

## 8.4 JWT Payload

示例：

```json
{
  "sub": "123",
  "username": "zhangsan",
  "role": "USER",
  "type": "access",
  "iat": 1788307200,
  "exp": 1788309000
}
```

## 8.5 用户角色

```text
USER
ADMIN
```

ADMIN 拥有系统全部权限。

---

# 9. 权限模型

## 9.1 权限原则

访问会议必须满足以下条件之一：

```text
ADMIN
OR
会议主持人
OR
会议参会者
OR
meeting_permissions 中存在 VIEW 授权
```

## 9.2 操作权限

| 操作 | 主持人 | 参会者 | 被授权用户 | ADMIN |
|---|---:|---:|---:|---:|
| 查看会议 | √ | √ | √ | √ |
| 查看纪要 | √ | √ | √ | √ |
| 查看 Transcript | √ | √ | √ | √ |
| 开启 AI 纪要 | √ | × | × | √ |
| 编辑纪要 | √ | × | × | √ |
| 重新生成 | √ | × | × | √ |
| 分享会议 | √ | × | × | √ |
| 撤销授权 | √ | × | × | √ |
| 查看 AI 原始版本 | √ | × | × | √ |
| 查看所有会议 | × | × | × | √ |
| 系统管理 | × | × | × | √ |

## 9.3 PermissionService

权限逻辑禁止散落在 API Controller 中。

统一实现：

```text
PermissionService

can_view_meeting()
can_edit_minutes()
can_regenerate_minutes()
can_manage_permissions()
can_toggle_ai_minutes()
```

ADMIN 检查优先：

```text
if role == ADMIN:
    ALLOW
```

---

# 10. 腾讯会议接入设计

## 10.1 应用类型

建议采用：

> 腾讯会议企业级自建应用

用于获取企业内部通过腾讯会议创建的会议数据。

## 10.2 接入方式

使用：

```text
REST API
+
Webhook
```

不使用腾讯会议音视频 SDK。

## 10.3 TencentMeetingClient

所有腾讯会议接口统一通过 Adapter 封装。

```text
TencentMeetingClient
│
├── get_meeting()
├── list_meetings()
├── get_participants()
├── get_recordings()
├── get_recording_detail()
├── get_transcript()
└── verify_webhook()
```

业务层不得直接调用腾讯会议 HTTP URL。

## 10.4 模块结构

```text
integrations/tencent_meeting/
│
├── client.py
├── auth.py
├── webhook.py
├── schemas.py
├── mapper.py
└── exceptions.py
```

## 10.5 腾讯数据内部标准化

腾讯返回的数据必须映射为内部 Domain Model。

例如：

```json
{
  "provider_segment_id": "p1001",
  "speaker_external_id": "user_10001",
  "speaker_name": "张三",
  "start_ms": 183000,
  "end_ms": 194000,
  "text": "推荐服务目前 P95 延迟还有 800ms。"
}
```

AI 层不得依赖腾讯原始 JSON。

---

# 11. Webhook 设计

## 11.1 Webhook Endpoint

```http
POST /api/v1/integrations/tencent-meeting/webhook
```

## 11.2 Webhook 原则

Webhook 请求收到后：

```text
Verify Signature
    ↓
Check Idempotency
    ↓
Save Event
    ↓
Create Async Task
    ↓
Return 200
```

不得在 Webhook HTTP 请求中：

- 等待 Transcript；
- 调用 LLM；
- 生成完整会议纪要。

## 11.3 幂等

`webhook_events` 需要唯一业务标识。

推荐：

```text
provider + trace_id
```

建立 UNIQUE INDEX。

## 11.4 事件处理

V1 关注的事件类型至少包括：

```text
会议结束相关事件
录制完成相关事件
转写完成相关事件
```

具体事件名称以实际腾讯会议开放平台配置为准。

## 11.5 补偿机制

Webhook 仅作为触发机制。

Worker 收到任务后必须再次查询腾讯会议实际状态。

流程：

```text
Webhook
    ↓
Worker
    ↓
Query Recording
    ↓
Query Transcript
    ↓
Ready?
 ┌──┴──┐
No    Yes
│      │
Retry  Continue
```

---

# 12. 核心业务状态机

## 12.1 Meeting Status

```text
SCHEDULED
IN_PROGRESS
ENDED
```

## 12.2 Minutes Status

```text
DISABLED
WAITING_MEETING_END
WAITING_RECORDING
WAITING_TRANSCRIPT
AI_PROCESSING
READY
FAILED
```

## 12.3 状态转换

```text
DISABLED
   │ enable
   ▼
WAITING_MEETING_END
   │ meeting ended
   ▼
WAITING_RECORDING
   │ recording ready
   ▼
WAITING_TRANSCRIPT
   │ transcript ready
   ▼
AI_PROCESSING
   │ success
   ▼
READY
```

异常：

```text
AI_PROCESSING
    ↓
FAILED
```

重新生成：

```text
READY / FAILED
      ↓
AI_PROCESSING
      ↓
READY / FAILED
```

---

# 13. 异步任务架构

## 13.1 Celery

使用：

```text
Celery + Redis
```

Redis 同时作为：

- Broker；
- 临时任务状态；
- 分布式锁；
- 幂等辅助。

## 13.2 Task Types

至少包含：

```text
SYNC_MEETING
FETCH_RECORDING
FETCH_TRANSCRIPT
GENERATE_MINUTES
REGENERATE_MINUTES
SEND_NOTIFICATION
```

## 13.3 任务链

典型任务链：

```text
Webhook
    ↓
FETCH_RECORDING
    ↓
FETCH_TRANSCRIPT
    ↓
GENERATE_MINUTES
    ↓
SEND_NOTIFICATION
```

## 13.4 重试策略

### Tencent API

```text
max_retries = 5
```

建议指数退避：

```text
1m → 5m → 15m → 30m → 60m
```

### LLM

```text
max_retries = 3
```

适用于：

- 网络异常；
- API 超时；
- 5xx；
- JSON 输出格式异常。

## 13.5 业务幂等

生成会议纪要任务需使用业务锁：

```text
minutes_generation:{meeting_id}
```

同一会议同一时刻只允许一个生成任务执行。

---

# 14. LLM 架构

## 14.1 当前模型

V1 默认：

```text
Provider: Bailian
Model: Qwen3.7
```

具体模型名通过配置设置，例如：

```env
LLM_PROVIDER=bailian
LLM_MODEL=qwen3.7
```

## 14.2 Provider Pattern

业务代码不得直接依赖百炼 SDK。

定义：

```python
class LLMProvider:
    async def generate_minutes(...):
        ...
```

实现可扩展为：

```text
LLMProvider
│
├── BailianProvider
├── OpenAICompatibleProvider
├── DeepSeekProvider
└── TencentHunyuanProvider
```

V1 只实现当前需要的 Provider。

## 14.3 模块结构

```text
integrations/llm/
│
├── base.py
├── factory.py
├── bailian.py
├── schemas.py
├── parser.py
├── prompts/
│   ├── minutes_short_v1.txt
│   ├── chunk_summary_v1.txt
│   └── global_summary_v1.txt
└── exceptions.py
```

---

# 15. LLM Workflow

## 15.1 总流程

短会议：

```text
Raw Transcript
      ↓
Normalize
      ↓
Token Estimate
      ↓
Single LLM Call
      ↓
Structured Output
```

长会议：

```text
Raw Transcript
      ↓
Normalize
      ↓
Chunk
      ↓
Chunk Summary × N
      ↓
Global Summary
      ↓
Structured Output
```

## 15.2 Chunk 原则

V1 可基于：

- 估算 Token 数；
- 最大字符数；
- Transcript Segment 边界

进行分块。

禁止从一个发言 segment 中间任意截断，优先在 segment 边界切分。

## 15.3 不使用 Agent

所有路径均由应用程序控制。

模型不进行：

- Tool Selection；
- Autonomous Planning；
- Autonomous Retry Strategy；
- External Action。

---

# 16. Transcript 标准化

## 16.1 标准结构

```json
{
  "sequence_no": 102,
  "speaker_user_id": 12,
  "speaker_external_id": "tm_u_1001",
  "speaker_name": "张三",
  "start_ms": 120300,
  "end_ms": 131100,
  "text": "我觉得项目需要延期两天。"
}
```

## 16.2 Normalize

标准化仅处理：

- 空白字符；
- 无意义重复空格；
- 段落格式；
- Speaker 统一；
- 顺序排序。

V1 不主动修改原始语义。

---

# 17. LLM Structured Output

## 17.1 Schema

推荐模型输出：

```json
{
  "summary": "本次会议主要讨论……",
  "topics": [
    {
      "title": "接口性能",
      "summary": "当前 P95 延迟约为 800ms。"
    }
  ],
  "decisions": [
    {
      "content": "上线日期调整为 9 月 10 日"
    }
  ],
  "action_items": [
    {
      "task": "优化推荐接口",
      "owner": "张三",
      "deadline": "2026-09-05"
    }
  ]
}
```

## 17.2 Pydantic Model

```python
class Topic(BaseModel):
    title: str
    summary: str

class Decision(BaseModel):
    content: str

class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: date | None = None

class MeetingMinutesOutput(BaseModel):
    summary: str
    topics: list[Topic]
    decisions: list[Decision]
    action_items: list[ActionItem]
```

## 17.3 缺失信息规则

如果会议没有明确负责人：

```json
{
  "owner": null
}
```

如果没有明确截止时间：

```json
{
  "deadline": null
}
```

禁止 LLM 推测。

---

# 18. LLM 输出校验

模型结果进入数据库之前：

```text
LLM Response
    ↓
Parse JSON
    ↓
Pydantic Validate
    ↓
Business Validate
    ↓
Save
```

## 18.1 JSON Parse Failed

执行 Repair / Retry。

## 18.2 Schema Failed

最多重试指定次数。

达到最大次数：

```text
minutes_status = FAILED
```

## 18.3 Business Validation

最低校验：

- summary 不为空；
- topics 类型正确；
- decisions 类型正确；
- action_items 类型正确；
- deadline 必须是合法日期或 null。

---

# 19. 数据模型总览

V1 核心表：

```text
users

meetings
meeting_participants
meeting_recordings
transcript_segments

meeting_minutes
minute_versions
minute_action_items

meeting_permissions

notifications

webhook_events
async_tasks
audit_logs
```

---

# 20. users

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 用户 ID |
| username | VARCHAR(64) UNIQUE | 登录名 |
| password_hash | VARCHAR(255) | 密码 Hash |
| employee_no | VARCHAR(64) NULL | 工号 |
| display_name | VARCHAR(128) | 显示姓名 |
| email | VARCHAR(255) NULL | 邮箱 |
| tencent_userid | VARCHAR(128) NULL | 腾讯会议用户标识 |
| role | VARCHAR(16) | USER / ADMIN |
| status | VARCHAR(16) | ACTIVE / DISABLED |
| last_login_at | DATETIME NULL | 最后登录 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

索引：

```text
UNIQUE(username)
INDEX(tencent_userid)
```

---

# 21. meetings

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 内部会议 ID |
| tencent_meeting_id | VARCHAR(128) UNIQUE | 腾讯会议 ID |
| meeting_code | VARCHAR(64) NULL | 会议号 |
| subject | VARCHAR(255) | 会议名称 |
| creator_user_id | BIGINT NULL FK | 内部主持人 |
| tencent_creator_userid | VARCHAR(128) NULL | 腾讯主持人 ID |
| start_time | DATETIME NULL | 开始时间 |
| end_time | DATETIME NULL | 结束时间 |
| meeting_status | VARCHAR(32) | 会议状态 |
| ai_minutes_enabled | BOOLEAN | 是否开启 |
| ai_minutes_enabled_by | BIGINT NULL | 开启人 |
| ai_minutes_enabled_at | DATETIME NULL | 开启时间 |
| minutes_status | VARCHAR(32) | AI 状态 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

索引：

```text
UNIQUE(tencent_meeting_id)
INDEX(creator_user_id)
INDEX(start_time)
INDEX(minutes_status)
```

---

# 22. meeting_participants

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_id | BIGINT FK | 会议 |
| user_id | BIGINT NULL FK | 内部用户 |
| tencent_userid | VARCHAR(128) NULL | 腾讯用户 |
| display_name | VARCHAR(128) | 姓名 |
| is_internal | BOOLEAN | 是否内部员工 |
| join_time | DATETIME NULL | 进入时间 |
| leave_time | DATETIME NULL | 离开时间 |
| created_at | DATETIME | 创建时间 |

`user_id` 允许为空，用于外部客户、供应商、腾讯会议访客。

---

# 23. meeting_recordings

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_id | BIGINT FK | 会议 |
| record_file_id | VARCHAR(128) | 腾讯录制文件 ID |
| recording_status | VARCHAR(32) | 录制状态 |
| transcript_status | VARCHAR(32) | 转写状态 |
| record_start_time | DATETIME NULL | 开始 |
| record_end_time | DATETIME NULL | 结束 |
| created_at | DATETIME | 创建 |
| updated_at | DATETIME | 更新 |

约束：

```text
UNIQUE(meeting_id, record_file_id)
```

---

# 24. transcript_segments

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_id | BIGINT FK | 会议 |
| recording_id | BIGINT FK | 录制 |
| provider | VARCHAR(32) | tencent_meeting |
| provider_segment_id | VARCHAR(128) NULL | 外部段落 ID |
| speaker_user_id | BIGINT NULL | 内部用户 |
| speaker_tencent_userid | VARCHAR(128) NULL | 腾讯用户 |
| speaker_name | VARCHAR(128) | 发言人 |
| start_ms | BIGINT | 开始毫秒 |
| end_ms | BIGINT | 结束毫秒 |
| text | TEXT | 文本 |
| sequence_no | INT | 顺序 |
| created_at | DATETIME | 创建 |

索引：

```text
INDEX(meeting_id, sequence_no)
INDEX(speaker_user_id)
```

---

# 25. meeting_minutes

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_id | BIGINT UNIQUE FK | 会议 |
| current_version_id | BIGINT NULL | 当前版本 |
| status | VARCHAR(32) | 状态 |
| created_at | DATETIME | 创建 |
| updated_at | DATETIME | 更新 |

---

# 26. minute_versions

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_minutes_id | BIGINT FK | 纪要 |
| version_no | INT | 版本号 |
| version_type | VARCHAR(16) | AI / MANUAL |
| base_version_id | BIGINT NULL | 基础版本 |
| content_json | JSON | 结构化纪要 |
| model_provider | VARCHAR(64) NULL | Provider |
| model_name | VARCHAR(128) NULL | 模型 |
| prompt_version | VARCHAR(64) NULL | Prompt 版本 |
| created_by | BIGINT NULL | 操作用户 |
| created_at | DATETIME | 创建 |

约束：

```text
UNIQUE(meeting_minutes_id, version_no)
```

版本示例：

```text
V1 AI
V2 MANUAL ← V1
V3 AI
V4 MANUAL ← V3
```

---

# 27. minute_action_items

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| minute_version_id | BIGINT FK | 版本 |
| task | TEXT | 任务 |
| owner_user_id | BIGINT NULL | 内部负责人 |
| owner_name | VARCHAR(128) NULL | 原始负责人文本 |
| deadline | DATE NULL | 截止日期 |
| status | VARCHAR(16) | PENDING 等 |
| created_at | DATETIME | 创建 |

即使 `content_json` 中保留 action_items，仍建议将 TODO 单独落表，便于后续查询与扩展。

---

# 28. meeting_permissions

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| meeting_id | BIGINT FK | 会议 |
| user_id | BIGINT FK | 被授权用户 |
| permission | VARCHAR(16) | VIEW |
| granted_by | BIGINT FK | 授权人 |
| created_at | DATETIME | 创建 |

约束：

```text
UNIQUE(meeting_id, user_id, permission)
```

---

# 29. webhook_events

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| provider | VARCHAR(32) | tencent_meeting |
| event_type | VARCHAR(128) | 事件类型 |
| trace_id | VARCHAR(255) | 幂等 ID |
| payload_json | JSON | 原始 Payload |
| process_status | VARCHAR(32) | 状态 |
| received_at | DATETIME | 接收时间 |
| processed_at | DATETIME NULL | 处理完成 |
| error_message | TEXT NULL | 错误 |

约束：

```text
UNIQUE(provider, trace_id)
```

---

# 30. async_tasks

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| task_type | VARCHAR(64) | 类型 |
| business_id | VARCHAR(128) | 业务 ID |
| celery_task_id | VARCHAR(255) NULL | Celery ID |
| status | VARCHAR(32) | 状态 |
| retry_count | INT | 重试次数 |
| error_message | TEXT NULL | 错误 |
| created_at | DATETIME | 创建 |
| started_at | DATETIME NULL | 开始 |
| finished_at | DATETIME NULL | 完成 |

---

# 31. notifications

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| user_id | BIGINT FK | 接收人 |
| type | VARCHAR(64) | 类型 |
| title | VARCHAR(255) | 标题 |
| content | TEXT | 内容 |
| meeting_id | BIGINT NULL FK | 会议 |
| is_read | BOOLEAN | 是否已读 |
| created_at | DATETIME | 创建 |
| read_at | DATETIME NULL | 已读时间 |

---

# 32. audit_logs

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | ID |
| user_id | BIGINT FK | 操作人 |
| action | VARCHAR(64) | 操作 |
| resource_type | VARCHAR(64) | 资源类型 |
| resource_id | VARCHAR(128) | 资源 ID |
| before_json | JSON NULL | 修改前 |
| after_json | JSON NULL | 修改后 |
| ip_address | VARCHAR(64) NULL | IP |
| created_at | DATETIME | 时间 |

重点操作：

```text
LOGIN
EDIT_MINUTES
REGENERATE_MINUTES
GRANT_PERMISSION
REVOKE_PERMISSION
TOGGLE_AI_MINUTES
ADMIN_VIEW_MEETING
ADMIN_UPDATE_LLM_CONFIG
```

由于 ADMIN 拥有全部权限，管理员访问敏感会议建议记录：

```text
ADMIN_VIEW_MEETING
```

---

# 33. ER 关系

```text
users
  │
  ├──────────────────────────────┐
  │                              │
  ▼                              ▼
meetings                   meeting_permissions
  │
  ├── meeting_participants
  │
  ├── meeting_recordings
  │       │
  │       ▼
  │  transcript_segments
  │
  └── meeting_minutes
           │
           ▼
      minute_versions
           │
           ▼
    minute_action_items

users
  ├── notifications
  └── audit_logs

webhook_events
async_tasks
```

---

# 34. REST API 设计规范

统一前缀：

```text
/api/v1
```

## 34.1 Success Response

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx"
}
```

## 34.2 Error Response

```json
{
  "code": 40001,
  "message": "invalid request",
  "data": null,
  "request_id": "req_xxx"
}
```

同时使用标准 HTTP Status Code。

---

# 35. Auth API

## POST /api/v1/auth/login

Request：

```json
{
  "username": "zhangsan",
  "password": "******"
}
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "token_type": "bearer"
  }
}
```

## POST /api/v1/auth/refresh

用于刷新 Access Token。

## POST /api/v1/auth/logout

注销当前会话。

## GET /api/v1/me

获取当前登录用户。

---

# 36. Meeting API

## GET /api/v1/meetings

Query：

```text
scope=hosted
scope=joined
scope=shared

minutes_status=READY

page=1
page_size=20
```

ADMIN 可：

```text
scope=all
```

## GET /api/v1/meetings/{meeting_id}

返回：

- 会议基本信息；
- 主持人；
- 参会者；
- AI 状态；
- 当前用户权限。

## PATCH /api/v1/meetings/{meeting_id}/ai-minutes

Request：

```json
{
  "enabled": true
}
```

权限：

```text
Host / ADMIN
```

---

# 37. Transcript API

## GET /api/v1/meetings/{meeting_id}/transcript

Query：

```text
page=1
page_size=100
```

Response：

```json
{
  "items": [
    {
      "id": 1,
      "speaker_name": "张三",
      "start_ms": 183000,
      "end_ms": 194000,
      "text": "……"
    }
  ],
  "page": 1,
  "page_size": 100,
  "total": 450
}
```

必须分页，避免一次返回数小时会议全部内容。

---

# 38. Minutes API

## GET /api/v1/meetings/{meeting_id}/minutes

返回当前展示版本。

## PUT /api/v1/meetings/{meeting_id}/minutes

权限：

```text
Host / ADMIN
```

Request：

```json
{
  "summary": "……",
  "topics": [],
  "decisions": [],
  "action_items": []
}
```

操作后：

```text
创建新的 MANUAL Version
```

不得修改历史版本。

## POST /api/v1/meetings/{meeting_id}/minutes/regenerate

权限：

```text
Host / ADMIN
```

返回：

```text
202 Accepted
```

生成任务进入 Celery。

## GET /api/v1/meetings/{meeting_id}/minutes/versions

权限：

```text
Host / ADMIN
```

## GET /api/v1/meetings/{meeting_id}/minutes/versions/{version_id}

权限：

```text
Host / ADMIN
```

---

# 39. Permission API

## GET /api/v1/meetings/{meeting_id}/permissions

权限：

```text
Host / ADMIN
```

## POST /api/v1/meetings/{meeting_id}/permissions

Request：

```json
{
  "user_id": 123,
  "permission": "VIEW"
}
```

权限：

```text
Host / ADMIN
```

## DELETE /api/v1/meetings/{meeting_id}/permissions/{user_id}

权限：

```text
Host / ADMIN
```

---

# 40. Notification API

## GET /api/v1/notifications

支持分页。

## PATCH /api/v1/notifications/{notification_id}/read

标记已读。

## POST /api/v1/notifications/read-all

全部标记已读。

---

# 41. Admin API

## GET /api/v1/admin/meetings

查看全部会议。

## GET /api/v1/admin/tasks

查看异步任务。

## POST /api/v1/admin/tasks/{task_id}/retry

重试失败任务。

## GET /api/v1/admin/audit-logs

查看审计日志。

## GET /api/v1/admin/users

用户管理。

## POST /api/v1/admin/users

创建内部用户。

## PATCH /api/v1/admin/users/{user_id}

修改用户。

## GET /api/v1/admin/llm-config

查看 LLM 配置。

## PUT /api/v1/admin/llm-config

修改 LLM 业务配置。

API Key 不允许明文返回前端。

---

# 42. Error Code 规范

建议：

```text
100xx Authentication
200xx Permission
300xx Meeting
400xx Transcript
500xx Minutes / LLM
600xx Tencent Meeting
700xx Async Task
800xx System
```

示例：

| Code | 含义 |
|---|---|
| 10001 | 用户名或密码错误 |
| 10002 | Token 无效 |
| 10003 | Token 已过期 |
| 20001 | 无会议访问权限 |
| 20002 | 无纪要编辑权限 |
| 30001 | 会议不存在 |
| 30002 | AI 纪要未开启 |
| 40001 | Transcript 尚未生成 |
| 40002 | Transcript 为空 |
| 50001 | LLM 调用失败 |
| 50002 | LLM 输出格式非法 |
| 50003 | AI 纪要生成中 |
| 60001 | 腾讯会议 API 调用失败 |
| 60002 | 腾讯会议鉴权失败 |
| 70001 | 异步任务执行失败 |
| 80001 | 系统内部错误 |

---

# 43. Backend 模块划分

```text
Auth
User
Meeting
Transcript
Minutes
Permission
Notification
Admin

TencentIntegration
LLMIntegration

Task
Audit
```

依赖关系：

```text
TencentIntegration
       ↓
Meeting
       ↓
Transcript
       ↓
Minutes
       ↓
LLMIntegration

Meeting
  ├── Permission
  └── Notification

Sensitive Operations
       ↓
Audit
```

---

# 44. Backend 目录结构

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── meetings.py
│   │           ├── minutes.py
│   │           ├── transcripts.py
│   │           ├── permissions.py
│   │           ├── notifications.py
│   │           ├── webhooks.py
│   │           └── admin.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── error_codes.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── user.py
│   │       ├── meeting.py
│   │       ├── participant.py
│   │       ├── recording.py
│   │       ├── transcript.py
│   │       ├── minutes.py
│   │       ├── permission.py
│   │       ├── notification.py
│   │       ├── webhook_event.py
│   │       ├── async_task.py
│   │       └── audit_log.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── meeting.py
│   │   ├── transcript.py
│   │   ├── minutes.py
│   │   ├── permission.py
│   │   └── notification.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── meeting_repository.py
│   │   ├── transcript_repository.py
│   │   ├── minutes_repository.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── meeting_service.py
│   │   ├── transcript_service.py
│   │   ├── minutes_service.py
│   │   ├── permission_service.py
│   │   ├── notification_service.py
│   │   └── audit_service.py
│   │
│   ├── integrations/
│   │   ├── tencent_meeting/
│   │   │   ├── client.py
│   │   │   ├── auth.py
│   │   │   ├── webhook.py
│   │   │   ├── schemas.py
│   │   │   ├── mapper.py
│   │   │   └── exceptions.py
│   │   │
│   │   └── llm/
│   │       ├── base.py
│   │       ├── factory.py
│   │       ├── bailian.py
│   │       ├── schemas.py
│   │       ├── parser.py
│   │       ├── exceptions.py
│   │       └── prompts/
│   │           ├── minutes_short_v1.txt
│   │           ├── chunk_summary_v1.txt
│   │           └── global_summary_v1.txt
│   │
│   ├── tasks/
│   │   ├── celery_app.py
│   │   ├── meeting_tasks.py
│   │   ├── transcript_tasks.py
│   │   ├── minutes_tasks.py
│   │   └── notification_tasks.py
│   │
│   └── utils/
│       ├── datetime.py
│       ├── pagination.py
│       └── idempotency.py
│
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

---

# 45. Frontend 目录结构

```text
frontend/
│
├── src/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── meeting.ts
│   │   ├── minutes.ts
│   │   ├── permission.ts
│   │   ├── notification.ts
│   │   └── admin.ts
│   │
│   ├── components/
│   │   ├── meeting/
│   │   ├── minutes/
│   │   ├── transcript/
│   │   └── common/
│   │
│   ├── views/
│   │   ├── auth/
│   │   │   └── LoginView.vue
│   │   ├── meetings/
│   │   │   ├── MeetingListView.vue
│   │   │   └── MeetingDetailView.vue
│   │   ├── notifications/
│   │   │   └── NotificationView.vue
│   │   └── admin/
│   │       ├── AdminMeetingView.vue
│   │       ├── AdminTaskView.vue
│   │       ├── AdminUserView.vue
│   │       └── AdminAuditView.vue
│   │
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── meeting.ts
│   │   └── notification.ts
│   │
│   ├── router/
│   ├── types/
│   ├── utils/
│   ├── App.vue
│   └── main.ts
│
├── package.json
├── vite.config.ts
└── Dockerfile
```

---

# 46. Repository 总目录

```text
ai-meeting-minutes/
│
├── backend/
├── frontend/
├── docs/
├── deploy/
├── scripts/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 47. docs 目录

推荐：

```text
docs/
│
├── PRD.md
├── SPEC.md
├── API.md
├── DATABASE.md
├── TENCENT_MEETING.md
└── LLM_PIPELINE.md
```

SPEC 定义总体规范，后续详细内容可拆分到独立文档。

---

# 48. 配置管理

`.env.example`：

```env
APP_ENV=development

DATABASE_URL=mysql+pymysql://user:password@mysql:3306/meeting_minutes
REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=change_me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

TENCENT_MEETING_APP_ID=
TENCENT_MEETING_SECRET_ID=
TENCENT_MEETING_SECRET_KEY=

LLM_PROVIDER=bailian
LLM_MODEL=qwen3.7
BAILIAN_API_KEY=

LLM_REQUEST_TIMEOUT=120
LLM_MAX_RETRIES=3
```

生产环境不得将真实 Secret 提交到 Git。

---

# 49. 日志规范

所有日志建议包含：

```text
request_id
user_id
meeting_id
task_id
provider
operation
duration_ms
status
```

示例：

```text
INFO
request_id=req_123
meeting_id=88
operation=generate_minutes
model=qwen3.7
duration_ms=8423
status=success
```

不得记录：

- 用户密码；
- JWT；
- LLM API Key；
- 腾讯 SecretKey。

完整 Transcript 不建议写入普通日志。

---

# 50. 审计要求

以下操作必须产生 `audit_logs`：

```text
用户登录
管理员查看会议
开启 / 关闭 AI 纪要
编辑会议纪要
重新生成纪要
新增授权
取消授权
管理员修改系统配置
管理员修改 LLM 配置
```

---

# 51. 安全要求

## 51.1 API

所有内部业务 API：

```text
HTTPS
+
JWT
+
Permission Check
```

## 51.2 Secret

以下信息只存在服务端：

```text
JWT Secret
Tencent SecretId
Tencent SecretKey
Bailian API Key
```

## 51.3 LLM 数据

V1 发送给外部 LLM：

- Transcript；
- 必要会议上下文。

原则上不发送：

- 音频；
- 视频；
- 与总结无关的员工账号字段。

## 51.4 数据库

生产数据库建议：

- 最小权限账号；
- 禁止 root 账号供应用使用；
- 定期备份。

---

# 52. 前端页面

V1 页面：

```text
/login
/meetings
/meetings/:id
/notifications
/admin/meetings
/admin/tasks
/admin/users
/admin/audit-logs
```

---

# 53. Meeting Detail 页面数据组织

```text
会议基础信息
├── 会议名称
├── 主持人
├── 时间
├── 参会人员
└── AI 状态

Tab
├── AI会议纪要
│    ├── Summary
│    ├── Topics
│    ├── Decisions
│    └── Action Items
│
└── Transcript
     └── Segment List
```

Host / ADMIN 显示：

```text
编辑
重新生成
分享
查看 AI 原始版本
```

---

# 54. 通知设计

AI 生成完成：

```text
type = MINUTES_READY
```

内容：

```text
《Alpha 项目周会》AI 会议纪要已生成。
```

AI 生成失败：

```text
type = MINUTES_FAILED
```

V1 建议至少通知 Host，ADMIN 可在后台查看失败任务。

---

# 55. 测试策略

## 55.1 Unit Test

重点：

```text
PermissionService
JWT
Password Hash
LLM Parser
Schema Validation
Tencent Mapper
Minutes Version
Idempotency
```

## 55.2 Integration Test

覆盖：

```text
Login
Meeting List
Toggle AI Minutes
Webhook
Transcript Save
Generate Minutes
Edit Minutes
Regenerate
Grant Permission
Notification
```

## 55.3 Mock

测试环境不得依赖真实腾讯会议和真实 LLM。

需要 Mock：

```text
TencentMeetingClient
LLMProvider
```

## 55.4 E2E

至少覆盖：

```text
登录
→ 查看会议
→ 开启 AI 纪要
→ 模拟 Webhook
→ 自动生成纪要
→ 查看纪要
→ 编辑
→ 重新生成
→ 分享
```

---

# 56. 关键测试用例

## TC-01 未开启 AI 纪要

Webhook 到达：

```text
不得调用 LLM
```

## TC-02 重复 Webhook

同一 trace_id 重复发送：

```text
只处理一次
```

## TC-03 Transcript 尚未准备好

Worker：

```text
进入 Retry
```

## TC-04 LLM JSON 非法

```text
Retry
```

超过最大次数：

```text
FAILED
```

## TC-05 普通用户访问其他会议

返回：

```text
403
```

## TC-06 ADMIN 访问任意会议

允许，并记录：

```text
ADMIN_VIEW_MEETING
```

## TC-07 人工编辑

必须产生：

```text
MANUAL Version
```

AI Version 保留。

## TC-08 重新生成

必须产生新的 AI Version，旧版本保留。

---

# 57. 性能要求

由于公司会议规模不大，V1 不设计大规模高并发。

## 57.1 普通 API

目标 P95：

```text
< 500ms
```

不包括外部腾讯接口和 LLM。

## 57.2 分页

会议列表：

```text
默认 20
最大 100
```

Transcript：

```text
默认 100 segments/page
```

## 57.3 AI

AI 任务全部异步。

前端不得保持 HTTP 请求直到 LLM 完成。

---

# 58. 数据保留

V1 默认保留：

- 会议基础数据；
- Transcript；
- AI Versions；
- Manual Versions；
- Audit Logs。

具体保留时长后续由公司数据安全策略确定，代码中不写死保留周期。

---

# 59. 数据一致性

## 59.1 会议

以：

```text
tencent_meeting_id
```

作为腾讯会议唯一外部键。

## 59.2 Recording

以：

```text
meeting_id + record_file_id
```

唯一。

## 59.3 Webhook

以：

```text
provider + trace_id
```

唯一。

## 59.4 Minute Version

以：

```text
meeting_minutes_id + version_no
```

唯一。

---

# 60. 事务边界

以下操作建议事务执行。

## 60.1 人工编辑

```text
Create MANUAL Version
+
Update current_version_id
+
Create Audit Log
```

## 60.2 AI 生成完成

```text
Create AI Version
+
Create Action Items
+
Update current_version_id
+
Update minutes_status
+
Create Notification Task
```

---

# 61. 项目异常处理原则

第三方异常不得直接泄漏给前端。

例如百炼返回详细错误时，前端统一返回：

```json
{
  "code": 50001,
  "message": "AI 会议纪要生成失败，请稍后重试"
}
```

详细异常仅记录内部日志。

---

# 62. 开发阶段建议

## Phase 1：基础骨架

完成：

- Repository；
- Docker；
- FastAPI；
- Vue；
- MySQL；
- Redis；
- Alembic；
- JWT；
- 用户表；
- 登录。

## Phase 2：会议基础业务

完成：

- meetings；
- participants；
- meeting list；
- meeting detail；
- PermissionService。

## Phase 3：腾讯会议接入

完成：

- TencentMeetingClient；
- Auth；
- Meeting Sync；
- Webhook；
- Recording；
- Transcript。

## Phase 4：LLM

完成：

- LLMProvider；
- BailianProvider；
- Qwen3.7；
- Prompt；
- Structured Output；
- Pydantic Validation；
- Long Meeting Workflow。

## Phase 5：Minutes

完成：

- meeting_minutes；
- minute_versions；
- action_items；
- AI Generation；
- Manual Edit；
- Regenerate。

## Phase 6：通知与权限

完成：

- Permissions；
- Notifications；
- Audit Logs。

## Phase 7：Admin

完成：

- Meetings；
- Tasks；
- Users；
- Audit；
- LLM Config。

## Phase 8：测试与部署

完成：

- Unit Test；
- Integration Test；
- E2E；
- Nginx；
- Docker Compose；
- Production Config。

---

# 63. V1 技术验收标准

## Backend

- [ ] JWT 登录可用；
- [ ] 密码使用安全 Hash；
- [ ] 权限通过 PermissionService 统一控制；
- [ ] ADMIN 拥有全部权限；
- [ ] 腾讯会议 API 通过 Adapter 调用；
- [ ] Webhook 具备幂等；
- [ ] Webhook 不执行长任务；
- [ ] Transcript 能够标准化保存；
- [ ] AI 任务异步执行；
- [ ] LLM 通过 Provider 抽象；
- [ ] 当前默认支持百炼 Qwen3.7；
- [ ] AI 返回经过 Schema 校验；
- [ ] 长会议支持 Chunk / Reduce；
- [ ] AI 原始版本保留；
- [ ] 人工编辑产生新 Version；
- [ ] 重新生成产生新 AI Version；
- [ ] 失败任务可以重试；
- [ ] 重要管理员操作存在 Audit Log。

## Frontend

- [ ] 用户可以登录；
- [ ] 可以查看本人会议；
- [ ] Host 可以开启 AI 纪要；
- [ ] 可以查看 AI 状态；
- [ ] 可以查看纪要；
- [ ] 可以查看 Transcript；
- [ ] Host 可以编辑；
- [ ] Host 可以重新生成；
- [ ] Host 可以授权其他用户；
- [ ] 用户可以查看通知；
- [ ] ADMIN 可以进入管理后台。

## Deployment

- [ ] Docker Compose 可启动完整系统；
- [ ] Nginx 正常代理；
- [ ] Secret 不提交 Git；
- [ ] 数据库 Migration 可执行；
- [ ] Redis / Worker 正常运行；
- [ ] 日志可查询。

---

# 64. 后续扩展预留

## V1.1

```text
Evidence
纪要定位原文
更多通知渠道
按发言人筛选 Transcript
```

## V2

```text
会议模板
项目周会
需求评审
技术评审
TODO 系统集成
导出 PDF / Word
```

## V3

```text
Embedding
Vector DB
RAG
跨会议问答
企业会议知识库
决策追踪
```

## Agent 引入条件

当系统出现：

```text
自主判断下一步
+
动态调用多个 Tool
+
根据执行结果重新规划
```

再考虑 Agent。

---

# 65. 最终技术基线

V1 最终采用：

```text
Frontend
Vue3 + TypeScript + Vite + Element Plus

Backend
FastAPI + Python 3.12
Pydantic v2
SQLAlchemy 2.x
Alembic

Authentication
Username / Password
JWT Access + Refresh Token

Database
MySQL 8

Async
Celery + Redis

Tencent Meeting
企业级自建应用
REST API + Webhook
TencentMeetingClient Adapter

LLM
百炼平台
Qwen3.7
LLMProvider Adapter
Structured JSON
Pydantic Validation
Long Meeting Map-Reduce

Architecture
模块化单体
+
独立 Celery Worker

Deployment
Docker Compose
+
Nginx

V1 不使用
Agent
RAG
Vector Database
ASR
Microservices
Kubernetes
```

---

# 66. 结论

AI 智能会议纪要系统 V1 的核心技术原则是：

> **以确定性业务 Workflow 管理整个会议处理链路，只在需要自然语言理解与信息抽取的位置调用 LLM。**

腾讯会议负责：

```text
会议
录制
转写
Speaker
时间轴
```

内部系统负责：

```text
身份认证
权限
数据同步
任务调度
纪要版本
通知
审计
```

Qwen3.7 负责：

```text
会议内容理解
摘要
主题提取
决策提取
TODO 提取
负责人 / Deadline 提取
```

通过：

```text
TencentMeetingClient
+
LLMProvider
```

隔离第三方依赖，使后续腾讯会议接口升级或 LLM 厂商切换时，不影响核心业务代码。

V1 优先追求：

```text
可落地
可测试
可追踪
可维护
可扩展
```

而不是提前引入 Agent、RAG、微服务或复杂分布式基础设施。
