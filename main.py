import feedparser
import requests
import os
import time

# --- 設定 ---
RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
LINE_NOTIFY_URL = "https://api.line.me/v2/bot/message/push"
LAST_FILE = "last_news.txt"
MAX_SEND_COUNT = 3 

def send_line_message(item):
    """LINEに任天堂風のフォーマットで送信する"""
    token = os.environ.get("LINE_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 🌟 任天堂トピックス風のUIデザイン
    message = (
        f"┏━━━━━━━━━━━━┓\n"
        f" 🔴 Nintendo Topics \n"
        f"┗━━━━━━━━━━━━┛\n\n"
        f"【新着】\n"
        f"{item.title}\n\n"
        f"▼ 詳しくはこちら\n"
        f"{item.link}"
    )
    
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    
    res = requests.post(LINE_NOTIFY_URL, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"送信成功: {item.title}")
    else:
        print(f"送信失敗: {res.status_code}")

def main():
    # 1. 正しいURLで取得
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.content)
    
    # 2. 古い順にソート（時系列を正す）
    entries = sorted(feed.entries, key=lambda x: x.get("published_parsed", 0))
    
    # 3. 既読タイトルの読み込み
    last_title = ""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
    
    # 4. 未送信の記事をピックアップ
    new_items = []
    found_last = (last_title == "")
    for item in entries:
        if found_last:
            new_items.append(item)
        elif item.title == last_title:
            found_last = True
            
    if not new_items:
        print("新着記事はありませんでした。")
        return

    # 5. 送信（最大3件まで）
    send_cnt = 0
    latest_processed_title = last_title
    for item in new_items:
        if send_cnt >= MAX_SEND_COUNT:
            break
        send_line_message(item)
        latest_processed_title = item.title
        send_cnt += 1
        time.sleep(1) 
    
    # 6. 保存
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(latest_processed_title)

if __name__ == "__main__":
    main()
