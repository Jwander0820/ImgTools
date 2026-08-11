from __future__ import annotations

import errno
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from imgtools.ui.api import (
    handle_get_preferences,
    handle_get_tool,
    handle_get_tools,
    handle_pick,
    handle_preview,
    handle_run,
    handle_update_preferences,
)


STATIC_DIR = Path(__file__).with_name("static")
INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
STATIC_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ImgToolsHandler)


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    open_browser: bool = True,
    fallback_port: bool = False,
) -> None:
    try:
        server = create_server(host, port)
    except OSError as exc:
        if not fallback_port or port == 0 or not _is_unavailable_port_error(exc):
            raise
        server = create_server(host, 0)
        print(
            f"ImgTools could not use port {port}; "
            f"using available port {server.server_address[1]} instead."
        )
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


def _is_unavailable_port_error(exc: OSError) -> bool:
    return (
        isinstance(exc, PermissionError)
        or getattr(exc, "winerror", None) in {10013, 10048}
        or getattr(exc, "errno", None) in {errno.EACCES, errno.EADDRINUSE}
    )


class ImgToolsHandler(BaseHTTPRequestHandler):
    server_version = "ImgToolsLocalUI/0.2"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(INDEX_HTML)
            return
        if path == "/api/tools":
            self._send_json(handle_get_tools())
            return
        if path.startswith("/api/tools/"):
            action = path.removeprefix("/api/tools/")
            result = handle_get_tool(action)
            self._send_json(result, status=200 if result["ok"] else 404)
            return
        if path == "/api/preferences":
            self._send_json(handle_get_preferences())
            return
        if path.startswith("/static/"):
            self._send_static(path.removeprefix("/static/"))
            return
        self._send_json({"ok": False, "message": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/api/run", "/api/pick", "/api/preview", "/api/preferences"}:
            self._send_json({"ok": False, "message": "Not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if path == "/api/run":
                result = handle_run(payload)
            elif path == "/api/preview":
                result = handle_preview(payload)
            elif path == "/api/preferences":
                result = handle_update_preferences(payload)
            else:
                result = handle_pick(payload)
            self._send_json(result)
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

    def _send_static(self, filename: str) -> None:
        requested = (STATIC_DIR / filename).resolve()
        if STATIC_DIR.resolve() not in requested.parents or not requested.is_file():
            self._send_json({"ok": False, "message": "Not found"}, status=404)
            return
        self._send_bytes(
            requested.read_bytes(),
            STATIC_CONTENT_TYPES.get(requested.suffix, "application/octet-stream"),
        )

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _send_html(self, html: str) -> None:
        self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8")

    def _send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
