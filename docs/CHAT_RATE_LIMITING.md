# `/api/chat` 伺服器端限流

## 行為

- 限制範圍：僅限網站的 `POST /api/chat`；LINE `/callback` 不受影響。
- 識別方式：來源 IP 經 HMAC-SHA256 後成為 Firestore 文件 ID，不保存原始 IP。
- 視窗：每個 UTC 整點重設的固定一小時視窗。
- 預設配額：每個訪客每小時 20 次有效問題。
- 無效 JSON、空白問題、超過 500 字與瀏覽器 `OPTIONS` 不計次。
- 超過配額：回 HTTP `429`，並在 `Retry-After` header 告知距離下個視窗的秒數。
- Firestore 或限流設定故障：採 fail-closed，回 HTTP `503`，不呼叫 RAG／Gemini。

Firestore transaction 讓多個 Cloud Run instance 使用同一份原子計數，避免記憶體型限流在擴展或重啟後失效。

## Cloud Run 環境變數

```text
FIRESTORE_CHAT_RATE_LIMIT_COLLECTION=chat_rate_limits
CHAT_RATE_LIMIT_PER_HOUR=20
CHAT_RATE_LIMIT_HASH_SECRET=<長度足夠的隨機 secret>
```

`CHAT_RATE_LIMIT_HASH_SECRET` 建議放在 Secret Manager，且不要提供給 Astro。為了相容目前部署，未設定時後端會沿用 `LINE_CHANNEL_SECRET`，但正式環境仍建議兩者分開，日後輪替 LINE secret 才不會讓所有匿名訪客文件 ID 同時改變。

Cloud Run runtime service account 必須能讀寫 `chat_rate_limits` 集合。集合會在第一個合法問題到達時由 Firestore 自動建立，不需手動建 collection。

## 回應範例

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 1842
Content-Type: application/json

{"error":"詢問次數已達上限，請稍後再試。"}
```

## 限制

IP 限流適合作為控制 Gemini 成本的第一層：它能擋住單一來源的密集直接呼叫，而且不依賴 CORS。但多人共用公司或行動網路 NAT 時可能共用額度，攻擊者也可能透過多 IP 繞過。流量增加後可再加入 Cloud Armor／API Gateway、Turnstile 或登入帳號配額，不應把 IP 限流當成完整身分驗證。
