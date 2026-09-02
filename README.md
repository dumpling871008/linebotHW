# RAG 個人履歷 AI 問答助手

一套整合 LINE Official Account、Astro 個人網站、Flask、LlamaIndex、Gemini 與 Firestore 的 AI 求職助理。

使用者可以詢問林君璇的經歷、技能、求職方向與專案內容。系統先從公開 Markdown 知識庫檢索相關片段，再由 Gemini 依回答政策產生有來源的回答；遇到資料不足、隱私資訊或需要本人承諾的問題時，系統不自行猜測，而是轉為 `HANDOFF` 並保存至 Firestore，供本人從後台確認。

目前本機版本包含 135 個 RAG 知識節點，完整後端測試為 76 項。

## 核心功能

- LINE Webhook、signature 驗證與 LINE Profile API。
- 網站 `POST /api/chat`，與 LINE 共用 `CareerBotService`。
- Markdown 知識庫、LlamaIndex 向量檢索與持久化索引。
- Gemini 結構化輸出與 `ANSWER`、`HANDOFF`、`OUT_OF_SCOPE` 三段式分流。
- 回答來源白名單驗證；無有效來源時強制轉為 `HANDOFF`。
- `HANDOFF` 問題保存至 Firestore `unknown_questions`。
- 所有有效問答以 best-effort 方式保存至 `chat_logs`。
- 網站 AI 回答包含來源 ID，前端可顯示對應站內連結。
- 私人留言 `POST /api/messages`、Cloudflare Turnstile、honeypot 與 Firestore 限流。
- `/api/chat` 伺服器端限流，使用 Firestore transaction 跨 Cloud Run instance 共用計數。
- Flask CORS origin 白名單、Docker、Gunicorn 與 Cloud Run 設定。

## 系統架構

```text
LINE Official Account ── POST /callback ─┐
                                         │
Astro / Cloudflare ──── POST /api/chat ──┼── Flask / Cloud Run
                                         │          │
                                         │     ChatRateLimiter
                                         │          └── Firestore chat_rate_limits
                                         │
                                         └── CareerBotService
                                                    │
                                              QuestionRouter
                                              ┌─────┴─────┐
                                              │           │
                                        LlamaIndex      Gemini
                                              │        Vertex AI
                                      storage/rag_index  │
                                              │           │
                                         Markdown ────────┘
                                              │
                                  ANSWER / HANDOFF / OUT_OF_SCOPE
                                              │
                                  ┌───────────┴────────────┐
                                  │                        │
                           Firestore chat_logs    unknown_questions

Astro Contact ─────── POST /api/messages ── WebsiteMessageService
                                               │
                                      Turnstile + validation
                                               │
                                Firestore website_messages
```

## 回答流程

1. 使用者從 LINE 或網站輸入問題。
2. 網站請求先經過伺服器端輸入驗證與每 IP 限流。
3. `RagService` 使用問題的 embedding 從持久化索引取回最相關的 5 個片段。
4. `QuestionRouter` 將回答政策、問題與檢索內容交給 Gemini。
5. Gemini 依 schema 回傳回答、route、原因與來源 ID。
6. 後端只接受存在於本次檢索結果的來源 ID。
7. `ANSWER` 回傳有依據的回答；`OUT_OF_SCOPE` 限制非求職問題；`HANDOFF` 使用固定文字並寫入待處理集合。
8. 完成的問答會嘗試寫入 `chat_logs`；紀錄失敗不會覆蓋原本回答。

## 技術棧

| 類別 | 技術 |
|---|---|
| API | Python 3.13、Flask、Gunicorn、Flask-CORS |
| AI／RAG | Gemini、Google GenAI Embedding、LlamaIndex |
| 儲存 | Firestore、LlamaIndex persisted storage |
| LINE | LINE Bot SDK v3、Messaging API、Profile API |
| 防濫用 | Firestore transaction、HMAC、Cloudflare Turnstile |
| 部署 | Docker、GCP Cloud Run、Cloudflare Workers／Wrangler |
| 測試 | pytest、Flask test client、mocked cloud services |

## 專案結構

```text
.
├── app.py                         # Flask 入口、LINE callback 與網站 API
├── career_bot_service.py          # LINE／網站共用的問答協調層
├── question_router.py             # RAG + Gemini 分流與來源驗證
├── rag_service.py                 # 向量索引載入、建立與檢索
├── knowledge_base_loader.py       # Markdown 載入、切片與 source ID
├── chat_rate_limiter.py           # 網站 AI 的 Firestore 共用限流
├── website_message_service.py     # 私人留言、Turnstile 與留言限流
├── unknown_question_repository.py # HANDOFF 待處理紀錄
├── chat_log_repository.py         # 一般問答與安全錯誤紀錄
├── evaluate_retrieval.py          # 檢索品質批次評估
├── knowledge_base/                # 公開知識、回答政策與 manifest
├── storage/rag_index/             # Cloud Run 執行時載入的持久化索引
├── tests/                         # 單元與 API 測試
├── docs/                          # 詳細報告與設計文件
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 本機環境

### 前置需求

- Python 3.13
- Google Cloud 專案與 Application Default Credentials
- Vertex AI API
- Firestore database
- LINE Messaging API channel
- Cloudflare Turnstile widget（若要測試私人留言）

### 1. 安裝依賴

使用 uv：

```powershell
uv sync --dev
```

或使用既有虛擬環境與 pip：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest
```

### 2. 建立環境設定

```powershell
Copy-Item .env.example .env
```

填入自己的 GCP、LINE、CORS 與 Turnstile 設定。`.env` 已被 Git 與 Docker 排除，不要提交任何 secret 或 credentials JSON。

本機呼叫 Vertex AI／Firestore 時，可使用：

```powershell
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 3. 啟動 Flask

```powershell
.venv\Scripts\python.exe app.py
```

服務預設監聽：

```text
http://localhost:8080
```

目前 `app.py` 在 import 時即要求 `LINE_CHANNEL_SECRET` 與 `LINE_CHANNEL_ACCESS_TOKEN`，即使只測試網站 API，也必須提供這兩個變數。

## 環境變數

### 核心設定

| 變數 | 必要性 | 說明 |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | 必要 | Vertex AI 與 Firestore 使用的 GCP project ID。 |
| `GOOGLE_CLOUD_LOCATION` | 選填 | 預設 `global`。 |
| `GEMINI_MODEL` | 選填 | 預設 `gemini-3.7-flash`。 |
| `LINE_CHANNEL_SECRET` | 必要 | 驗證 LINE webhook signature；也可作為 Chat HMAC secret 的相容 fallback。 |
| `LINE_CHANNEL_ACCESS_TOKEN` | 必要 | LINE Messaging API 回覆訊息。 |
| `CORS_ALLOWED_ORIGINS` | 必要於網站 | 逗號分隔，例如 `http://localhost:4321,https://example.com`；不可使用 `*`。 |
| `PORT` | 選填 | Flask／Cloud Run port，預設 `8080`。 |

### Firestore 集合

| 變數 | 預設值 |
|---|---|
| `FIRESTORE_UNKNOWN_QUESTION_COLLECTION` | `unknown_questions` |
| `FIRESTORE_CHAT_LOG_COLLECTION` | `chat_logs` |
| `FIRESTORE_WEBSITE_MESSAGE_COLLECTION` | `website_messages` |
| `FIRESTORE_MESSAGE_RATE_LIMIT_COLLECTION` | `website_message_rate_limits` |
| `FIRESTORE_CHAT_RATE_LIMIT_COLLECTION` | `chat_rate_limits` |

### 限流與 Turnstile

| 變數 | 必要性 | 說明 |
|---|---|---|
| `CHAT_RATE_LIMIT_PER_HOUR` | 選填 | 網站 AI 每 IP、每 UTC 固定小時的配額，預設 `20`。 |
| `CHAT_RATE_LIMIT_HASH_SECRET` | 正式環境建議必要 | HMAC IP 的 server-only secret；未設定時沿用 LINE secret。 |
| `WEBSITE_MESSAGE_RATE_LIMIT` | 選填 | 私人留言每小時上限，預設 `5`。 |
| `TURNSTILE_SECRET_KEY` | 留言功能必要 | 只能放在後端，不能使用 `PUBLIC_` 前綴。 |
| `TURNSTILE_ALLOWED_HOSTNAMES` | 選填 | 逗號分隔；未設定時由 CORS origins 推導。 |

完整範例請參考 [.env.example](.env.example)。

## API

### 健康檢查

```http
GET /
```

### 網站 AI 問答

```http
POST /api/chat
Content-Type: application/json

{
  "question": "她在 SEER 專案負責什麼？"
}
```

成功回應：

```json
{
  "response": "回答內容",
  "route": "ANSWER",
  "source_ids": ["projects.05_seer.008"]
}
```

主要狀態碼：

- `200`：`ANSWER`、`HANDOFF` 或 `OUT_OF_SCOPE` 處理完成。
- `400`：JSON 或問題格式不正確。
- `429`：同一訪客超過每小時配額，並附 `Retry-After`。
- `503`：限流、RAG、Gemini 或必要 Firestore 流程不可用。
- `204`：瀏覽器 OPTIONS preflight。

PowerShell 測試：

```powershell
$body = @{ question = "她在 SEER 專案負責什麼？" } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8080/api/chat" `
  -ContentType "application/json" `
  -Body $body
```

### 私人留言

```http
POST /api/messages
Content-Type: application/json
```

包含 `name`、`email`、`topic`、`message`、honeypot `website` 與 `turnstile_token`。Turnstile token 應由真實網站 widget 取得，不適合硬寫成固定測試值。

### LINE Webhook

```http
POST /callback
X-Line-Signature: ...
```

LINE Developer Console 的 webhook URL 必須指向 Cloud Run 正式網址加上 `/callback`，不能只填服務根網址。

## RAG 知識庫與索引

`knowledge_base/manifest.json` 決定哪些 Markdown 文件會進入公開索引。`09_missing_information.md` 是本人待補資料，不會被索引。

目前持久化索引包含 135 個節點。Cloud Run 會直接載入 `storage/rag_index`；Docker build 不會排除這個目錄。

更新知識庫後必須同步重建索引，否則應用程式仍會使用舊向量。現有索引存在時，`RagService` 會直接載入，不會自行判斷 Markdown 是否改變。重建前請先保留舊索引備份，並確認 Application Default Credentials 已切換到正確的 GCP 帳號。

本機檢索測試：

```powershell
.venv\Scripts\python.exe rag_service.py "她有哪些後端技能？"
```

索引與 Markdown 的 `source_id` 一致性已納入測試。

## 執行測試

```powershell
.venv\Scripts\python.exe -m pytest -q
```

目前結果：

```text
76 passed
```

測試使用 mock 隔離 Gemini、LINE 與 Firestore，不會寫入正式雲端資料。部署後仍需另外執行正式環境 smoke test。

## Docker

建置：

```powershell
docker build -t career-bot-api .
```

執行：

```powershell
docker run --rm -p 8080:8080 --env-file .env career-bot-api
```

容器使用 Gunicorn：1 worker、4 threads、120 秒 timeout，並監聽 `0.0.0.0:${PORT:-8080}`。

## Cloud Run 部署檢查

目前最新程式與 135 節點索引仍需重新建置、部署。部署前確認：

1. `storage/rag_index` 已包含目前 135 個節點。
2. Cloud Run runtime service account 可以呼叫 Vertex AI，並可讀寫所需 Firestore 集合。
3. LINE、Turnstile 與 Chat HMAC secret 使用 Cloud Run／Secret Manager 設定，沒有放進映像。
4. 已設定正式 `CORS_ALLOWED_ORIGINS`，只包含實際 Cloudflare 網站 origin。
5. 已設定 `CHAT_RATE_LIMIT_PER_HOUR`、限流集合與 `CHAT_RATE_LIMIT_HASH_SECRET`。
6. 沒有把 `.env`、service-account JSON、PEM 或 API key 放進 Docker image。
7. 部署後依序測試健康檢查、三種 route、LINE callback、私人留言、Chat `429` 與 Firestore 紀錄。

## 安全與隱私

- CORS 是瀏覽器存取控制，不是 API 身分驗證；因此 Chat 另有伺服器端限流。
- Chat 限流與留言限流都不保存原始 IP。
- `unknown_questions`、`chat_logs` 與 `website_messages` 沒有公開讀取 API。
- Firestore Python server SDK 使用 IAM；Firebase Security Rules 不能取代 runtime service account 的最小權限設定。
- AI 回答需通過檢索來源白名單，沒有有效來源時採 fail-closed 的 `HANDOFF`。
- 使用者仍可能在問題或留言中自行輸入個資；正式上線前應決定保存期限與刪除政策。

IP 限流是成本保護的第一層，不是完整身分驗證。若公開流量增加，仍應評估 Cloud Armor、API Gateway、Turnstile 或登入後的使用者配額。

## 目前狀態與下一步

已在本機完成：

- 135 節點 RAG 索引與 source ID 一致性檢查。
- `/api/chat` Firestore 跨 instance 限流。
- Cloudflare Workers／Wrangler 部署說明校正。
- 76 項後端測試與 Astro 正式建置檢查。

下一步：

1. 重新部署目前 Cloud Run 映像與最新索引。
2. 完成 Turnstile、Firestore IAM 與限流環境變數設定。
3. 執行正式環境 smoke test。
4. 加入分階段 latency、request ID 與 Cloud Monitoring 告警。
5. 為知識庫建立版本 hash 或 CI 索引同步流程。

## 延伸文件

- [完整專案報告](docs/PROJECT_REPORT.md)
- [Chat API 限流設計](docs/CHAT_RATE_LIMITING.md)
- [問答紀錄與資料保留](docs/CHAT_LOGGING.md)
- [知識庫維護說明](knowledge_base/README.md)
