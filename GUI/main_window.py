# main_window.py
# The main application window: one Notebook with a tab per module.

import os
import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme
from scheduling_gui import SchedulingFrame
from memory_gui import MemoryFrame
from page_replacement_gui import PageReplacementFrame
from cache_gui import CacheFrame
from comparison_gui import ComparisonFrame


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("OS Process Visualization")
        self.geometry("1220x840")
        self.configure(bg=theme.APP_BG)
        theme.setup_styles(self)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # the five modules, one per tab
        notebook.add(SchedulingFrame(notebook), text="Process Scheduling")
        notebook.add(MemoryFrame(notebook), text="Memory Management")
        notebook.add(PageReplacementFrame(notebook), text="Page Replacement")
        notebook.add(CacheFrame(notebook), text="Cache Memory")
        notebook.add(ComparisonFrame(notebook), text="Comparison")


if __name__ == "__main__":
    MainWindow().mainloop()
