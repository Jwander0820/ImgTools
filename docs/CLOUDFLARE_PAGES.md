# Cloudflare Pages 直接部署

此方案使用 Pages Direct Upload，從電腦直接上傳 `web/dist/`，不連 GitHub／GitLab。Cloudflare 只提供 HTML、CSS、JavaScript、PDF.js 和相關靜態資源。使用者的圖片、PDF、密碼與成品皆在瀏覽器內處理，不需要 Python、容器、Pages Functions、資料庫或檔案儲存服務。

## 先在電腦測試

需要 Node.js 22.13+ 或 24+。第一次安裝或 lockfile 更新後執行 `npm.cmd ci --ignore-scripts`；不要加 `--omit=optional`，Wrangler 的本機模擬依賴平台專用套件。

```powershell
cd D:\Tools\ImgTools\web
npm.cmd ci --ignore-scripts
npm.cmd start
```

`start` 先建置，再啟動 `http://127.0.0.1:5859`。瀏覽器自行開啟此網址；Ctrl+C 停止。之後每次測試只需執行 `npm.cmd start`。修改原始碼後須重新建置；此指令不是原始碼熱更新開發伺服器。

若要測試接近 Pages 的資源服務行為：

```powershell
npm.cmd run cf:dev
```

網址為 `http://127.0.0.1:5860`，僅本機模擬，不會上傳或部署，也不需要先登入。Wrangler 在電腦啟動模擬器，不代表正式網站需要執行 Worker 程式。

## 設定檔

`web/wrangler.jsonc`：

```json
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "imgtools-web",
  "pages_build_output_dir": "./dist",
  "compatibility_date": "2026-09-23"
}
```

- `name`：Pages 專案名稱，正式建立前可改成想要的名稱。建立指令與設定檔名稱必須相同。
- `pages_build_output_dir`：只上傳 `web/dist/`，不會上傳原始圖片、data、本機 Python 工具或 node_modules。
- `compatibility_date`：固定 Wrangler／Pages 相容設定；本案沒有自訂 Functions。
- 不需在檔案寫入 API Token。登入授權由 Wrangler 管理；本設定未指定帳號或自訂網域。

這份設定預備給新的 Direct Upload 專案。若要沿用已有專案，先確認其名稱、正式分支與既有設定，再調整此檔，不要直接套到不相關專案。

## 第一次正式發布

以下指令由你決定發布時才執行；建立專案與部署會變更 Cloudflare。

```powershell
cd D:\Tools\ImgTools\web
npx.cmd wrangler login
npx.cmd wrangler pages project create imgtools-web --production-branch main
npm.cmd run cf:deploy
```

`login` 會開啟瀏覽器授權。建立時若改用其他名稱，同步修改 `wrangler.jsonc` 的 `name`。如果你可存取多個 Cloudflare 帳號，依 Wrangler 提示選定目標帳號；需要固定帳號時可在本機設定 `CLOUDFLARE_ACCOUNT_ID`。

部署完成後使用 Wrangler 回傳的 `pages.dev` 網址；實際可用名稱以建立結果為準。這裡的 `main` 是 Pages 的正式環境分支標籤，不需要 GitHub；指令明確指定它，避免目前 Git 分支意外變成預覽部署。

之後更新：

```powershell
npm.cmd run cf:deploy
```

此指令每次先建置，再部署到正式環境。若想先發布另一個預覽網址、不替換正式版：

```powershell
npm.cmd run cf:deploy:preview
```

預覽也會上傳到 Cloudflare 並產生可存取網址，不是本機測試。設定自訂網域時，到該 Pages 專案的 Custom domains 新增即可，無需改影像處理程式。

## 不使用命令列上傳的替代方式

先執行 `npm.cmd run build`，再到 Cloudflare Dashboard 的 Workers & Pages 建立 Pages Direct Upload 專案，拖曳 `web/dist` 資料夾或其內容的 ZIP。Wrangler 設定檔供 CLI 使用；Dashboard 拖曳上傳不會讀取它。

## 驗證與發布界線

此次準備設定與指令，沒有執行登入、建立遠端專案、上傳、網域設定或正式部署。正式網域、帳號權限及線上結果仍須發布時確認。Direct Upload 專案日後不能直接改成 Git integration，若改變部署方式需另建專案。

2026-09-23 本機驗證：Wrangler 4.136.3 成功讀取設定並在 5860 埠啟動；HTML、MJS、PDF worker、WASM 回應 200 且 MIME 正確；Chrome 在 Pages 模擬環境成功將測試 PDF 輸出並下載為 1920 × 1440 PNG，console 無錯誤。`npm start` 另以隔離埠 15859 確認可建置與提供頁面。6 項模型測試及 `git diff --check` 通過。本次未變更影像演算法或 Python 程式，未重跑 Python 測試。

官方依據（2026-09-23 查核）：[Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)、[Wrangler 設定](https://developers.cloudflare.com/pages/functions/wrangler-configuration/)、[Pages CLI](https://developers.cloudflare.com/workers/wrangler/commands/pages/)。
