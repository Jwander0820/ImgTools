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
        self.assertIn('id="quick-settings"', INDEX_HTML)
        self.assertIn('id="quick-action-editor"', INDEX_HTML)
        self.assertIn('id="output-naming"', INDEX_HTML)
        self.assertIn('data-output-naming="fixed"', INDEX_HTML)
        self.assertIn('data-output-naming="source"', INDEX_HTML)

    def test_frontend_exposes_server_pdf_default_dpi(self):
        from imgtools.ui.server import INDEX_HTML, STATIC_DIR

        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="pdf-default-dpi"', INDEX_HTML)
        workbench = INDEX_HTML.index('id="workbench"')
        dpi_setting = INDEX_HTML.index('id="pdf-default-setting"')
        self.assertGreater(dpi_setting, workbench)
        self.assertIn("savePdfDefaultDpi", script)
        self.assertIn("pdf_default_dpi", script)
        self.assertIn("selected.category !== 'pdf'", script)

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
        self.assertIn("'/api/preferences'", script)
        self.assertIn("preference.source", script)
        self.assertIn("pinned_actions", script)
        self.assertIn("ordered-path-list", script)
        self.assertIn("movePathItem", script)
        self.assertIn("removePathItem", script)
        self.assertIn(".forEach((param) => renderPathOrder", script)

    def test_frontend_contains_dialogue_stack_interactive_preview(self):
        from imgtools.ui.server import STATIC_DIR

        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        styles = (STATIC_DIR / "app.css").read_text(encoding="utf-8")

        self.assertIn("function renderDialoguePreview", script)
        self.assertIn("function initDialoguePreview", script)
        self.assertIn("pickerPayload.include_previews = true", script)
        self.assertIn("pointermove", script)
        self.assertIn("dialogue-preview-canvas", styles)

    def test_frontend_contains_watermark_positioning_editor(self):
        from imgtools.ui.server import STATIC_DIR

        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        styles = (STATIC_DIR / "app.css").read_text(encoding="utf-8")

        self.assertIn("function renderWatermarkEditor", script)
        self.assertIn("function initWatermarkEditor", script)
        self.assertIn("function drawWatermarkPreview", script)
        self.assertIn('id="param_text" type="text" required', script)
        self.assertIn("請輸入浮水印文字。", script)
        self.assertIn("watermark.batch_text", script)
        self.assertIn("data-watermark-color", script)
        self.assertIn("param_repeat_spacing", script)
        self.assertIn("data-watermark-position", script)
        self.assertIn("watermark-preview-canvas", styles)
        self.assertIn("watermark-position-button", styles)
        self.assertIn("watermark-direct-input", styles)
        self.assertIn("watermark-swatch", styles)

    def test_frontend_normalizes_all_local_path_param_types(self):
        from imgtools.ui.server import STATIC_DIR

        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("function normalizeLocalPath(value)", script)
        self.assertIn(".map(normalizeLocalPath)", script)
        self.assertIn("['path', 'folder'].includes(param.type)", script)

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

    def test_http_server_returns_tool_details(self):
        from imgtools.ui.server import create_server

        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            conn = HTTPConnection(host, port, timeout=5)
            conn.request("GET", "/api/tools/pdf.render_page")
            response = conn.getresponse()
            body = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(response.status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["tool"]["action"], "pdf.render_page")

    def test_http_server_reads_and_updates_preferences(self):
        from imgtools.ui.server import create_server

        get_result = {"ok": True, "pinned_actions": [], "quick_actions": []}
        update_result = {"ok": True, "pinned_actions": ["gif.images_to_gif"], "quick_actions": []}
        with patch("imgtools.ui.server.handle_get_preferences", return_value=get_result), patch(
            "imgtools.ui.server.handle_update_preferences", return_value=update_result
        ):
            server = create_server("127.0.0.1", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                conn = HTTPConnection(host, port, timeout=5)
                conn.request("GET", "/api/preferences")
                get_response = conn.getresponse()
                get_body = json.loads(get_response.read().decode("utf-8"))

                payload = json.dumps({"pinned_actions": ["gif.images_to_gif"]}).encode("utf-8")
                conn.request(
                    "POST",
                    "/api/preferences",
                    body=payload,
                    headers={"Content-Type": "application/json"},
                )
                post_response = conn.getresponse()
                post_body = json.loads(post_response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(get_response.status, 200)
        self.assertEqual(get_body, get_result)
        self.assertEqual(post_response.status, 200)
        self.assertEqual(post_body, update_result)

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
