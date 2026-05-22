# -*- coding: utf-8 -*-
# api_client.py: 联网查词 + 中文翻译
# 翻译：MyMemory API（无需 key，在公司网络可访问）
# 熔断机制：本次会话内连续失败超阈值后停止翻译尝试，直接显示英文
import requests
import concurrent.futures

_DICT_URL  = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
_MM_URL    = "https://api.mymemory.translated.net/get"
_GT_URL    = "https://translate.googleapis.com/translate_a/single"  # Google 免费备用
_TIMEOUT   = 5   # 字典 API 超时
_TIMEOUT_TR = 3  # 翻译超时（单条）

# ─── 翻译熔断器 ───────────────────────────────────────────────────────────────
# 连续失败 _FAIL_LIMIT 次后，本会话内停止翻译，直接显示英文（避免反复等待）
_fail_count = 0
_FAIL_LIMIT = 2
_disabled   = False


def _reset_circuit():
    """重置熔断器（可选：供测试或手动恢复）"""
    global _fail_count, _disabled
    _fail_count = 0
    _disabled   = False


def _record_fail():
    global _fail_count, _disabled
    _fail_count += 1
    if _fail_count >= _FAIL_LIMIT:
        _disabled = True
        print("[翻译] MyMemory 连续失败，本次会话停止翻译请求，仅显示英文原文。")


def _record_success():
    global _fail_count, _disabled
    _fail_count = 0   # 成功后重置计数


# ─── MyMemory 翻译 ────────────────────────────────────────────────────────────

def translate_batch(texts: list, target: str = "zh-CN") -> list:
    """批量翻译。MyMemory 并发逐条；熔断后直接返回空列表（显示英文兜底）。"""
    global _disabled
    if not texts:
        return []
    if _disabled:
        return [""] * len(texts)   # 熔断：跳过翻译，不等待

    non_empty = [(i, t) for i, t in enumerate(texts) if t.strip()]
    if not non_empty:
        return [""] * len(texts)

    results = [""] * len(texts)

    def _one(idx_text):
        idx, text = idx_text
        # 1. 先尝试 MyMemory
        try:
            r = requests.get(_MM_URL,
                params={"q": text, "langpair": f"en|{target}"},
                timeout=_TIMEOUT_TR)
            if r.status_code == 200:
                trans = r.json().get("responseData", {}).get("translatedText", "")
                if trans and "MYMEMORY WARNING" not in trans:
                    return idx, trans, True
        except Exception as e:
            print(f"[MyMemory] {e}")
        # 2. MyMemory 失败/限流 → 回退 Google Translate
        try:
            r = requests.get(_GT_URL,
                params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": text},
                timeout=_TIMEOUT_TR)
            if r.status_code == 200:
                data = r.json()
                parts = data[0] if data else []
                trans = "".join(p[0] for p in parts if p and p[0]) if parts else ""
                if trans:
                    return idx, trans, True
        except Exception as e:
            print(f"[GoogleTrans] {e}")
        return idx, "", False

    any_success = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for idx, trans, ok in pool.map(_one, non_empty):
            results[idx] = trans
            if ok:
                any_success = True

    if any_success:
        _record_success()
    else:
        _record_fail()

    return results


def translate_single(text: str, target: str = "zh-CN") -> str:
    results = translate_batch([text], target)
    return results[0] if results else ""


# ─── Free Dictionary API ──────────────────────────────────────────────────────

def fetch_online(word: str) -> dict:
    """查询单词，返回 UI 标准格式。defs 中每条含 def_cn（翻译成功时）。"""
    empty = {
        "word": word, "defs": [], "phonetic_uk": "", "phonetic_us": "",
        "pos": "", "pro": None, "source": "not_found"
    }
    try:
        r = requests.get(_DICT_URL.format(word=word.lower()), timeout=_TIMEOUT)
        if r.status_code != 200:
            cn = translate_single(word)
            if cn and cn.strip().lower() != word.strip().lower():
                return {
                    "word": word, "phonetic_uk": "", "phonetic_us": "",
                    "pos": "", "pro": None, "source": "online",
                    "defs": [{"pos": "", "def_cn": cn, "def_en": "",
                               "example_en": "", "example_cn": "",
                               "domain": "general", "is_pro": 0, "order": 0}],
                }
            return empty

        data = r.json()
        if not data or not isinstance(data, list):
            return empty

        entry = data[0]
        result = {
            "word":         entry.get("word", word),
            "phonetic_uk":  _pick_phonetic(entry, "uk"),
            "phonetic_us":  _pick_phonetic(entry, "us"),
            "pos": "", "defs": [], "pro": None, "source": "online",
        }

        raw_defs = []
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            if not result["pos"]:
                result["pos"] = pos
            for defi in meaning.get("definitions", [])[:3]:
                raw_defs.append({
                    "pos":        pos,
                    "def_en":     defi.get("definition", ""),
                    "example_en": defi.get("example", ""),
                    "domain":     "general",
                    "is_pro":     0,
                    "order":      len(raw_defs),
                })
        if not raw_defs:
            return empty

        # 批量翻译 def_en + example_en（熔断后立即返回空，不等待）
        to_translate = ([d["def_en"] for d in raw_defs] +
                        [d["example_en"] if d["example_en"] else "" for d in raw_defs])
        translations = translate_batch(to_translate)

        n = len(raw_defs)
        for i, d in enumerate(raw_defs):
            result["defs"].append({
                "pos":        d["pos"],
                "def_cn":     translations[i] if i < len(translations) else "",
                "def_en":     d["def_en"],
                "example_en": d["example_en"],
                "example_cn": (translations[n + i]
                               if (i < len(translations) - n and d["example_en"])
                               else ""),
                "domain":     d["domain"],
                "is_pro":     d["is_pro"],
                "order":      d["order"],
            })
        return result

    except Exception as e:
        print(f"[API] {e}")
        return empty


def _pick_phonetic(entry: dict, accent: str) -> str:
    for p in entry.get("phonetics", []):
        src  = p.get("sourceUrl", "").lower()
        text = p.get("text", "")
        if text:
            if accent == "uk" and "uk" in src:
                return text
            if accent == "us" and "us" in src:
                return text
    for p in entry.get("phonetics", []):
        if p.get("text"):
            return p["text"]
    return entry.get("phonetic", "")
