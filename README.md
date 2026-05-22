# LogiDict — 物流外贸词典

专为外贸物流从业者设计的桌面词典应用，支持 FCL、海运、贸易术语的快速查询。

## 功能

- 🔍 本地词库搜索（125+ 专业术语）+ 在线补充（含中文翻译）
- 📋 全局热键：剪贴板搜索 / OCR 截图识别 / 悬浮翻译窗
- ⚙️ 设置面板：取词功能可独立开关，默认关闭避免与其他程序快捷键冲突
- 🔊 TTS 发音（英美音标）
- ⭐ 词汇本收藏
- 🌙 暗色主题

## 快捷键

| 快捷键 | 功能 | 默认状态 |
|--------|------|----------|
| Alt+D | 呼出主窗口 | 始终启用 |
| Alt+Q | 截图 OCR 取词 | 默认关闭，可在设置中开启 |
| 双击 Ctrl+C | 复制取词 | 默认关闭，可在设置中开启 |

## 技术栈

- Python 3.13 + PyQt6
- SQLite（本地词库 + 在线结果缓存）
- RapidOCR（ONNX，离线 OCR）
- PyInstaller（单文件打包，无需安装 Python）

## 项目结构

```
main.py              # 入口：启动/托盘/热键
main_window.py       # 主窗口 UI
floating_window.py   # 悬浮翻译窗
search_engine.py     # 搜索引擎（本地+在线）
database.py          # SQLite schema + 查询 + 自动迁移
ocr_service.py       # OCR 服务（RapidOCR 主，winrt 备）
tts_service.py       # 语音播报
hotkey_manager.py    # 全局热键（支持动态开关）
clipboard_monitor.py # 剪贴板监听（支持动态开关）
settings.py          # 应用设置读写（%APPDATA%/LogiDict/settings.json）
api_client.py        # 在线词典 API + 翻译（MyMemory / Google 备用）
seed_data.json       # 初始词库数据（125 条）
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

- **v1.2.7** — 新增设置面板（取词/复制取词默认关闭，可独立开关）；修复打包版闪退（数据库列名迁移 + examples 表缺失）
- **v1.2.6** — 修复英文搜索无中文翻译；在线缓存 schema 自动迁移；翻译新增 Google Translate 备用
- **v1.2.5** — 修复任务栏/标题栏图标不显示；新增 CY_CUT / CV_CUT 词条
- **v1.2.4** — 修复搜索结果重影；修复普通词汇无法搜到；新增 SOP 专业术语 27 条
- **v1.2.3** — OCR 截图识别（RapidOCR ONNX 引擎，离线可用）
- **v1.2.0** — 悬浮翻译窗；全局热键；系统托盘
- **v1.0.0** — 初始版本：本地词库搜索 + TTS 发音
