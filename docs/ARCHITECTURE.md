# ImgTools 架構與維護指南

本文件描述目前程式的實際架構。舊腳本遷移計畫與 `legacy/` 相容層已結束，不再是維護入口。

## 1. 架構總覽

```text
使用者 / 自動化
  ├─ main.py ───────────── 啟動 Browser UI 並開啟瀏覽器
  ├─ Browser UI ── HTTP ── imgtools.ui.server / imgtools.ui.api
  ├─ CLI ───────────────── imgtools.cli
  └─ Python ────────────── imgtools.service.runner.run_tool
                                  │
                                  ▼
                       imgtools.service.registry
                         ToolSpec + ToolParam
                                  │
                    validate / coerce / safety / manifest
                                  │
                                  ▼
                           imgtools.core.*
                                  │
                                  ▼
                     本機輸入檔與產生的輸出檔
```

最重要的 seam 是 `run_tool(action, params)`。UI 與 CLI 只負責接收輸入及顯示結果；參數驗證、安全預設、handler 選擇與結果格式集中在 service module，影像演算法集中在 core module。

## 2. 目錄與責任

| 路徑 | 責任 | 維護時機 |
|---|---|---|
| `main.py` | 固定啟動 `127.0.0.1:5858` UI 並開啟瀏覽器的便利入口 | 預設 UI 啟動行為改變時 |
| `imgtools/__main__.py` | `python -m imgtools` 的唯一模組入口 | CLI 啟動方式改變時 |
| `imgtools/cli.py` | `list`、`describe`、`run`、`ui` 命令 | 新增命令列層級能力時 |
| `imgtools/service/registry.py` | 所有 action、參數 metadata 與 handler 對應 | 新增／修改工具時必改 |
| `imgtools/service/runner.py` | 驗證、型別轉換、安全預設、統一結果、manifest | 所有入口都需要的新執行規則 |
| `imgtools/service/schemas.py` | 將 `ToolSpec` 轉成可供外部讀取的 schema | schema contract 改變時 |
| `imgtools/service/safety.py` | 共用覆寫與高風險預設 | 新增破壞性能力前 |
| `imgtools/service/preferences.py` | 常用 actions、使用次數、PDF DPI | UI 偏好改變時 |
| `imgtools/service/manifest.py` | 執行紀錄與敏感欄位遮蔽 | 稽核格式改變時 |
| `imgtools/service/state.py` | 狀態資料夾解析 | 儲存位置策略改變時 |
| `imgtools/core/*.py` | 實際影像、PDF、TIF、影片與檔名處理 | 演算法或輸出行為改變時 |
| `imgtools/ui/api.py` | HTTP payload 到 service 的薄 adapter | HTTP contract 改變時 |
| `imgtools/ui/server.py` | loopback HTTP server 與靜態檔案 | 路由或 server 行為改變時 |
| `imgtools/ui/static/` | registry-driven 表單與結果 UI | 視覺或互動改變時 |
| `tests/` | interface 與核心行為的回歸測試 | 每次行為變更時 |
| `examples/` | payload 與偏好格式範例 | contract 改變時同步更新 |

## 3. 對外入口

### 3.1 一鍵 UI 入口

從專案根目錄執行 `python main.py`，會呼叫 `imgtools.ui.server.serve("127.0.0.1", 5858, open_browser=True)`。若 5858 已遭占用，server 會直接回報錯誤，不會靜默改用其他埠。這個檔案只負責提供方便的啟動方式，不承載 UI 或工具邏輯。

### 3.2 CLI

唯一命令入口是 `python -m imgtools <command>`：

| Command | Interface |
|---|---|
| `list` | 輸出所有 `ToolSpec` 的 JSON 陣列 |
| `describe <action>` | 輸出指定 action metadata |
| `run <action>` | 以 `--param key=value` 或 `--params-json` 呼叫 runner |
| `ui` | 啟動本機 UI；預設固定使用 `127.0.0.1:5858`，可用 `--port` 明確改寫 |

### 3.3 Python

穩定的自動化入口：

```python
from imgtools.service.runner import run_tool

result = run_tool(
    "pdf.render_page",
    {"pdf_path": r"D:\input\sample.pdf", "page": 1, "dpi": 192},
)
```

`run_tool()` 接受 action 字串與 dict，永遠回傳 dict。呼叫者應先檢查 `result["ok"]`，不要依賴 core exception。

### 3.4 HTTP

本機 UI server 提供下列路由：

| Method | Route | 用途 |
|---|---|---|
| `GET` | `/api/tools` | 取得全部工具 metadata |
| `GET` | `/api/tools/<action>` | 取得單一工具 metadata |
| `GET` | `/api/preferences` | 取得 UI 偏好與常用工具 |
| `POST` | `/api/run` | `{action, params}` 執行工具 |
| `POST` | `/api/pick` | 開啟 Windows 本機檔案選擇器 |
| `POST` | `/api/preview` | 將 UI 輸入的本機圖片路徑轉成瀏覽器可顯示的縮圖資料 |
| `POST` | `/api/preferences` | 更新 `pinned_actions` 或 `pdf_default_dpi` |

這是沒有驗證機制的本機 interface，預設只應綁定 loopback，不應直接公開到網路。

## 4. Action interface

`ToolSpec` 是 registry 的單一事實來源：

- `action`：穩定且唯一的機器名稱，例如 `pdf.render_page`。
- `title`、`category`、`description`：UI 與工具發現資訊。
- `params`：`ToolParam` tuple，定義型別、必填、預設、選項與說明。
- `handler`：接受已整理參數 dict 的 core callable。
- `danger_level`：目前 rename 為高風險，runner 會套用安全預設。
- `featured`：沒有使用者偏好時的預設快速工具。

支援的參數型別為 `string`、`int`、`float`、`bool`、`path`、`folder`、`path_list`。路徑會移除 Windows 複製時包住整段路徑的雙引號；`path_list` 可透過 `min_items`、`max_items` 宣告數量限制，runner 與 UI 會共用這份 metadata。

Core handler 的 interface：

```python
def handler(params: dict[str, object]) -> dict[str, object]:
    ...
```

成功至少回傳 `{"ok": true, "outputs": {}, "warnings": []}`。可預期的失敗直接 raise 明確 exception；runner 會轉成：

```json
{
  "ok": false,
  "action": "...",
  "error_code": "ValueError",
  "message": "...",
  "outputs": {},
  "warnings": []
}
```

Runner 會補上 `action`，並在預設情況寫入 `manifest_path`。

## 5. 資料流與安全規則

1. Adapter 收到使用者輸入。
2. `runner` 從 registry 取得 `ToolSpec`。
3. 必填值、choices 與型別在 `_prepare_params()` 統一處理。
4. PDF 未指定 DPI 時讀取 server preference。
5. `safety` 對高風險 action 套用預設；rename 沒有 `confirm=true` 不會改檔。
6. Core handler 解析實體路徑、處理檔案並回傳結構化結果。
7. Runner 將成功或失敗寫入 manifest，敏感參數以 `[REDACTED]` 取代。

輸出路徑集中由 `imgtools/core/common.py` 管理。明確路徑預設不可覆寫；隱含路徑遇到衝突會建立 `-2`、`-3`。`output_naming=fixed` 使用 `output.*`；單一來源的 `output_naming=source` 使用來源檔名或來源資料夾名。由多張圖片合成單一圖片檔時，`default_sequence_output_stem()` 統一採用實際合成順序中最後一張圖片的檔名，資料夾型輸入則以排序後最後一張命名；輸出資料夾維持各 action 原本的位置。UI 的命名模式透過 preferences API 保存到私有狀態檔，不依賴瀏覽器 origin。

狀態根目錄預設是 `data/.imgtools/`：

```text
data/.imgtools/
  preferences.json
  manifests/*.manifest.json
```

測試或可攜式環境可設定 `IMGTOOLS_STATE_DIR` 隔離狀態。

## 6. 新增或修改工具

1. 先在 `tests/` 加入從預定 interface 觀察的 failing test。
2. 在對應 `imgtools/core/<category>.py` 實作 handler；避免 UI、CLI 或固定工作目錄知識。
3. 在 `imgtools/service/registry.py` 新增或更新 `ToolSpec`。
4. 若新增共通危險操作，先更新 `safety.py`，不可只在單一 UI 阻擋。
5. 確認 `python -m imgtools describe <action>` 的 metadata 足以讓 UI 自動建立表單。
6. 如 contract 改變，同步更新 `examples/`、README 與本文件。
7. 跑聚焦測試、全套測試、CLI list 與殘留引用掃描。

只有一個執行實作時，不要額外建立 pass-through adapter。需要替換外部依賴或測試替身時，seam 放在 core 內部，避免擴大對外 interface。

## 7. 測試地圖

| 變更 | 優先測試 |
|---|---|
| Registry / ToolSpec | `test_registry.py`、`test_schemas.py` |
| Runner / validation | `test_runner.py`、`test_safety.py` |
| HTTP / UI | `test_ui_api.py`、`test_ui_server.py` |
| Output naming | `test_output_defaults.py` |
| Preferences | `test_preferences.py` |
| 單一處理工具 | 對應的 `test_<category>.py` |
| 架構清潔度 | `test_architecture.py` |

完整驗證：

```powershell
python -m unittest discover -s tests
python -m compileall imgtools tests
python -m imgtools list
rg -n -i "legacy|pdf_dpi_conversion_tools|merge_img_to_one_pdf" imgtools examples README.md requirements.txt
```

最後一條只允許在 Git 歷史或備份分支出現；目前工作樹的程式、測試與文件不應再引用舊實作。
