# AI 智能会议纪要系统 API.md

> 文档类型：REST API Design  
> 版本：v1.0  
> 对应文档：`AI智能会议纪要系统_SPEC_v1.0.md`  
> Backend：FastAPI  
> API Prefix：`/api/v1`  
> 更新时间：2026-09-02

---

# 1. 文档目的

本文档定义 AI 智能会议纪要系统 V1 的 HTTP API 规范，包括：

- 身份认证；
- 用户；
- 会议；
- AI 会议纪要；
- Transcript；
- 权限；
- 通知；
- 管理员；
- 腾讯会议 Webhook；
- 分页；
- 状态码；
- 错误码；
- 请求与响应格式；
- 权限要求。

---

# 2. API 设计原则

## 2.1 REST

统一使用：

```text
GET     查询
POST    创建 / 执行动作
PUT     完整更新业务资源
PATCH   局部更新
DELETE  删除 / 撤销
```

---

## 2.2 API Version

统一：

```text
/api/v1
```

后续破坏性变更：

```text
/api/v2
```

---

## 2.3 JSON

除腾讯会议特殊 Webhook 要求外，业务 API：

```http
Content-Type: application/json
```

统一 UTF-8。

---

## 2.4 HTTP Status Code

| Status | 使用场景 |
|---|---|
| 200 | 查询 / 更新成功 |
| 201 | 创建成功 |
| 202 | 已接受异步任务 |
| 204 | 删除 / 无响应体 |
| 400 | 请求格式错误 |
| 401 | 未登录 / Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 状态冲突 / 重复操作 |
| 422 | 参数校验失败 |
| 429 | 请求过多 |
| 500 | 系统内部错误 |
| 502 | 第三方服务异常 |
| 503 | 服务暂不可用 |

---

# 3. 统一响应格式

## 3.1 Success

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_01HXYZ"
}
```

---

## 3.2 Error

```json
{
  "code": 20001,
  "message": "无会议访问权限",
  "data": null,
  "request_id": "req_01HXYZ"
}
```

---

## 3.3 422 Validation Error

FastAPI 原生 422 不直接暴露给前端。

统一转换：

```json
{
  "code": 90001,
  "message": "请求参数校验失败",
  "data": {
    "fields": [
      {
        "field": "username",
        "message": "字段不能为空"
      }
    ]
  },
  "request_id": "req_01HXYZ"
}
```

---

# 4. Request ID

每个请求生成：

```text
X-Request-ID
```

如果客户端传入合法 ID，可以沿用。

Response Header：

```http
X-Request-ID: req_01HXYZ
```

日志统一携带：

```text
request_id
user_id
meeting_id
```

---

# 5. Authentication

业务 API：

```http
Authorization: Bearer <access_token>
```

Webhook 不使用 JWT。

---

# 6. JWT

## 6.1 Access Token

建议有效期：

```text
30 min
```

## 6.2 Refresh Token

建议有效期：

```text
7 days
```

Refresh Token Session 保存在 Redis。

## 6.3 Token Payload

```json
{
  "sub": "123",
  "username": "zhangsan",
  "role": "USER",
  "type": "access",
  "jti": "uuid",
  "iat": 1788307200,
  "exp": 1788309000
}
```

---

# 7. Pagination

统一：

```text
page
page_size
```

默认：

```text
page = 1
page_size = 20
```

普通列表最大：

```text
100
```

Transcript 默认：

```text
page_size = 100
```

Response：

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 120,
  "total_pages": 6
}
```

---

# 8. Error Code

## 8.1 Authentication 100xx

| Code | Message |
|---:|---|
| 10001 | 用户名或密码错误 |
| 10002 | Token 无效 |
| 10003 | Token 已过期 |
| 10004 | Refresh Token 无效 |
| 10005 | 用户已禁用 |

## 8.2 Permission 200xx

| Code | Message |
|---:|---|
| 20001 | 无会议访问权限 |
| 20002 | 无会议纪要编辑权限 |
| 20003 | 无会议权限管理权限 |
| 20004 | 需要管理员权限 |

## 8.3 Meeting 300xx

| Code | Message |
|---:|---|
| 30001 | 会议不存在 |
| 30002 | AI 会议纪要未开启 |
| 30003 | 当前会议状态不允许该操作 |
| 30004 | 会议尚未结束 |

## 8.4 Transcript 400xx

| Code | Message |
|---:|---|
| 40001 | Transcript 尚未生成 |
| 40002 | Transcript 为空 |
| 40003 | Transcript 获取失败 |

## 8.5 Minutes / LLM 500xx

| Code | Message |
|---:|---|
| 50001 | LLM 调用失败 |
| 50002 | LLM 输出格式非法 |
| 50003 | AI 会议纪要生成中 |
| 50004 | 会议纪要不存在 |
| 50005 | 当前会议已有生成任务 |

## 8.6 Tencent Meeting 600xx

| Code | Message |
|---:|---|
| 60001 | 腾讯会议 API 调用失败 |
| 60002 | 腾讯会议鉴权失败 |
| 60003 | 腾讯会议 Webhook 验证失败 |
| 60004 | 腾讯会议录制尚未准备完成 |

## 8.7 Async 700xx

| Code | Message |
|---:|---|
| 70001 | 异步任务不存在 |
| 70002 | 异步任务执行失败 |
| 70003 | 当前任务不可重试 |

## 8.8 System 800xx / 900xx

| Code | Message |
|---:|---|
| 80001 | 系统内部错误 |
| 80002 | 服务暂不可用 |
| 90001 | 请求参数校验失败 |

---

# 9. 权限记号

本文档使用：

```text
PUBLIC
USER
HOST
VIEWER
ADMIN
```

含义：

### PUBLIC

无需登录。

### USER

任意正常登录用户。

### VIEWER

满足以下任意条件：

```text
ADMIN
OR Host
OR Participant
OR meeting_permissions VIEW
```

### HOST

```text
会议主持人
OR ADMIN
```

### ADMIN

仅管理员。

---

# 10. Auth API

# 10.1 POST /api/v1/auth/login

登录。

权限：

```text
PUBLIC
```

Request：

```json
{
  "username": "zhangsan",
  "password": "password"
}
```

Response `200`：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
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

Errors：

```text
10001
10005
```

---

# 10.2 POST /api/v1/auth/refresh

刷新 Token。

权限：

```text
PUBLIC
```

Request：

```json
{
  "refresh_token": "eyJ..."
}
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 1800
  },
  "request_id": "req_xxx"
}
```

推荐 Refresh Token Rotation：

旧 Refresh Token 使用一次后失效。

---

# 10.3 POST /api/v1/auth/logout

注销。

权限：

```text
USER
```

Request：

```json
{
  "refresh_token": "eyJ..."
}
```

Response：

```http
204 No Content
```

后台删除 Redis Refresh Session。

---

# 10.4 GET /api/v1/me

当前用户。

权限：

```text
USER
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 12,
    "username": "zhangsan",
    "employee_no": "E0012",
    "display_name": "张三",
    "email": "zhangsan@example.com",
    "role": "USER",
    "status": "ACTIVE"
  },
  "request_id": "req_xxx"
}
```

---

# 11. Meeting API

# 11.1 GET /api/v1/meetings

会议列表。

权限：

```text
USER
```

Query：

```text
scope=hosted|joined|shared
minutes_status=READY
meeting_status=ENDED
keyword=alpha
page=1
page_size=20
```

普通用户不允许：

```text
scope=all
```

ADMIN 支持：

```text
scope=all
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 101,
        "subject": "Alpha 项目周会",
        "meeting_code": "123456789",
        "host": {
          "id": 12,
          "display_name": "张三"
        },
        "start_time": "2026-09-02T06:00:00Z",
        "end_time": "2026-09-02T07:00:00Z",
        "meeting_status": "ENDED",
        "ai_minutes_enabled": true,
        "minutes_status": "READY",
        "my_role": "HOST"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 8,
    "total_pages": 1
  },
  "request_id": "req_xxx"
}
```

---

# 11.2 GET /api/v1/meetings/{meeting_id}

会议详情。

权限：

```text
VIEWER
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 101,
    "tencent_meeting_id": "tm_xxx",
    "meeting_code": "123456789",
    "subject": "Alpha 项目周会",
    "host": {
      "id": 12,
      "display_name": "张三"
    },
    "participants": [
      {
        "user_id": 12,
        "display_name": "张三",
        "is_internal": true
      },
      {
        "user_id": 15,
        "display_name": "李四",
        "is_internal": true
      }
    ],
    "start_time": "2026-09-02T06:00:00Z",
    "end_time": "2026-09-02T07:00:00Z",
    "meeting_status": "ENDED",
    "ai_minutes_enabled": true,
    "minutes_status": "READY",
    "permissions": {
      "can_view": true,
      "can_edit_minutes": true,
      "can_regenerate": true,
      "can_manage_permissions": true,
      "can_view_ai_versions": true
    }
  },
  "request_id": "req_xxx"
}
```

---

# 11.3 PATCH /api/v1/meetings/{meeting_id}/ai-minutes

开启或关闭 AI 会议纪要。

权限：

```text
HOST
```

Request：

```json
{
  "enabled": true
}
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "meeting_id": 101,
    "ai_minutes_enabled": true,
    "minutes_status": "WAITING_MEETING_END"
  },
  "request_id": "req_xxx"
}
```

业务规则：

### 开启

如果会议未结束：

```text
WAITING_MEETING_END
```

如果会议已经结束：

```text
WAITING_RECORDING
```

并触发异步状态检查。

### 关闭

只有还未进入不可逆 AI 处理阶段时允许直接关闭。

V1 推荐：

```text
READY 后关闭开关不删除已有纪要
```

只是停止未来自动处理。

---

# 12. Transcript API

# 12.1 GET /api/v1/meetings/{meeting_id}/transcript

查看完整逐字稿。

权限：

```text
VIEWER
```

Query：

```text
page=1
page_size=100
speaker_user_id=12
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 10001,
        "sequence_no": 1,
        "speaker": {
          "user_id": 12,
          "display_name": "张三"
        },
        "start_ms": 13500,
        "end_ms": 18500,
        "text": "推荐模块目前还有性能问题。"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total": 442,
    "total_pages": 5
  },
  "request_id": "req_xxx"
}
```

Errors：

```text
40001
40002
```

---

# 13. Minutes API

# 13.1 GET /api/v1/meetings/{meeting_id}/minutes

读取当前展示版本。

权限：

```text
VIEWER
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "meeting_id": 101,
    "status": "READY",
    "version": {
      "id": 1001,
      "version_no": 2,
      "version_type": "MANUAL",
      "created_at": "2026-09-02T08:30:00Z"
    },
    "content": {
      "summary": "本次会议主要讨论 Alpha 项目上线进度。",
      "topics": [
        {
          "title": "接口性能",
          "summary": "推荐服务 P95 仍约为 800ms。"
        }
      ],
      "decisions": [
        {
          "content": "上线日期调整至 2026-09-10"
        }
      ],
      "action_items": [
        {
          "id": 5001,
          "task": "优化推荐接口",
          "owner": {
            "user_id": 12,
            "name": "张三"
          },
          "deadline": "2026-09-05",
          "status": "PENDING"
        }
      ]
    }
  },
  "request_id": "req_xxx"
}
```

---

# 13.2 PUT /api/v1/meetings/{meeting_id}/minutes

人工编辑当前纪要。

权限：

```text
HOST
```

Request：

```json
{
  "summary": "修改后的会议概要",
  "topics": [
    {
      "title": "接口性能",
      "summary": "修改后的内容"
    }
  ],
  "decisions": [
    {
      "content": "上线日期调整至 2026-09-10"
    }
  ],
  "action_items": [
    {
      "task": "优化推荐接口",
      "owner_user_id": 12,
      "owner_name": "张三",
      "deadline": "2026-09-05"
    }
  ]
}
```

处理：

```text
Current Version
      ↓
Create MANUAL Version
      ↓
Create Action Items
      ↓
Update current_version_id
      ↓
Audit Log
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "version_id": 1002,
    "version_no": 3,
    "version_type": "MANUAL"
  },
  "request_id": "req_xxx"
}
```

---

# 13.3 POST /api/v1/meetings/{meeting_id}/minutes/regenerate

重新生成会议纪要。

权限：

```text
HOST
```

Request：

```json
{}
```

Response：

```http
202 Accepted
```

```json
{
  "code": 0,
  "message": "AI 会议纪要重新生成任务已创建",
  "data": {
    "task_id": 9001,
    "meeting_id": 101,
    "minutes_status": "AI_PROCESSING"
  },
  "request_id": "req_xxx"
}
```

规则：

- 不删除旧 Version；
- 同一会议不得并发生成；
- 创建新 AI Version；
- 失败不影响原当前版本。

Errors：

```text
50003
50005
```

---

# 13.4 GET /api/v1/meetings/{meeting_id}/minutes/versions

查看版本列表。

权限：

```text
HOST
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1003,
        "version_no": 3,
        "version_type": "AI",
        "model_provider": "bailian",
        "model_name": "qwen3.7",
        "prompt_version": "minutes_v1",
        "created_at": "2026-09-02T09:00:00Z"
      },
      {
        "id": 1002,
        "version_no": 2,
        "version_type": "MANUAL",
        "created_by": {
          "id": 12,
          "display_name": "张三"
        },
        "created_at": "2026-09-02T08:30:00Z"
      }
    ]
  },
  "request_id": "req_xxx"
}
```

ADMIN 同样可访问任意会议。

---

# 13.5 GET /api/v1/meetings/{meeting_id}/minutes/versions/{version_id}

读取指定版本。

权限：

```text
HOST
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1001,
    "version_no": 1,
    "version_type": "AI",
    "base_version_id": null,
    "model_provider": "bailian",
    "model_name": "qwen3.7",
    "prompt_version": "minutes_v1",
    "content": {},
    "created_at": "2026-09-02T08:00:00Z"
  },
  "request_id": "req_xxx"
}
```

---

# 14. Permission API

# 14.1 GET /api/v1/meetings/{meeting_id}/permissions

查看主动授权列表。

权限：

```text
HOST
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "user": {
          "id": 22,
          "display_name": "王五"
        },
        "permission": "VIEW",
        "granted_by": {
          "id": 12,
          "display_name": "张三"
        },
        "created_at": "2026-09-02T08:10:00Z"
      }
    ]
  },
  "request_id": "req_xxx"
}
```

---

# 14.2 POST /api/v1/meetings/{meeting_id}/permissions

授权。

权限：

```text
HOST
```

Request：

```json
{
  "user_id": 22,
  "permission": "VIEW"
}
```

Response：

```http
201 Created
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "meeting_id": 101,
    "user_id": 22,
    "permission": "VIEW"
  },
  "request_id": "req_xxx"
}
```

重复授权：

```text
409 Conflict
```

---

# 14.3 DELETE /api/v1/meetings/{meeting_id}/permissions/{user_id}

取消授权。

权限：

```text
HOST
```

Response：

```http
204 No Content
```

---

# 15. Notification API

# 15.1 GET /api/v1/notifications

权限：

```text
USER
```

Query：

```text
is_read=false
page=1
page_size=20
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 3001,
        "type": "MINUTES_READY",
        "title": "AI 会议纪要已生成",
        "content": "《Alpha 项目周会》AI 会议纪要已生成。",
        "meeting_id": 101,
        "is_read": false,
        "created_at": "2026-09-02T08:05:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  },
  "request_id": "req_xxx"
}
```

---

# 15.2 PATCH /api/v1/notifications/{notification_id}/read

标记已读。

权限：

```text
USER
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 3001,
    "is_read": true
  },
  "request_id": "req_xxx"
}
```

只能操作自己的通知。

---

# 15.3 POST /api/v1/notifications/read-all

全部已读。

权限：

```text
USER
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "updated_count": 8
  },
  "request_id": "req_xxx"
}
```

---

# 16. User Search API

主动分享会议时需要搜索内部员工。

# 16.1 GET /api/v1/users/search

权限：

```text
USER
```

Query：

```text
q=张
limit=20
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 12,
        "display_name": "张三",
        "employee_no": "E0012",
        "username": "zhangsan"
      }
    ]
  },
  "request_id": "req_xxx"
}
```

不得返回：

- password_hash；
- 敏感系统字段。

---

# 17. Tencent Meeting Webhook

# 17.1 POST /api/v1/integrations/tencent-meeting/webhook

权限：

```text
Tencent Meeting Signature
```

不使用 JWT。

处理流程：

```text
Receive
   ↓
Verify Signature
   ↓
Extract trace_id / event_type
   ↓
INSERT webhook_events
   ↓
Duplicate?
 ┌─┴─┐
Yes No
│    │
200  Create Async Task
     │
     ▼
    200
```

关键原则：

> Webhook 只负责接收事件并触发后台任务，不同步等待 Transcript 或 LLM。

## Response

根据腾讯会议实际 Webhook 协议返回官方要求的成功格式。

若官方只要求 HTTP 200，则：

```http
200 OK
```

---

# 18. Admin User API

# 18.1 GET /api/v1/admin/users

权限：

```text
ADMIN
```

Query：

```text
keyword=
status=ACTIVE
role=USER
page=1
page_size=20
```

---

# 18.2 POST /api/v1/admin/users

创建用户。

权限：

```text
ADMIN
```

Request：

```json
{
  "username": "lisi",
  "password": "InitialPassword123!",
  "employee_no": "E0015",
  "display_name": "李四",
  "email": "lisi@example.com",
  "tencent_userid": "tm_user_15",
  "role": "USER"
}
```

Response：

```http
201 Created
```

注意：

Response 不返回密码。

---

# 18.3 PATCH /api/v1/admin/users/{user_id}

权限：

```text
ADMIN
```

Request 示例：

```json
{
  "display_name": "李四",
  "status": "DISABLED"
}
```

---

# 18.4 POST /api/v1/admin/users/{user_id}/reset-password

管理员重置密码。

权限：

```text
ADMIN
```

Request：

```json
{
  "new_password": "NewPassword123!"
}
```

必须记录 Audit Log。

---

# 19. Admin Meeting API

# 19.1 GET /api/v1/admin/meetings

权限：

```text
ADMIN
```

支持：

```text
keyword
host_user_id
meeting_status
minutes_status
start_date
end_date
page
page_size
```

---

# 19.2 GET /api/v1/admin/meetings/{meeting_id}

可直接复用普通 Meeting Detail Service。

权限：

```text
ADMIN
```

必须记录：

```text
ADMIN_VIEW_MEETING
```

---

# 20. Admin Task API

# 20.1 GET /api/v1/admin/tasks

权限：

```text
ADMIN
```

Query：

```text
task_type=
status=
business_id=
page=1
page_size=20
```

Response：

```json
{
  "items": [
    {
      "id": 9001,
      "task_type": "GENERATE_MINUTES",
      "business_id": "101",
      "status": "FAILED",
      "retry_count": 3,
      "error_message": "LLM timeout",
      "created_at": "...",
      "started_at": "...",
      "finished_at": "..."
    }
  ]
}
```

---

# 20.2 POST /api/v1/admin/tasks/{task_id}/retry

手动重试。

权限：

```text
ADMIN
```

Response：

```http
202 Accepted
```

```json
{
  "code": 0,
  "message": "任务已重新提交",
  "data": {
    "task_id": 9002
  },
  "request_id": "req_xxx"
}
```

---

# 21. Admin Audit API

# 21.1 GET /api/v1/admin/audit-logs

权限：

```text
ADMIN
```

Query：

```text
user_id=
action=
resource_type=
resource_id=
start_time=
end_time=
page=
page_size=
```

Response：

```json
{
  "items": [
    {
      "id": 7001,
      "user": {
        "id": 1,
        "display_name": "管理员"
      },
      "action": "ADMIN_VIEW_MEETING",
      "resource_type": "MEETING",
      "resource_id": "101",
      "ip_address": "10.0.0.10",
      "created_at": "..."
    }
  ]
}
```

---

# 22. Admin LLM Config API

V1 API Key 不通过数据库配置接口管理。

API 仅调整非敏感业务配置。

# 22.1 GET /api/v1/admin/llm-config

权限：

```text
ADMIN
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "provider": "bailian",
    "model": "qwen3.7",
    "timeout_seconds": 120,
    "max_retries": 3,
    "api_key_configured": true
  },
  "request_id": "req_xxx"
}
```

注意：

```text
api_key_configured
```

只返回是否已经配置。

不返回实际 API Key。

---

# 22.2 PUT /api/v1/admin/llm-config

权限：

```text
ADMIN
```

Request：

```json
{
  "provider": "bailian",
  "model": "qwen3.7",
  "timeout_seconds": 120,
  "max_retries": 3
}
```

Response：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "provider": "bailian",
    "model": "qwen3.7",
    "timeout_seconds": 120,
    "max_retries": 3
  },
  "request_id": "req_xxx"
}
```

必须记录：

```text
ADMIN_UPDATE_LLM_CONFIG
```

---

# 23. Internal Task API

V1 不向前端暴露 Celery 内部 Callback API。

Celery Worker 直接调用 Service / Repository。

禁止设计：

```text
POST /internal/generate
```

给公网访问。

---

# 24. Meeting Sync

会议同步主要由：

```text
Webhook
+
Backend Scheduled Compensation
```

完成。

V1 普通用户不提供“手动同步腾讯会议”按钮。

ADMIN 后续如需要可增加：

```http
POST /api/v1/admin/meetings/sync
```

但不作为首版必需 API。

---

# 25. LLM API 不对前端暴露

禁止：

```text
Vue
 ↓
百炼 API
```

正确：

```text
Vue
 ↓
FastAPI
 ↓
Celery Worker
 ↓
LLMProvider
 ↓
百炼
```

因此系统内部没有：

```text
/api/v1/llm/chat
```

这类通用接口。

---

# 26. AI Regenerate 状态查询

前端无需轮询独立 Task API。

直接轮询：

```http
GET /api/v1/meetings/{meeting_id}
```

读取：

```text
minutes_status
```

或读取：

```http
GET /api/v1/meetings/{meeting_id}/minutes
```

状态：

```text
AI_PROCESSING
READY
FAILED
```

V1 可每：

```text
3~5 秒
```

短时轮询。

后续可升级：

- SSE；
- WebSocket。

V1 不需要。

---

# 27. API 幂等

## 27.1 Webhook

依靠：

```text
provider + trace_id
```

## 27.2 Regenerate

同一会议同时只允许一个生成任务。

如果已经：

```text
AI_PROCESSING
```

返回：

```http
409 Conflict
```

```json
{
  "code": 50005,
  "message": "当前会议已有生成任务",
  "data": null,
  "request_id": "req_xxx"
}
```

## 27.3 Permission

重复 VIEW 授权：

```http
409 Conflict
```

---

# 28. Rate Limit

V1 建议至少限制：

## Login

按 IP：

```text
10 requests / minute
```

按 username：

```text
5 failed attempts / 10 minutes
```

## Regenerate

同一 Meeting：

```text
禁止并发
```

可进一步限制：

```text
5 次 / 小时
```

避免误操作造成模型费用。

---

# 29. Request Validation

## Username

```text
3~64 chars
```

## Password

建议最低：

```text
8 chars
```

生产建议：

- 大小写；
- 数字；
- 特殊字符；

是否强制复杂度由公司内部策略决定。

## page_size

```text
1 <= page_size <= 100
```

Transcript：

```text
1 <= page_size <= 200
```

---

# 30. Minutes Request Schema

建议统一：

```json
{
  "summary": "string",
  "topics": [
    {
      "title": "string",
      "summary": "string"
    }
  ],
  "decisions": [
    {
      "content": "string"
    }
  ],
  "action_items": [
    {
      "task": "string",
      "owner_user_id": 12,
      "owner_name": "张三",
      "deadline": "2026-09-05"
    }
  ]
}
```

规则：

- `summary` 不允许纯空白；
- `task` 不允许空；
- `owner_user_id` 可为 null；
- `owner_name` 可为 null；
- `deadline` 可为 null；
- 未明确的信息必须保存 null，不允许前端自己补全。

---

# 31. LLM Structured Output Schema

LLM 输出与 API 编辑 Schema 保持尽可能接近。

LLM：

```json
{
  "summary": "...",
  "topics": [],
  "decisions": [],
  "action_items": [
    {
      "task": "...",
      "owner": "张三",
      "deadline": "2026-09-05"
    }
  ]
}
```

后台再执行：

```text
owner text
   ↓
Try Match Internal User
   ↓
owner_user_id / owner_name
```

匹配不到：

```text
owner_user_id = null
owner_name = LLM 原始文本
```

---

# 32. 第三方错误映射

腾讯会议、百炼异常必须映射为内部错误。

例如：

```text
Bailian HTTP 429
        ↓
Retry in Worker
        ↓
最终失败
        ↓
50001 LLM 调用失败
```

前端不得看到第三方：

- AccessKey；
- Request URL 中敏感参数；
- 原始鉴权错误；
- SDK Stack Trace。

---

# 33. API Security

所有业务 API：

```text
JWT Auth
+
PermissionService
+
HTTPS
```

敏感操作：

```text
Edit Minutes
Regenerate
Permission Change
Admin
```

同时写 Audit Log。

---

# 34. CORS

生产环境禁止：

```text
allow_origins = ["*"]
```

仅允许公司内部 Web Domain。

例如：

```text
https://meeting-ai.company.com
```

---

# 35. OpenAPI

FastAPI 自动提供 OpenAPI。

开发环境：

```text
/docs
/redoc
```

生产环境建议：

- 仅内网开放；
- 或关闭 Swagger UI；
- 不影响 `/openapi.json` 是否按公司策略控制。

---

# 36. API 模块映射

```text
api/v1/endpoints/

auth.py
users.py
meetings.py
transcripts.py
minutes.py
permissions.py
notifications.py
webhooks.py
admin_users.py
admin_meetings.py
admin_tasks.py
admin_audit.py
admin_config.py
```

不建议把所有管理员 API 全塞入一个：

```text
admin.py
```

当文件过大时应按资源拆分。

---

# 37. Service 映射

```text
AuthService
UserService
MeetingService
TranscriptService
MinutesService
PermissionService
NotificationService
AuditService
AdminService
```

Controller：

- 解析输入；
- 鉴权；
- 调用 Service；
- 返回 Schema。

不得承担复杂业务逻辑。

---

# 38. API 测试要求

每个 Endpoint 至少覆盖：

```text
Success
401
403
404
Validation Failure
Business Conflict
```

重点：

## Auth

- 正确密码；
- 错误密码；
- Disabled User；
- Refresh；
- Logout 后 Refresh 失效。

## Meeting

- Host；
- Participant；
- Shared；
- Unrelated User；
- ADMIN。

## Minutes

- Read；
- Edit；
- Regenerate；
- Duplicate Regenerate；
- Version List。

## Permission

- Grant；
- Duplicate Grant；
- Revoke；
- Unauthorized Grant。

## Webhook

- Valid；
- Invalid Signature；
- Duplicate trace_id；
- Unknown Event。

---

# 39. API V1 完整清单

```text
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/me

GET    /api/v1/users/search

GET    /api/v1/meetings
GET    /api/v1/meetings/{meeting_id}
PATCH  /api/v1/meetings/{meeting_id}/ai-minutes

GET    /api/v1/meetings/{meeting_id}/transcript

GET    /api/v1/meetings/{meeting_id}/minutes
PUT    /api/v1/meetings/{meeting_id}/minutes
POST   /api/v1/meetings/{meeting_id}/minutes/regenerate
GET    /api/v1/meetings/{meeting_id}/minutes/versions
GET    /api/v1/meetings/{meeting_id}/minutes/versions/{version_id}

GET    /api/v1/meetings/{meeting_id}/permissions
POST   /api/v1/meetings/{meeting_id}/permissions
DELETE /api/v1/meetings/{meeting_id}/permissions/{user_id}

GET    /api/v1/notifications
PATCH  /api/v1/notifications/{notification_id}/read
POST   /api/v1/notifications/read-all

POST   /api/v1/integrations/tencent-meeting/webhook

GET    /api/v1/admin/users
POST   /api/v1/admin/users
PATCH  /api/v1/admin/users/{user_id}
POST   /api/v1/admin/users/{user_id}/reset-password

GET    /api/v1/admin/meetings
GET    /api/v1/admin/meetings/{meeting_id}

GET    /api/v1/admin/tasks
POST   /api/v1/admin/tasks/{task_id}/retry

GET    /api/v1/admin/audit-logs

GET    /api/v1/admin/llm-config
PUT    /api/v1/admin/llm-config
```

---

# 40. V1 API 验收清单

- [ ] API 全部使用 `/api/v1`；
- [ ] 登录返回 Access + Refresh Token；
- [ ] Refresh Token 可撤销；
- [ ] 普通用户只能查看有权限会议；
- [ ] ADMIN 可以访问全部会议；
- [ ] Host 可以开启 AI 纪要；
- [ ] 未开启会议不能生成纪要；
- [ ] Transcript API 分页；
- [ ] Minutes 返回当前 Version；
- [ ] 编辑纪要创建 MANUAL Version；
- [ ] Regenerate 返回 202；
- [ ] 同一会议禁止并发生成；
- [ ] 旧 AI Version 不删除；
- [ ] Host 可授权 VIEW；
- [ ] 非 Host 不可授权；
- [ ] 通知只允许用户操作自己的记录；
- [ ] Webhook 有签名验证；
- [ ] Webhook 有幂等；
- [ ] Webhook 不同步调用 LLM；
- [ ] Admin 敏感操作有 Audit；
- [ ] LLM API Key 不通过 API 返回；
- [ ] 第三方异常转换为内部错误码；
- [ ] 所有接口带 request_id；
- [ ] OpenAPI Schema 与真实实现一致。

---

# 41. 后续版本 API 预留

## V1.1 Evidence

可增加：

```text
GET /api/v1/meetings/{meeting_id}/minutes/evidence
```

或直接在 Minutes Response 中附：

```json
{
  "evidence": {
    "segment_ids": [100, 101],
    "start_ms": 120000,
    "end_ms": 135000
  }
}
```

## V2 Export

```text
GET /api/v1/meetings/{meeting_id}/minutes/export?format=pdf
GET /api/v1/meetings/{meeting_id}/minutes/export?format=docx
```

## V3 Knowledge Base

独立设计：

```text
/api/v1/knowledge/...
```

不污染当前会议 CRUD API。

---

# 42. 结论

V1 API 围绕以下资源设计：

```text
Auth
User
Meeting
Transcript
Minutes
Permission
Notification
Admin
Webhook
```

核心原则：

```text
统一鉴权
统一权限
统一响应
统一错误码
异步 AI
Webhook 幂等
版本不可覆盖
管理员操作可审计
第三方接口不暴露给前端
```
