import sqlite3
from .config import DB_PATH
from datetime import datetime

def get_db_connection():
    """DB接続を取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """データベースのテーブルを初期化（作成）する"""
    sql_create_sources_table = """
    CREATE TABLE IF NOT EXISTS sources (
        source_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        feed_url TEXT NOT NULL,
        language TEXT NOT NULL
    );
    """
    
    sql_create_articles_table = """
    CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        original_title TEXT NOT NULL,
        original_url TEXT NOT NULL UNIQUE,
        original_summary TEXT,
        published_date DATETIME,
        fetched_at DATETIME NOT NULL,
        translated_title TEXT,
        translated_summary TEXT,
        gemini_explanation TEXT,
        gemini_insight TEXT,
        gemini_example TEXT,
        FOREIGN KEY (source_id) REFERENCES sources (source_id)
    );
    """
    
    with get_db_connection() as conn:
        conn.execute(sql_create_sources_table)
        conn.execute(sql_create_articles_table)
        print("Database initialized.")

def get_or_create_source_id(name, feed_url, language):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT source_id FROM sources WHERE name = ?", (name,))
        data = cursor.fetchone()
        
        if data:
            return data["source_id"]
        else:
            cursor.execute(
                "INSERT INTO sources (name, feed_url, language) VALUES (?, ?, ?)",
                (name, feed_url, language)
            )
            conn.commit()
            print(f"New source added: {name}")
            return cursor.lastrowid

def insert_article(source_id, title, url, summary, pub_date):
    fetched_at = datetime.now()
    sql = """
    INSERT OR IGNORE INTO articles (
        source_id, original_title, original_url, original_summary, 
        published_date, fetched_at
    ) VALUES (?, ?, ?, ?, ?, ?);
    """
    try:
        with get_db_connection() as conn:
            conn.execute(sql, (source_id, title, url, summary, pub_date, fetched_at))
            conn.commit()
    except Exception as e:
        print(f"Error inserting article: {e} (URL: {url})")

def get_untranslated_articles():
    """
    まだ処理（翻訳・解説生成）が行われていない記事を取得する。
    一度の処理数は多めに150件設定。
    """
    sql = """
    SELECT 
        a.article_id, 
        a.original_title, 
        a.original_summary,
        s.language
    FROM articles a
    JOIN sources s ON a.source_id = s.source_id
    WHERE a.translated_title IS NULL
    LIMIT 150;
    """
    with get_db_connection() as conn:
        return conn.execute(sql).fetchall()

def update_translation(article_id, title, summary, explanation, insight, example):
    """翻訳・解説結果をDBに更新する"""
    sql = """
    UPDATE articles
    SET translated_title = ?, 
        translated_summary = ?, 
        gemini_explanation = ?,
        gemini_insight = ?,
        gemini_example = ?
    WHERE article_id = ?;
    """
    with get_db_connection() as conn:
        conn.execute(sql, (title, summary, explanation, insight, example, article_id))
        conn.commit()

def get_articles_for_today():
    """
    今日の記事を取得する。
    表示順序を以下の優先度で固定する:
    1. Google (AI Blog, Japan Blog等)
    2. OpenAI
    3. GitHub
    4. Zenn Trends
    5. Zenn (Copilot)
    6. Qiita Trends
    7. Qiita (Copilot)
    """
    sql = """
    SELECT 
        s.name AS source_name,
        s.language,
        a.*
    FROM articles a
    JOIN sources s ON a.source_id = s.source_id
    WHERE date(a.fetched_at) = date('now', 'localtime')
    ORDER BY 
        CASE 
            WHEN s.name LIKE '%Google%' THEN 1
            WHEN s.name LIKE '%OpenAI%' THEN 2
            WHEN s.name LIKE '%GitHub%' THEN 3
            WHEN s.name = 'Zenn Trends' THEN 4
            WHEN s.name = 'Zenn (Copilot)' THEN 5
            WHEN s.name = 'Qiita Trends' THEN 6
            WHEN s.name = 'Qiita (Copilot)' THEN 7
            ELSE 8
        END ASC,
        a.published_date DESC;
    """
    with get_db_connection() as conn:
        return conn.execute(sql).fetchall()