# memory_gui.py
# Memory Management screen.
# Only builds the window and calls simulate() from the memory algorithm files.

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "Memory_Management"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import first_fit, best_fit, worst_fit, next_fit
import theme

ALGOS = {"First Fit": first_fit, "Best Fit": best_fit,
         "Worst Fit": worst_fit, "Next Fit": next_fit}

USED_COLOR = "#8fd19e"      # part of a block that is taken
FREE_COLOR = "#e4ebf3"      # part of a block that is still free


class MemoryFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)
        self.result = None
        self._build_ui()

    # =====================================================================
    # Build the screen
    # =====================================================================
    def _build_ui(self):
        tk.Label(self, text="Memory Management", bg=theme.APP_BG, fg=theme.TEXT,
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

        tk.Label(body, text="Block Sizes :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.blocks_var = tk.StringVar(value="100 500 200 300 600")
        ttk.Entry(body, textvariable=self.blocks_var, width=28).pack(fill="x", pady=(0, 8))
        self.blocks_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Process Sizes :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.sizes_var = tk.StringVar(value="212 417 112 426")
        ttk.Entry(body, textvariable=self.sizes_var, width=28).pack(fill="x", pady=(0, 8))
        self.sizes_var.trace_add("write", lambda *a: self._invalidate())

        tk.Label(body, text="Algorithm :", bg=theme.CARD_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(anchor="w")
        self.algo_var = tk.StringVar(value="First Fit")
        box = ttk.Combobox(body, textvariable=self.algo_var,
                           values=list(ALGOS.keys()), state="readonly", width=14)
        box.pack(anchor="w", pady=(0, 10))
        box.bind("<<ComboboxSelected>>", lambda e: self._invalidate())

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x")
        ttk.Button(btns, text="▶ Allocate", style="Green.TButton",
                   command=self._run).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="↺ Reset",
                   command=self._reset).pack(side="left", expand=True, fill="x", padx=2)

        # statistics
        card, body = theme.section_card(left, "Statistics", theme.HEADER_PURPLE)
        card.pack(fill="x", pady=(10, 0))
        self.stats = {}
        for name in ["Allocated", "Not allocated", "Free memory", "Total memory"]:
            row = tk.Frame(body, bg=theme.CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name + " :", bg=theme.CARD_BG, fg=theme.TEXT,
                     font=theme.FONT_NORMAL, width=14, anchor="w").pack(side="left")
            var = tk.StringVar(value="-")
            self.stats[name] = var
            tk.Label(row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

    def _build_right(self, right):
        # picture of the memory blocks
        card, body = theme.section_card(right, "Memory Blocks", theme.HEADER_YELLOW)
        card.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, bg="white", height=220, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        lower = tk.Frame(right, bg=theme.APP_BG)
        lower.pack(fill="both", expand=True, pady=(10, 0))

        # which process went where
        card, body = theme.section_card(lower, "Allocation Table", theme.HEADER_GREEN)
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        cols = ("PID", "Size", "Block", "Result")
        self.table = ttk.Treeview(body, columns=cols, show="headings", height=6)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=90, anchor="center")
        self.table.pack(fill="both", expand=True)

        # log of what happened
        card, body = theme.section_card(lower, "Event Log", theme.HEADER_BLUE)
        card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.log = tk.Text(body, height=6, width=34, font=theme.FONT_MONO,
                           bd=0, highlightthickness=0, state="disabled")
        self.log.pack(fill="both", expand=True)

    # =====================================================================
    # Run and playback
    # =====================================================================
    def _invalidate(self):
        self.result = None
        if hasattr(self, "playback"):
            self.playback.disable()

    def _reset(self):
        self.blocks_var.set("100 500 200 300 600")
        self.sizes_var.set("212 417 112 426")
        self.algo_var.set("First Fit")
        self.canvas.delete("all")
        self.table.delete(*self.table.get_children())
        self._set_log("")
        for v in self.stats.values():
            v.set("-")
        self._invalidate()

    def _run(self):
        try:
            blocks = [int(x) for x in self.blocks_var.get().split()]
            sizes = [int(x) for x in self.sizes_var.get().split()]
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Sizes must be whole numbers separated by spaces.")
            return
        if not blocks or not sizes:
            messagebox.showinfo("Missing input", "Enter block sizes and process sizes.")
            return

        procs = [{"pid": "P%d" % (i + 1), "size": s} for i, s in enumerate(sizes)]

        # run the algorithm once; this builds the whole snapshot list
        self.result = ALGOS[self.algo_var.get()].simulate(blocks, procs)

        self.stats["Allocated"].set(self.result["allocated"])
        self.stats["Not allocated"].set(self.result["failed"])
        self.stats["Free memory"].set(self.result["free_left"])
        self.stats["Total memory"].set(self.result["total"])

        self.playback.load(self.result["snapshots"])

    def _snapshot_label(self, snap):
        if snap["block"] is None:
            return "t=%d : NOT ALLOCATED : %s (%d)" % (snap["t"], snap["pid"], snap["size"])
        return "t=%d : ALLOCATED : %s (%d) -> Block %d" % (
            snap["t"], snap["pid"], snap["size"], snap["block"] + 1)

    def _set_log(self, text):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", text)
        self.log.config(state="disabled")

    # show the state after step "index" (only a lookup, never a re-run)
    def _render_snapshot(self, index, snap):
        snaps = self.result["snapshots"]

        # allocation table up to now
        self.table.delete(*self.table.get_children())
        lines = ""
        for i in range(index + 1):
            s = snaps[i]
            where = "Block %d" % (s["block"] + 1) if s["block"] is not None else "-"
            self.table.insert("", "end",
                              values=(s["pid"], s["size"], where,
                                      "Allocated" if s["result"] == "OK" else "Failed"))
            lines += "t = %-2d : %-3s (%d) -> %s\n" % (s["t"], s["pid"], s["size"], where)
        self._set_log(lines)

        self._draw_blocks(snap)

    # draw one bar per memory block, green part = used, grey part = free
    def _draw_blocks(self, snap):
        c = self.canvas
        c.delete("all")

        blocks = self.result["blocks"]
        biggest = max(blocks)

        width = int(c.winfo_width()) - 120
        if width < 100:
            width = 600                   # before the canvas knows its size

        y = 20
        height = 26
        for i in range(len(blocks)):
            size = blocks[i]
            free = snap["free"][i]
            used = size - free
            full_w = width * size / float(biggest)
            used_w = full_w * used / float(size) if size else 0

            # block name on the left
            c.create_text(10, y + height / 2, anchor="w", text="Block %d" % (i + 1),
                          font=("Segoe UI", 9, "bold"))
            # whole block (free part)
            c.create_rectangle(70, y, 70 + full_w, y + height,
                               fill=FREE_COLOR, outline="#44607e")
            # used part on top
            if used > 0:
                c.create_rectangle(70, y, 70 + used_w, y + height,
                                   fill=USED_COLOR, outline="#44607e")
                c.create_text(70 + used_w / 2, y + height / 2,
                              text=str(snap["taken"][i]), font=("Segoe UI", 9, "bold"))
            # sizes on the right
            c.create_text(80 + full_w, y + height / 2, anchor="w",
                          text="%d / %d free" % (free, size), font=("Segoe UI", 8))
            y += height + 10


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Memory Management")
    root.geometry("1150x760")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    MemoryFrame(root).pack(fill="both", expand=True)
    root.mainloop()
