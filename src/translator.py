import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file.")

genai.configure(api_key=API_KEY)

generation_config = {
  "temperature": 0.4,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite-preview-09-2025",
    generation_config=generation_config,
    safety_settings=safety_settings
)

def get_translation_and_explanation(original_title, original_summary, language="en"):
    """
    記事のタイトルと概要を受け取り、Geminiで処理してJSONを返す。
    language='ja' の場合は翻訳をスキップし、考察のみ生成する。
    """
    print(f"Analyzing ({language}): {original_title[:40]}...")
    
    # 言語に応じてプロンプトを切り替える
    if language == "ja":
        # --- 日本語記事用プロンプト（修正：トンマナ合わせ） ---
        prompt = f"""
        あなたはIT・AI分野の専門コンサルタントです。
        以下の日本語の技術記事（概要）を読み、ビジネスパーソンやエンジニアに向けた
        「考察」「ユースケース」「用語解説」を作成してください。
        元の文章が日本語なので翻訳は不要です。

        【入力情報】
        タイトル: {original_title}
        概要: {original_summary}

        【出力項目（JSON）】
        1. translated_title: (文字列) 入力されたタイトルをそのまま出力してください。
        
        2. translated_summary: (文字列) 
           概要を読みやすく簡潔な「です・ます」調の日本語で要約してください。
           箇条書きや改行は使用せず、1つの段落（100〜150文字程度）にまとめてください。
           英語記事の要約スタイルに合わせてください。

        3. gemini_insight: (文字列) 【考察】この記事の技術が業界に与える影響や、エンジニアにとってのメリットを専門家の視点で解説してください。
        4. gemini_example: (文字列) 【具体例】この技術や知見が実際にどう役立つか、具体的な利用シーンを記述してください。
        5. gemini_explanation: (文字列のリスト配列) 
           【用語解説】記事に出てくる専門用語について、
           ["用語A: 解説A", "用語B: 解説B"] の形式のリストで出力してください。
           
        ---
        厳格なJSON形式で出力してください:
        {{
          "translated_title": "...",
          "translated_summary": "...",
          "gemini_insight": "...",
          "gemini_example": "...",
          "gemini_explanation": ["...", "..."] 
        }}
        """
    else:
        # --- 英語記事用プロンプト ---
        prompt = f"""
        あなたはIT・AI分野の専門コンサルタントです。
        以下の英語ニュース記事について、日本のビジネスパーソンやエンジニアに向けて
        有益な情報を提供するためのJSONを作成してください。

        【入力情報】
        タイトル: {original_title}
        概要: {original_summary}

        【出力項目（JSON）】
        1. translated_title: (文字列) タイトルを自然な日本語に翻訳してください。
        2. translated_summary: (文字列) 概要を「です・ます」調で簡潔に翻訳してください。
        3. gemini_insight: (文字列) 【考察】業界への影響や背景を論理的な文章で記述してください。
        4. gemini_example: (文字列) 【具体例】具体的なユースケースを記述してください。
        5. gemini_explanation: (文字列のリスト配列) 
           【用語解説】記事に出てくる専門用語や前提知識を、
           ["用語A: 解説A", "用語B: 解説B"] という形式のリスト配列で出力してください。
           
        ---
        厳格なJSON形式で出力してください:
        {{
          "translated_title": "...",
          "translated_summary": "...",
          "gemini_insight": "...",
          "gemini_example": "...",
          "gemini_explanation": ["...", "..."] 
        }}
        """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}')
            
            if start_index != -1 and end_index != -1:
                json_string = raw_text[start_index : end_index + 1]
                response_json = json.loads(json_string)
                
                if not isinstance(response_json.get("gemini_explanation"), list):
                    response_json["gemini_explanation"] = []
                
                return response_json
            else:
                raise ValueError(f"Failed to extract JSON from API response.")

        except Exception as e:
            print(f"!!! Gemini API Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = 3
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("!!! All retry attempts failed.")
                return None
    return None