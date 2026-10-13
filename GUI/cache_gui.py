# cache_gui.py
# Cache Memory screen.
# Only builds the window and calls simulate() from the cache algorithm files.

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "Cache_Memory"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import direct_mapping, fully_associative, set_associative
import theme


class CacheFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)
        self.result = None
        self.num_lines = 4
        self.cells = []          # grid of labels for the cache table
        self._build_ui()
        self._on_algo_change()

    # =====================================================================
    # Build the screen
    # =====================================================================
    def _build_ui(self):
        tk.Label(self, text="Cache Memory", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_TITLE).pack(anchor="w", padx=20, pady=(12, 6))

        middle = tk.Frame(self, bg=theme.APP_BG)
        middle.pack(fill="both", expand=True, padx=16)

        left = tk.Frame(middle, bg=theme.APP_BG)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = tk.Frame(middle, bg=theme.APP_BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)

        self.playback = theme.PlaybackBar(self, on_render=self._render_snapshot,
                                          make_label=self._snapshot_label)
        self.playback.pack(fill="x", padx=16, pady=10)

    def _build_left(self, left):
        card, body = theme.section_card(left, "Inputs", theme.HEADER_BLUE)
        card.pack(fill="x")

        tk.Label(body, text="Block Reference String :", bg=theme.CARD_BG,
                 fg=theme.TEXT, font=theme.FONT_NORMAL).pack(anchor="w")
        self.ref_var = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3")
        ttk.Entry(body, textvariable=self.ref_var, width=28).pack(fill="x", pady=(0, 8))
        self.ref_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Cache Lines :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.lines_var = tk.StringVar(value="4")
        ttk.Spinbox(body, from_=1, to=16, width=6,
                    textvariable=self.lines_var).pack(anchor="w", pady=(0, 8))
        self.lines_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Mapping :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.algo_var = tk.StringVar(value="Direct")
        box = ttk.Combobox(body, textvariable=self.algo_var,
                           values=["Direct", "Fully Associative", "Set Associative"],
                           state="readonly", width=18)
        box.pack(anchor="w", pady=(0, 8))
        box.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

        # ways is only needed for set associative
        self.ways_label = tk.Label(body, text="Lines per Set :", bg=theme.CARD_BG,
                                   fg=theme.TEXT, font=theme.FONT_NORMAL)
        self.ways_label.pack(anchor="w")
        self.ways_var = tk.StringVar(value="2")
        self.ways_spin = ttk.Spinbox(body, from_=1, to=8, width=6,
                                     textvariable=self.ways_var)
        self.ways_spin.pack(anchor="w", pady=(0, 10))
        self.ways_var.trace_add("write", lambda *a: self._invalidate())

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x")
        ttk.Button(btns, text="▶ Simulate", style="Green.TButton",
                   command=self._run).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="↺ Reset",
                   command=self._reset).pack(side="left", expand=True, fill="x", padx=2)

        # statistics
        card, body = theme.section_card(left, "Statistics", theme.HEADER_PURPLE)
        card.pack(fill="x", pady=(10, 0))
        self.stats = {}
        for name in ["Hits", "Misses", "Hit ratio", "Miss ratio"]:
            row = tk.Frame(body, bg=theme.CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name + " :", bg=theme.CARD_BG, fg=theme.TEXT,
                     font=theme.FONT_NORMAL, width=11, anchor="w").pack(side="left")
            var = tk.StringVar(value="-")
            self.stats[name] = var
            tk.Label(row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

    def _build_right(self, right):
        # cache table: one column per reference
        card, body = theme.section_card(right, "Cache State", theme.HEADER_YELLOW)
        card.pack(fill="x")
        self.grid_canvas = tk.Canvas(body, bg=theme.CARD_BG, height=190,
                                     highlightthickness=0)
        hbar = ttk.Scrollbar(body, orient="horizontal", command=self.grid_canvas.xview)
        self.grid_canvas.configure(xscrollcommand=hbar.set)
        self.grid_canvas.pack(fill="x")
        hbar.pack(fill="x")
        self.grid_inner = tk.Frame(self.grid_canvas, bg=theme.CARD_BG)
        self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_inner.bind("<Configure>", lambda e: self.grid_canvas.configure(
            scrollregion=self.grid_canvas.bbox("all")))

        # event log
        card, body = theme.section_card(right, "Event Log", theme.HEADER_GREEN)
        card.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(body, height=8, font=theme.FONT_MONO,
                           bd=0, highlightthickness=0, state="disabled")
        self.log.pack(fill="both", expand=True)

    # =====================================================================
    # Run and playback
    # =====================================================================
    # the "lines per set" box only matters for set associative mapping
    def _on_algo_change(self):
        if self.algo_var.get() == "Set Associative":
            self.ways_spin.config(state="normal")
            self.ways_label.config(fg=theme.TEXT)
        else:
            self.ways_spin.config(state="disabled")
            self.ways_label.config(fg=theme.MUTED)
        self._invalidate()

    def _invalidate(self):
        self.result = None
        if hasattr(self, "playback"):
            self.playback.disable()

    def _reset(self):
        self.ref_var.set("7 0 1 2 0 3 0 4 2 3")
        self.lines_var.set("4")
        self.ways_var.set("2")
        self.algo_var.set("Direct")
        self._clear()
        self._on_algo_change()

    def _clear(self):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.cells = []
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        for v in self.stats.values():
            v.set("-")

    def _run(self):
        try:
            blocks = [int(x) for x in self.ref_var.get().split()]
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Reference string must be whole numbers separated by spaces.")
            return
        if not blocks:
            messagebox.showinfo("No input", "Enter a block reference string.")
            return

        try:
            self.num_lines = max(1, int(self.lines_var.get()))
        except ValueError:
            self.num_lines = 4

        algo = self.algo_var.get()
        if algo == "Direct":
            self.result = direct_mapping.simulate(blocks, self.num_lines)
        elif algo == "Fully Associative":
            self.result = fully_associative.simulate(blocks, self.num_lines)
        else:
            try:
                ways = max(1, int(self.ways_var.get()))
            except ValueError:
                ways = 2
            if ways > self.num_lines:
                messagebox.showerror("Invalid input",
                                     "Lines per set cannot be more than total cache lines.")
                return
            self.result = set_associative.simulate(blocks, self.num_lines, ways)

        self.stats["Hits"].set(self.result["hits"])
        self.stats["Misses"].set(self.result["misses"])
        self.stats["Hit ratio"].set("%s %%" % self.result["hit_ratio"])
        self.stats["Miss ratio"].set("%s %%" % self.result["miss_ratio"])

        self._build_grid(blocks)
        self.playback.load(self.result["snapshots"])

    # build the empty table: Block row, one row per line, Result row
    def _build_grid(self, blocks):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.cells = []

        names = ["Block →"] + self._line_names() + ["Result"]

        for r, name in enumerate(names):
            tk.Label(self.grid_inner, text=name, bg=theme.HEADER_BLUE, fg=theme.TEXT,
                     font=("Segoe UI", 9, "bold"), width=10, relief="solid",
                     bd=1).grid(row=r, column=0, sticky="nsew")

        for col in range(len(blocks)):
            column = []
            for r in range(len(names)):
                lbl = tk.Label(self.grid_inner, text="", bg="white", fg=theme.TEXT,
                               font=theme.FONT_NORMAL, width=4, relief="solid", bd=1)
                lbl.grid(row=r, column=col + 1, sticky="nsew")
                column.append(lbl)
            self.cells.append(column)

    # row names: L0, L1... or for set associative S0-W0, S0-W1...
    def _line_names(self):
        if self.algo_var.get() == "Set Associative":
            names = []
            for s in range(self.result["num_sets"]):
                for w in range(self.result["ways"]):
                    names.append("S%d-W%d" % (s, w))
            return names
        return ["L%d" % i for i in range(self.num_lines)]

    # flatten a snapshot's cache into one list, one value per row
    def _cache_list(self, snap):
        if self.algo_var.get() == "Set Associative":
            flat = []
            for one_set in snap["cache"]:
                flat += one_set
            return flat
        return snap["cache"]

    def _snapshot_label(self, snap):
        word = "HIT" if snap["result"] == "H" else "MISS"
        return "t=%d : %s : block %d" % (snap["t"], word, snap["block"])

    # fill the table columns up to now (only a lookup, never a re-run)
    def _render_snapshot(self, index, snap):
        snaps = self.result["snapshots"]

        for col, column in enumerate(self.cells):
            if col <= index:
                s = snaps[col]
                column[0].config(text=str(s["block"]), bg=theme.HEADER_BLUE)
                values = self._cache_list(s)
                for i in range(len(column) - 2):
                    v = values[i] if i < len(values) else None
                    column[1 + i].config(text="" if v is None else str(v), bg="white")
                if s["result"] == "H":
                    column[-1].config(text="H", bg=theme.HIT_GREEN)
                else:
                    column[-1].config(text="M", bg=theme.FAULT_RED)
            else:
                for lbl in column:
                    lbl.config(text="", bg="white")

        # event log up to now
        text = ""
        for i in range(index + 1):
            s = snaps[i]
            word = "HIT " if s["result"] == "H" else "MISS"
            if "set" in s:
                text += "t = %-2d : %s (block %d -> set %d)\n" % (s["t"], word, s["block"], s["set"])
            else:
                text += "t = %-2d : %s (block %d -> line %d)\n" % (s["t"], word, s["block"], s["line"])
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cache Memory")
    root.geometry("1150x760")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    CacheFrame(root).pack(fill="both", expand=True)
    root.mainloop()
