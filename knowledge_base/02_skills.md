---
title: 技術與能力
category: skills
visibility: public
status: confirmed
last_updated: 2026-08-21
tags: [Python, Flask, GCP, Gemini, LINE, Docker, SQL]
---

# 技術與能力

以下技能以「曾經學習或在專案中實際使用」為準，不代表每一項都達到相同熟練程度。

## 程式與後端

- Python：主要使用語言，用於 Flask API、資料處理、AI Pipeline 串接與自動化程式。
- Flask：實作路由、Blueprint、Application Factory、設定管理、驗證與 Service／Repository 分層。
- REST API：具備請求驗證、錯誤回應、身分驗證、權限檢查及第三方 API 串接經驗。
- 套件與環境管理：使用 `uv`、`pyproject.toml` 與虛擬環境管理 Python 專案。
- 測試：接觸 pytest，能為 API 與核心流程建立基本測試。

## 資料庫與資料處理

- SQL：具備基礎查詢與資料操作能力。
- MySQL／Cloud SQL：在任務型後端架構中保存使用者、任務、圖片與處理狀態。
- 資料處理：接觸 NumPy、OpenCV、Pillow 與資料格式轉換。
- 資料一致性概念：理解先提交 Task 再觸發背景工作、短交易領取任務，以及長時間任務不可依賴 Container 本機檔案。

## AI 與 LLM

- Gemini API／Vertex AI：曾進行文字與影像相關 API 串接。
- Prompt 設計：能定義回答格式、限制輸出範圍與處理模型回傳結果。
- RAG：已將個人 Markdown 資料整理成 LINE Bot 的個人知識庫，完成向量檢索、回答分流與來源驗證流程。
- 影像 AI：專案使用 SAM、Grounding DINO 與 YOLOv8，重點在模型能力的應用整合、輸出驗證與資料集流程。
- 多模態：具備將圖片輸入 Gemini 並取得結構化辨識結果的實作經驗。

## 雲端、部署與維運

- Google Cloud：Cloud Run Service、Cloud Run Job、Cloud SQL、Cloud Storage、Secret Manager。
- Docker：將 Flask 服務容器化並部署至 Cloud Run。
- Git／GitHub：基本版本控制、分支與遠端儲存庫操作。
- Linux：具備基本指令、檔案系統與部署環境操作能力。
- Nginx／HTTPS：接觸反向代理與憑證設定。

## 前端與入口整合

- LINE Messaging API：Webhook、Signature 驗證、Reply Message、Push Message 與 Rich Menu。
- LIFF：登入、取得 Profile、傳遞 ID Token 與 Web 介面整合。
- HTML／CSS：能修改與維護一般網頁。
- Astro：使用 Astro 建立個人作品集網站，管理 Project 與 Note 的 Markdown 內容。

## 自動化與辦公工具

- Power Automate：曾將繳費單照片中的資料擷取並整理到 Excel 活頁簿。
- Excel、Google Sheets、Word：日常資料整理與文件製作。
- SOP 與教學文件：能將操作流程、常見問題與排除方式整理成圖文文件。

## 不應過度延伸的描述

- 不應說成「精通所有 GCP 服務」。
- 不應說成「自行設計或從零訓練 SAM、Grounding DINO 等基礎模型」。
- 不應說成「具備多年正式 AI 工程師經驗」。
- YOLO 訓練功能屬於專案流程的一部分；本人職責應著重後端、雲端與 AI 流程整合，除非之後補充更精確的模型訓練分工。
