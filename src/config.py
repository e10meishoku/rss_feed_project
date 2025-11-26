# src/config.py

FEEDS = [
    # --- 海外AIニュース (英語) ---
    {
        "name": "GitHub Changelog", 
        "url": "https://github.blog/changelog/feed/", 
        "lang": "en"
    },
    {
        "name": "OpenAI News", 
        "url": "https://openai.com/news/rss.xml", 
        "lang": "en"
    },
    {
        "name": "Google AI Blog", 
        "url": "https://blog.google/technology/ai/rss/", 
        "lang": "en"
    },
    
    # --- 日本の公式ブログ (日本語) ---
    {
        "name": "Google Japan Blog", 
        "url": "https://blog.google/intl/ja-jp/rss/", 
        "lang": "ja"
    },

    # --- 日本のテックトレンド (日本語) ---
    {
        "name": "Zenn Trends", 
        "url": "https://zenn.dev/feed", 
        "lang": "ja"
    },
    {
        "name": "Qiita Trends", 
        "url": "https://qiita.com/popular-items/feed", 
        "lang": "ja"
    },

    # --- 特定ワード監視 (日本語) ---
    {
        "name": "Zenn (Copilot)",
        "url": "https://zenn.dev/topics/githubcopilot/feed",
        "lang": "ja"
    },
    {
        "name": "Qiita (Copilot)",
        "url": "https://qiita.com/tags/githubcopilot/feed",
        "lang": "ja"
    }
]

# 生成されるファイルのパス
DB_PATH = "output/news_collector.db"
REPORT_HTML_PATH = f"output/report_{{date}}.html"