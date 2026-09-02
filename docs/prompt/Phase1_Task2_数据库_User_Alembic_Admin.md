# Phase 1 Task 2：数据库基础 + User Model + Alembic + UserRepository + Password Hash + create_admin

> 项目：AI 智能会议纪要系统  
> 项目根目录：`F:\BoFang\aimeeting`  
> GitHub 仓库：`https://github.com/Zst2001/aimeeting`  
> 设计文档目录：`F:\BoFang\aimeeting\docs`  
> 本提示词建议保存位置：`F:\BoFang\aimeeting\docs\prompt\Phase1_Task2_数据库_User_Alembic_Admin.md`  
> Codex 完成后的确认报告目录：`F:\BoFang\aimeeting\docs\require`  
> 当前阶段：Phase 1 / Task 2  
> 前置任务：Phase 1 Task 1 已验收通过  
> 当前目标：在 Task 1 工程骨架基础上完成数据库用户域基础，不实现 JWT、登录 API、会议业务、腾讯会议或 LLM

---

# 一、开始任务前必须做的事情

你现在需要在现有项目：

```text
F:\BoFang\aimeeting
```

中完成：

> **Phase 1 Task 2：数据库基础 + User Model + Alembic + UserRepository + Password Hash + create_admin**

开始修改代码前，必须先完成以下检查。

首先重新阅读并理解以下设计文档：

```text
F:\BoFang\aimeeting\docs\AI智能会议纪要系统_PRD_v1.0.md
F:\BoFang\aimeeting\docs\AI智能会议纪要系统_SPEC_v1.0.md
F:\BoFang\aimeeting\docs\DATABASE.md
F:\BoFang\aimeeting\docs\API.md
F:\BoFang\aimeeting\docs\TENCENT_MEETING.md
F:\BoFang\aimeeting\docs\LLM_PIPELINE.md
```

如果实际文件名存在轻微差异，请以 `docs` 目录真实文件为准进行识别。

同时阅读上一阶段确认报告：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task1_确认报告.md
```

确认 Task 1 当前已经完成的工程基础，包括：

```text
FastAPI
Vue3
MySQL
Redis
Docker Compose
Settings
SQLAlchemy Session 基础
/health
/ready
Request ID
Logging
Global Exception
Backend Tests
Frontend Build
```

在开始修改前执行：

```powershell
cd F:\BoFang\aimeeting
git status
git branch --show-current
git log -1 --oneline
```

记录当前 Git 基线。

本 Task 不要求你自动向 GitHub Push，也不要擅自执行：

```text
git push
git reset --hard
git clean -fd
```

除非用户后续明确要求。

---

# 二、设计文档优先级

如果本提示词与已有设计文档存在冲突：

```text
PRD
↓
SPEC
↓
DATABASE.md
↓
API.md
↓
其他细化文档
```

其中数据库字段、索引、约束和用户表设计：

> **以 DATABASE.md 为直接实现依据。**

不要根据个人偏好重新设计 `users` 表。

如果发现无法安全判断的冲突：

1. 不自行猜测；
2. 保留现有设计；
3. 在确认报告中明确指出；
4. 不扩大实现范围。

---

# 三、Task 2 的目标

Task 2 完成后，系统应具备如下基础链路：

```text
MySQL
  ↓
Alembic
  ↓
users table
  ↓
SQLAlchemy User Model
  ↓
UserRepository
  ↓
Argon2id Password Hash
  ↓
create_admin CLI
```

并且必须真实验证：

```text
alembic upgrade head
        ↓
users table created
        ↓
create_admin
        ↓
ADMIN inserted
        ↓
password stored as hash
        ↓
duplicate username rejected
        ↓
alembic downgrade -1
        ↓
users table removed
        ↓
alembic upgrade head
        ↓
users table restored
```

Task 2 的核心是：

> 建立后续 Auth 模块可直接复用的数据库用户基础。

---

# 四、本阶段明确禁止实现的内容

当前 Task 不要实现：

```text
JWT
Access Token
Refresh Token
Redis Refresh Session
AuthService

POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET /api/v1/me

Login 页面
Axios Auth Interceptor
Router Auth Guard

Meeting
MeetingParticipant
MeetingRecording
Transcript
MeetingMinutes
MinuteVersion
ActionItem
Permission
Notification
AuditLog
SystemSetting

TencentMeetingClient
腾讯会议 REST API
腾讯会议 Webhook

百炼
Qwen3.7 Plus
LLMProvider
Prompt
LLM Pipeline

Celery 业务任务
Agent
RAG
Vector DB
ASR
```

Task 2 不应该新增任何新的业务 HTTP API。

如果你开始实现：

```text
/login
/me
/admin/users
```

说明已经越界，应停止。

---

# 五、Task 1 必须保持稳定

Task 2 不允许破坏上一阶段已经完成的功能。

完成后必须继续保证：

```text
GET /health → 200
GET /ready → MySQL/Redis 正常
X-Request-ID 正常
FastAPI 正常启动
Vue 正常启动
Docker Compose 正常
Backend tests 正常
Frontend build 正常
```

不要为了 Task 2 重构 Task 1 中已经稳定的目录和实现，除非确有必要。

如果必须修改已有基础代码：

- 修改应最小化；
- 说明原因；
- 在确认报告列出。

---

# 六、users 表必须严格落实 DATABASE.md

需要实现的 `users` 字段：

```text
id
username
password_hash
employee_no
display_name
email
tencent_userid
role
status
last_login_at
created_at
updated_at
```

数据库语义：

```text
id                  BIGINT UNSIGNED PK AUTO_INCREMENT

username            VARCHAR(64) NOT NULL UNIQUE

password_hash       VARCHAR(255) NOT NULL

employee_no         VARCHAR(64) NULL UNIQUE

display_name        VARCHAR(128) NOT NULL

email               VARCHAR(255) NULL

tencent_userid      VARCHAR(128) NULL

role                VARCHAR(16) NOT NULL DEFAULT USER

status              VARCHAR(16) NOT NULL DEFAULT ACTIVE

last_login_at       DATETIME(6) NULL

created_at          DATETIME(6) NOT NULL

updated_at          DATETIME(6) NOT NULL
```

索引至少包括：

```text
UNIQUE(username)

UNIQUE(employee_no)

INDEX(tencent_userid)

INDEX(role, status)
```

注意：

`employee_no` 允许 NULL。

MySQL 唯一索引允许多条 NULL，符合当前设计需求。

---

# 七、UserRole 与 UserStatus

Python 代码层定义：

```python
class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
```

以及：

```python
class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
```

数据库字段仍使用：

```text
VARCHAR
```

不要改为 MySQL ENUM。

原因：

- 与 DATABASE.md 一致；
- 后续扩展更容易；
- 避免数据库 Enum Migration 复杂化。

Enum 放置位置应清晰，可根据当前目录合理选择，例如：

```text
app/db/models/user.py
```

或独立 constants/enums 模块。

不要为两个 Enum 创建过度复杂的 Domain 层。

---

# 八、SQLAlchemy User Model

新增：

```text
backend/app/db/models/
├── __init__.py
└── user.py
```

User Model：

- 使用 Task 1 已存在的统一 `Base`；
- 字段长度必须与 DATABASE.md 对齐；
- nullable 必须对齐；
- index / unique 必须对齐；
- 不应额外增加未经设计确认的字段。

不要使用：

```python
Base.metadata.create_all(...)
```

来创建生产表。

所有数据库结构变化必须通过：

```text
Alembic Migration
```

管理。

---

# 九、时间字段规范

项目规范：

```text
数据库统一存 UTC
```

Task 2 需要正确处理：

```text
created_at
updated_at
last_login_at
```

不要在项目各处随意使用：

```python
datetime.now()
```

导致本地时区不确定。

推荐使用统一 UTC helper，例如：

```text
app/utils/datetime.py
```

但如果 Task 1 当前已有合理 UTC 实现，应复用，不重复创建。

要求：

```text
created_at / updated_at
```

创建时有正确值。

`last_login_at`：

```text
Task 2 可以保持 NULL
```

Task 3 登录成功时再更新。

---

# 十、Alembic 初始化

Task 2 正式初始化 Alembic。

推荐结构：

```text
backend/
├── alembic.ini
└── migrations/
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── <revision>_create_users.py
```

要求：

`migrations/env.py` 必须：

```text
加载 Settings
加载 SQLAlchemy Base
加载 User Model metadata
```

数据库 URL 必须来自：

```text
Settings
```

禁止在：

```text
alembic.ini
migrations/env.py
```

硬编码：

```text
username
password
localhost
完整连接字符串
```

---

# 十一、第一条 Migration

本 Task 只创建：

```text
users
```

Migration 名称建议：

```text
create_users
```

Revision ID 可以由 Alembic 自动生成。

不要提前创建：

```text
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
system_settings
```

这些属于后续阶段。

---

# 十二、Migration Upgrade / Downgrade

Migration 必须同时实现：

```python
upgrade()
```

和：

```python
downgrade()
```

并实际验证：

```powershell
alembic upgrade head
alembic current
alembic downgrade -1
alembic upgrade head
```

验证过程中应检查：

```text
upgrade → users 表存在
downgrade → users 表删除
再次 upgrade → users 表恢复
```

不要只生成 Migration 文件而不运行。

---

# 十三、不要在 Backend 启动时自动执行 Migration

禁止在 FastAPI 启动过程中写：

```python
subprocess.run(["alembic", "upgrade", "head"])
```

也不要：

```python
Base.metadata.create_all()
```

自动替代 Migration。

当前正确模式：

```text
开发/部署步骤
        ↓
alembic upgrade head
        ↓
启动应用
```

README 中补充 Migration 操作即可。

---

# 十四、Password Hash

Task 2 需要新增：

```text
backend/app/core/security.py
```

当前只实现密码相关基础：

```text
hash_password()
verify_password()
```

使用：

> **Argon2id**

推荐依赖：

```text
argon2-cffi
```

禁止：

```text
明文密码
MD5
SHA1
SHA256(password)
自制 salt 算法
```

Task 2 不实现 JWT。

---

# 十五、密码函数要求

例如：

```python
def hash_password(password: str) -> str:
    ...
```

以及：

```python
def verify_password(password: str, password_hash: str) -> bool:
    ...
```

要求测试：

```text
hash != plaintext

正确密码：
verify = True

错误密码：
verify = False
```

如果传入非法 Hash：

不应导致整个应用异常退出。

应根据安全组件合理处理。

---

# 十六、Password Policy

Task 2 `create_admin` 至少检查：

```text
密码不能为空
建议最少 8 字符
确认密码一致
```

不要在 Task 2 实现复杂企业密码策略。

API.md 中更完整的密码策略后续可继续增强。

---

# 十七、UserRepository

新增：

```text
backend/app/repositories/
├── __init__.py
└── user_repository.py
```

至少实现：

```text
get_by_id()

get_by_username()

get_by_employee_no()

get_by_tencent_userid()

create()
```

方法命名可以符合当前代码风格，但职责必须完整。

---

# 十八、Repository 层职责

Repository 负责：

```text
SQLAlchemy Query
Persistence
Basic DB Access
```

不负责：

```text
HTTP Response
JWT
Password Input
Console Output
Business Permission
```

调用链：

```text
CLI / Future Service
        ↓
UserRepository
        ↓
SQLAlchemy Session
        ↓
MySQL
```

`create_admin.py` 应尽量复用 `UserRepository`。

不要在多个文件重复：

```python
select(User).where(User.username == ...)
```

---

# 十九、UserRepository.create

创建用户时应接收已经 Hash 后的：

```text
password_hash
```

不要让 Repository 自己接收明文密码。

职责：

```text
Security Layer
    ↓ hash
Repository
    ↓ save
```

这样后续：

```text
AdminService
Auth/User management
```

可以保持一致。

---

# 二十、数据库 IntegrityError

重复：

```text
username
employee_no
```

可能触发 MySQL IntegrityError。

Repository 或调用层需要：

- 正确 rollback；
- 不让 Session 留在 failed transaction 状态；
- 将错误转换成明确业务结果。

Task 2 不需要建立完整业务错误码 API，但 CLI 和测试必须能够确认重复用户不会覆盖原数据。

---

# 二十一、create_admin CLI

新增：

```text
backend/app/scripts/
├── __init__.py
└── create_admin.py
```

执行方式：

```powershell
cd F:\BoFang\aimeeting\backend
python -m app.scripts.create_admin
```

如果从 Docker 容器执行：

```powershell
docker compose exec backend python -m app.scripts.create_admin
```

具体 README 应写清楚当前可用方式。

---

# 二十二、create_admin 交互输入

建议：

```text
Username:
Display name:
Employee no (optional):
Email (optional):
Tencent userid (optional):
Password:
Confirm password:
```

密码输入必须使用：

```python
getpass.getpass()
```

终端不得明文回显密码。

---

# 二十三、create_admin 创建内容

管理员必须：

```text
role = ADMIN
status = ACTIVE
```

保存：

```text
password_hash
```

禁止保存：

```text
原始 password
```

创建成功后终端仅输出类似：

```text
Admin user created successfully.
```

不要输出：

```text
password
password_hash
数据库连接信息
```

---

# 二十四、重复管理员处理

如果用户名已经存在：

```text
拒绝创建
```

不要：

```text
覆盖密码
升级角色
更新已有账户
删除旧用户
```

例如：

```text
User 'admin' already exists.
```

然后安全退出。

如果 employee_no 冲突，同样拒绝。

---

# 二十五、CLI 事务

create_admin 应保证：

```text
成功 → COMMIT
失败 → ROLLBACK
```

数据库 Session 必须正常关闭。

不要让 CLI 异常后留下连接未释放。

---

# 二十六、不要把默认管理员写死

禁止：

```text
admin / admin
admin / 123456
```

禁止系统启动自动插入固定管理员。

第一个管理员只能通过：

```text
create_admin CLI
```

显式创建。

---

# 二十七、Task 2 测试结构

建议新增：

```text
backend/tests/
├── test_health.py
├── test_security.py
└── test_user_repository.py
```

必要时可增加：

```text
test_create_admin.py
```

但不要为了测试 CLI 写大量复杂框架。

---

# 二十八、Security Unit Test

至少覆盖：

```text
hash_password 返回值不是明文

同一密码每次 hash 可以不同

正确密码 verify=True

错误密码 verify=False
```

Argon2id 自带随机 salt，因此：

```text
hash(password) != hash(password)
```

通常是正常行为。

不要写错误测试要求 Hash 每次完全一致。

---

# 二十九、Repository Integration Test

至少验证：

```text
create USER

get_by_id

get_by_username

get_by_employee_no

get_by_tencent_userid

重复 username 被拒绝
```

测试用户至少包含：

```text
USER
ACTIVE
```

不要只测 ADMIN。

---

# 三十、真实 MySQL Integration Verification

虽然部分单元测试可以 Mock，但 Task 2 必须至少进行一次真实 MySQL 验证。

优先复用 Task 1 的 Docker MySQL。

例如：

```powershell
docker compose up -d mysql redis backend
```

然后：

```powershell
docker compose exec backend alembic upgrade head
```

并执行对应测试/验证。

不要只在 SQLite 中验证后声称 MySQL Schema 已通过。

---

# 三十一、数据库表结构核对

Migration 后应实际检查 `users` 表。

可使用：

```sql
SHOW CREATE TABLE users;
```

或：

```text
SQLAlchemy Inspector
```

至少确认：

```text
字段
VARCHAR 长度
NULL
UNIQUE
INDEX
```

与 DATABASE.md 一致。

在确认报告中简要记录核对结果。

---

# 三十二、Task 2 不要求修改 Frontend

正常情况下：

```text
frontend/
```

本 Task 不需要新增页面和认证逻辑。

要求完成后：

```text
npm run typecheck
npm run build
```

仍然通过。

如果前端完全没有修改，也应在报告中说明：

```text
Frontend source unchanged; regression build passed.
```

---

# 三十三、README 更新

Task 2 需要在 README 新增：

```text
Database Migration

alembic upgrade head
alembic current
alembic downgrade -1

Create First Admin

python -m app.scripts.create_admin
```

同时说明：

```text
不要直接使用 Base.metadata.create_all()
```

README 不要写真实管理员密码。

---

# 三十四、pyproject.toml

Task 2 需要加入：

```text
argon2-cffi
```

Alembic 如果 Task 1 已安装则保持。

不要引入：

```text
python-jose
PyJWT
```

JWT 属于 Task 3。

---

# 三十五、Docker 回归

Task 2 完成后至少重新执行：

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

验证：

```text
mysql healthy
redis healthy
backend healthy
frontend running
```

Task 2 不应破坏 Task 1 Docker 环境。

---

# 三十六、Health Regression

重新验证：

```text
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/ready
```

期望：

```text
/health → 200
/ready  → 200
mysql=ok
redis=ok
```

---

# 三十七、Git 检查

任务结束前执行：

```powershell
git status
git diff --stat
git diff
```

检查：

- 是否误改六份设计文档；
- 是否产生 `.env`；
- 是否提交虚拟环境；
- 是否提交 node_modules；
- 是否存在意外生成文件。

如果六份设计文档被意外修改：

> 在不破坏用户其他工作的前提下恢复本 Task 对这些文件的修改，并在报告说明。

不要自动覆盖用户在任务开始前已经存在的未提交修改。

---

# 三十八、禁止自动 Push

完成 Task 2 后：

不要自动：

```text
git push
```

也不要自动创建 GitHub PR。

只报告：

```text
git status
主要 diff
```

是否 Commit / Push 由用户决定。

如果用户当前工作流已经明确要求 Codex 自动 Commit，则遵循用户后续明确指令；本提示词本身不授权自动 Push。

---

# 三十九、建议执行顺序

请按照以下顺序进行：

```text
Step 1
重新阅读六份设计文档 + Task 1 报告

Step 2
检查 git status / 当前基线

Step 3
检查 Task 1 DB Base / Session 实现

Step 4
补充 UserRole / UserStatus

Step 5
实现 User SQLAlchemy Model

Step 6
初始化 Alembic

Step 7
创建 create_users Migration

Step 8
执行 alembic upgrade head

Step 9
核对 users 表结构

Step 10
执行 downgrade -1

Step 11
再次 upgrade head

Step 12
实现 Argon2id password utilities

Step 13
实现 UserRepository

Step 14
实现 create_admin CLI

Step 15
创建 Unit / Integration Tests

Step 16
实际创建一个测试 ADMIN

Step 17
验证密码不是明文

Step 18
验证重复 username 被拒绝

Step 19
执行完整 backend pytest

Step 20
执行 frontend typecheck/build regression

Step 21
执行 Docker Compose regression

Step 22
执行 /health /ready regression

Step 23
执行 git diff 检查

Step 24
生成 Task 2 确认报告
```

---

# 四十、必须实际执行的验证命令

根据当前环境选择正确命令，但至少完成等价验证。

Backend：

```powershell
cd F:\BoFang\aimeeting\backend

.\.venv\Scripts\python.exe -m pytest -q
```

如果虚拟环境路径不同，以项目实际为准。

Alembic：

```powershell
alembic upgrade head
alembic current
alembic downgrade -1
alembic upgrade head
```

如果 Alembic 只在容器环境：

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

Create Admin：

```powershell
python -m app.scripts.create_admin
```

或 Docker：

```powershell
docker compose exec backend python -m app.scripts.create_admin
```

Docker：

```powershell
cd F:\BoFang\aimeeting

docker compose config
docker compose up -d --build
docker compose ps
```

Frontend：

```powershell
cd F:\BoFang\aimeeting\frontend

npm run typecheck
npm run build
```

HTTP：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
http://127.0.0.1:5173/
```

---

# 四十一、Definition of Done

只有真实满足以下条件，Task 2 才能标记为 SUCCESS：

```text
[ ] Task 1 原有功能保持正常

[ ] 六份设计文档未被修改

[ ] UserRole 已定义
[ ] UserStatus 已定义

[ ] users SQLAlchemy Model 与 DATABASE.md 一致

[ ] username UNIQUE
[ ] employee_no UNIQUE 且允许 NULL
[ ] tencent_userid 有索引
[ ] role + status 有联合索引

[ ] created_at / updated_at 使用统一 UTC 策略
[ ] last_login_at 允许 NULL

[ ] Alembic 初始化完成
[ ] create_users Migration 完成

[ ] alembic upgrade head 成功
[ ] alembic current 正确
[ ] alembic downgrade -1 成功
[ ] 再次 alembic upgrade head 成功

[ ] users 表实际结构与 DATABASE.md 对齐

[ ] Argon2id password hash 完成
[ ] verify_password 完成
[ ] password hash 不等于明文

[ ] UserRepository 完成
[ ] get_by_id 正常
[ ] get_by_username 正常
[ ] get_by_employee_no 正常
[ ] get_by_tencent_userid 正常
[ ] create 正常
[ ] duplicate username 正确拒绝并 rollback

[ ] create_admin CLI 完成
[ ] 密码通过 getpass 输入
[ ] ADMIN role 正确
[ ] ACTIVE status 正确
[ ] 数据库中不存在明文密码
[ ] duplicate admin username 不覆盖原用户

[ ] Backend Unit Tests 通过
[ ] MySQL Integration 验证通过

[ ] Frontend typecheck 仍通过
[ ] Frontend build 仍通过

[ ] docker compose config 通过
[ ] Docker Compose 启动正常

[ ] /health 返回 200
[ ] /ready 返回 200 且 mysql/redis 为 ok

[ ] README 已补充 Migration / create_admin 使用说明

[ ] .env 未进入 Git
[ ] Git diff 中无意外设计文档修改

[ ] 未实现 JWT
[ ] 未实现 Login API
[ ] 未实现 Refresh Token
[ ] 未实现 Frontend Login
[ ] 未实现 Meeting
[ ] 未实现 Tencent Meeting
[ ] 未实现 LLM
```

---

# 四十二、完成后必须生成确认报告

完成编码和验证后，在：

```text
F:\BoFang\aimeeting\docs\require
```

创建：

```text
Phase1_Task2_确认报告.md
```

如果已经存在需要保留的历史版本，不要静默覆盖，可以创建：

```text
Phase1_Task2_确认报告_v2.md
```

---

# 四十三、确认报告必须包含

```text
# Phase 1 Task 2 确认报告

## 1. 完成状态
SUCCESS / PARTIAL / BLOCKED

## 2. 本次完成内容

## 3. 新增 / 修改文件
列出主要文件路径与用途。

## 4. 数据模型实现
说明 User 字段、Enum、索引、约束。

## 5. Alembic
说明 revision、upgrade、downgrade、current 实际结果。

## 6. UserRepository
说明实现的方法和真实测试结果。

## 7. Password Security
说明 Argon2id、hash/verify 测试，不展示真实密码。

## 8. create_admin
说明实际执行结果、ADMIN role、ACTIVE status、重复创建验证。

## 9. MySQL 实际验证
说明 users 表结构核对方式和结果。

## 10. 自动化测试
列出实际执行命令和结果。

## 11. Docker / Health Regression
说明 docker compose、/health、/ready 结果。

## 12. Git 变更检查
说明 git status / diff，确认 docs 设计文件是否未修改。

## 13. Definition of Done Checklist
逐项真实填写 [x] / [ ]

## 14. 未完成 / 阻塞项
无则写“无”。

## 15. 与设计文档的偏差
无则写“无”。

## 16. 发现的问题 / 风险
例如 MySQL、Migration、Windows、依赖等。

## 17. 下一步建议
只能建议：

Phase 1 Task 3：
Backend Auth + JWT + Redis Refresh Token + Login/Refresh/Logout/Me

不要直接开始 Task 3。
```

---

# 四十四、任务结束规则

完成 Task 2 后：

1. 停止继续编码；
2. 不进入 Task 3；
3. 不实现任何 JWT/API；
4. 写确认报告；
5. 在 Codex 对话中简要汇报：
   - Task 2 是否 SUCCESS；
   - pytest 是否通过；
   - Alembic upgrade/downgrade 是否通过；
   - create_admin 是否真实验证；
   - Docker / health 是否正常；
   - 是否存在设计偏差；
   - Git 当前是否有未提交修改；
6. 告诉用户报告路径；
7. 等待用户审核。

---

# 四十五、最终要求

本 Task 的最终目标不是“做登录”，而是建立：

```text
可靠 User 数据模型
+
可靠 Migration
+
可靠 Repository
+
可靠 Password Hash
+
可靠 First Admin 初始化方式
```

为下一阶段：

```text
Phase 1 Task 3
Backend Authentication
```

提供稳定基础。

不要扩大 Scope。

完成后将确认报告保存到：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task2_确认报告.md
```

然后停止，等待下一步指令。
