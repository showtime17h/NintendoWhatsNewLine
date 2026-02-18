import feedparser
import requests
import os
import time
import json

# --- 設定 ---
RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
LINE_NOTIFY_URL = "https://api.line.me/v2/bot/message/push"
LAST_FILE = "last_news.txt"
MAX_SEND_COUNT = 3 

def send_flex_message(item):
    """Flex Message形式で送信する"""
    token = os.environ.get("LINE_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    if not token or not user_id:
        print("Error: 設定が足りません。")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 🔴 Flex Messageの構造（任天堂風デザイン）
    flex_contents = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": "https://www.nintendo.co.jp/common/img/header/logo_nintendo.png", # 仮画像（任天堂ロゴ）
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Nintendo News", "weight": "bold", "color": "#e60012", "size": "sm"},
                {"type": "text", "text": item.title, "weight": "bold", "size": "xl", "wrap": True, "margin": "md"},
                {"type": "separator", "margin": "xxl"},
                {"type": "text", "text": "任天堂公式サイトで詳細をチェック", "size": "xs", "color": "#aaaaaa", "margin": "md"}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#e60012",
                    "action": {
                        "type": "uri",
                        "label": "記事を読む",
                        "uri": item.link
                    }
                }
            ]
        }
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "flex",
                "altText": f"【任天堂新着】{item.title}",
                "contents": flex_contents
            }
        ]
    }
    
    res = requests.post(LINE_NOTIFY_URL, headers=headers, data=json.dumps(payload))
    print(f"送信ステータス: {res.status_code}")

def main():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.content)
    
    # 時系列ソート
    entries = sorted(feed.entries, key=lambda x: x.get("published_parsed", 0))
    
    last_title = ""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
    
    new_items = []
    found_last = (last_title == "")
    for item in entries:
        if found_last:
            new_items.append(item)
        elif item.title == last_title:
            found_last = True
            
    if not new_items:
        print("新着なし")
        return

    send_cnt = 0
    latest_title = last_title
    for item in new_items:
        if send_cnt >= MAX_SEND_COUNT:
            break
        send_flex_message(item)
        latest_title = item.title
        send_cnt += 1
        time.sleep(1)
    
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(latest_title)

if __name__ == "__main__":
    main()
