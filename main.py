import os
import sys

# make the GUI folder importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI"))

from main_window import MainWindow

if __name__ == "__main__":
    MainWindow().mainloop()
