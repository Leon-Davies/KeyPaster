# KeyPaster

KeyPaster is a small Windows utility for mapping a single keyboard key to a reusable block of text.

When you press a mapped key, KeyPaster:

1. snapshots the current Windows clipboard;
2. places your configured text on the clipboard;
3. sends `Ctrl+V` to the currently focused application;
4. waits briefly for the target application to consume the paste; and
5. restores the previous clipboard contents.

A successfully registered mapped key is consumed as a Windows global hotkey, so its normal action is replaced while KeyPaster is active. For example, mapping **Page Down** means Page Down pastes your text instead of scrolling.

## What V1 includes

- A graphical editor for creating, editing and deleting mappings.
- A broad choice of navigation, function, letter, number and numpad keys.
- Persistent configuration in `%APPDATA%\KeyPaster\config.json`.
- Immediate hotkey updates after saving a mapping.
- Automatic protection against assigning the same key twice.
- A warning when Windows refuses a reserved or conflicting key.
- Clipboard restoration for common HGLOBAL-backed Windows formats, including Unicode text, HTML/RTF payloads, DIB images, file-drop payloads and many registered formats.
- A notification-area icon: closing the window hides KeyPaster instead of stopping your mappings.
- A **Pause hotkeys** control.
- Hotkeys automatically pause while the KeyPaster editor itself has focus, making it possible to edit text even if you map a letter key.
- **Start KeyPaster with Windows** when running the packaged `.exe`.
- A Windows GitHub Actions build that produces a portable `KeyPaster.exe`.

## Fastest way to use it

### Packaged executable

Open the latest successful **Windows CI and build** workflow in GitHub Actions, download the `KeyPaster-Windows` artifact, extract it, and run `KeyPaster.exe`.

The executable is portable. Your mappings are stored in your Windows profile rather than next to the executable, so rebuilding or replacing the `.exe` does not erase them.

### Run from source

If Python 3.11+ is installed, double-click `Run-KeyPaster.bat`. On first run it creates a local `.venv`, installs the two runtime dependencies, and launches KeyPaster without a console window.

## First-use test

1. Open KeyPaster.
2. Click **New mapping**.
3. Choose **Page Down**.
4. Enter a name and some multi-line text, then click **Save mapping**.
5. Copy a recognisable piece of text such as `ORIGINAL CLIPBOARD`.
6. Click into Notepad (or another text field) and press **Page Down**.
7. Confirm the mapped text is pasted and the page does not scroll.
8. Press normal `Ctrl+V`; `ORIGINAL CLIPBOARD` should paste, proving the previous clipboard was restored.

## Notes and limits

- KeyPaster is Windows-only.
- F12 is intentionally unavailable because Windows reserves it for debuggers.
- Windows can refuse a key if another program has already registered it globally; KeyPaster reports that mapping as unavailable.
- `SendInput` follows normal Windows integrity rules. A non-elevated KeyPaster instance cannot inject input into an elevated application.
- Clipboard formats backed by opaque handles rather than movable global memory are not cloned. KeyPaster restores the common data representations used by normal text, rich text, browser content, copied files and typical copied images. If an uncommon clipboard format cannot be cloned, the UI reports a warning after the paste.

## Build locally

Double-click `Build-KeyPaster.bat` after the source environment exists. The result is written to `dist\KeyPaster.exe`.
