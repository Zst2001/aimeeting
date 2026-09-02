# AI 智能会议纪要系统 DATABASE.md

> 文档类型：Database Design  
> 版本：v1.0  
> 对应文档：`AI智能会议纪要系统_SPEC_v1.0.md`  
> 数据库：MySQL 8.x  
> ORM：SQLAlchemy 2.x  
> Migration：Alembic  
> 更新时间：2026-09-02

---

# 1. 文档目的

本文档定义 AI 智能会议纪要系统 V1 的数据库结构，包括：

- 表结构；
- 字段类型；
- 主键与外键；
- 唯一约束；
- 索引；
- 状态枚举；
- 版本管理；
- 数据一致性规则；
- 事务边界；
- 数据删除与保留策略；
- Alembic Migration 规范。

V1 数据库设计目标：

1. 支撑腾讯会议数据同步；
2. 支撑逐字稿存储；
3. 支撑 AI 纪要多版本；
4. 支撑人工修改版本；
5. 支撑会议级权限；
6. 支撑异步任务、Webhook 幂等；
7. 支撑管理员审计；
8. 为后续 TODO 管理、RAG、Evidence 扩展预留空间。

---

# 2. 数据库设计原则

## 2.1 使用关系型数据库

V1 使用 MySQL 8。

不引入：

- MongoDB；
- Elasticsearch；
- Vector Database；
- 时序数据库。

原因：

V1 核心数据均为强关系型数据：

```text
User
Meeting
Participant
Recording
Transcript
Minutes
Version
Permission
Notification
Audit
```

---

## 2.2 第三方数据与内部数据隔离

腾讯会议返回的数据不得直接作为内部业务模型使用。

例如：

```text
Tencent Meeting JSON
        ↓
Mapper
        ↓
Internal Database Model
```

内部表统一使用：

- 内部自增 ID；
- 第三方 external id；
- provider 字段；
- 内部状态字段。

---

## 2.3 AI 内容版本化

AI 生成结果和人工修改结果禁止覆盖历史版本。

使用：

```text
meeting_minutes
      ↓
minute_versions
```

实现：

```text
V1 AI
V2 MANUAL ← V1
V3 AI
V4 MANUAL ← V3
```

---

## 2.4 时间规范

数据库统一保存 UTC 时间。

字段：

```text
DATETIME(6)
```

前端按照用户时区显示。

所有业务代码禁止混用：

- UTC；
- 本地时间；
- Unix 时间戳。

腾讯会议毫秒级发言时间使用：

```text
BIGINT start_ms
BIGINT end_ms
```

表示相对录制开始时间。

---

# 3. 字符集与数据库配置

建议：

```sql
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci
```

数据库：

```text
meeting_minutes
```

建议生产环境开启：

```text
InnoDB
strict mode
UTC timezone
```

---

# 4. ER 总览

```text
users
  │
  ├────────────────────────────────────┐
  │                                    │
  ▼                                    ▼
meetings                         meeting_permissions
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
system_settings
```

---

# 5. 状态常量

建议代码层使用 Python Enum，数据库保存字符串。

## 5.1 UserRole

```text
USER
ADMIN
```

## 5.2 UserStatus

```text
ACTIVE
DISABLED
```

## 5.3 MeetingStatus

```text
SCHEDULED
IN_PROGRESS
ENDED
```

## 5.4 MinutesStatus

```text
DISABLED
WAITING_MEETING_END
WAITING_RECORDING
WAITING_TRANSCRIPT
AI_PROCESSING
READY
FAILED
```

## 5.5 RecordingStatus

```text
UNKNOWN
PROCESSING
READY
FAILED
```

## 5.6 TranscriptStatus

```text
UNKNOWN
WAITING
READY
FAILED
```

## 5.7 MinuteVersionType

```text
AI
MANUAL
```

## 5.8 ActionItemStatus

V1：

```text
PENDING
```

为后续扩展预留：

```text
IN_PROGRESS
DONE
CANCELLED
```

## 5.9 AsyncTaskStatus

```text
PENDING
RUNNING
SUCCESS
FAILED
RETRYING
```

## 5.10 WebhookProcessStatus

```text
RECEIVED
PROCESSING
SUCCESS
FAILED
IGNORED
```

---

# 6. users

用户表。

```sql
CREATE TABLE users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    employee_no VARCHAR(64) NULL,
    display_name VARCHAR(128) NOT NULL,
    email VARCHAR(255) NULL,
    tencent_userid VARCHAR(128) NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'USER',
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    last_login_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_username (username),
    UNIQUE KEY uk_users_employee_no (employee_no),
    KEY idx_users_tencent_userid (tencent_userid),
    KEY idx_users_role_status (role, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 6.1 字段说明

| 字段 | 必填 | 说明 |
|---|---:|---|
| id | √ | 内部用户 ID |
| username | √ | 登录用户名 |
| password_hash | √ | Argon2id/bcrypt Hash |
| employee_no | × | 公司工号 |
| display_name | √ | 显示姓名 |
| email | × | 邮箱 |
| tencent_userid | × | 腾讯会议企业用户 ID |
| role | √ | USER / ADMIN |
| status | √ | ACTIVE / DISABLED |
| last_login_at | × | 最后登录时间 |

## 6.2 规则

- `username` 不允许重复；
- `password_hash` 不允许返回前端；
- 禁止保存明文密码；
- 禁用用户不得获取新的 Access Token；
- `tencent_userid` 用于腾讯会议参会人映射。

---

# 7. meetings

会议主表。

```sql
CREATE TABLE meetings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tencent_meeting_id VARCHAR(128) NOT NULL,
    meeting_code VARCHAR(64) NULL,
    subject VARCHAR(255) NOT NULL,
    creator_user_id BIGINT UNSIGNED NULL,
    tencent_creator_userid VARCHAR(128) NULL,
    start_time DATETIME(6) NULL,
    end_time DATETIME(6) NULL,
    meeting_status VARCHAR(32) NOT NULL DEFAULT 'SCHEDULED',
    ai_minutes_enabled TINYINT(1) NOT NULL DEFAULT 0,
    ai_minutes_enabled_by BIGINT UNSIGNED NULL,
    ai_minutes_enabled_at DATETIME(6) NULL,
    minutes_status VARCHAR(32) NOT NULL DEFAULT 'DISABLED',
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_meetings_tencent_meeting_id (tencent_meeting_id),
    KEY idx_meetings_creator (creator_user_id),
    KEY idx_meetings_start_time (start_time),
    KEY idx_meetings_status (meeting_status),
    KEY idx_meetings_minutes_status (minutes_status),
    CONSTRAINT fk_meetings_creator
        FOREIGN KEY (creator_user_id) REFERENCES users(id),
    CONSTRAINT fk_meetings_ai_enabled_by
        FOREIGN KEY (ai_minutes_enabled_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 7.1 核心规则

### AI 开关关闭

```text
ai_minutes_enabled = false
minutes_status = DISABLED
```

### AI 开关开启但会议未结束

```text
minutes_status = WAITING_MEETING_END
```

### 会议结束

```text
WAITING_RECORDING
```

### 录制完成

```text
WAITING_TRANSCRIPT
```

### AI 开始处理

```text
AI_PROCESSING
```

### AI 成功

```text
READY
```

### AI 失败

```text
FAILED
```

---

# 8. meeting_participants

会议参与者。

```sql
CREATE TABLE meeting_participants (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NULL,
    tencent_userid VARCHAR(128) NULL,
    display_name VARCHAR(128) NOT NULL,
    is_internal TINYINT(1) NOT NULL DEFAULT 0,
    join_time DATETIME(6) NULL,
    leave_time DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_participants_meeting (meeting_id),
    KEY idx_participants_user (user_id),
    KEY idx_participants_tencent_userid (tencent_userid),
    CONSTRAINT fk_participants_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_participants_user
        FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 8.1 设计说明

`user_id` 允许 NULL。

原因：

会议可能包含：

- 外部客户；
- 供应商；
- 访客；
- 未绑定内部账户的腾讯会议用户。

## 8.2 权限判断

普通用户是否为会议参会者：

```sql
SELECT 1
FROM meeting_participants
WHERE meeting_id = :meeting_id
  AND user_id = :current_user_id
LIMIT 1;
```

---

# 9. meeting_recordings

云录制文件。

```sql
CREATE TABLE meeting_recordings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_id BIGINT UNSIGNED NOT NULL,
    record_file_id VARCHAR(128) NOT NULL,
    recording_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    transcript_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    record_start_time DATETIME(6) NULL,
    record_end_time DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_recording_meeting_file (meeting_id, record_file_id),
    KEY idx_recordings_meeting_status (meeting_id, recording_status),
    KEY idx_recordings_transcript_status (transcript_status),
    CONSTRAINT fk_recordings_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 9.1 为什么独立建表

不能直接把 `record_file_id` 放入 `meetings`。

一次会议可能：

- 多次开启录制；
- 产生多个录制文件；
- 后续出现不同转写记录。

因此使用一对多：

```text
Meeting 1 ─── N Recording
```

---

# 10. transcript_segments

会议逐字稿。

```sql
CREATE TABLE transcript_segments (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_id BIGINT UNSIGNED NOT NULL,
    recording_id BIGINT UNSIGNED NOT NULL,
    provider VARCHAR(32) NOT NULL DEFAULT 'tencent_meeting',
    provider_segment_id VARCHAR(128) NULL,
    speaker_user_id BIGINT UNSIGNED NULL,
    speaker_tencent_userid VARCHAR(128) NULL,
    speaker_name VARCHAR(128) NOT NULL,
    start_ms BIGINT UNSIGNED NOT NULL,
    end_ms BIGINT UNSIGNED NOT NULL,
    text TEXT NOT NULL,
    sequence_no INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_transcript_meeting_sequence (meeting_id, sequence_no),
    KEY idx_transcript_recording_sequence (recording_id, sequence_no),
    KEY idx_transcript_speaker_user (speaker_user_id),
    CONSTRAINT fk_transcript_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_transcript_recording
        FOREIGN KEY (recording_id) REFERENCES meeting_recordings(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_transcript_speaker_user
        FOREIGN KEY (speaker_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 10.1 排序

读取完整 Transcript：

```sql
SELECT *
FROM transcript_segments
WHERE meeting_id = :meeting_id
ORDER BY sequence_no ASC;
```

## 10.2 幂等导入

如果腾讯接口存在稳定 `provider_segment_id`，推荐增加：

```text
UNIQUE(recording_id, provider_segment_id)
```

如果不能保证稳定，则通过 Worker 导入事务：

1. 锁定 recording；
2. 删除该 recording 旧 segments；
3. 批量重新插入。

V1 推荐优先使用稳定外部段落 ID。

---

# 11. meeting_minutes

一场会议对应一个逻辑纪要对象。

```sql
CREATE TABLE meeting_minutes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_id BIGINT UNSIGNED NOT NULL,
    current_version_id BIGINT UNSIGNED NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'AI_PROCESSING',
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_minutes_meeting (meeting_id),
    KEY idx_minutes_current_version (current_version_id),
    CONSTRAINT fk_minutes_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

说明：

`current_version_id` 因循环外键问题，可以在第二次 Migration 中添加 FK：

```sql
ALTER TABLE meeting_minutes
ADD CONSTRAINT fk_minutes_current_version
FOREIGN KEY (current_version_id) REFERENCES minute_versions(id);
```

---

# 12. minute_versions

纪要版本。

```sql
CREATE TABLE minute_versions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_minutes_id BIGINT UNSIGNED NOT NULL,
    version_no INT UNSIGNED NOT NULL,
    version_type VARCHAR(16) NOT NULL,
    base_version_id BIGINT UNSIGNED NULL,
    content_json JSON NOT NULL,
    model_provider VARCHAR(64) NULL,
    model_name VARCHAR(128) NULL,
    prompt_version VARCHAR(64) NULL,
    created_by BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_minute_version_no (meeting_minutes_id, version_no),
    KEY idx_minute_versions_type (meeting_minutes_id, version_type),
    KEY idx_minute_versions_base (base_version_id),
    CONSTRAINT fk_version_minutes
        FOREIGN KEY (meeting_minutes_id) REFERENCES meeting_minutes(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_version_base
        FOREIGN KEY (base_version_id) REFERENCES minute_versions(id),
    CONSTRAINT fk_version_creator
        FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 12.1 content_json

示例：

```json
{
  "summary": "本次会议主要讨论 Alpha 项目上线安排。",
  "topics": [
    {
      "title": "接口性能",
      "summary": "当前 P95 延迟约 800ms，需要继续优化。"
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
      "owner": "张三",
      "deadline": "2026-09-05"
    }
  ]
}
```

## 12.2 AI Version

```text
version_type = AI
model_provider = bailian
model_name = qwen3.7
prompt_version = minutes_v1
created_by = NULL
```

## 12.3 Manual Version

```text
version_type = MANUAL
base_version_id = 被编辑的版本
created_by = 当前用户 ID
```

---

# 13. minute_action_items

结构化 TODO。

```sql
CREATE TABLE minute_action_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    minute_version_id BIGINT UNSIGNED NOT NULL,
    task TEXT NOT NULL,
    owner_user_id BIGINT UNSIGNED NULL,
    owner_name VARCHAR(128) NULL,
    deadline DATE NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_action_items_version (minute_version_id),
    KEY idx_action_items_owner (owner_user_id),
    KEY idx_action_items_deadline (deadline),
    CONSTRAINT fk_action_version
        FOREIGN KEY (minute_version_id) REFERENCES minute_versions(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_action_owner
        FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 13.1 为什么 JSON + 独立表同时存在

`content_json` 用于完整纪要版本快照。

`minute_action_items` 用于：

- 查询“我的待办”；
- 按负责人过滤；
- 按截止日期过滤；
- 后续同步项目管理系统。

---

# 14. meeting_permissions

主动授权表。

```sql
CREATE TABLE meeting_permissions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    meeting_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    permission VARCHAR(16) NOT NULL DEFAULT 'VIEW',
    granted_by BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_meeting_user_permission (meeting_id, user_id, permission),
    KEY idx_permissions_user (user_id),
    CONSTRAINT fk_permission_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_permission_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_permission_granted_by
        FOREIGN KEY (granted_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

V1：

```text
permission = VIEW
```

后续可扩展：

```text
EDIT
MANAGE
```

---

# 15. notifications

站内通知。

```sql
CREATE TABLE notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    meeting_id BIGINT UNSIGNED NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL,
    read_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    KEY idx_notifications_user_read (user_id, is_read, created_at),
    KEY idx_notifications_meeting (meeting_id),
    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_notification_meeting
        FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

类型：

```text
MINUTES_READY
MINUTES_FAILED
```

---

# 16. webhook_events

Webhook 原始事件及幂等表。

```sql
CREATE TABLE webhook_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider VARCHAR(32) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    payload_json JSON NOT NULL,
    process_status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED',
    received_at DATETIME(6) NOT NULL,
    processed_at DATETIME(6) NULL,
    error_message TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_webhook_provider_trace (provider, trace_id),
    KEY idx_webhook_status_received (process_status, received_at),
    KEY idx_webhook_event_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

核心规则：

```text
provider + trace_id
```

必须唯一。

重复 Webhook：

```text
INSERT 失败 / 已存在
        ↓
直接返回成功
```

不得再次触发 AI 任务。

---

# 17. async_tasks

后台任务审计表。

```sql
CREATE TABLE async_tasks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_type VARCHAR(64) NOT NULL,
    business_id VARCHAR(128) NOT NULL,
    celery_task_id VARCHAR(255) NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    retry_count INT UNSIGNED NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    created_at DATETIME(6) NOT NULL,
    started_at DATETIME(6) NULL,
    finished_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    KEY idx_async_task_status (status, created_at),
    KEY idx_async_task_business (task_type, business_id),
    KEY idx_async_celery_task_id (celery_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

任务类型：

```text
SYNC_MEETING
FETCH_RECORDING
FETCH_TRANSCRIPT
GENERATE_MINUTES
REGENERATE_MINUTES
SEND_NOTIFICATION
```

---

# 18. audit_logs

安全审计。

```sql
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    before_json JSON NULL,
    after_json JSON NULL,
    ip_address VARCHAR(64) NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_audit_user_time (user_id, created_at),
    KEY idx_audit_resource (resource_type, resource_id, created_at),
    KEY idx_audit_action_time (action, created_at),
    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

V1 重点审计：

```text
LOGIN
TOGGLE_AI_MINUTES
EDIT_MINUTES
REGENERATE_MINUTES
GRANT_PERMISSION
REVOKE_PERMISSION
ADMIN_VIEW_MEETING
ADMIN_UPDATE_LLM_CONFIG
```

---

# 19. system_settings

用于保存非敏感系统配置。

```sql
CREATE TABLE system_settings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    setting_key VARCHAR(128) NOT NULL,
    setting_value JSON NOT NULL,
    description VARCHAR(255) NULL,
    updated_by BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_system_settings_key (setting_key),
    CONSTRAINT fk_system_setting_user
        FOREIGN KEY (updated_by) REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

可保存：

```text
llm.provider
llm.model
llm.timeout_seconds
llm.max_retries
minutes.long_meeting_threshold
```

禁止保存：

```text
BAILIAN_API_KEY
TENCENT_SECRET_KEY
JWT_SECRET
```

敏感 Secret 使用：

- 环境变量；
- Docker Secret；
- 公司 Secret Manager。

---

# 20. Refresh Token / Session

V1 不额外建立数据库 Token 表。

使用 Redis 管理 Refresh Token Session。

建议 Key：

```text
auth:refresh:{jti}
```

Value：

```json
{
  "user_id": 123,
  "expires_at": "..."
}
```

Logout：

```text
DELETE auth:refresh:{jti}
```

这样可以真正失效 Refresh Token。

---

# 21. Redis Key 规范

建议统一前缀：

```text
aimm:
```

示例：

```text
aimm:auth:refresh:{jti}
aimm:lock:minutes_generation:{meeting_id}
aimm:lock:transcript_fetch:{meeting_id}
aimm:rate_limit:login:{ip}
```

锁必须设置 TTL，避免死锁。

---

# 22. 数据事务规范

## 22.1 人工编辑

必须在一个事务中：

```text
SELECT current_version FOR UPDATE
        ↓
Create MANUAL Version
        ↓
Create minute_action_items
        ↓
Update current_version_id
        ↓
Create audit_log
        ↓
COMMIT
```

任何一步失败：

```text
ROLLBACK
```

---

## 22.2 AI 生成成功

事务：

```text
Create AI Version
        ↓
Create Action Items
        ↓
Update meeting_minutes.current_version_id
        ↓
Update meeting_minutes.status = READY
        ↓
Update meetings.minutes_status = READY
        ↓
COMMIT
```

通知可以在事务提交后异步执行。

---

## 22.3 权限授权

事务：

```text
Insert meeting_permissions
        ↓
Create audit_log
        ↓
COMMIT
```

---

# 23. 并发控制

## 23.1 AI 生成

Redis Lock：

```text
aimm:lock:minutes_generation:{meeting_id}
```

同一会议只允许一个：

```text
GENERATE_MINUTES
```

或：

```text
REGENERATE_MINUTES
```

同时运行。

---

## 23.2 Version Number

创建版本前：

```sql
SELECT *
FROM meeting_minutes
WHERE id = :minutes_id
FOR UPDATE;
```

版本号：

```text
MAX(version_no) + 1
```

在事务内计算。

---

# 24. 删除策略

V1 以审计和可追溯为优先。

## 24.1 User

默认不物理删除。

使用：

```text
status = DISABLED
```

## 24.2 Meeting

V1 管理后台默认不提供删除会议能力。

如后续增加删除，应由管理员操作并审计。

## 24.3 Minute Versions

不允许删除历史 Version。

## 24.4 Audit Logs

不允许业务用户删除。

---

# 25. 数据保留策略

V1 暂不写死保留周期。

默认保存：

- meetings；
- transcript_segments；
- minute_versions；
- action items；
- webhook_events；
- audit_logs。

后续由公司安全策略确定：

```text
30 days
90 days
180 days
1 year
```

代码层需支持后续增加定时清理任务。

---

# 26. 数据库索引重点

重点查询：

## 26.1 我的会议

```text
creator_user_id
participant user_id
permission user_id
start_time
```

## 26.2 会议详情

```text
tencent_meeting_id
meeting_id
```

## 26.3 Transcript

```text
meeting_id + sequence_no
```

## 26.4 任务后台

```text
status + created_at
```

## 26.5 通知

```text
user_id + is_read + created_at
```

## 26.6 审计日志

```text
user_id + created_at
resource_type + resource_id
action + created_at
```

---

# 27. 避免 N+1

ORM 查询要求：

会议详情加载：

```text
meeting
participants
recordings
```

使用：

```text
selectinload / joinedload
```

会议列表禁止为每条会议单独查询：

- 主持人；
- AI 状态；
- 权限。

---

# 28. Repository 层规范

推荐 Repository：

```text
UserRepository
MeetingRepository
ParticipantRepository
RecordingRepository
TranscriptRepository
MinutesRepository
PermissionRepository
NotificationRepository
AuditRepository
TaskRepository
```

API Controller 不允许直接编写复杂 SQL。

---

# 29. Alembic Migration 规划

建议初始 Migration 拆分：

```text
0001_create_users
0002_create_meetings_and_participants
0003_create_recordings_and_transcripts
0004_create_minutes_and_versions
0005_create_permissions_notifications
0006_create_webhooks_tasks_audit
0007_create_system_settings
0008_add_current_version_fk
```

Migration 必须：

- 可重复部署；
- 禁止直接修改已发布 Migration；
- 新需求新增 Migration；
- Production 禁止手动改表绕过 Alembic。

---

# 30. 初始化数据

第一次部署建议创建管理员。

通过 CLI：

```bash
python -m app.scripts.create_admin
```

而不是在数据库写死：

```text
admin / 123456
```

---

# 31. 数据库备份建议

中小公司 V1 最低要求：

```text
每日自动备份
+
保留最近 7~30 天
```

生产环境建议：

- 开启 binlog；
- 定期验证恢复能力。

---

# 32. V1 数据库验收清单

- [ ] 所有表通过 Alembic 创建；
- [ ] users.username 唯一；
- [ ] meetings.tencent_meeting_id 唯一；
- [ ] recording 文件具有联合唯一约束；
- [ ] transcript 支持稳定排序；
- [ ] meeting 与 minutes 一对一；
- [ ] minutes 支持多版本；
- [ ] AI Version 不会被人工编辑覆盖；
- [ ] TODO 独立落表；
- [ ] 主动授权使用 meeting_permissions；
- [ ] Webhook 存在唯一幂等键；
- [ ] Async Task 可追踪；
- [ ] Admin 敏感操作写 audit_logs；
- [ ] 系统配置与 Secret 分离；
- [ ] Refresh Token 可在 Redis 失效；
- [ ] 关键查询均存在索引；
- [ ] 删除会议可正确级联业务数据；
- [ ] 数据库全部使用 utf8mb4；
- [ ] 时间统一使用 UTC。

---

# 33. 后续扩展

## V1.1 Evidence

增加：

```text
minute_evidences
```

字段可包括：

```text
minute_version_id
item_type
item_index
transcript_segment_id
start_ms
end_ms
```

用于：

```text
点击会议结论
      ↓
定位原始逐字稿
```

## V2 TODO 管理

`minute_action_items` 可扩展：

```text
assignee_status
external_task_id
external_system
completed_at
```

## V3 RAG

新增独立 Embedding / Vector Store。

不修改当前 MySQL 核心业务数据模型。

---

# 34. 结论

V1 数据库围绕四条核心数据链设计：

```text
User → Meeting → Transcript

Meeting → Minutes → Version

Meeting → Permission → User

Webhook → Async Task → AI Processing
```

设计重点不是追求复杂度，而是：

```text
数据一致性
版本可追溯
权限可验证
任务可恢复
Webhook 可幂等
后续可扩展
```
