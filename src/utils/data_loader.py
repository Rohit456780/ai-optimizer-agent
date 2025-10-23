import json

def load_json_data(path: str):
    """
    Reads a JSON input file and returns parsed data as a Python dictionary.
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
        print(f"✅ Successfully loaded JSON data from {path}")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return None