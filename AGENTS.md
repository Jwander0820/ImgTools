# AGENTS.md

本文件適用於整個 ImgTools 專案，包含 Python 本機工作台與 `web/` 靜態網頁版。線上版入口為 [imgtools.jwander.net](https://imgtools.jwander.net/)。不再保留或依賴 `legacy/`。

## 版本與執行邊界

| 版本 | 處理方式 | 開發入口 |
| --- | --- | --- |
| 本機版 | 瀏覽器 UI、CLI 與 Python 共用 action registry、runner 與本機檔案系統 | `main.py`、`imgtools/`；預設 `127.0.0.1:5858` |
| 靜態網頁版 | 使用者瀏覽器內的 Canvas／PDF.js，下載 PNG；無 Python API、伺服器佇列或 manifest | `web/`；本機預覽 `127.0.0.1:5859` |

靜態版目前提供台詞疊圖、直向疊圖、文字浮水印與 PDF 單頁轉 PNG，不代表本機所有 actions 都已移植。修改前先確認影響版本；共用圖示及配色的修改需檢查兩版。

## 架構與開發規則

1. 新功能先定義可觀察行為與 interface，再補 failing test，最後實作。
2. 本機 UI、CLI 與自動化一律經過 `imgtools.service.runner.run_tool()`。非同步 UI 任務也須經由 `handle_run()` 呼叫 runner，不可另建繞過驗證、安全預設或 manifest 的執行路徑。獨立靜態版依下方瀏覽器處理契約維護。
3. 新本機 action 必須在 `imgtools/service/registry.py` 註冊。參數型別、必填、預設與選項集中於 `ToolSpec` / `ToolParam`，本機前端依 metadata 產生表單。
4. 本機影像演算法放在 `imgtools/core/`。Core 不解析 CLI、不啟動 UI、不使用固定輸入路徑，也不直接 `sys.exit()`；需要進度或取消時使用 `service/execution.py` 的可選執行上下文。
5. 本機 HTTP 層維持薄 adapter；兩版前端使用原生 ES modules。本機前端無須建置；靜態版透過 `web/build.mjs` 複製模組、共用素材與 PDF.js 資源。不要為單一實作額外加入只轉呼叫的相容層。
6. 測試應觀察公開 interface 的行為；靜態字串檢查不能取代任務狀態、輸出保護與使用者操作的驗證。

## 本機任務與檔案安全

- Rename 預設只預覽，只有 `confirm=true` 才能修改名稱。排隊中的改名可取消，開始執行後不提供取消，避免只套用部分變更。
- 輸出預設不覆寫，命名與路徑規則集中在 `core/common.py`。新增輸出流程時，須考慮驗證後同名檔案才出現的情況；不可自動刪除使用者輸入。
- UI 任務由 `service/jobs.py` 依序執行，runner 的鎖只序列化同一服務程序的呼叫，不代表不同程序之間已互斥。
- 長任務在安全節點呼叫 `checkpoint()`，完成檔案寫入後才呼叫 `record_output()`。取消或失敗須回傳已完成輸出；取消不回滾或清除使用者檔案。原生編碼與寫入須等待當前步驟結束，影片取消需確實終止並回收 ffmpeg 子程序。
- 保留 `request_id` 去重及 `session_id` 核對。重試不得因結果紀錄清除或服務重啟而再次執行不確定的舊請求；完成後清除任務參數中的密碼等敏感資料。
- 輪詢傳送精簡任務摘要，完整結果依需求取得。歷史結果目前保留於服務記憶體，重啟後不會復原佇列；磁碟上的 manifest 仍保留。
- 檔案開啟功能只接受已知任務的輸出及允許的格式，不得接受任意命令。
- 本機 HTTP 服務預設使用 `127.0.0.1:5858`。現有路徑輸入、選檔與預覽 API 不應直接公開到網路。

## 本機前端維護

以下模組位於 `imgtools/ui/static/`：

| 模組 | 責任 |
| --- | --- |
| `app.js`、`state.mjs` | 啟動、導覽、偏好、跨工具表單與預覽狀態 |
| `form.mjs`、`fields.mjs` | registry 表單、路徑選擇、圖片排序與縮圖 |
| `watermark.mjs`、`stack.mjs`、`dialogue.mjs` | 各工具的即時編輯器 |
| `task-store.mjs`、`jobs.mjs` | 任務狀態、重試、取消與任務列 |
| `result-model.mjs`、`results.mjs` | 結果語意、表格、檔案操作與成品預覽 |
| `app.css`、`layout.css` | 編輯器元件、工作台配置與共用字級 |

- `ToolSpec.ui_replacement` 控制整合後的 UI 入口，不刪除原 action。目前 `watermark.batch_text` 由 `watermark.text` 提供 UI，CLI／Python 與歷史任務保留原 action；舊釘選及使用次數在顯示時合併，讀取不重寫原紀錄。
- 浮水印依張數切換單張輸出檔案／批次輸出資料夾，保留兩種模式的表單值，送出只包含目前啟用的欄位。
- 新增工具時同步確認結果的呈現方式。改名需區分預覽與實際變更，中繼資料需可閱讀及搜尋；一般使用者不應依賴原始 JSON 判斷結果。
- 任務與結果需保留原工具身分。切換工具不得繞過未完成任務的送出限制；較舊的輪詢回應不得覆蓋新增或取消後的狀態。
- 延遲的圖片預覽與選檔回應須檢查目前工具及請求版本，避免更新已切換的表單。
- 維持繁體中文操作文字、明確欄位標籤、鍵盤操作及必填提示。一般操作與開發用 JSON 分開，長路徑與結果表格不得撐寬整個頁面。

## 靜態版與共用素材

| 路徑 | 責任 |
| --- | --- |
| `web/app.mjs` | 選檔／拖曳、排序、忙碌狀態、預覽版本與下載生命週期 |
| `web/model.mjs` | 檔案／尺寸限制、合成版面與浮水印幾何計算 |
| `web/render.mjs`、`web/pdf.mjs` | Canvas 影像輸出、PDF.js 單頁渲染及資源釋放 |
| `web/fields.mjs`、`web/watermark-editor.mjs` | 欄位、滑桿、浮水印指標與鍵盤互動 |
| `web/build.mjs`、`web/preview.mjs` | 靜態產物建置、僅供 loopback 使用的 HTTP 預覽 |
| `imgtools/ui/static/shared/` | 兩版共用的 `theme.css` 與 `icons/` 唯一來源 |

- 靜態版只處理使用者選取的 File，不上傳圖片、PDF、密碼或檔案路徑；不加入本機路徑 API、任意遠端檔案載入或寫回原檔。
- 影像入口為 `renderImages()`，PDF 入口為 `renderPdf()`。驗證與幾何規則集中於模型；預覽、控制框與正式輸出使用一致座標，控制點不可畫入成品。
- 選檔與拖曳共用載入流程；新一批檔案全部驗證／解碼成功才加入，失敗保留既有輸入與成果。載入及輸出期間鎖定輸入。
- 非同步預覽核對請求版本；工具、排序或參數變更後立即使舊下載失效。清除及替換時釋放 Blob URL、圖片與 PDF 資源，密碼不持久保存。
- 檔案大小、張數、像素及邊長限制以 `web/model.mjs` 為準；超限應提示使用者，不默默降低輸出解析度。不得假設 PDF.js 與本機 PyMuPDF 像素完全相同。
- 保留繁體中文、明確標籤、鍵盤操作與觸控捲動。浮水印移動、縮放及旋轉控制點使用 Pointer Events；只有操作控制點時停用預設觸控手勢。
- 共用配色與圖示只修改 `shared/` 原始檔，再重新建置 `web/dist/`；不要手改產物。主圖示為藍底白線，功能圖示沿用品牌藍色，需同時確認頁首與 favicon 的辨識度。
- PDF.js 與 worker、CMap、字型、WASM 及授權檔隨產物同站提供；依賴版本與 lockfile 同步維護，不改成執行時依賴 CDN。
- 建置需保留完整儲存庫以讀取共用素材，部署只提供 `web/dist/`。`npm.cmd start` 建置後啟動 5859 預覽，原始碼修改後需重建；`cf:dev` 在 5860 模擬 Pages，兩者均不發布。

## 驗證與本機環境

優先使用專案 `.venv`，安裝方式見 README。Windows 啟動器會優先使用 `.venv\Scripts\python.exe`，再回退到 `%LOCALAPPDATA%\Python\bin\python.exe`；`ImgTools.cmd --check` 可檢查選用的解譯器而不啟動服務。不要將個人電腦上的 Python 絕對路徑寫入程式或測試。靜態版 Node 版本以 `web/.node-version` 為準；Windows 使用 `npm.cmd`，以 `npm.cmd ci --ignore-scripts` 安裝鎖定依賴，不省略 Wrangler 需要的平台 optional dependencies。

- 使用者已指定共用 Python 環境時，先確認該環境的解譯器與依賴，再將下列指令中的 Python 路徑替換為該環境；不必另建 `.venv`。`ImgTools.cmd` 不會自動尋找其他虛擬環境，不可僅憑套件所在位置推定啟動器使用的環境。
- 測試及瀏覽器驗證使用臨時目錄或 `data/` 下獨立的測試資料，並設定 `IMGTOOLS_STATE_DIR` 隔離偏好與 manifest。不得改動使用者原始圖片、預設偏好或既有任務成果。
- 先執行與變更相關的測試。程式行為變更完成後執行下列完整檢查；只修改文件時核對內容、路徑與差異格式即可。

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests
node --test tests/frontend.test.mjs
& .\.venv\Scripts\python.exe -m compileall -q imgtools tests
& .\.venv\Scripts\python.exe -m imgtools list
# 靜態版模型測試與部署產物建置（先安裝 web 依賴）
npm.cmd --prefix web run cf:build
git diff --check
```

- 對修改的 JS 模組執行 `node --check <檔案路徑>`。任務變更優先檢查 `test_jobs.py`、`test_job_http.py` 與 `frontend.test.mjs`，包含排隊、取消、部分輸出、去重及連線失敗。
- UI 變更須以瀏覽器驗證桌面與窄視窗，至少檢查 1280px 與 375px 寬度。涉及編輯器或結果時，驗證圖片順序、預覽尺寸、改名語意、中繼資料搜尋與長輸出路徑；區分自動測試與實際操作已確認的範圍。
- 靜態版以 HTTP 載入建置後的 `dist` 驗證，不以 `file://` 取代；檢查四工具切換、選檔／拖曳、排序、過期結果、實際 PNG 下載、PDF 錯誤及資源載入。互動變更另檢查指標／鍵盤與觸控模擬；窄視窗或觸控模擬不代表實體手機已驗證。
- 結束時重設測試用視窗尺寸，停止本次建立的測試服務。不要停止使用者原先執行的服務或刪除既有資料。

## 文件與 Git

- README 保持精簡，只放版本入口、功能摘要、安裝與基本使用。action、API 與維護細節放 `docs/ARCHITECTURE.md`；靜態版契約放 `docs/WEB_VERSION.md`；建置及發布設定放 `docs/CLOUDFLARE_PAGES.md`，操作範例放 `examples/`。變更時同步更新受影響文件，避免把完整操作規格再次堆回 README。
- 驗證紀錄註明日期、版本與限制；歷史結果保留當時情境，不把某次測試數量或「未部署」當成永久現況。本機 UI 歷史見 `docs/UI_ITERATION.md`。
- Cloudflare Pages 的 Git 整合、分支及建置設定在遠端管理；`web/wrangler.jsonc` 不代表已完成 Git 連接。本專案部署流程以 `main` 為正式分支，共用素材變更也需納入建置監看。
- 修改前檢查 Git 狀態並保留既有工作。Commit message 使用繁體中文 Conventional Commit；只要求撰寫訊息時不提交，收到明確 commit 指示後才提交已確認的變更，不推定 push 或部署授權。
- `cf:build` 只測試與建置；`cf:deploy`、`cf:deploy:preview` 會實際上傳，推送 `main` 也可能觸發正式部署。完成本機建置不等於已驗證線上發布。

完整維護說明見 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，靜態版範圍見 [docs/WEB_VERSION.md](docs/WEB_VERSION.md)，發布流程見 [docs/CLOUDFLARE_PAGES.md](docs/CLOUDFLARE_PAGES.md)。
