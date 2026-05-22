# -*- coding: utf-8 -*-
"""剪贴板监听：检测双击 Ctrl+C 划词翻译，支持动态启用/禁用"""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import time

class ClipboardMonitor(QObject):
    word_captured = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clipboard = QApplication.clipboard()
        self._last_text = ""
        self._last_time = 0.0
        self._interval = 0.5
        self._enabled = False   # 默认禁用

    def enable(self):
        if self._enabled:
            return
        self._clipboard.dataChanged.connect(self._on_clipboard_changed)
        self._enabled = True
        print("[Clipboard] 监听已启用")

    def disable(self):
        if not self._enabled:
            return
        try:
            self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
        except Exception:
            pass
        self._enabled = False
        print("[Clipboard] 监听已禁用")

    def _on_clipboard_changed(self):
        try:
            text = self._clipboard.text().strip()
        except Exception:
            return
        if not text or len(text) > 200:
            return
        now = time.time()
        if text == self._last_text and (now - self._last_time) < self._interval:
            self.word_captured.emit(text)
        self._last_text = text
        self._last_time = now
