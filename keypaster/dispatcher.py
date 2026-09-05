from __future__ import annotations

import logging
import queue
from collections.abc import Callable
from typing import Any


class UiDispatcher:
    """Thread-safe bridge into Tk's main thread.

    Background worker and tray threads only enqueue Python callables. The Tk
    thread drains the queue from its normal event loop, so no Tcl/Tk API is
    called directly from a background thread.
    """

    def __init__(self, root: Any, interval_ms: int = 40) -> None:
        self._root = root
        self._interval_ms = interval_ms
        self._queue: queue.SimpleQueue[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = (
            queue.SimpleQueue()
        )
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._root.after(self._interval_ms, self._drain)

    def post(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        if not self._running:
            return
        self._queue.put((callback, args, kwargs))

    def stop(self) -> None:
        self._running = False
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _drain(self) -> None:
        if not self._running:
            return
        while True:
            try:
                callback, args, kwargs = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args, **kwargs)
            except Exception:
                logging.exception("UI dispatcher callback failed")
        if self._running:
            self._root.after(self._interval_ms, self._drain)
