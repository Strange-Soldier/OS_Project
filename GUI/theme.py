# theme.py
# Shared look-and-feel for all GUI screens, plus two reusable widgets:
#   - PlaybackBar : the |<  <  Play/Pause  >  >| control strip
#   - attach_cell_editor : lets the user double-click a table cell to edit it
# Keeping these in ONE place means every screen looks the same and the
# playback rules live in a single spot.

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Colors (a light-blue theme with colored section-header strips)
# ---------------------------------------------------------------------------
APP_BG        = "#eaf1fb"   # window background
CARD_BG       = "#ffffff"   # white cards that hold tables
HEADER_BLUE   = "#cfe2f7"   # section header strip (blue)
HEADER_GREEN  = "#d6ecd2"   # section header strip (green)
HEADER_YELLOW = "#f7e9c3"   # section header strip (yellow)
HEADER_PURPLE = "#e2dcf3"   # section header strip (purple)

ACCENT_GREEN  = "#4caf50"   # "run" buttons
ACCENT_RED    = "#e57373"   # "remove" buttons
ACCENT_BLUE   = "#2f6fed"   # "play" button
TEXT          = "#1f2d3d"   # normal text color
MUTED         = "#9aa6b2"   # greyed-out text

HIT_GREEN     = "#bfe6c0"   # cell color for a HIT
FAULT_RED     = "#f4c7c7"   # cell color for a FAULT

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 10)


# ---------------------------------------------------------------------------
# setup_styles() configures the ttk widgets once per window.
# ---------------------------------------------------------------------------
def setup_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")    # "clam" lets us set our own colors

    style.configure("TFrame", background=APP_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=APP_BG, foreground=TEXT, font=FONT_NORMAL)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=FONT_NORMAL)
    style.configure("Title.TLabel", background=APP_BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Header.TLabel", foreground=TEXT, font=FONT_HEADER)

    style.configure("TButton", font=FONT_NORMAL, padding=6)
    style.configure("Green.TButton", background=ACCENT_GREEN, foreground="white")
    style.map("Green.TButton", background=[("active", "#43a047")])
    style.configure("Red.TButton", background=ACCENT_RED, foreground="white")
    style.map("Red.TButton", background=[("active", "#ef5350")])
    style.configure("Blue.TButton", background=ACCENT_BLUE, foreground="white")
    style.map("Blue.TButton", background=[("active", "#2a61d0")])

    style.configure("TCombobox", font=FONT_NORMAL)
    style.configure("Treeview", font=FONT_NORMAL, rowheight=26,
                    background="white", fieldbackground="white")
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    background=HEADER_BLUE)
    style.configure("TNotebook", background=APP_BG)
    style.configure("TNotebook.Tab", font=FONT_NORMAL, padding=(14, 6))
    return style


# ---------------------------------------------------------------------------
# section_header() draws a colored strip with a bold title (like the mockups).
# Returns the card frame underneath where you put your content.
# ---------------------------------------------------------------------------
def section_card(parent, title, color):
    # outer card with a thin border
    card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#c9d6e5",
                    highlightthickness=1)
    # the colored header strip
    strip = tk.Frame(card, bg=color)
    strip.pack(fill="x")
    tk.Label(strip, text=title, bg=color, fg=TEXT, font=FONT_HEADER,
             anchor="w", padx=10, pady=6).pack(fill="x")
    # body area for the caller's widgets
    body = tk.Frame(card, bg=CARD_BG)
    body.pack(fill="both", expand=True, padx=10, pady=10)
    return card, body


# ---------------------------------------------------------------------------
# attach_cell_editor() makes a ttk.Treeview editable:
# double-click a cell in one of the editable columns to type a new value.
# ---------------------------------------------------------------------------
def attach_cell_editor(tree, editable_columns, on_change=None):

    def on_double_click(event):
        # which row and column was clicked
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)      # like "#2"
        if not row_id or not col_id:
            return

        # "#2" means the 2nd VISIBLE column, so look it up in the shown list
        shown = tree["displaycolumns"]
        if not shown or shown[0] == "#all":
            shown = tree["columns"]
        pos = int(col_id.replace("#", "")) - 1
        if pos < 0 or pos >= len(shown):
            return
        col_name = shown[pos]
        if col_name not in editable_columns:
            return                                   # this column is read-only

        # where to place the little edit box
        x, y, w, h = tree.bbox(row_id, col_id)
        value = tree.set(row_id, col_name)

        edit = tk.Entry(tree, font=FONT_NORMAL)
        edit.place(x=x, y=y, width=w, height=h)
        edit.insert(0, value)
        edit.focus_set()

        def save(_=None):
            tree.set(row_id, col_name, edit.get())
            edit.destroy()
            if on_change is not None:
                on_change()          # tell the screen an input changed

        edit.bind("<Return>", save)       # Enter saves
        edit.bind("<Escape>", lambda e: edit.destroy())
        edit.bind("<FocusOut>", save)     # clicking away saves

    tree.bind("<Double-1>", on_double_click)


# ---------------------------------------------------------------------------
# PlaybackBar : the shared scrub controls used by Scheduling and Page Replacement.
#
# How it works (this is the "unique feature"):
#   - It starts DISABLED. Nothing can be played until data is loaded.
#   - load(snapshots) is called AFTER the algorithm finished; it stores the
#     already-computed snapshot list and turns the controls on.
#   - Every button just moves an index inside that list and calls the owner's
#     render function. It NEVER re-runs the algorithm while scrubbing.
#   - Play uses root.after() to step forward; Pause cancels it; it stops at
#     the last snapshot.
#   - disable() is called whenever the inputs change, so stale data cannot be
#     scrubbed.
# ---------------------------------------------------------------------------
class PlaybackBar(tk.Frame):

    def __init__(self, parent, on_render, make_label):
        super().__init__(parent, bg=APP_BG)

        self.on_render = on_render      # function(index, snapshot) -> redraw screen
        self.make_label = make_label    # function(snapshot) -> status text

        self.snapshots = []             # the computed list (filled by load())
        self.index = 0                  # which snapshot we are showing
        self.playing = False            # is auto-play running?
        self.after_id = None            # id of the scheduled root.after call

        # --- the five control buttons ---
        self.b_first = ttk.Button(self, text="|<", width=4, command=self.go_first)
        self.b_prev  = ttk.Button(self, text="<",  width=4, command=self.go_prev)
        self.b_play  = ttk.Button(self, text="▶ Play", style="Blue.TButton",
                                  width=10, command=self.toggle_play)
        self.b_next  = ttk.Button(self, text=">",  width=4, command=self.go_next)
        self.b_last  = ttk.Button(self, text=">|", width=4, command=self.go_last)

        self.b_first.pack(side="left", padx=3)
        self.b_prev.pack(side="left", padx=3)
        self.b_play.pack(side="left", padx=3)
        self.b_next.pack(side="left", padx=3)
        self.b_last.pack(side="left", padx=3)

        # --- speed slider ---
        tk.Label(self, text="Speed:", bg=APP_BG, fg=TEXT,
                 font=FONT_NORMAL).pack(side="left", padx=(20, 4))
        self.speed = tk.DoubleVar(value=1.0)
        self.slider = ttk.Scale(self, from_=0.25, to=3.0, variable=self.speed,
                                length=140, orient="horizontal")
        self.slider.pack(side="left")
        self.speed_lbl = tk.Label(self, text="1.0x", bg=APP_BG, fg=TEXT,
                                  font=FONT_NORMAL, width=5)
        self.speed_lbl.pack(side="left", padx=4)
        self.speed.trace_add("write", self._update_speed_label)

        # --- status label ("t=4 : HIT : page 0") ---
        self.status = tk.Label(self, text="", bg=APP_BG, fg=TEXT,
                               font=FONT_MONO, anchor="w")
        self.status.pack(side="left", padx=20)

        self.disable()                  # start greyed out

    # show the speed next to the slider
    def _update_speed_label(self, *args):
        self.speed_lbl.config(text="%.2fx" % self.speed.get())

    # turn all controls off (start, or whenever inputs change)
    def disable(self):
        self.pause()
        self.snapshots = []
        for b in (self.b_first, self.b_prev, self.b_play, self.b_next, self.b_last):
            b.config(state="disabled")
        self.slider.config(state="disabled")
        self.status.config(text="Run the simulation to enable playback", fg=MUTED)

    # called AFTER the algorithm finished: store snapshots and turn controls on
    def load(self, snapshots):
        self.pause()
        self.snapshots = snapshots
        self.index = 0
        on = "normal"
        for b in (self.b_first, self.b_prev, self.b_play, self.b_next, self.b_last):
            b.config(state=on)
        self.slider.config(state=on)
        self.status.config(fg=TEXT)
        self._render()

    # redraw the current snapshot and update the status label
    def _render(self):
        if not self.snapshots:
            return
        snap = self.snapshots[self.index]
        self.on_render(self.index, snap)
        self.status.config(text=self.make_label(snap))

    # --- button actions: each one only moves the index ---
    def go_first(self):
        self.pause()
        self.index = 0
        self._render()

    def go_prev(self):
        self.pause()
        if self.index > 0:
            self.index -= 1
            self._render()

    def go_next(self):
        self.pause()
        if self.index < len(self.snapshots) - 1:
            self.index += 1
            self._render()

    def go_last(self):
        self.pause()
        self.index = len(self.snapshots) - 1
        self._render()

    # --- auto play ---
    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.snapshots:
            return
        self.playing = True
        self.b_play.config(text="❚❚ Pause")
        self._tick()

    def pause(self):
        self.playing = False
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.b_play.config(text="▶ Play")

    # one automatic step; schedules the next one with root.after()
    def _tick(self):
        if not self.playing:
            return
        if self.index >= len(self.snapshots) - 1:
            self.pause()            # reached the end, stop
            return
        self.index += 1
        self._render()
        delay = int(800 / self.speed.get())     # slider controls the speed
        self.after_id = self.after(delay, self._tick)
