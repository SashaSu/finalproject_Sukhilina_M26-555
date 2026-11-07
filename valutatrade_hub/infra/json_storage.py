import json
import os
from pathlib import Path


def load_json(file_path):
    """Загрузка данных из JSON-файла"""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(file_path, data):
    """Сохранение данных в JSON-файл"""
    file_path = Path(file_path)
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise