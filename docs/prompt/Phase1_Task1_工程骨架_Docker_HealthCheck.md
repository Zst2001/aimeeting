# Phase 1 Task 1：工程骨架 + Docker + FastAPI/Vue + MySQL/Redis + Health Check

> 项目：AI 智能会议纪要系统  
> 项目根目录：`F:\BoFang\aimeeting`  
> 设计文档目录：`F:\BoFang\aimeeting\docs`  
> 本提示词建议保存位置：`F:\BoFang\aimeeting\docs\prompt\Phase1_Task1_工程骨架_Docker_HealthCheck.md`  
> Codex 完成后的确认报告目录：`F:\BoFang\aimeeting\docs\require`  
> 当前任务阶段：Phase 1 / Task 1  
> 任务目标：只完成工程骨架、Docker、本地基础服务和 Health Check，不提前实现后续业务功能

---

## 一、开始任务前必须先做的事情

你现在要在现有项目 `F:\BoFang\aimeeting` 中完成 **Phase 1 Task 1：工程骨架 + Docker + FastAPI/Vue + MySQL/Redis + Health Check**。

在开始修改任何代码前，先重新阅读并理解以下六份项目设计文档：

```text
F:\BoFang\aimeeting\docs\PRD.md
F:\BoFang\aimeeting\docs\SPEC.md
F:\BoFang\aimeeting\docs\DATABASE.md
F:\BoFang\aimeeting\docs\API.md
F:\BoFang\aimeeting\docs\TENCENT_MEETING.md
F:\BoFang\aimeeting\docs\LLM_PIPELINE.md
```

如果实际文件名存在轻微差异，请先查看 `docs` 目录并根据内容识别对应文档。

这些文档已经确定了项目总体边界和技术方向。你必须以它们为依据进行开发，不要自行重新设计架构。

特别注意：

1. 不要修改这六份设计文档；
2. 不要删除已有文件；
3. 不要覆盖 `docs` 中已经确认的内容；
4. 当前只完成 Phase 1 Task 1；
5. 不要提前实现后续 Task 2、Task 3、Task 4；
6. 不要为了“目录完整”创建大量没有实际用途的空业务文件；
7. 不要引入未在 SPEC 中要求的复杂技术。

如果发现本提示词与六份设计文档存在冲突：

> 以 PRD 的产品边界为最高业务依据，以 SPEC 的总体技术架构为最高技术依据；DATABASE/API/TENCENT_MEETING/LLM_PIPELINE 作为各领域的细化规范。

如果仍然存在无法安全判断的冲突，停止相关部分实现，并在最终确认报告中明确说明。

---

# 二、本阶段的任务边界

本 Task 只负责搭建后续所有开发工作的基础工程环境。

本阶段完成后应该达到：

```text
F:\BoFang\aimeeting
        ↓
docker compose up
        ↓
MySQL 正常启动
Redis 正常启动
FastAPI 正常启动
Vue3 正常启动
        ↓
GET /health
        ↓
200 OK
        ↓
GET /ready
        ↓
能够检查 MySQL / Redis
```

本阶段 **不要求用户登录功能**。

---

# 三、本阶段明确禁止实现的功能

当前 Task 不要实现：

```text
users 表
SQLAlchemy User Model
Alembic users migration
create_admin

账号密码登录
JWT
Access Token
Refresh Token
Redis Refresh Session
AuthService
/api/v1/auth/*
/api/v1/me

Meeting
MeetingParticipant
MeetingRecording
Transcript
Minutes
Permission
Notification
Audit Log

腾讯会议 API
腾讯会议 Webhook
TencentMeetingClient

百炼
Qwen3.7 Plus
LLMProvider
Prompt
LLM Pipeline

Celery 业务任务
AI 纪要
Agent
RAG
Vector DB
ASR

管理后台业务
会议页面
会议详情
```

Celery 依赖本阶段也不是必须的。如果为了后续架构提前安装 Celery package，不要创建任何真实业务 Worker/Task；优先保持 Task 1 最小化。

---

# 四、项目根目录要求

现有项目根目录：

```text
F:\BoFang\aimeeting
```

最终至少应该形成：

```text
F:\BoFang\aimeeting
│
├── backend/
├── frontend/
├── docs/
│   ├── ...
│   ├── prompt/
│   └── require/
│
├── deploy/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

注意：

`docs` 目录已经存在，不要重建，不要破坏原有文档。

如果：

```text
docs\prompt
docs\require
```

不存在，可以创建。

---

# 五、Backend 工程骨架

后端使用：

```text
Python 3.12
FastAPI
Pydantic v2
pydantic-settings
SQLAlchemy 2.x
PyMySQL
Redis
HTTPX
Uvicorn
```

本阶段可以安装 SQLAlchemy / Alembic，为 Task 2 做准备，但：

> 不创建业务数据库表，不生成 users migration。

推荐 Backend 最小目录：

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── error_codes.py
│   │
│   └── db/
│       ├── __init__.py
│       ├── base.py
│       └── session.py
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── pyproject.toml
└── Dockerfile
```

可以根据合理需要添加 `conftest.py`，但不要创建会议、纪要、腾讯会议、LLM 等尚未使用的空壳业务文件。

---

# 六、Python 包管理

如果项目当前为空，优先采用：

```text
pyproject.toml
```

不要同时维护两套互相冲突的 `requirements.txt` 和 `pyproject.toml`。

建议核心依赖至少包含：

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
pymysql
alembic
redis
httpx
pytest
```

可添加：

```text
ruff
```

不要在本阶段引入：

```text
LangChain
LangGraph
OpenAI
DashScope
Milvus
Kafka
RabbitMQ
```

---

# 七、FastAPI 应用要求

创建 `backend/app/main.py`。

FastAPI Application 至少具备：

```text
应用名称
版本
统一配置读取
日志初始化
Request ID Middleware
Health Router
```

应用名称建议：

```text
AI Meeting Minutes
```

---

# 八、配置管理

必须使用 `pydantic-settings`，统一放在：

```text
backend/app/core/config.py
```

禁止项目各处散落 `os.getenv(...)`。

至少包含：

```text
APP_NAME
APP_ENV
DEBUG
DATABASE_HOST
DATABASE_PORT
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
REDIS_URL
BACKEND_HOST
BACKEND_PORT
```

可以预留 JWT、腾讯会议、百炼配置字段，但本 Task 不实现对应业务。

---

# 九、.env.example

项目根目录创建：

```text
.env.example
```

至少包含：

```env
APP_NAME=AI Meeting Minutes
APP_ENV=development
DEBUG=true

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

DATABASE_HOST=mysql
DATABASE_PORT=3306
DATABASE_NAME=meeting_minutes
DATABASE_USER=meeting_user
DATABASE_PASSWORD=meeting_password

MYSQL_ROOT_PASSWORD=change_me_root

REDIS_URL=redis://redis:6379/0

# Reserved for later phases
JWT_SECRET_KEY=change_me

TENCENT_MEETING_APP_ID=
TENCENT_MEETING_SDK_ID=
TENCENT_MEETING_SECRET_ID=
TENCENT_MEETING_SECRET_KEY=

LLM_PROVIDER=bailian
LLM_MODEL=qwen3.7-plus
BAILIAN_API_KEY=
```

真实 `.env` 不得提交 Git。需要运行时可以复制 `.env.example → .env`，但必须确认 `.env` 已被 `.gitignore` 忽略。

---

# 十、数据库连接基础设施

虽然本阶段不创建业务表，但需要建立数据库连接基础设施。

使用：

```text
SQLAlchemy 2.x
Sync Session
PyMySQL
```

不要使用：

```text
AsyncSession
asyncmy
```

推荐 `backend/app/db/session.py` 提供：

```text
engine
SessionLocal
get_db()
```

Database URL 通过 Settings 构造，禁止硬编码数据库密码和 localhost。

---

# 十一、Redis Client

Health Check 需要验证 Redis。

可以创建简单 Redis Client 或 helper。

当前只用于：

```text
/ready
```

不要实现 Refresh Token、Redis Lock、Celery 业务。

---

# 十二、Health Check

必须实现两个接口。

## 12.1 GET /health

用途：

```text
Liveness
```

不检查数据库。

返回：

```http
200 OK
```

```json
{
  "status": "ok"
}
```

它只回答 FastAPI 进程是否正常运行。

## 12.2 GET /ready

用途：

```text
Readiness
```

检查：

```text
MySQL
Redis
```

成功：

```http
200 OK
```

```json
{
  "status": "ready",
  "components": {
    "mysql": "ok",
    "redis": "ok"
  }
}
```

MySQL 或 Redis 任意一个不可用时建议：

```http
503 Service Unavailable
```

```json
{
  "status": "not_ready",
  "components": {
    "mysql": "error",
    "redis": "ok"
  }
}
```

不得向客户端暴露数据库密码、完整 URL、Redis URL 或 Stack Trace。

---

# 十三、统一 Request ID

每个 HTTP Request：

```text
读取 X-Request-ID
```

如果不存在则生成新 ID。

Response Header：

```http
X-Request-ID: ...
```

至少测试 `/health` Response 存在 `X-Request-ID`。

---

# 十四、日志

Phase 1 建立基础日志配置，至少包含：

```text
timestamp
level
logger
message
request_id
```

开发环境可以使用可读文本格式。

不要引入 ELK / Loki 等额外基础设施。

---

# 十五、统一异常基础

创建基础：

```text
AppException
```

和全局 Exception Handler。

内部异常统一输出类似：

```json
{
  "code": 80001,
  "message": "系统内部错误",
  "data": null,
  "request_id": "req_xxx"
}
```

详细 Stack Trace 只写开发日志，禁止返回前端。

---

# 十六、Frontend 初始化

前端技术：

```text
Vue 3
TypeScript
Vite
Element Plus
Pinia
Vue Router
Axios
```

本阶段只要求基础页面可运行。

推荐：

```text
frontend/
│
├── src/
│   ├── api/
│   │   └── client.ts
│   ├── views/
│   │   └── HomeView.vue
│   ├── router/
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── Dockerfile
```

首页只需要简单展示：

```text
AI 智能会议纪要系统
Backend Status
```

可通过 `GET /health` 显示 Backend 是否正常。

不要做 Login 页面。

---

# 十七、Vite Proxy

开发环境配置前端代理到 Backend。

浏览器不能通过容器内部地址直接访问：

```text
http://backend:8000
```

建议 Vite Dev Server Proxy：

```text
/health → backend:8000
/ready  → backend:8000
/api    → backend:8000
```

保持前端 API Client 不依赖硬编码后端 Host。

---

# 十八、Docker Compose

项目根目录创建：

```text
docker-compose.yml
```

本阶段至少包含：

```text
mysql
redis
backend
frontend
```

当前不要加入：

```text
celery-worker
nginx
```

---

# 十九、MySQL Docker

使用：

```text
mysql:8
```

需要：

```text
persistent volume
healthcheck
```

例如：

```text
mysqladmin ping
```

Backend 应等待 MySQL Healthy。

---

# 二十、Redis Docker

使用：

```text
redis:7
```

配置：

```text
healthcheck
redis-cli ping
```

Backend 应等待 Redis Healthy。

---

# 二十一、Backend Dockerfile

建议：

```text
Python 3.12 slim
```

负责：

```text
安装依赖
复制应用
启动 uvicorn
```

开发环境 reload 可以由 Docker Compose command 覆盖，不要把 production Dockerfile 与 reload 强绑定。

---

# 二十二、Frontend Dockerfile

Task 1 可以使用 Node LTS 开发容器。

如果项目初始化后生成 `package-lock.json`，后续 Docker 优先：

```text
npm ci
```

不要删除 lockfile。

---

# 二十三、开发端口

建议：

```text
Frontend 5173
Backend 8000
MySQL 3306
Redis 6379
```

---

# 二十四、Docker Health

执行：

```text
docker compose ps
```

应尽量看到：

```text
mysql      healthy
redis      healthy
backend    healthy / running
frontend   running
```

Backend Docker healthcheck 可以使用 `/health`。

---

# 二十五、Nginx

本 Task 不要求正式 Nginx。

`deploy/` 可以保留为空目录或 `.gitkeep`。

生产 Nginx 后续部署阶段再实现。

---

# 二十六、.gitignore

至少包含：

```text
.env
.env.*

!.env.example

__pycache__/
*.py[cod]

.pytest_cache/
.ruff_cache/
.mypy_cache/

.venv/
venv/

node_modules/
dist/

.idea/
.vscode/

*.log

.DS_Store
Thumbs.db
```

不要误忽略：

```text
docs/
package-lock.json
.env.example
```

---

# 二十七、README

根目录 `README.md` 至少写：

```text
项目简介
当前阶段 Phase 1 Task 1
技术栈
目录结构
环境要求
.env 配置
Docker 启动
docker compose ps
Backend Health
Backend Ready
FastAPI Docs
Frontend
停止服务
Backend Test
Frontend Build
```

不要复制完整 PRD。

---

# 二十八、后端测试

必须增加自动化测试。

至少覆盖：

```text
GET /health → 200
status = ok

/health Response 包含 X-Request-ID

/ready MySQL/Redis 成功路径

/ready 组件异常路径
```

`/ready` 单元测试应尽量通过 Mock / Dependency Injection，不要求 pytest 必须依赖 Docker。

另外必须尽可能执行真实 Docker Integration Check。

---

# 二十九、Frontend 验证

至少实际执行：

```text
npm install 或 npm ci
npm run build
```

如果 package 中有：

```text
npm run typecheck
```

也执行。

不能有明显 TypeScript Build Error。

---

# 三十、不要过度工程化

明确禁止：

```text
Kubernetes
Helm
Terraform
Kafka
RabbitMQ
MongoDB
Elasticsearch
Grafana
Prometheus
Service Mesh
Microservices
LangChain
LangGraph
Agent
RAG
```

Task 1 只需要：

```text
Vue
FastAPI
MySQL
Redis
Docker
Health
```

---

# 三十一、执行顺序

请按以下顺序执行并阶段性验证：

```text
Step 1
检查现有项目目录

Step 2
确认 docs 六份设计文档未修改

Step 3
创建 Backend 基础骨架

Step 4
实现 Settings

Step 5
实现 DB Session / Redis 基础

Step 6
实现 FastAPI /health /ready

Step 7
实现 Request ID / Exception / Logging

Step 8
创建 Backend Tests

Step 9
初始化 Vue3 + TS + Vite

Step 10
加入 Element Plus / Pinia / Router / Axios

Step 11
创建简单 Home

Step 12
创建 Backend / Frontend Dockerfile

Step 13
创建 docker-compose.yml

Step 14
创建 .env.example / .gitignore

Step 15
更新 README

Step 16
执行 Backend Test

Step 17
执行 Frontend Build

Step 18
执行 docker compose config

Step 19
执行 docker compose up -d --build

Step 20
执行最终 HTTP 验收
```

---

# 三十二、必须实际执行的验证

不要只生成代码然后声称“应该能运行”。

尽可能实际执行：

```text
pytest
npm run build
docker compose config
docker compose up -d --build
docker compose ps
```

并实际验证：

```text
GET http://localhost:8000/health
GET http://localhost:8000/ready
http://localhost:5173
```

如果环境无法运行 Docker，不要伪造结果。

确认报告中必须写：

```text
未执行
原因
用户需要执行的命令
```

---

# 三十三、Definition of Done

只有满足下面标准，才能认为 Task 1 完成：

```text
[ ] docs 六份设计文档未被修改

[ ] backend 基础工程存在
[ ] frontend Vue3 + TS + Vite 工程存在

[ ] FastAPI 正常启动
[ ] Vue 正常启动
[ ] MySQL 8 Docker 正常启动
[ ] Redis 7 Docker 正常启动

[ ] /health 返回 200
[ ] /ready 能检测 MySQL
[ ] /ready 能检测 Redis
[ ] MySQL 不可用时 /ready 返回 not_ready / 503
[ ] Redis 不可用时 /ready 返回 not_ready / 503

[ ] X-Request-ID 正常
[ ] 基础日志正常
[ ] AppException / 全局异常处理存在
[ ] Settings 集中管理

[ ] .env.example 存在
[ ] .env 被 gitignore

[ ] docker-compose.yml 存在
[ ] Backend Dockerfile 存在
[ ] Frontend Dockerfile 存在

[ ] Backend pytest 通过
[ ] Frontend build 通过
[ ] docker compose config 通过
[ ] docker compose up -d --build 可执行，或明确说明环境阻塞

[ ] README 包含完整 Task 1 启动方式

[ ] 未提前实现 Auth
[ ] 未提前实现 Meeting
[ ] 未提前实现 Tencent Meeting
[ ] 未提前实现 LLM
```

---

# 三十四、代码质量要求

保持：

```text
简单
明确
可测试
低耦合
不重复
```

不要把所有逻辑写进 `main.py`，也不要为了所谓 Clean Architecture 创建几十层没有价值的抽象。

Task 1 的目标是：

> 建立足够清晰、能够支持后续逐阶段开发的基础骨架。

---

# 三十五、完成后必须生成确认报告

完成编码和验证后，必须在：

```text
F:\BoFang\aimeeting\docs\require
```

创建：

```text
Phase1_Task1_确认报告.md
```

如果该文件已经存在，不要静默覆盖需要保留的历史报告。必要时使用：

```text
Phase1_Task1_确认报告_v2.md
```

---

# 三十六、确认报告格式

确认报告至少包含：

```text
# Phase 1 Task 1 确认报告

## 1. 完成状态
SUCCESS / PARTIAL / BLOCKED

## 2. 本次完成内容

## 3. 新增 / 修改文件
列出主要文件及作用。

## 4. 当前项目关键目录结构
不要包含 node_modules 等大目录。

## 5. 技术实现说明
Backend
Frontend
Docker
MySQL
Redis
Health
Config
Logging
Exception
Request ID

## 6. 测试与验证
列出实际执行命令、是否成功、关键结果。

## 7. Docker 验证
docker compose config
docker compose build/up
docker compose ps

## 8. HTTP 验证
/health
/ready
Frontend

## 9. Definition of Done Checklist
逐项真实填写 [x] / [ ]

## 10. 未完成 / 阻塞项
无则写“无”。

## 11. 与设计文档的偏差
无则写“无”。

## 12. 发现的问题 / 风险
如 Docker 环境、端口、依赖、Windows 路径等。

## 13. 下一步建议
只能建议 Phase 1 Task 2：
数据库基础 + User Model + Alembic + create_admin
```

---

# 三十七、任务结束规则

完成 Task 1 后：

1. 写确认报告；
2. 在 Codex 对话中简要汇报；
3. 告诉我报告完整路径；
4. 告诉我测试是否全部通过；
5. 告诉我是否存在未解决问题；
6. 停止开发。

不要继续进入：

```text
Phase 1 Task 2
```

等待我审核确认后再继续。

---

# 三十八、最终任务要求

你当前唯一目标是：

> 在 `F:\BoFang\aimeeting` 中建立一个真实可运行、真实可测试、可继续扩展的 AI 智能会议纪要系统基础工程。

最终基础链路应尽量真实验证：

```text
Docker
  ↓
MySQL + Redis
  ↓
FastAPI
  ↓
/health + /ready

Vue
  ↓
Frontend Running
  ↓
调用 Backend Health
```

不要提前开发任何会议业务、认证业务或 AI 功能。

完成后将确认报告保存到：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task1_确认报告.md
```

然后等待下一步指令。
