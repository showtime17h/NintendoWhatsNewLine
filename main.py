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

def send_flex_message(title, link, image_url, category_name):
    """LINEにFlex Messageを送る（カテゴリ名を受け取るように変更）"""
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
                # ここでカテゴリ名を表示するように変更
                {"type": "text", "text": category_name, "weight": "bold", "color": "#E60012", "size": "sm"},
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
            "altText": f"【{category_name}】{title}",
            "contents": flex_content
        }]
    }
    requests.post(url, headers=headers, json=payload)

def main():
    RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "text/xml,application/xml,application/xhtml+xml",
    }
    
    feed = None
    try:
        rss_res = requests.get(RSS_URL, headers=headers, timeout=15)
        if rss_res.status_code == 200:
            feed = feedparser.parse(rss_res.content)
    except Exception as e:
        print(f"エラー: {e}")

    if feed and feed.entries:
        entry = feed.entries[0]
        title = entry.title
        link = entry.link
        # RSSからカテゴリを取得。無い場合は "Nintendo News" にする
        category_name = entry.get('category', 'Nintendo News')
    else:
        # 直接解析（スクレイピング）の場合
        try:
            res = requests.get("https://www.nintendo.co.jp/news/index.html", headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            first_news = soup.find('a', class_='nc-c-newsCard')
            title = first_news.find('h3').get_text(strip=True)
            link = first_news['href']
            if not link.startswith('http'):
                link = "https://www.nintendo.co.jp" + link
            # スクレイピング時はカテゴリ取得が難しいため固定
            category_name = "Nintendo News"
        except:
            return

    # 前回のタイトル読み込み
    last_title = ""
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    # 自動運用モード：タイトルが違う時だけ送信
    if title != last_title: 
        image_url = get_article_image(link)
        # カテゴリ名を渡して送信
        send_flex_message(title, link, image_url, category_name)
        
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
