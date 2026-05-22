# -*- coding: utf-8 -*-
# LogiDict - Main Entry Point
# 启动：系统托盘 + 主窗口 + 全局热键 + 悬浮翻译窗
import sys
import os
import base64

# 必须在 QApplication 之前设置高DPI
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_B64 = (
    "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"
    "b8BJvHzsAAAAAElFTkSuQmCCiVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYA"
    "AABccqhmAAAK10lEQVR4nO3dC2yV5R3H8X9vtLQUCoXKTUCBhZuIaALBEIlz"
    "GjZExU1gF9yWLGwJ2WKMLHFkWSRLZnVLJIRBALfgxn1jMJEx5nDjIguQICD3"
    "i2UghVIKlJa2tGU5Z0K4lpbnbc95nt/3kzQxxD7n9fJ83+d9z3tJsRbUY0Th"
    "lZb8PMBHxzZPTWmpz2rWD2LCA8kdhMgHZtID/sQgssGY+IB/IXAehIkP+BuC"
    "VJdfZvIDieU6B++pHkx8IIzVQJNXAEx+IDndy9xsUgCY/EBya+ocbXQAmPyA"
    "H5oyVxsVACY/4JfGztm7BoDJD/ipMXO3wQAw+QG/3W0O3zEATH4gDA3NZacL"
    "gQD47bYBYO8PhOVOc/qWADD5gTDdbm5zCAAIuyEA7P2BsN08x1kBAMKuBYC9"
    "P6Dh+rnOCgAQRgAA9QCw/Ae0XJ3zrAAAYQQAEEYAAGEpHP8DulgBAMIIACCM"
    "AADCCAAgjAAAwggAIIwAAMIIACCMAADCCAAgjAAAwggAIIwAAMIIACCMAADC"
    "CAAgjAAAwggAIIwAAMIIACCMAADCCAAgjAAAwggAIIwAAMIIACCMAADCCAAg"
    "jAAAwggAIIwAAMIIACCMAADCCAAgjAAAwggAIIwAAMIIACCMAADCCAAgjAAA"
    "wggAIIwAAMIIACCMAADCCAAgjAAAwggAIIwAAMIIACCMAADC0k3IgL4Ftub3"
    "LzuN8caMf9r8JdstJHN/9YI9PbJPQj67vv5K/Ke2rt6qa2qtqrrWKipr7MLF"
    "ais7f8nOlFVa8elyO158wY7+96wdOFoa/3NEQyoASD6pqSnxn/T0VMvKTLd2"
    "uXf/nRPFF2zrzuP20ZajtvZfB62y6nJLbGqQCAC8061zW+vWeYA9//SA+ORf"
    "s/6ALV+z2zZvP5boTfMO5wDgteysDHtx9EBbNGO8rZz7bXv8sZ6J3iSvEAAE"
    "Y8iALrbwnZfiP3175Sd6c7xAABCc2Crg/Xcn2aRxjyR6U5IeAUCQYicUp7/6"
    "lM0vHGftcrMSvTlJiwAgaE893tuWzJxgHTvkJHpTkhIBQPD69+lkf/rtxPi3"
    "B7gRAYCEXt3b2/JZE60gn5XA9QgAZHS9r63Ne3Nc/PwA/o8AQMrD/Tvb2z8b"
    "bSkpid6S5EAAIOfZL/ez733j0URvRlIgAJA0dfJI69ktz9RxMARn5RerbdAz"
    "Mxr8e2I3/MRW3WlpqZYe+/ni5p+szAzLyc6wtm0yLa9dayvokGPdu7Sz3j07"
    "2NBBXS0/L7tZ/gu1zsqwt14fbeOnLLIrV0wWAUCLiN3yG1NXX2c1l+vifx27"
    "5bchseP0wf062zNP9LUJzw6OPAbDhnS38WMG2+K/7jRVHAIgacX2zJ/sLbbC"
    "2Rts+POzbdrb6+zchapIP+Mn3x9hrTLSTBUBgBdiq4b3VuywURPm2dp/H4xs"
    "3K4FufbN5x42VQQAXok9DWjy63+xmQu2RDbmlEnDZa8NIADw8tDgrTkbbO7i"
    "bZGM1yk/J/7VoCICAG/9cuZ6+3DT4UjGmjh2sCkiAPB6JfDTN9dG8pDQRx/q"
    "JvkQEQIAr5WUVljhnA2RjDV+zEOmhgDAe0tX77LjJ887j/OVBD0aPZEIALxX"
    "W1tvcxZujeSW4R5dtS4PJgAIwoq/74m/VMTVqOEPmBICgGDuR4i9JMTVEwQA"
    "8NPaDe4BeGRgF1PCCgDB2Li1yPnOvvy87PiFQSoIAIJxvrzKDheVOo8zoE+B"
    "qSAACMqeQyXOY/Tr3clUEAAE5eBnZ5zH6Ne7o6kgAAhK0YlzzmN0KWjEO8oD"
    "QQAQlM+Ly53HKMhvYyoIAIJScrbCeYwCvgUA/HT2XKXzGLltMmUeEMIKAEEp"
    "r6i+9gBSFwUihwEEAEGJXQh0qfqy8zg52RmmgAAgOFVV7jcFZbbiEADwUvUX"
    "7x1w0UrkUeGsABCc+rp65zEyWQEAfqqP4F1fma1YAQBeSk93n7xp6RqLY41/"
    "SkhpFcHkrY7g6UI+IAAITkYEJ/Cqa9xPJPqAACA40QSg1hQQAAQlNTXFsiI4"
    "g19NAAD/5OVmxSPg6mJFjSlgBYCgtM9rHck4p0vd7yr0AQFAUDq0y3Ye48LF"
    "artU5X4/gQ8IAIJS0NH9ib6nzlw0FQQAQXmwRwfnMYpL3J8q5AsCgKA8eH97"
    "5zEOF501FQQAQXkgghXApwdPmwoCgGDE7uAb2Nf9pR57CADgn9h7/Vzv46+t"
    "q7cDR9zfLeALVgAIxrAh9zuPsWtfsdVE8EARXxAABGP0qC85j7H+46OmhAAg"
    "CH165Vv/Pu7v9PtoyxFTQgAQhJe+Nsh5jNJzlbZr/ylTQgDgvdiLPL713BDn"
    "cVZ/uD+Sdwr4hADAe9/9+lBrk9PKeZyFq3aaGgIAr/XslmdTJg13HmfHnpO2"
    "95DOBUBXEQB4K/ad/2+mfTWS9/gtEtz7xxAAeCk9LdVm/GKMPTa4WyQn/1at"
    "22uKNN5/hKB07JBjs6aPtWFDukcy3qwF/7FKkfv/b0YA4NVef+LYwfba5JHW"
    "LjcrkjFPni6391bsMFUEAF6c6BvzZD/7zrgh1qUgN9Kx3/ndZpkHgN4OAUDi"
    "/udLS40/wDMjPc2yszMsNyczvmfv3KmNdb0v1/r17mRDB3aNX+XXHHbuK7Zl"
    "q3ebMgLQRD//8ZPxn2S2becJe/FHC1v0QpyiTa+ZT2J7/VemfxC/+08Z3wJA"
    "UuHsDXbos1JTRwAgZ+PWIpu/dFuiNyMpEABI2Xe4xH44baVF8AbxIBAAyPj8"
    "dLm9/OpyK79YnehNSRoEABJKyypt0ivLrLhE55n/jUEAELwDR8/Y2B/8wQ5y"
    "0u8WBABB+8emw/bC5D/a8ZPnE70pSYnrABCksvOX7I0Z6+3Pf/s00ZuS1AgA"
    "gnL5cp0tXb3bfj1vY/y4Hw0jAAhC7FHeS97fZbMWbImf7UfjEAB4bff+U7bs"
    "g922ct3e+LIfTUMA4JWKSzW29ZMTtnn7MVv/8ZH4GX7cOwKAhKutrbea2rr4"
    "8XtNTZ2VV9ZYaVmFnS27ZCVlFXb85IX4dfuHikrt2IlzVif25N7mlNJjRCH/"
    "NgFRXAcACCMAgDACAAgjAIAwAgAIIwCAMAIACCMAgDACAAgjAIAwAgAIIwCA"
    "MAIACCMAgDACAAgjAIAwAgAIIwCAMAIACCMAgDACAAgjAIAwAgAIIwCAMAIA"
    "CCMAgDACAAgjAIAwAgAIIwCAMAIACCMAgDACAAgjAIAwAgAIIwCAMAIACCMA"
    "gDACAAgjAIAwAgAIIwCAMAIACCMAgDACAAhLT/QGHJ6wKtGbACRM78VjE/fh"
    "rAAAbRwCAMIIACCMAADCCAAgjAAAwggAIIwAAMIIACCMAADCCAAgjAAAwggA"
    "IIwAAMIIACAsXf1+aEAZKwBAGAEAhBEAQBgBAISlHts8NSXRGwGg5cXmPisA"
    "QBgBAIQRAEA9AJwHALRcnfOsAABhBAAQdi0AHAYAGq6f66wAAGE3BIBVABC2"
    "m+c4KwBA2C0BYBUAhOl2c/u2KwAiAITlTnOaQwBA2B0DwCoACENDc7nBFQAR"
    "APx2tzl810MAIgD4qTFzt1HnAIgA4JfGztlGnwQkAoAfmjJXm/QtABEAkltT"
    "52iTvwYkAkByupe56fRA0B4jCq+4/D4Ady47ZacLgVgNAInlOgcjeyQ4qwGg"
    "5US18438nQCEAGg+Ua+6m/WlIMQAcNech9ot+lYgggDYXbXkubX/AXufrnBi"
    "SuuqAAAAAElFTkSuQmCC"
)


def load_app_icon():
    """从嵌入的 base64 数据加载图标"""
    data = base64.b64decode(ICON_B64)
    pix = QPixmap()
    pix.loadFromData(data)
    return QIcon(pix)

sys.path.insert(0, BASE_DIR)

import database as db
import settings as app_settings
from search_engine import SearchEngine
from tts_service import TTSService
from hotkey_manager import HotkeyManager
from clipboard_monitor import ClipboardMonitor
from ocr_service import OCRService
from main_window import MainWindow
from floating_window import FloatingWindow



class _OcrBridge(QObject):
    """跨线程传递 OCR 结果：后台线程 emit → Qt 主线程 slot"""
    result = pyqtSignal(str)


def make_tray_icon():
    """生成简单的蓝色圆形托盘图标"""
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    from PyQt6.QtGui import QPainter
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#89b4fa"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setFont(painter.font())
    painter.setPen(QColor("#1e1e2e"))
    font = painter.font()
    font.setPixelSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "L")
    painter.end()
    return QIcon(pix)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LogiDict")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(load_app_icon())

    # 初始化数据库
    db.init_db()
    db.seed_database()
    db.init_online_cache()
    db.clean_stale_online_cache()  # 清理无翻译旧缓存

    # 初始化服务
    engine = SearchEngine()
    tts = TTSService()
    ocr = OCRService()

    # 主窗口
    window = MainWindow(engine, tts, db)

    # 悬浮窗
    float_win = FloatingWindow(
        engine, tts,
        on_open_main=lambda word: (window.search(word), window.bring_to_front())
    )

    # 系统托盘
    tray = QSystemTrayIcon(load_app_icon(), app)
    tray.setToolTip("LogiDict — 物流外贸词典")
    menu = QMenu()
    act_show = menu.addAction("打开主窗口")
    act_show.triggered.connect(window.bring_to_front)
    menu.addSeparator()
    act_quit = menu.addAction("退出")
    act_quit.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.bring_to_front()
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    )
    tray.show()

    # 全局热键
    hotkey = HotkeyManager()
    hotkey.show_main_window.connect(window.bring_to_front)
    hotkey.clipboard_search.connect(lambda: _on_clipboard_search(window, float_win))
    hotkey.capture_ocr.connect(lambda: _on_ocr_capture(window, float_win, ocr))
    hotkey.start()   # 仅注册 Alt+D

    # 剪贴板监听（默认禁用）
    clip = ClipboardMonitor()
    clip.word_captured.connect(lambda text: _on_clipboard_search_text(text, window, float_win))

    # 按已保存设置决定是否启用取词功能
    cfg = app_settings.load()
    if cfg.get("hotkey_ocr_enabled"):
        hotkey.enable_ocr()
    if cfg.get("hotkey_clipboard_enabled"):
        hotkey.enable_clipboard()
        clip.enable()

    # 监听设置变更
    def _on_settings_changed(new_cfg):
        app_settings.save(new_cfg)
        if new_cfg.get("hotkey_ocr_enabled"):
            hotkey.enable_ocr()
        else:
            hotkey.disable_ocr()
        if new_cfg.get("hotkey_clipboard_enabled"):
            hotkey.enable_clipboard()
            clip.enable()
        else:
            hotkey.disable_clipboard()
            clip.disable()

    window.settings_changed.connect(_on_settings_changed)

    window.setWindowIcon(load_app_icon())
    window.show()
    sys.exit(app.exec())


def _on_clipboard_search(main_win, float_win):
    import pyperclip
    try:
        text = pyperclip.paste().strip()
    except Exception:
        text = ""
    if not text:
        return
    if len(text.split()) <= 4:  # 短词/短语才弹悬浮窗
        float_win.popup(text)
    else:
        main_win.search(text)
        main_win.bring_to_front()


def _on_clipboard_search_text(text: str, main_win, float_win):
    text = text.strip()
    if not text:
        return
    if len(text.split()) <= 4:
        float_win.popup(text)
    else:
        main_win.search(text)
        main_win.bring_to_front()


def _on_ocr_capture(main_win, float_win, ocr):
    from PyQt6.QtGui import QCursor
    pos = QCursor.pos()
    # Signal bridge：后台线程 emit，Qt 自动排队到主线程执行
    bridge = _OcrBridge()
    bridge.result.connect(lambda text: _ocr_show(text, pos, float_win, main_win))
    def on_ocr_done(text):
        bridge.result.emit(text.strip())
    if ocr.available:
        ocr.capture_and_recognize(callback=on_ocr_done)
    else:
        main_win.bring_to_front()


def _ocr_show(text, pos, float_win, main_win):
    if text:
        float_win.popup(text, pos)
    else:
        main_win.bring_to_front()


if __name__ == "__main__":
    main()
