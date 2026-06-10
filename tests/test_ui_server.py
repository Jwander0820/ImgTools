import json
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import patch


class UIServerTests(unittest.TestCase):
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

    def test_handler_log_message_is_quiet_for_background_server(self):
        from imgtools.ui.server import ImgToolsHandler

        self.assertIsNone(ImgToolsHandler.log_message(None, "GET %s", "/"))


if __name__ == "__main__":
    unittest.main()
