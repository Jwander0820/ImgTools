# 圖像處理小工具

## 本機 UI

目前可用下列指令啟動重構後的本機影像工作桌：

```powershell
& 'D:\venv\PythonTools\Scripts\python.exe' -m imgtools ui --host 127.0.0.1 --port 8765
```

已整合到 UI 的工具包含：

- TIF / EXIF metadata 讀取。
- 批次替換檔名與資料夾名稱（預設 dry-run）。
- PDF 單頁或全頁轉 PNG。
- 圖片合併 PDF／多頁 TIF、動畫平移長截圖。
- 多頁 TIF 拆頁與指定頁抽出。
- 圖片序列轉 GIF。
- MP4 拆幀、MP4 轉 GIF、GIF 轉 MP4。
- 白底文字／圖章區域擷取，輸出透明 PNG。
- 可置中、四角或自訂座標的文字浮水印。

UI 會依 action registry 自動產生參數表單；輸出檔預設不覆寫。

### 快速使用

首頁的「常用功能」可由「管理常用功能」釘選，並用下列順序組成最多 8 個快速入口：

1. 使用者釘選的工具，依釘選順序排列。
2. 未釘選工具依成功執行次數與最近使用時間排列。
3. 其餘空位由 action registry 的 `featured` 系統預設補足。

只有成功執行工具才會累積次數；單純瀏覽或開啟工具不會記錄。快速入口會標示「已釘選」、「常用」或「預設」，方便確認每個項目的來源。

釘選與使用次數保存在 Server 本機狀態檔 `data/.imgtools/preferences.json`，不依賴瀏覽器儲存，因此更新前端或更換瀏覽器後仍會保留。這個實際檔案已由 `.gitignore` 排除，不會提交或上傳；可提交的結構範例放在 `examples/preferences.example.json`。若希望將狀態放在版本目錄以外，可用 `IMGTOOLS_STATE_DIR` 指定固定的本機資料夾。

PDF 單頁與全頁工具頁內的「PDF 預設 DPI」也保存在同一份 Server 偏好檔，套用到未明確填寫 DPI 的 PDF 任務；任務自行指定的 DPI 仍有最高優先權。這項設定只在 PDF 工具頁顯示，重構後的 UI、API 與 runner 不再讀取 `legacy/pdf_tools/config.json`。

上方橫軸的「預設檔名」是所有工具共用設定，並保存在目前瀏覽器：

- **統一命名**：使用 `output.<副檔名>`；多檔輸出則使用 `output_page...`、`output_frame...`。
- **跟隨來源**：單檔來源使用 `<原始檔名>.<輸出副檔名>`，資料夾來源使用 `<資料夾名稱>.<輸出副檔名>`；多檔輸出沿用同一個來源名稱作為前綴。
- 只有輸出位置留白時會套用共用設定；手動指定的輸出路徑不會被改名。
- 預設名稱若已存在，會在真正寫檔前改用 `-2`、`-3`。同格式輸出也不會覆寫原始檔，例如 `photo.png` 會先輸出為 `photo-2.png`。

路徑欄位可以貼上，也可以按「選擇」叫出本機檔案／資料夾選擇器；較少使用的輸出位置、覆寫與技術參數收在「進階設定」。

常用單檔輸出可直接留白：

- 圖片序列轉 GIF：輸出到圖片資料夾的 `output.gif`。
- 圖片合併 PDF：輸出到圖片資料夾的 `output.pdf`。
- 圖片合併多頁 TIF：輸出到圖片資料夾的 `output.tif`。
- MP4 拆幀：統一命名模式輸出到影片旁的 `output_frames` 資料夾。
- MP4 轉 GIF：輸出到影片旁的 `output.gif`。
- GIF 轉 MP4：輸出到 GIF 旁的 `output.mp4`。
- 文字浮水印：輸出到原圖片旁的 `output.<原副檔名>`。
- 預設檔名或拆幀資料夾已存在時會安全加上 `-2`、`-3`，不會覆寫舊檔。

影片功能透過 `imageio-ffmpeg` 內附的 ffmpeg 執行；若要指定自訂 ffmpeg，可在啟動前設定 `IMGTOOLS_FFMPEG`。

執行 manifest 集中保存在 Server 端的 `data/.imgtools/manifests/`，常用功能偏好保存在同一狀態目錄的 `preferences.json`；不會再於來源或指定輸出資料夾建立 `.imgtools`。密碼等敏感參數會以 `[REDACTED]` 保存。如需改變狀態資料位置，可在啟動前設定 `IMGTOOLS_STATE_DIR`。

### 合併merge_img資料夾下的圖片 (merge_img.py)
1. 合併為 多幀TIF檔案
2. 合併為 多頁PDF檔案
3. 合併為 GIF檔案

### 讀取圖片檔案的exif資訊 (read_img_exif.py)
1. pil_tag_v2: 透過**PIL的tag_v2**讀取檔案的exif資訊
2. tifftools_ifds: 透過**tifftools**讀取檔案，並提取出exif資訊
3. exifread_ifds: 透過直接開啟檔案，使用**exifread**提取出exif資訊，讀取多幀tif推薦使用
4. !image.save使用tiffinfo改寫tif tag的方法
5. !使用tifftools改寫tif tag的方法 (謹慎使用)

### 將gif轉換成mp4，mp4轉換成gif (gif_tools.py)
1. convert_mp4_to_frame: 將 mp4 影片檔案逐幀儲存
2. convert_images_to_gif: 將指定資料夾中的圖片轉換為一個 gif 檔案
3. mp4_to_gif: 透過moviepy，直接將 mp4 轉換成 gif
4. gif_to_mp4: 透過moviepy，直接將 gif 轉換成 mp4

### 簡易tif工具 (tif_tools.py)
1. save_multipage_tiff: 將多張圖片壓縮成一個多頁 tif 檔案
2. split_all_page: 拆分多頁tif檔並儲存成單頁tif檔
3. process_single_page: 查看或儲存單一頁面的 tif 圖片

### 圖片簡易去背功能 (crop_text.py)
1. 提供白底圖片可以用於快速裁切出圖片並生成去背透明底圖，建議用於文字提取

### 批量變更檔名、資料夾名稱方法 (rename_file_and_folder.py)
1. rename_files_by_string: 指定路徑內，將所有 檔案名稱 的指定字串替換成新字串
2. rename_folder_by_string: 指定路徑內，將所有 資料夾名稱 的指定字串替換成新字串

### 添加浮水印與生成特殊浮水印(watermark)
1. add_watermark.py: 添加指定文字浮水印
2. generate_special_text.py: 生成特殊樣式浮水印(實驗性)

### PDF抽頁工具(pdf_dpi_conversion_tools.py)
0. 使用方法為壓成EXE後在cmd中使用
1. 快速抽取PDF指定頁，並轉換成圖片(.png)


### 研究相關
1. test_cv_minarearect_logic: 透過圖片連續旋轉確認minAreaRect計算角度的邏輯
2. test_multiple_rotated: 測試多次旋轉對圖像造成的改變與破壞
