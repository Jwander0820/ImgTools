# ImgTools

ImgTools 是一套完全在本機執行的影像工作台。本機版所有功能共用同一份 action registry，可由瀏覽器 UI、CLI 或 Python 呼叫；輸入檔不會上傳到網路。

另有獨立的 **靜態網頁版**（`web/`），提供台詞疊圖、快速直向疊圖、文字浮水印與 PDF 單頁轉 PNG。全部在使用者瀏覽器處理，不需要 Python API、容器或檔案上傳；完整本機版仍然保留。

靜態版可選檔或拖曳圖片加入清單，台詞疊圖提供預覽旁的字幕起點／間距滑桿；浮水印可用圖示控制點拖曳定位、縮放與旋轉，也能用滑桿、數值或鍵盤調整。手機使用相同的觸控控制點，並提供設定與預覽間的跳轉入口。

線上版頁首與 favicon 使用「影像工作台」SVG，四項功能採用同套圖示，素材集中於 `web/icons/`；本機 UI 的視覺統一留待下一階段。

## 靜態網頁版預覽

建置需要 Node.js 22.13+ 或 24+，正式主機只需提供靜態檔案：

```powershell
cd web
npm.cmd ci --ignore-scripts
npm.cmd start
```

開啟 <http://127.0.0.1:5859>。部署目錄是 `web/dist/`，不要公開整個專案；PDF.js 與字型／解碼資源已包含在產物中，不依賴 CDN。只用 `file://` 雙擊 HTML 不能取代 HTTP 預覽。完整範圍、限制、驗證紀錄與本機背景啟動評估見 [docs/WEB_VERSION.md](docs/WEB_VERSION.md)。

Cloudflare 使用 **Pages Direct Upload**，不需連 GitHub：`npm.cmd run cf:dev` 在 5860 埠本機模擬；`npm.cmd run cf:deploy` 會建置並發布。帳號登入、首次建立專案與 `web/wrangler.jsonc` 設定說明見 [Cloudflare 直接部署](docs/CLOUDFLARE_PAGES.md)。

## 功能

| 類別 | Actions |
|---|---|
| Metadata | `metadata.read_tif_tags` |
| Rename | `rename.files_replace`、`rename.folders_replace` |
| PDF | `pdf.render_page`、`pdf.render_all_pages` |
| Merge | `merge.stack_vertical`、`merge.dialogue_stack`、`merge.images_to_pdf`、`merge.images_to_tif`、`merge.panorama_translation` |
| TIF | `tif.split_pages`、`tif.extract_page` |
| GIF / Video | `gif.images_to_gif`、`video.extract_frames`、`gif.mp4_to_gif`、`gif.gif_to_mp4` |
| Image | `crop.text_regions`、`watermark.text`、`watermark.batch_text` |

目前共有 19 個 actions。以 `python -m imgtools list` 取得 registry 的即時完整清單與參數定義。

`merge.stack_vertical` 是快速上下對比工具：選擇 2～9 張同寬圖片後，UI 會顯示各張縮圖並可依「由上到下」調整順序，同時在輸出前即時合成完整長圖預覽；完成後也會在執行結果區顯示可捲動的成品預覽。預覽只使用縮圖且不會提前寫檔，正式輸出仍是一張不縮放、不加間距的 PNG，例如兩張 1920×1080 會輸出為 1920×2160。使用「跟隨來源」命名時，輸出保存在第一張圖片旁，檔名採用排序後最後一張圖片的名稱。

`merge.dialogue_stack` 是動畫台詞敘事工具：第一張作為完整基底，後續圖片只取底部全寬字幕帶並依順序向下排列。UI 的「字幕剪輯台」可拖曳字幕帶起點、調整每句間距並即時預覽；預覽使用縮圖，正式輸出仍保留原始解析度且不做淡入混合。圖片可經由本機選檔器載入，也可直接貼上路徑由本機服務產生預覽。所有由多張圖片合成單一圖片檔的工具，在「跟隨來源」模式都採用實際合成順序中最後一張圖片的檔名；資料夾型輸入則依排序後最後一張命名。

`watermark.text` 的 UI 會把浮水印工作拆成即時預覽與控制面板：可一次選取一張或多張圖片，拖曳文字到畫布內的自訂位置，或使用中央／四角預設位置，再用角度、不透明度、字型大小、顏色與邊界距離微調。預設角度為 30 度、透明度為 25%，字型大小 0 代表依圖片自動。開啟「重複平鋪」即可用同一組設定覆蓋整張圖片；`watermark.batch_text` 仍可作為明確的批次工作入口。

## 安裝

需要 Python 3.14 或相容版本：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

影片轉換使用 `imageio-ffmpeg` 提供的 ffmpeg；也可用環境變數 `IMGTOOLS_FFMPEG` 指定執行檔。

## 使用本機 UI

Windows 可直接雙擊專案根目錄的 `ImgTools.cmd`。它會優先使用專案 `.venv\Scripts\python.exe`；沒有專案環境時，才沿用 `%LOCALAPPDATA%\Python\bin\python.exe`。可執行 `ImgTools.cmd --check` 查看選用的 Python 而不啟動服務。啟動後請保留 CMD 視窗；關閉該視窗就會一併停止 ImgTools 的本機 UI 服務。瀏覽器分頁不會被強制關閉，但停止服務後便無法繼續操作。

也可以在專案最外層手動執行：

```powershell
& .\.venv\Scripts\python.exe .\main.py
```

它會固定啟動 `127.0.0.1:5858` 並自動開啟瀏覽器；若 5858 已遭占用，會直接回報錯誤。需要調整 host、port 或停用自動開啟瀏覽器時，改用完整 CLI：

```powershell
& .\.venv\Scripts\python.exe -m imgtools ui
```

預設同樣固定開啟 `http://127.0.0.1:5858`。如不希望自動開啟瀏覽器：

```powershell
& .\.venv\Scripts\python.exe -m imgtools ui --no-browser
```

如其他程式必須連到固定埠，請明確傳入 `--port`；明確指定的埠無法使用時會直接回報錯誤，不會靜默改埠。

UI 由 registry 動態產生工具清單與表單，支援選檔、固定／來源檔名模式、常用功能、PDF 預設 DPI、執行結果與 manifest。預設檔名模式保存在 `data/.imgtools/preferences.json`，重新啟動或改用其他 port 時仍會沿用。

常用工具顯示為精簡捷徑，窄視窗的工具庫可展開／收合；主要處理按鈕固定在畫面底部。執行結果會標示來源工具：改名預覽顯示前後對照與衝突，TIF 中繼資料可搜尋，圖片成果可切換縮圖，並可開啟檔案或所在資料夾。

UI 任務依序單工執行，可在切換工具或重新整理頁面後繼續查看佇列、耗時及處理進度。同一工具有未完成任務時會暫停再次送出；不同工具可加入佇列。排隊中的任務可立即取消，執行中的影像任務在安全節點停止，影片轉換會終止 ffmpeg。原生影像編碼等步驟須完成當前步驟才能回應取消；已完成的輸出會保留。改名開始後不可取消，避免只套用部分名稱。任務歷史保留於服務記憶體中（最多 50 個已結束任務）；重啟服務會清除佇列，磁碟上的 manifest 仍保留。

## 使用 CLI

```powershell
# 列出工具
& .\.venv\Scripts\python.exe -m imgtools list

# 查看單一工具
& .\.venv\Scripts\python.exe -m imgtools describe pdf.render_page

# 執行工具
& .\.venv\Scripts\python.exe -m imgtools run pdf.render_page `
  --param 'pdf_path=D:\input\sample.pdf' `
  --param 'page=1' `
  --param 'dpi=192'

# 也可一次傳入 JSON 參數
& .\.venv\Scripts\python.exe -m imgtools run watermark.text `
  --params-json '{"input_path":"D:\\input\\photo.png","text":"Sample"}'
```

CLI 輸出為 JSON。`--no-manifest` 可停用該次 manifest；`examples/tasks/` 是可複製的 payload 範例，不是可直接執行的 task-file 指令。

## 安全與輸出

- 批次改名預設只預覽，必須明確傳入 `confirm=true` 才會變更檔名。
- 明確指定的輸出檔若已存在，預設拒絕覆寫；只有 `overwrite=true` 才允許覆寫。
- 未指定輸出時會自動避開既有檔案，以 `-2`、`-3` 依序命名。
- 執行紀錄與偏好預設保存在 `data/.imgtools/`；可用 `IMGTOOLS_STATE_DIR` 改到其他位置。
- manifest 會遮蔽 `password`、`token`、`secret`、`api_key` 等敏感參數。

## 開發與維護

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests
& .\.venv\Scripts\python.exe -m compileall imgtools tests
node --test tests/frontend.test.mjs
```

專案協作規則請見 [AGENTS.md](AGENTS.md)。架構、所有入口、interface contract、新增工具流程與維護地圖請見 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
