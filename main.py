import feedparser
import requests
import os
from bs4 import BeautifulSoup
import time

# 設定
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("USER_ID")

def get_article_image(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image["content"]
    except:
        pass
    return "https://www.nintendo.co.jp/common/img/i/icon_nintendo.png"

def send_flex_message(title, link, image_url):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    
    flex_content = {
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
                {"type": "text", "text": "Nintendo Topics", "weight": "bold", "color": "#E60012", "size": "sm"},
                {"type": "text", "text": title, "weight": "bold", "size": "xl", "wrap": True, "margin": "md"},
                {"type": "separator", "margin": "xxl"},
                {"type": "button", "action": {"type": "uri", "label": "記事を読む", "uri": link}, "style": "primary", "color": "#E60012", "margin": "md"}
            ]
        }
    }

    payload = {
        "to": USER_ID,
        "messages": [{
            "type": "flex",
            "altText": f"新着：{title}",
            "contents": flex_content
        }]
    }
    requests.post(url, headers=headers, json=payload)

def main():
    RSS_URL = "https://www.nintendo.co.jp/data/rss/topics.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    
    # 3回までリトライする
    feed = None
    for i in range(3):
        try:
            rss_res = requests.get(RSS_URL, headers=headers, timeout=10)
            feed = feedparser.parse(rss_res.content)
            if feed.entries:
                break
            time.sleep(2) # 失敗したら2秒待つ
        except:
            continue
    
    if not feed or not feed.entries:
        print("RSSの取得に失敗しました。")
        return

    entry = feed.entries[0]
    title = entry.title
    link = entry.link

    # 重複チェック（通常運用に戻す）
    last_title = ""
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    # 今回はテストなので「!=」ではなく「True」にして、実際のニュースが届くか最終確認してください
    if True: 
        image_url = get_article_image(link)
        send_flex_message(title, link, image_url)
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
