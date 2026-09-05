import os
import threading
from uuid import uuid4

import pytest

from keypaster.single_instance import SingleInstance


@pytest.mark.skipif(os.name != "nt", reason="Windows-only single-instance primitive")
def test_second_instance_signals_primary() -> None:
    name = rf"Local\KeyPaster.Test.{uuid4()}"
    first = SingleInstance(name)
    second = SingleInstance(name)
    called = threading.Event()

    try:
        assert first.is_primary is True
        assert second.is_primary is False
        first.start_watcher(called.set)
        second.signal_existing()
        assert called.wait(timeout=2)
    finally:
        second.close()
        first.close()
