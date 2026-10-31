# scheduling_gui.py
# Process Scheduling screen.
# This file only builds the window and calls simulate() from the algorithm
# files. There is no scheduling math here.

import os
import queue
import sys
import tkinter as tk
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "CPU_Scheduling"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fcfs, sjf, srtf, rr
import fcfs_WIO, sjf_WIO, srtf_wIO, rr_wIO
import theme
import insights

ALGORITHMS = ["FCFS", "SJF", "SRTF", "Round Robin"]

# which module to use for each algorithm, without and with I/O
PLAIN = {"FCFS": fcfs, "SJF": sjf, "SRTF": srtf, "Round Robin": rr}
WITH_IO = {"FCFS": fcfs_WIO, "SJF": sjf_WIO, "SRTF": srtf_wIO, "Round Robin": rr_wIO}

# colors for the boxes in the running queue
BOX_COLORS = ["#7fb3ff", "#8fd19e", "#ffd27f", "#c7a8ec",
              "#ff9e9e", "#86d7d1", "#f0b3d8", "#b7c47f"]
IDLE_COLOR = "#d8dee6"


class SchedulingFrame(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=theme.APP_BG)
        self.result = None          # result of the last run
        self.colors = {}            # pid -> box color
        self.steps = []             # (start, end) tick range of every step
        self.current_insights = []  # one explanation line per step
        self.procs = []             # processes of the last run
        self.algo = None            # algorithm of the last run
        self.with_io = False        # I/O mode of the last run
        self.tq = None              # time quantum of the last run
        self.run_id = 0             # bumped per run, so late AI replies are dropped
        self.ai_queue = queue.Queue()   # worker thread -> main thread
        self.ai_pending = False     # waiting for a Groq answer?
        self.ai_polling = False     # is the queue poller already running?
        self._build_ui()
        self._on_algo_change()


    def _build_ui(self):
        tk.Label(self, text="Process Scheduling", bg=theme.APP_BG, fg=theme.TEXT,
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

        # |< doubles as the reset button: rewind and empty the insights log
        self.playback.b_first.config(command=self._reset_playback)

    def _build_left(self, left):
        # --- process table ---
        card, body = theme.section_card(left, "Processes", theme.HEADER_BLUE)
        card.pack(fill="x", pady=(0, 10))

        cols = ("PID", "AT", "BT", "IOat", "IOdur")
        titles = {"PID": "PID", "AT": "AT", "BT": "BT",
                  "IOat": "I/O at", "IOdur": "I/O dur"}

        # table + vertical scrollbar side by side
        holder = tk.Frame(body, bg=theme.CARD_BG)
        holder.pack(fill="x")
        self.tree = ttk.Treeview(holder, columns=cols, show="headings", height=6)
        bar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(side="left", fill="x", expand=True)
        bar.pack(side="left", fill="y")

        for c in cols:
            self.tree.heading(c, text=titles[c])
            self.tree.column(c, width=72, anchor="center")
        # double-click a cell to edit it; editing turns playback off again
        theme.attach_cell_editor(self.tree, cols, on_change=self._after_edit)

        for row in [("P1", 0, 5, 2, 2), ("P2", 1, 3, 1, 2), ("P3", 2, 4, 2, 1)]:
            self.tree.insert("", "end", values=row)

        btns = tk.Frame(body, bg=theme.CARD_BG)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="+ Add Process", style="Green.TButton",
                   command=self._add).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btns, text="- Remove Process", style="Red.TButton",
                   command=self._remove).pack(side="left", expand=True, fill="x", padx=2)

        # --- options ---
        opt = tk.Frame(left, bg=theme.APP_BG)
        opt.pack(fill="x", pady=4)

        tk.Label(opt, text="Algorithm :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).grid(row=0, column=0, sticky="w", pady=4)
        self.algo_var = tk.StringVar(value="FCFS")
        box = ttk.Combobox(opt, textvariable=self.algo_var, values=ALGORITHMS,
                           state="readonly", width=16)
        box.grid(row=0, column=1, sticky="w", padx=6)
        box.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

        tk.Label(opt, text="I/O Mode :", bg=theme.APP_BG, fg=theme.TEXT,
                 font=theme.FONT_NORMAL).grid(row=1, column=0, sticky="w", pady=4)
        self.mode_var = tk.StringVar(value="Without I/O")
        box2 = ttk.Combobox(opt, textvariable=self.mode_var,
                            values=["Without I/O", "With I/O"],
                            state="readonly", width=16)
        box2.grid(row=1, column=1, sticky="w", padx=6)
        box2.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

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
        self.metrics = {}
        for name in ["Avg WT", "Avg TAT", "Avg RT", "Avg CT"]:
            row = tk.Frame(body, bg=theme.CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name + " :", bg=theme.CARD_BG, fg=theme.TEXT,
                     font=theme.FONT_NORMAL, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value="-")
            self.metrics[name] = var
            tk.Label(row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

    def _build_right(self, right):
        top = tk.Frame(right, bg=theme.APP_BG)
        top.pack(fill="x")

        card, body = theme.section_card(top, "Ready Queue", theme.HEADER_GREEN)
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.ready_box = tk.Listbox(body, height=5, font=theme.FONT_NORMAL,
                                    bd=0, highlightthickness=0)
        self.ready_box.pack(fill="both", expand=True)

        card, body = theme.section_card(top, "Currently Running Process", theme.HEADER_YELLOW)
        card.pack(side="left", fill="both", expand=True, padx=6)
        self.running_lbl = tk.Label(body, text="-", bg=theme.CARD_BG,
                                    fg=theme.TEXT, font=("Segoe UI", 16, "bold"))
        self.running_lbl.pack(fill="both", expand=True)

        card, body = theme.section_card(top, "Blocked (I/O)", "#dfe4ea")
        card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.blocked_box = tk.Listbox(body, height=5, font=theme.FONT_NORMAL,
                                      bd=0, highlightthickness=0)
        self.blocked_box.pack(fill="both", expand=True)

        # running queue drawing (boxes in the order the CPU ran them).
        # fixed height, so the insights log underneath gets the leftover room.
        card, body = theme.section_card(right, "Running Queue", theme.HEADER_BLUE)
        card.pack(fill="x", pady=(10, 0))
        qholder = tk.Frame(body, bg="white")
        qholder.pack(fill="x")
        self.canvas = tk.Canvas(qholder, bg="white", height=150, highlightthickness=0)
        qbar = ttk.Scrollbar(qholder, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=qbar.set)
        self.canvas.pack(side="top", fill="x")
        qbar.pack(side="bottom", fill="x")

        # insights log: one line per step, added underneath as playback moves
        card, body = theme.section_card(right, "Step Insights", theme.HEADER_PURPLE)
        card.pack(fill="both", expand=True, pady=(10, 0))

        holder = tk.Frame(body, bg=theme.CARD_BG)
        holder.pack(fill="both", expand=True)
        self.insight_text = tk.Text(holder, height=7, wrap="word", bd=0,
                                    highlightthickness=0, bg="white",
                                    fg=theme.TEXT, font=theme.FONT_NORMAL,
                                    padx=8, pady=6, state="disabled",
                                    cursor="arrow")
        bar = ttk.Scrollbar(holder, orient="vertical",
                            command=self.insight_text.yview)
        self.insight_text.configure(yscrollcommand=bar.set)
        self.insight_text.pack(side="left", fill="both", expand=True)
        bar.pack(side="left", fill="y")

        # the time stamp at the start of each line is dimmed
        self.insight_text.tag_configure("t", foreground=theme.MUTED,
                                        font=theme.FONT_MONO)
        # the newest line is highlighted so the current step stands out
        self.insight_text.tag_configure("now", background="#eef4ff",
                                        font=("Segoe UI", 10, "bold"))

        self.insight_src = tk.Label(body, text="", bg=theme.CARD_BG,
                                    fg=theme.MUTED, font=("Segoe UI", 8),
                                    anchor="w")
        self.insight_src.pack(fill="x", pady=(4, 0))

    # =====================================================================
    # Table helpers
    # =====================================================================
    def _add(self):
        n = len(self.tree.get_children()) + 1
        self.tree.insert("", "end", values=("P%d" % n, 0, 1, 1, 1))
        self._after_edit()

    def _remove(self):
        items = self.tree.get_children()
        if items:
            self.tree.delete(items[-1])
            self._invalidate()

    # after any edit: sort the rows by arrival time and turn playback off
    def _after_edit(self):
        self._sort_rows()
        self._invalidate()

    # put the table rows in arrival-time order
    def _sort_rows(self):
        rows = []
        for item in self.tree.get_children():
            rows.append(self.tree.item(item, "values"))

        # sort by arrival time; rows with bad numbers keep their place at the end
        def key(v):
            try:
                return int(v[1])
            except ValueError:
                return 10 ** 9
        rows.sort(key=key)

        self.tree.delete(*self.tree.get_children())
        for v in rows:
            self.tree.insert("", "end", values=v)

    # show the I/O columns only when the With I/O mode is on
    def _on_algo_change(self):
        with_io = self.mode_var.get() == "With I/O"

        shown = ["PID", "AT", "BT"]
        if with_io:
            shown += ["IOat", "IOdur"]
        self.tree["displaycolumns"] = shown

        # time quantum is only used by Round Robin
        if self.algo_var.get() == "Round Robin":
            self.tq_entry.config(state="normal")
        else:
            self.tq_entry.config(state="disabled")

        self._invalidate()

    # read the table rows into a list of dicts
    def _read_processes(self):
        with_io = self.mode_var.get() == "With I/O"
        procs = []
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            p = {"pid": str(v[0]), "at": int(v[1]), "bt": int(v[2])}
            if with_io:
                p["io_at"] = int(v[3])
                p["io_dur"] = int(v[4])
            procs.append(p)
        return procs

    # =====================================================================
    # Run and playback
    # =====================================================================
    def _invalidate(self):
        self.result = None
        self.steps = []
        self.current_insights = []
        self.ai_pending = False     # any answer still in flight is now stale
        if hasattr(self, "insight_text"):
            self._clear_log()
            self.insight_src.config(text="")
        if hasattr(self, "playback"):
            self.playback.disable()

    # reject values that make no physical sense (negatives, zero burst).
    # Returns True if every process is valid, otherwise shows an error.
    def _validate(self, procs, with_io):
        for p in procs:
            if p["at"] < 0:
                messagebox.showerror("Invalid input",
                    "%s: Arrival Time cannot be negative." % p["pid"])
                return False
            if p["bt"] < 1:
                messagebox.showerror("Invalid input",
                    "%s: Burst Time must be a whole number >= 1." % p["pid"])
                return False
            if with_io and (p["io_at"] < 0 or p["io_dur"] < 0):
                messagebox.showerror("Invalid input",
                    "%s: I/O values cannot be negative." % p["pid"])
                return False
        return True

    def _run(self):
        self._sort_rows()        # always run in arrival-time order

        algo = self.algo_var.get()
        with_io = self.mode_var.get() == "With I/O"
        module = WITH_IO[algo] if with_io else PLAIN[algo]

        try:
            procs = self._read_processes()
        except ValueError:
            messagebox.showerror("Invalid input",
                                 "Please enter whole numbers for AT, BT and I/O.")
            return
        if not procs:
            messagebox.showinfo("No processes", "Add at least one process.")
            return

        # reject impossible values (negative times, zero/negative burst, etc.)
        if not self._validate(procs, with_io):
            return

        if with_io:
            for p in procs:
                if p["io_at"] >= p["bt"]:
                    messagebox.showerror(
                        "Invalid I/O",
                        "%s: I/O at (%d) must be smaller than Burst Time (%d)."
                        % (p["pid"], p["io_at"], p["bt"]))
                    return

        tq = None
        if algo == "Round Robin":
            try:
                tq = int(self.tq_var.get())
            except ValueError:
                tq = 2
            if tq < 1:
                messagebox.showerror("Invalid input",
                                     "Time Quantum must be a whole number >= 1.")
                return

        # run the algorithm once; this builds the whole snapshot list
        self.result = module.simulate(procs, tq)

        # store run details for insights
        self.procs = procs
        self.algo = algo
        self.with_io = with_io
        self.tq = tq

        # give each process a color for its box
        self.colors = {}
        for i, p in enumerate(procs):
            self.colors[p["pid"]] = BOX_COLORS[i % len(BOX_COLORS)]

        m = self.result["metrics"]
        self.metrics["Avg WT"].set(m["avg_wt"])
        self.metrics["Avg TAT"].set(m["avg_tat"])
        self.metrics["Avg RT"].set(m["avg_rt"])
        self.metrics["Avg CT"].set(m["avg_ct"])

        # insights: the local lines are ready now, Groq wording may follow
        self.run_id = self.run_id + 1
        run_id = self.run_id

        # the worker thread must not touch widgets, so it only drops its
        # answer in this queue and the main thread picks it up in _poll_ai
        def on_ai(lines, note):
            self.ai_queue.put((run_id, lines, note))

        self.steps, self.current_insights, pending = insights.build(
            procs, self.result, algo, tq, with_io, on_ai=on_ai)

        if pending:
            self.insight_src.config(text="local explanations - asking Groq ...")
            self.ai_pending = True
            if not self.ai_polling:         # never stack two pollers
                self.ai_polling = True
                self.after(200, self._poll_ai)
        elif insights.get_key():
            self.insight_src.config(text="explained by Groq AI")
        else:
            self.insight_src.config(
                text="local explanations (set GROQ_API_KEY in .env for AI wording)")

        # one playback stop per step, not per tick: FCFS and SJF jump over the
        # whole burst, Round Robin over one quantum, SRTF stays tick by tick.
        stops = [self.result["snapshots"][b - 1] for a, b in self.steps]
        self.playback.load(stops)

    # look for the Groq answer; runs on the main thread, so widgets are safe
    def _poll_ai(self):
        while True:
            try:
                run_id, lines, note = self.ai_queue.get_nowait()
            except queue.Empty:
                break
            if run_id != self.run_id or not self.result:
                continue            # answer from an older run, throw it away

            self.ai_pending = False
            if lines:
                self.current_insights = lines
                self.insight_src.config(text="explained by Groq AI")
                self._write_log(self.playback.index)
            else:
                self.insight_src.config(
                    text="local explanations (Groq unavailable: %s)" % note)
            break

        if self.ai_pending:
            self.after(200, self._poll_ai)      # nothing yet, look again
        else:
            self.ai_polling = False

    def _snapshot_label(self, snap):
        pid = snap["running"] if snap["running"] else "idle"
        i = self.playback.index if hasattr(self, "playback") else 0
        if i < len(self.steps):
            a, b = self.steps[i]
            return "step %d/%d   t=%d to %d   %s" % (i + 1, len(self.steps),
                                                     a, b, pid)
        return "t=%d : %s" % (snap["t"], pid)

    # redraw everything for one snapshot (only a lookup, never a re-run)
    def _render_snapshot(self, index, snap):
        self.ready_box.delete(0, "end")
        for pid in snap["ready"]:
            self.ready_box.insert("end", pid)

        self.running_lbl.config(text=snap["running"] if snap["running"] else "idle")

        self.blocked_box.delete(0, "end")
        for pid in snap["blocked"]:
            self.blocked_box.insert("end", pid)

        self._write_log(index)
        # draw the chart up to the end of this step
        end = self.steps[index][1] if index < len(self.steps) else snap["t"] + 1
        self._draw_queue(end)

    # =====================================================================
    # Insights log
    # =====================================================================
    # The log always holds every step from the start up to the current one,
    # so moving forward adds lines underneath and the reset button empties it.
    def _write_log(self, upto):
        box = self.insight_text
        box.config(state="normal")
        box.delete("1.0", "end")

        for i in range(min(upto + 1, len(self.current_insights))):
            a = self.steps[i][0] if i < len(self.steps) else i
            start = box.index("end-1c")
            box.insert("end", "%2d.  t=%-3d " % (i + 1, a), "t")
            box.insert("end", self.current_insights[i] + "\n")
            if i == upto:
                box.tag_add("now", start, "end-1c")

        box.config(state="disabled")
        box.see("end")            # keep the newest line in view

    def _clear_log(self):
        box = self.insight_text
        box.config(state="normal")
        box.delete("1.0", "end")
        box.config(state="disabled")

    # the |< button rewinds playback and wipes the log
    def _reset_playback(self):
        self.playback.go_first()
        self._clear_log()

    # turn the ticks before "end" into boxes: one box per run, plus idle boxes
    def _make_boxes(self, end):
        boxes = []
        for i in range(min(end, len(self.result["snapshots"]))):
            pid = self.result["snapshots"][i]["running"]
            name = pid if pid else "idle"
            if boxes and boxes[-1][0] == name:
                boxes[-1][2] = i + 1          # same as before, stretch the box
            else:
                boxes.append([name, i, i + 1])  # new box
        return boxes

    # burst still left for each box's process once that box ends.
    # The preemptive algorithms show this under the chart, since it is what
    # decides when the process comes back.
    def _balance_after(self, boxes):
        bt = {}
        for p in self.procs:
            bt[p["pid"]] = p["bt"]

        used = {}
        out = []
        for name, start, end in boxes:
            if name == "idle":
                out.append(None)
                continue
            used[name] = used.get(name, 0) + (end - start)
            out.append(bt.get(name, 0) - used[name])
        return out

    # draw the running queue boxes left to right
    def _draw_queue(self, end):
        c = self.canvas
        c.delete("all")
        if not self.result:
            return

        boxes = self._make_boxes(end)
        if not boxes:
            return
        total = boxes[-1][2]

        left = 30
        # boxes are drawn to a fixed time scale: each unit of time is UNIT_PX
        # pixels wide. So a box's width is purely (ticks it ran x UNIT_PX) --
        # a process that ran twice as long is twice as wide, and already-drawn
        # boxes never change size as new ones get appended. When the chart runs
        # past the canvas edge the horizontal scrollbar takes over.
        UNIT_PX = 70
        top, bottom = 35, 90

        # preemptive runs give the CPU back before finishing, so show what each
        # process still has left when its box ends
        preemptive = self.algo in ("SRTF", "Round Robin")
        balance = self._balance_after(boxes) if preemptive else None

        for i, (name, b_start, b_end) in enumerate(boxes):
            # b_start / b_end are tick positions, so the box lands at its real
            # place on the timeline and its width scales with its duration
            x1 = left + b_start * UNIT_PX
            x2 = left + b_end * UNIT_PX
            color = IDLE_COLOR if name == "idle" else self.colors.get(name, "#9ec5fe")
            c.create_rectangle(x1, top, x2, bottom, fill=color, outline="#44607e")
            c.create_text((x1 + x2) / 2, (top + bottom) / 2, text=name,
                          font=("Segoe UI", 10, "bold"))
            c.create_text(x1, bottom + 12, text=str(b_start), font=("Segoe UI", 8))

            if balance and balance[i] is not None:
                c.create_text((x1 + x2) / 2, bottom + 30,
                              text=str(balance[i]),
                              font=("Segoe UI", 11, "bold"), fill="#5a6b7c")

        # the time at the very end
        end_x = left + total * UNIT_PX
        c.create_text(end_x, bottom + 12, text=str(total), font=("Segoe UI", 8))

        # let the scrollbar reach every box when they overflow the canvas
        c.configure(scrollregion=(0, 0, end_x + 20, int(c["height"])))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Process Scheduling")
    root.geometry("1150x760")
    root.configure(bg=theme.APP_BG)
    theme.setup_styles(root)
    SchedulingFrame(root).pack(fill="both", expand=True)
    root.mainloop()
