# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

block_cipher = None

winrt_hiddenimports = collect_submodules("winrt")
pyttsx3_hiddenimports = collect_submodules("pyttsx3")
rapidocr_hiddenimports = collect_submodules("rapidocr_onnxruntime")
# 收集 RapidOCR 包内所有数据文件（含 models/*.onnx 和 config.yaml）
rapidocr_datas, rapidocr_binaries, rapidocr_hidden2 = collect_all("rapidocr_onnxruntime")

a = Analysis(
    [r"C:\Users\miaoyua\Documents\LogiDict\main.py"],
    pathex=[r"C:\Users\miaoyua\Documents\LogiDict"],
    binaries=rapidocr_binaries + [
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_foundation.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_foundation_collections.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_globalization.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_graphics_imaging.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_media_ocr.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_storage.cp313-win_amd64.pyd", r"winrt"),
    (r"C:/Users/miaoyua/AppData/Roaming\Python\Python313\site-packages\winrt\_winrt_windows_storage_streams.cp313-win_amd64.pyd", r"winrt")
    ],
    datas=rapidocr_datas + [
        (r"C:\Users\miaoyua\Documents\LogiDict\styles.qss",      "."),
        (r"C:\Users\miaoyua\Documents\LogiDict\seed_data.json",   "."),
    ],
    hiddenimports=(
        winrt_hiddenimports + pyttsx3_hiddenimports +
        rapidocr_hiddenimports + rapidocr_hidden2 + [
        "winrt", "winrt.windows", "winrt.windows.media", "winrt.windows.media.ocr",
        "winrt.windows.graphics", "winrt.windows.graphics.imaging",
        "winrt.windows.storage", "winrt.windows.storage.streams",
        "winrt.windows.foundation", "winrt.windows.foundation.collections",
        "winrt.windows.globalization",
        "winrt.runtime",
        "pyttsx3.drivers", "pyttsx3.drivers.sapi5",
        "sqlite3", "keyboard", "pyperclip", "mss", "requests",
        "PIL", "PIL.Image", "PIL.ImageEnhance",
        "win32com", "win32com.client",
        "comtypes", "comtypes.client",
        "rapidocr_onnxruntime",
        "onnxruntime", "onnxruntime.capi",
        "numpy", "numpy.core", "numpy.core._multiarray_umath",
        "cv2", "shapely", "pyclipper",
    ]),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "scipy", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LogiDict",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r"C:\Users\miaoyua\Documents\LogiDict\logidict.ico",
    version_file=None,
)
