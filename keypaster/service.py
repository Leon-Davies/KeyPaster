from __future__ import annotations

import queue
import threading
import time
from typing import Callable

from .models import KeyMapping
from .windows import ClipboardController, send_ctrl_v


StatusCallback = Callable[[str, str], None]


class PasteService:
    def __init__(
        self,
        status_callback: StatusCallback | None = None,
        restore_delay: float = 0.22,
    ) -> None:
        self._status_callback = status_callback or (lambda _level, _message: None)
        self._restore_delay = restore_delay
        self._queue: queue.Queue[KeyMapping | None] = queue.Queue(maxsize=20)
        self._thread = threading.Thread(target=self._run, name="KeyPasterPaste", daemon=True)
        self._clipboard = ClipboardController()
        self._thread.start()

    def submit(self, mapping: KeyMapping) -> None:
        try:
            self._queue.put_nowait(mapping)
        except queue.Full:
            self._status_callback("warning", "Paste queue is full; a key press was ignored.")

    def stop(self) -> None:
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while True:
            mapping = self._queue.get()
            if mapping is None:
                return
            self._paste(mapping)

    def _paste(self, mapping: KeyMapping) -> None:
        snapshot = None
        try:
            snapshot = self._clipboard.snapshot()
            self._clipboard.set_text(mapping.text)
            send_ctrl_v()
            time.sleep(self._restore_delay)
            self._clipboard.restore(snapshot)
            if snapshot.skipped_formats:
                self._status_callback(
                    "warning",
                    "Text pasted. Some uncommon clipboard formats could not be cloned; common text/image formats were preserved.",
                )
            else:
                self._status_callback("ok", f"Pasted “{mapping.name or mapping.key}”.")
        except Exception as exc:
            if snapshot is not None:
                try:
                    self._clipboard.restore(snapshot)
                except Exception as restore_exc:
                    self._status_callback(
                        "error",
                        f"Paste failed and clipboard restoration also failed: {restore_exc}",
                    )
                    return
            self._status_callback("error", f"Paste failed: {exc}")
