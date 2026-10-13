import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "CPU_Scheduling"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fcfs, sjf, srtf, rr
import fcfs_WIO, sjf_WIO, srtf_wIO, rr_wIO
import theme

# the algorithms, in table order, with their plain and _WIO modules
ALGO_ROWS = [
    ("FCFS", fcfs, fcfs_WIO, None),
    ("SJF",  sjf,  sjf_WIO,  None),
    ("SRTF", srtf, srtf_wIO, None),
    ("RR",   rr,   rr_wIO,   2),       # RR needs a time quantum
]

class ComparisonFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Process Scheduling - Comparison", bg=theme.APP_BG,
                 fg=theme.TEXT, font=theme.FONT_TITLE).pack(anchor="w",
                                                            padx=20, pady=(12, 6))

        middle = tk.Frame(self, bg=theme.APP_BG)
        middle.pack(fill="both", expand=True, padx=16, pady=4)

        # ---- left: process input ----
        left = tk.Frame(middle, bg=theme.APP_BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        card, body = theme.section_card(left, "Processes", theme.HEADER_BLUE)
        card.pack(fill="x")

        cols = ("PID", "AT", "BT", "IOat", "IOdur")
        holder = tk.Frame(body, bg=theme.CARD_BG)
        holder.pack(fill="x")
        self.tree = ttk.Treeview(holder, columns=cols, show="headings", height=7)
        bar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(side="left", fill="x", expand=True)
        bar.pack(side="left", fill="y")

        headings = {"PID": "PID", "AT": "AT", "BT": "BT",
                    "IOat": "I/O at", "IOdur": "I/O dur"}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=72, anchor="center")
        theme.attach_cell_editor(self.tree, cols, on_change=self._sort_rows)

        for row in [("P1", 0, 5, 2, 2), ("P2", 1, 3, 1, 2), ("P3", 2, 4, 2, 1)]:
            self.tree.insert("", "end", values=row)

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="+ Add Process", style="Green.TButton",
                   command=self._add_process).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="- Remove Process", style="Red.TButton",
                   command=self._remove_process).pack(side="left", expand=True, fill="x", padx=2)

        # I/O toggle + Compare button
        opt = tk.Frame(left, bg=theme.APP_BG)
        opt.pack(fill="x", pady=8)
        tk.Label(opt, text="I/O Mode :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).pack(side="left")
        self.mode_var = tk.StringVar(value="Without I/O")
        mode_box = ttk.Combobox(opt, textvariable=self.mode_var,
                                values=["Without I/O", "With I/O"],
                                state="readonly", width=14)
        mode_box.pack(side="left", padx=6)
        mode_box.bind("<<ComboboxSelected>>", lambda e: self._on_mode_change())

        ttk.Button(left, text="▶  Compare", style="Green.TButton",
                   command=self._compare).pack(fill="x")

        # ---- right: one big metrics table ----
        right = tk.Frame(middle, bg=theme.APP_BG)
        right.pack(side="left", fill="both", expand=True)

        card, body = theme.section_card(right, "All Metrics Table", theme.HEADER_PURPLE)
        card.pack(fill="both", expand=True)

        rcols = ("Algorithm", "AvgWT", "AvgTAT", "AvgRT", "AvgCT")
        titles = {"Algorithm": "Algorithm", "AvgWT": "Avg Waiting Time",
                  "AvgTAT": "Avg Turnaround Time", "AvgRT": "Avg Response Time",
                  "AvgCT": "Avg Completion Time"}
        self.result_tree = ttk.Treeview(body, columns=rcols, show="headings",
                                        height=6)
        for c in rcols:
            self.result_tree.heading(c, text=titles[c])
            self.result_tree.column(c, width=150, anchor="center")
        self.result_tree.pack(fill="both", expand=True)

        # one empty row per algorithm (filled when Compare is pressed)
        self.row_ids = {}
        for name, _, _, _ in ALGO_ROWS:
            self.row_ids[name] = self.result_tree.insert(
                "", "end", values=(name, "-", "-", "-", "-"))

        self._on_mode_change()

    # show the I/O columns only when they are needed
    def _on_mode_change(self):
        with_io = self.mode_var.get() == "With I/O"
        shown = ["PID", "AT", "BT"]
        if with_io:
            shown += ["IOat", "IOdur"]
        self.tree["displaycolumns"] = shown

    def _add_process(self):
        n = len(self.tree.get_children()) + 1
        self.tree.insert("", "end", values=("P%d" % n, 0, 1, 1, 1))
        self._sort_rows()

    def _remove_process(self):
        items = self.tree.get_children()
        if items:
            self.tree.delete(items[-1])

    # put the table rows in arrival-time order
    def _sort_rows(self):
        rows = [self.tree.item(i, "values") for i in self.tree.get_children()]

        def key(v):
            try:
                return int(v[1])
            except ValueError:
                return 10 ** 9
        rows.sort(key=key)

        self.tree.delete(*self.tree.get_children())
        for v in rows:
            self.tree.insert("", "end", values=v)

    # read the table into a list of dicts
    def _read_processes(self, with_io):
        procs = []
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            p = {"pid": str(v[0]), "at": int(v[1]), "bt": int(v[2])}
            if with_io:
                p["io_at"] = int(v[3])
                p["io_dur"] = int(v[4])
            procs.append(p)
        return procs

    def _compare(self):
        self._sort_rows()          # always compare in arrival-time order
        with_io = self.mode_var.get() == "With I/O"

        try:
            procs = self._read_processes(with_io)
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Please enter whole numbers for all fields.")
            return
        if not procs:
            messagebox.showinfo("No processes", "Add at least one process.")
            return

        if with_io:
            for p in procs:
                if p["io_at"] >= p["bt"]:
                    messagebox.showerror(
                        "Invalid I/O",
                        "%s: I/O at (%d) must be smaller than Burst Time (%d)."
                        % (p["pid"], p["io_at"], p["bt"]))
                    return

        # run every algorithm on the SAME input and fill its row
        for name, plain_mod, wio_mod, tq in ALGO_ROWS:
            module = wio_mod if with_io else plain_mod
            # each simulate() needs its own fresh copy of the process list
            copy = [dict(p) for p in procs]
            result = module.simulate(copy, tq)
            m = result["metrics"]
            self.result_tree.item(self.row_ids[name],
                                  values=(name, m["avg_wt"], m["avg_tat"],
                                          m["avg_rt"], m["avg_ct"]))


# run this screen on its own
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Process Scheduling - Comparison")
    root.geometry("1150x620")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    ComparisonFrame(root).pack(fill="both", expand=True)
    root.mainloop()
