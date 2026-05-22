# -*- coding: utf-8 -*-
"""TTS 语音朗读：pyttsx3 封装，异步不阻塞 UI"""
import threading
import pyttsx3

class TTSService:
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        self._busy = False

    def _get_engine(self):
        """每个线程独立初始化引擎（pyttsx3 线程不安全）"""
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        # 优先选英语发音人
        for v in voices:
            if "english" in v.name.lower() or "en" in v.id.lower():
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 165)   # 语速
        engine.setProperty("volume", 0.9)
        return engine

    def speak(self, text: str, lang: str = "en"):
        """异步朗读；若正在朗读则跳过"""
        if self._busy:
            return
        t = threading.Thread(target=self._speak_worker, args=(text,), daemon=True)
        t.start()

    def _speak_worker(self, text: str):
        with self._lock:
            self._busy = True
            try:
                engine = self._get_engine()
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"[TTS] {e}")
            finally:
                self._busy = False

    def is_busy(self):
        return self._busy
