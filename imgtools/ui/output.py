"""Open only artifacts from a known UI job; never accept arbitrary commands."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


OPENABLE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff', '.gif', '.pdf', '.mp4'}


def open_job_output(manager, payload):
    job = manager.get(str(payload.get('job_id', '')))
    outputs = (job.get('result') or {}).get('outputs', {})
    files = {Path(value).resolve() for value in outputs.get('files', [])}
    path = Path(str(payload.get('path', ''))).expanduser().resolve()
    mode = payload.get('mode', 'file')
    if mode not in {'file', 'folder'} or path not in files:
        raise ValueError('只能開啟這項任務已產生的輸出檔案')
    target = path.parent if mode == 'folder' else path
    if not target.exists():
        raise FileNotFoundError('輸出已移動或刪除')
    if mode == 'file' and (not target.is_file() or target.suffix.lower() not in OPENABLE_SUFFIXES):
        raise ValueError('此檔案格式不支援直接開啟，請開啟所在資料夾')
    if sys.platform == 'win32':
        os.startfile(str(target))
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(target)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {'ok': True}
