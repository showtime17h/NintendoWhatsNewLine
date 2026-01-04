import feedparser
import requests
import os
from bs4 import BeautifulSoup
import time

# 設定
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("USER_ID")

def get_article_image(url):
    """記事のURLからサムネイル画像を探す"""
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
    """LINEにFlex Messageを送る"""
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
                {"type": "text", "text": "Nintendo News", "weight": "bold", "color": "#E60012", "size": "sm"},
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
    # 教えていただいた正しいRSS URL
    RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "text/xml,application/xml,application/xhtml+xml",
    }
    
    feed = None
    try:
        print(f"RSS取得を試行中: {RSS_URL}")
        rss_res = requests.get(RSS_URL, headers=headers, timeout=15)
        if rss_res.status_code == 200:
            feed = feedparser.parse(rss_res.content)
    except Exception as e:
        print(f"エラー: {e}")

    if feed and feed.entries:
        print("RSS取得成功！")
        entry = feed.entries[0]
        title = entry.title
        link = entry.link
    else:
        # 万が一RSSがブロックされた場合の代替手段（ニュース一覧ページを解析）
        print("RSSが取得できなかったため、直接ページを解析します。")
        try:
            res = requests.get("https://www.nintendo.co.jp/news/index.html", headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 最初のニュースのリンクを取得（構造に合わせて調整）
            first_news = soup.find('a', class_='nc-c-newsCard')
            if not first_news:
                first_news = soup.select_one('.nc-c-newsCardList__item a')
                
            title = first_news.find('h3').get_text(strip=True)
            link = first_news['href']
            if not link.startswith('http'):
                link = "https://www.nintendo.co.jp" + link
        except Exception as e:
            print(f"最終手段も失敗しました: {e}")
            return

    # 重複チェック（テスト用にTrueにしています）
    if True: 
        print(f"送信内容: {title}")
        image_url = get_article_image(link)
        send_flex_message(title, link, image_url)
        
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
