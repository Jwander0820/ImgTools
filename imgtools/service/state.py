from __future__ import annotations

import os
from pathlib import Path


def state_root() -> Path:
    configured = os.environ.get("IMGTOOLS_STATE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / ".imgtools"
