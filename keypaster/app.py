from __future__ import annotations

import argparse
import logging
import os
import sys
import tkinter as tk
from pathlib import Path

from .config import ConfigError, ConfigStore
from .models import AppConfig
from .service import PasteService
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
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _load_config(store: ConfigStore) -> AppConfig:
    try:
        return store.load()
    except ConfigError as exc:
        logging.exception("Configuration could not be loaded")
        raise SystemExit(str(exc)) from exc


def _tray_icon_image():
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (35, 104, 211, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 8, 54, 56), radius=9, fill=(255, 255, 255, 255))
    draw.rectangle((20, 20, 44, 24), fill=(35, 104, 211, 255))
    draw.rectangle((20, 30, 44, 34), fill=(35, 104, 211, 255))
    draw.rectangle((20, 40, 36, 44), fill=(35, 104, 211, 255))
    return image


def main(argv: list[str] | None = None) -> int:
    if os.name != "nt":
        print("KeyPaster currently supports Windows only.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="KeyPaster desktop application")
    parser.add_argument("--minimized", action="store_true", help="Start hidden in the notification area")
    args = parser.parse_args(argv)

    _configure_logging()
    store = ConfigStore()
    config = _load_config(store)

    root = tk.Tk()
    root.withdraw()

    shutting_down = False
    tray = None
    ui: KeyPasterUI | None = None

    def runtime_status(level: str, message: str) -> None:
        logging.log(logging.ERROR if level == "error" else logging.INFO, message)
        if ui:
            ui.set_runtime_status(level, message)

    paste_service = PasteService(status_callback=runtime_status)
    hotkeys = HotkeyManager(on_hotkey=paste_service.submit)
    hotkeys.start()

    def show_window() -> None:
        if ui:
            root.after(0, ui.show)

    def hide_window() -> None:
        if ui:
            root.after(0, ui.hide)

    def shutdown() -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        try:
            if tray:
                tray.stop()
        except Exception:
            logging.exception("Tray shutdown failed")
        try:
            hotkeys.stop()
        finally:
            paste_service.stop()
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

    try:
        import pystray

        tray = pystray.Icon(
            APP_NAME,
            _tray_icon_image(),
            APP_NAME,
            menu=pystray.Menu(
                pystray.MenuItem("Open KeyPaster", lambda _icon, _item: show_window(), default=True),
                pystray.MenuItem("Exit", lambda _icon, _item: root.after(0, shutdown)),
            ),
        )
        tray.run_detached()
    except Exception:
        logging.exception("Could not create notification-area icon")
        tray = None

    if args.minimized:
        ui.hide()
    else:
        ui.show()

    try:
        root.mainloop()
    finally:
        if not shutting_down:
            shutdown()
    return 0
