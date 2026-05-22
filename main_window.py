# -*- coding: utf-8 -*-
# LogiDict - Main Window (PyQt6)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QListWidget, QListWidgetItem, QSplitter,
    QCompleter, QApplication, QStackedWidget
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QPoint
)
from PyQt6.QtGui import QKeySequence, QShortcut
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SearchThread(QThread):
    result_ready = pyqtSignal(dict)
    def __init__(self, engine, word):
        super().__init__()
        self.engine = engine
        self.word = word
    def run(self):
        result = self.engine._do_search(self.word)
        self.result_ready.emit(result or {})


class ProCard(QFrame):
    def __init__(self, pro: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("ProCard")
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        title_row = QHBoxLayout()
        full_form = pro.get("full_form", "")
        abbrev = pro.get("abbrev", "")
        domain = pro.get("domain", "")
        title_text = full_form if full_form else abbrev
        title = QLabel(f"<b>{title_text}</b>")
        title.setObjectName("ProTitle")
        domain_lbl = QLabel(domain.upper())
        domain_lbl.setObjectName("DomainTag")
        domain_lbl.setFixedHeight(20)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(domain_lbl)
        lay.addLayout(title_row)
        pdcn = pro.get("pro_def_cn", "")
        if pdcn:
            lbl = QLabel(pdcn)
            lbl.setObjectName("ProDefCn")
            lbl.setWordWrap(True)
            lay.addWidget(lbl)
        pden = pro.get("pro_def_en", "")
        if pden:
            lbl = QLabel(pden)
            lbl.setObjectName("ProDefEn")
            lbl.setWordWrap(True)
            lay.addWidget(lbl)
        for key, icon in [("biz_example_1", "💼"), ("biz_example_2", "📦")]:
            ex = pro.get(key, "")
            if ex:
                ex_lbl = QLabel(f"{icon} {ex}")
                ex_lbl.setObjectName("BizExample")
                ex_lbl.setWordWrap(True)
                lay.addWidget(ex_lbl)
        related = pro.get("related", "")
        if related:
            rel_lbl = QLabel(f"<span style='color:#999'>Related:</span> {related}")
            rel_lbl.setObjectName("RelatedTerms")
            rel_lbl.setWordWrap(True)
            lay.addWidget(rel_lbl)


class DefItem(QFrame):
    """单条释义：编号 + 中文定义 + 英文定义 + 双语例句"""
    def __init__(self, d: dict, index: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("DefItem")
        lay = QVBoxLayout(self)
        lay.setSpacing(3)
        lay.setContentsMargins(0, 4, 0, 6)
        def_cn = d.get("def_cn", "")
        def_en = d.get("def_en", "")
        # 编号 + 中文释义（主行）
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        num_lbl = QLabel(f"{index}.")
        num_lbl.setObjectName("DefNum")
        num_lbl.setFixedWidth(20)
        top_row.addWidget(num_lbl)
        if def_cn:
            cn_lbl = QLabel(def_cn)
            cn_lbl.setObjectName("DefCn")
            cn_lbl.setWordWrap(True)
            top_row.addWidget(cn_lbl, 1)
        elif def_en:
            en_inline = QLabel(def_en)
            en_inline.setObjectName("DefCn")
            en_inline.setWordWrap(True)
            top_row.addWidget(en_inline, 1)
        lay.addLayout(top_row)
        # 英文原文（次行，缩进对齐编号）
        if def_en and def_cn:
            en_lbl = QLabel(def_en)
            en_lbl.setObjectName("DefEn")
            en_lbl.setWordWrap(True)
            en_lbl.setContentsMargins(26, 0, 0, 0)
            lay.addWidget(en_lbl)
        # 双语例句
        ex_en = d.get("example_en", "")
        ex_cn = d.get("example_cn", "")
        if ex_en:
            ex_frame = QFrame()
            ex_frame.setObjectName("ExampleFrame")
            ex_lay = QVBoxLayout(ex_frame)
            ex_lay.setSpacing(2)
            ex_lay.setContentsMargins(26, 4, 0, 0)
            ex_en_lbl = QLabel(f"📝 <i>{ex_en}</i>")
            ex_en_lbl.setObjectName("ExampleEn")
            ex_en_lbl.setWordWrap(True)
            ex_lay.addWidget(ex_en_lbl)
            if ex_cn:
                ex_cn_lbl = QLabel(f"　{ex_cn}")
                ex_cn_lbl.setObjectName("ExampleCn")
                ex_cn_lbl.setWordWrap(True)
                ex_lay.addWidget(ex_cn_lbl)
            lay.addWidget(ex_frame)


class DefGroup(QFrame):
    """按词性分组的释义块：POS 标题 + 多条 DefItem"""
    def __init__(self, pos: str, defs: list, parent=None):
        super().__init__(parent)
        self.setObjectName("DefGroup")
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 8)
        # 词性标题行
        pos_row = QHBoxLayout()
        pos_lbl = QLabel(pos.lower() if pos else "other")
        pos_lbl.setObjectName("PosTag")
        pos_row.addWidget(pos_lbl)
        pos_row.addStretch()
        lay.addLayout(pos_row)
        # 逐条释义
        for i, d in enumerate(defs, 1):
            lay.addWidget(DefItem(d, index=i))



class SuggestionPanel(QFrame):
    """搜索框下方的悬浮候选词面板"""
    word_selected = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("SuggestionPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(0)
        self._list = QListWidget()
        self._list.setObjectName("SugList")
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.itemClicked.connect(self._on_click)
        lay.addWidget(self._list)
        self.hide()

    def update_items(self, items: list, anchor_widget=None):
        """更新候选词列表并重新定位"""
        self._list.clear()
        for it in items:
            word = it.get("word", "")
            pos  = it.get("part_of_speech", "") or it.get("pos", "")
            hint = it.get("full_form", "") or it.get("def_cn", "")
            hint = (hint[:30] + "…") if len(hint) > 30 else hint

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, word)
            # 两行文字：词＋词性 / 简义
            display = f"{word}"
            if pos:
                display += f"  [{pos}]"
            item.setText(display)
            item.setToolTip(hint)
            # 在 decoration role 存 hint，由 delegate 绘制
            item.setData(Qt.ItemDataRole.UserRole + 1, hint)
            self._list.addItem(item)

        n = len(items)
        if n:
            self._list.setCurrentRow(-1)
            row_h = 52
            self.setFixedHeight(n * row_h + 8)
            if anchor_widget:
                self._reposition(anchor_widget)
            self.show()
            self.raise_()
        else:
            self.hide()

    def _reposition(self, ref: QWidget):
        pos = ref.mapTo(self.parentWidget(), QPoint(0, ref.height()))
        self.move(pos.x(), pos.y())
        self.setFixedWidth(ref.width())

    def _on_click(self, item):
        word = item.data(Qt.ItemDataRole.UserRole)
        if word:
            self.hide()
            self.word_selected.emit(word)

    def navigate(self, direction: int) -> str:
        """上下方向键导航；返回当前高亮词"""
        n = self._list.count()
        if n == 0:
            return ""
        cur = self._list.currentRow()
        cur = max(0, min(n - 1, cur + direction))
        self._list.setCurrentRow(cur)
        return self._list.item(cur).data(Qt.ItemDataRole.UserRole)

    def current_word(self) -> str:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ""

    def paintEvent(self, e):
        super().paintEvent(e)

    def drawItemDelegate(self):
        pass

class ResultPanel(QScrollArea):
    def __init__(self, tts, on_add_vocab, on_remove_vocab, parent=None):
        super().__init__(parent)
        self.tts = tts
        self.on_add_vocab = on_add_vocab
        self.on_remove_vocab = on_remove_vocab
        self.current_word = ""
        self.in_vocab = False
        self.setWidgetResizable(True)
        self.setObjectName("ResultPanel")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container.setObjectName("ResultContainer")
        self._layout = QVBoxLayout(self._container)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(20, 16, 20, 24)
        self.setWidget(self._container)

    def show_result(self, result: dict, in_vocab: bool = False):
        self._clear()
        self.current_word = result.get("word", "")
        self.in_vocab = in_vocab
        if not result.get("word"):
            cn_q = result.get("cn_query", "")
            msg = f"未找到「{cn_q}」相关英文词汇" if cn_q else "未找到结果 / Not found"
            lbl = QLabel(msg)
            lbl.setObjectName("NotFound")
            self._layout.addWidget(lbl)
            hint = QLabel("提示：可尝试英文或缩写搜索，如 FCL、B/L、ETA 等" if cn_q else "")
            hint.setObjectName("EmptyHint")
            if cn_q:
                self._layout.addWidget(hint)
            self._layout.addStretch()
            return
        head_row = QHBoxLayout()
        word_lbl = QLabel(result["word"])
        word_lbl.setObjectName("WordHead")
        head_row.addWidget(word_lbl)
        puk = result.get("phonetic_uk", "")
        pus = result.get("phonetic_us", "")
        if puk or pus:
            pt = ""
            if puk:
                pt += f"<span style='color:#888'>UK</span> {puk}&nbsp;&nbsp;"
            if pus:
                pt += f"<span style='color:#888'>US</span> {pus}"
            ph_lbl = QLabel(pt)
            ph_lbl.setObjectName("Phonetic")
            head_row.addWidget(ph_lbl)
        head_row.addStretch()
        tts_btn = QPushButton("🔊")
        tts_btn.setObjectName("IconBtn")
        tts_btn.setFixedSize(32, 32)
        tts_btn.setToolTip("朗读")
        tts_btn.clicked.connect(lambda: self.tts.speak(result["word"]))
        head_row.addWidget(tts_btn)
        self._fav_btn = QPushButton("★" if in_vocab else "☆")
        self._fav_btn.setObjectName("FavBtn")
        self._fav_btn.setFixedSize(32, 32)
        self._fav_btn.setCheckable(True)
        self._fav_btn.setChecked(in_vocab)
        self._fav_btn.setToolTip("收藏")
        self._fav_btn.clicked.connect(self._toggle_vocab)
        head_row.addWidget(self._fav_btn)
        src = result.get("source", "")
        if src == "online":
            src_lbl = QLabel("[在线]")
            src_lbl.setObjectName("SourceTag")
            head_row.addWidget(src_lbl)
        cn_q = result.get("cn_query", "")
        if cn_q:
            cn_tag = QLabel(f"「{cn_q}」")
            cn_tag.setObjectName("SourceTag")
            head_row.addWidget(cn_tag)
        self._layout.addLayout(head_row)
        self._layout.addWidget(self._separator())
        defs = result.get("defs", [])
        if defs:
            # 添加"释义"区块标题
            def_title = QLabel("  释义 / Definitions")
            def_title.setObjectName("SectionTitle")
            self._layout.addWidget(def_title)
            # 按词性分组
            groups = {}
            order = []
            for d in defs:
                p = d.get("pos", "") or "other"
                if p not in groups:
                    groups[p] = []
                    order.append(p)
                groups[p].append(d)
            for p in order:
                self._layout.addWidget(DefGroup(p, groups[p]))
            self._layout.addWidget(self._separator())
        pro = result.get("pro")
        if pro:
            pro_title = QLabel("  专业释义 / Professional")
            pro_title.setObjectName("SectionTitle")
            self._layout.addWidget(pro_title)
            self._layout.addWidget(ProCard(pro))
        self._layout.addStretch()
        self.verticalScrollBar().setValue(0)

    def show_empty(self, message: str = "在上方搜索框输入单词"):
        self._clear()
        lbl = QLabel(message)
        lbl.setObjectName("EmptyHint")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addStretch()
        self._layout.addWidget(lbl)
        self._layout.addStretch()

    def show_loading(self):
        self._clear()
        lbl = QLabel("查询中…")
        lbl.setObjectName("LoadingHint")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addStretch()
        self._layout.addWidget(lbl)
        self._layout.addStretch()

    def _toggle_vocab(self):
        if self._fav_btn.isChecked():
            self.on_add_vocab(self.current_word)
            self._fav_btn.setText("★")
        else:
            self.on_remove_vocab(self.current_word)
            self._fav_btn.setText("☆")

    def _clear(self):
        def _recurse(layout):
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
                elif item.layout():
                    _recurse(item.layout())
        _recurse(self._layout)

    def _separator(self):
        line = QFrame()
        line.setObjectName("Separator")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        return line


class SidePanel(QWidget):
    word_selected = pyqtSignal(str)
    history_deleted = pyqtSignal(str)   # 删除历史条目时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidePanel")
        self.setFixedWidth(180)
        self._vocab_set = set()   # 已收藏词集合，用于右键菜单判断

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(0)
        self._hist_btn = QPushButton("历史")
        self._hist_btn.setObjectName("SideTabBtn")
        self._hist_btn.setCheckable(True)
        self._hist_btn.setChecked(True)
        self._vocab_btn = QPushButton("词汇本")
        self._vocab_btn.setObjectName("SideTabBtn")
        self._vocab_btn.setCheckable(True)
        btn_row.addWidget(self._hist_btn)
        btn_row.addWidget(self._vocab_btn)
        lay.addLayout(btn_row)

        self._stack = QStackedWidget()
        self._hist_list = QListWidget()
        self._hist_list.setObjectName("SideList")
        self._hist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._hist_list.customContextMenuRequested.connect(self._hist_context_menu)
        self._vocab_list = QListWidget()
        self._vocab_list.setObjectName("SideList")
        self._stack.addWidget(self._hist_list)
        self._stack.addWidget(self._vocab_list)
        lay.addWidget(self._stack)

        self._hist_btn.clicked.connect(lambda: self._switch(0))
        self._vocab_btn.clicked.connect(lambda: self._switch(1))
        self._hist_list.itemClicked.connect(lambda i: self.word_selected.emit(i.text()))
        self._vocab_list.itemClicked.connect(lambda i: self.word_selected.emit(i.text()))

    def _switch(self, idx):
        self._stack.setCurrentIndex(idx)
        self._hist_btn.setChecked(idx == 0)
        self._vocab_btn.setChecked(idx == 1)

    def _hist_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        item = self._hist_list.itemAt(pos)
        if not item:
            return
        word = item.text()
        menu = QMenu(self)
        # 已收藏的词不能删除历史
        if word.lower() in self._vocab_set:
            act_info = menu.addAction("★ 已收藏，不可删除历史")
            act_info.setEnabled(False)
        else:
            act_del = menu.addAction("× 删除此条记录")
            act_del.triggered.connect(lambda: self.history_deleted.emit(word))
        menu.exec(self._hist_list.mapToGlobal(pos))

    def update_history(self, words: list):
        self._hist_list.clear()
        for w in words:
            item = QListWidgetItem(w)
            # 已收藏的词加星号提示
            if w.lower() in self._vocab_set:
                item.setForeground(item.foreground())  # 用样式表控制颜色
                item.setToolTip("已收藏")
            self._hist_list.addItem(item)

    def update_vocab(self, words: list):
        self._vocab_set = {w.lower() for w in words}
        self._vocab_list.clear()
        for w in words:
            self._vocab_list.addItem(QListWidgetItem(w))


class MainWindow(QMainWindow):
    def __init__(self, search_engine, tts_service, db_module):
        super().__init__()
        self.engine = search_engine
        self.tts = tts_service
        self.db = db_module
        self._search_thread = None
        self.setWindowTitle("LogiDict v1.2.7 — 物流外贸词典")
        self.setMinimumSize(720, 560)
        self.resize(860, 620)
        qss_path = (os.path.join(sys._MEIPASS, "styles.qss")
                if getattr(sys, "frozen", False)
                else os.path.join(BASE_DIR, "styles.qss"))
        if os.path.exists(qss_path):
            with open(qss_path, encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_side()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        search_bar = QWidget()
        search_bar.setObjectName("SearchBar")
        search_bar.setFixedHeight(56)
        sb_lay = QHBoxLayout(search_bar)
        sb_lay.setContentsMargins(16, 8, 16, 8)
        self._search_input = QLineEdit()
        self._search_input.setObjectName("SearchInput")
        self._search_input.setPlaceholderText("搜索单词 / Search")
        self._search_input.setMinimumHeight(36)
        self._search_input.returnPressed.connect(self._do_search)
        self._suggestion_panel = SuggestionPanel(self)
        self._suggestion_panel.word_selected.connect(self._on_suggestion_selected)
        self._search_input.textChanged.connect(self._update_suggestions)
        # 搜索框键盘事件：上下导航候选词
        self._search_input.installEventFilter(self)
        search_btn = QPushButton("搜索")
        search_btn.setObjectName("SearchBtn")
        search_btn.setFixedSize(64, 36)
        search_btn.clicked.connect(self._do_search)
        sb_lay.addWidget(self._search_input)
        sb_lay.addWidget(search_btn)
        root.addWidget(search_bar)
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)
        self._side = SidePanel()
        self._side.word_selected.connect(self.search)
        self._side.history_deleted.connect(self._delete_history)
        body_lay.addWidget(self._side)
        div = QFrame()
        div.setObjectName("VertDiv")
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFixedWidth(1)
        body_lay.addWidget(div)
        self._result = ResultPanel(
            self.tts,
            on_add_vocab=self._add_vocab,
            on_remove_vocab=self._remove_vocab
        )
        body_lay.addWidget(self._result, 1)
        root.addWidget(body, 1)
        self._result.show_empty()

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("Alt+D"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Escape"), self, activated=self.hide)
        QShortcut(QKeySequence("Alt+S"), self,
                  activated=lambda: self.tts.speak(self._search_input.text()))

    def _focus_search(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self._search_input.setFocus()
        self._search_input.selectAll()

    def _update_suggestions(self, text):
        text = text.strip()
        if len(text) < 1:
            self._suggestion_panel.hide()
            return
        items = self.engine.suggest(text, limit=8)
        self._suggestion_panel.update_items(items, anchor_widget=self._search_input)

    def _on_suggestion_selected(self, word: str):
        self._search_input.blockSignals(True)
        self._search_input.setText(word)
        self._search_input.blockSignals(False)
        self.search(word)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self._search_input:
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key == Qt.Key.Key_Down:
                    word = self._suggestion_panel.navigate(1)
                    if word:
                        self._search_input.blockSignals(True)
                        self._search_input.setText(word)
                        self._search_input.blockSignals(False)
                    return True
                elif key == Qt.Key.Key_Up:
                    word = self._suggestion_panel.navigate(-1)
                    if word:
                        self._search_input.blockSignals(True)
                        self._search_input.setText(word)
                        self._search_input.blockSignals(False)
                    return True
                elif key == Qt.Key.Key_Escape:
                    self._suggestion_panel.hide()
                    return False
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._suggestion_panel.hide()
                    return False
            elif event.type() == QEvent.Type.FocusOut:
                # 延迟隐藏，避免点击面板时面板还未响应就消失
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(150, self._check_hide_suggestion)
        return super().eventFilter(obj, event)

    def _check_hide_suggestion(self):
        focused = QApplication.focusWidget()
        if focused is not self._search_input and focused is not self._suggestion_panel._list:
            self._suggestion_panel.hide()

    def _do_search(self):
        word = self._search_input.text().strip()
        if not word:
            return
        self.search(word)

    def search(self, word: str):
        word = word.strip()
        if not word:
            return
        self._search_input.setText(word)
        self._result.show_loading()
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
        self._search_thread = SearchThread(self.engine, word)
        self._search_thread.result_ready.connect(self._on_result)
        self._search_thread.start()

    def _on_result(self, result: dict):
        in_vocab = self.db.word_in_vocab(result.get("word", ""))
        self._result.show_result(result, in_vocab)
        self._refresh_side()

    def _add_vocab(self, word: str):
        self.db.add_word_to_vocab(word)
        self._refresh_side()

    def _remove_vocab(self, word: str):
        self.db.remove_word_from_vocab(word)
        self._refresh_side()

    def _delete_history(self, word: str):
        self.db.delete_history(word)
        self._refresh_side()

    def _refresh_side(self):
        hist = [r["query"] for r in self.db.get_history(20)]
        vocab = [r["word"] for r in self.db.get_vocab_book()]
        self._side.update_vocab(vocab)   # vocab first so _vocab_set is up-to-date
        self._side.update_history(hist)

    def bring_to_front(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        self._focus_search()
