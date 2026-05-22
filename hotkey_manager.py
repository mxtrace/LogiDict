# -*- coding: utf-8 -*-
"""全局热键管理：keyboard 模块注册，信号桥接到 Qt 主线程"""
import keyboard
from PyQt6.QtCore import QObject, pyqtSignal
import threading

class HotkeyManager(QObject):
    show_main_window = pyqtSignal()    # Alt+D
    capture_ocr      = pyqtSignal()    # Alt+Q
    clipboard_search = pyqtSignal()    # 双击 Ctrl+C（由此处检测）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._registered = False
        self._ctrl_c_times = []         # 记录 Ctrl+C 时间戳

    def start(self):
        if self._registered:
            return
        t = threading.Thread(target=self._register, daemon=True)
        t.start()
        self._registered = True

    def _register(self):
        try:
            keyboard.add_hotkey("alt+d", lambda: self.show_main_window.emit(), suppress=False)
            keyboard.add_hotkey("alt+q", lambda: self.capture_ocr.emit(), suppress=False)
            # Ctrl+C 双击检测
            keyboard.on_press_key("c", self._on_c_press)
        except Exception as e:
            print(f"[Hotkey] {e} — 尝试以普通权限运行")

    def _on_c_press(self, event):
        import time
        if not keyboard.is_pressed("ctrl"):
            return
        now = time.time()
        self._ctrl_c_times = [t for t in self._ctrl_c_times if now - t < 0.5]
        self._ctrl_c_times.append(now)
        if len(self._ctrl_c_times) >= 2:
            self._ctrl_c_times.clear()
            self.clipboard_search.emit()

    def stop(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self._registered = False
