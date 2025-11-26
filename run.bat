@echo off

rem ▼▼▼ 文字化け対策：コマンドプロンプトの文字コードをUTF-8に変更します ▼▼▼
chcp 65001 > nul

echo ====================================
echo  RSSフィードコレクターを起動します... (venv仮想環境)
echo ====================================

REM PC本体のPythonではなく、
REM このプロジェクト専用の仮想環境(.venv)内のPythonを直接指定して実行します
.\.venv\Scripts\python.exe src/main.py

echo.
echo ====================================
echo  処理が完了しました。
echo ====================================
echo.

rem --- ▼▼▼ ここからが追加部分です ▼▼▼ ---

rem 1. 今日の日付を YYYY-MM-DD 形式で取得します
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set datetime=%%I
set YYYY=%datetime:~0,4%
set MM=%datetime:~4,2%
set DD=%datetime:~6,2%
set TODAY=%YYYY%-%MM%-%DD%

rem 2. 今日のレポートファイルへのパスを組み立てます
set REPORT_FILE=output\report_%TODAY%.html

rem 3. ファイルが存在するか確認してから開きます
if exist "%REPORT_FILE%" (
    echo %TODAY% のレポートファイルを開きます...
    rem startコマンドでデフォルトのブラウザでファイルを開きます
    start "" "%REPORT_FILE%"
) else (
    echo %TODAY% のレポートファイルが見つかりませんでした。
)

rem --- ▲▲▲ 追加部分はここまでです ▲▲▲ ---

echo.
pause