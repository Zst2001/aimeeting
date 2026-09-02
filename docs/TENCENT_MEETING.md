# AI 智能会议纪要系统 TENCENT_MEETING.md

> 文档类型：Tencent Meeting Integration Design  
> 版本：v1.0  
> 对应文档：`PRD.md` / `SPEC.md` / `DATABASE.md` / `API.md`  
> 接入对象：腾讯会议企业级自建应用  
> 更新时间：2026-09-02

---

# 1. 文档目的

本文档定义 AI 智能会议纪要系统 V1 与腾讯会议的集成规范，主要解决：

- 公司需要开通哪些腾讯会议能力；
- 为什么使用企业级自建应用；
- REST API 与 Webhook 如何配合；
- 如何同步会议、录制和转写；
- Webhook 如何验签、解码和保证幂等；
- 如何将腾讯会议返回结构映射为内部 Domain Model；
- 如何处理录制或转写尚未完成；
- 如何进行失败重试与补偿；
- 哪些第三方字段禁止直接渗透业务层。

本文档不负责：

- AI 摘要 Prompt；
- LLM 调用；
- 内部用户 JWT；
- 前端页面实现。

---

# 2. V1 接入结论

V1 采用：

```text
腾讯会议企业级自建应用
        +
REST API
        +
Webhook
```

不采用：

```text
腾讯会议音视频 SDK
腾讯会议客户端嵌入式会议能力
腾讯会议 MCP 作为生产核心接入
OAuth 第三方应用
自建实时音视频采集
```

原因：

V1 不负责创建音视频会议能力，也不要求在公司 Web 内直接开会。

员工继续使用腾讯会议客户端：

```text
腾讯会议正常创建 / 参加会议
             ↓
公司系统同步会议数据
             ↓
主持人在公司系统开启 AI 会议纪要
             ↓
会议结束后处理录制和逐字稿
```

---

# 3. 腾讯会议企业账户前置条件

正式联调前，公司需要具备腾讯会议商业版或企业版等支持企业开放 API 的版本。

管理员需要完成：

1. 创建企业自建应用；
2. 应用类型选择企业级；
3. 获取应用凭证；
4. 启用应用；
5. 配置事件订阅；
6. 配置云录制能力；
7. 配置录制转写；
8. 确认需要的企业成员均拥有腾讯会议企业用户标识。

---

# 4. 为什么使用企业级自建应用

业务要求：

> 即使员工直接在腾讯会议 App 中创建会议，公司系统仍然需要读取这些会议的数据。

因此选择企业级自建应用。

目标能力：

```text
企业账户下会议
    ↓
无论通过
腾讯会议 App
REST API
其他企业级来源
创建
    ↓
企业级应用可以进行统一数据接入
```

V1 不选择应用级自建应用，因为应用级应用的数据范围更适合“仅处理由该应用自身创建的数据”的场景。

---

# 5. 凭证管理

需要配置的腾讯会议应用参数以实际企业控制台为准，通常包括：

```text
AppID
SDKID
SecretID
SecretKey
Webhook Token
EncodingAESKey（若控制台要求）
```

配置示例：

```env
TENCENT_MEETING_BASE_URL=https://api.meeting.qq.com

TENCENT_MEETING_APP_ID=
TENCENT_MEETING_SDK_ID=
TENCENT_MEETING_SECRET_ID=
TENCENT_MEETING_SECRET_KEY=

TENCENT_MEETING_WEBHOOK_TOKEN=
TENCENT_MEETING_ENCODING_AES_KEY=
```

规则：

- 不提交 Git；
- 不写入前端；
- 不返回普通业务 API；
- 不写入普通日志；
- 生产环境优先 Secret Manager / Docker Secret。

---

# 6. REST API 鉴权策略

企业自建应用使用腾讯会议企业内部应用鉴权方式。

当前接口调用会涉及官方要求的请求头，例如：

```text
X-TC-Key
X-TC-Timestamp
X-TC-Nonce
X-TC-Signature
X-TC-Registered
AppId
SdkId
```

实际字段、签名算法、参与签名的数据必须以联调时腾讯会议官方“企业内部应用鉴权 / 服务端 API 调试工具”当前规范为准。

## 6.1 代码原则

禁止：

```python
# service 中直接拼腾讯签名
```

统一：

```text
TencentMeetingClient
        ↓
TencentMeetingAuth
        ↓
HTTPX
```

建议接口：

```python
class TencentMeetingAuth:
    def build_headers(
        self,
        method: str,
        path: str,
        query: dict,
        body: dict | None
    ) -> dict:
        ...
```

业务 Service 不关心：

- Secret；
- Nonce；
- Timestamp；
- Signature。

---

# 7. TencentMeetingClient

目录：

```text
app/integrations/tencent_meeting/
│
├── client.py
├── auth.py
├── webhook.py
├── schemas.py
├── mapper.py
├── constants.py
└── exceptions.py
```

推荐抽象：

```python
class TencentMeetingClient:

    async def get_meeting(self, ...):
        ...

    async def get_ended_meetings(self, ...):
        ...

    async def get_recordings(self, ...):
        ...

    async def get_recording_detail(self, ...):
        ...

    async def get_transcript_paragraphs(self, ...):
        ...

    async def get_transcript_details(self, ...):
        ...
```

所有 REST 请求统一处理：

- Auth；
- Timeout；
- Retryable Error；
- JSON Decode；
- 腾讯错误码；
- Request Logging；
- Response Mapping。

---

# 8. V1 需要的腾讯会议能力

## 8.1 获取会议详情

用途：

- 同步会议名称；
- Meeting ID；
- Meeting Code；
- 主持人；
- 开始时间；
- 结束时间；
- 腾讯会议状态。

典型官方接口：

```text
GET /v1/meetings/{meetingId}
```

系统内部调用：

```text
TencentMeetingClient.get_meeting()
```

---

# 9. 获取已结束会议

V1 需要能够补偿发现 Webhook 漏掉或系统停机期间结束的会议。

可使用企业账户级已结束会议查询能力。

目的：

```text
Scheduled Compensation
        ↓
查询一段时间内已结束会议
        ↓
与内部 meetings 对比
        ↓
Upsert
```

注意：

- 该类账户级仪表盘 API 可能存在较低调用频率限制；
- 补偿任务应低频执行；
- V1 建议每 15~30 分钟一次，而不是高频轮询。

---

# 10. 参会者数据

系统需要的不是“受邀成员”本身，而是用于权限判定的“实际参会者”。

实现时应优先使用腾讯会议能够提供实际参会成员信息的接口/企业数据能力。

如果首期联调中 API 权限只能稳定获得：

```text
会议主持人
+
受邀成员
```

不得直接将“受邀成员”永久等同于“实际参会者”。

应在代码中区分：

```text
INVITEE
ACTUAL_PARTICIPANT
```

最终 `meeting_participants` 应尽量写入实际参加过会议的内部用户。

## 10.1 用户映射

腾讯会议：

```text
userid
```

映射：

```text
users.tencent_userid
```

查找：

```text
Tencent userid
       ↓
UserRepository.get_by_tencent_userid()
       ↓
internal user_id
```

匹配不到：

```text
user_id = NULL
is_internal = false
```

不得因为姓名相同自动绑定账户。

---

# 11. 云录制是 V1 AI 纪要前置条件

V1 不采集实时音频。

因此会议总结的数据源为：

```text
Tencent Cloud Recording
        ↓
Recording Transcript
```

AI 纪要生成前置条件：

```text
ai_minutes_enabled = true
AND
meeting ended
AND
cloud recording exists
AND
transcript ready
```

如果主持人没有云录制：

```text
WAITING_RECORDING
```

达到业务超时时间后：

```text
FAILED / NO_RECORDING
```

V1 的数据库状态暂可统一表现为：

```text
FAILED
```

错误原因保存在任务/日志中。

---

# 12. 录制转写配置建议

为了保证自动纪要链路稳定，建议企业管理员在腾讯会议企业设置中统一配置：

```text
云录制
+
同时开启录制转写
```

而不是依赖每位主持人在会后手动生成逐字稿。

如果公司不希望所有会议自动转写，可仍保持：

```text
只有主持人开启公司 AI 纪要
+
主持人自行确保本次会议开启云录制/录制转写
```

但产品应明确提示。

---

# 13. 查询录制列表

腾讯会议录制列表接口可按：

- userid；
- meeting_id；
- meeting_code；
- 时间区间；

查询。

典型接口：

```text
GET /v1/records
```

系统：

```python
await client.get_recordings(
    meeting_id=...,
    ...
)
```

内部保存：

```text
meeting_recordings

meeting_id
record_file_id
recording_status
transcript_status
record_start_time
record_end_time
```

---

# 14. recording.completed

V1 重点订阅：

```text
recording.completed
```

它表示：

> 会议云录制已完成转码。

事件中可获得录制文件信息，包括 `record_file_id`。

推荐链路：

```text
recording.completed
        ↓
Webhook 验证
        ↓
保存 webhook_events
        ↓
异步任务 FETCH_RECORDING
        ↓
Upsert meeting_recordings
        ↓
进入 WAITING_TRANSCRIPT
```

注意：

```text
recording.completed
```

不等价于：

```text
Transcript 一定已经可读取
```

因此不能立即假设逐字稿就绪。

---

# 15. 录制详情

录制详情能力可用于获取：

- 视频播放/下载信息；
- 音频地址；
- 转写文件信息。

V1 原则：

> 不下载视频和音频用于 AI。

AI 只需要：

```text
Transcript Text
```

因此：

- 不持久化视频；
- 不持久化音频；
- 不把视频/音频发送给百炼；
- 仅在排障或未来 ASR 备用方案时考虑音频地址。

---

# 16. 查询转写段落

腾讯会议提供转写段落信息查询能力。

典型接口：

```text
GET /v1/records/transcripts/paragraphs
```

用途：

- 判断是否存在转写；
- 获取段落总数；
- 获取可继续查询的 pid 信息；
- 为大段 Transcript 分页拉取做准备。

---

# 17. 查询录制转写详情

核心接口：

```text
GET /v1/records/transcripts/details
```

关键参数：

```text
meeting_id
record_file_id
operator_id
operator_id_type
pid
limit
```

其中企业用户：

```text
operator_id_type = 1
```

具体值联调时以官方文档为准。

返回核心内容包括：

```text
paragraphs
pid
start_time
end_time
speaker_info
sentences / words
text
more
```

---

# 18. Transcript 拉取策略

不能假设一次请求永远返回完整 Transcript。

推荐：

```text
pid = None
segments = []

loop:
    response = get_transcript_details(pid, limit)
    append response.paragraphs

    if response.more == false:
        break

    pid = next_pid
```

注意：

具体 next pid 获取方式应按照腾讯会议接口实际返回结构实现。

Client 层负责分页。

Service 层调用：

```python
paragraphs = await client.get_full_transcript(...)
```

业务层不处理腾讯分页协议。

---

# 19. Transcript Mapper

腾讯数据：

```text
Tencent Paragraph
```

必须经过：

```text
TencentTranscriptMapper
```

转换：

```python
@dataclass
class TranscriptSegmentDTO:
    provider_segment_id: str | None
    speaker_external_id: str | None
    speaker_name: str
    start_ms: int
    end_ms: int
    text: str
    sequence_no: int
```

然后保存 `transcript_segments`。

---

# 20. 文本拼接规则

腾讯转写可能按照：

```text
Paragraph
 └── Sentence
      └── Word
```

多层返回。

Mapper 统一生成：

```text
一个逻辑 Segment 对应一个腾讯 Paragraph
```

文本：

```text
paragraph_text =
    按顺序拼接 paragraph 下 sentence/word 文本
```

禁止：

- 任意改写；
- AI 清洗；
- 修正语义；
- 删除内容。

原始 Transcript 标准化只做格式整理。

---

# 21. Speaker 映射

如果腾讯返回：

```text
speaker_info.userid
speaker_info.username
```

执行：

```text
userid
  ↓
users.tencent_userid
  ↓
speaker_user_id
```

找不到：

```text
speaker_user_id = NULL
speaker_name = 腾讯原名称
```

Speaker Name 不应作为唯一身份依据。

---

# 22. Webhook Endpoint

系统公开接口：

```text
GET  /api/v1/integrations/tencent-meeting/webhook
POST /api/v1/integrations/tencent-meeting/webhook
```

GET：

```text
腾讯会议配置事件订阅时验证 URL
```

POST：

```text
正式接收事件
```

---

# 23. Webhook GET 验证

腾讯会议配置 Callback URL 时会发送 GET 验证请求。

请求包含类似：

```text
check_str
```

以及 Header：

```text
timestamp
nonce
signature
```

处理：

```text
Receive GET
    ↓
URL Decode
    ↓
Verify Signature
    ↓
Base64 Decode check_str
    ↓
3 秒内返回明文
```

Response：

```text
只返回解码后的明文字符串
```

不要增加：

- JSON；
- 引号；
- 换行；
- HTML。

---

# 24. Webhook POST 验证

POST Body：

```json
{
  "data": "<base64 encoded event>"
}
```

Header：

```text
timestamp
nonce
signature
```

处理：

```text
Read Raw data
    ↓
Verify Signature
    ↓
Base64 Decode data
    ↓
JSON Parse
    ↓
Extract event / trace_id / payload
```

签名当前官方规则应封装在：

```text
TencentWebhookVerifier
```

V1 代码禁止在 Router 中手写签名算法。

---

# 25. Webhook Signature

当前腾讯会议回调签名逻辑的核心形式为：

```text
sha1(sort(token, timestamp, nonce, data))
```

GET URL 验证时参与签名的数据为对应验证字符串。

实际实现必须通过腾讯会议官方调试工具/官方示例进行联调验证。

建议：

```python
class TencentWebhookVerifier:
    def verify(
        self,
        timestamp: str,
        nonce: str,
        data: str,
        signature: str
    ) -> bool:
        ...
```

比较签名时建议使用恒定时间比较函数。

---

# 26. Webhook 成功响应

正式 POST 回调处理成功后，应按腾讯会议当前回调协议返回成功字符串：

```text
successfully received callback
```

并确保：

```text
HTTP 200
```

Webhook Handler 需要快速返回。

不得在 Handler 中执行：

```text
拉取完整 Transcript
调用 Qwen
生成纪要
发送通知
```

---

# 27. Webhook 超时和重试

腾讯会议在回调服务未及时正确响应时会重试。

因此必须假设：

```text
同一事件可能收到多次
```

不能以：

```text
“腾讯只会发一次”
```

作为系统设计前提。

---

# 28. Webhook 幂等

解码事件后获取：

```text
trace_id
```

写入：

```text
webhook_events
```

唯一键：

```text
(provider, trace_id)
```

流程：

```text
POST
 ↓
Verify
 ↓
Decode
 ↓
INSERT webhook_events
 ↓
Duplicate?
 ┌──┴──┐
Yes   No
 │     │
Return Create Celery Task
200    │
       ▼
      Return 200
```

重复事件不再次创建业务任务。

---

# 29. 事件订阅建议

V1 至少关注：

```text
meeting.created
meeting.updated
meeting.canceled
meeting.started
meeting.end
recording.completed
```

其中会议纪要主链路最重要：

```text
meeting.end
recording.completed
```

如果腾讯会议控制台提供独立的“转写完成”类事件且企业账号可订阅，联调时优先订阅。

但系统不可依赖“必须存在转写完成 Webhook”。

V1 必须保留：

```text
recording.completed
        ↓
Worker 查询 transcript
        ↓
未就绪则 Retry
```

作为稳定基线。

---

# 30. meeting.end 处理

收到：

```text
meeting.end
```

执行：

```text
Sync Meeting
        ↓
meeting_status = ENDED
```

如果：

```text
ai_minutes_enabled = false
```

结束。

如果：

```text
ai_minutes_enabled = true
```

设置：

```text
minutes_status = WAITING_RECORDING
```

创建：

```text
FETCH_RECORDING
```

异步任务。

---

# 31. recording.completed 处理

收到：

```text
recording.completed
```

提取：

```text
record_file_id
```

Upsert：

```text
meeting_recordings
```

如果对应 Meeting：

```text
ai_minutes_enabled = true
```

则：

```text
WAITING_TRANSCRIPT
```

创建：

```text
FETCH_TRANSCRIPT
```

---

# 32. FETCH_TRANSCRIPT

任务流程：

```text
Load Meeting
    ↓
Check AI Enabled
    ↓
Load Recording
    ↓
Call Tencent Transcript API
    ↓
Transcript Ready?
 ┌─────┴─────┐
No          Yes
│            │
Retry      Map DTO
             ↓
         DB Transaction
             ↓
       transcript_status=READY
             ↓
       GENERATE_MINUTES
```

---

# 33. Transcript 未就绪

未就绪属于：

```text
Expected Temporary State
```

不是立即业务失败。

建议重试：

```text
1 min
5 min
15 min
30 min
60 min
```

达到配置上限后：

```text
meeting.minutes_status = FAILED
async_tasks.status = FAILED
```

并记录：

```text
TRANSCRIPT_NOT_READY_TIMEOUT
```

---

# 34. 录制不存在

如果会议已经结束但未发现云录制：

第一次：

```text
WAITING_RECORDING
```

异步查询若干次。

建议：

```text
1m → 5m → 15m → 30m
```

仍无录制：

```text
FAILED
```

前端显示：

> 未检测到腾讯会议云录制，无法生成 AI 会议纪要。

---

# 35. 补偿同步机制

Webhook 不作为唯一数据来源。

增加 Celery Beat / Scheduler：

```text
sync_recent_ended_meetings
```

建议：

```text
每 15~30 分钟
```

查询：

```text
最近 N 小时 / 当天
已结束会议
```

进行 Upsert。

用途：

- 服务短暂宕机；
- Webhook 配置故障；
- 腾讯回调重试耗尽；
- 数据库临时不可用。

---

# 36. 会议 Sync Upsert

外部唯一键：

```text
tencent_meeting_id
```

同步：

```text
不存在 → INSERT
存在 → UPDATE mutable fields
```

禁止根据：

```text
meeting_code
subject
```

判断是否同一会议。

---

# 37. Recording Upsert

唯一：

```text
meeting_id + record_file_id
```

重复：

```text
UPDATE status
```

不得重复创建。

---

# 38. Transcript Upsert

优先：

```text
recording_id + provider_segment_id
```

如果腾讯侧段落 ID 稳定：

```text
UPSERT
```

如果联调确认段落 ID 可能变化：

```text
Transaction
 ↓
Delete recording segments
 ↓
Bulk insert current transcript
```

两种方案只能选一种，联调后固化。

---

# 39. 腾讯 API Timeout

HTTPX 建议：

```text
connect timeout: 5s
read timeout: 20~30s
```

转写大响应可单独提高。

具体通过配置：

```env
TENCENT_MEETING_CONNECT_TIMEOUT=5
TENCENT_MEETING_READ_TIMEOUT=30
```

---

# 40. 腾讯 API Retry

Client 层只重试：

```text
网络连接异常
Timeout
429
部分 5xx
```

不自动重试：

```text
鉴权错误
参数错误
权限错误
明确的资源不存在
```

业务层对：

```text
录制尚未生成
转写尚未生成
```

采用 Celery 延迟重试，而不是 HTTP Client 瞬时重试。

---

# 41. 错误映射

定义：

```text
TencentMeetingAuthError
TencentMeetingPermissionError
TencentMeetingRateLimitError
TencentMeetingNotFoundError
TencentMeetingTemporaryError
TencentMeetingInvalidResponseError
```

映射内部：

```text
60001 腾讯会议 API 调用失败
60002 腾讯会议鉴权失败
60003 Webhook 验证失败
60004 录制尚未准备完成
```

---

# 42. 日志

REST 请求日志：

```text
provider=tencent_meeting
operation=get_transcript
meeting_id=...
record_file_id=...
duration_ms=...
status=success/error
request_id=...
```

禁止记录：

```text
SecretKey
完整 Signature
完整 Transcript
录制下载地址长期明文
```

---

# 43. 腾讯会议 API 限流

所有 Client 代码必须对：

```text
HTTP 429
官方业务限流错误
```

进行识别。

账户级重型接口必须低频调用。

V1 不做高并发请求。

建议：

```text
Celery Queue:
tencent_meeting_io
```

限制 Worker 并发数量，例如：

```text
2~4
```

后续根据企业 API 限额调整。

---

# 44. Operator ID

多项录制/转写 API 需要：

```text
operator_id
operator_id_type
```

V1 推荐优先使用：

```text
会议创建者 / 企业内部注册用户 userid
```

并在 `TencentMeetingClient` 内部统一决定。

禁止 Controller 自己传不同 Operator 策略。

推荐：

```python
operator = operator_resolver.resolve(meeting)
```

---

# 45. API 调试流程

正式开发前先使用腾讯会议服务端 API 调试工具完成：

```text
Step 1
验证企业级应用凭证

Step 2
成功查询一个测试会议

Step 3
成功开启一次测试云录制

Step 4
成功查询录制列表

Step 5
成功拿到 record_file_id

Step 6
成功查询 transcript paragraphs

Step 7
成功查询 transcript details

Step 8
配置 Webhook GET URL 校验

Step 9
验证 meeting.end

Step 10
验证 recording.completed
```

只有以上链路打通后再接 Celery 自动化。

---

# 46. 本地开发 Webhook

腾讯会议 Callback URL 需要可被腾讯服务器访问。

本地开发可使用公司允许的临时公网隧道工具。

生产：

```text
https://meeting-ai.company.com/api/v1/integrations/tencent-meeting/webhook
```

必须：

```text
HTTPS
```

并通过 Nginx 反代 FastAPI。

---

# 47. 防火墙

如果公司服务器启用了入站 IP 白名单：

> 必须根据腾讯会议官方最新 Webhook 源 IP 文档配置放行。

不要把 IP 段硬编码进业务程序。

由基础设施配置管理。

---

# 48. 安全边界

腾讯会议层拿到的数据属于公司敏感会议数据。

必须：

```text
Tencent API
  ↓
Backend only
```

前端绝不能：

```text
直接调用 api.meeting.qq.com
```

前端只访问内部：

```text
/api/v1/...
```

---

# 49. V1 不做腾讯智能纪要直出

腾讯会议自身可能提供智能纪要能力。

本项目 V1 仍然选择：

```text
Tencent Transcript
        ↓
Our LLM Pipeline
```

原因：

- 公司需要自定义输出结构；
- 需要统一版本管理；
- 需要后续更换 LLM；
- 需要人工编辑；
- 需要内部 TODO 数据结构；
- 需要公司自己的权限与审计。

腾讯智能纪要可作为：

```text
未来质量对比
```

而不是 V1 核心数据源。

---

# 50. Integration Sequence

完整主链：

```text
Tencent Meeting
       │
       │ meeting.end
       ▼
Webhook Endpoint
       │
       ├── Verify
       ├── Decode
       ├── Idempotency
       └── Save Event
       │
       ▼
Celery
FETCH_RECORDING
       │
       ▼
Tencent REST API
       │
       ▼
meeting_recordings
       │
       │ recording.completed
       ▼
FETCH_TRANSCRIPT
       │
       ▼
Tencent Transcript API
       │
       ▼
Transcript Mapper
       │
       ▼
transcript_segments
       │
       ▼
GENERATE_MINUTES
```

---

# 51. 联调验收清单

## Application

- [ ] 公司腾讯会议版本具备企业 API 能力；
- [ ] 创建企业级自建应用；
- [ ] AppID / SDKID / SecretID / SecretKey 可用；
- [ ] Secret 未进入 Git。

## REST API

- [ ] 可以查询会议；
- [ ] 可以查询已结束会议；
- [ ] 可以查询录制列表；
- [ ] 可以拿到 record_file_id；
- [ ] 可以查询转写段落；
- [ ] 可以拉取完整转写；
- [ ] 多页 Transcript 可以完整获取。

## Webhook

- [ ] GET URL 校验通过；
- [ ] POST 签名校验通过；
- [ ] Base64 解码正确；
- [ ] trace_id 正确提取；
- [ ] 重复事件不会重复执行；
- [ ] meeting.end 正常处理；
- [ ] recording.completed 正常处理；
- [ ] 5 秒内正确返回 Callback 成功响应。

## Database

- [ ] Meeting Upsert 幂等；
- [ ] Recording Upsert 幂等；
- [ ] Transcript Segment 顺序正确；
- [ ] Speaker 映射正确；
- [ ] 外部参会者 user_id 可为 NULL。

## Async

- [ ] Transcript 未就绪自动重试；
- [ ] 无录制能够进入异常状态；
- [ ] 腾讯 API 暂时异常可恢复；
- [ ] 最终成功触发 GENERATE_MINUTES。

---

# 52. 后续扩展

V1.1：

```text
腾讯转写搜索
原文 Evidence
录制定位
```

V2：

```text
更多会议平台 Adapter
```

可扩展：

```text
MeetingProvider

TencentMeetingProvider
TeamsProvider
ZoomProvider
FeishuProvider
```

内部 Transcript 与 Minutes 业务无需改变。

---

# 53. 最终结论

腾讯会议接入层只负责：

```text
会议事实
录制事实
转写事实
Speaker
时间轴
```

禁止让腾讯会议原始数据结构直接进入：

```text
MinutesService
LLMProvider
Frontend
```

统一边界：

```text
Tencent REST / Webhook
        ↓
TencentMeeting Adapter
        ↓
Internal Domain Model
        ↓
Meeting / Transcript Service
```

V1 的稳定性核心是：

```text
Webhook Event Driven
+
REST State Verification
+
Celery Retry
+
Scheduled Compensation
+
Database Idempotency
```
