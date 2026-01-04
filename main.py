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
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    
    flex_content = {
        "type": "bubble",
        "hero": {
            "type": "image", "url": image_url, "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": category_name, "weight": "bold", "color": "#E60012", "size": "sm"},
                {"type": "text", "text": title, "weight": "bold", "size": "xl", "wrap": True, "margin": "md"},
                {"type": "separator", "margin": "xxl"},
                {"type": "button", "action": {"type": "uri", "label": "記事を読む", "uri": link}, "style": "primary", "color": "#E60012", "margin": "md"}
            ]
        }
    }

    payload = {
        "to": USER_ID,
        "messages": [{"type": "flex", "altText": f"【{category_name}】{title}", "contents": flex_content}]
    }
    requests.post(url, headers=headers, json=payload)

def main():
    RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    
    # 前回の最新記事タイトルを読み込む
    last_title = ""
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    entries_to_send = []
    
    try:
        rss_res = requests.get(RSS_URL, headers=headers, timeout=15)
        feed = feedparser.parse(rss_res.content)
        
        # 取得した記事を上から順番に確認
        for entry in feed.entries:
            if entry.title == last_title:
                break # 前回の最新記事にぶつかったら、そこから先は送信済みなので終了
            
            entries_to_send.append({
                "title": entry.title,
                "link": entry.link,
                "category": entry.get('category', 'Nintendo News')
            })
    except Exception as e:
        print(f"RSS取得エラー: {e}")
        return

    # 新しい記事があった場合（古い順に送るためリストを逆順にする）
    if entries_to_send:
        for item in reversed(entries_to_send):
            print(f"送信中: {item['title']}")
            img = get_article_image(item['link'])
            send_flex_message(item['title'], item['link'], img, item['category'])
            time.sleep(1) # 連続送信による負荷軽減
        
        # 一番新しい記事のタイトルを保存
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(entries_to_send[0]['title'])
    else:
        print("新着記事はありませんでした。")

if __name__ == "__main__":
    main()
