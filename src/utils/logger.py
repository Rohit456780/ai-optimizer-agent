import os
import json
from datetime import datetime

LOG_PATH = "logs/optimizer_runs.log"
os.makedirs("logs", exist_ok=True)

def log_run(entry: dict):
    """
    Append a structured run record to logs/optimizer_runs.log.
    Each line is a JSON object for easy parsing later.
    """
    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def print_summary(entry: dict):
    print(f"\n📝 Logged Run → mode={entry.get('mode')} | value={entry.get('value')} | "
          f"runtime={entry.get('runtime')}s | status={entry.get('status')}")
