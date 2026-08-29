# 林君璇 LINE Bot 個人知識庫

這是一套提供給企業與招募方使用的公開求職知識庫，預計由 LINE Official Account 的 RAG（Retrieval-Augmented Generation）流程檢索後，再交給 LLM 產生回答。

## 使用目的

- 回答林君璇的背景、技能、工作經歷與專案經驗。
- 協助企業快速判斷職缺與候選人的適配程度。
- 清楚區分已確認事實、進行中項目與尚待本人確認的資訊。
- 當問題超出知識庫時，不讓模型自行猜測，而是記錄至 Firestore 後台供本人查看。

## 文件結構

| 文件 | 用途 | 建議納入檢索 |
|---|---|---|
| `00_answer_policy.md` | 回答規則與隱私邊界 | 是 |
| `01_profile.md` | 個人簡介與職涯定位 | 是 |
| `02_skills.md` | 技術與可轉移能力 | 是 |
| `03_work_experience.md` | 過往工作經歷 | 是 |
| `04_education_and_transition.md` | 學歷與轉職脈絡 | 是 |
| `projects/05_seer.md` | SEER／Smart Label 專案 | 是 |
| `projects/06_linebot_portfolio.md` | 個人求職 LINE Bot 專案 | 是，但須保留狀態欄位 |
| `07_job_preferences.md` | 目標職位與工作方向 | 是 |
| `08_faq.md` | 招募常見問題 | 是 |
| `09_missing_information.md` | 待本人補充資料 | 否 |
| `manifest.json` | 匯入與索引設定 | 否 |
| `test_questions.json` | RAG 測試題 | 否 |

## 建議檢索方式

1. 讀取 `manifest.json` 中 `index: true` 的 Markdown。
2. 依二級或三級標題切成段落，每段保留來源檔名與標題。
3. 對使用者問題執行向量檢索，取得最相關的 3 至 5 個段落。
4. 僅允許 LLM 使用取回段落中的內容回答。
5. 若沒有足夠證據、答案涉及待確認欄位，或模型無法提供來源段落 ID，改走「未回答問題」流程。

## 維護規則

- 只放願意公開給企業與招募方的內容。
- 更新經歷、技能或專案後，同步修改 `last_updated`。
- 進行中的功能必須標示「進行中」或「規劃中」，不可描述為已完成。
- 技能應以「實際使用情境」描述，不使用無法驗證的熟練度或年資。
- `09_missing_information.md` 補完後，將確認內容移到對應文件。

目前版本：`v0.1.0`  
最後整理日期：`2026-08-21`
