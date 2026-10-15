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
        card.pack(fill="x")

        # metric columns: key in the metrics dict + heading shown to the user.
        # For every one of these, a LOWER value is better.
        self.metric_cols = [
            ("avg_wt",  "Avg Waiting Time"),
            ("avg_tat", "Avg Turnaround Time"),
            ("avg_rt",  "Avg Response Time"),
            ("avg_ct",  "Avg Completion Time"),
        ]

        # Build the results as a grid of Labels (not a Treeview) so individual
        # cells can be colored to highlight the best/worst value per column.
        grid = tk.Frame(body, bg=theme.CARD_BG)
        grid.pack(fill="x")

        headers = ["Algorithm"] + [title for _, title in self.metric_cols]
        for col, text in enumerate(headers):
            grid.grid_columnconfigure(col, weight=1, uniform="metric")
            tk.Label(grid, text=text, bg=theme.HEADER_BLUE, fg=theme.TEXT,
                     font=("Segoe UI", 9, "bold"), relief="solid", bd=1,
                     padx=6, pady=6, wraplength=120).grid(
                         row=0, column=col, sticky="nsew")

        # one row of cells per algorithm; remember the value labels for coloring
        self.cells = {}          # name -> list of 4 metric Labels
        for r, (name, _, _, _) in enumerate(ALGO_ROWS, start=1):
            tk.Label(grid, text=name, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                     padx=6, pady=6).grid(row=r, column=0, sticky="nsew")
            row_cells = []
            for col in range(len(self.metric_cols)):
                lbl = tk.Label(grid, text="-", bg="white", fg=theme.TEXT,
                               font=theme.FONT_NORMAL, relief="solid", bd=1,
                               padx=6, pady=6)
                lbl.grid(row=r, column=col + 1, sticky="nsew")
                row_cells.append(lbl)
            self.cells[name] = row_cells

        # small legend for the highlight colors
        legend = tk.Frame(body, bg=theme.CARD_BG)
        legend.pack(fill="x", pady=(8, 0))
        tk.Label(legend, text="  ", bg=theme.HIT_GREEN, relief="solid",
                 bd=1).pack(side="left")
        tk.Label(legend, text=" lowest (best)   ", bg=theme.CARD_BG,
                 fg=theme.TEXT, font=theme.FONT_NORMAL).pack(side="left")
        tk.Label(legend, text="  ", bg=theme.FAULT_RED, relief="solid",
                 bd=1).pack(side="left")
        tk.Label(legend, text=" highest (worst)", bg=theme.CARD_BG,
                 fg=theme.TEXT, font=theme.FONT_NORMAL).pack(side="left")

        # ---- insights panel ----
        card, body = theme.section_card(right, "Insights", theme.HEADER_GREEN)
        card.pack(fill="both", expand=True, pady=(10, 0))
        self.insights = tk.Text(body, height=9, font=theme.FONT_NORMAL,
                                bd=0, highlightthickness=0, wrap="word")
        self.insights.pack(side="left", fill="both", expand=True)
        ibar = ttk.Scrollbar(body, command=self.insights.yview)
        ibar.pack(side="left", fill="y")
        self.insights.config(yscrollcommand=ibar.set)
        self.insights.insert("end", "Press Compare to generate insights.")
        self.insights.config(state="disabled")

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

        # reject impossible values (negative times, zero/negative burst, etc.)
        for p in procs:
            if p["at"] < 0:
                messagebox.showerror("Invalid input",
                    "%s: Arrival Time cannot be negative." % p["pid"])
                return
            if p["bt"] < 1:
                messagebox.showerror("Invalid input",
                    "%s: Burst Time must be a whole number >= 1." % p["pid"])
                return
            if with_io and (p["io_at"] < 0 or p["io_dur"] < 0):
                messagebox.showerror("Invalid input",
                    "%s: I/O values cannot be negative." % p["pid"])
                return

        if with_io:
            for p in procs:
                if p["io_at"] >= p["bt"]:
                    messagebox.showerror(
                        "Invalid I/O",
                        "%s: I/O at (%d) must be smaller than Burst Time (%d)."
                        % (p["pid"], p["io_at"], p["bt"]))
                    return

        # run every algorithm on the SAME input, keep each metrics dict
        metrics_by_algo = {}          # name -> metrics dict
        for name, plain_mod, wio_mod, tq in ALGO_ROWS:
            module = wio_mod if with_io else plain_mod
            # each simulate() needs its own fresh copy of the process list
            copy = [dict(p) for p in procs]
            result = module.simulate(copy, tq)
            metrics_by_algo[name] = result["metrics"]

        self._fill_table(metrics_by_algo)
        self._show_insights(metrics_by_algo, with_io)

    # fill the grid and color the best (lowest) and worst (highest) cell
    # in each metric column
    def _fill_table(self, metrics_by_algo):
        names = [name for name, _, _, _ in ALGO_ROWS]

        for ci, (key, _) in enumerate(self.metric_cols):
            values = [metrics_by_algo[name][key] for name in names]
            lo, hi = min(values), max(values)

            for name in names:
                val = metrics_by_algo[name][key]
                lbl = self.cells[name][ci]
                lbl.config(text="%g" % val)
                # only color when there is a real spread between algorithms
                if lo == hi:
                    lbl.config(bg="white")
                elif val == lo:
                    lbl.config(bg=theme.HIT_GREEN)      # lowest = best
                elif val == hi:
                    lbl.config(bg=theme.FAULT_RED)      # highest = worst
                else:
                    lbl.config(bg="white")

    # turn the numbers into short plain-English takeaways
    def _show_insights(self, metrics_by_algo, with_io):
        names = [name for name, _, _, _ in ALGO_ROWS]
        lines = []

        # best algorithm for each metric (lowest value wins)
        pretty = {"avg_wt": "waiting time", "avg_tat": "turnaround time",
                  "avg_rt": "response time", "avg_ct": "completion time"}
        for key, _ in self.metric_cols:
            best = min(names, key=lambda n: metrics_by_algo[n][key])
            worst = max(names, key=lambda n: metrics_by_algo[n][key])
            bval = metrics_by_algo[best][key]
            wval = metrics_by_algo[worst][key]
            if bval == wval:
                lines.append("- Average %s is the same (%g) for every algorithm."
                             % (pretty[key], bval))
            else:
                lines.append("- Lowest average %s: %s (%g); highest: %s (%g)."
                             % (pretty[key], best, bval, worst, wval))

        # overall winner: fewest "wins" ranking across WT, TAT and RT
        score = {n: 0 for n in names}
        for key in ("avg_wt", "avg_tat", "avg_rt"):
            best = min(names, key=lambda n: metrics_by_algo[n][key])
            score[best] += 1
        top = max(names, key=lambda n: score[n])
        if score[top] > 0:
            lines.append("")
            lines.append("Overall: %s looks best here, leading in %d of the "
                         "three key metrics (WT, TAT, RT)."
                         % (top, score[top]))

        # context-switch note (fewer switches = less overhead)
        cs = {n: metrics_by_algo[n].get("context_switches", 0) for n in names}
        cs_lo = min(names, key=lambda n: cs[n])
        cs_hi = max(names, key=lambda n: cs[n])
        if cs[cs_lo] != cs[cs_hi]:
            lines.append("- Fewest context switches: %s (%d); most: %s (%d) "
                         "- more switches mean more scheduling overhead."
                         % (cs_lo, cs[cs_lo], cs_hi, cs[cs_hi]))

        # CPU utilisation note (I/O mode can leave the CPU idle)
        if with_io:
            util = {n: metrics_by_algo[n].get("cpu_util", 0) for n in names}
            u_hi = max(names, key=lambda n: util[n])
            lines.append("- Highest CPU utilisation: %s (%g%%)."
                         % (u_hi, util[u_hi]))

        self.insights.config(state="normal")
        self.insights.delete("1.0", "end")
        self.insights.insert("end", "\n".join(lines))
        self.insights.config(state="disabled")


# run this screen on its own
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Process Scheduling - Comparison")
    root.geometry("1150x620")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    ComparisonFrame(root).pack(fill="both", expand=True)
    root.mainloop()
