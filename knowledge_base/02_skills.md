---
title: 技術與能力
category: skills
visibility: public
status: confirmed
last_updated: 2026-08-30
tags: [Python, Flask, SQL, PostgreSQL, ETL, LlamaIndex, Gemini, GCP, Docker, LINE]
---

# 技術與能力

## 技能描述原則

以下技能以「曾學習、親自操作或在專案中實際使用」為準，各項熟悉程度不完全相同。林君璇的專案開發包含 AI 協作與文件查閱；她能閱讀與修改既有程式、說明主要系統流程，並完成實際操作，但部分功能若要從零設計或獨立撰寫，仍會使用 AI、官方文件或既有範例協助。

回答技能問題時，應同時說明實作情境與能力邊界，不得只根據技術名稱推定為熟練或精通。

## Python 與後端開發

### Python

- 主要使用的程式語言。
- 實作情境包含 Flask API、LINE Bot、RAG 問答、104 職缺資料擷取、資料清理、ETL 練習、自動化程式及 AI API 串接。
- 能閱讀與修改既有 Python 程式，理解函式、條件判斷、例外處理、資料結構、模組匯入及套件使用方式。
- 完整系統或較複雜流程若需從零設計，仍會搭配 AI、文件與範例進行。

### Flask 與後端架構

- 曾使用 Flask 建立 API 與 LINE Webhook 服務。
- 接觸並實作路由、Blueprint、Application Factory、環境設定、請求驗證與錯誤回應。
- 在專案中使用 Service／Repository／Storage 等分層概念，將 HTTP 請求處理、商業流程、資料存取及檔案儲存責任分開。
- 理解耗時 AI 任務不應直接放在一般 HTTP route 中長時間執行，應交由背景工作處理。

### REST API 與外部服務串接

- 能使用 Python 呼叫第三方 API，傳送參數、Headers 與 JSON 資料，並處理回傳結果。
- 實作過輸入驗證、HTTP 錯誤回應、身分驗證、資源所有權檢查及外部 API 串接。
- 串接經驗包含 Gemini API、LINE Messaging API、LIFF 驗證流程與 104 職缺 API。

### Python 專案環境

- 使用過 `uv`、`pyproject.toml` 與 Python 虛擬環境管理套件及專案環境。
- 能依既有專案說明安裝相依套件、啟動服務並調整環境變數。
- 接觸 pytest，可閱讀並建立 API 或核心流程的基本測試；不應描述為具備完整測試架構設計經驗。

## 資料庫、SQL 與資料工程

### SQL

- 具備基礎 SQL 查詢與資料操作經驗。
- 使用過建表、欄位型別、主鍵、外鍵、`CHECK` 條件、`SELECT`、篩選、彙總及資料表關聯查詢。
- 能閱讀並修改既有 SQL，並透過查詢檢查資料筆數、缺失值與載入結果。
- 目前不應描述為熟悉複雜查詢最佳化、資料庫效能調校或大規模資料平台設計。

### PostgreSQL

- 在 ETL 練習專案中使用 PostgreSQL 16。
- 建立並查詢 `staging`、`warehouse`、`audit`、`quality` 等 Schema 與相關資料表。
- 實作情境包含來源資料暫存、維度表設計、ETL 執行紀錄及不合格資料紀錄。
- 能說明資料從來源檔案進入資料庫的基本流程，並閱讀、修改既有建表與查詢語法。

### MySQL／Cloud SQL

- 在任務型後端架構中使用 MySQL／Cloud SQL 保存使用者、任務、圖片資料與處理狀態。
- 理解先寫入 Task、完成資料庫交易後再觸發背景工作的設計目的。
- 接觸長時間任務的短交易領取、任務狀態更新與失敗處理概念。

### SQLite／SQLAlchemy

- 在 104 職缺爬蟲系統中使用 SQLite 與 SQLAlchemy 保存職缺、追蹤狀態及備註。
- 能配合既有模型與流程進行資料讀寫及功能修改。
- 不應延伸為熟悉進階 ORM 設計或大型資料庫遷移管理。

### pandas／Faker／openpyxl

- 在 ETL 練習專案中使用 Faker 產生模擬顧客、商品、訂單與退貨資料。
- 使用 pandas 進行表格資料處理，並透過 openpyxl 產生或處理 Excel 檔案。
- 已在 AI 協作下成功執行資料產生流程，能閱讀及修改既有 Python 程式；從零設計完整資料產生器仍需文件或 AI 協助。

### Pentaho Data Integration

- 使用 Pentaho Spoon 建立及執行資料轉換流程。
- 已完成轉換執行並能確認資料載入結果。
- 目前屬於專案練習經驗，不應描述為具備企業級 Pentaho 維運或複雜排程經驗。

### ETL 與資料品質概念

- 能說明來源資料產生、Staging、資料品質檢查、Warehouse 與稽核紀錄的基本流程。
- 實作過缺失資料檢查、不合格資料保存及 ETL 執行狀態紀錄。
- 已使用 Python、Excel、PostgreSQL、Pentaho 與 Docker Compose 執行相關步驟。
- 此 ETL 專案仍在持續優化；能閱讀與修改既有 Python／SQL，但從零設計完整 Pipeline 仍需 AI 或文件協助。

## 資料擷取與 104 職缺爬蟲

### Python requests

- 使用 `requests` 呼叫 104 職缺 API，帶入關鍵字、頁數與數量等搜尋參數。
- 解析 API 回傳內容，整理職缺名稱、公司、工作內容與連結等欄位。

### 職缺整理與篩選

- 已實作工程師職缺蒐集與欄位整理。
- 透過職稱與條件規則排除工務、營運或其他不相關職缺，降低非工程職缺混入。
- 前端可調整搜尋關鍵字、搜尋數量及頁數。
- 系統可保存職缺追蹤狀態與個人備註。
- 此系統在 AI 協作下完成；不應描述為完全獨立從零開發，或擴張成具備大規模分散式爬蟲經驗。

## 生成式 AI、RAG 與影像應用

### Gemini API／Vertex AI

- 曾串接 Gemini 文字與圖片輸入能力。
- 能設定 Prompt、指定輸出格式、處理模型回傳結果，並將模型能力整合至 Flask、LINE Bot 或其他服務流程。
- 曾將圖片交給 Gemini 辨識車牌，並要求回傳結構化結果。

### Prompt 設計

- 能設定 Bot 身分、回答範圍、禁止推測事項、資料不足時的回覆及結構化輸出要求。
- 知道 Prompt 不能取代程式端驗證，重要的權限、格式與資料邊界仍需由程式控制。

### LlamaIndex 與 RAG

- 將個人履歷、技能、工作經歷與專案資料整理為 Markdown 知識庫。
- 使用 LlamaIndex 建立向量索引與相似度檢索，並將索引持久化保存。
- 實作檢索結果的 `source_id`、來源段落與分數傳遞，讓回答可以追蹤資料來源。
- 透過 Question Router 將問題分為可回答與需本人確認的情況，再交由 Gemini 產生受政策限制的回答。
- 無法回答的問題會連同提問資訊與檢索結果保存至 Firestore，供後台追蹤；此流程已完成並測試成功。

### 影像 AI 與多模態

- 專案使用 SAM、Grounding DINO 與 YOLOv8，重點為既有模型能力整合、模型輸出驗證、影像任務流程及資料集產出。
- 接觸圖片、Mask、標註與 YOLOv8-seg 資料格式處理。
- 具備將圖片輸入 Gemini 並取得結構化辨識結果的實作經驗。
- 不應描述為自行設計或從零訓練 SAM、Grounding DINO 等基礎模型。

## 雲端、容器與部署

### Google Cloud

- 專案接觸 Cloud Run Service、Cloud Run Job、Cloud SQL、Cloud Storage 與 Secret Manager。
- 理解 Cloud Run Service 適合處理短時間 HTTP 請求，Cloud Run Job 適合執行較長的批次或 AI 任務。
- 理解容器本機檔案不是可靠的永久儲存位置，圖片、Mask 與輸出檔應保存至 Cloud Storage，任務狀態應保存至資料庫。
- 不應描述為精通所有 GCP 服務、雲端網路或企業級雲端架構。

### Docker／Docker Compose

- 曾將 Flask 服務容器化並部署至 Cloud Run。
- 在 ETL 專案中使用 Docker Compose 啟動 PostgreSQL，設定連接埠、Volume 與健康檢查。
- 能依既有設定啟動、停止及查看容器狀態；較複雜的容器架構仍需文件或協助。

### Git／GitHub

- 具備基本版本控制經驗，包括初始化儲存庫、提交修改、建立及切換分支、設定遠端與推送程式碼。
- 曾處理分支名稱或 `refspec` 不一致造成的推送問題。

### Linux、Nginx 與 HTTPS

- 具備基本 Linux 指令、檔案系統、服務啟動及部署環境操作經驗。
- 接觸 Nginx 反向代理、路由轉發與 HTTPS 憑證設定。
- 不應描述為具備完整 Linux 系統管理或資安維運經驗。

## LINE、前端與網站

### LINE Messaging API

- 實作 Webhook、Signature 驗證、Reply Message、Push Message、Follow Event 與 Rich Menu。
- 將 LINE Bot 作為個人求職入口，整合 RAG 問答、履歷、104 與個人網站連結。

### LIFF

- 實作 LIFF 初始化、登入、取得使用者 Profile、取得 ID Token，並將 Token 傳至後端驗證。
- 理解前端顯示的 LINE 身分資訊不能直接被後端信任，仍需驗證 ID Token。

### HTML／CSS／JavaScript

- 能修改一般網頁介面與互動功能。
- 在 104 職缺系統中製作搜尋條件、職缺列表、狀態與備註操作介面。
- 目前不應描述為專精前端框架或複雜 JavaScript 應用架構。

### Astro

- 使用 Astro 建立個人作品集網站，展示個人資料、專案與 Markdown 筆記。
- 調整內容集合、動態路由與元件，將原始範本的 Work 結構改為 Projects。
- 個人網站已整合 AI 問答功能。

## 自動化、文件與溝通

### Power Automate

- 曾建立流程，從學生繳費單照片擷取資料並整理至 Excel 活頁簿。
- 此經驗可描述為實際使用自動化工具改善資料整理流程，不應延伸為大型企業 RPA 專案經驗。

### 文件與 SOP

- 能將操作步驟、常見問題與排除方式整理成圖文 SOP 及教學手冊。
- 曾整理教室設備、HDMI、電腦及 Webex 常見問題與處理流程，協助新進人員接手工作。
- 具備將技術流程轉換成一般使用者可理解說明的經驗。

## 整體能力邊界

- 可以說：曾在專案中實際使用上述技術，能說明主要流程，並能閱讀與修改部分既有程式及設定。
- 可以說：會使用 AI 協作、官方文件與錯誤訊息協助完成開發及學習。
- 不應說：精通 Python、SQL、GCP、前端或所有列出的工具。
- 不應說：能完全不依賴參考資料，從零獨立設計所有系統、ETL Pipeline 或雲端架構。
- 不應說：自行設計或從零訓練 SAM、Grounding DINO 等基礎模型。
- 不應說：具備多年正式 AI、後端或資料工程師工作經驗。
- YOLO 訓練功能屬於團隊專案流程的一部分；本人負責範圍應以專案文件中的確認內容為準。
