import os
import sys
from datetime import datetime
import time
import re
import json

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_untranslated_articles, update_translation, get_articles_for_today
from src.feed_parser import fetch_all_feeds
from src.translator import get_translation_and_explanation
from src.config import REPORT_HTML_PATH

def step_1_init_database():
    print("--- [Step 1/4] Initializing Database ---")
    init_db()
    print("------------------------------------------\n")

def step_2_fetch_articles():
    print("--- [Step 2/4] Fetching RSS Feeds ---")
    fetch_all_feeds()
    print("---------------------------------------\n")

def step_3_translate_articles():
    print("--- [Step 3/4] Analyzing Articles via Gemini ---")
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

        # DBから取得した言語情報を渡す
        target_lang = article["language"]

        result = get_translation_and_explanation(
            article["original_title"], 
            article["original_summary"],
            language=target_lang
        )
        
        if result:
            explanation_json = json.dumps(result.get("gemini_explanation", []), ensure_ascii=False)

            update_translation(
                article["article_id"],
                str(result.get("translated_title", "処理エラー")),
                str(result.get("translated_summary", "要約エラー")),
                explanation_json, 
                str(result.get("gemini_insight", "")),
                str(result.get("gemini_example", ""))
            )
            print(f"Successfully processed: {result.get('translated_title')}")
        else:
            print(f"Failed to process article ID: {article['article_id']}")
            
    print("------------------------------------------------\n")

def get_source_style(source_name):
    """ソース名に応じたグラデーションとアイコン文字"""
    name_lower = source_name.lower()
    
    if "google" in name_lower:
        return "linear-gradient(135deg, #4285F4 0% 25%, #EA4335 25% 50%, #FBBC05 50% 75%, #34A853 75% 100%)", "G"
    elif "openai" in name_lower:
        return "linear-gradient(135deg, #10a37f, #007c66)", "O"
    elif "github" in name_lower:
        return "linear-gradient(135deg, #24292e, #6e7681)", "GH"
    elif "hugging" in name_lower:
        return "linear-gradient(135deg, #FFD000, #FF9D00)", "HF"
    elif "anthropic" in name_lower or "claude" in name_lower:
        return "linear-gradient(135deg, #d97757, #f2ccc2)", "An"
    
    # ▼▼▼ Zenn/Qiita用の色設定 ▼▼▼
    elif "zenn" in name_lower:
        return "linear-gradient(135deg, #3ea8ff, #007bb6)", "Zn"
    elif "qiita" in name_lower:
        return "linear-gradient(135deg, #55c500, #2da600)", "Qi"
        
    else:
        initial = source_name[:1].upper() if source_name else "?"
        return "linear-gradient(135deg, #6c757d, #adb5bd)", initial

def step_4_generate_report():
    print("--- [Step 4/4] Generating Today's HTML Report ---")
    articles = get_articles_for_today()
    
    if not articles:
        print("No new articles found today.")
        print("--------------------------------------------------\n")
        return

    today_str = datetime.now().strftime('%Y-%m-%d')
    display_date = datetime.now().strftime('%Y年%m月%d日')
    html_path = REPORT_HTML_PATH.format(date=today_str)

    # CSSスタイル定義
    css_styles = """
        /* リセットと基本設定 */
        :root {
            --bg-color: #f4f6f8;
            --card-bg: #ffffff;
            --text-main: #333;
            --text-sub: #666;
            --primary-color: #1a73e8;
        }
        body {
            font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-main);
            background-image: radial-gradient(#dce0e3 1px, transparent 1px);
            background-size: 20px 20px;
        }

        /* ヘッダー */
        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
        }
        header h1 {
            color: #1a237e;
            margin: 0 0 10px 0;
            font-size: 2.2em;
        }
        header .date-info {
            background-color: #fff;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            color: var(--text-sub);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-weight: bold;
        }

        /* グリッドレイアウト */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
            max-width: 1200px;
            margin: 0 auto;
        }

        /* 記事カード */
        .article-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            cursor: pointer;
            border: 1px solid transparent;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: rgba(26, 115, 232, 0.3);
        }

        /* カードヘッダー */
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .card-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
            margin-right: 12px;
            flex-shrink: 0;
        }
        .card-meta {
            display: flex;
            flex-direction: column;
            font-size: 0.8em;
            color: var(--text-sub);
        }
        .source-name {
            font-weight: bold;
            color: #444;
        }

        /* カードタイトルと概要 */
        .card-title {
            font-size: 1.15em;
            margin: 0 0 10px 0;
            line-height: 1.4;
            color: #202124;
            font-weight: bold;
        }
        .card-summary {
            font-size: 0.9em;
            color: #5f6368;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 15px;
        }
        .read-more-btn {
            margin-top: auto;
            align-self: flex-start;
            font-size: 0.85em;
            color: var(--primary-color);
            font-weight: bold;
            background: rgba(26, 115, 232, 0.08);
            padding: 5px 12px;
            border-radius: 4px;
        }

        /* モーダル */
        dialog {
            border: none;
            border-radius: 16px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.25);
            max-width: 800px;
            width: 90%;
            padding: 0;
            background: #fff;
            color: #333;
            max-height: 90vh;
        }
        dialog::backdrop {
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(2px);
        }
        .modal-content-wrapper {
            padding: 40px;
            overflow-y: auto;
            max-height: 85vh;
        }
        
        .close-btn {
            position: absolute;
            top: 15px;
            right: 20px;
            background: #f1f3f4;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            font-size: 1.2em;
            cursor: pointer;
            color: #555;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .close-btn:hover { background: #e0e0e0; }

        .modal-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .modal-icon {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.8em;
            margin-right: 20px;
            text-shadow: 0 1px 3px rgba(0,0,0,0.3);
            flex-shrink: 0;
        }
        .modal-title h2 {
            margin: 0 0 5px 0;
            font-size: 1.6em;
            line-height: 1.3;
        }
        .modal-meta {
            color: #777;
            font-size: 0.9em;
        }

        .insight-section {
            background-color: #f0f7ff;
            border-left: 5px solid #1a73e8;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
        }
        .insight-title {
            color: #1a73e8;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
        }
        .example-section {
            background-color: #fff8e1;
            border-left: 5px solid #ffa000;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .example-title {
            color: #e65100;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
        }
        
        .glossary-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px dashed #ddd;
        }
        .glossary-chip {
            background: #fff;
            border: 1px solid #ddd;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            color: #555;
            display: flex;
            align-items: center;
        }

        /* 原文リンクのスタイル修正 */
        .original-link {
            display: inline-block;
            color: #1a73e8;
            text-decoration: none;
            font-weight: bold;
            font-size: 0.95em;
        }
        .original-link:hover { text-decoration: underline; }
        .original-link-container {
            margin: 15px 0 25px 0; /* 概要と考察の間にスペース */
        }

        @media (max-width: 600px) {
            .grid-container { grid-template-columns: 1fr; }
            .modal-content-wrapper { padding: 25px; }
            .modal-header { flex-direction: column; align-items: flex-start; }
            .modal-icon { margin-bottom: 15px; }
        }
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI News Dashboard ({today_str})</title>
        <style>{css_styles}</style>
    </head>
    <body>
        <header>
            <h1>Daily Tech Insights</h1>
            <span class="date-info">{display_date} | {len(articles)} Updates</span>
        </header>

        <div class="grid-container">
    """

    dialog_contents = {}

    for index, article in enumerate(articles):
        source_name = article["source_name"]
        lang = article["language"]
        url = article["original_url"]
        pub_date = article["published_date"] or "---"
        
        bg_gradient, icon_text = get_source_style(source_name)

        def nl2br(text):
            if not text: return ""
            return text.replace('\n', '<br>')

        if lang == 'ja':
            # 日本語記事も翻訳済みのフィールド(translated_title等)に
            # 整形されたテキストが入っているため、そちらを優先的に使う
            title = article["translated_title"] or article["original_title"]
            summary = nl2br(article["translated_summary"] or article["original_summary"])
            
            # 考察などのフィールドは共通
            insight_html = ""
            example_html = ""
            glossary_html = ""
        else:
            title = article["translated_title"] or article["original_title"]
            summary = nl2br(article["translated_summary"])
            insight_html = ""
            example_html = ""
            glossary_html = ""
            
        # 考察のHTML生成
        if article["gemini_insight"]:
            insight_html = f"""
            <div class="insight-section">
                <div class="insight-title">🧠 考察・ビジネスへの影響</div>
                {nl2br(article["gemini_insight"])}
            </div>
            """

        # 具体例のHTML生成
        if article["gemini_example"]:
            example_html = f"""
            <div class="example-section">
                <div class="example-title">💡 具体的な例・ユースケース</div>
                {nl2br(article["gemini_example"])}
            </div>
            """

        # 用語解説のHTML生成
        explanation_str = article["gemini_explanation"]
        try:
            expl_list = json.loads(explanation_str) if explanation_str else []
            if isinstance(expl_list, list) and expl_list:
                items = ""
                for item in expl_list:
                        clean_item = re.sub(r'^[\s・\-\*]+', '', str(item)).strip()
                        if clean_item:
                            items += f'<span class="glossary-chip">📘 {clean_item}</span>'
                if items:
                    glossary_html = f'<div class="glossary-wrap">{items}</div>'
        except:
            pass

        html_content += f"""
        <div class="article-card" onclick="openModal('modal-{index}')">
            <div class="card-header">
                <div class="card-icon" style="background: {bg_gradient};">{icon_text}</div>
                <div class="card-meta">
                    <span class="source-name">{source_name}</span>
                    <span>{pub_date}</span>
                </div>
            </div>
            <div class="card-title">{title}</div>
            <div class="card-summary">{summary}</div>
            <div class="read-more-btn">詳細を読む →</div>
        </div>
        """

        dialog_html = f"""
        <dialog id="modal-{index}">
            <button class="close-btn" onclick="closeModal('modal-{index}')">×</button>
            <div class="modal-content-wrapper">
                <div class="modal-header">
                    <div class="modal-icon" style="background: {bg_gradient};">{icon_text}</div>
                    <div class="modal-title">
                        <h2>{title}</h2>
                        <div class="modal-meta">{source_name} | {pub_date}</div>
                    </div>
                </div>
                
                <div style="font-size:1.1em; line-height:1.8;">
                    {summary}
                </div>
                
                <div class="original-link-container">
                    <a href="{url}" target="_blank" class="original-link">原文記事を開く ({source_name}) ↗</a>
                </div>

                {insight_html}
                {example_html}
                {glossary_html}

            </div>
        </dialog>
        """
        dialog_contents[index] = dialog_html

    html_content += "</div>"

    for idx in dialog_contents:
        html_content += dialog_contents[idx]

    html_content += """
    <script>
        function openModal(id) {
            const modal = document.getElementById(id);
            if (modal) {
                modal.showModal();
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.close();
                    }
                });
            }
        }
        function closeModal(id) {
            const modal = document.getElementById(id);
            if (modal) modal.close();
        }
    </script>
    </body>
    </html>
    """

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Report generated: {html_path}")
    print("--------------------------------------------------\n")

def main():
    start_time = datetime.now()
    print(f"Process started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    step_1_init_database()
    step_2_fetch_articles()
    step_3_translate_articles()
    step_4_generate_report()
    
    end_time = datetime.now()
    print(f"Process finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()