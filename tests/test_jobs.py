import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch


class JobTests(unittest.TestCase):
    def wait_terminal(self, manager, job_id):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job = manager.get(job_id)
            if job['status'] in {'completed', 'failed', 'cancelled'}:
                return job
            time.sleep(.01)
        self.fail('job did not finish')

    def test_queue_serializes_runs_and_deduplicates_retry(self):
        from imgtools.service.jobs import JobManager
        entered = threading.Event()
        release = threading.Event()
        calls = []

        def execute(payload):
            calls.append(payload['action'])
            entered.set()
            release.wait(3)
            return {'ok': True, 'action': payload['action'], 'outputs': {}, 'warnings': []}

        with JobManager(execute) as manager:
            first = manager.submit('pdf.render_page', {}, request_id='request-1')
            self.assertTrue(entered.wait(2))
            again = manager.submit('pdf.render_page', {}, request_id='request-1')
            second = manager.submit('tif.extract_page', {}, request_id='request-2')
            self.assertEqual(first['id'], again['id'])
            self.assertEqual(second['status'], 'queued')
            self.assertEqual(calls, ['pdf.render_page'])
            release.set()
            self.assertEqual(self.wait_terminal(manager, second['id'])['status'], 'completed')
            self.assertEqual(calls, ['pdf.render_page', 'tif.extract_page'])

    def test_cancel_queued_job_never_executes_it(self):
        from imgtools.service.jobs import JobManager
        entered = threading.Event()
        release = threading.Event()
        calls = []

        def execute(payload):
            calls.append(payload['action'])
            entered.set()
            release.wait(3)
            return {'ok': True, 'outputs': {}, 'warnings': []}

        with JobManager(execute) as manager:
            manager.submit('pdf.render_page', {})
            self.assertTrue(entered.wait(2))
            second = manager.submit('tif.extract_page', {})
            self.assertEqual(manager.cancel(second['id'])['status'], 'cancelled')
            release.set()
        self.assertEqual(calls, ['pdf.render_page'])

    def test_running_cancel_reports_progress_and_preserves_outputs(self):
        from imgtools.service.execution import checkpoint, record_output
        from imgtools.service.jobs import JobManager
        entered = threading.Event()
        release = threading.Event()

        def execute(payload):
            checkpoint('處理第 1 頁', 0, 2)
            record_output('completed-page.png')
            entered.set()
            release.wait(3)
            checkpoint('處理第 2 頁', 1, 2)
            self.fail('cancelled work continued')

        with JobManager(execute) as manager:
            job = manager.submit('pdf.render_all_pages', {})
            self.assertTrue(entered.wait(2))
            current = manager.get(job['id'])
            self.assertEqual(current['progress']['total'], 2)
            self.assertEqual(manager.cancel(job['id'])['status'], 'cancelling')
            release.set()
            cancelled = self.wait_terminal(manager, job['id'])
            self.assertEqual(cancelled['status'], 'cancelled')
            self.assertEqual(cancelled['result']['outputs']['files'], ['completed-page.png'])

    def test_failure_does_not_stop_queue_and_unknown_job_is_not_success(self):
        from imgtools.service.jobs import JobManager
        def execute(payload):
            if payload['action'] == 'pdf.render_page':
                raise RuntimeError('test error')
            return {'ok': True, 'outputs': {}, 'warnings': []}
        with JobManager(execute) as manager:
            first = manager.submit('pdf.render_page', {})
            second = manager.submit('tif.extract_page', {})
            self.assertEqual(self.wait_terminal(manager, first['id'])['status'], 'failed')
            self.assertEqual(self.wait_terminal(manager, second['id'])['status'], 'completed')
            with self.assertRaises(KeyError):
                manager.get('unknown')

    def test_request_id_cannot_be_reused_with_different_input(self):
        from imgtools.service.jobs import JobManager
        with JobManager(lambda p: {'ok': True}) as manager:
            manager.submit('pdf.render_page', {'page': 1}, request_id='same')
            with self.assertRaises(ValueError):
                manager.submit('pdf.render_page', {'page': 2}, request_id='same')

    def test_runner_cancellation_has_partial_outputs_and_manifest(self):
        from imgtools.service.execution import ExecutionContext, bind_execution, checkpoint, record_output
        from imgtools.service.runner import run_tool
        event = threading.Event()
        def handler(params):
            record_output('done.png')
            event.set()
            checkpoint('next')
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'IMGTOOLS_STATE_DIR': folder}):
            with patch('imgtools.service.runner.get_tool') as get_tool:
                get_tool.return_value.params = ()
                get_tool.return_value.danger_level = 'low'
                get_tool.return_value.handler = handler
                with bind_execution(ExecutionContext(event)):
                    result = run_tool('test.cancel', {})
            self.assertEqual(result['error_code'], 'CANCELLED')
            self.assertEqual(result['outputs']['files'], ['done.png'])
            self.assertTrue(Path(result['manifest_path']).is_file())

    def test_old_server_session_cannot_resubmit_uncertain_work(self):
        from imgtools.service.jobs import JobManager
        with JobManager(lambda p: {'ok': True}) as manager:
            with self.assertRaises(ValueError):
                manager.submit('pdf.render_page', {}, session_id='previous-server')
            self.assertEqual(manager.list(), [])

    def test_expired_result_retry_never_runs_again(self):
        from imgtools.service.jobs import JobManager
        calls = []
        def execute(payload):
            calls.append(payload['action'])
            return {'ok': True}
        with JobManager(execute, history_limit=1) as manager:
            first = manager.submit('pdf.render_page', {}, request_id='old')
            self.wait_terminal(manager, first['id'])
            second = manager.submit('pdf.render_page', {}, request_id='new')
            self.wait_terminal(manager, second['id'])
            self.assertEqual(len(manager.list()), 1)
            with self.assertRaisesRegex(ValueError, '紀錄已過期'):
                manager.submit('pdf.render_page', {}, request_id='old')
            self.assertEqual(len(calls), 2)

    def test_queue_limit_and_summary_do_not_expose_params_or_full_results(self):
        from imgtools.service.jobs import JobManager
        entered, release = threading.Event(), threading.Event()
        def execute(payload):
            entered.set(); release.wait(3)
            return {'ok': True, 'outputs': {'files':['done.png']}}
        with JobManager(execute, queue_limit=1) as manager:
            job = manager.submit('pdf.render_page', {'password':'private'})
            self.assertTrue(entered.wait(2))
            with self.assertRaises(ValueError):
                manager.submit('pdf.render_page', {})
            release.set()
            self.wait_terminal(manager, job['id'])
            summary = manager.list()[0]
            self.assertNotIn('result', summary)
            self.assertNotIn('payload', summary)
            self.assertNotIn('private', str(summary))
            self.assertTrue(summary['has_result'])

    def test_pdf_cancel_preserves_first_page_only(self):
        import fitz
        from imgtools.service.execution import ExecutionContext, bind_execution
        from imgtools.service.runner import run_tool
        event = threading.Event()
        def report(progress):
            if progress['completed'] == 1:
                event.set()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with fitz.open() as doc:
                doc.new_page(width=20,height=20)
                doc.new_page(width=20,height=20)
                doc.save(root / 'source.pdf')
            with bind_execution(ExecutionContext(event, report)):
                result = run_tool('pdf.render_all_pages', {'pdf_path':str(root / 'source.pdf')}, manifest=False)
            self.assertEqual(result['error_code'], 'CANCELLED')
            self.assertEqual(len(result['outputs']['files']), 1)
            self.assertTrue(Path(result['outputs']['files'][0]).is_file())
            self.assertEqual(len(list(root.rglob('*.png'))), 1)

    def test_video_cancel_does_not_publish_partial_or_replace_existing_output(self):
        from imgtools.service.execution import ExecutionContext, bind_execution
        from imgtools.service.runner import run_tool
        event = threading.Event()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'source.mp4').write_bytes(b'source')
            (root / 'existing.gif').write_bytes(b'existing-output')
            def convert(arguments):
                Path(arguments[-1]).write_bytes(b'incomplete')
                event.set()
            with patch('imgtools.core.video._run_ffmpeg', side_effect=convert), bind_execution(ExecutionContext(event)):
                result = run_tool('gif.mp4_to_gif', {'input_path':str(root / 'source.mp4'), 'output_path':str(root / 'existing.gif'), 'overwrite':True}, manifest=False)
            self.assertEqual(result['error_code'], 'CANCELLED')
            self.assertEqual((root / 'existing.gif').read_bytes(), b'existing-output')
            self.assertFalse(list(root.glob('.imgtools-video-*')))

    def test_video_cancel_terminates_the_child_process(self):
        import subprocess
        import sys
        from imgtools.core.video import _run_ffmpeg
        from imgtools.service.execution import ExecutionCancelled, ExecutionContext, bind_execution
        event = threading.Event()
        processes = []
        original_popen = subprocess.Popen
        def start_child(arguments, **kwargs):
            process = original_popen([sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)
            processes.append(process)
            return process
        def report(progress):
            if progress['message'].startswith('影片轉換中'):
                event.set()
        started = time.monotonic()
        with patch('imgtools.core.video._ffmpeg_executable', return_value='test-child'), \
                patch('imgtools.core.video.subprocess.Popen', side_effect=start_child), \
                bind_execution(ExecutionContext(event, report)):
            with self.assertRaises(ExecutionCancelled):
                _run_ffmpeg([])
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())
        self.assertLess(time.monotonic() - started, 5)

    def test_video_publish_does_not_overwrite_a_file_created_during_conversion(self):
        from imgtools.service.runner import run_tool
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'source.mp4').write_bytes(b'source')
            target = root / 'result.gif'
            def convert(arguments):
                Path(arguments[-1]).write_bytes(b'converted')
                target.write_bytes(b'created-by-another-process')
            with patch('imgtools.core.video._run_ffmpeg', side_effect=convert):
                result = run_tool('gif.mp4_to_gif', {'input_path':str(root / 'source.mp4'), 'output_path':str(target)}, manifest=False)
            self.assertFalse(result['ok'])
            self.assertEqual(target.read_bytes(), b'created-by-another-process')


if __name__ == '__main__':
    unittest.main()
