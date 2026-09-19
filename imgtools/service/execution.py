"""Optional execution feedback shared by CLI, UI jobs and core operations."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import Event, RLock
from typing import Callable


RUN_LOCK = RLock()


class ExecutionCancelled(Exception):
    error_code = 'CANCELLED'


@dataclass
class ExecutionContext:
    cancel: Event
    report: Callable[[dict], None] = lambda progress: None
    outputs: list[str] = field(default_factory=list)


_current: ContextVar[ExecutionContext | None] = ContextVar('imgtools_execution', default=None)


@contextmanager
def bind_execution(context: ExecutionContext):
    token = _current.set(context)
    try:
        yield context
    finally:
        _current.reset(token)


def checkpoint(message: str = '處理中', completed: int | None = None, total: int | None = None):
    context = _current.get()
    if context is None:
        return
    if context.cancel.is_set():
        raise ExecutionCancelled('已取消；已完成的輸出會保留。')
    context.report({'message': message, 'completed': completed, 'total': total})


def record_output(path):
    context = _current.get()
    if context is not None and str(path) not in context.outputs:
        context.outputs.append(str(path))


def partial_outputs() -> dict:
    context = _current.get()
    return {'files': list(context.outputs)} if context and context.outputs else {}
