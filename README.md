# ImgTools

影像處理工具，提供免安裝的線上版，以及具備完整工具庫、CLI 與 Python 介面的本機版。檔案在瀏覽器或本機處理，不需上傳。

**[開啟線上版：imgtools.jwander.net](https://imgtools.jwander.net/)**

## 功能

| 版本 | 提供功能 |
| --- | --- |
| 線上版 | 台詞疊圖、直向疊圖、文字浮水印（單張／批次）、PDF 單頁轉 PNG |
| 本機版 | 上述功能，加上批次改名、TIF 中繼資料與分頁處理、PDF 全頁轉圖、圖片合成 PDF／TIF、平移拼接、GIF／影片轉換、影片擷取影格與文字區域裁切 |

線上版選檔或拖曳檔案後即可預覽、處理並下載 PNG；完整操作與限制見 [靜態版說明](docs/WEB_VERSION.md)。本機版另有任務佇列、進度與結果紀錄。

## 本機安裝與啟動

需要 Python 3.14+。首次使用可在專案根目錄建立環境；已有安裝相依套件的 Python 環境也可直接沿用：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe .\main.py
```

沿用既有環境時，將指令中的 `.venv\Scripts\python.exe` 換成該環境的 Python 路徑即可。

Windows 使用專案 `.venv` 安裝後，也可雙擊 `ImgTools.cmd`，自動開啟 [本機工作台](http://127.0.0.1:5858)。使用期間保留 CMD 視窗，關閉即停止服務；`ImgTools.cmd --check` 可檢查使用的 Python。

本機服務僅供本機使用，不應直接公開到網路。批次改名預設只預覽，明確確認才套用；輸出預設不覆寫既有檔案。偏好與執行紀錄保存在 `data/.imgtools/`，可用 `IMGTOOLS_STATE_DIR` 指定其他位置。

## CLI

```powershell
# 列出工具與查看參數
& .\.venv\Scripts\python.exe -m imgtools list
& .\.venv\Scripts\python.exe -m imgtools describe pdf.render_page

# 將 PDF 第一頁轉成 PNG
& .\.venv\Scripts\python.exe -m imgtools run pdf.render_page --param 'pdf_path=D:\input\sample.pdf' --param 'page=1'
```

CLI 回傳 JSON；Python 呼叫方式見 [架構指南](docs/ARCHITECTURE.md)，參數範例見 [examples/tasks](examples/tasks/)。

## 開發與文件

靜態版開發使用 Node.js，版本見 [web/.node-version](web/.node-version)：

```powershell
cd web
npm.cmd ci --ignore-scripts
npm.cmd start
```

開啟 [靜態版本機預覽](http://127.0.0.1:5859)，修改後重新建置。部署產物為 `web/dist/`。

- [AGENTS.md](AGENTS.md)：開發規則與驗證指令
- [架構與維護指南](docs/ARCHITECTURE.md)：模組、API、CLI／Python 與新增工具流程
- [靜態版說明](docs/WEB_VERSION.md)：操作、限制與驗證紀錄
- [Cloudflare Pages 部署](docs/CLOUDFLARE_PAGES.md)：Git 自動建置與發布設定
- [本機 UI 迭代紀錄](docs/UI_ITERATION.md)：介面變更與歷次驗證
