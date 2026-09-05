import time

import keypaster.service as service_module
from keypaster.models import KeyMapping
from keypaster.service import PasteService


class DummyClipboard:
    pass


def test_worker_survives_unexpected_execute_failure(monkeypatch) -> None:
    monkeypatch.setattr(service_module, "ClipboardController", lambda: DummyClipboard())
    statuses: list[tuple[str, str]] = []
    service = PasteService(status_callback=lambda level, message: statuses.append((level, message)))
    calls = {"count": 0}

    def execute(_mapping) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("boom")

    monkeypatch.setattr(service, "_execute", execute)
    mapping = KeyMapping.create(name="test", key="PAGE_DOWN", text="hello")

    try:
        service.submit(mapping)
        service.submit(mapping)
        deadline = time.time() + 2
        while calls["count"] < 2 and time.time() < deadline:
            time.sleep(0.01)
        assert calls["count"] == 2
        assert any(level == "error" for level, _message in statuses)
    finally:
        service.stop()
