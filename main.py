import feedparser
import requests
import os
import time

# --- 設定 ---
RSS_URL = "https://www.nintendo.co.jp/rss/topics/index.xml"
LINE_NOTIFY_URL = "https://api.line.me/v2/bot/message/push"
LAST_FILE = "last_news.txt"
MAX_SEND_COUNT = 3  # 1回の実行で送る最大件数（LINE枠節約のため）

def send_line_message(item):
    """LINEにメッセージを送信する"""
    token = os.environ.get("LINE_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 読みやすくフォーマット
    message = f"【任天堂新着】\n\n{item.title}\n{item.link}"
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    res = requests.post(LINE_NOTIFY_URL, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"送信成功: {item.title}")
    else:
        print(f"送信失敗: {res.status_code} {res.text}")

def main():
    # 1. RSSを取得（User-Agentを設定してアクセス拒否を防止）
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.content)
    
    # 2. 記事を日付の古い順に並び替え
    # published_parsed が無い場合に備えて取得順も考慮
    entries = sorted(feed.entries, key=lambda x: x.get("published_parsed", 0))
    
    # 3. 前回の最終タイトルを読み込み
    last_title = ""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
    
    # 4. 新着記事を特定
    new_items = []
    found_last = (last_title == "") # 初回実行なら全て新着扱い
    
    for item in entries:
        if found_last:
            new_items.append(item)
        elif item.title == last_title:
            found_last = True
            
    if not new_items:
        print("新着記事はありませんでした。")
        return

    # 5. 送信（最大件数制限を適用）
    send_cnt = 0
    latest_processed_title = last_title
    
    for item in new_items:
        if send_cnt >= MAX_SEND_COUNT:
            print(f"送信上限({MAX_SEND_COUNT}件)に達したため、残りは次回に持ち越します。")
            break
            
        send_line_message(item)
        latest_processed_title = item.title
        send_cnt += 1
        time.sleep(1) # 連続送信による負荷軽減
    
    # 6. 最後に送信した記事のタイトルを保存
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(latest_processed_title)

if __name__ == "__main__":
    main()
