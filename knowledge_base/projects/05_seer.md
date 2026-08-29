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

## 背景任務可靠性概念

- 透過 Claim Token 與 Lease 避免多個 Worker 同時提交同一任務的結果。
- 使用 Heartbeat 延長有效租約。
- 輸出依 Attempt 分開保存，避免失敗嘗試污染正式結果。
- 整體執行較接近 at-least-once，最後提交透過 fencing 概念降低重複寫入風險。
- 失敗任務不阻塞後續任務，重試可搭配 Exponential Backoff。

## 林君璇的主要著力範圍

- Flask 後端架構與 API 流程理解。
- LINE Bot、LIFF 登入與使用者身分串接。
- Service／Repository／Storage 的職責拆分。
- Cloud Run Service、Cloud Run Job、Cloud SQL 與 GCS 的系統整合。
- 長時間背景任務、Task 狀態與權限流程的設計及除錯。
- 將技術架構整理成可說明、可交接的文件與簡報。

## 責任邊界

SEER 是團隊專案，平台確實使用 SAM、Grounding DINO 與 YOLOv8，但不應因此回答成「林君璇獨立設計、訓練所有模型」。目前已確認的重點是後端、雲端、LINE／LIFF 與 AI Pipeline 的系統整合。若企業追問模型訓練的精確個人分工，應記錄問題並由本人補充。
