# ImgTools

ImgTools 是一套完全在本機執行的影像工作台。所有功能共用同一份 action registry，可由瀏覽器 UI、CLI 或 Python 呼叫；輸入檔不會上傳到網路。

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

`merge.stack_vertical` 是快速上下對比工具：選擇 2～4 張同寬圖片後，可在 UI 依「由上到下」調整順序，再輸出一張不縮放、不加間距的 PNG。例如兩張 1920×1080 會輸出為 1920×2160。

`merge.dialogue_stack` 是動畫台詞敘事工具：第一張作為完整基底，後續圖片只取底部全寬字幕帶並依順序向下排列。UI 的「字幕剪輯台」可拖曳字幕帶起點、調整每句間距並即時預覽；預覽使用縮圖，正式輸出仍保留原始解析度且不做淡入混合。圖片可經由本機選檔器載入，也可直接貼上路徑由本機服務產生預覽。

`watermark.text` 的 UI 會把浮水印工作拆成即時預覽與控制面板：可一次選取一張或多張圖片，拖曳文字到畫布內的自訂位置，或使用中央／四角預設位置，再用角度、不透明度、字型大小、顏色與邊界距離微調。預設角度為 30 度、透明度為 25%，字型大小 0 代表依圖片自動。開啟「重複平鋪」即可用同一組設定覆蓋整張圖片；`watermark.batch_text` 仍可作為明確的批次工作入口。

## 安裝

需要 Python 3.14 或相容版本：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

影片轉換使用 `imageio-ffmpeg` 提供的 ffmpeg；也可用環境變數 `IMGTOOLS_FFMPEG` 指定執行檔。

## 使用本機 UI

最簡單的方式是在專案最外層直接執行：

```powershell
& .\.venv\Scripts\python.exe .\main.py
```

它會啟動 `127.0.0.1:8765` 並自動開啟瀏覽器。需要調整 host、port 或停用自動開啟瀏覽器時，改用完整 CLI：

```powershell
& .\.venv\Scripts\python.exe -m imgtools ui
```

預設開啟 `http://127.0.0.1:8765`。如不希望自動開啟瀏覽器：

```powershell
& .\.venv\Scripts\python.exe -m imgtools ui --no-browser
```

UI 由 registry 動態產生工具清單與表單，支援選檔、固定／來源檔名模式、常用功能、PDF 預設 DPI、執行結果與 manifest。

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
```

架構、所有入口、interface contract、新增工具流程與維護地圖請見 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
