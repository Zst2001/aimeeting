# Phase 1 Task 3：Backend Auth + JWT + Redis Refresh Session + Login / Refresh / Logout / Me

> 项目：AI 智能会议纪要系统  
> 项目根目录：`F:\BoFang\aimeeting`  
> GitHub 仓库：`https://github.com/Zst2001/aimeeting`  
> 设计文档目录：`F:\BoFang\aimeeting\docs`  
> 本提示词建议保存位置：`F:\BoFang\aimeeting\docs\prompt\Phase1_Task3_Backend_Auth_JWT_Redis.md`  
> Codex 完成后的确认报告目录：`F:\BoFang\aimeeting\docs\require`  
> 当前阶段：Phase 1 / Task 3  
> 前置任务：Task 1、Task 2 已验收通过  
> 当前目标：只完成后端认证体系，不实现前端登录、Meeting、腾讯会议或 LLM

---

# 一、开始任务前：先验证 Git 仓库，失败则停止

上一阶段确认报告显示 Codex 在 `F:\BoFang\aimeeting` 中执行 Git 命令时得到：

```text
fatal: not a git repository
```

用户现已明确说明 GitHub 仓库为：

```text
https://github.com/Zst2001/aimeeting
```

因此 Task 3 开始编码前，必须先进入：

```powershell
cd F:\BoFang\aimeeting
```

然后实际执行：

```powershell
Get-Location
git rev-parse --show-toplevel
git status
git branch --show-current
git remote -v
git log -1 --oneline
```

预期：

```text
git rev-parse --show-toplevel
```

应指向：

```text
F:\BoFang\aimeeting
```

并且：

```text
git remote -v
```

应能看到与以下仓库一致的 `origin`：

```text
https://github.com/Zst2001/aimeeting
```

如果当前目录仍然返回：

```text
fatal: not a git repository
```

或者 Git Root 不是当前项目：

> **立即停止 Task 3 编码。**

不要自行执行：

```text
git init
git clone
git reset --hard
git clean -fd
```

也不要移动、覆盖现有代码。

此时只需向用户报告：

```text
BLOCKED：F:\BoFang\aimeeting 未识别为目标 Git 仓库
```

并说明实际 Git 命令输出，等待用户处理。

如果 Git 仓库正常，再继续下面任务。

---

# 二、检查 Task 3 开始时的 Git 工作区

Git 仓库确认后执行：

```powershell
git status --short
```

如果存在未提交改动：

1. 不要自动丢弃；
2. 不要 reset；
3. 记录这些改动；
4. 判断是否明显属于 Task 1 / Task 2 已完成但尚未提交的内容。

如果工作区存在大量无法判断来源的改动：

> 停止编码并报告用户。

如果工作区状态清晰，可以继续。

本 Task 不授权 Codex 自动：

```text
git push
git reset --hard
git clean
force push
```

是否 Commit / Push 由用户决定。

---

# 三、重新阅读项目设计文档

开始编码前重新阅读：

```text
F:\BoFang\aimeeting\docs\AI智能会议纪要系统_PRD_v1.0.md
F:\BoFang\aimeeting\docs\AI智能会议纪要系统_SPEC_v1.0.md
F:\BoFang\aimeeting\docs\DATABASE.md
F:\BoFang\aimeeting\docs\API.md
F:\BoFang\aimeeting\docs\TENCENT_MEETING.md
F:\BoFang\aimeeting\docs\LLM_PIPELINE.md
```

并阅读：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task1_确认报告.md
F:\BoFang\aimeeting\docs\require\Phase1_Task2_确认报告.md
```

如果文件实际命名存在 `(1)` 或版本后缀，请使用当前项目中真实有效的确认报告。

不得修改六份核心设计文档。

---

# 四、设计优先级

出现冲突时：

```text
PRD
↓
SPEC
↓
DATABASE.md / API.md
↓
领域细化文档
↓
Task Prompt
```

其中 Auth HTTP Contract、错误码、返回格式：

> **以 API.md 为直接依据。**

Task 2 的 User Model / Repository / Argon2id 已经是稳定基础，除非确有 bug，否则不要重新设计。

---

# 五、Task 3 目标

完成后系统应具备：

```text
username + password
        ↓
AuthService
        ↓
UserRepository
        ↓
Argon2id Verify
        ↓
JWT Access Token
+
JWT Refresh Token
        ↓
Redis Refresh Session
        ↓
Protected API
```

必须实现四个接口：

```http
POST /api/v1/auth/login

POST /api/v1/auth/refresh

POST /api/v1/auth/logout

GET /api/v1/me
```

并支持：

```text
Access Token
Refresh Token
Refresh Rotation
Logout Revocation
Disabled User
get_current_user
require_admin
last_login_at
统一 Auth 错误码
```

---

# 六、本阶段明确禁止实现

不要实现：

```text
Frontend Login 页面
Pinia Auth Store
Axios Token Interceptor
Frontend Router Guard

Admin User CRUD API

Meeting
MeetingParticipant
MeetingRecording
Transcript
Minutes
Permission
Notification
Audit 业务

TencentMeetingClient
腾讯会议 REST API
腾讯会议 Webhook

Bailian
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

Task 3 是：

> **Backend Auth Only**

前端认证属于 Task 4。

---

# 七、Task 1 / Task 2 必须保持稳定

完成 Task 3 后仍必须保证：

```text
Task 1:
FastAPI
Vue
Docker
MySQL
Redis
/health
/ready
Request ID
Logging
Exception

Task 2:
users Model
Alembic
UserRepository
Argon2id
create_admin
```

全部回归通过。

不要为了 Auth 大规模重构已有基础代码。

---

# 八、依赖

根据现有 SPEC，JWT 优先使用：

```text
python-jose[cryptography]
```

加入：

```text
backend/pyproject.toml
```

不要同时引入多个 JWT 库，例如：

```text
PyJWT + python-jose
```

只保留一个明确实现。

Redis 继续使用 Task 1 已有：

```text
redis-py
```

不要引入新的 Session Server 或认证框架。

---

# 九、认证配置

`Settings` 增加或正式启用：

```text
JWT_SECRET_KEY
JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS
```

默认开发配置建议：

```env
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

`.env.example` 中可以保留：

```env
JWT_SECRET_KEY=change_me
```

作为占位符。

但要求：

- Secret 不得硬编码在 Python；
- Secret 不得写日志；
- Token 不得写普通日志；
- 生产环境若 `APP_ENV=production`，不应允许明显弱占位 Secret 静默运行。

如果实现生产环境 Secret 校验，应保持简单，不要建立复杂 Secret Manager。

---

# 十、JWT Claims

Access Token 至少包含：

```json
{
  "sub": "123",
  "username": "zhangsan",
  "role": "USER",
  "type": "access",
  "jti": "<uuid>",
  "iat": 1788307200,
  "exp": 1788309000
}
```

Refresh Token：

```json
{
  "sub": "123",
  "username": "zhangsan",
  "role": "USER",
  "type": "refresh",
  "jti": "<uuid>",
  "iat": 1788307200,
  "exp": 1788912000
}
```

要求：

```text
sub 使用内部 users.id，序列化为 string
type 必须存在
jti 必须存在且唯一
iat / exp 必须存在
```

不要在 Token 中放：

```text
password_hash
email
Tencent Secret
其他敏感字段
```

---

# 十一、Access / Refresh 必须严格区分

实现统一安全函数，例如：

```text
create_access_token()
create_refresh_token()
decode_token()
```

并对 token type 做严格校验。

要求：

```text
Refresh Token 不能访问 /me
Access Token 不能调用 /refresh
```

错误必须按 API 规范映射，而不是抛 500。

---

# 十二、Token 错误映射

使用现有：

```text
AppException
```

与统一 Error Response。

至少：

```text
10001 用户名或密码错误

10002 Token 无效

10003 Token 已过期

10004 Refresh Token 无效

10005 用户已禁用
```

推荐行为：

```text
Access malformed / signature invalid / wrong type
→ 10002

Access expired
→ 10003

Refresh malformed / signature invalid / wrong type / expired / Redis session missing
→ 10004

Disabled User
→ 10005
```

不要将 JWT 库原始异常直接返回前端。

---

# 十三、Login Schema

Request：

```json
{
  "username": "zhangsan",
  "password": "password"
}
```

建议：

```text
LoginRequest
```

字段最低校验：

```text
username 非空
password 非空
```

不要在 Router 中手写大量字段校验。

---

# 十四、Login 业务流程

完整流程：

```text
POST /api/v1/auth/login
        ↓
Validate Request
        ↓
UserRepository.get_by_username
        ↓
Verify Password
        ↓
Check status == ACTIVE
        ↓
Update last_login_at
        ↓
Create Access Token
        ↓
Create Refresh Token
        ↓
Store Refresh Session in Redis
        ↓
Return TokenResponse
```

---

# 十五、用户名不存在与密码错误

安全要求：

```text
用户不存在
```

和：

```text
密码错误
```

必须返回同样结果：

```text
HTTP 401
code = 10001
message = 用户名或密码错误
```

禁止：

```text
“用户名不存在”
“密码错误”
```

分别返回。

如实现 dummy Argon2 verification 用于降低用户名枚举时序差异，可以做，但不要过度复杂化。

---

# 十六、Disabled User

若：

```text
status = DISABLED
```

即使密码正确：

```text
Login → 拒绝
```

错误：

```text
10005
```

Refresh 时也必须重新加载 User 并检查：

```text
ACTIVE
```

即：

> 用户被管理员禁用后，不应继续通过旧 Refresh Token 获取新的 Access Token。

---

# 十七、last_login_at

Task 3 在 `UserRepository` 中新增合理方法，例如：

```text
update_last_login()
```

只有：

```text
成功登录
```

才更新：

```text
last_login_at = UTC now
```

以下情况不能更新：

```text
用户名不存在
密码错误
DISABLED
Refresh
```

使用 Task 2 已有统一 UTC helper。

---

# 十八、Refresh Session Redis Key

统一前缀：

```text
aimm:
```

Refresh Session：

```text
aimm:auth:refresh:{jti}
```

Value 至少包含：

```json
{
  "user_id": 123
}
```

可以包含：

```text
username
created_at
```

但不要保存完整 Refresh Token。

---

# 十九、Redis TTL

Refresh Session TTL 必须：

```text
与 Refresh Token 剩余有效期一致
```

不能永久保存。

Integration Test 必须验证：

```text
TTL > 0
```

且大致不超过配置的 Refresh 生命周期。

---

# 二十、为什么 Refresh JWT 还要 Redis

当前设计明确需要可撤销 Refresh Token。

有效 Refresh 条件：

```text
JWT valid
AND
type=refresh
AND
Redis Session exists
AND
User ACTIVE
```

Logout：

```text
Delete Redis Session
```

即可使 Refresh Token 失效。

Task 3 不实现 Access Token Blacklist。

---

# 二十一、Refresh Rotation

必须实现：

> **Refresh Token Rotation**

正确流程：

```text
Refresh A
    ↓
Decode / Validate
    ↓
Check User
    ↓
Atomically consume Redis Session A
    ↓
Create Access B
Create Refresh B
    ↓
Store Session B
    ↓
Return B
```

旧：

```text
Refresh A
```

之后必须不可再使用。

---

# 二十二、原子消费 Refresh Session

当前 Redis 为 Redis 7。

优先使用：

```text
GETDEL
```

或等价原子操作。

不要使用存在明显竞态的：

```text
GET
↓
DELETE
```

作为 Refresh Rotation 核心实现。

目标：

两个并发请求同时使用同一个 Refresh Token 时：

```text
只有一个成功
```

另一个：

```text
10004 Refresh Token 无效
```

---

# 二十三、Refresh 业务流程

Request：

```json
{
  "refresh_token": "..."
}
```

流程：

```text
POST /api/v1/auth/refresh
        ↓
Decode Refresh Token
        ↓
Validate Signature / Exp / Type
        ↓
Load User
        ↓
Check ACTIVE
        ↓
Atomically consume old Redis Session
        ↓
Create new Access
        ↓
Create new Refresh
        ↓
Save new Redis Session
        ↓
Return Tokens
```

如果 Redis 中不存在旧 Session：

```text
10004
```

如果旧 Refresh Token 已使用过：

```text
10004
```

---

# 二十四、Refresh 失败的一致性

如果旧 Session 已被消费，但创建/保存新 Session 时出现不可恢复错误：

- 不允许伪造成功；
- 返回内部可恢复/服务异常；
- 用户可以重新 Login；
- 记录日志，但不要记录完整 Token。

不要为了极端场景引入复杂分布式事务。

---

# 二十五、Logout API

严格参考 API.md：

```http
POST /api/v1/auth/logout
```

当前权限：

```text
USER
```

因此要求：

```text
有效 Access Bearer Token
+
Request Body Refresh Token
```

Request：

```json
{
  "refresh_token": "..."
}
```

流程：

```text
Validate current Access User
        ↓
Decode provided Refresh Token
        ↓
确认 Refresh Token sub 与当前用户一致
        ↓
Delete Redis Session
        ↓
204 No Content
```

不要允许：

```text
用户 A 用自己的 Access Token
注销用户 B 的 Refresh Token
```

---

# 二十六、Logout 幂等

如果 Refresh Token：

- JWT 本身有效；
- 属于当前用户；
- Redis Session 已经不存在；

Logout 可以仍视为完成：

```http
204 No Content
```

不要因为用户重复点击 Logout 而产生 500。

若 Refresh Token 明显伪造或属于其他用户，则拒绝。

---

# 二十七、Access Token Logout 语义

Task 3 不实现：

```text
Access Token Blacklist
```

因此 Logout 后：

```text
Refresh Token 立即失效
Access Token 最长仍可能在剩余 30min 内有效
```

这是当前 V1 已接受的设计：

```text
Short-lived Access Token
+
Revocable Refresh Token
```

不要自行增加所有 API 请求都查 Redis 的 Access Session。

---

# 二十八、GET /api/v1/me

必须实现：

```http
GET /api/v1/me
```

Header：

```http
Authorization: Bearer <access_token>
```

流程：

```text
get_current_user
        ↓
Decode Access JWT
        ↓
type == access
        ↓
sub → user_id
        ↓
UserRepository.get_by_id
        ↓
Check ACTIVE
        ↓
Return CurrentUserResponse
```

Response 中可以包含：

```text
id
username
employee_no
display_name
email
role
status
```

绝对不能返回：

```text
password_hash
```

---

# 二十九、API Dependency

新增统一认证依赖，建议位置：

```text
backend/app/api/dependencies.py
```

或项目现有约定下的等价文件。

至少实现：

```text
get_current_user()
require_admin()
```

`get_current_user()`：

- 负责 Authorization Bearer；
- Access JWT 解析；
- User 加载；
- ACTIVE 检查。

`require_admin()`：

```text
current_user.role == ADMIN
```

否则：

```text
20004 需要管理员权限
```

虽然 Task 3 还没有 Admin API，但这个 dependency 要完成并测试，供后续复用。

---

# 三十、Bearer 认证错误

不要依赖 FastAPI 默认行为产生不统一的 403。

如果使用：

```text
HTTPBearer
```

建议：

```text
auto_error=False
```

然后通过统一 `AppException` 返回项目规定的：

```text
401 + 10002/10003
```

所有 Auth API 保持统一 Response 格式。

---

# 三十一、AuthService

新增：

```text
backend/app/services/auth_service.py
```

职责至少：

```text
authenticate_user()

login()

refresh_tokens()

logout()
```

可以根据清晰性拆出内部私有函数。

禁止：

```text
Router 直接操作 Redis
Router 直接 encode JWT
Router 直接写 SQLAlchemy Query
```

正确：

```text
Router
  ↓
AuthService
  ↓
UserRepository / Security / Refresh Session Store
```

---

# 三十二、Refresh Session Store

为了避免 `AuthService` 散落 Redis Key 和序列化细节，建议建立一个轻量组件，例如：

```text
backend/app/core/refresh_sessions.py
```

或项目现有风格下：

```text
backend/app/services/refresh_session_service.py
```

职责：

```text
store(jti, user_id, ttl)

consume(jti)   # atomic GETDEL

delete(jti)

exists / ttl   # 测试或必要诊断
```

不要为了它建立过度复杂 Repository/Domain 层。

---

# 三十三、Pydantic Schemas

新增：

```text
backend/app/schemas/auth.py
backend/app/schemas/user.py
```

至少包含：

```text
LoginRequest
RefreshRequest
LogoutRequest
TokenPair / TokenResponse
UserSummary
CurrentUserResponse
```

确保：

```text
password_hash
```

不会因为 ORM serialization 意外进入 Response。

---

# 三十四、API Router

按照项目 API 结构组织：

```text
/api/v1/auth/login
/api/v1/auth/refresh
/api/v1/auth/logout
/api/v1/me
```

建议：

```text
backend/app/api/v1/router.py

backend/app/api/v1/endpoints/auth.py
backend/app/api/v1/endpoints/users.py
```

如果 Task 1 当前 API 目录结构略有不同，可以做最小必要调整。

不要创建会议业务 Router。

---

# 三十五、统一成功响应

除 `204 logout` 外，继续使用 API.md 统一 Envelope：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx"
}
```

Login Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 12,
      "username": "zhangsan",
      "display_name": "张三",
      "role": "USER"
    }
  },
  "request_id": "req_xxx"
}
```

Refresh Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 1800
  },
  "request_id": "req_xxx"
}
```

---

# 三十六、Logout Response

严格按照 API.md：

```http
204 No Content
```

不要返回：

```json
{
  "code": 0
}
```

除非现有项目 API 规范已经明确修改。

---

# 三十七、认证日志

允许记录：

```text
operation=login
user_id
username（如公司日志策略允许）
status
request_id
```

禁止记录：

```text
password
password_hash
access_token
refresh_token
JWT_SECRET_KEY
Redis Session 原始敏感值
```

失败登录日志也不要写用户输入密码。

---

# 三十八、Login Rate Limit

`API.md` 中已有 Login Rate Limit 设计：

```text
IP: 10 requests / minute
Username: 5 failed attempts / 10 minutes
```

但当前 API.md 未明确为限流新增专用业务错误码。

因此本 Task 的处理原则：

> **不要为了 Rate Limit 擅自发明新的项目错误码。**

如果能够在不破坏既有 API Error Contract 的前提下清晰实现，可实现简单 Redis Counter + TTL，并使用标准 HTTP 429，同时在确认报告明确说明采用的内部 code。

如果无法在不修改设计文档的情况下确定错误码：

```text
本 Task 暂不实现登录限流
```

并在确认报告中写为：

```text
Deferred：API.md 定义了限流策略，但未定义对应业务错误码，等待后续统一错误码设计后实现。
```

这不阻塞 Task 3 SUCCESS。

不要为 Rate Limit 引入大型第三方框架。

---

# 三十九、测试数据

测试应通过 fixture / factory 创建临时：

```text
ACTIVE USER
DISABLED USER
ADMIN
```

测试结束后清理：

```text
MySQL Test Users
Redis Refresh Keys
```

不要把固定测试管理员和固定已知密码永久留在开发数据库。

---

# 四十、Security Unit Tests

至少测试：

```text
Access Token 生成 / Decode

Refresh Token 生成 / Decode

Access type 正确

Refresh type 正确

jti 存在

sub 正确

expired access

invalid signature

refresh used as access rejected

access used as refresh rejected
```

Task 2 的：

```text
hash_password
verify_password
```

回归仍需通过。

---

# 四十一、Login Integration Tests

至少覆盖：

```text
正确 username/password
→ 200

不存在 username
→ HTTP 401 + code 10001

错误 password
→ HTTP 401 + code 10001

不存在用户和错误密码对外 message 一致

DISABLED
→ code 10005

成功 login
→ last_login_at updated

失败 login
→ last_login_at unchanged

成功 login
→ Redis Refresh Session exists

Redis TTL > 0
```

---

# 四十二、/me Integration Tests

至少：

```text
valid access
→ 200

no Authorization
→ 401

malformed token
→ 10002

expired access
→ 10003

refresh token as Bearer
→ 10002

deleted/nonexistent user
→ 拒绝

DISABLED user
→ 10005

Response 不包含 password_hash
```

---

# 四十三、Refresh Integration Tests

必须覆盖：

```text
valid Refresh A
→ 200
→ Access B + Refresh B

Refresh A Redis Session 被消费

Refresh B Redis Session 存在

Refresh A 再次使用
→ 10004

Access Token 调 /refresh
→ 10004

invalid refresh
→ 10004

expired refresh
→ 10004

DISABLED user refresh
→ 10005
```

并验证：

```text
Rotation 后旧 JTI 不存在
新 JTI 存在
新 JTI TTL > 0
```

---

# 四十四、Refresh 并发语义

至少通过：

```text
GETDEL / 原子 consume 实现
```

保证代码层没有明显 GET+DELETE 竞态。

如果能够稳定编写并发 Integration Test，可以验证：

```text
同一 Refresh Token 两个并发请求
只有一个成功
```

如果 Windows / TestClient 并发测试引入明显脆弱性，可以不强制写并发 E2E 测试，但必须：

- 实现原子 Redis 操作；
- 单元/集成验证旧 Token 只能消费一次；
- 在报告说明。

---

# 四十五、Logout Integration Tests

至少：

```text
Login
→ Session exists

Logout(valid access + own refresh)
→ 204

Refresh Session removed

Old Refresh 再调用 refresh
→ 10004

重复 Logout
→ 204（在 Refresh JWT 本身仍合法且属于当前用户时）

User A Access + User B Refresh
→ 拒绝
```

---

# 四十六、require_admin Test

不要为了测试新增生产 `/test-admin` API。

可以：

- 直接测试 dependency；
- 或在 tests 内创建临时 FastAPI Test App / test route。

至少验证：

```text
ADMIN → Allow

USER → 403 + 20004
```

不要污染生产 API。

---

# 四十七、真实 Redis Integration

Task 3 必须至少使用一次真实 Docker Redis 验证：

```text
login
→ key exists

refresh
→ old key gone
→ new key exists

logout
→ new key gone
```

不要只 Mock Redis 后声称 Refresh Session 已完成。

---

# 四十八、真实 MySQL Integration

继续复用 Task 2 Docker MySQL。

至少验证：

```text
UserRepository
last_login_at
User status
```

与 AuthService 真实联动。

不要切换到 SQLite 代替全部 Auth Integration Test。

---

# 四十九、API Response Security

实际 HTTP 测试中检查：

```text
password_hash
```

没有出现在：

```text
/login
/me
/refresh
错误 Response
```

也不要返回：

```text
Redis Key
JWT Secret
内部 Stack Trace
```

---

# 五十、Frontend

Task 3 不实现前端 Auth。

仅回归：

```powershell
npm run typecheck
npm run build
```

如果 frontend 源码无需修改：

在确认报告注明：

```text
Frontend auth intentionally deferred to Task 4.
Frontend source unchanged except unavoidable config if any.
```

---

# 五十一、Docker 回归

实际执行：

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

必须继续看到：

```text
mysql healthy
redis healthy
backend healthy
frontend running
```

---

# 五十二、Health 回归

实际：

```text
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/ready
```

要求：

```text
/health → 200

/ready → 200
mysql=ok
redis=ok
```

---

# 五十三、Swagger / OpenAPI

Task 3 完成后检查：

```text
http://127.0.0.1:8000/docs
```

至少应能看到：

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET /api/v1/me
```

Schema 正确。

不要把：

```text
password_hash
```

暴露在 Response Schema 中。

---

# 五十四、README 更新

README 新增后端认证说明：

```text
Create Admin（Task2 已有）

Login API

Authorization: Bearer

Refresh Token

Logout

Development Test
```

不要在 README：

```text
写真实 Token
写真实密码
写 JWT Secret
```

---

# 五十五、Git 结束检查

Task 3 完成后执行：

```powershell
cd F:\BoFang\aimeeting

git status --short
git diff --stat
git diff
```

并检查：

```text
六份核心设计文档是否被改动
.env 是否意外进入 Git
真实 Secret 是否出现
Token 是否被写入文件
node_modules/.venv 是否被 Track
```

如果设计文档被本 Task 意外修改，应只恢复本 Task 引入的意外修改，不得覆盖用户原有改动。

---

# 五十六、不要自动 Commit / Push

Task 完成后默认：

```text
不自动 commit
不自动 push
```

在确认报告给出：

```text
当前 branch
git status
主要 diff
```

等待用户审核。

---

# 五十七、建议实现顺序

严格按以下顺序推进：

```text
Step 1
Git 仓库强制检查

Step 2
重新阅读六份文档 + Task1/Task2 报告

Step 3
记录 Task 3 开始前 git status

Step 4
检查 Task2 security / repository / Redis helper

Step 5
补 JWT Settings 与依赖

Step 6
实现 Access / Refresh Token Security Functions

Step 7
实现 Refresh Session Store（Redis GETDEL）

Step 8
补 UserRepository.update_last_login

Step 9
实现 Auth Schemas

Step 10
实现 AuthService

Step 11
实现 get_current_user / require_admin

Step 12
实现 /login

Step 13
实现 /refresh

Step 14
实现 /logout

Step 15
实现 /me

Step 16
Security Unit Tests

Step 17
Auth MySQL + Redis Integration Tests

Step 18
真实 Login → Refresh → Logout 链路验证

Step 19
运行完整 pytest

Step 20
Frontend typecheck/build regression

Step 21
Docker regression

Step 22
/health /ready regression

Step 23
OpenAPI 检查

Step 24
Git diff / Secret 泄漏检查

Step 25
生成确认报告并停止
```

---

# 五十八、必须实际验证的完整 Auth 链

至少用一个临时测试用户真实验证：

```text
Create ACTIVE User
       ↓
POST /login
       ↓
Access A + Refresh A
       ↓
Redis Session A exists
       ↓
GET /me with Access A
       ↓
200
       ↓
POST /refresh with Refresh A
       ↓
Access B + Refresh B
       ↓
Session A gone
Session B exists
       ↓
Reuse Refresh A
       ↓
Rejected 10004
       ↓
POST /logout
Access B + Refresh B
       ↓
204
       ↓
Session B gone
       ↓
Refresh B
       ↓
Rejected 10004
```

然后清理测试用户及测试 Redis 数据。

---

# 五十九、Definition of Done

只有真实满足以下内容才可标记 Task 3 SUCCESS：

```text
[ ] F:\BoFang\aimeeting 已确认是目标 Git 仓库
[ ] origin 指向/对应 https://github.com/Zst2001/aimeeting
[ ] Task 开始前 Git 状态已记录

[ ] Task 1 功能保持正常
[ ] Task 2 功能保持正常
[ ] 六份核心设计文档未被修改

[ ] python-jose[cryptography] 或设计指定的唯一 JWT 实现已加入
[ ] JWT Secret 通过 Settings 读取
[ ] Access 生命周期配置化
[ ] Refresh 生命周期配置化

[ ] Access Token 实现
[ ] Refresh Token 实现
[ ] token type 严格区分
[ ] sub/jti/iat/exp 正确
[ ] invalid token 映射正确
[ ] expired access 映射 10003

[ ] Refresh Session 存 Redis
[ ] Redis key 使用 aimm:auth:refresh:{jti}
[ ] Redis TTL 正确
[ ] Refresh 原子消费使用 GETDEL 或等价操作

[ ] Refresh Rotation 正常
[ ] Old Refresh 不可复用
[ ] New Refresh Session 正常建立

[ ] Logout 可以撤销 Refresh Session
[ ] Logout 校验 Refresh Token 属于当前 Access User
[ ] 重复 Logout 幂等行为正确

[ ] UserRepository.update_last_login 完成
[ ] 成功 Login 更新 last_login_at
[ ] 失败 Login 不更新 last_login_at

[ ] AuthService 完成
[ ] get_current_user 完成
[ ] require_admin 完成

[ ] POST /api/v1/auth/login 正常
[ ] POST /api/v1/auth/refresh 正常
[ ] POST /api/v1/auth/logout 正常
[ ] GET /api/v1/me 正常

[ ] 错误密码与不存在用户都返回 10001
[ ] DISABLED User 无法 Login
[ ] DISABLED User 无法 Refresh

[ ] Refresh Token 不能访问 /me
[ ] Access Token 不能作为 Refresh 使用
[ ] password_hash 不出现在任何 API Response

[ ] Security Unit Tests 通过
[ ] MySQL Auth Integration Test 通过
[ ] Redis Refresh Integration Test 通过
[ ] Login → Me → Refresh → Reuse Reject → Logout → Refresh Reject 完整链通过

[ ] Backend pytest 全部通过
[ ] Frontend typecheck 通过
[ ] Frontend build 通过

[ ] docker compose config 通过
[ ] Docker Compose 启动正常
[ ] /health 200
[ ] /ready 200 且 mysql/redis ok

[ ] Swagger/OpenAPI 可看到四个 Auth 接口
[ ] README 已更新 Auth 开发说明

[ ] git diff 已检查
[ ] .env / Secret / Token 未意外进入 Git
[ ] 未自动 Push

[ ] 未实现 Frontend Login
[ ] 未实现 Meeting
[ ] 未实现 Tencent Meeting
[ ] 未实现 LLM
```

---

# 六十、确认报告

完成后创建：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task3_确认报告.md
```

如果已有需要保留的报告，使用版本后缀，不静默覆盖历史。

---

# 六十一、确认报告格式

至少：

```text
# Phase 1 Task 3 确认报告

## 1. 完成状态
SUCCESS / PARTIAL / BLOCKED

## 2. Git 基线检查
- Get-Location
- git rev-parse --show-toplevel
- branch
- remote
- 开始时 git status
- 是否确认目标仓库

## 3. 本次完成内容

## 4. 新增 / 修改文件

## 5. JWT 实现
- Access
- Refresh
- Claims
- Expiration
- Error mapping

## 6. Redis Refresh Session
- Key
- TTL
- GETDEL / atomic consume
- Rotation

## 7. AuthService 与 Dependencies
- login
- refresh
- logout
- get_current_user
- require_admin

## 8. API 实现
- POST /login
- POST /refresh
- POST /logout
- GET /me

## 9. Security Behavior
- wrong password
- nonexistent user
- disabled user
- token type
- password_hash exposure

## 10. 自动化测试
列出实际命令和结果。

## 11. 真实 MySQL / Redis 验证
说明实际 Integration Test。

## 12. 完整 Auth 链路验证
Login → Me → Refresh → old token reject → Logout → refresh reject

## 13. Docker / Health / Frontend Regression

## 14. OpenAPI 检查

## 15. Login Rate Limit
说明：
- 已实现；或
- Deferred，原因是现有 API.md 未定义专用业务错误码。
不得默默省略。

## 16. Git 结束检查
- git status --short
- git diff --stat
- 核心 docs 是否未修改
- 是否发现 Secret
- 是否自动 Push：必须为 No

## 17. Definition of Done Checklist
逐项真实 [x] / [ ]

## 18. 未完成 / 阻塞项
无则写“无”。

## 19. 与设计文档的偏差
无则写“无”。

## 20. 发现的问题 / 风险

## 21. 下一步建议

只能建议：

Phase 1 Task 4：
Frontend Auth + Login Page + Pinia Auth Store + Axios Refresh + Router Guard + Logout

不要直接开始 Task 4。
```

---

# 六十二、任务结束规则

完成 Task 3 后：

1. 生成确认报告；
2. 不继续 Task 4；
3. 不自动 Commit/Push；
4. 在 Codex 对话中汇报：
   - Git 仓库是否正常；
   - Task 3 状态；
   - pytest 数量和结果；
   - Login/Refresh/Logout/Me 是否全部实际验证；
   - Refresh Rotation 是否通过；
   - Redis GETDEL/原子消费是否通过；
   - Docker/Health 是否正常；
   - 是否存在设计偏差；
   - 当前 Git 工作区状态；
5. 报告路径；
6. 停止，等待用户验收。

---

# 六十三、最终目标

本 Task 唯一目标是建立：

```text
User
+
Argon2id
+
AuthService
+
JWT Access
+
JWT Refresh
+
Redis Revocation
+
Refresh Rotation
+
FastAPI Auth Dependencies
```

形成真实可靠的：

```text
Login
→ Authenticated Request
→ Refresh
→ Logout
```

后端认证闭环。

不要提前进入：

```text
Frontend Auth
Meeting
Tencent Meeting
LLM
```

完成后报告保存至：

```text
F:\BoFang\aimeeting\docs\require\Phase1_Task3_确认报告.md
```

然后停止开发。
