import os
import json

HIGH_SCORE_FILE = "high_score.json"

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": int(score)}, f)
    except (IOError, TypeError):
        pass