---
title: 個人求職 LINE Bot
category: project
visibility: public
status: in_progress
last_updated: 2026-08-21
tags: [LINE Bot, Gemini, RAG, Firestore, Cloud Run, Rich Menu]
---

# 個人求職 LINE Bot

## 專案狀態

進行中。LINE Bot 訊息收發、LINE Profile API、Gemini、個人知識庫、RAG 回答分流與 Firestore 未回答問題記錄已完成測試；求職 Rich Menu 與正式部署仍待完成。

## 專案目標

建立一個企業認識林君璇與聯絡她的入口。企業可以從 LINE 圖文選單開啟履歷、104 與個人網站，也可以在聊天室詢問她的技能、工作經歷、專案與求職方向。

## V1 規劃功能

- 三格 Rich Menu：履歷、104、個人網站。
- 使用 Gemini 根據個人知識庫回答招募問題。
- Markdown 文件切分與向量檢索。
- 回答必須有知識庫依據，不足時不可自行編造。
- 將無法回答的問題寫入 Firestore。
- 由林君璇定期從 Firestore 後台查看並處理待回答問題。
- 部署至 Google Cloud Run，敏感設定放入 Secret Manager。

## 預計技術

- Python、Flask、`uv`。
- LINE Messaging API。
- Gemini on Vertex AI。
- Embeddings 與 RAG。
- Firestore。
- Docker、Cloud Run、Secret Manager。

## 無法回答時的流程

1. 系統檢索個人知識庫。
2. 若相關度不足，或回答無法提供來源段落，判定為資料不足。
3. 將問題、提問者、時間、檢索分數與狀態寫入 Firestore。
4. 回覆企業「已記錄並轉達本人」。
5. 林君璇從 Firestore 後台查看並處理 `pending` 問題。

## 此專案想呈現的能力

- LINE Webhook 與第三方 API 串接。
- RAG、Prompt 約束與 Hallucination 防護。
- 未回答問題的資料閉環。
- 公開資訊與私人資訊的權限邊界。
- 可部署、可維護的後端服務設計。

## 回答限制

Bot 可以說明 RAG 分流與 Firestore 後台記錄已完成測試，但不得把 Rich Menu 或正式部署描述為已上線。
