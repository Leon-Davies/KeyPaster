from keypaster.windows import (
    CF_BITMAP,
    CF_DIB,
    CF_DIBV5,
    CF_ENHMETAFILE,
    CF_GDIOBJFIRST,
    CF_HDROP,
    CF_LOCALE,
    CF_OEMTEXT,
    CF_TEXT,
    CF_UNICODETEXT,
    REGISTERED_FORMAT_FIRST,
    is_hglobal_clipboard_format,
)


def test_known_hglobal_formats_are_safe_to_clone() -> None:
    for format_id in (
        CF_TEXT,
        CF_OEMTEXT,
        CF_DIB,
        CF_UNICODETEXT,
        CF_HDROP,
        CF_LOCALE,
        CF_DIBV5,
        CF_GDIOBJFIRST,
        REGISTERED_FORMAT_FIRST,
    ):
        assert is_hglobal_clipboard_format(format_id)


def test_typed_and_private_handles_are_not_global_locked() -> None:
    assert not is_hglobal_clipboard_format(CF_BITMAP)
    assert not is_hglobal_clipboard_format(CF_ENHMETAFILE)
    assert not is_hglobal_clipboard_format(0x0200)
