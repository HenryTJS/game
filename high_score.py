import os
import json
from typing import Union

# ====================== 最高分系统 ======================
HIGH_SCORE_FILE = "high_score.json"

def load_high_score() -> int:
    """
    从文件中加载最高分记录。
    :return: 最高分记录，如果文件不存在或读取失败返回0
    """
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0

def save_high_score(score: Union[int, float]) -> None:
    """
    将最高分记录保存到文件中。
    :param score: 要保存的最高分
    """
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": int(score)}, f)
    except (IOError, TypeError):
        pass