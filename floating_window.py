# -*- coding: utf-8 -*-
# FloatingWindow: 鼠标附近弹出的悬浮翻译窗
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class FloatingWindow(QWidget):
    _result_ready = pyqtSignal(dict)  # 搜索结果信号（后台→主线程）

    def __init__(self, search_engine, tts_service, on_open_main=None, parent=None):
        super().__init__(parent)
        self.engine = search_engine
        self.tts = tts_service
        self.on_open_main = on_open_main
        self._pinned = False
        self._current_word = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(320)
        self.setMaximumWidth(500)

        qss_path = os.path.join(BASE_DIR, "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        self._build_ui()
        self._drag_pos = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._auto_hide)
        self._result_ready.connect(self._display)  # 跨线程安全更新 UI

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("FloatCard")
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(14, 10, 14, 12)
        card_lay.setSpacing(6)

        # 标题行
        title_row = QHBoxLayout()
        self._word_lbl = QLabel("")
        self._word_lbl.setObjectName("FloatWord")
        title_row.addWidget(self._word_lbl)
        title_row.addStretch()

        self._pin_btn = QPushButton("\U0001f4cc")
        self._pin_btn.setObjectName("FloatIconBtn")
        self._pin_btn.setFixedSize(24, 24)
        self._pin_btn.setToolTip("固定窗口")
        self._pin_btn.clicked.connect(self._toggle_pin)
        title_row.addWidget(self._pin_btn)

        self._tts_btn = QPushButton("\U0001f50a")
        self._tts_btn.setObjectName("FloatIconBtn")
        self._tts_btn.setFixedSize(24, 24)
        self._tts_btn.setToolTip("朗读")
        self._tts_btn.clicked.connect(lambda: self.tts.speak(self._word_lbl.text()))
        title_row.addWidget(self._tts_btn)

        self._open_btn = QPushButton("⛶")
        self._open_btn.setObjectName("FloatIconBtn")
        self._open_btn.setFixedSize(24, 24)
        self._open_btn.setToolTip("在主窗口打开")
        self._open_btn.clicked.connect(self._open_in_main)
        title_row.addWidget(self._open_btn)

        close_btn = QPushButton("×")
        close_btn.setObjectName("FloatCloseBtn")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        title_row.addWidget(close_btn)
        card_lay.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("Separator")
        card_lay.addWidget(sep)

        # 音标
        self._phonetic_lbl = QLabel("")
        self._phonetic_lbl.setObjectName("FloatPhonetic")
        card_lay.addWidget(self._phonetic_lbl)

        # 释义（前2条）
        self._def_lbl = QLabel("")
        self._def_lbl.setObjectName("FloatDef")
        self._def_lbl.setWordWrap(True)
        card_lay.addWidget(self._def_lbl)

        # 专业摘要
        self._pro_lbl = QLabel("")
        self._pro_lbl.setObjectName("FloatPro")
        self._pro_lbl.setWordWrap(True)
        card_lay.addWidget(self._pro_lbl)

        outer.addWidget(self._card)

    def popup(self, word: str, pos=None):
        self._pinned = False
        self._current_word = word
        self._word_lbl.setText(word)
        self._phonetic_lbl.setText("")
        self._def_lbl.setText("查询中...")
        self._pro_lbl.setText("")

        if pos is None:
            pos = QCursor.pos()

        screen = QApplication.primaryScreen().geometry()
        x = min(pos.x() + 12, screen.width() - 520)
        y = min(pos.y() + 20, screen.height() - 220)
        self.adjustSize()
        self.move(x, y)
        self.show()
        self.raise_()
        self._start_hide_timer()

        def on_result(result):
            # 在后台线程中 emit，Qt 自动排队到主线程执行 _display
            if result.get("word", "").lower() == self._current_word.lower():
                self._result_ready.emit(result)
        self.engine.search(word, callback=on_result)

    def _display(self, result: dict):
        puk = result.get("phonetic_uk", "")
        pus = result.get("phonetic_us", "")
        pt_parts = []
        if puk:
            pt_parts.append(f"UK {puk}")
        if pus:
            pt_parts.append(f"US {pus}")
        self._phonetic_lbl.setText("  ".join(pt_parts))

        defs = result.get("defs", [])[:2]
        def_lines = []
        for d in defs:
            pos = d.get("pos", "")
            dcn = d.get("def_cn", "")
            den = d.get("def_en", "")
            line = f"<b>{pos}</b> " if pos else ""
            line += dcn if dcn else den
            def_lines.append(line)
        self._def_lbl.setText("<br>".join(def_lines) if def_lines else "未找到")

        pro = result.get("pro")
        if pro:
            pdcn = pro.get("pro_def_cn", "")
            if pdcn:
                short = pdcn[:80] + ("..." if len(pdcn) > 80 else "")
                self._pro_lbl.setText("专业: " + short)
        self.adjustSize()

    def _toggle_pin(self):
        self._pinned = not self._pinned
        self._hide_timer.stop()
        style = "background:#4d9aff;color:#fff;border-radius:4px;" if self._pinned else ""
        self._pin_btn.setStyleSheet(style)

    def _open_in_main(self):
        word = self._current_word
        if self.on_open_main and word:
            self.on_open_main(word)
        self.hide()

    def _start_hide_timer(self):
        if not self._pinned:
            self._hide_timer.start(8000)

    def _auto_hide(self):
        if not self._pinned:
            self.hide()

    def enterEvent(self, event):
        self._hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._start_hide_timer()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
