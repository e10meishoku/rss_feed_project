import feedparser
from bs4 import BeautifulSoup
from .config import FEEDS
from .database import get_or_create_source_id, insert_article
import time
from datetime import datetime, timedelta

def clean_html(html_content):
    """概要欄のHTMLタグを除去してプレーンテキストにする"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text().strip()

def parse_published_date(entry):
    """公開日時を 'YYYY-MM-DD HH:MM:SS' 形式の文字列に変換"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
    return None

def fetch_all_feeds():
    """config.pyのすべてのフィードを取得し、DBに保存"""
    print("Fetching feeds...")
    
    # 3日前より新しい記事のみを処理対象とする
    cutoff_date = datetime.now() - timedelta(days=4) 
    
    # ブラウザのふりをするためのUser-Agentを設定
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

    for i, feed_info in enumerate(FEEDS):
        # 2つ目以降のフィード取得の前に5秒休む (アクセス制限対策)
        if i > 0:
            print("Waiting 5 seconds before next request...")
            time.sleep(5)

        name = feed_info["name"]
        url = feed_info["url"]
        lang = feed_info["lang"]
        
        print(f"\nProcessing: {name} ({url})")
        
        source_id = get_or_create_source_id(name, url, lang)
        
        feed = feedparser.parse(url, agent=USER_AGENT)
        
        if feed.bozo:
            print(f"WARNING: Failed to parse feed {name}.")
            # エラーが出ても一部取得できている場合があるため続行を試みるが、致命的な場合はスキップされる可能性がある
            # print(f"Error detail: {feed.bozo_exception}")
            
        skipped_count = 0 
        for entry in feed.entries:
            
            try:
                pub_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                if pub_dt.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                    skipped_count += 1
                    continue
            except (AttributeError, TypeError, ValueError):
                pass

            title = entry.title
            link = entry.link
            
            # ▼▼▼ 概要/本文の取得ロジックを強化 (Qiita/Zenn対応) ▼▼▼
            summary_raw = ""
            # 1. RSSの standard 'summary'
            if 'summary' in entry:
                summary_raw = entry.summary
            # 2. Atomフィード (Qiitaなど) の 'content'
            elif 'content' in entry and len(entry.content) > 0:
                summary_raw = entry.content[0].value
            # 3. RSSの 'description' (fallback)
            elif 'description' in entry:
                summary_raw = entry.description
            
            summary_clean = clean_html(summary_raw)
            
            # DB容量節約のため、あまりに長い場合はカット（Geminiにはこれでも十分伝わる）
            if len(summary_clean) > 3000:
                summary_clean = summary_clean[:3000] + "..."

            pub_date_str = parse_published_date(entry)

            insert_article(source_id, title, link, summary_clean, pub_date_str)
            
        print(f"Finished processing {name}. Found {len(feed.entries)} entries. (Skipped {skipped_count} old entries)")
    
    print("\nAll feeds processed.")