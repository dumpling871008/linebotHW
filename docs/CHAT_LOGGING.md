# 問答紀錄

## 紀錄範圍

網站與 LINE 共用 CareerBotService，每次完成分流後，將問題與回答寫入
Firestore 的 chat_logs 集合。原本 unknown_questions 的 HANDOFF 待回覆流程不變。

- ANSWER、HANDOFF、OUT_OF_SCOPE 均會嘗試寫入一次。
- 分流或 HANDOFF 待回覆紀錄寫入失敗時，也嘗試保存錯誤紀錄；response 為 null，
  error_code 僅保留固定代碼，不保存原始例外訊息。
- 無效 JSON、空白、超過網站字數限制的輸入，以及 OPTIONS 不記錄。
- 在 CareerBotService 建立之前就失敗的請求、程序被終止的請求，可能無法記錄。
- 紀錄採 best-effort；Firestore 權限、連線或寫入失敗時，不改變原本的問答結果。
  Firestore 寫入 RPC timeout 為 2 秒且停用自動重試；SDK 初始化或取得憑證仍可能另花時間。
  程式不會在 HTTP 回覆之後使用背景執行緒寫入。
- status=success 代表後端處理完成，不代表使用者瀏覽器一定收到回覆。
  前端逾時不一定會中斷 Cloud Run 的處理。

## 保存欄位

- question：問題內容。
- response：AI 回覆；處理失敗時為 null。
- route：ANSWER、HANDOFF、OUT_OF_SCOPE；分流失敗時為 null。
- source_ids：本次回答使用的來源 ID。
- channel：website、line 或 local_test。
- status：success 或 error。
- error_code：routing_failed、handoff_storage_failed，正常時為 null。
- created_at：Firestore 伺服器時間。

一般紀錄不包含額外的姓名、IP、Email 或 LINE user ID。
使用者自行寫在問題裡的個資仍會隨文字保存，不能將這些紀錄視為已匿名化。
原本 HANDOFF 集合中的 LINE 身分欄位仍維持既有行為。

## 部署設定

Cloud Run 沿用現有 GOOGLE_CLOUD_PROJECT 與執行身分，新增選填環境變數：

    FIRESTORE_CHAT_LOG_COLLECTION=chat_logs

未設定時也會使用 chat_logs，不需要改 Astro 的 API URL 或 JSON 格式。
不要把 Google 服務帳戶金鑰或任何管理憑證放入 PUBLIC_ 前綴的變數。

1. 先部署 Astro 的保存提示，再啟用新版後端；LINE 也應在帳號說明或歡迎訊息提供同等提示。
2. 在 Cloud Run 的現有服務部署包含這些修改的新版映像。
3. 保留 Gemini、LINE、CORS 與留言表單的既有環境變數，不要整批覆蓋。
4. 確認執行身分有寫入 Firestore 的 IAM 權限，並確認資料庫禁止公開存取紀錄。
5. 用不含個資的測試問題呼叫網站，然後在 Google Cloud Console 的
   Firestore 資料頁檢查 chat_logs 是否產生文件。
6. 也測試 HANDOFF：chat_logs 保留問答紀錄，unknown_questions 保留待回覆項目。
   不需為測試輸入真實聯絡資料。
7. 若只有問答成功卻看不到紀錄，檢查 Cloud Run 中
   「Chat log could not be saved」警告及服務帳戶權限。

## 存取、查閱與保留期限

這次沒有新增公開的紀錄查詢 API，也不讓瀏覽器直接連線至 Firestore。
請以你自己的 Google 帳號登入 Console 查閱；只授予必要管理者資料讀取權限。

Python 的 Firestore 伺服器 SDK 使用 IAM，並繞過 Firebase Security Rules。
因此還必須檢查資料庫的用戶端規則，確保 chat_logs 不被任何允許公開讀寫的規則涵蓋。
單獨加入拒絕規則不能抵銷另一條符合路徑的允許規則。
這次沒有部署或修改線上 IAM / Security Rules，也沒有驗證它們已經符合要求。

本次未新增自動刪除流程或 TTL。上線前請決定保留期限，定期清理不再需要的紀錄；
如需自動到期刪除，應另行加入到期時間欄位並啟用 Firestore TTL。

官方參考：
[Firestore 安全規則與伺服器端 IAM](https://firebase.google.com/docs/firestore/security/insecure-rules)

## 本機驗證

在後端專案執行：

    .venv\Scripts\python.exe -m pytest -q

新增測試以 Mock 取代 Firestore、Gemini 與 LINE 外部呼叫，不需要真實雲端寫入。
部署完成後仍需上述正式環境驗證，單元測試通過不代表線上權限已設定。
