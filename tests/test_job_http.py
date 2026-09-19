import json
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch


class JobHTTPTests(unittest.TestCase):
    def setUp(self):
        from imgtools.ui.server import create_server
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict('os.environ', {'IMGTOOLS_STATE_DIR': self.temp.name})
        self.env.start()
        self.server = create_server('127.0.0.1', 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.env.stop()
        self.temp.cleanup()

    def request(self, route, payload=None, headers=None):
        conn = HTTPConnection(*self.server.server_address, timeout=3)
        conn.request('POST' if payload is not None else 'GET', route,
                     body=json.dumps(payload) if payload is not None else None,
                     headers=headers or {'Content-Type': 'application/json'})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, data

    def test_real_rename_preview_job_reports_operations_without_renaming(self):
        target = Path(self.temp.name) / 'before.txt'
        target.write_text('unchanged')
        code, body = self.request('/api/jobs', {'action':'rename.files_replace', 'params':{
            'target_folder':self.temp.name, 'target':'before', 'replacement':'after'}, 'request_id':'http-test'})
        self.assertEqual(code, 200)
        job_id = json.loads(body)['job']['id']
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            _, body = self.request('/api/jobs/' + job_id)
            job = json.loads(body)['job']
            if job['status'] in {'completed','failed'}:
                break
            time.sleep(.01)
        self.assertEqual(job['status'], 'completed')
        self.assertTrue(job['result']['outputs']['dry_run'])
        self.assertEqual(job['result']['outputs']['count'], 1)
        self.assertTrue(target.exists())
        _, repeat = self.request('/api/jobs', {'action':'rename.files_replace', 'params':{
            'target_folder':self.temp.name, 'target':'before', 'replacement':'after'}, 'request_id':'http-test'})
        self.assertEqual(json.loads(repeat)['job']['id'], job_id)

    def test_output_open_requires_registered_artifact_and_correct_job(self):
        from imgtools.ui.output import open_job_output
        file = Path(self.temp.name) / 'generated.png'
        file.write_bytes(b'fixture')
        self.server.jobs.execute = lambda payload: {'ok':True, 'outputs':{'files':[str(file)]}}
        job = self.server.jobs.submit('pdf.render_page', {})
        deadline = time.monotonic() + 2
        while self.server.jobs.get(job['id'])['status'] != 'completed' and time.monotonic() < deadline:
            time.sleep(.01)
        with patch('imgtools.ui.output.os.startfile', create=True) as open_file, patch('imgtools.ui.output.sys.platform','win32'):
            open_job_output(self.server.jobs, {'job_id':job['id'],'path':str(file),'mode':'folder'})
            open_file.assert_called_once_with(str(file.parent))
            with self.assertRaises(ValueError):
                open_job_output(self.server.jobs, {'job_id':job['id'],'path':str(file.parent / 'arbitrary.exe')})
            self.assertEqual(open_file.call_count, 1)

    def test_foreign_origin_and_non_object_payload_are_rejected(self):
        status, _ = self.request('/api/jobs', {'action':'pdf.render_page'}, {'Origin':'https://example.org'})
        self.assertEqual(status, 403)
        status, body = self.request('/api/jobs', [])
        self.assertFalse(json.loads(body)['ok'])

    def test_es_modules_have_javascript_content_type_and_missing_job_is_404(self):
        for path in ('/static/state.mjs','/static/task-store.mjs','/static/results.mjs'):
            conn = HTTPConnection(*self.server.server_address, timeout=3)
            conn.request('GET', path)
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn('javascript', response.getheader('Content-Type'))
            response.read(); conn.close()
        self.assertEqual(self.request('/api/jobs/missing')[0], 404)

    def test_occupied_port_preserves_bind_error_for_launcher_fallback(self):
        import socket
        from imgtools.ui.server import create_server
        with socket.socket() as occupied:
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                occupied.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            with self.assertRaises(OSError):
                with create_server(*occupied.getsockname()):
                    pass
