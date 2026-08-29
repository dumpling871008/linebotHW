---
title: 招募常見問題
category: faq
visibility: public
status: confirmed
last_updated: 2026-08-21
tags: [FAQ, 面試, 招募, 專案]
---

# 招募常見問題

## 可以簡單介紹林君璇嗎？

林君璇畢業於中原大學心理學系，曾從事教育與教務支援工作，之後投入 Python、後端系統、生成式 AI 與 GCP 的學習及專案實作。目前以 AI 應用工程師、Python 後端工程師與資料工程相關職位為主要方向。

## 為什麼從心理學與教育領域轉職工程師？

她在工作中接觸 Python 與 Power Automate 後，發現自己喜歡將問題拆解並透過程式改善流程，因此開始系統性學習後端、資料庫、雲端與 AI 應用。

## 非資訊本科會是問題嗎？

她不會把短期學習包裝成多年工程經驗，而是以實際專案、架構設計、程式碼與持續練習證明能力。心理學和教育經驗也讓她更重視使用者需求、溝通與問題定義。

## 她想應徵什麼職位？

主要方向是 AI 應用工程師、Python 後端工程師及資料工程相關初階職位，特別對 LLM、RAG、API 串接、企業知識應用、工作流程自動化與 GCP 部署有興趣。

## 她最具代表性的專案是什麼？

目前最具代表性的專案是 SEER／Smart Label 智慧影像標記平台，整合 LINE／LIFF、Flask、GCP、SAM、Grounding DINO 與 YOLOv8，讓使用者能上傳圖片、執行 AI 標註並匯出 YOLOv8-seg 資料集。

## 她在 SEER 中主要負責什麼？

目前已確認的著力範圍是 Flask 後端、LINE／LIFF、Service／Repository／Storage 分層、Cloud Run Service 與 Job、Cloud SQL、GCS，以及長時間任務和權限流程的系統整合與說明。

## 她有自己訓練模型嗎？

SEER 專案流程包含 YOLOv8 訓練，並使用 SAM 與 Grounding DINO。但目前不應描述成她獨立從零設計或訓練所有模型。她已確認的主要能力是模型能力的應用、後端與雲端流程整合；精確模型訓練分工需要本人補充。

## 為什麼 SEER 要把 Cloud Run Service 和 Job 分開？

一般 API 應快速回應，但 AI 標註包含圖片下載、模型初始化、推論、Mask、匯出和壓縮，可能執行較久。Service 處理短請求，Job 處理長時間背景任務，可以降低 Request Timeout 並讓任務狀態更容易管理。

## 為什麼要先 Commit Task 再觸發 Job？

若先觸發 Job，Worker 可能在原本的資料庫 Transaction 尚未 Commit 前查詢 Task，因而得到「找不到 Task」。先 Commit 可以確保 Worker 啟動時資料已經存在。

## 她使用過哪些 GCP 服務？

專案中接觸 Cloud Run Service、Cloud Run Job、Cloud SQL、Google Cloud Storage 與 Secret Manager，並理解 Container 本機檔案不適合作為永久資料保存位置。

## 她有 LLM 開發經驗嗎？

她曾使用 Gemini API 進行 LINE Bot 回覆與圖片內容辨識，也已在個人求職 LINE Bot 中完成 RAG、結構化輸出、回答邊界與未知問題後台記錄流程。

## 她熟悉哪些後端設計概念？

她在專案中使用或學習 Flask Application Factory、Blueprint、Service Layer、Repository、Storage Abstraction、身分驗證、資源 Owner 檢查、背景工作與任務狀態管理。

## 過去教育工作和工程工作有什麼關聯？

教育工作培養了需求理解、問題拆解、資料觀察與溝通能力；教務工作則累積了設備排錯、系統資源管理、SOP 標準化及知識交接經驗。這些能力可延伸到系統分析、除錯和技術文件。

## 她是否具備正式工程師年資？

目前資料不支持多年正式工程師年資的說法。她以轉職訓練與專案實作累積工程能力，適合以初階或重視潛力與整合能力的職位進行評估。

## 她最快何時可以到職？

目前知識庫沒有已確認的到職日期，需要由本人回覆。系統應將此問題記錄至 Firestore 後台供她查看。

## 她的期望薪資是多少？

目前知識庫沒有已確認的期望薪資，需要由本人依職務內容與條件回覆。

## 要如何查看她的履歷、104 或作品集？

可使用 LINE 圖文選單開啟相關頁面。正式網址尚待補入知識庫與 Rich Menu 設定，在網址確認前不得自行生成連結。

## 要如何聯絡她？

可以直接在此 LINE 官方帳號留下問題或聯絡需求。私人 Email、電話及其他聯絡方式需在本人確認公開後才可提供。
