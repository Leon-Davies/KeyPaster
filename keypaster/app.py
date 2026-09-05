from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import tkinter as tk
from pathlib import Path

from . import __version__
from .config import ConfigError, ConfigStore
from .dispatcher import UiDispatcher
from .models import AppConfig
from .service import PasteService
from .single_instance import SingleInstance
from .ui import KeyPasterUI
from .windows import HotkeyManager


APP_NAME = "KeyPaster"


def _configure_logging() -> None:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".cache"
    log_dir = base / APP_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "keypaster.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s: %(message)s",
    )


def _load_config(store: ConfigStore) -> AppConfig:
    try:
        return store.load()
    except ConfigError as exc:
        logging.exception("Configuration could not be loaded from %s", store.path)
        raise SystemExit(str(exc)) from exc


def _tray_icon_image():
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (35, 104, 211, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=10, fill=(255, 255, 255, 255))
    draw.rectangle((18, 20, 46, 25), fill=(35, 104, 211, 255))
    draw.rectangle((18, 31, 46, 36), fill=(35, 104, 211, 255))
    draw.rectangle((18, 42, 38, 47), fill=(35, 104, 211, 255))
    return image


def main(argv: list[str] | None = None) -> int:
    if os.name != "nt":
        print("KeyPaster currently supports Windows only.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="KeyPaster desktop application")
    parser.add_argument("--minimized", action="store_true", help="Start minimized")
    args = parser.parse_args(argv)

    _configure_logging()
    store = ConfigStore()
    frozen = bool(getattr(sys, "frozen", False))
    try:
        entrypoint = str(Path(sys.argv[0]).resolve())
    except OSError:
        entrypoint = sys.argv[0]
    logging.info(
        "START KeyPaster version=%s pid=%s frozen=%s executable=%s entrypoint=%s config=%s",
        __version__,
        os.getpid(),
        frozen,
        sys.executable,
        entrypoint,
        store.path,
    )

    instance = SingleInstance()
    if not instance.is_primary:
        logging.info("SECONDARY instance detected; signalling existing KeyPaster and exiting")
        try:
            instance.signal_existing()
        finally:
            instance.close()
        return 0

    config = _load_config(store)

    root = tk.Tk()
    root.withdraw()
    dispatcher = UiDispatcher(root)

    def report_tk_exception(exc_type, exc_value, exc_traceback) -> None:
        logging.error("Tk callback failed", exc_info=(exc_type, exc_value, exc_traceback))

    root.report_callback_exception = report_tk_exception

    previous_thread_hook = threading.excepthook

    def report_thread_exception(args: threading.ExceptHookArgs) -> None:
        logging.error(
            "Unhandled background thread exception",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        previous_thread_hook(args)

    threading.excepthook = report_thread_exception

    shutting_down = False
    tray = None
    ui: KeyPasterUI | None = None

    def runtime_status(level: str, message: str) -> None:
        logging.log(logging.ERROR if level == "error" else logging.INFO, message)
        if ui:
            dispatcher.post(ui.set_runtime_status, level, message)

    paste_service = PasteService(status_callback=runtime_status)
    hotkeys = HotkeyManager(on_hotkey=paste_service.submit)
    hotkeys.start()

    def show_window() -> None:
        if ui:
            ui.show()

    def hide_window() -> None:
        if ui:
            ui.hide()

    def shutdown() -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        logging.info("SHUTDOWN KeyPaster version=%s pid=%s", __version__, os.getpid())
        try:
            if tray:
                tray.stop()
        except Exception:
            logging.exception("Tray shutdown failed")
        try:
            hotkeys.stop()
        except Exception:
            logging.exception("Hotkey shutdown failed")
        try:
            paste_service.stop()
        except Exception:
            logging.exception("Action worker shutdown failed")
        try:
            instance.close()
        except Exception:
            logging.exception("Single-instance shutdown failed")
        dispatcher.stop()
        try:
            root.quit()
            root.destroy()
        except tk.TclError:
            pass

    ui = KeyPasterUI(
        root=root,
        config_store=store,
        config=config,
        hotkeys=hotkeys,
        on_exit=shutdown,
        on_hide=hide_window,
    )
    root.title(f"KeyPaster {__version__}")
    dispatcher.start()
    instance.start_watcher(lambda: dispatcher.post(show_window))

    try:
        import pystray

        tray = pystray.Icon(
            APP_NAME,
            _tray_icon_image(),
            f"KeyPaster {__version__} - double-click to open",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Open KeyPaster",
                    lambda _icon, _item: dispatcher.post(show_window),
                    default=True,
                ),
                pystray.MenuItem("Exit", lambda _icon, _item: dispatcher.post(shutdown)),
            ),
        )
        tray.run_detached()
        ui.set_tray_available(True)
    except Exception:
        logging.exception("Could not create notification-area icon")
        tray = None
        ui.set_tray_available(False)

    if args.minimized:
        if ui.can_hide_to_tray and config.settings.minimize_to_tray:
            ui.hide()
        else:
            ui.show()
            root.iconify()
    else:
        ui.show()

    try:
        root.mainloop()
    finally:
        if not shutting_down:
            shutdown()
        threading.excepthook = previous_thread_hook
    return 0
