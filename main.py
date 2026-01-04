import feedparser
import requests
import os
from bs4 import BeautifulSoup

# 設定（GitHubのSecretsから読み込み）
LINE_TOKEN = os.environ["LINE_ACCESS_TOKEN"]
USER_ID = os.environ["USER_ID"]

def get_article_image(url):
    """記事のURLからサムネイル画像を頑張って探す関数"""
    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        # OGP画像（SNS用画像）を探す
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image["content"]
    except:
        pass
    # 見つからない時の予備画像（任天堂のロゴなど）
    return "https://www.nintendo.co.jp/common/img/i/icon_nintendo.png"

def send_flex_message(title, link, image_url):
    """豪華な見た目のメッセージを送る本体"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    
    # Flex Messageの構造（JSON）
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
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        return

    entry = feed.entries[0]
    title = entry.title
    link = entry.link

    # 重複チェック
    last_title = ""
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    if title != last_title:
        # 画像を取得して送信
        image_url = get_article_image(link)
        send_flex_message(title, link, image_url)
        
        # タイトル保存
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
