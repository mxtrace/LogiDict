# -*- coding: utf-8 -*-
"""全局热键管理：keyboard 模块注册，信号桥接到 Qt 主线程"""
import keyboard
from PyQt6.QtCore import QObject, pyqtSignal
import threading

class HotkeyManager(QObject):
    show_main_window = pyqtSignal()    # Alt+D（始终启用）
    capture_ocr      = pyqtSignal()    # Alt+Q（可关闭）
    clipboard_search = pyqtSignal()    # 双击 Ctrl+C（可关闭）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._registered = False
        self._ocr_enabled = False
        self._clipboard_enabled = False
        self._ctrl_c_times = []

    def start(self):
        """启动基础热键（仅 Alt+D 呼出主窗口）"""
        if self._registered:
            return
        t = threading.Thread(target=self._register_base, daemon=True)
        t.start()
        self._registered = True

    def _register_base(self):
        try:
            keyboard.add_hotkey("alt+d", lambda: self.show_main_window.emit(), suppress=False)
        except Exception as e:
            print(f"[Hotkey] {e}")

    # ── OCR 取词（Alt+Q）─────────────────────────────
    def enable_ocr(self):
        if self._ocr_enabled:
            return
        try:
            keyboard.add_hotkey("alt+q", lambda: self.capture_ocr.emit(), suppress=False)
            self._ocr_enabled = True
            print("[Hotkey] Alt+Q 取词已启用")
        except Exception as e:
            print(f"[Hotkey] enable_ocr: {e}")

    def disable_ocr(self):
        if not self._ocr_enabled:
            return
        try:
            keyboard.remove_hotkey("alt+q")
        except Exception:
            pass
        self._ocr_enabled = False
        print("[Hotkey] Alt+Q 取词已禁用")

    # ── 复制取词（双击 Ctrl+C）───────────────────────
    def enable_clipboard(self):
        if self._clipboard_enabled:
            return
        try:
            keyboard.on_press_key("c", self._on_c_press)
            self._clipboard_enabled = True
            print("[Hotkey] 双击 Ctrl+C 复制取词已启用")
        except Exception as e:
            print(f"[Hotkey] enable_clipboard: {e}")

    def disable_clipboard(self):
        if not self._clipboard_enabled:
            return
        try:
            keyboard.unhook_key("c")
        except Exception:
            pass
        self._clipboard_enabled = False
        self._ctrl_c_times.clear()
        print("[Hotkey] 双击 Ctrl+C 复制取词已禁用")

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
        self._ocr_enabled = False
        self._clipboard_enabled = False
