from keypaster.dispatcher import UiDispatcher


class FakeRoot:
    def __init__(self) -> None:
        self.callbacks = []

    def after(self, _delay: int, callback) -> None:
        self.callbacks.append(callback)


def test_dispatcher_runs_posted_work_from_scheduled_drain() -> None:
    root = FakeRoot()
    dispatcher = UiDispatcher(root, interval_ms=1)
    seen: list[str] = []

    dispatcher.start()
    dispatcher.post(seen.append, "ok")

    assert len(root.callbacks) == 1
    root.callbacks.pop(0)()
    assert seen == ["ok"]


def test_dispatcher_drops_new_work_after_stop() -> None:
    root = FakeRoot()
    dispatcher = UiDispatcher(root, interval_ms=1)
    seen: list[str] = []

    dispatcher.start()
    dispatcher.stop()
    dispatcher.post(seen.append, "late")

    root.callbacks.pop(0)()
    assert seen == []
