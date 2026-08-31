---
title: SEER 智慧影像標記平台
category: project
visibility: public
status: confirmed
last_updated: 2026-08-21
tags: [SEER, Smart Label, Flask, GCP, LINE, LIFF, SAM, Grounding DINO, YOLOv8]
---

# SEER 智慧影像標記平台

## 專案定位

SEER（Smart Label）是一套整合 AI 自動分割、人工審核與模型訓練流程的影像標註平台。使用者可透過 Web 或 LINE／LIFF 上傳圖片與文字 Prompt，系統將原始圖片處理成可供後續訓練使用的 YOLOv8-seg 資料集。
- 專案類型：工程師轉職訓練團隊專題。
- 專案名稱：SEER／Smart Label 智慧影像標記平台。
- 目前狀態：已部署至 Google Cloud，供專題展示使用。
- 重要限制：此專案屬於展示版本，不應描述為已正式商業上線或已有企業客戶使用。

## 專案要解決的問題

建立影像辨識資料集通常需要人工逐張標記，資料量大時會耗費大量時間。SEER 將既有 AI 模型、自動標註、人工審核、資料集匯出及模型訓練整合為同一套流程，讓沒有模型開發背景的使用者也能透過 Web 或 LINE 入口建立影像任務。

專案重點不只是展示模型結果，而是把圖片上傳、身分驗證、任務建立、背景處理、進度追蹤、人工修正、輸出下載與模型訓練串成可操作的應用系統。

## 使用者流程

1. 使用者從 LINE Rich Menu 或 LIFF 進入系統。
2. 完成 LINE 身分驗證。
3. 上傳圖片並輸入要辨識的物件 Prompt。
4. 後端建立 Task，將圖片保存至 Storage。
5. 背景 Worker 執行圖片下載、模型推論、Mask 產生與結果整理。
6. 使用者檢查結果與任務進度。
7. 系統匯出 YOLOv8-seg 格式的資料集 ZIP。

## AI 與輸出流程

- 使用 Grounding DINO 依文字描述定位物件。
- 使用 SAM 產生物件分割 Mask。
- 專案流程包含 YOLOv8 訓練與信心分數結果。
- 匯出內容包含 `data.yaml`、`images/` 與 `labels/`。
- 低信心結果不放入最終 ZIP，並在介面呈現偵測數、匯出數、排除數與低信心清單。
- 若全部結果皆為低信心，系統不產生資料集 ZIP。

## 後端設計

- 使用 Flask 建立 API。
- 採用 Application Factory 與 Blueprint 組織功能。
- Route 負責 HTTP 請求、驗證與回應。
- Service 負責商業流程與跨元件協調。
- Repository 封裝使用者、任務、圖片等資料存取。
- Storage Abstraction 讓 Service 不需要知道底層使用本機檔案或 Google Cloud Storage。

## Cloud Run Service 與 Job 的分工

一般 Web API 適合快速回應，但 AI 標註可能包含模型初始化、圖片下載、推論、Mask、資料集匯出與壓縮，執行時間較長。若直接在 Flask Request 中完成，可能讓使用者長時間等待或遇到 Timeout。

因此系統將工作拆分為：

- Cloud Run Service：處理登入、建立任務、查詢狀態、權限驗證與下載授權等短請求。
- Cloud Run Job：執行一次性的長時間 AI Pipeline。

Task 會先寫入 MySQL 並 Commit，確認資料已存在後才觸發 Job，避免 Worker 啟動時查不到尚未提交的 Task。

## 持久化與權限

- Cloud SQL／MySQL 保存使用者、任務與處理狀態。
- Google Cloud Storage 保存圖片、Mask 與資料集 ZIP。
- Secret Manager 保存 LINE 等敏感設定。
- 下載使用短效簽章 URL。
- 以 LINE User ID 對應使用者，查詢、預覽與下載均檢查 Task Owner。
- 未登入請求回傳 401；非本人資源以 404 避免洩漏資源是否存在。
- Cloud SQL／MySQL：保存使用者、任務、圖片紀錄與處理狀態。
- Cloud Storage：保存上傳圖片、中間產物、標註資料與下載檔案。
- Secret Manager：保存 LINE 及雲端服務所需的敏感設定。
- 本機開發與 GCP 環境透過儲存抽象切換本機檔案與 Cloud Storage。

## 背景任務可靠性概念

- 透過 Claim Token 與 Lease 避免多個 Worker 同時提交同一任務的結果。
- 使用 Heartbeat 延長有效租約。
- 輸出依 Attempt 分開保存，避免失敗嘗試污染正式結果。
- 整體執行較接近 at-least-once，最後提交透過 fencing 概念降低重複寫入風險。
- 失敗任務不阻塞後續任務，重試可搭配 Exponential Backoff。

## 林君璇本人負責範圍

### LINE Bot／LIFF 整合

- 串接 LINE Messaging API 與 LIFF。
- 處理 LIFF 初始化、登入及使用者 Profile 取得。
- 將 LINE ID Token 傳送至後端驗證，不直接信任前端提供的使用者 ID。
- 整合圖片與 Prompt 上傳、任務入口、進度查詢及完成通知。

### 身分驗證與資料權限

- 以驗證後的 LINE 身分對應系統使用者。
- 讓任務、圖片預覽及下載流程依擁有者身分進行權限檢查。
- 避免使用者只靠修改網址或 Task ID 存取其他人的任務資料。

### GCP 與儲存整合

- 整合 Cloud Run Service、Cloud Run Job、Cloud SQL、Cloud Storage 與 Secret Manager。
- 處理圖片、中間產物及輸出檔案在本機與 GCS 環境中的儲存流程。
- 參與上傳 Session、多階段上傳及任務建立後的檔案管理流程。
- 理解容器本機檔案不是永久儲存位置，因此將持久資料分別保存至資料庫及 Cloud Storage。

### Worker 與長時間任務

- 將長時間 AI 工作從一般 API 請求中分離，由背景 Worker 執行。
- 參與 Worker 任務領取、狀態更新、失敗處理與重試流程。
- 使用 Lease、Heartbeat 與 Claim Token 等概念降低重複處理或過期 Worker 覆寫結果的風險。
- 任務完成後串接 LINE 通知與結果下載流程。

### 容器化與部署

- 使用 Docker 整理服務執行環境。
- 將相關服務部署至 GCP 並處理部署過程中的設定與連線問題。
- 配合雲端環境調整資料庫、儲存及敏感設定的使用方式。

## 不屬於林君璇主要負責的部分

- SAM、YOLO-World、DINOv2 核心模型設計與訓練。
- 從零建立或研究基礎模型演算法。
- Web 主介面的主要設計與全部前端功能。
- Flask 後端主體與所有 API 的完整獨立開發。
- 團隊其他成員完成的模型、介面與專案成果。

若回答「她是否會訓練模型」，可以說專案整體具備使用資料集訓練模型的功能，她也理解資料從標註到訓練的流程；但不得回答成訓練模組或核心模型由她獨立設計完成。

## 技術選擇與解題重點

### 為什麼區分 Cloud Run Service 與背景工作

圖片處理與 AI 推論時間較長，若直接放在一般 HTTP route 中執行，容易造成請求逾時，也會讓使用者長時間等待。因此系統先建立任務並保存狀態，再由背景 Worker 處理，前端則查詢任務進度。

### 為什麼需要資料庫與 Cloud Storage

Cloud Run 容器可能重新啟動或被替換，本機檔案無法作為可靠的永久儲存。任務狀態及結構化資料保存於資料庫，圖片與輸出檔案保存於 Cloud Storage，才能讓不同執行個體共同存取。

### 為什麼需要 Lease、Heartbeat 與 Claim Token

背景任務可能因容器中斷、執行逾時或重試而被不同 Worker 處理。Lease 與 Heartbeat 用來表示 Worker 是否仍持有任務；Claim Token 用來避免已失效的 Worker 回來覆寫較新的結果。

### 為什麼下載仍需要權限檢查

即使檔案位於 Cloud Storage，也不能只依靠使用者知道檔案網址就允許下載。系統需要先確認任務所有權，再提供受限時間的下載方式，以降低跨使用者存取風險。

## 專案成果

- 完成 LINE LIFF 圖片與 Prompt 上傳入口。
- 完成 LINE 身分驗證與任務所有權整合。
- 將 AI 長時間任務與一般 API 請求分離。
- 完成雲端資料庫、檔案儲存、Worker 與 LINE 通知的流程整合。
- 完成候選標註、人工審核、資料集匯出、模型訓練、進度查詢與下載的展示流程。
- 專案已部署至 GCP，可供專題展示。

## AI 協作與能力邊界

林君璇在此專案中使用 AI、官方文件與既有範例協助理解架構、撰寫及修改程式、排查錯誤與完成部署。她能說明本人負責流程的主要目的與資料流，也能閱讀及修改相關程式；不應描述為在完全沒有參考資料的情況下，獨立從零完成整個平台。

## 建議回答方式

### 如果被問「SEER 是什麼？」

SEER 是一套將 AI 候選標註、人工審核、資料集匯出與模型訓練整合在一起的智慧影像標記平台。使用者可以透過 Web 或 LINE LIFF 上傳圖片與 Prompt，查詢任務進度，並在處理完成後下載結果。

### 如果被問「君璇在 SEER 負責什麼？」

君璇主要負責 LINE Bot／LIFF、LINE 身分驗證，以及 GCP 儲存、背景 Worker、任務通知與部署整合。AI 核心模型與 Web 主介面屬於團隊其他分工，不能描述成由她獨立完成。

### 如果被問「SEER 有正式上線嗎？」

SEER 已部署至 GCP，作為可操作的專題展示版本；目前沒有資料證明它已成為正式商業產品或已有企業客戶正式使用。

## 回答邊界

- 可以介紹團隊專案的完整功能，但必須另外說明林君璇本人負責範圍。
- 不得把團隊專案全部描述成她獨立開發。
- 不得說她從零設計或訓練 SAM、YOLO-World、DINOv2。
- 不得將 GCP 展示部署描述為正式商業上線。
- 不得虛構使用者數、標註效率、模型準確率、成本節省或企業採用成果。
- 不得提供雲端憑證、內部網址、資料庫連線資訊或其他敏感設定。

SEER 是團隊專案，平台確實使用 SAM、Grounding DINO 與 YOLOv8，但不應因此回答成「林君璇獨立設計、訓練所有模型」。目前已確認的重點是後端、雲端、LINE／LIFF 與 AI Pipeline 的系統整合。若企業追問模型訓練的精確個人分工，應記錄問題並由本人補充。
