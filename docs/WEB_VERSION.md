# ImgTools 靜態版

線上使用：[imgtools.jwander.net](https://imgtools.jwander.net/)。免安裝，檔案在瀏覽器處理，成果下載至使用者裝置。

## 範圍與 interface

目前方向是四項特定功能的靜態網頁開源工具，介面只保留工具名稱、操作說明與必要狀態，不使用宣傳標語或工具副標。本機背景啟動暫緩，下方量測僅保留為先前評估紀錄。

`web/` 是獨立、無 Python 後端的瀏覽器版本，只提供台詞疊圖、直向疊圖、文字浮水印、PDF 單頁 PNG。保留本機版全部工具；本機 action 仍經由 Python runner。靜態版以 `renderImages(action, images, params)` 作為影像處理入口，PDF 由 PDF.js 在瀏覽器處理。

- 選檔只讀取使用者選取的 File，不傳送影像、PDF、密碼或檔案路徑到伺服器。
- 桌面可直接拖曳圖片進入頁面，與選檔共用同一份驗證。圖片追加到清單，PDF 替換目前檔案；不支援資料夾或遠端網址。整批新檔案驗證／解碼失敗時保留既有輸入與成果；要換整批圖片先按清除。
- 圖片依選取清單排序，可上移、下移與移除。直向疊圖要求同寬 2–9 張；台詞疊圖要求同尺寸 2–12 張，首張完整、後續字幕帶覆蓋合成。
- 台詞的字幕帶起點／每句間距都有預覽旁的滑桿，與數字欄位同步；字幕帶縮短時，必要時自動降低間距至可用高度。
- 浮水印支援單張與批次、角度、透明度、顏色、預設／自訂位置、平鋪，輸出 PNG。拖曳預覽中的十字箭頭可自訂位置，斜箭頭可調字級，環形箭頭可繞文字中心旋轉；控制點只顯示 SVG 圖示，保留輔助閱讀名稱與滑鼠提示。亦可用大小／角度滑桿、數字欄位與方向鍵操作（每次 1 度，Shift 每次 10 度）。預覽首張；批次逐張處理並提供個別下載。
- 自訂位置以圖片寬高比例套用各張圖片，字級為來源像素（0 為依各圖自動計算）。可容納的字框會限制在圖片內；文字超過整張畫面時仍可能裁切，請縮小字級。平鋪模式可用滑桿調整整體字級與角度，不提供單個浮水印控制點。控制點與框線不會輸出到成品。
- PDF 支援指定頁碼、DPI、密碼，輸出 PNG。渲染結果不保證與 PyMuPDF 像素一致。
- 參數錯誤不產生成品；變更工具、檔案或設定後移除過期成果；處理期間鎖定輸入。提供清除按鈕釋放檔案與成品。
- 設定尺寸與總像素上限，超限顯示可操作錯誤，不默默降低輸出解析度。

## 邊界

不提供平移長截圖、伺服器佇列、本機路徑、系統字型檔路徑或寫回原檔。瀏覽器另存下載，不保留原圖片 metadata。中文字型使用裝置可用字型，跨系統外觀可能不同。

靜態版已提供線上使用；本機背景常駐與 Windows 排程仍屬下方的歷史評估範圍。

## 共用視覺與操作

兩版採用相同藍白配色、工具卡片選取樣式及淺藍預覽底色，本機保留完整工具庫與任務工作台，以 `LOCAL`／`WEB` 區分版本。頁首及 favicon 共用「影像工作台」SVG：主圖示為 `#225c99` 藍色圓角底與白色線條，讓深色背景下仍可辨識；四功能圖示使用品牌藍色線條。

圖示唯一來源為 `imgtools/ui/static/shared/icons/`，配色與字型由 `imgtools/ui/static/shared/theme.css` 共用，靜態建置複製整個 shared 目錄至 `dist/shared/`。主圖示以 32px、功能圖示以 24px 顯示，旁邊保留工具名稱；圖片使用空 alt，避免輔助閱讀重複朗讀。靜態版手機保留可捲動區域、48px 觸控控制點與滑桿，數字欄位採 16px 字級，提供前往預覽／返回設定的跳轉入口。本機窄視窗工具庫可收合，常用工具使用兩欄卡片。

## 預覽與部署

```powershell
cd web
npm.cmd ci --ignore-scripts
npm.cmd run build
npm.cmd run preview
```

網址為 `http://127.0.0.1:5859`，可用 `PORT` 環境變數調整預覽埠。Ctrl+C 停止預覽。Node.js 只用於安裝、複製產物和本機預覽，不是上線後的執行依賴。PDF.js 版本固定於 package-lock.json。

亦可用 `npm.cmd start` 一次完成建置與預覽。部署方向改採 Cloudflare Pages Git integration，監看 GitHub `main`；`web/wrangler.jsonc` 指定產物，`web/.node-version` 指定建置版本。首次連結、Pages 欄位與發布流程見 [CLOUDFLARE_PAGES.md](CLOUDFLARE_PAGES.md)。Wrangler 需要平台專用 optional dependencies，因此安裝時不要加 `--omit=optional`。

部署時上傳 `web/dist/` 全部內容至 HTTPS 靜態主機；Cloudflare 建置命令為 `npm ci --ignore-scripts && npm run cf:build`（工作目錄 `web`，設定 `SKIP_DEPENDENCY_INSTALL=1`），輸出目錄 `dist`。使用相對資源路徑，可放在子目錄。主機須正確提供 `.mjs` 的 JavaScript MIME 與 `.wasm` 的 `application/wasm`。不要把專案根目錄、data、node_modules 或本機 API 公開。

套件與 CMap、字型、WASM 同站提供；PDF 工具才延遲載入 PDF.js。未加入分析追蹤、外部字型或 Service Worker。頁面未操作時不輪詢 API。PDF.js Apache-2.0 授權及資源附帶授權隨產物保留。執行 `npm test` 驗證瀏覽器模型；`node --test tests/frontend.test.mjs` 仍是原本本機前端測試。

## 本機無黑窗常駐評估

本機服務可以改以 `pythonw.exe` 或工作排程器啟動，並使用 `python -m imgtools ui --no-browser` 對應的參數；仍僅監聽 `127.0.0.1:5858`。隱藏視窗不會降低或提高影像演算法本身的負載。

建議登入時啟動、同一任務已存在就略過，而非每天重複開一份。由於現有選檔器使用 tkinter，應在使用者登入的互動工作階段啟動。真正實作時還需記錄錯誤到檔案、提供停止入口與辨認既有服務，避免關掉使用者原先的程序。不可只把 CMD 視窗藏起來，卻失去日誌及停止方式。

2026-09-23 的短時間量測：以獨立狀態資料夾、15858 埠、無瀏覽器連線啟動服務，在啟動後等待 2 秒，再取樣 10 秒，CPU 累計增量 0.0 秒、Working Set 約 26.9 MiB、Private Memory 約 16.2 MiB。使用測試用 Python 3.12，這是「新啟動、未處理圖片」的短樣本，不是長期記憶體或影像處理峰值保證；瀏覽器、圖片解碼與 PDF 輸出另計。原本的任務 worker 使用 condition 等待，沒有忙碌空轉。

本次工作環境沒有專案 `.venv`，原 CMD 的備援 Python 路徑也不存在；回歸使用 bundled Python 與 `data/web-qa-deps` 隔離依賴，未改系統 Python 或原啟動器。日後設定常駐前須先依 README 建立正式 `.venv`。

## 驗證紀錄（2026-09-23）

文件更新查核：線上首頁回應 HTTP 200，標題為「ImgTools 影像工具」，含 `WEB` 版本標示。此次未重新操作線上四工具，也未查核 Cloudflare 帳號、部署 commit 或 Git 觸發紀錄。

以下保留各次實作當時的測試結果；其中「未公開部署」描述該輪工作範圍，不代表目前網站尚未上線。

- 共用本機視覺：五份 SVG 移至 `imgtools/ui/static/shared/icons/`，兩版載入相同圖示及配色。靜態建置、13 項模型測試與跨版本素材內容比對通過；本機工作台的桌面／窄視窗操作驗證見 [UI_ITERATION.md](UI_ITERATION.md)。部署監看路徑已納入 shared 目錄，未公開部署。

- 指定 SVG 套用：Chrome 1280px／375px 確認五個圖示載入、四工具切換、鍵盤導覽及無水平溢出；favicon 指向 C 主圖示，五份 SVG 回應 200 與 `image/svg+xml`，console 無錯誤。建置包含 icons，22 項 JS、158 項 Python、JS syntax、compileall、CLI list、diff check 通過。未在實體手機或 Safari 驗證 favicon，未公開部署。

- 圖示控制點與旋轉：新增旋轉方向、跨越 ±180 度及手機控制點分離測試，13 項模型、9 項既有前端、158 項 Python 通過；JS syntax、build、compileall、CLI list、diff check 通過。Chrome 1280px 滑鼠旋轉與方向鍵、375px CDP 觸控旋轉、角度滑桿同步、平鋪、清除及過期下載移除通過，無水平溢出或 console 錯誤。下載 PNG 的變更像素呈設定的近垂直方向且中心位置正確；未在實體手機或 Safari 驗證。

- 互動補強：新增模型測試先失敗再實作，11 項模型、9 項既有前端、158 項 Python 測試通過；compileall、CLI list、修改 JS syntax、build、diff check 通過。
- Chrome 1280px／375px 驗證：合成 drag/drop 檔案事件可追加圖片；錯誤格式不清除既有輸入／成果；字幕滑桿同步與間距上限；實際滑鼠拖曳／縮放；CDP 觸控模擬移動、縮放、pointer cancel；方向鍵調整、平鋪模式、切換工具與清除。小字浮水印控制點保持分離，控制點外可觸控捲動頁面。兩張不同尺寸圖片批次下載 PNG 的變更像素位置，與各圖設定的相對座標相符，console 無錯誤。此為桌面 Chrome 及觸控模擬，未驗證實體手機、作業系統檔案總管拖曳或 Safari。

- 文案精簡：移除頁首標語、右上提示及四工具副標，空白預覽改用操作提示；1280px／375px 四工具切換無水平溢出，台詞預覽與 PNG 產生通過。重新建置與 15 項前端／模型測試通過。未變更影像演算法；本次未重跑 Python 測試。測試服務已停止。

- 新增模型測試先失敗、實作後通過：合成尺寸、字幕帶位置、來源排序、檔案與像素限制。
- Chrome 實際操作：四項工具產生及下載 PNG；台詞排序後重新合成；直向疊圖不同寬度拒絕；兩張批次浮水印；PDF 144 DPI、頁碼超界、加密解鎖與密碼清除。
- 1280px 桌面與 375px 窄視窗檢查；窄視窗切換全部工具無水平溢出，台詞成果與下載可操作。這是桌面 Chrome 窄視窗，不代表已在實體手機或 Safari／Firefox 驗證。
- 一般台詞疊圖、重新排序台詞疊圖及直向疊圖的瀏覽器下載 PNG，與 Python runner 產生的對照圖逐像素相同（限此次測試圖片）。另以測試修正半像素裁切時 JavaScript 與 Python 捨入差異。
- 原本 Python 完整回歸 158 項通過，既有前端 9 項、新增模型 6 項通過；compileall、CLI list、JS syntax、diff check 通過。首次 Python 回歸因缺少依賴失敗，隔離安裝後補驗通過。
- `npm install` 當時回報 0 已知弱點，不代表永久安全保證。
- 未測大檔壓力、長期常駐、所有 PDF 字型／色彩格式或實體手機記憶體極限；未公開部署。
