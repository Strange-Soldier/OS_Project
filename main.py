import os
import sys

# Load .env file if it exists (for API keys like GROQ_API_KEY)
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

load_env()

# make the GUI folder importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI"))

from main_window import MainWindow

if __name__ == "__main__":
    MainWindow().mainloop()
