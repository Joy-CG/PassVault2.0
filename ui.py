"""
ui.py — PassVault GUI

Design language: sleek black & white futuristic / minimal
  - Pure black (#080808) background
  - Crisp white (#ffffff) as primary accent
  - Mid-greys for hierarchy (#1a1a1a cards, #2a2a2a borders, #888 dim text)
  - Sharp geometry: thin 1px borders, no rounded corners, tight spacing
  - Monospace everywhere for that terminal-meets-luxury feel
  - Danger: desaturated red (#cc3333) — understated, not garish
"""

import tkinter as tk
from tkinter import ttk, messagebox
from vault import Vault
from generator import generate_password, estimate_entropy, pool_size
from breach import check_breach, breach_summary

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = "#080808"
BG2       = "#111111"
BG3       = "#1a1a1a"
BORDER    = "#2a2a2a"
BORDER_HI = "#ffffff"
FG        = "#ffffff"
FG_DIM    = "#666666"
FG_MID    = "#aaaaaa"
ACCENT    = "#ffffff"
DANGER    = "#cc3333"
SUCCESS   = "#44aa66"
MONO      = ("Courier New", 11)
MONO_LG   = ("Courier New", 13, "bold")
MONO_SM   = ("Courier New", 9)
SANS_SM   = ("Helvetica", 9)


def copy_to_clipboard(root: tk.Tk, text: str) -> None:
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()


def styled_entry(parent, show="", width=30, font=MONO) -> tk.Entry:
    return tk.Entry(
        parent, show=show, width=width, font=font,
        bg=BG3, fg=FG, insertbackground=FG,
        relief="flat", highlightthickness=1,
        highlightbackground=BORDER, highlightcolor=BORDER_HI,
    )


def styled_button(parent, text, command, danger=False, ghost=False, small=False) -> tk.Button:
    if danger:
        bg, fg, abg, hl = "#1a0a0a", DANGER, "#2a0f0f", DANGER
    elif ghost:
        bg, fg, abg, hl = BG3, FG_MID, BG2, BORDER
    else:
        bg, fg, abg, hl = FG, BG, "#cccccc", FG
    font = ("Courier New", 8) if small else ("Courier New", 10, "bold")
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
        relief="flat", padx=12, pady=5, cursor="hand2", font=font, bd=0,
        highlightthickness=1, highlightbackground=hl, highlightcolor=hl,
    )


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginScreen(tk.Frame):
    def __init__(self, master, vault, on_success):
        super().__init__(master, bg=BG)
        self._vault = vault
        self._on_success = on_success
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)
        card = tk.Frame(self, bg=BG2, padx=48, pady=48,
                        highlightthickness=1, highlightbackground=BORDER_HI)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Frame(card, bg=FG, height=3, width=320).pack(fill="x", pady=(0, 28))
        tk.Label(card, text="PASSVAULT", font=("Courier New", 32, "bold"),
                 bg=BG2, fg=FG).pack()
        tk.Label(card, text="SECURE  LOCAL  PASSWORD  MANAGER",
                 font=("Courier New", 8), bg=BG2, fg=FG_DIM).pack(pady=(4, 32))

        tk.Label(card, text="MASTER PASSWORD", font=("Courier New", 8),
                 bg=BG2, fg=FG_DIM, anchor="w").pack(fill="x")
        self._pw_entry = styled_entry(card, show="*", width=34, font=MONO_LG)
        self._pw_entry.pack(fill="x", ipady=8, pady=(4, 4))
        self._pw_entry.bind("<Return>", lambda _: self._submit())
        self._pw_entry.focus()

        self._status_var = tk.StringVar()
        tk.Label(card, textvariable=self._status_var, font=("Courier New", 8),
                 bg=BG2, fg=DANGER, wraplength=300, anchor="w").pack(fill="x", pady=(2, 16))

        is_new = not self._vault.vault_exists()
        btn_text = "[ INITIALISE VAULT ]" if is_new else "[ UNLOCK VAULT ]"
        styled_button(card, btn_text, self._submit).pack(fill="x", ipady=6)

        if is_new:
            tk.Label(card, text="No vault detected. A new vault will be created.",
                     font=("Courier New", 8), bg=BG2, fg=FG_DIM, wraplength=300).pack(pady=(12, 0))

        tk.Frame(card, bg=BORDER, height=1, width=320).pack(fill="x", pady=(28, 0))
        tk.Label(card, text="AES-128-CBC  *  ARGON2ID  *  64MB MEMORY HARD",
                 font=("Courier New", 7), bg=BG2, fg="#333333").pack(pady=(6, 0))

    def _submit(self):
        pw = self._pw_entry.get()
        if len(pw) < 8:
            self._status_var.set("ERROR: Password must be at least 8 characters.")
            return
        if not self._vault.vault_exists():
            self._vault.create(pw)
            self._on_success()
        else:
            if self._vault.unlock(pw):
                self._on_success()
            else:
                self._status_var.set("ERROR: Incorrect master password.")
                self._pw_entry.delete(0, "end")


# ── Generator ─────────────────────────────────────────────────────────────────

class GeneratorDialog(tk.Toplevel):
    def __init__(self, master, on_use=None):
        super().__init__(master)
        self._on_use = on_use
        self.title("Generator")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(master)
        self._build()
        self._regenerate()

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, highlightthickness=1, highlightbackground=BORDER_HI)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=FG, height=2).pack(fill="x")
        tk.Label(hdr, text="PASSWORD GENERATOR", font=("Courier New", 12, "bold"),
                 bg=BG2, fg=FG, pady=12).pack()

        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        pw_box = tk.Frame(body, bg=BG3, highlightthickness=1, highlightbackground=BORDER_HI)
        pw_box.pack(fill="x", pady=(0, 8))
        self._pw_var = tk.StringVar()
        tk.Label(pw_box, textvariable=self._pw_var, font=("Courier New", 12, "bold"),
                 bg=BG3, fg=FG, wraplength=360, justify="center",
                 pady=16, padx=16).pack(fill="x")

        self._entropy_lbl = tk.Label(body, text="", font=("Courier New", 8),
                                     bg=BG, fg=FG_DIM)
        self._entropy_lbl.pack()
        self._bar = tk.Canvas(body, height=2, bg=BORDER, highlightthickness=0)
        self._bar.pack(fill="x", pady=(3, 16))

        tk.Label(body, text="LENGTH", font=("Courier New", 8),
                 bg=BG, fg=FG_DIM, anchor="w").pack(fill="x")
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(4, 12))
        self._length_var = tk.IntVar(value=16)
        self._len_lbl = tk.Label(row, text="16", font=("Courier New", 12, "bold"),
                                 bg=BG, fg=FG, width=3)
        self._len_lbl.pack(side="right")
        tk.Scale(row, from_=8, to=64, orient="horizontal",
                 variable=self._length_var, command=self._on_len,
                 bg=BG, fg=FG, troughcolor=BG3, highlightthickness=0,
                 sliderrelief="flat", activebackground=FG, showvalue=False,
                 ).pack(side="left", fill="x", expand=True)

        tk.Label(body, text="CHARACTER SET", font=("Courier New", 8),
                 bg=BG, fg=FG_DIM, anchor="w").pack(fill="x")
        opts = tk.Frame(body, bg=BG)
        opts.pack(fill="x", pady=(4, 16))
        self._upper   = tk.BooleanVar(value=True)
        self._digits  = tk.BooleanVar(value=True)
        self._symbols = tk.BooleanVar(value=True)
        for text, var in [("A-Z", self._upper), ("0-9", self._digits), ("!@#", self._symbols)]:
            tk.Checkbutton(opts, text=text, variable=var, command=self._regenerate,
                           bg=BG, fg=FG, selectcolor=BG3, activebackground=BG,
                           activeforeground=FG, font=("Courier New", 10),
                           cursor="hand2").pack(side="left", padx=(0, 20))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x")
        styled_button(btn_row, "[ REGENERATE ]", self._regenerate).pack(side="left")
        styled_button(btn_row, "[ COPY ]", self._copy, ghost=True).pack(side="left", padx=(8, 0))
        if self._on_use:
            styled_button(btn_row, "[ USE PASSWORD ]", self._use).pack(side="right")

    def _on_len(self, _=None):
        self._len_lbl.config(text=str(self._length_var.get()))
        self._regenerate()

    def _regenerate(self, _=None):
        l = self._length_var.get()
        u, d, s = self._upper.get(), self._digits.get(), self._symbols.get()
        pw = generate_password(l, u, d, s)
        self._pw_var.set(pw)
        self._current_pw = pw
        ps = pool_size(u, d, s)
        entropy = estimate_entropy(l, ps)
        if entropy < 40:
            grade, color, fill = "WEAK",   DANGER,  0.20
        elif entropy < 60:
            grade, color, fill = "FAIR",   "#888844", 0.45
        elif entropy < 80:
            grade, color, fill = "GOOD",   FG_MID,  0.70
        else:
            grade, color, fill = "STRONG", FG,      1.00
        self._entropy_lbl.config(
            text=f"{grade}  *  {entropy:.0f} bits  *  pool {ps} chars", fg=color)
        self._bar.update_idletasks()
        w = self._bar.winfo_width() or 360
        self._bar.delete("all")
        self._bar.create_rectangle(0, 0, w, 2, fill=BORDER, outline="")
        self._bar.create_rectangle(0, 0, int(w * fill), 2, fill=color, outline="")

    def _copy(self):
        copy_to_clipboard(self.winfo_toplevel(), self._current_pw)
        messagebox.showinfo("Copied", "Password copied to clipboard.", parent=self)

    def _use(self):
        if self._on_use:
            self._on_use(self._current_pw)
        self.destroy()


# ── Entry Form ────────────────────────────────────────────────────────────────

class EntryForm(tk.Toplevel):
    def __init__(self, master, vault, on_save, entry=None):
        super().__init__(master)
        self._vault = vault
        self._on_save = on_save
        self._entry = entry
        self.title("Edit" if entry else "New Entry")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(master)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, highlightthickness=1, highlightbackground=BORDER_HI)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=FG, height=2).pack(fill="x")
        tk.Label(hdr, text="EDIT ENTRY" if self._entry else "NEW ENTRY",
                 font=("Courier New", 12, "bold"), bg=BG2, fg=FG, pady=12).pack()

        body = tk.Frame(self, bg=BG, padx=28, pady=16)
        body.pack(fill="both")
        self._vars = {}

        for label_text, key, show in [
            ("SITE / APP",        "site",     ""),
            ("USERNAME / EMAIL",  "username", ""),
            ("PASSWORD",          "password", "*"),
            ("NOTES",             "notes",    ""),
        ]:
            tk.Label(body, text=label_text, font=("Courier New", 8),
                     bg=BG, fg=FG_DIM, anchor="w").pack(fill="x", pady=(8, 2))
            var = tk.StringVar(value=self._entry.get(key, "") if self._entry else "")
            self._vars[key] = var
            e = styled_entry(body, show=show, width=38)
            e.insert(0, var.get())
            e.pack(fill="x", ipady=6)
            e.bind("<KeyRelease>", lambda ev, k=key, w=e: self._vars[k].set(w.get()))

            if key == "password":
                self._pw_widget = e
                self._show_pw = False
                pw_btn_row = tk.Frame(body, bg=BG)
                pw_btn_row.pack(fill="x", pady=(4, 0))
                self._toggle_btn = tk.Button(
                    pw_btn_row, text="SHOW", font=("Courier New", 8),
                    bg=BG, fg=FG_DIM, relief="flat", bd=0,
                    cursor="hand2", activebackground=BG, activeforeground=FG,
                    command=self._toggle_pw)
                self._toggle_btn.pack(side="left")
                styled_button(pw_btn_row, "[ GENERATE ]",
                              self._open_generator, ghost=True, small=True).pack(side="right")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(20, 16))
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x", pady=(0, 4))
        styled_button(btn_row, "[ CANCEL ]", self.destroy, ghost=True).pack(side="right", padx=(8, 0))
        styled_button(btn_row, "[ SAVE ]", self._save).pack(side="right")

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self._pw_widget.config(show="" if self._show_pw else "*")
        self._toggle_btn.config(text="HIDE" if self._show_pw else "SHOW")

    def _open_generator(self):
        def use_pw(pw):
            self._pw_widget.delete(0, "end")
            self._pw_widget.insert(0, pw)
            self._vars["password"].set(pw)
            self._show_pw = True
            self._pw_widget.config(show="")
            self._toggle_btn.config(text="HIDE")
        GeneratorDialog(self, on_use=use_pw)

    def _save(self):
        site  = self._vars["site"].get().strip()
        uname = self._vars["username"].get().strip()
        pw    = self._vars["password"].get()
        notes = self._vars["notes"].get().strip()
        if not site or not pw:
            messagebox.showwarning("Missing", "Site and Password are required.", parent=self)
            return
        if self._entry:
            self._vault.update_entry(self._entry["id"], site, uname, pw, notes)
        else:
            self._vault.add_entry(site, uname, pw, notes)
        self._on_save()
        self.destroy()


# ── Vault Screen ──────────────────────────────────────────────────────────────

class VaultScreen(tk.Frame):
    def __init__(self, master, vault, on_lock):
        super().__init__(master, bg=BG)
        self._vault = vault
        self._on_lock = on_lock
        self._build()
        self._refresh()

    def _build(self):
        self.pack(fill="both", expand=True)

        top = tk.Frame(self, bg=BG2, highlightthickness=1, highlightbackground=BORDER)
        top.pack(fill="x", side="top")
        tk.Frame(top, bg=FG, height=2).pack(fill="x", side="top")

        inner_top = tk.Frame(top, bg=BG2, pady=10)
        inner_top.pack(fill="x")
        tk.Label(inner_top, text="PASSVAULT", font=("Courier New", 14, "bold"),
                 bg=BG2, fg=FG).pack(side="left", padx=16)
        styled_button(inner_top, "[ + ADD ]",  self._open_add).pack(side="right", padx=(0, 12))
        styled_button(inner_top, "GENERATOR",  self._open_generator, ghost=True).pack(side="right", padx=(0, 6))
        styled_button(inner_top, "LOCK",       self._lock, danger=True).pack(side="right", padx=(0, 6))

        search_frame = tk.Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        search_frame.pack(fill="x")
        search_inner = tk.Frame(search_frame, bg=BG, padx=16, pady=8)
        search_inner.pack(fill="x")
        tk.Label(search_inner, text="SEARCH", font=("Courier New", 8),
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 10))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh())
        search_entry = styled_entry(search_inner, width=50)
        search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        search_entry.bind("<KeyRelease>",
                          lambda _: self._search_var.set(search_entry.get()))
        self._count_var = tk.StringVar()
        tk.Label(search_inner, textvariable=self._count_var,
                 font=("Courier New", 8), bg=BG, fg=FG_DIM).pack(side="right", padx=(12, 0))

        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=16, pady=12)
        self._canvas     = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        scrollbar        = ttk.Scrollbar(list_frame, orient="vertical",
                                         command=self._canvas.yview)
        self._scrollable = tk.Frame(self._canvas, bg=BG)
        self._scrollable.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._scrollable, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def _refresh(self):
        query   = self._search_var.get()
        entries = self._vault.search(query)
        for w in self._scrollable.winfo_children():
            w.destroy()
        if not entries:
            msg = "NO ENTRIES FOUND." if self._vault.all_entries() \
                  else "VAULT EMPTY  --  PRESS [ + ADD ] TO BEGIN."
            tk.Label(self._scrollable, text=msg, font=("Courier New", 10),
                     bg=BG, fg=FG_DIM).pack(pady=48)
            self._count_var.set("")
            return
        n = len(entries)
        self._count_var.set(f"{n} RECORD{'S' if n != 1 else ''}")
        for entry in entries:
            self._build_row(entry)

    def _build_row(self, entry):
        outer = tk.Frame(self._scrollable, bg=BG)
        outer.pack(fill="x", pady=(0, 6))

        accent_bar = tk.Frame(outer, bg=BORDER, width=2)
        accent_bar.pack(side="left", fill="y")

        row = tk.Frame(outer, bg=BG2, pady=10, padx=14,
                       highlightthickness=1, highlightbackground=BORDER)
        row.pack(side="left", fill="x", expand=True)

        def on_enter(_):
            row.config(highlightbackground=FG_DIM)
            accent_bar.config(bg=FG)
        def on_leave(_):
            row.config(highlightbackground=BORDER)
            accent_bar.config(bg=BORDER)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        left = tk.Frame(row, bg=BG2)
        left.pack(side="left", fill="both", expand=True)

        badge_letter = (entry["site"][0].upper() if entry["site"] else "?")
        badge = tk.Frame(left, bg=BG, width=38, height=38,
                         highlightthickness=1, highlightbackground=FG_DIM)
        badge.pack(side="left", padx=(0, 14))
        badge.pack_propagate(False)
        tk.Label(badge, text=badge_letter, font=("Courier New", 14, "bold"),
                 bg=BG, fg=FG).place(relx=0.5, rely=0.5, anchor="center")

        text_col = tk.Frame(left, bg=BG2)
        text_col.pack(side="left", fill="both")
        tk.Label(text_col, text=entry["site"], font=("Courier New", 12, "bold"),
                 bg=BG2, fg=FG, anchor="w").pack(fill="x")
        uname_text = entry["username"] if entry["username"] else "no username"
        tk.Label(text_col, text=uname_text, font=("Courier New", 9),
                 bg=BG2, fg=FG_DIM, anchor="w").pack(fill="x")
        masked = "*" * min(len(entry["password"]), 18)
        tk.Label(text_col, text=masked, font=("Courier New", 9),
                 bg=BG2, fg="#333333", anchor="w").pack(fill="x")

        btn_col = tk.Frame(row, bg=BG2)
        btn_col.pack(side="right")
        styled_button(btn_col, "COPY",
                      lambda e=entry: self._copy_pw(e), ghost=True, small=True).pack(pady=2, fill="x")
        styled_button(btn_col, "EDIT",
                      lambda e=entry: self._open_edit(e), ghost=True, small=True).pack(pady=2, fill="x")
        styled_button(btn_col, "DEL",
                      lambda e=entry: self._delete(e), danger=True, small=True).pack(pady=2, fill="x")
        styled_button(btn_col, "BREACH",
                      lambda e=entry: self._check_breach(e), ghost=True, small=True).pack(pady=2, fill="x")

    def _copy_pw(self, entry):
        copy_to_clipboard(self.winfo_toplevel(), entry["password"])
        messagebox.showinfo("Copied",
                            f"Password for '{entry['site']}' copied to clipboard.",
                            parent=self)

    def _open_add(self):       EntryForm(self.winfo_toplevel(), self._vault, self._refresh)
    def _open_generator(self): GeneratorDialog(self.winfo_toplevel())
    def _open_edit(self, e):   EntryForm(self.winfo_toplevel(), self._vault, self._refresh, entry=e)

    def _delete(self, entry):
        if messagebox.askyesno("Confirm", f"Delete '{entry['site']}'?",
                               icon="warning", parent=self):
            self._vault.delete_entry(entry["id"])
            self._refresh()


    def _check_breach(self, entry: dict):
        """Check a password against HaveIBeenPwned using k-anonymity."""
        import threading
        def run():
            try:
                found, count = check_breach(entry["password"])
                msg, severity = breach_summary(found, count)
                color = {"safe": "#44aa66", "warning": "#cc8833", "danger": "#cc3333"}[severity]
                icon  = "✓" if not found else "⚠"
                self.after(0, lambda: self._show_breach_result(
                    entry["site"], msg, color, icon))
            except ConnectionError as e:
                self.after(0, lambda: messagebox.showerror(
                    "Network Error",
                    f"Could not reach HaveIBeenPwned:\n{e}\n\nCheck your internet connection.",
                    parent=self))
        threading.Thread(target=run, daemon=True).start()
        self._status_message("Checking breach database...")

    def _show_breach_result(self, site: str, msg: str, color: str, icon: str):
        """Show breach check result as a popup."""
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Breach Check")
        win.configure(bg="#080808")
        win.resizable(False, False)
        win.grab_set()
        win.transient(self.winfo_toplevel())

        tk.Frame(win, bg=color, height=3).pack(fill="x")
        tk.Label(win, text=icon, font=("Courier New", 36),
                 bg="#080808", fg=color, pady=10).pack()
        tk.Label(win, text=f"BREACH CHECK  —  {site.upper()}",
                 font=("Courier New", 10, "bold"),
                 bg="#080808", fg="#ffffff").pack()
        tk.Label(win, text=msg, font=("Courier New", 9),
                 bg="#080808", fg="#aaaaaa",
                 wraplength=300, pady=12, padx=20).pack()
        tk.Label(win,
                 text="Checked via HaveIBeenPwned k-anonymity API.\nYour password was never transmitted.",
                 font=("Courier New", 7), bg="#080808", fg="#444444").pack(pady=(0, 6))
        tk.Frame(win, bg="#2a2a2a", height=1).pack(fill="x")
        styled_button(win, "[ CLOSE ]", win.destroy).pack(pady=12)

    def _status_message(self, msg: str):
        """Briefly flash a status message in the count label."""
        self._count_var.set(msg)
        self.after(3000, lambda: self._count_var.set(""))

    def _lock(self):
        self._vault.lock()
        self._on_lock()


# ── App ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PassVault")
        self.geometry("800x580")
        self.minsize(660, 460)
        self.configure(bg=BG)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Vertical.TScrollbar",
                        background=BG3, troughcolor=BG2,
                        arrowcolor=BORDER, bordercolor=BORDER, relief="flat")
        self._vault = Vault()
        self._current_frame = None
        self._show_login()

    def _clear(self):
        if self._current_frame:
            self._current_frame.destroy()
            self._current_frame = None

    def _show_login(self):
        self._clear()
        self._current_frame = LoginScreen(self, self._vault, self._show_vault)

    def _show_vault(self):
        self._clear()
        self._current_frame = VaultScreen(self, self._vault, self._show_login)


def run():
    App().mainloop()
