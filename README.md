# KeyPaster

KeyPaster is a lightweight Windows utility, built entirely in **Python**, for mapping a keyboard key to a reusable block of text.

Press a mapped key and KeyPaster temporarily saves your clipboard, pastes the configured text into the active application, then restores your previous clipboard. The key's normal action is suppressed while the mapping is active — for example, **Page Down** can paste a prompt instead of scrolling.

If you use **AutoHotkey mainly for fixed text snippets**, KeyPaster is a focused alternative for that use case. It has no AutoHotkey dependency. It is especially useful when managing multiple AI or coding agents and repeatedly sending similar review, follow-up, or handoff prompts.

![KeyPaster interface](docs/keypaster-ui.png)

## Install

**Requirements:** Windows 10/11 and Python 3.11 or newer.

1. Click **Code → Download ZIP** on this repository and extract it.
2. Double-click `Run-KeyPaster.bat`.
3. On first launch, KeyPaster creates its own `.venv`, installs the required Python packages, and opens the app.

After the first launch, run `Run-KeyPaster.bat` whenever you want to start KeyPaster.

## Use

1. Click **New mapping**.
2. Give the mapping a name.
3. Choose the keyboard key to replace.
4. Enter the text you want that key to paste.
5. Click **Save mapping**.
6. Switch to any normal text field and press the mapped key.

Closing the main window keeps KeyPaster running in the notification area. Use **Pause hotkeys** when you temporarily want the mapped keys to behave normally.

Mappings are saved persistently in:

```text
%APPDATA%\KeyPaster\config.json
```

## How it works

For each mapped key press, KeyPaster:

1. snapshots the current Windows clipboard;
2. places the mapped text on the clipboard;
3. sends `Ctrl+V` to the active application; and
4. restores the previous clipboard contents.

KeyPaster uses Windows global hotkeys, so a successfully mapped key replaces its normal action while KeyPaster is active.

## Build a standalone executable

After running the source version once, double-click `Build-KeyPaster.bat`.

The executable is created at:

```text
dist\KeyPaster.exe
```

Your mappings are stored in your Windows profile, so replacing or rebuilding the executable does not remove them.

## Current limits

- Windows only.
- V1 maps individual keys rather than key combinations.
- F12 is unavailable because Windows reserves it for debuggers.
- Another application may already own a global hotkey; KeyPaster will report the conflict.
- A non-elevated KeyPaster process cannot send input to an elevated application.
