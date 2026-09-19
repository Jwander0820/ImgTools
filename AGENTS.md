# AGENTS.md

本文件適用於整個 ImgTools 專案。這是以 action registry 為核心的本機影像工作台，由瀏覽器 UI、CLI 與 Python 共用處理邏輯；不再保留或依賴 `legacy/`。

## 架構與開發規則

1. 新功能先定義可觀察行為與 interface，再補 failing test，最後實作。
2. UI、CLI 與自動化一律經過 `imgtools.service.runner.run_tool()`。非同步 UI 任務也須經由 `handle_run()` 呼叫 runner，不可另建繞過驗證、安全預設或 manifest 的執行路徑。
3. 新 action 必須在 `imgtools/service/registry.py` 註冊。參數型別、必填、預設與選項集中於 `ToolSpec` / `ToolParam`，前端依 metadata 產生表單。
4. 影像演算法放在 `imgtools/core/`。Core 不解析 CLI、不啟動 UI、不使用固定輸入路徑，也不直接 `sys.exit()`；需要進度或取消時使用 `service/execution.py` 的可選執行上下文。
5. HTTP 層維持薄 adapter；前端使用原生 ES modules，無須建置流程。不要為單一實作額外加入只轉呼叫的相容層。
6. 測試應觀察公開 interface 的行為；靜態字串檢查不能取代任務狀態、輸出保護與使用者操作的驗證。

## 任務與檔案安全

- Rename 預設只預覽，只有 `confirm=true` 才能修改名稱。排隊中的改名可取消，開始執行後不提供取消，避免只套用部分變更。
- 輸出預設不覆寫，命名與路徑規則集中在 `core/common.py`。新增輸出流程時，須考慮驗證後同名檔案才出現的情況；不可自動刪除使用者輸入。
- UI 任務由 `service/jobs.py` 依序執行，runner 的鎖只序列化同一服務程序的呼叫，不代表不同程序之間已互斥。
- 長任務在安全節點呼叫 `checkpoint()`，完成檔案寫入後才呼叫 `record_output()`。取消或失敗須回傳已完成輸出；取消不回滾或清除使用者檔案。原生編碼與寫入須等待當前步驟結束，影片取消需確實終止並回收 ffmpeg 子程序。
- 保留 `request_id` 去重及 `session_id` 核對。重試不得因結果紀錄清除或服務重啟而再次執行不確定的舊請求；完成後清除任務參數中的密碼等敏感資料。
- 輪詢傳送精簡任務摘要，完整結果依需求取得。歷史結果目前保留於服務記憶體，重啟後不會復原佇列；磁碟上的 manifest 仍保留。
- 檔案開啟功能只接受已知任務的輸出及允許的格式，不得接受任意命令。
- 本機 HTTP 服務預設使用 `127.0.0.1:5858`。現有路徑輸入、選檔與預覽 API 不應直接公開到網路。

## 前端維護

| 模組 | 責任 |
| --- | --- |
| `app.js`、`state.mjs` | 啟動、導覽、偏好、跨工具表單與預覽狀態 |
| `form.mjs`、`fields.mjs` | registry 表單、路徑選擇、圖片排序與縮圖 |
| `watermark.mjs`、`stack.mjs`、`dialogue.mjs` | 各工具的即時編輯器 |
| `task-store.mjs`、`jobs.mjs` | 任務狀態、重試、取消與任務列 |
| `result-model.mjs`、`results.mjs` | 結果語意、表格、檔案操作與成品預覽 |
| `app.css`、`layout.css` | 編輯器元件、工作台配置與共用字級 |

- 新增工具時同步確認結果的呈現方式。改名需區分預覽與實際變更，中繼資料需可閱讀及搜尋；一般使用者不應依賴原始 JSON 判斷結果。
- 任務與結果需保留原工具身分。切換工具不得繞過未完成任務的送出限制；較舊的輪詢回應不得覆蓋新增或取消後的狀態。
- 延遲的圖片預覽與選檔回應須檢查目前工具及請求版本，避免更新已切換的表單。
- 維持繁體中文操作文字、明確欄位標籤、鍵盤操作及必填提示。一般操作與開發用 JSON 分開，長路徑與結果表格不得撐寬整個頁面。

## 驗證與本機環境

優先使用專案 `.venv`，安裝方式見 README。Windows 啟動器會優先使用 `.venv\Scripts\python.exe`，再回退到原有 Python 路徑；`ImgTools.cmd --check` 可檢查選用的解譯器而不啟動服務。不要將個人電腦上的 Python 絕對路徑寫入程式或測試。

- 測試及瀏覽器驗證使用臨時目錄或 `data/` 下獨立的測試資料，並設定 `IMGTOOLS_STATE_DIR` 隔離偏好與 manifest。不得改動使用者原始圖片、預設偏好或既有任務成果。
- 先執行與變更相關的測試。程式行為變更完成後執行下列完整檢查；只修改文件時核對內容、路徑與差異格式即可。

```powershell
python -m unittest discover -s tests
node --test tests/frontend.test.mjs
python -m compileall -q imgtools tests
python -m imgtools list
git diff --check
```

- 對修改的 JS 模組執行 `node --check <檔案路徑>`。任務變更優先檢查 `test_jobs.py`、`test_job_http.py` 與 `frontend.test.mjs`，包含排隊、取消、部分輸出、去重及連線失敗。
- UI 變更須以瀏覽器驗證桌面與窄視窗，至少檢查 1280px 與 375px 寬度。涉及編輯器或結果時，驗證圖片順序、預覽尺寸、改名語意、中繼資料搜尋與長輸出路徑；區分自動測試與實際操作已確認的範圍。
- 結束時重設測試用視窗尺寸，停止本次建立的測試服務。不要停止使用者原先執行的服務或刪除既有資料。

## 文件與 Git

- 改變 action、API、輸出或操作流程時，同步更新 README、`docs/ARCHITECTURE.md` 與相關範例。驗證紀錄應註明日期與限制，不把某次測試數量當成固定規格。
- 修改前檢查 Git 狀態並保留既有工作。Commit message 使用繁體中文 Conventional Commit；只要求撰寫訊息時不提交，收到明確 commit 指示後才提交已確認的變更，不推定 push 或部署授權。

完整維護說明見 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，本次 UI 迭代與驗證範圍見 [docs/UI_ITERATION.md](docs/UI_ITERATION.md)。
