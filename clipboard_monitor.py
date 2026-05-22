# -*- coding: utf-8 -*-
"""剪贴板监听：检测双击 Ctrl+C 划词翻译"""
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication
import time

class ClipboardMonitor(QObject):
    word_captured = pyqtSignal(str)   # 触发时发出选中文本

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clipboard = QApplication.clipboard()
        self._last_text = ""
        self._last_time = 0.0
        self._double_ctrl_c_interval = 0.5  # 两次 Ctrl+C 间隔阈值（秒）

        # 监听剪贴板变化（用于配合 hotkey_manager 的双击 Ctrl+C）
        self._clipboard.dataChanged.connect(self._on_clipboard_changed)

    def _on_clipboard_changed(self):
        try:
            text = self._clipboard.text().strip()
        except Exception:
            return   # 剪贴板内容非文本（图片等），忽略
        if not text or len(text) > 200:
            return
        now = time.time()
        # 双击检测：同一文本在 interval 内连续触发两次
        if text == self._last_text and (now - self._last_time) < self._double_ctrl_c_interval:
            self.word_captured.emit(text)
        self._last_text = text
        self._last_time = now

    def get_selected_text(self) -> str:
        """直接获取当前剪贴板文本"""
        return self._clipboard.text().strip()
