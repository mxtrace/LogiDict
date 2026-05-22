# -*- coding: utf-8 -*-
"""应用设置读写：存储于 %APPDATA%/LogiDict/settings.json"""
import json, os, sys

def _settings_path() -> str:
    if getattr(sys, "frozen", False):
        d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "LogiDict")
    else:
        d = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")

DEFAULTS = {
    "hotkey_ocr_enabled":       False,   # Alt+Q 截图取词
    "hotkey_clipboard_enabled": False,   # 双击 Ctrl+C 复制取词
}

def load() -> dict:
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return dict(DEFAULTS)

def save(data: dict):
    try:
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Settings] 保存失败: {e}")
