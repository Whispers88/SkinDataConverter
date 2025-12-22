import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

SV_TTK_OK = True
try:
    import sv_ttk
except Exception:
    SV_TTK_OK = False

DND_OK = True
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:
    DND_OK = False

ULONG_MAX = (1 << 64) - 1

KEY_IMPORTED_WORKSHOP = {"imported workshop skins", "importedworkshopskins"}
KEY_STORED_DATA_SKINS = {"storeddataskins"}
KEY_SKIN_LIST = {"skinlist"}
LSKINS_HINT_FIELDS = {"isenabled", "isapproved", "marketname", "enabled", "approved"}

DARK = {
    "bg": "#1e1e1e",
    "panel": "#252526",
    "panel2": "#2d2d30",
    "fg": "#d4d4d4",
    "muted": "#a6a6a6",
    "border": "#3c3c3c",
    "select_bg": "#094771",
    "select_fg": "#ffffff",
}


def to_ulong(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if 0 <= value <= ULONG_MAX else None
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            n = int(s)
            return n if 0 <= n <= ULONG_MAX else None
    return None


def is_lskins_dict(d):
    if not isinstance(d, dict) or not d:
        return False
    keys_are_numeric = all(isinstance(k, str) and k.strip().isdigit() for k in d.keys())
    if not keys_are_numeric:
        return False
    values_are_dicts = all(isinstance(v, dict) for v in d.values())
    if not values_are_dicts:
        return False
    for v in d.values():
        for fk in v.keys():
            if isinstance(fk, str) and fk.strip().lower() in LSKINS_HINT_FIELDS:
                return True
    return True


def extract_ids(obj, out_ids):
    if isinstance(obj, dict):
        if is_lskins_dict(obj):
            for k in obj.keys():
                n = to_ulong(k)
                if n not in (None, 0):
                    out_ids.add(n)
            for v in obj.values():
                extract_ids(v, out_ids)
            return

        for k, v in obj.items():
            k_norm = k.strip().lower() if isinstance(k, str) else ""

            if isinstance(k, str) and k_norm == "skinid":
                n = to_ulong(v)
                if n not in (None, 0):
                    out_ids.add(n)
                continue

            if k_norm in KEY_IMPORTED_WORKSHOP and isinstance(v, dict):
                for _, lst in v.items():
                    extract_ids(lst, out_ids)
                continue

            if k_norm in KEY_STORED_DATA_SKINS:
                extract_ids(v, out_ids)
                continue

            if k_norm in KEY_SKIN_LIST:
                extract_ids(v, out_ids)
                continue

            extract_ids(v, out_ids)
        return

    if isinstance(obj, list):
        if not obj:
            return

        all_scalar_ulongs = True
        for x in obj:
            if to_ulong(x) is None:
                all_scalar_ulongs = False
                break

        if all_scalar_ulongs:
            for x in obj:
                n = to_ulong(x)
                if n not in (None, 0):
                    out_ids.add(n)
            return

        for x in obj:
            extract_ids(x, out_ids)
        return

    return


def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Skin/Workshop ID Converter")
        self.root.minsize(980, 640)

        self.added_files = []
        self.added_files_set = set()
        self.merged_ids = set()

        self._apply_dark_theme()
        self._build_ui()
        self._setup_dnd()

        self._set_status("Drop JSON files anywhere in the window, or click Add…")

    def _apply_dark_theme(self):
        if SV_TTK_OK:
            sv_ttk.set_theme("dark")
            return

        self.root.configure(bg=DARK["bg"])
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=DARK["bg"])
        style.configure("Card.TFrame", background=DARK["panel"], relief="flat")
        style.configure("Toolbar.TFrame", background=DARK["bg"])
        style.configure("TLabel", background=DARK["bg"], foreground=DARK["fg"])
        style.configure("Muted.TLabel", background=DARK["bg"], foreground=DARK["muted"])
        style.configure("Title.TLabel", background=DARK["bg"], foreground=DARK["fg"], font=("Segoe UI", 12, "bold"))

        style.configure("TButton", padding=(12, 8))
        style.map(
            "TButton",
            foreground=[("disabled", DARK["muted"])],
        )

    def _build_ui(self):
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 6))

        ttk.Label(toolbar, text="Skin/Workshop ID Converter", style="Title.TLabel").pack(side=tk.LEFT)

        ttk.Frame(toolbar).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Button(toolbar, text="Add…", command=self.add_files_via_dialog).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="Save As…", command=self.save_output_as).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="Copy", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="Clear", command=self.clear_all).pack(side=tk.LEFT)

        content = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left_card = ttk.Frame(content, style="Card.TFrame")
        content.add(left_card, weight=1)

        right_card = ttk.Frame(content, style="Card.TFrame")
        content.add(right_card, weight=2)

        left = ttk.Frame(left_card)
        left.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        right = ttk.Frame(right_card)
        right.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left_hdr = ttk.Frame(left)
        left_hdr.pack(fill=tk.X)

        ttk.Label(left_hdr, text="Files").pack(side=tk.LEFT)
        self.count_label = ttk.Label(left_hdr, text="Files: 0   IDs: 0", style="Muted.TLabel")
        self.count_label.pack(side=tk.RIGHT)

        self.drop_hint = ttk.Label(
            left,
            text="Drag & drop .json files here.\nThen copy and save the output to oxide/data/skinner/ImportedSkins.json",
            style="Muted.TLabel",
            anchor="center",
            justify="center",
        )
        self.drop_hint.pack(fill=tk.X, pady=(10, 10))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.file_list = tk.Listbox(
            list_frame,
            activestyle="none",
            borderwidth=1,
            highlightthickness=1,
            selectmode=tk.EXTENDED,
        )
        self.file_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=self.file_scroll.set)

        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        right_hdr = ttk.Frame(right)
        right_hdr.pack(fill=tk.X)

        ttk.Label(right_hdr, text="Output").pack(side=tk.LEFT)
        ttk.Label(right_hdr, text='Format: { "ulong": {} }', style="Muted.TLabel").pack(side=tk.RIGHT)

        out_frame = ttk.Frame(right)
        out_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.output_text = tk.Text(out_frame, wrap="word", undo=True, borderwidth=1, highlightthickness=1)
        self.out_scroll = ttk.Scrollbar(out_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=self.out_scroll.set)

        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.out_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.status = ttk.Label(self.root, text="", anchor="w", style="Muted.TLabel")
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        if not SV_TTK_OK:
            self._apply_dark_to_tk_widgets()

        self._update_counts()

    def _apply_dark_to_tk_widgets(self):
        self.file_list.configure(
            bg=DARK["panel2"],
            fg=DARK["fg"],
            selectbackground=DARK["select_bg"],
            selectforeground=DARK["select_fg"],
            highlightbackground=DARK["border"],
            highlightcolor=DARK["border"],
        )
        self.output_text.configure(
            bg=DARK["panel2"],
            fg=DARK["fg"],
            insertbackground=DARK["fg"],
            highlightbackground=DARK["border"],
            highlightcolor=DARK["border"],
        )

    def _setup_dnd(self):
        if not DND_OK:
            return

        for w in (self.root, self.drop_hint, self.file_list):
            try:
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

    def _set_status(self, msg):
        self.status.config(text=msg)

    def _update_counts(self):
        self.count_label.config(text=f"Files: {len(self.added_files)}   IDs: {len(self.merged_ids)}")

    def _render_output(self):
        out = {str(i): {} for i in sorted(self.merged_ids)}
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, json.dumps(out, indent=2))

    def _refresh_files_list(self):
        self.file_list.delete(0, tk.END)
        for p in self.added_files:
            self.file_list.insert(tk.END, os.path.basename(p))

    def add_files(self, paths):
        if not paths:
            return

        errors = []
        added_now = 0
        ids_before = len(self.merged_ids)

        for p in paths:
            p = p.strip()
            if not p:
                continue

            if p.startswith("{") and p.endswith("}"):
                p = p[1:-1]

            if not p.lower().endswith(".json"):
                continue
            if p in self.added_files_set:
                continue

            try:
                data = load_json_file(p)
                ids = set()
                extract_ids(data, ids)
                self.merged_ids.update(ids)

                self.added_files.append(p)
                self.added_files_set.add(p)
                added_now += 1
            except Exception as e:
                errors.append(f"{p}: {e}")

        self._refresh_files_list()
        self._update_counts()
        self._render_output()

        ids_added = len(self.merged_ids) - ids_before
        self._set_status(f"Added {added_now} file(s), +{ids_added} new ID(s). Total IDs: {len(self.merged_ids)}")

        if errors:
            messagebox.showwarning(
                "Some files failed",
                "Some files could not be imported:\n\n"
                + "\n".join(errors[:12])
                + ("" if len(errors) <= 12 else "\n..."),
            )

    def add_files_via_dialog(self):
        paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        self.add_files(list(paths))

    def on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
        except Exception:
            paths = [event.data]
        self.add_files(list(paths))

    def clear_all(self):
        self.added_files.clear()
        self.added_files_set.clear()
        self.merged_ids.clear()

        self._refresh_files_list()
        self._update_counts()
        self.output_text.delete("1.0", tk.END)
        self._set_status("Cleared. Drop more JSON files to begin again.")

    def copy_to_clipboard(self):
        text = self.output_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._set_status("Copied output to clipboard.")

    def save_output_as(self):
        raw = self.output_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Nothing to save", "No output to save yet.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="converted_skins.json",
        )
        if not path:
            return

        try:
            parsed = json.loads(raw)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
            self._set_status(f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))


def main():
    if DND_OK:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
