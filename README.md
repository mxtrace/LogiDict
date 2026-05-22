# LogiDict — 物流外贸词典

专为外贸物流从业者设计的桌面词典应用，支持FCL、海运、贸易术语的快速查询。

## 功能

- 🔍 本地词库搜索（125+ 专业术语）+ 在线补充
- 📋 全局热键：剪贴板搜索 / OCR 截图识别 / 悬浮翻译窗
- 🔊 TTS 发音（英美音标）
- ⭐ 词汇本收藏
- 🌙 暗色主题

## 技术栈

- Python 3.13 + PyQt6
- SQLite（本地词库）
- RapidOCR（ONNX，离线 OCR）
- PyInstaller（单文件打包）

## 项目结构

```
main.py              # 入口：启动/托盘/热键
main_window.py       # 主窗口 UI
floating_window.py   # 悬浮翻译窗
search_engine.py     # 搜索引擎（本地+在线）
database.py          # SQLite schema + 查询
ocr_service.py       # OCR 服务（RapidOCR 主，winrt 备）
tts_service.py       # 语音播报
hotkey_manager.py    # 全局热键
clipboard_monitor.py # 剪贴板监听
api_client.py        # 在线词典 API
seed_data.json       # 初始词库数据
styles.qss           # Qt 样式表（暗色主题）
logidict.ico         # 应用图标
logidict.spec        # PyInstaller 打包配置
```

## 打包

```bash
python -m PyInstaller logidict.spec --noconfirm
# 输出：dist/LogiDict.exe
```

## 版本历史

- **v1.2.5** — 修复图标显示；新增 CY_CUT / CV_CUT 词条
- **v1.2.4** — 修复搜索重影；修复普通词汇搜索；新增 SOP 术语 27 条
- **v1.2.3** — OCR 截图识别；RapidOCR 引擎集成
- **v1.2.0** — 悬浮翻译窗；全局热键；系统托盘
- **v1.0.0** — 初始版本：本地词库搜索 + TTS
