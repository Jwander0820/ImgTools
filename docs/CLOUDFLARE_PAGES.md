# Cloudflare Pages 與 GitHub 自動部署

線上入口：[imgtools.jwander.net](https://imgtools.jwander.net/)。以下保存本專案的建置與發布設定，供後續維護或重新建立環境使用。

使用 Cloudflare Pages 的 Git integration：GitHub 保存原始碼，Cloudflare 建置並提供網站。這不需要啟用 GitHub Pages。推送到正式分支後，GitHub 整合事件會觸發 Cloudflare 建置，不需要自己寫定時拉取腳本。

使用者圖片、PDF、密碼與產生的 PNG 都在瀏覽器內處理。Cloudflare 只提供 HTML、CSS、JavaScript、圖示、PDF.js 與相關靜態資源，沒有 Python 後端、Functions 或圖片上傳服務。

## 第一次連接 GitHub

先將含 `web/` 的版本提交並推送至 GitHub；只在本機 commit 不會觸發遠端部署。初次在 Cloudflare 按 Save and Deploy 也會立即開始建置並公開網站。

在 Cloudflare Dashboard 的 Workers & Pages 建立 **Pages** 專案，選擇連接 Git repository，授權 Cloudflare GitHub App 存取 `Jwander0820/ImgTools`。可只授權這個儲存庫。使用原生整合，不需要 GitHub Actions 部署 workflow，也不需要在儲存庫放 Cloudflare API Token。

| 欄位 | 設定值 |
| --- | --- |
| Repository | `Jwander0820/ImgTools` |
| Project name | `imgtools-web`（若改名，同步修改 `web/wrangler.jsonc`） |
| Production branch | `main` |
| Framework preset | `None` |
| Root directory | `web` |
| Build command | `npm ci --ignore-scripts && npm run cf:build` |
| Build output directory | `dist`（相對於 `web`，不要再填 `web/dist`） |
| Build system | v3 |
| Environment variable | `SKIP_DEPENDENCY_INSTALL=1`（正式與預覽都設定） |
| Node.js | 由 `web/.node-version` 指定 `24.18.0` |

`cf:build` 先執行 `tests/web-model.test.mjs`，成功才產生部署目錄。`npm ci` 使用已提交的 lockfile；跳過 Cloudflare 自動安裝可避免同一輪安裝兩次。不要加入 `--omit=optional`，Wrangler 的平台套件需要 optional dependencies。建置變數應在 Pages 建置設定中配置，不是 `wrangler.jsonc` 的執行期 `vars`。

GitHub 授權、儲存庫、正式分支及建置命令屬於 Cloudflare 專案設定，**不能只靠 `wrangler.jsonc` 完成連接**。本專案的 Wrangler 設定只定義名稱、靜態產物路徑及相容日期。

## 分支與更新範圍

在 Settings → Builds／Build → Branch control 啟用 `main` 的自動部署。本專案預設分支已改名為 `main`；既有 Pages 專案也須同步更新 Production branch。

- 推送 `main`：建置成功後更新正式網站。
- 預覽分支：可使用 Custom branches，只包含 `preview`；推送該分支時取得預覽網址，合併至 `main` 才更新正式版。若暫時不用預覽，可選 None。
- 本機修改或 commit：不會更新網站，必須完成 push。
- 建置失敗：查看 Pages 建置日誌及對應 commit，修正後再次推送；不要只看 GitHub push 成功就認定網站已更新。

建議在 Build watch paths 的 Include paths 設定以下三項，Exclude paths 留空：

```text
web/*
tests/web-model.test.mjs
imgtools/ui/static/shared/*
```

此處是相對於儲存庫的路徑；Pages 的 `*` 包含下層目錄。共用圖示與配色位於 `imgtools/ui/static/shared/`，必須納入才能在素材更新時重建網站；建置時需保留完整 repository，`web/build.mjs` 會讀取此目錄。這樣只改 Python 本機工具或一般文件時，通常可略過網站建置；Cloudflare 對空推送或非常大量的變更有例外，見官方文件。

## 本機預覽與檢查

```powershell
# 從專案根目錄執行
cd web
npm.cmd ci --ignore-scripts
npm.cmd run cf:build
npm.cmd run preview
```

預覽為 `http://127.0.0.1:5859`。日常也可執行 `npm.cmd start` 建置並啟動預覽；Ctrl+C 停止。原始碼修改後須重新建置，這不是熱更新伺服器。`npm.cmd run cf:dev` 則在 `http://127.0.0.1:5860` 本機模擬 Pages，不會部署。

## 已經建立 Direct Upload 專案的情況

Cloudflare 不允許把既有 Direct Upload 專案直接切成 Git integration。若要用原生 GitHub 自動建置，需另建 Git-integrated Pages 專案，再處理自訂網域移轉；不要刪除既有站點來試設定。

另一種選擇是保留 Direct Upload，讓 GitHub Actions 建置後用 Wrangler 上傳，需要配置帳號與 API Token secrets。本專案目前採原生 Git integration，沒有加入第二套部署 workflow。

建立新專案時，請使用上方的連接 Git 流程，不要執行先前版本文件的 `wrangler pages project create` 指令建立 Direct Upload 專案。

## 保留的手動部署指令

連接 Git 後日常更新以 push 為主。已確認目標專案與正式分支時，仍可用 Wrangler 手動部署到該 Git-integrated 專案：

```powershell
npx.cmd wrangler login
npm.cmd run cf:deploy
# 或手動發布預覽：
npm.cmd run cf:deploy:preview
```

兩者都會實際上傳。正式指令固定 `--branch main`，預覽為 `--branch preview`，應與 Pages 設定一致。手動部署可能發布尚未推送的本機內容，不能用來證明 Git 自動部署已接通。

## 流量與限制

依 2026-09-23 官方文件，Pages 純靜態請求免費且不限次數，產品頁列出不限頻寬。Free 方案仍有每月 500 次建置、同時 1 次建置、每站 20,000 個檔案及每檔 25 MiB 等限制；Functions 另計。本工具在瀏覽器處理圖片，因此使用者的原圖及成品大小不會直接轉成主機上下載流量。

GitHub Pages 則有每月 100 GB 的軟性頻寬限制，且限制用於線上業務、電子商務及主要提供商業 SaaS 的網站。免費開源工具不因流量增加就自動屬於商業用途；把原始碼放在 GitHub、由 Cloudflare 提供網站，並不是使用 GitHub Pages 主機。

## 目前狀態與查核紀錄

2026-09-23 文件更新：使用者已提供線上版本網址，實際請求首頁回應 HTTP 200，頁面標題為「ImgTools 影像工具」並含 `WEB` 標示。此次僅確認網站可連線，未登入 Cloudflare 查核帳號、專案、目前部署 commit 或真實 Git 自動建置紀錄。

### 先前部署準備紀錄（2026-09-23）

以下是網站上線前的查核結果，保留作為環境與測試紀錄；當時的待辦不代表目前仍未部署。

當時靜態版、共用圖示與浮水印整合已推送至 GitHub（`a22fc89`）。GitHub 預設分支與本機追蹤分支已由 `master` 改為 `main`，提交紀錄不變；該輪登入的 Cloudflare 帳號尚無 ImgTools Pages 專案。

同日產物為 214 個檔案、合計約 6.35 MiB，最大檔案約 2.13 MiB，符合上述單檔與檔案數限制。這是全部產物大小，不等同每次造訪的傳輸量；PDF 資源延遲載入，瀏覽器快取也會影響流量。

本機以 Node 24.18.0 執行 `npm ci --ignore-scripts` 與 `npm run cf:build`，13 項模型測試及建置通過，`git diff --check` 通過；尚未驗證 Cloudflare Linux 建置環境及真實 Git 觸發。此輪只調整建置指令、版本設定及文件，影像程式與 UI 未變更，沿用前輪瀏覽器及 Python 回歸紀錄。

該輪已推送網站程式，但未建立 Cloudflare 遠端專案或部署；首次 GitHub 授權、Pages 建立及真實推送驗證是當時列出的後續工作。

官方依據：[Git 整合](https://developers.cloudflare.com/pages/configuration/git-integration/)、[分支控制](https://developers.cloudflare.com/pages/configuration/branch-build-controls/)、[建置設定](https://developers.cloudflare.com/pages/configuration/build-configuration/)、[建置環境](https://developers.cloudflare.com/pages/configuration/build-image/)、[建置路徑](https://developers.cloudflare.com/pages/configuration/build-watch-paths/)、[Wrangler 設定](https://developers.cloudflare.com/pages/functions/wrangler-configuration/)、[Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)、[Pages 靜態請求計價](https://developers.cloudflare.com/pages/functions/pricing/)、[Pages 產品](https://www.cloudflare.com/products/pages/)、[Pages 限制](https://developers.cloudflare.com/pages/platform/limits/)、[GitHub Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。
