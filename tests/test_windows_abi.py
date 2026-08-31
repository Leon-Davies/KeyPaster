import ctypes
import os
import sys

import pytest

from keypaster import windows


@pytest.mark.skipif(os.name != "nt", reason="Win32 ABI check")
def test_sendinput_structures_match_windows_abi() -> None:
    if sys.maxsize > 2**32:
        assert ctypes.sizeof(windows.KEYBDINPUT) == 24
        assert ctypes.sizeof(windows.INPUT) == 40
    else:
        assert ctypes.sizeof(windows.KEYBDINPUT) == 16
        assert ctypes.sizeof(windows.INPUT) == 28
