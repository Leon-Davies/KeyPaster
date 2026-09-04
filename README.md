# KeyPaster

KeyPaster is a small Windows utility built entirely in **Python**.

Map a keyboard key to either:

- reusable text
- volume up/down or mute
- play/pause, next track, previous track, or stop

For text mappings, KeyPaster saves your clipboard, pastes the text, then restores your previous clipboard. It is useful as a simple AutoHotkey replacement when you only need fixed text shortcuts, especially for repeated prompts when managing multiple AI or coding agents.

![KeyPaster](docs/keypaster-ui.png)

## Install

**Requires Windows 10/11 and Python 3.11+.**

1. Download this repository with **Code > Download ZIP**.
2. Extract it.
3. Double-click `Run-KeyPaster.bat`.

The first launch creates its own Python environment automatically.

## Use

1. Click **New mapping**.
2. Choose the key you want to replace.
3. Choose an action.
4. Add text if using **Paste text**.
5. Click **Save mapping**.

Minimizing or closing KeyPaster sends it to the system tray. Your mappings stay active and are saved between launches.

To build a standalone executable, run `Build-KeyPaster.bat`.
