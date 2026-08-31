---
title: 待本人確認與補充
category: maintenance
visibility: private
status: partial
exclude_from_rag: true
last_updated: 2026-08-31
tags: [維護, 待確認, 不公開]
---

# 待本人確認與補充

> 此文件僅供林君璇維護資料使用，不得匯入公開 RAG 索引，也不得作為 Bot 對外回答的直接來源。所有標示 `[待補]` 或 `[待確認]` 的內容都必須由本人確認，不能由 LLM 推測。

## 已確認的公開連結

- 履歷 PDF 公開資料夾：<https://drive.google.com/drive/folders/1SvsUChh-mGeNetvNLjXeJocdsloeWcrK?usp=sharing>
- 104 公開履歷：<https://pda.104.com.tw/profile/share/dk9T2793fxceQe3oWUAnDSzHFDjFGV9m>
- 個人網站正式網址：<https://shelly-portfolio.seer-ai.cloud/>
- GitHub 公開網址：<https://github.com/dumpling871008>
- GitHub 是否由 Bot 主動提供：`[待確認]`

目前 Bot 可主動提供履歷 PDF、104 公開履歷與個人網站。GitHub 雖為公開網址，但本人尚未確認是否要列為招募回答中的主動公開連結。

## 聯絡資料

- 求職用 Email：`dumpling8877@gmail.com`
- 是否公開 Email：`是`
- 是否公開電話：`否`
- 偏好的企業聯絡方式：`Email`
- 是否接受企業在目前的 LINE 官方帳號留言：`是`
- LINE Official Account 名稱：`[待補]`
- LINE Official Account ID：`[待補]`
- LINE Official Account 加入網址：`[待補]`

Bot 可以提供求職 Email，也可以請對方在目前聊天室留言；在名稱、ID 與加入網址補齊前，不得自行產生 LINE 聯絡資料。

## 求職方向與條件

- 主要方向：`AI 應用工程師`
- 延伸方向：`Python 後端工程師、資料工程相關初階職位`
- 最快到職時間：`錄取後一個月內`
- 可面試時段：`平日上午或下午，實際日期需另行確認`
- 期望薪資或面議規則：`面議，不提供固定數字`
- 希望工作地點：`北部區域`
- 遠端／混合／辦公室偏好：`皆可`
- 是否接受出差：`可以`
- 是否接受輪班：`[待確認]`
- 是否接受搬遷：`[待確認]`
- 對特定公司或職缺的接受意願：`需依個別職缺由本人確認`

## 教育與訓練

- 原學校：`國立高雄科技大學運籌管理系`
- 原學校就讀期間：`2018.09～2020.06`
- 轉學考準備期間：`2020.06～2021.06`
- 通過轉學考時間：`2021.06`
- 中原大學心理學系就讀期間：`2021.09～2025.01`
- 緯育班級正式課程名稱：`AI 應用開發實戰班`
- 訓練正式起訖期間：`2026.05～2026.09`
- 證照名稱、取得日期與證書連結：`[待補]`

## SEER／Smart Label 專案

- 專案團隊人數：`4 人`
- 專案狀態：`已部署至 GCP，作為可操作的專題展示版本`
- 正式商業上線或企業客戶使用：`未確認，不可宣稱`
- 最終模型組合：`SAM、YOLO-World、DINOv2`

### 已確認的個人負責範圍

- LINE Messaging API 與 LIFF 整合。
- LIFF 初始化、登入、Profile 取得及 LINE ID Token 驗證流程。
- 圖片與 Prompt 上傳入口、任務進度查詢及完成通知整合。
- 任務、圖片預覽與下載流程的使用者身分及 Owner 權限檢查。
- Cloud Run Service、Cloud Run Job、Cloud SQL、Cloud Storage 與 Secret Manager 整合。
- 圖片、中間產物及輸出檔案的本機／Cloud Storage 儲存流程。
- 背景 Worker 的任務領取、狀態更新、失敗處理與重試流程。
- Docker 容器化及 GCP 展示環境部署整合。

### 已確認不屬於主要分工的內容

- SAM、YOLO-World、DINOv2 核心模型設計與訓練。
- Web 主介面的主要設計及全部前端功能。
- Flask 後端主體與所有 API 的完整獨立開發。
- 團隊其他成員完成的模型、介面與專案成果。

### 模型訓練分工

專案整體包含使用資料集進行模型訓練的功能。林君璇理解從候選標註、人工審核、資料集匯出到模型訓練的流程，但核心模型與訓練模組不是已確認的主要分工，不得描述為由她獨立設計或完成。

### 仍待補充

- 是否有可公開 Demo、展示影片或 GitHub：`[待補]`
- 可公開的效能、準確率、處理時間或使用量：`[待補]`
- 專案正式開發期間：`[待補]`
- 是否有其他尚未寫入的個人負責功能：`[待本人逐項補充]`

## 個人求職 LINE Bot

- 專案狀態：`進行中／Cloud Run 測試版`
- Cloud Run 部署狀態：`後端已部署，目前僅本人測試`
- Cloud Run 公開網址：`[待補；不得因已部署而自行產生網址]`
- 外部使用狀態：`尚未正式公開`
- LINE Official Account 名稱與 ID：`[待補]`
- Gemini Model 設定：透過 `GEMINI_MODEL` 設定，程式預設為 `gemini-3.7-flash`
- RAG Embedding Model：`gemini-embedding-001`
- Rich Menu：`目前沒有`
- RAG、Question Router 與來源追蹤：`已完成測試`
- Firestore 未回答問題記錄：`已完成測試，目前由本人從後台人工查看`
- 履歷、104、個人網站連結：`已確認，但尚未建立 Rich Menu`

## 仍待本人優先確認

1. GitHub 是否要由 Bot 主動提供。
2. LINE Official Account 名稱、ID 與加入網址。
3. SEER 可公開 Demo、影片或程式碼連結。
4. SEER 專案正式開發期間。
5. SEER 是否有經驗證且可對外公開的效能或處理時間數據。
6. 是否接受輪班與搬遷。
7. 專業證照資訊；若目前沒有，可明確改為「無」。

## 維護規則

1. 此檔案應放在 `maintenance` 目錄，不得放入公開知識庫索引範圍。
2. 公開 RAG 建索引時，只讀取 `visibility: public` 且未設定 `exclude_from_rag: true` 的文件。
3. 每次本人確認新資料後，同步更新對應的公開知識檔，避免公開檔與維護檔互相矛盾。
4. 專案狀態改變後，應移除過期的「規劃中」「待部署」或「尚未完成」說法。
5. 不因欄位存在網址、技術名稱或規劃內容，就推論它已公開、已部署或由本人獨立完成。
