import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

# Supabaseへの接続設定
# バッチ処理なので、RLSを無視できる "SERVICE_ROLE_KEY" を使うのがポイント
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or Key is missing. Check your .env file.")

supabase: Client = create_client(url, key)

def init_db():
    """
    Supabaseではテーブル作成済みなので、この関数は何もしなくてOK。
    main.py との互換性のために残しています。
    """
    print("Database is managed by Supabase. Skipping local init.")

def get_or_create_source_id(name, feed_url, language):
    """ソースIDを取得、なければ作成"""
    try:
        # まず名前で検索
        response = supabase.table("sources").select("id").eq("name", name).execute()
        
        if response.data:
            return response.data[0]["id"]
        
        # なければ新規作成
        print(f"Adding new source: {name}")
        new_source = {
            "name": name, 
            "feed_url": feed_url, 
            "language": language
        }
        response = supabase.table("sources").insert(new_source).execute()
        return response.data[0]["id"]
        
    except Exception as e:
        print(f"Error in get_or_create_source_id: {e}")
        return None

def insert_article(source_id, title, link, summary, pub_date):
    """記事を保存（URL重複時は無視）"""
    if not source_id:
        return

    # タイムゾーン等の調整
    if pub_date is None:
        pub_date = datetime.now().isoformat()

    try:
        # 重複チェックはSupabase側の unique制約 に任せる
        # on_conflict="url" で重複時は何もしない設定
        data = {
            "source_id": source_id,
            "title": title,
            "url": link,
            "summary": summary, # ここは翻訳前の日本語要約（原文ママ）などが入る
            "published_at": pub_date,
            "collected_date": datetime.now().strftime('%Y-%m-%d')
        }
        
        # ignore_duplicates=True を指定して重複エラーを防ぐ
        supabase.table("articles").upsert(data, on_conflict="url", ignore_duplicates=True).execute()
        
    except Exception as e:
        # 重複エラーなどはここで握りつぶされることが多いが、ログに出す
        print(f"Error inserting article ({link}): {e}")

def get_untranslated_articles():
    """
    まだGemini処理が終わっていない記事を取得
    条件: translated_title が NULL のもの
    """
    try:
        # sourcesテーブルの情報も一緒に取得(join)する
        # 上限100件にしておく（Geminiのレート制限対策）
        response = supabase.table("articles") \
            .select("id, title, summary, sources(language)") \
            .is_("gemini_insight", "null") \
            .limit(100) \
            .execute()
            
        articles = []
        for item in response.data:
            # 使いやすい形に整形
            articles.append({
                "article_id": item["id"],
                "original_title": item["title"],
                "original_summary": item["summary"],
                "language": item["sources"]["language"]
            })
        return articles
        
    except Exception as e:
        print(f"Error fetching untranslated articles: {e}")
        return []

def update_translation(article_id, title, summary, explanation_json_str, insight, example):
    """Geminiの解析結果を保存"""
    try:
        # JSON文字列をPythonのリスト/辞書に戻す
        # SupabaseにはJSONB型としてデータ構造のまま渡す
        explanation_data = []
        if explanation_json_str:
            try:
                explanation_data = json.loads(explanation_json_str)
            except:
                pass

        data = {
            "gemini_insight": insight,
            "gemini_example": example,
            "gemini_explanation": explanation_data, # JSONBカラムへ
            # 翻訳タイトルなどは現状のカラム定義に合わせて保存
            # もしカラムを作っていなければ、SQLで追加するか、ここを削ってください
             "title": title, # 必要に応じて上書き
             "summary": summary # 必要に応じて上書き
        }
        
        supabase.table("articles").update(data).eq("id", article_id).execute()
        
    except Exception as e:
        print(f"Error updating article {article_id}: {e}")

def get_articles_for_today():
    """今日の記事を取得（HTML生成用ではなくデバッグ確認用として残す）"""
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        response = supabase.table("articles") \
            .select("*, sources(name, language)") \
            .eq("collected_date", today) \
            .execute()
        return response.data
    except Exception as e:
        print(e)
        return []