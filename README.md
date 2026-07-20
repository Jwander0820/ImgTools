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
- 圖片合併 PDF、動畫平移長截圖。
- 多頁 TIF 拆頁與指定頁抽出。
- 圖片序列轉 GIF。
- 文字浮水印。

UI 會依 action registry 自動產生參數表單；輸出檔預設不覆寫。

### 快速使用

首頁的「常用功能」可直接開啟 PDF 全頁轉圖、圖片合併 PDF、圖片序列轉 GIF 與文字浮水印。路徑欄位可以貼上，也可以按「選擇」叫出本機檔案／資料夾選擇器；較少使用的輸出位置、覆寫與技術參數收在「進階設定」。

常用單檔輸出可直接留白：

- 圖片序列轉 GIF：輸出到圖片資料夾的 `output.gif`。
- 圖片合併 PDF：輸出到圖片資料夾的 `output.pdf`。
- 文字浮水印：輸出到原圖片旁的 `output.<原副檔名>`。
- 預設檔名已存在時會安全改用 `output-2.*`、`output-3.*`，不會覆寫舊檔。

執行 manifest 集中保存在 Server 端的 `data/.imgtools/manifests/`，不會再於來源或指定輸出資料夾建立 `.imgtools`；密碼等敏感參數會以 `[REDACTED]` 保存。如需改變狀態資料位置，可在啟動前設定 `IMGTOOLS_STATE_DIR`。

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
