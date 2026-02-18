import feedparser
import requests
import os
import time
import json
from bs4 import BeautifulSoup

# --- 設定 ---
RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
LINE_NOTIFY_URL = "https://api.line.me/v2/bot/message/push"
LAST_FILE = "last_news.txt"
MAX_SEND_COUNT = 3 

def get_article_image(url):
    """記事のURLからOGP画像をスクレイピングする"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        # og:imageタグを探す
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image["content"]
    except:
        pass
    # 取得失敗時はデフォルト画像
    return "https://www.nintendo.co.jp/common/img/header/logo_nintendo.png"

def send_flex_message(item):
    token = os.environ.get("LINE_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    
    # 記事ごとの画像をスクレイピングで取得
    image_url = get_article_image(item.link)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Flex MessageのJSON構造
    flex_contents = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Nintendo News", "weight": "bold", "color": "#e60012", "size": "sm"},
                {"type": "text", "text": item.title, "weight": "bold", "size": "md", "wrap": True, "margin": "md"},
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
                    "action": {"type": "uri", "label": "詳しく見る", "uri": item.link}
                }
            ]
        }
    }

    payload = {
        "to": user_id,
        "messages": [{"type": "flex", "altText": item.title, "contents": flex_contents}]
    }
    
    requests.post(LINE_NOTIFY_URL, headers=headers, data=json.dumps(payload))

def main():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.content)
    
    # 時系列ソート（古い順）
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
        time.sleep(2) # スクレイピングの負荷軽減のため少し待機
    
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(latest_title)

if __name__ == "__main__":
    main()
