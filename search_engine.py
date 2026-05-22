# -*- coding: utf-8 -*-
# search_engine.py: 本地词库优先，联网 API 兜底，统一数据格式
import threading
from database import (search_local, get_word_detail, add_history,
                      get_online_cache, set_online_cache, suggest_with_def,
                      _is_chinese, persist_online_word)
from api_client import fetch_online


def normalize_db_result(raw: dict) -> dict:
    """将数据库原始格式转换为 UI 标准格式"""
    if not raw:
        return {}
    defs = []
    for d in raw.get("definitions", []):
        defs.append({
            "pos": d.get("pos", ""),
            "def_cn": d.get("def_cn", ""),
            "def_en": d.get("def_en", ""),
            "example_en": d.get("example_en", ""),
            "example_cn": d.get("example_cn", ""),
            "domain": d.get("domain", ""),
            "is_pro": d.get("is_professional", 0),
            "order": d.get("sort_order", 0),
        })
    pro = None
    p = raw.get("professional")
    if p:
        pro = {
            "abbrev": p.get("abbrev", ""),
            "full_form": p.get("full_form", ""),
            "domain": p.get("domain", ""),
            "pro_def_cn": p.get("pro_def_cn", ""),
            "pro_def_en": p.get("pro_def_en", ""),
            "biz_example_1": p.get("biz_example_1", ""),
            "biz_example_2": p.get("biz_example_2", ""),
            "related": p.get("related_terms", ""),
            "tags": p.get("tags", ""),
        }
    return {
        "word": raw.get("word", ""),
        "phonetic_uk": raw.get("phonetic_uk", ""),
        "phonetic_us": raw.get("phonetic_us", ""),
        "pos": raw.get("pos", ""),
        "defs": defs,
        "pro": pro,
    }


class SearchEngine:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def search(self, word: str, callback=None):
        """同步搜索返回 dict；提供 callback 则异步执行"""
        word = word.strip()
        if not word:
            return None
        if callback:
            t = threading.Thread(target=self._search_async, args=(word, callback), daemon=True)
            t.start()
            return None
        return self._do_search(word)

    def _search_async(self, word, callback):
        result = self._do_search(word)
        callback(result)

    def _do_search(self, word: str):
        with self._lock:
            if word in self._cache:
                return self._cache[word]

        # 1. 本地搜索（中文输入直接走这条路，不走在线 API）
        hits = search_local(word)
        # 只接受精确匹配（忽略大小写）；模糊命中（如搜 purpose 匹配 general purpose）
        # 不作为主结果，继续走在线 API
        if hits and hits[0].get("word", "").lower() != word.lower():
            hits = []
        if hits:
            word_id = hits[0].get("id")
            raw = get_word_detail(word_id) if word_id else None
            if raw:
                result = normalize_db_result(raw)
                result["source"] = "local"
                # 中文搜索时附带匹配的查询词，供 UI 提示
                if _is_chinese(word):
                    result["cn_query"] = word
            else:
                result = {"word": hits[0]["word"], "defs": [], "pro": None, "source": "local"}
        elif _is_chinese(word):
            # 中文查询，本地无结果 → 直接返回未找到（word="" 触发"未找到结果"显示）
            result = {"word": "", "defs": [], "pro": None, "source": "not_found",
                      "cn_query": word}
        else:
            # 英文查询：检查 SQLite 在线缓存，再调 API
            cached = get_online_cache(word)
            if cached:
                result = cached
                result["source"] = "online"
                # 如果缓存存在但未写入 words 表（旧数据或异常），补充写入
                persist_online_word(word, result)
            else:
                result = fetch_online(word)
                result["source"] = "online" if result.get("defs") else "not_found"
                if result.get("defs"):
                    set_online_cache(word, result)
                    persist_online_word(word, result)  # 写入 words/defs 表，支持中文反查

        if result.get("word"):
            add_history(result["word"])
            with self._lock:
                self._cache[word] = result
        return result

    def suggest(self, prefix: str, limit: int = 8):
        """返回带中文简义的候选词列表，供 SuggestionPanel 使用。
        中文 prefix 时返回匹配的英文词条列表。
        """
        return suggest_with_def(prefix, limit=limit)

    def clear_cache(self):
        with self._lock:
            self._cache.clear()
