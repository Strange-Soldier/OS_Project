# scheduling_gui.py
# CPU Scheduling screen.
# This file ONLY builds the window and calls simulate() from the algorithm
# files.  There is NO scheduling math here.

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# make the CPU_Scheduling folder importable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "CPU_Scheduling"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fcfs, sjf, srtf, rr, priority
import fcfs_WIO, sjf_WIO, srtf_wIO, rr_wIO, priority_WIO
import theme

# which module to use for each (algorithm, mode) choice
ALGORITHMS = ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"]

PLAIN_MODULE = {"FCFS": fcfs, "SJF": sjf, "SRTF": srtf,
                "Round Robin": rr, "Priority": priority}
WIO_MODULE = {"FCFS": fcfs_WIO, "SJF": sjf_WIO, "SRTF": srtf_wIO,
              "Round Robin": rr_wIO, "Priority": priority_WIO}

# a few fixed colors to paint the Gantt bars (cycled if there are more PIDs)
BAR_COLORS = ["#7fb3ff", "#8fd19e", "#ffd27f", "#c7a8ec",
              "#ff9e9e", "#86d7d1", "#f0b3d8", "#b7c47f"]


class SchedulingFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)

        # the full result dict from the last run (None until first run)
        self.result = None
        self.pid_color = {}          # pid -> gantt color

        self._build_ui()
        self._on_algo_change()       # set correct columns / TQ state at start

    # =====================================================================
    # Build the screen
    # =====================================================================
    def _build_ui(self):
        # ---- title ----
        tk.Label(self, text="Scheduling", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_TITLE).pack(anchor="w", padx=20, pady=(12, 6))

        # ---- middle area: left controls + right panels ----
        middle = tk.Frame(self, bg=theme.APP_BG)
        middle.pack(fill="both", expand=True, padx=16)

        left = tk.Frame(middle, bg=theme.APP_BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(middle, bg=theme.APP_BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)

        # ---- bottom: playback bar ----
        self.playback = theme.PlaybackBar(self, on_render=self._render_snapshot,
                                          make_label=self._snapshot_label)
        self.playback.pack(fill="x", padx=16, pady=10)

    def _build_left(self, left):
        # --- Processes table ---
        card, body = theme.section_card(left, "Processes", theme.HEADER_BLUE)
        card.pack(fill="x", pady=(0, 10))

        cols = ("PID", "AT", "BT", "Priority", "IOat", "IOdur")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=6)
        headings = {"PID": "PID", "AT": "AT", "BT": "BT", "Priority": "Priority",
                    "IOat": "I/O at", "IOdur": "I/O dur"}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=70, anchor="center")
        self.tree.pack(fill="x")
        # double-click a cell to edit it; editing an input disables playback
        theme.attach_cell_editor(self.tree, cols, on_change=self._invalidate)

        # some starter rows (PID, AT, BT, Priority, IOat, IOdur)
        for row in [("P1", 0, 5, 2, 2, 2), ("P2", 1, 3, 1, 1, 2),
                    ("P3", 2, 4, 3, 2, 1)]:
            self.tree.insert("", "end", values=row)

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="+ Add Process", style="Green.TButton",
                   command=self._add_process).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="- Remove Process", style="Red.TButton",
                   command=self._remove_process).pack(side="left", expand=True, fill="x", padx=2)

        # --- options ---
        opt = tk.Frame(left, bg=theme.APP_BG)
        opt.pack(fill="x", pady=4)

        tk.Label(opt, text="Algorithm :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).grid(row=0, column=0, sticky="w", pady=4)
        self.algo_var = tk.StringVar(value="FCFS")
        algo_box = ttk.Combobox(opt, textvariable=self.algo_var, values=ALGORITHMS,
                                state="readonly", width=16)
        algo_box.grid(row=0, column=1, sticky="w", padx=6)
        algo_box.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

        tk.Label(opt, text="I/O Mode :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).grid(row=1, column=0, sticky="w", pady=4)
        self.mode_var = tk.StringVar(value="Without I/O")
        mode_box = ttk.Combobox(opt, textvariable=self.mode_var,
                                values=["Without I/O", "With I/O"],
                                state="readonly", width=16)
        mode_box.grid(row=1, column=1, sticky="w", padx=6)
        mode_box.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

        tk.Label(opt, text="Time Quantum :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).grid(row=2, column=0, sticky="w", pady=4)
        self.tq_var = tk.StringVar(value="2")
        self.tq_entry = ttk.Entry(opt, textvariable=self.tq_var, width=8)
        self.tq_entry.grid(row=2, column=1, sticky="w", padx=6)
        self.tq_var.trace_add("write", lambda *a: self._invalidate())

        ttk.Button(left, text="▶  Compile & Run", style="Green.TButton",
                   command=self._run).pack(fill="x", pady=(8, 10))

        # --- metrics ---
        card, body = theme.section_card(left, "Metrics", theme.HEADER_PURPLE)
        card.pack(fill="x")
        self.metric_vars = {}
        for name in ["Avg WT", "Avg TAT", "CPU Util", "Context Switches"]:
            row = tk.Frame(body, bg=theme.CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name + " :", bg=theme.CARD_BG, fg=theme.TEXT,
                     font=theme.FONT_NORMAL, width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value="-")
            self.metric_vars[name] = var
            tk.Label(row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

    def _build_right(self, right):
        top = tk.Frame(right, bg=theme.APP_BG)
        top.pack(fill="x")

        # Ready Queue
        card, body = theme.section_card(top, "Ready Queue", theme.HEADER_GREEN)
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.ready_box = tk.Listbox(body, height=5, font=theme.FONT_NORMAL,
                                    bd=0, highlightthickness=0)
        self.ready_box.pack(fill="both", expand=True)

        # Running
        card, body = theme.section_card(top, "Running (CPU)", theme.HEADER_YELLOW)
        card.pack(side="left", fill="both", expand=True, padx=6)
        self.running_lbl = tk.Label(body, text="-", bg=theme.CARD_BG,
                                    fg=theme.TEXT, font=("Segoe UI", 16, "bold"))
        self.running_lbl.pack(fill="both", expand=True)

        # Blocked / I/O
        self.blocked_card, body = theme.section_card(top, "Blocked (I/O)", "#dfe4ea")
        self.blocked_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.blocked_box = tk.Listbox(body, height=5, font=theme.FONT_NORMAL,
                                      bd=0, highlightthickness=0)
        self.blocked_box.pack(fill="both", expand=True)

        # Gantt chart
        card, body = theme.section_card(right, "Gantt Chart", theme.HEADER_BLUE)
        card.pack(fill="both", expand=True, pady=(10, 0))
        self.canvas = tk.Canvas(body, bg="white", height=140, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    # =====================================================================
    # Table helpers
    # =====================================================================
    def _add_process(self):
        n = len(self.tree.get_children()) + 1
        self.tree.insert("", "end", values=("P%d" % n, 0, 1, 1, 1, 1))
        self._invalidate()

    def _remove_process(self):
        items = self.tree.get_children()
        if items:
            self.tree.delete(items[-1])
            self._invalidate()

    # show only the columns that the current algorithm / mode needs
    def _on_algo_change(self):
        algo = self.algo_var.get()
        with_io = self.mode_var.get() == "With I/O"

        shown = ["PID", "AT", "BT"]
        if algo == "Priority":
            shown.append("Priority")
        if with_io:
            shown += ["IOat", "IOdur"]
        self.tree["displaycolumns"] = shown

        # Time Quantum only matters for Round Robin
        if algo == "Round Robin":
            self.tq_entry.config(state="normal")
        else:
            self.tq_entry.config(state="disabled")

        # grey the Blocked panel out when there is no I/O
        if with_io:
            self.blocked_box.config(state="normal")
        else:
            self.blocked_box.config(state="disabled")

        self._invalidate()

    # read the process rows out of the table into a list of dicts
    def _read_processes(self):
        algo = self.algo_var.get()
        with_io = self.mode_var.get() == "With I/O"
        procs = []
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            p = {"pid": str(v[0]), "at": int(v[1]), "bt": int(v[2])}
            if algo == "Priority":
                p["priority"] = int(v[3])
            if with_io:
                p["io_at"] = int(v[4])
                p["io_dur"] = int(v[5])
            procs.append(p)
        return procs

    # =====================================================================
    # Run + playback
    # =====================================================================
    # called whenever an input changes: the old playback is no longer valid
    def _invalidate(self):
        self.result = None
        if hasattr(self, "playback"):
            self.playback.disable()

    def _run(self):
        # pick the right module for the algorithm + I/O mode
        algo = self.algo_var.get()
        with_io = self.mode_var.get() == "With I/O"
        module = WIO_MODULE[algo] if with_io else PLAIN_MODULE[algo]

        # read the inputs
        try:
            procs = self._read_processes()
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Please enter whole numbers for AT, BT, Priority and I/O.")
            return
        if not procs:
            messagebox.showinfo("No processes", "Add at least one process.")
            return

        # time quantum (only used by Round Robin)
        tq = None
        if algo == "Round Robin":
            try:
                tq = int(self.tq_var.get())
            except ValueError:
                tq = 2

        # RUN THE ALGORITHM ONCE -- this builds the whole snapshot list
        self.result = module.simulate(procs, tq)

        # give every process a Gantt color
        self.pid_color = {}
        for i, p in enumerate(procs):
            self.pid_color[p["pid"]] = BAR_COLORS[i % len(BAR_COLORS)]

        # fill the metrics panel
        m = self.result["metrics"]
        self.metric_vars["Avg WT"].set(m["avg_wt"])
        self.metric_vars["Avg TAT"].set(m["avg_tat"])
        self.metric_vars["CPU Util"].set("%s %%" % m["cpu_util"])
        self.metric_vars["Context Switches"].set(m["context_switches"])

        # hand the finished snapshot list to the playback bar (this enables it)
        self.playback.load(self.result["snapshots"])

    # status label text for a snapshot:  "t=4 : P2 running : P2"
    def _snapshot_label(self, snap):
        pid = snap["running"] if snap["running"] else "-"
        return "t=%d : %s : %s" % (snap["t"], snap["event"], pid)

    # redraw everything for one snapshot (pure lookup, no recompute)
    def _render_snapshot(self, index, snap):
        # ready queue
        self.ready_box.config(state="normal")
        self.ready_box.delete(0, "end")
        for pid in snap["ready"]:
            self.ready_box.insert("end", pid)

        # running
        self.running_lbl.config(text=snap["running"] if snap["running"] else "idle")

        # blocked / I/O
        self.blocked_box.config(state="normal")
        self.blocked_box.delete(0, "end")
        for pid in snap["blocked"]:
            self.blocked_box.insert("end", pid)
        if self.mode_var.get() != "With I/O":
            self.blocked_box.config(state="disabled")

        # gantt chart up to the current time
        self._draw_gantt(current_time=snap["t"] + 1)

    # draw the Gantt bars, but only the part up to current_time
    def _draw_gantt(self, current_time):
        c = self.canvas
        c.delete("all")
        if not self.result:
            return

        gantt = self.result["gantt"]
        if not gantt:
            return

        total = gantt[-1][2]                 # end time of the last bar
        left = 40
        right = int(c.winfo_width()) - 20
        if right < left + 50:
            right = left + 600               # fallback before the canvas is sized
        scale = (right - left) / float(total)
        y_top = 30
        y_bot = 80

        for (pid, start, end) in gantt:
            if start >= current_time:
                continue                      # not reached yet
            draw_end = min(end, current_time) # clip the currently-running bar
            x1 = left + start * scale
            x2 = left + draw_end * scale
            color = self.pid_color.get(pid, "#9ec5fe")
            c.create_rectangle(x1, y_top, x2, y_bot, fill=color, outline="#44607e")
            c.create_text((x1 + x2) / 2, (y_top + y_bot) / 2, text=pid,
                          font=("Segoe UI", 10, "bold"))
            c.create_text(x1, y_bot + 12, text=str(start), font=("Segoe UI", 8))

        # time marker at the end of what we have drawn
        shown_end = min(current_time, total)
        xmark = left + shown_end * scale
        c.create_line(xmark, y_top - 8, xmark, y_bot + 8, fill="red", width=2)
        c.create_text(xmark, y_bot + 24, text="t=%d" % shown_end,
                      fill="red", font=("Segoe UI", 8, "bold"))


# run this screen on its own
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Scheduling")
    root.geometry("1150x760")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    SchedulingFrame(root).pack(fill="both", expand=True)
    root.mainloop()
