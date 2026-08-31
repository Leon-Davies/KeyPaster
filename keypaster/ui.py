from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .config import ConfigError, ConfigStore
from .keys import KEY_ID_BY_LABEL, key_label, key_labels
from .models import AppConfig, KeyMapping
from .windows import HotkeyManager, is_frozen, set_start_with_windows


BG = "#F4F6F8"
CARD = "#FFFFFF"
TEXT = "#18212F"
MUTED = "#637083"
ACCENT = "#2368D3"
ACCENT_HOVER = "#1B56B2"
BORDER = "#DCE2EA"
SUCCESS = "#1F7A4D"
WARNING = "#A86005"
DANGER = "#B42318"


class KeyPasterUI:
    def __init__(
        self,
        root: tk.Tk,
        config_store: ConfigStore,
        config: AppConfig,
        hotkeys: HotkeyManager,
        on_exit: Callable[[], None],
        on_hide: Callable[[], None],
    ) -> None:
        self.root = root
        self.config_store = config_store
        self.config = config
        self.hotkeys = hotkeys
        self.on_exit = on_exit
        self.on_hide = on_hide
        self.selected_id: str | None = None
        self.manual_paused = False
        self._focus_suspended: bool | None = None
        self._registration_errors: dict[str, str] = {}

        self.root.title("KeyPaster")
        self.root.geometry("960x650")
        self.root.minsize(820, 560)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._configure_styles()
        self._build_ui()
        self._refresh_mappings()
        self._apply_hotkeys(show_errors=False)
        self._sync_startup_checkbox()
        self._poll_focus_state()
        if not self.config.mappings:
            self._new_mapping()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10), background=CARD, fieldbackground=CARD)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))
        style.configure("TCombobox", padding=6)
        style.configure("TCheckbutton", background=BG, font=("Segoe UI", 9))

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 14))
        title_block = tk.Frame(header, bg=BG)
        title_block.pack(side="left")
        tk.Label(title_block, text="KeyPaster", font=("Segoe UI Semibold", 24), fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(
            title_block,
            text="Map a keyboard key to reusable text, then paste it anywhere with one press.",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

        self.pause_button = tk.Button(
            header,
            text="Pause hotkeys",
            command=self._toggle_manual_pause,
            font=("Segoe UI Semibold", 9),
            fg=TEXT,
            bg=CARD,
            activebackground="#E9EEF5",
            relief="flat",
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.pause_button.pack(side="right", pady=4)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=26, pady=(0, 18))
        body.grid_columnconfigure(0, weight=4, uniform="body")
        body.grid_columnconfigure(1, weight=5, uniform="body")
        body.grid_rowconfigure(0, weight=1)

        left = self._card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        left_heading = tk.Frame(left, bg=CARD)
        left_heading.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        tk.Label(left_heading, text="Mappings", font=("Segoe UI Semibold", 14), fg=TEXT, bg=CARD).pack(side="left")
        self.new_button = self._primary_button(left_heading, "＋ New mapping", self._new_mapping)
        self.new_button.pack(side="right")

        tk.Label(
            left,
            text="A mapped key is replaced globally while KeyPaster is active.",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=CARD,
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))

        tree_frame = tk.Frame(left, bg=CARD)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=("key", "name"), show="headings", selectmode="browse")
        self.tree.heading("key", text="Key")
        self.tree.heading("name", text="Name / preview")
        self.tree.column("key", width=120, minwidth=90, stretch=False)
        self.tree.column("name", width=240, minwidth=160, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        right = self._card(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(7, weight=1)

        tk.Label(right, text="Mapping details", font=("Segoe UI Semibold", 14), fg=TEXT, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=22, pady=(20, 14)
        )
        self._field_label(right, "Name", 1)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(right, textvariable=self.name_var, font=("Segoe UI", 10))
        self.name_entry.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 13), ipady=5)

        self._field_label(right, "Key", 3)
        self.key_var = tk.StringVar()
        self.key_combo = ttk.Combobox(
            right,
            textvariable=self.key_var,
            values=key_labels(),
            state="readonly",
            font=("Segoe UI", 10),
        )
        self.key_combo.grid(row=4, column=0, sticky="ew", padx=22, pady=(0, 13))

        self._field_label(right, "Text to paste", 5)
        tk.Label(
            right,
            text="Line breaks and Unicode are preserved.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=CARD,
        ).grid(row=6, column=0, sticky="w", padx=22, pady=(0, 5))

        text_frame = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        text_frame.grid(row=7, column=0, sticky="nsew", padx=22, pady=(0, 14))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        self.text_box = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            font=("Segoe UI", 10),
            fg=TEXT,
            bg="#FBFCFE",
            insertbackground=TEXT,
            relief="flat",
            padx=10,
            pady=10,
        )
        self.text_box.grid(row=0, column=0, sticky="nsew")
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_box.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.text_box.configure(yscrollcommand=text_scroll.set)

        actions = tk.Frame(right, bg=CARD)
        actions.grid(row=8, column=0, sticky="ew", padx=22, pady=(0, 14))
        self.save_button = self._primary_button(actions, "Save mapping", self._save_mapping)
        self.save_button.pack(side="left")
        self.delete_button = self._secondary_button(actions, "Delete", self._delete_mapping, danger=True)
        self.delete_button.pack(side="left", padx=(8, 0))
        self.clear_button = self._secondary_button(actions, "Clear", self._new_mapping)
        self.clear_button.pack(side="right")

        settings = tk.Frame(self.root, bg=BG)
        settings.pack(fill="x", padx=28, pady=(0, 8))
        self.startup_var = tk.BooleanVar(value=False)
        self.startup_check = ttk.Checkbutton(
            settings,
            text="Start KeyPaster with Windows",
            variable=self.startup_var,
            command=self._toggle_startup,
        )
        self.startup_check.pack(side="left")
        if not is_frozen():
            self.startup_check.state(["disabled"])
            tk.Label(
                settings,
                text="(available in the packaged .exe)",
                font=("Segoe UI", 8),
                fg=MUTED,
                bg=BG,
            ).pack(side="left", padx=(4, 0))

        self.status_label = tk.Label(
            settings,
            text="Ready",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=BG,
            anchor="e",
        )
        self.status_label.pack(side="right")

    @staticmethod
    def _card(parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)

    @staticmethod
    def _field_label(parent: tk.Widget, text: str, row: int) -> None:
        tk.Label(parent, text=text, font=("Segoe UI Semibold", 9), fg=TEXT, bg=CARD).grid(
            row=row, column=0, sticky="w", padx=22, pady=(0, 5)
        )

    @staticmethod
    def _primary_button(parent: tk.Widget, text: str, command: Callable[[], None]) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI Semibold", 9),
            fg="white",
            bg=ACCENT,
            activeforeground="white",
            activebackground=ACCENT_HOVER,
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )

    @staticmethod
    def _secondary_button(parent: tk.Widget, text: str, command: Callable[[], None], danger: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9),
            fg=DANGER if danger else TEXT,
            bg="#F0F3F7",
            activebackground="#E4E9F0",
            relief="flat",
            bd=0,
            padx=13,
            pady=8,
            cursor="hand2",
        )

    def _refresh_mappings(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for mapping in self.config.mappings:
            preview = " ".join(mapping.text.split())
            if len(preview) > 42:
                preview = preview[:39] + "…"
            description = mapping.name or preview
            if mapping.id in self._registration_errors:
                description = f"⚠ {description}"
            self.tree.insert("", "end", iid=mapping.id, values=(key_label(mapping.key), description))
        if self.selected_id and self.tree.exists(self.selected_id):
            self.tree.selection_set(self.selected_id)
        self._update_status()

    def _on_tree_select(self, _event: object = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        mapping = self._find_mapping(selection[0])
        if not mapping:
            return
        self.selected_id = mapping.id
        self.name_var.set(mapping.name)
        self.key_var.set(key_label(mapping.key))
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", mapping.text)

    def _new_mapping(self) -> None:
        self.selected_id = None
        self.tree.selection_remove(*self.tree.selection())
        self.name_var.set("")
        self.key_var.set("Page Down")
        self.text_box.delete("1.0", "end")
        self.name_entry.focus_set()

    def _save_mapping(self) -> None:
        label = self.key_var.get().strip()
        key_id = KEY_ID_BY_LABEL.get(label)
        text = self.text_box.get("1.0", "end-1c")
        name = self.name_var.get().strip()
        if not key_id:
            messagebox.showwarning("Choose a key", "Choose the keyboard key you want to map.", parent=self.root)
            return
        if not text:
            messagebox.showwarning("Add text", "Enter the text KeyPaster should paste.", parent=self.root)
            return
        duplicate = next((m for m in self.config.mappings if m.key == key_id and m.id != self.selected_id), None)
        if duplicate:
            messagebox.showwarning(
                "Key already mapped",
                f"{label} is already mapped to “{duplicate.name or 'another entry'}”. Choose a different key.",
                parent=self.root,
            )
            return
        if self.selected_id:
            mapping = self._find_mapping(self.selected_id)
            if mapping:
                mapping.name = name
                mapping.key = key_id
                mapping.text = text
        else:
            mapping = KeyMapping.create(name=name, key=key_id, text=text)
            self.config.mappings.append(mapping)
            self.selected_id = mapping.id
        try:
            self.config_store.save(self.config)
        except ConfigError as exc:
            messagebox.showerror("Could not save", str(exc), parent=self.root)
            return
        self._apply_hotkeys(show_errors=True)
        self._refresh_mappings()
        self._set_status("ok", f"Saved {label} mapping.")

    def _delete_mapping(self) -> None:
        if not self.selected_id:
            return
        mapping = self._find_mapping(self.selected_id)
        if not mapping:
            return
        if not messagebox.askyesno(
            "Delete mapping",
            f"Delete the mapping for {key_label(mapping.key)}?",
            parent=self.root,
        ):
            return
        self.config.mappings = [m for m in self.config.mappings if m.id != mapping.id]
        self.selected_id = None
        self.config_store.save(self.config)
        self._apply_hotkeys(show_errors=False)
        self._refresh_mappings()
        self._new_mapping()
        self._set_status("ok", "Mapping deleted.")

    def _apply_hotkeys(self, show_errors: bool) -> None:
        # Always stage the current configuration with the hotkey thread, even if
        # KeyPaster is temporarily suspended while its own window has focus.
        self._registration_errors = self.hotkeys.reload(self.config.mappings)
        should_suspend = self.manual_paused or self._is_ui_focused()
        state_errors = self.hotkeys.set_suspended(should_suspend)
        if not should_suspend:
            self._registration_errors = state_errors
        if show_errors and self._registration_errors:
            failed = [key_label(m.key) for m in self.config.mappings if m.id in self._registration_errors]
            messagebox.showwarning(
                "Some keys could not be registered",
                "Windows is already using or reserving: " + ", ".join(failed) + ".\n\nChoose another key for those mappings.",
                parent=self.root,
            )

    def _toggle_manual_pause(self) -> None:
        self.manual_paused = not self.manual_paused
        self.pause_button.configure(text="Resume hotkeys" if self.manual_paused else "Pause hotkeys")
        self._sync_hotkey_suspension(force=True)

    def _poll_focus_state(self) -> None:
        self._sync_hotkey_suspension()
        self.root.after(250, self._poll_focus_state)

    def _sync_hotkey_suspension(self, force: bool = False) -> None:
        focused = self._is_ui_focused()
        desired = self.manual_paused or focused
        if force or desired != self._focus_suspended:
            self._focus_suspended = desired
            errors = self.hotkeys.set_suspended(desired)
            if not desired:
                self._registration_errors = errors
                self._refresh_mappings()
            self._update_status()

    def _is_ui_focused(self) -> bool:
        try:
            return self.root.focus_get() is not None
        except tk.TclError:
            return False

    def _update_status(self) -> None:
        if self.manual_paused:
            self._set_status("warning", "Hotkeys paused")
            return
        if self._is_ui_focused():
            self._set_status("info", "Hotkeys pause while KeyPaster is focused")
            return
        active = len(self.config.mappings) - len(self._registration_errors)
        if self._registration_errors:
            self._set_status("warning", f"Active · {active}/{len(self.config.mappings)} mappings")
        else:
            self._set_status("ok", f"Active · {active} mapping{'s' if active != 1 else ''}")

    def set_runtime_status(self, level: str, message: str) -> None:
        self.root.after(0, lambda: self._set_status(level, message))

    def _set_status(self, level: str, message: str) -> None:
        colors = {"ok": SUCCESS, "warning": WARNING, "error": DANGER, "info": MUTED}
        self.status_label.configure(text=message, fg=colors.get(level, MUTED))

    def _find_mapping(self, mapping_id: str) -> KeyMapping | None:
        return next((mapping for mapping in self.config.mappings if mapping.id == mapping_id), None)

    def _sync_startup_checkbox(self) -> None:
        self.startup_var.set(self.config.settings.start_with_windows if is_frozen() else False)

    def _toggle_startup(self) -> None:
        enabled = bool(self.startup_var.get())
        try:
            set_start_with_windows(enabled)
            self.config.settings.start_with_windows = enabled
            self.config_store.save(self.config)
            self._set_status("ok", "Windows startup setting updated.")
        except Exception as exc:
            self.startup_var.set(not enabled)
            messagebox.showerror("Could not update startup", str(exc), parent=self.root)

    def _handle_close(self) -> None:
        if self.config.settings.close_to_tray:
            self.on_hide()
        else:
            self.on_exit()

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.after(50, self.root.focus_force)

    def hide(self) -> None:
        self.root.withdraw()
        self._sync_hotkey_suspension(force=True)
