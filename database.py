# -*- coding: utf-8 -*-
"""数据库模块：SQLite 词库 Schema + 查询接口"""
import sqlite3, os, json, sys


def _get_data_dir() -> str:
    """用户数据目录：开发时用项目目录，打包后用 %APPDATA%/LogiDict"""
    if getattr(sys, "frozen", False):
        d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "LogiDict")
        os.makedirs(d, exist_ok=True)
        return d
    return os.path.dirname(os.path.abspath(__file__))


def _get_resource(filename: str) -> str:
    """获取只读捆绑资源路径（seed_data.json / styles.qss）"""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


DB_PATH = os.path.join(_get_data_dir(), "logidict.db")
DATA_DIR = _get_data_dir()


def _is_chinese(text: str) -> bool:
    """判断字符串是否包含中文字符"""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def init_db():
    conn = get_conn(); c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL, phonetic_uk TEXT, phonetic_us TEXT,
            pos TEXT, cn_keywords TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_word ON words(word);
        CREATE TABLE IF NOT EXISTS definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
            pos TEXT, def_cn TEXT, def_en TEXT,
            example_en TEXT, example_cn TEXT,
            domain TEXT DEFAULT 'general',
            is_pro INTEGER DEFAULT 0, sort_order INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS pro_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
            abbrev TEXT, full_form TEXT, domain TEXT,
            pro_def_cn TEXT, pro_def_en TEXT,
            biz_example_1 TEXT, biz_example_2 TEXT,
            related_terms TEXT, tags TEXT);
        CREATE TABLE IF NOT EXISTS vocab_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER REFERENCES words(id),
            word TEXT NOT NULL, note TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_vocab ON vocab_book(word_id);
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL, word_id INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    # 迁移：旧版列名 part_of_speech -> 新版 pos
    try:
        conn.execute("ALTER TABLE words RENAME COLUMN part_of_speech TO pos")
        conn.commit()
    except Exception:
        pass
    # 迁移：旧版列名 display_order -> 新版 sort_order
    try:
        conn.execute("ALTER TABLE definitions RENAME COLUMN display_order TO sort_order")
        conn.commit()
    except Exception:
        pass
    # 迁移：旧版表名 professional_terms -> 新版 pro_cards（重建方式）
    try:
        conn.execute("ALTER TABLE professional_terms RENAME TO pro_cards")
        conn.commit()
    except Exception:
        pass
    # 数据库迁移：旧版没有 cn_keywords 列，安全补充
    try:
        conn.execute("ALTER TABLE words ADD COLUMN cn_keywords TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # 列已存在，忽略
    # 迁移：旧版列名 is_professional -> is_pro
    try:
        conn.execute("ALTER TABLE definitions RENAME COLUMN is_professional TO is_pro")
        conn.commit()
    except Exception:
        pass
    # 迁移：旧版 definitions 缺少 example_en/example_cn 列
    for col in ("example_en", "example_cn"):
        try:
            conn.execute(f"ALTER TABLE definitions ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass
    # 迁移：旧版 definitions 缺少 example_en/example_cn 列
    for _col in ("example_en", "example_cn"):
        try:
            conn.execute(f"ALTER TABLE definitions ADD COLUMN {_col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass
    # 确保在线缓存表存在（兼容重建场景）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS online_cache (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            word     TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            data_json TEXT   NOT NULL,
            cached_at TEXT   DEFAULT (datetime('now'))
        )
    """)
    conn.commit(); conn.close()


def seed_database():
    """从 seed_data.json 导入词库种子数据（支持 cn_keywords 字段）。"""
    json_path = _get_resource("seed_data.json")
    if not os.path.exists(json_path):
        return 0
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    conn = get_conn(); c = conn.cursor()
    count = 0
    for item in data:
        c.execute("SELECT id FROM words WHERE lower(word)=lower(?)", (item['word'],))
        existing = c.fetchone()
        cn_kw = item.get('cn_keywords', '')
        if existing:
            # 更新已有词条的 cn_keywords（支持重新 seed 时补充中文关键词）
            c.execute("UPDATE words SET cn_keywords=? WHERE id=?", (cn_kw, existing['id']))
            continue
        c.execute(
            "INSERT INTO words (word,phonetic_uk,phonetic_us,pos,cn_keywords) VALUES (?,?,?,?,?)",
            (item['word'], item.get('phonetic_uk',''), item.get('phonetic_us',''),
             item.get('pos',''), cn_kw)
        )
        wid = c.lastrowid
        for d in item.get('defs', []):
            c.execute(
                "INSERT INTO definitions (word_id,pos,def_cn,def_en,example_en,example_cn,domain,is_pro,sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (wid, d.get('pos',''), d.get('def_cn',''), d.get('def_en',''),
                 d.get('example_en',''), d.get('example_cn',''),
                 d.get('domain','general'), d.get('is_pro',0), d.get('order',0))
            )
        pro = item.get('pro')
        if pro:
            c.execute(
                "INSERT INTO pro_cards (word_id,abbrev,full_form,domain,pro_def_cn,pro_def_en,biz_example_1,biz_example_2,related_terms,tags) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (wid, pro.get('abbrev',''), pro.get('full_form',''), pro.get('domain',''),
                 pro.get('pro_def_cn',''), pro.get('pro_def_en',''),
                 pro.get('biz_example_1',''), pro.get('biz_example_2',''),
                 pro.get('related',''), pro.get('tags',''))
            )
        count += 1
    conn.commit(); conn.close()
    return count


def search_local(query: str, limit: int = 10):
    """三级本地搜索。中文输入时匹配 cn_keywords 和 def_cn；英文时匹配 word。"""
    q = query.strip()
    if not q:
        return []
    conn = get_conn(); c = conn.cursor()

    if _is_chinese(q):
        # 中文搜索：JOIN definitions，同时搜 cn_keywords 和 def_cn
        sql = """
            SELECT DISTINCT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                            w.pos, w.cn_keywords
            FROM words w
            LEFT JOIN definitions d ON d.word_id = w.id
            WHERE w.cn_keywords LIKE ?
               OR d.def_cn LIKE ?
            ORDER BY
                CASE WHEN w.cn_keywords LIKE ? THEN 0 ELSE 1 END,
                length(w.word)
            LIMIT ?
        """
        pat = '%' + q + '%'
        prefix_pat = q + '%'
        rows = c.execute(sql, (pat, pat, prefix_pat, limit)).fetchall()
        results = [dict(r) for r in rows]
    else:
        ql = q.lower()
        c.execute("SELECT id,word,phonetic_uk,phonetic_us,pos FROM words WHERE lower(word)=? LIMIT ?", (ql, limit))
        results = [dict(r) for r in c.fetchall()]
        if not results:
            c.execute("SELECT id,word,phonetic_uk,phonetic_us,pos FROM words WHERE lower(word) LIKE ? LIMIT ?", (ql+'%', limit))
            results = [dict(r) for r in c.fetchall()]
        if len(results) < 3:
            c.execute("SELECT id,word,phonetic_uk,phonetic_us,pos FROM words WHERE lower(word) LIKE ? AND lower(word) NOT LIKE ? LIMIT ?",
                      ('%'+ql+'%', ql+'%', limit))
            ids = {r['id'] for r in results}
            for r in c.fetchall():
                if r['id'] not in ids:
                    results.append(dict(r))

    conn.close()
    return results[:limit]


def get_word_detail(word_id: int):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM words WHERE id=?", (word_id,))
    row = c.fetchone()
    if not row:
        return None
    word = dict(row)
    c.execute("SELECT * FROM definitions WHERE word_id=? ORDER BY sort_order", (word_id,))
    word['definitions'] = [dict(r) for r in c.fetchall()]
    c.execute("SELECT * FROM pro_cards WHERE word_id=?", (word_id,))
    pro = c.fetchone()
    word['professional'] = dict(pro) if pro else None
    conn.close()
    return word


def add_to_vocab(word_id, word, note=''):
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO vocab_book (word_id,word,note) VALUES (?,?,?)", (word_id, word, note))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def remove_from_vocab(word_id):
    conn = get_conn()
    conn.execute("DELETE FROM vocab_book WHERE word_id=?", (word_id,))
    conn.commit(); conn.close()


def is_in_vocab(word_id) -> bool:
    conn = get_conn()
    r = conn.execute("SELECT 1 FROM vocab_book WHERE word_id=?", (word_id,)).fetchone()
    conn.close()
    return r is not None


def get_vocab_book():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM vocab_book ORDER BY added_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_history(query, word_id=None):
    conn = get_conn()
    conn.execute("INSERT INTO history (query,word_id) VALUES (?,?)", (query, word_id))
    conn.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY searched_at DESC LIMIT 500)")
    conn.commit(); conn.close()


def get_history(limit=30):
    conn = get_conn()
    rows = conn.execute(
        "SELECT query, MAX(searched_at) as t FROM history GROUP BY query ORDER BY t DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == '__main__':
    init_db(); n = seed_database()
    print(f'初始化完成，写入 {n} 个词条')


# ─── Word-string based helpers for UI layer ───
def word_in_vocab(word: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM vocab_book WHERE LOWER(word)=LOWER(?)", (word,)
    ).fetchone()
    conn.close()
    return row is not None

def add_word_to_vocab(word: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM words WHERE LOWER(word)=LOWER(?)", (word,)
    ).fetchone()
    word_id = row["id"] if row else None
    try:
        conn.execute(
            "INSERT OR IGNORE INTO vocab_book (word_id, word) VALUES (?,?)",
            (word_id, word)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def remove_word_from_vocab(word: str) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM vocab_book WHERE LOWER(word)=LOWER(?)", (word,))
    conn.commit()
    conn.close()
    return True


def delete_history(query: str) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM history WHERE LOWER(query)=LOWER(?)", (query,))
    conn.commit()
    conn.close()
    return True

def clear_history() -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return True


# ─── Online result cache（联网查词结果持久缓存）───
def init_online_cache():
    conn = get_conn()
    # 迁移旧 schema（旧表无 data_json 列）：直接删除重建，缓存数据丢失无影响
    cols = [r[1] for r in conn.execute("PRAGMA table_info(online_cache)")]
    if cols and "data_json" not in cols:
        conn.execute("DROP TABLE online_cache")
        print("[DB] online_cache 旧 schema 已迁移")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS online_cache (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            word      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            data_json TEXT    NOT NULL,
            cached_at TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def clean_stale_online_cache():
    """清理 online_cache 中所有 def_cn 全为空的旧缓存（无翻译数据，需重新查询）"""
    import json as _json
    conn = get_conn()
    rows = conn.execute("SELECT word, data_json FROM online_cache").fetchall()
    to_del = []
    for word, dj in rows:
        try:
            d = _json.loads(dj)
            defs = d.get("defs", [])
            if defs and all(not df.get("def_cn", "").strip() for df in defs):
                to_del.append(word)
        except Exception:
            to_del.append(word)
    for w in to_del:
        conn.execute("DELETE FROM online_cache WHERE LOWER(word)=LOWER(?)", (w,))
    if to_del:
        print(f"[DB] 清理无翻译旧缓存 {len(to_del)} 条: {to_del}")
    conn.commit()
    conn.close()


def get_online_cache(word: str):
    import json
    conn = get_conn()
    row = conn.execute(
        "SELECT data_json FROM online_cache WHERE LOWER(word)=LOWER(?)", (word,)
    ).fetchone()
    conn.close()
    return json.loads(row["data_json"]) if row else None

def set_online_cache(word: str, data: dict):
    import json
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO online_cache (word, data_json) VALUES (?, ?)",
        (word, json.dumps(data, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

def persist_online_word(word: str, data: dict):
    """将在线查词结果持久化到 words/definitions 表，使其支持中文反查。
    若该词已存在则跳过（不覆盖本地词库数据）。
    """
    if not word or not data.get("defs"):
        return
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM words WHERE lower(word)=lower(?)", (word,))
    if c.fetchone():
        conn.close()
        return  # 已存在，不覆盖
    c.execute(
        "INSERT INTO words (word, phonetic_uk, phonetic_us, pos, cn_keywords) VALUES (?,?,?,?,?)",
        (data.get("word", word),
         data.get("phonetic_uk", ""),
         data.get("phonetic_us", ""),
         data.get("pos", ""),
         "")  # 在线词无预设中文关键词
    )
    wid = c.lastrowid
    for i, d in enumerate(data.get("defs", [])):
        c.execute(
            "INSERT INTO definitions (word_id,pos,def_cn,def_en,example_en,example_cn,domain,is_pro,sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
            (wid, d.get("pos",""), d.get("def_cn",""), d.get("def_en",""),
             d.get("example_en",""), d.get("example_cn",""),
             d.get("domain","general"), d.get("is_pro",0), i)
        )
        # 例句直接写入 definitions 表的 example_en/example_cn 列
    conn.commit(); conn.close()


def suggest_with_def(query: str, limit: int = 8) -> list:
    """返回带简短中文释义的候选词，用于搜索下拉面板。
    英文：优先级 精确 > 前缀 > 包含。
    中文：匹配 cn_keywords 或 def_cn，返回对应英文词条。
    """
    q = query.strip()
    if not q:
        return []
    conn = get_conn()

    if _is_chinese(q):
        sql = """
            SELECT DISTINCT w.word, w.pos,
                   COALESCE(d.def_cn, '') AS def_cn,
                   COALESCE(p.full_form, '') AS full_form
            FROM words w
            LEFT JOIN definitions d ON d.word_id = w.id AND d.sort_order = 0
            LEFT JOIN pro_cards p ON p.word_id = w.id
            WHERE w.cn_keywords LIKE ?
               OR d.def_cn LIKE ?
            ORDER BY
                CASE WHEN w.cn_keywords LIKE ? THEN 0 ELSE 1 END,
                length(w.word)
            LIMIT ?
        """
        pat = '%' + q + '%'
        prefix_pat = q + '%'
        rows = conn.execute(sql, (pat, pat, prefix_pat, limit)).fetchall()
    else:
        ql = q.lower()
        sql = """
            SELECT w.word, w.pos,
                   COALESCE(d.def_cn, '') AS def_cn,
                   COALESCE(p.full_form, '') AS full_form
            FROM words w
            LEFT JOIN definitions d ON d.word_id = w.id AND d.sort_order = 0
            LEFT JOIN pro_cards p ON p.word_id = w.id
            WHERE lower(w.word) LIKE ?
            ORDER BY
                CASE WHEN lower(w.word) = ?          THEN 0
                     WHEN lower(w.word) LIKE ?        THEN 1
                     ELSE                                  2 END,
                length(w.word)
            LIMIT ?
        """
        rows = conn.execute(sql, (f"%{ql}%", ql, f"{ql}%", limit)).fetchall()

    conn.close()
    return [dict(r) for r in rows]
