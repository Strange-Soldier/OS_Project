# main_window.py
# The main application window: one Notebook with a tab per screen.

import os
import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme
from scheduling_gui import SchedulingFrame
from page_replacement_gui import PageReplacementFrame
from comparison_gui import ComparisonFrame


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("OS Process Visualization")
        self.geometry("1200x820")
        self.configure(bg=theme.APP_BG)
        theme.setup_styles(self)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # each tab holds one screen
        notebook.add(SchedulingFrame(notebook), text="Scheduling")
        notebook.add(self._memory_placeholder(notebook), text="Memory Allocation")
        notebook.add(PageReplacementFrame(notebook), text="Virtual Paging")
        notebook.add(ComparisonFrame(notebook), text="Comparison")

    # Memory Allocation is left for later (memory_gui.py is untouched/empty)
    def _memory_placeholder(self, parent):
        frame = tk.Frame(parent, bg=theme.APP_BG)
        tk.Label(frame, text="Memory Allocation screen coming soon.",
                 bg=theme.APP_BG, fg=theme.MUTED,
                 font=theme.FONT_HEADER).pack(expand=True)
        return frame


if __name__ == "__main__":
    MainWindow().mainloop()
