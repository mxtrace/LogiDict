# -*- coding: utf-8 -*-
# OCR 服务：截取鼠标附近区域，识别文字
# 主引擎：RapidOCR (PaddleOCR ONNX)，后台初始化+预热，不阻塞启动
# 备用：Windows OCR (winrt)
import threading
import os
import ctypes
import re
import tempfile

try:
    import mss
    import mss.tools
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import numpy as np
    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR as _RapidOCR
    _RAPID_AVAILABLE = True
except ImportError:
    _RAPID_AVAILABLE = False

try:
    import winrt.windows.media.ocr as _winrt_ocr
    import winrt.windows.graphics.imaging as _winrt_img
    import winrt.windows.storage as _winrt_storage
    _WINRT_AVAILABLE = True
except ImportError:
    _WINRT_AVAILABLE = False

_REGION_W     = 400
_REGION_H     = 90
_CURSOR_OFF_X = 200
_CURSOR_OFF_Y = 45
_SCALE        = 2


class OCRService:
    def __init__(self):
        self._busy   = threading.Lock()
        self._engine = None
        self._winrt  = None
        self._mode   = "none"
        self._ready  = threading.Event()   # 初始化+预热完成后 set

        if _RAPID_AVAILABLE and _MSS_AVAILABLE and _PIL_AVAILABLE and _NP_AVAILABLE:
            self._mode = "rapid"
            # 全部在后台线程完成，主线程立即返回
            threading.Thread(target=self._init_rapid, daemon=True).start()

        elif _WINRT_AVAILABLE and _MSS_AVAILABLE:
            threading.Thread(target=self._init_winrt, daemon=True).start()

        else:
            self._ready.set()   # 无引擎可用，直接就绪（空操作）
            print("[OCR] 所有引擎不可用")

    # ─── 后台初始化 ───────────────────────────────────────────────────────────

    def _init_rapid(self):
        try:
            self._engine = _RapidOCR(text_cls=False)
            # 预热：消除首次推理的 JIT 编译开销
            dummy = np.zeros((180, 800, 3), dtype=np.uint8)
            self._engine(dummy)
            print("[OCR] RapidOCR 就绪（已预热）")
        except Exception as e:
            print(f"[OCR] RapidOCR 初始化失败: {e}")
            self._mode = "none"
        finally:
            self._ready.set()

    def _init_winrt(self):
        try:
            import winrt.windows.globalization as _wgl
            engine = _winrt_ocr.OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                lang = _wgl.Language("en-US")
                engine = _winrt_ocr.OcrEngine.try_create_from_language(lang)
            self._winrt = engine
            self._mode  = "winrt"
            print("[OCR] Windows OCR 就绪（备用）")
        except Exception as e:
            print(f"[OCR] Windows OCR 初始化失败: {e}")
            self._mode = "none"
        finally:
            self._ready.set()

    # ─── 公共接口 ────────────────────────────────────────────────────────────

    @property
    def available(self):
        return _MSS_AVAILABLE and (self._mode != "none" or not self._ready.is_set())

    def capture_and_recognize(self, callback=None):
        if not _MSS_AVAILABLE:
            if callback: callback("")
            return
        if not self._busy.acquire(blocking=False):
            return
        threading.Thread(target=self._worker, args=(callback,), daemon=True).start()

    def _worker(self, callback):
        try:
            # 等待初始化完成（最多 15s；通常 app 启动后 3-4s 内完成）
            if not self._ready.wait(timeout=15):
                print("[OCR] 引擎初始化超时")
                if callback: callback("")
                return
            if self._mode == "none":
                if callback: callback("")
                return

            x, y = self._get_cursor_pos()
            region = {
                "left":   max(0, x - _CURSOR_OFF_X),
                "top":    max(0, y - _CURSOR_OFF_Y),
                "width":  _REGION_W, "height": _REGION_H,
            }
            with mss.MSS() as sct:
                shot = sct.grab(region)

            img = Image.frombytes("RGB", shot.size, shot.rgb)
            img = img.resize((img.width * _SCALE, img.height * _SCALE), Image.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(1.8)
            img = ImageEnhance.Sharpness(img).enhance(1.5)
            cursor_in_img = (_CURSOR_OFF_X * _SCALE, _CURSOR_OFF_Y * _SCALE)

            if self._mode == "rapid":
                word = self._recognize_rapid(img, cursor_in_img)
            else:
                word = self._recognize_winrt(img, cursor_in_img)

            if callback: callback(word)
        except Exception as e:
            print(f"[OCR] {e}")
            if callback: callback("")
        finally:
            self._busy.release()

    # ─── RapidOCR ────────────────────────────────────────────────────────────

    def _recognize_rapid(self, img_pil, cursor_xy):
        img_np = np.array(img_pil)
        result, _ = self._engine(img_np)
        if not result:
            return ""
        cx, cy = cursor_xy
        words = []
        for item in result:
            pts   = item[0]
            text  = item[1].strip()
            score = float(item[2]) if len(item) > 2 else 0.0
            if not text or score < 0.3:
                continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            bx, by = min(xs), min(ys)
            bw, bh = max(xs) - bx, max(ys) - by
            PAD_X = max(8, int(bw * 0.1))
            PAD_Y = max(8, int(bh * 0.4))
            words.append({
                "text":  text,
                "x": bx - PAD_X, "y": by - PAD_Y,
                "w": bw + PAD_X*2, "h": bh + PAD_Y*2,
                "cx": bx + bw/2,  "cy": by + bh/2,
                "score": score,
            })
        return self._pick_best_word(words, cx, cy)

    # ─── Windows OCR（备用） ──────────────────────────────────────────────────

    def _recognize_winrt(self, img_pil, cursor_xy):
        import asyncio
        tmp = os.path.join(tempfile.gettempdir(), "logidict_ocr_tmp.png")
        img_pil.save(tmp)
        try:
            word = asyncio.run(self._winrt_async(tmp, cursor_xy))
        finally:
            try: os.remove(tmp)
            except: pass
        return word

    async def _winrt_async(self, img_path, cursor_xy):
        try:
            sf      = await _winrt_storage.StorageFile.get_file_from_path_async(os.path.abspath(img_path))
            stream  = await sf.open_async(_winrt_storage.FileAccessMode.READ)
            decoder = await _winrt_img.BitmapDecoder.create_async(stream)
            bitmap  = await decoder.get_software_bitmap_async()
            result  = await self._winrt.recognize_async(bitmap)
            if not result: return ""
            cx, cy = cursor_xy
            words  = []
            for line in result.lines:
                for w in line.words:
                    r = w.bounding_rect
                    PAD_X = max(6, int(r.width  * 0.15))
                    PAD_Y = max(6, int(r.height * 0.40))
                    words.append({
                        "text":  w.text.strip(),
                        "x": r.x-PAD_X, "y": r.y-PAD_Y,
                        "w": r.width+PAD_X*2, "h": r.height+PAD_Y*2,
                        "cx": r.x+r.width/2, "cy": r.y+r.height/2,
                        "score": 1.0,
                    })
            return self._pick_best_word(words, cx, cy)
        except Exception as e:
            print(f"[OCR-winrt] {e}")
            return ""

    # ─── 共用：选取光标下最近词 ──────────────────────────────────────────────

    def _pick_best_word(self, words, cx, cy):
        if not words:
            return ""
        # 优先：bbox 包含光标
        best = None
        for w in words:
            if (w["x"] <= cx <= w["x"]+w["w"] and w["y"] <= cy <= w["y"]+w["h"]):
                best = w; break
        # 退而求其次：最近中心点
        if not best:
            best = min(words, key=lambda w: (w["cx"]-cx)**2 + (w["cy"]-cy)**2)

        word = best["text"]

        # 多词块取光标最近词
        if " " in word:
            tokens = word.split()
            best_tok, best_dist = tokens[0], float("inf")
            offset = 0
            for tok in tokens:
                tok_cx = best["x"] + best["w"] * (offset + len(tok)/2) / max(len(word), 1)
                if abs(tok_cx - cx) < best_dist:
                    best_dist = abs(tok_cx - cx)
                    best_tok  = tok
                offset += len(tok) + 1
            word = best_tok

        cleaned = re.sub(r"[^A-Za-z0-9/\-'.]", "", word)
        if len(cleaned) >= 2 and not cleaned.isdigit():
            return cleaned
        if any("\u4e00" <= c <= "\u9fff" for c in word):
            return word
        return cleaned if len(cleaned) >= 1 else ""

    def _get_cursor_pos(self):
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
