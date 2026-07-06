from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from imgtools.ui.api import handle_get_tools, handle_run


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ImgToolsHandler)


def serve(host: str = "127.0.0.1", port: int = 8765, *, open_browser: bool = True) -> None:
    server = create_server(host, port)
    url = f"http://{host}:{server.server_address[1]}"
    print(f"ImgTools local UI: {url}")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nImgTools local UI stopped.")
    finally:
        server.server_close()


class ImgToolsHandler(BaseHTTPRequestHandler):
    server_version = "ImgToolsLocalUI/0.1"

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send_html(INDEX_HTML)
            return
        if self.path == "/api/tools":
            self._send_json(handle_get_tools())
            return
        self._send_json({"ok": False, "message": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self._send_json({"ok": False, "message": "Not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._send_json(handle_run(payload))
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "error_code": exc.__class__.__name__,
                    "message": str(exc),
                    "outputs": {},
                    "warnings": [],
                },
                status=500,
            )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


INDEX_HTML = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ImgTools Local UI</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --line: #d8dee8;
      --accent: #1264a3;
      --accent-dark: #0b4f82;
      --danger: #a33a2a;
      --ok: #237a57;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft JhengHei", "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    header h1 { margin: 0; font-size: 18px; }
    header span { color: var(--muted); font-size: 13px; }
    main {
      display: grid;
      grid-template-columns: 300px minmax(360px, 1fr) minmax(360px, 520px);
      gap: 16px;
      padding: 16px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .title {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      font-weight: 700;
    }
    .tools { max-height: calc(100vh - 110px); overflow: auto; }
    .tool {
      display: block;
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      padding: 12px 14px;
      text-align: left;
      cursor: pointer;
    }
    .tool:hover, .tool.active { background: #eef5fb; }
    .tool strong { display: block; font-size: 14px; }
    .tool small { color: var(--muted); display: block; margin-top: 4px; }
    form, .result { padding: 14px; }
    .meta { color: var(--muted); font-size: 13px; line-height: 1.5; }
    label { display: block; font-size: 13px; font-weight: 700; margin: 14px 0 6px; }
    input, select, textarea {
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
    }
    textarea { min-height: 112px; resize: vertical; }
    input[type="checkbox"] { width: auto; min-height: auto; }
    .hint { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .actions { display: flex; gap: 10px; margin-top: 18px; }
    button.primary, button.secondary {
      border-radius: 6px;
      padding: 9px 14px;
      cursor: pointer;
      font-weight: 700;
    }
    button.primary { border: 0; background: var(--accent); color: #fff; }
    button.primary:hover { background: var(--accent-dark); }
    button.secondary { border: 1px solid var(--line); background: #fff; color: var(--text); }
    pre {
      margin: 0;
      padding: 12px;
      background: #111827;
      color: #e5edf6;
      border-radius: 6px;
      max-height: calc(100vh - 170px);
      overflow: auto;
      font-size: 12px;
      line-height: 1.45;
    }
    .status { font-weight: 700; margin-bottom: 10px; }
    .status.ok { color: var(--ok); }
    .status.fail { color: var(--danger); }
    @media (max-width: 1080px) {
      main { grid-template-columns: 1fr; }
      .tools { max-height: none; }
    }
  </style>
</head>
<body>
  <header>
    <h1>ImgTools Local UI</h1>
    <span>localhost</span>
  </header>
  <main>
    <section>
      <div class="title">工具</div>
      <div id="tools" class="tools"></div>
    </section>
    <section>
      <div class="title">參數</div>
      <form id="form"></form>
    </section>
    <section>
      <div class="title">結果</div>
      <div class="result">
        <div id="status" class="status">尚未執行</div>
        <pre id="result">{}</pre>
      </div>
    </section>
  </main>
  <script>
    let tools = [];
    let selected = null;

    async function boot() {
      const data = await (await fetch('/api/tools')).json();
      tools = data.tools || [];
      selected = tools[0] || null;
      renderTools();
      renderForm();
    }

    function renderTools() {
      const el = document.getElementById('tools');
      el.innerHTML = '';
      tools.forEach(tool => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'tool' + (selected && selected.action === tool.action ? ' active' : '');
        button.onclick = () => { selected = tool; renderTools(); renderForm(); };
        button.innerHTML = `<strong>${escapeHtml(tool.title)}</strong><small>${escapeHtml(tool.action)}</small>`;
        el.appendChild(button);
      });
    }

    function renderForm() {
      const form = document.getElementById('form');
      if (!selected) {
        form.innerHTML = '';
        return;
      }
      form.innerHTML = `<div class="meta">${escapeHtml(selected.description)}</div>`;
      selected.params.forEach(param => {
        const block = document.createElement('div');
        const id = `param_${param.name}`;
        const required = param.required ? ' *' : '';
        const value = param.default === undefined ? '' : param.default;
        if (param.type === 'bool') {
          block.innerHTML = `<label><input id="${id}" type="checkbox" ${value ? 'checked' : ''}> ${escapeHtml(param.name)}${required}</label><div class="hint">${escapeHtml(param.description || '')}</div>`;
        } else if (param.type === 'path_list') {
          const pathValue = Array.isArray(value) ? value.join('\\n') : value;
          block.innerHTML = `<label for="${id}">${escapeHtml(param.name)}${required}</label><textarea id="${id}" placeholder="每行一個圖片路徑">${escapeHtml(String(pathValue))}</textarea><div class="hint">${escapeHtml(param.description || '')}</div>`;
        } else if (param.choices && param.choices.length) {
          block.innerHTML = `<label for="${id}">${escapeHtml(param.name)}${required}</label><select id="${id}">${param.choices.map(choice => `<option value="${escapeHtml(choice)}" ${choice === value ? 'selected' : ''}>${escapeHtml(choice)}</option>`).join('')}</select><div class="hint">${escapeHtml(param.description || '')}</div>`;
        } else {
          block.innerHTML = `<label for="${id}">${escapeHtml(param.name)}${required}</label><input id="${id}" value="${escapeHtml(String(value))}" placeholder="${escapeHtml(param.type)}"><div class="hint">${escapeHtml(param.description || '')}</div>`;
        }
        form.appendChild(block);
      });
      const actions = document.createElement('div');
      actions.className = 'actions';
      actions.innerHTML = '<button class="primary" type="submit">執行</button><button class="secondary" type="button" id="copy">複製 JSON</button>';
      form.appendChild(actions);
      form.onsubmit = runTool;
      document.getElementById('copy').onclick = copyTask;
    }

    function params() {
      const out = {};
      selected.params.forEach(param => {
        const el = document.getElementById(`param_${param.name}`);
        if (!el) return;
        if (param.type === 'bool') out[param.name] = el.checked;
        else if (param.type === 'path_list') out[param.name] = el.value.split(/\\r?\\n/).map(value => value.trim()).filter(Boolean);
        else if (el.value !== '') out[param.name] = el.value;
      });
      return out;
    }

    async function runTool(event) {
      event.preventDefault();
      setStatus('執行中...', null);
      const payload = { action: selected.action, params: params() };
      const data = await (await fetch('/api/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) })).json();
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      setStatus(data.ok ? '完成' : '失敗', data.ok);
    }

    async function copyTask() {
      const task = { action: selected.action, params: params() };
      const text = JSON.stringify(task, null, 2);
      await navigator.clipboard.writeText(text);
      document.getElementById('result').textContent = text;
      setStatus('已複製 JSON task', true);
    }

    function setStatus(text, ok) {
      const el = document.getElementById('status');
      el.textContent = text;
      el.className = 'status' + (ok === true ? ' ok' : ok === false ? ' fail' : '');
    }

    function escapeHtml(value) {
      return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
    }

    boot();
  </script>
</body>
</html>
"""
