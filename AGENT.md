# AGENT.md

ImgTools 已完成從舊腳本集合到 registry-driven 本機工具平台的遷移。專案不再保留或依賴 `legacy/`。

## 開發規則

1. 新功能先定義可觀察行為與 interface，再補 failing test，最後實作。
2. UI、CLI 與自動化一律經過 `imgtools.service.runner.run_tool()`，不可各自直呼 core。
3. 新 action 必須在 `imgtools/service/registry.py` 註冊；前端表單會從 registry 自動產生。
4. Core 不解析 CLI、不啟動 UI、不使用固定輸入路徑，也不直接 `sys.exit()`。
5. Rename 維持預設 dry-run；輸出維持預設不覆寫；不可自動刪除使用者輸入。
6. 測試應通過公開 interface 驗證行為，不為內部實作保留相容層。

完整維護說明見 `docs/ARCHITECTURE.md`。

