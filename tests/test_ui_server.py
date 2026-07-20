import json
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import patch


class UIServerTests(unittest.TestCase):
    def test_index_loads_separate_frontend_assets(self):
        from imgtools.ui.server import INDEX_HTML

        self.assertIn('/static/app.css', INDEX_HTML)
        self.assertIn('/static/app.js', INDEX_HTML)
        self.assertIn('id="tool-search"', INDEX_HTML)
        self.assertIn('id="category-filters"', INDEX_HTML)
        self.assertIn('id="quick-actions"', INDEX_HTML)
        self.assertIn('id="output-naming"', INDEX_HTML)
        self.assertIn('data-output-naming="fixed"', INDEX_HTML)
        self.assertIn('data-output-naming="source"', INDEX_HTML)

    def test_frontend_script_is_schema_driven_and_supports_path_lists(self):
        from imgtools.ui.server import STATIC_DIR

        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("selected.params.forEach", script)
        self.assertIn("param.type === 'path_list'", script)
        self.assertIn(r"value.join('\n')", script)
        self.assertIn(r"split(/\r?\n/)", script)
        self.assertIn("tool.featured", script)
        self.assertIn("param.advanced", script)
        self.assertIn("'/api/pick'", script)
        self.assertIn("video: '影片'", script)
        self.assertIn("localStorage", script)
        self.assertIn("output_naming: outputNaming", script)
        self.assertIn("param.source_default_hint", script)

    def test_http_server_returns_static_assets(self):
        from imgtools.ui.server import create_server

        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            conn = HTTPConnection(host, port, timeout=5)
            conn.request("GET", "/static/app.css")
            response = conn.getresponse()
            body = response.read().decode("utf-8")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(response.status, 200)
        self.assertIn("text/css", response.getheader("Content-Type"))
        self.assertIn("--ink", body)

    def test_http_server_returns_tools(self):
        from imgtools.ui.server import create_server

        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            conn = HTTPConnection(host, port, timeout=5)
            conn.request("GET", "/api/tools")
            response = conn.getresponse()
            body = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(response.status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("tools", body)

    def test_http_server_runs_action(self):
        from imgtools.ui.server import create_server

        fake_result = {"ok": True, "action": "x.y", "outputs": {}, "warnings": []}
        with patch("imgtools.ui.server.handle_run", return_value=fake_result):
            server = create_server("127.0.0.1", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                conn = HTTPConnection(host, port, timeout=5)
                payload = json.dumps({"action": "x.y", "params": {}}).encode("utf-8")
                conn.request("POST", "/api/run", body=payload, headers={"Content-Type": "application/json"})
                response = conn.getresponse()
                body = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(response.status, 200)
        self.assertEqual(body, fake_result)

    def test_http_server_opens_local_picker(self):
        from imgtools.ui.server import create_server

        fake_result = {"ok": True, "paths": ["D:/Images"]}
        with patch("imgtools.ui.server.handle_pick", return_value=fake_result):
            server = create_server("127.0.0.1", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                conn = HTTPConnection(host, port, timeout=5)
                payload = json.dumps({"mode": "folder"}).encode("utf-8")
                conn.request("POST", "/api/pick", body=payload, headers={"Content-Type": "application/json"})
                response = conn.getresponse()
                body = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(response.status, 200)
        self.assertEqual(body, fake_result)

    def test_handler_log_message_is_quiet_for_background_server(self):
        from imgtools.ui.server import ImgToolsHandler

        self.assertIsNone(ImgToolsHandler.log_message(None, "GET %s", "/"))


if __name__ == "__main__":
    unittest.main()
