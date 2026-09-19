"""A bounded, single-worker queue for the local UI. All work uses the runner."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from threading import Condition, Event, Thread
from time import time
from uuid import uuid4

from .execution import ExecutionCancelled, ExecutionContext, bind_execution
from .registry import get_tool


TERMINAL = {'completed', 'failed', 'cancelled'}


class JobManager:
    def __init__(self, execute, *, history_limit=50, queue_limit=16):
        self.execute = execute
        self.session_id = uuid4().hex
        self.history_limit = history_limit
        self.queue_limit = queue_limit
        self._jobs = {}
        # Retain small request receipts for this server session even after the
        # full result is pruned, so an old retry cannot execute twice.
        self._requests = {}
        self._condition = Condition()
        self._closed = False
        self._worker = Thread(target=self._work, name='imgtools-jobs', daemon=True)
        self._worker.start()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def submit(self, action, params, *, request_id=None, session_id=None):
        if session_id is not None and session_id != self.session_id:
            raise ValueError('服務已重新啟動，無法確認先前任務；請先檢查輸出再重新送出')
        spec = get_tool(action)
        if not isinstance(params, dict):
            raise ValueError('params 必須是物件')
        if request_id is not None and (not isinstance(request_id, str) or not 1 <= len(request_id) <= 128):
            raise ValueError('request_id 必須是 1～128 字元的字串')
        payload = {'action': action, 'params': deepcopy(params)}
        fingerprint = sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self._condition:
            if self._closed:
                raise ValueError('任務服務已停止')
            if request_id in self._requests:
                previous_fingerprint, job_id = self._requests[request_id]
                if previous_fingerprint != fingerprint:
                    raise ValueError('request_id 已用於不同的任務')
                if job_id not in self._jobs:
                    raise ValueError('這筆任務已受理，但結果紀錄已過期；請先檢查輸出')
                return self._view(self._jobs[job_id])
            if sum(j['status'] not in TERMINAL for j in self._jobs.values()) >= self.queue_limit:
                raise ValueError('佇列已滿，請等待目前任務完成')
            job = {
                'id': uuid4().hex, 'action': action, 'title': spec.title,
                'status': 'queued', 'created_at': time(), 'started_at': None,
                'finished_at': None, 'progress': {'message': '等待前面的任務完成', 'completed': None, 'total': None},
                'result': None, 'request_id': request_id, 'fingerprint': fingerprint, 'payload': payload, 'cancel': Event(),
            }
            self._jobs[job['id']] = job
            if request_id:
                self._requests[request_id] = (fingerprint, job['id'])
            view = self._view(job)
            self._condition.notify_all()
            return view

    def get(self, job_id):
        with self._condition:
            return self._view(self._jobs[job_id])

    def list(self):
        with self._condition:
            return [self._view(job, include_result=False) for job in reversed(self._jobs.values())]

    def cancel(self, job_id):
        with self._condition:
            job = self._jobs[job_id]
            if job['status'] in TERMINAL:
                return self._view(job)
            if job['status'] != 'queued' and job['action'].startswith('rename.'):
                raise ValueError('改名開始後須等待完成，避免只套用部分變更')
            job['cancel'].set()
            if job['status'] == 'queued':
                job.update(status='cancelled', finished_at=time(), result=self._cancelled(job, {}))
                job['payload']['params'] = {}
                self._prune_history()
            else:
                job['status'] = 'cancelling'
                job['progress']['message'] = '正在取消，等待目前處理步驟結束'
            self._condition.notify_all()
            return self._view(job)

    def _prune_history(self):
        terminal = sorted((job for job in self._jobs.values() if job['status'] in TERMINAL),
                          key=lambda job: job['finished_at'])
        for job in terminal[:max(0, len(terminal) - self.history_limit)]:
            del self._jobs[job['id']]

    def _view(self, job, *, include_result=True):
        excluded = {'payload', 'cancel', 'request_id', 'fingerprint'}
        if not include_result:
            excluded.add('result')
        view = {key: deepcopy(value) for key, value in job.items() if key not in excluded}
        view['has_result'] = job['result'] is not None
        view['elapsed_seconds'] = round((job['finished_at'] or time()) - (job['started_at'] or job['created_at']), 1)
        queued = [j['id'] for j in self._jobs.values() if j['status'] == 'queued']
        view['queue_position'] = queued.index(job['id']) + 1 if job['id'] in queued else 0
        view['can_cancel'] = job['status'] == 'queued' or (job['status'] == 'running' and not job['action'].startswith('rename.'))
        return view

    def _progress(self, job, progress):
        with self._condition:
            if job['status'] == 'running':
                job['progress'] = progress

    def _cancelled(self, job, outputs):
        return {'ok': False, 'action': job['action'], 'error_code': 'CANCELLED',
                'message': '已取消；已完成的輸出會保留。', 'outputs': outputs, 'warnings': []}

    def _work(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._closed or any(j['status'] == 'queued' for j in self._jobs.values()))
                if self._closed:
                    return
                job = next(j for j in self._jobs.values() if j['status'] == 'queued')
                job.update(status='running', started_at=time())
                job['progress']['message'] = '準備處理'
            context = ExecutionContext(job['cancel'], lambda progress: self._progress(job, progress))
            try:
                with bind_execution(context):
                    result = self.execute(job['payload'])
            except ExecutionCancelled:
                result = self._cancelled(job, {'files': context.outputs})
            except Exception as exc:
                result = {'ok': False, 'action': job['action'], 'error_code': type(exc).__name__,
                          'message': str(exc), 'outputs': {'files': context.outputs}, 'warnings': []}
            with self._condition:
                job['result'] = result
                job['status'] = 'cancelled' if result.get('error_code') == 'CANCELLED' else 'completed' if result.get('ok') else 'failed'
                job['finished_at'] = time()
                job['payload']['params'] = {}  # Do not retain passwords after execution.
                self._prune_history()
                self._condition.notify_all()

    def close(self):
        with self._condition:
            for job in self._jobs.values():
                if job['status'] == 'queued':
                    job.update(status='cancelled', finished_at=time(), result=self._cancelled(job, {}))
                    job['payload']['params'] = {}
                if job['status'] not in TERMINAL and not job['action'].startswith('rename.'):
                    job['cancel'].set()
            self._closed = True
            self._condition.notify_all()
        self._worker.join(timeout=5)
