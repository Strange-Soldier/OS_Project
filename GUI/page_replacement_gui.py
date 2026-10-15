# page_replacement_gui.py
# Virtual Paging screen (Page Replacement).
# This file ONLY builds the window and calls simulate() from fifo/lru/opt.
# There is NO page-replacement math here.

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# make the Page_Replacement folder importable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "Page_Replacement"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fifo, lru, opt
import theme

ALGO_MODULE = {"FIFO": fifo, "LRU": lru, "OPT": opt}


class PageReplacementFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)

        self.result = None
        self.frame_size = 3
        self.cell_labels = []     # grid of Label widgets for the frames table

        self._build_ui()

    # =====================================================================
    # Build the screen
    # =====================================================================
    def _build_ui(self):
        tk.Label(self, text="Page Replacement", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_TITLE).pack(anchor="w", padx=20, pady=(12, 6))

        # the whole screen is the paging view (Cache has its own tab now)
        page = tk.Frame(self, bg=theme.APP_BG)
        page.pack(fill="both", expand=True, padx=16, pady=4)
        self._build_paging(page)

    def _build_paging(self, tab):
        # ---- left controls ----
        middle = tk.Frame(tab, bg=theme.APP_BG)
        middle.pack(fill="both", expand=True)

        left = tk.Frame(middle, bg=theme.APP_BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        card, body = theme.section_card(left, "Inputs", theme.HEADER_BLUE)
        card.pack(fill="x")

        tk.Label(body, text="Reference String :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.ref_var = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3")
        ref_entry = ttk.Entry(body, textvariable=self.ref_var, width=28)
        ref_entry.pack(fill="x", pady=(0, 8))
        self.ref_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Frames :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.frames_var = tk.StringVar(value="3")
        self.frames_spin = ttk.Spinbox(body, from_=1, to=10, width=6,
                                       textvariable=self.frames_var)
        self.frames_spin.pack(anchor="w", pady=(0, 8))
        self.frames_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Algorithm :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.algo_var = tk.StringVar(value="FIFO")
        algo_box = ttk.Combobox(body, textvariable=self.algo_var,
                                values=["FIFO", "LRU", "OPT"],
                                state="readonly", width=12)
        algo_box.pack(anchor="w", pady=(0, 10))
        algo_box.bind("<<ComboboxSelected>>", lambda e: self._invalidate())

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x")
        ttk.Button(btns, text="▶ Simulate", style="Green.TButton",
                   command=self._run).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="↺ Reset", command=self._reset).pack(
            side="left", expand=True, fill="x", padx=2)

        # ---- right panels ----
        right = tk.Frame(middle, bg=theme.APP_BG)
        right.pack(side="left", fill="both", expand=True)

        # Frames table (built as a grid of colored labels for full control)
        card, body = theme.section_card(right, "Frames (Memory State)",
                                        theme.HEADER_YELLOW)
        card.pack(fill="x")
        # horizontal scroll area for the grid (many references = many columns)
        self.grid_canvas = tk.Canvas(body, bg=theme.CARD_BG, height=170,
                                     highlightthickness=0)
        hbar = ttk.Scrollbar(body, orient="horizontal", command=self.grid_canvas.xview)
        self.grid_canvas.configure(xscrollcommand=hbar.set)
        self.grid_canvas.pack(fill="x")
        hbar.pack(fill="x")
        self.grid_inner = tk.Frame(self.grid_canvas, bg=theme.CARD_BG)
        self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_inner.bind("<Configure>", lambda e: self.grid_canvas.configure(
            scrollregion=self.grid_canvas.bbox("all")))

        lower = tk.Frame(right, bg=theme.APP_BG)
        lower.pack(fill="both", expand=True, pady=(10, 0))

        # Event log
        card, body = theme.section_card(lower, "Event Log", theme.HEADER_GREEN)
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.log = tk.Text(body, height=8, width=40, font=theme.FONT_MONO,
                           bd=0, highlightthickness=0)
        self.log.pack(side="left", fill="both", expand=True)
        logbar = ttk.Scrollbar(body, command=self.log.yview)
        logbar.pack(side="left", fill="y")
        self.log.config(yscrollcommand=logbar.set, state="disabled")

        # Statistics
        card, body = theme.section_card(lower, "Statistics", theme.HEADER_PURPLE)
        card.pack(side="left", fill="y", padx=(6, 0))
        self.stat_vars = {}
        for name in ["Page hits", "Page faults", "Hit ratio", "Miss ratio"]:
            row = tk.Frame(body, bg=theme.CARD_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=name + " :", bg=theme.CARD_BG, fg=theme.TEXT,
                     font=theme.FONT_NORMAL, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value="-")
            self.stat_vars[name] = var
            tk.Label(row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

        # ---- playback bar ----
        self.playback = theme.PlaybackBar(tab, on_render=self._render_snapshot,
                                          make_label=self._snapshot_label)
        self.playback.pack(fill="x", pady=10)

    # =====================================================================
    # Run + playback
    # =====================================================================
    def _invalidate(self):
        self.result = None
        if hasattr(self, "playback"):
            self.playback.disable()

    def _reset(self):
        self.ref_var.set("7 0 1 2 0 3 0 4 2 3")
        self.frames_var.set("3")
        self.algo_var.set("FIFO")
        self._clear_outputs()
        self._invalidate()

    def _clear_outputs(self):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.cell_labels = []
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        for v in self.stat_vars.values():
            v.set("-")

    def _run(self):
        # read reference string
        try:
            pages = [int(x) for x in self.ref_var.get().split()]
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Reference string must be whole numbers separated by spaces.")
            return
        if not pages:
            messagebox.showinfo("No pages", "Enter a reference string first.")
            return
        if any(p < 0 for p in pages):
            messagebox.showerror("Invalid input",
                                 "Page numbers cannot be negative.")
            return

        try:
            self.frame_size = int(self.frames_var.get())
        except ValueError:
            self.frame_size = 3
        if self.frame_size < 1:
            messagebox.showerror("Invalid input",
                                 "Frames must be a whole number >= 1.")
            return

        module = ALGO_MODULE[self.algo_var.get()]

        # RUN THE ALGORITHM ONCE -- builds the whole snapshot list
        self.result = module.simulate(pages, self.frame_size)

        # build the (empty) frames grid once, then fill it while scrubbing
        self._build_grid(pages)

        # statistics (miss ratio is just the rest of 100%)
        self.stat_vars["Page hits"].set(self.result["hits"])
        self.stat_vars["Page faults"].set(self.result["faults"])
        self.stat_vars["Hit ratio"].set("%s %%" % self.result["hit_ratio"])
        self.stat_vars["Miss ratio"].set("%s %%" % round(100 - self.result["hit_ratio"], 2))

        # enable playback with the finished snapshot list
        self.playback.load(self.result["snapshots"])

    # build the grid of labels: Ref row, F1..Fn rows, Result row
    def _build_grid(self, pages):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.cell_labels = []

        n = len(pages)
        row_names = ["Ref →"] + ["F%d" % (i + 1) for i in range(self.frame_size)] + ["Result"]

        # left header column
        for r, name in enumerate(row_names):
            tk.Label(self.grid_inner, text=name, bg=theme.HEADER_BLUE, fg=theme.TEXT,
                     font=("Segoe UI", 9, "bold"), width=8, height=1,
                     relief="solid", bd=1).grid(row=r, column=0, sticky="nsew")

        # one empty column per reference; remember the labels so we can fill them
        for col in range(n):
            col_labels = []
            for r in range(len(row_names)):
                lbl = tk.Label(self.grid_inner, text="", bg="white", fg=theme.TEXT,
                               font=theme.FONT_NORMAL, width=4, height=1,
                               relief="solid", bd=1)
                lbl.grid(row=r, column=col + 1, sticky="nsew")
                col_labels.append(lbl)
            self.cell_labels.append(col_labels)

    def _snapshot_label(self, snap):
        word = "HIT" if snap["result"] == "H" else "FAULT"
        return "t=%d : %s : page %d" % (snap["t"], word, snap["ref"])

    # fill the grid columns up to the current index; rebuild the event log
    def _render_snapshot(self, index, snap):
        snaps = self.result["snapshots"]

        for col, col_labels in enumerate(self.cell_labels):
            if col <= index:
                s = snaps[col]
                # Ref row
                col_labels[0].config(text=str(s["ref"]), bg=theme.HEADER_BLUE)
                # frame rows
                for i in range(self.frame_size):
                    val = s["frames"][i]
                    col_labels[1 + i].config(text="" if val is None else str(val),
                                             bg="white")
                # result row (green = hit, red = fault)
                if s["result"] == "H":
                    col_labels[-1].config(text="H", bg=theme.HIT_GREEN)
                else:
                    col_labels[-1].config(text="F", bg=theme.FAULT_RED)
                # faintly highlight the current column
                mark = "#fff6cc" if col == index else "white"
                col_labels[0].config(bg=theme.HEADER_BLUE)
                for i in range(self.frame_size):
                    if col_labels[1 + i].cget("text") != "":
                        col_labels[1 + i].config(bg=mark)
            else:
                # not reached yet -> keep these columns blank
                for lbl in col_labels:
                    lbl.config(text="", bg="white")

        # event log up to current index
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        for t in range(index + 1):
            s = snaps[t]
            word = "HIT  " if s["result"] == "H" else "FAULT"
            self.log.insert("end", "t = %-2d : %s (page %d)\n" % (s["t"], word, s["ref"]))
        self.log.see("end")
        self.log.config(state="disabled")


# run this screen on its own
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Process Visualization - Virtual Paging")
    root.geometry("1150x780")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    PageReplacementFrame(root).pack(fill="both", expand=True)
    root.mainloop()
