import os
import sys
from datetime import datetime
import time

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 新しい database.py から関数をインポート
# init_db は実質何もしませんが互換性のため残しています
from src.database import init_db, get_untranslated_articles, update_translation
from src.feed_parser import fetch_all_feeds
from src.translator import get_translation_and_explanation

def step_1_init():
    print("--- [Step 1/3] Database Check ---")
    init_db() # Supabase接続確認用
    print("---------------------------------\n")

def step_2_fetch_articles():
    print("--- [Step 2/3] Fetching RSS Feeds ---")
    fetch_all_feeds() # ここでSupabaseに記事がINSERTされます
    print("---------------------------------------\n")

def step_3_translate_articles():
    print("--- [Step 3/3] Analyzing Articles via Gemini ---")
    
    # Supabaseから未処理記事を取得
    untranslated = get_untranslated_articles()
    
    if not untranslated:
        print("No new articles to process.")
        print("------------------------------------------------\n")
        return

    print(f"Found {len(untranslated)} new articles to process.")
    
    REQUEST_INTERVAL = 5
    
    for i, article in enumerate(untranslated):
        if i > 0:
            print(f"Waiting for {REQUEST_INTERVAL} seconds to respect API rate limits...")
            time.sleep(REQUEST_INTERVAL)

        # 記事の言語情報を取得
        target_lang = article["language"]
        article_id = article["article_id"]

        print(f"Processing ID: {article_id} ({article['original_title'][:30]}...)")

        # Gemini APIを呼び出し
        result = get_translation_and_explanation(
            article["original_title"], 
            article["original_summary"],
            language=target_lang
        )
        
        if result:
            # 解説リストをJSON文字列に変換 (translator.pyの戻り値によっては不要だが念のため)
            import json
            explanation_data = result.get("gemini_explanation", [])
            # 万が一文字列で返ってきてしまった場合の安全策
            if isinstance(explanation_data, str):
                 explanation_json_str = explanation_data
            else:
                 explanation_json_str = json.dumps(explanation_data, ensure_ascii=False)

            update_translation(
                article_id,
                str(result.get("translated_title", "処理エラー")),
                str(result.get("translated_summary", "要約エラー")),
                explanation_json_str, 
                str(result.get("gemini_insight", "")),
                str(result.get("gemini_example", ""))
            )
            print(f"Successfully processed.")
        else:
            print(f"Failed to process article ID: {article_id}")
            
    print("------------------------------------------------\n")

def main():
    start_time = datetime.now()
    print(f"Process started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 3ステップ実行 (レポート生成は削除)
    step_1_init()
    step_2_fetch_articles()
    step_3_translate_articles()
    
    end_time = datetime.now()
    print(f"Process finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()