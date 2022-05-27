# 圖像處理小工具

### 合併merge_img資料夾下的圖片
1. 合併為 多幀TIF檔案
2. 合併為 多頁PDF檔案
3. 合併為 GIF檔案

### 讀取圖片檔案的exif資訊
1. pil_tag_v2 : 透過**PIL的tag_v2**讀取檔案的exif資訊
2. tifftools_ifds : 透過**tifftools**讀取檔案，並提取出exif資訊
3. exifread_ifds : 透過直接開啟檔案，使用**exifread**提取出exif資訊，讀取多幀tif推薦使用
4. !image.save使用tiffinfo改寫tif tag的方法
5. !使用tifftools改寫tif tag的方法 (謹慎使用)