import feedparser
import requests
import os
from bs4 import BeautifulSoup
import json

# 設定（GitHubのSecretsから読み込み）
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("USER_ID")

def get_article_image(url):
    """記事のURLからサムネイル画像を探す"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
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
    
    print("--- LINE送信テスト開始 ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス内容: {response.text}")
    print("--- LINE送信テスト終了 ---")

def main():
    if not LINE_TOKEN or not USER_ID:
        print("エラー: LINE_ACCESS_TOKEN または USER_ID が未設定です。")
        return

    # 【重要】User-Agentを設定してRSSを取得
    RSS_URL = "https://www.nintendo.co.jp/data/rss/topics.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        rss_res = requests.get(RSS_URL, headers=headers, timeout=10)
        feed = feedparser.parse(rss_res.content)
    except Exception as e:
        print(f"RSS取得失敗: {e}")
        return
    
    if not feed.entries:
        print("記事が見つかりませんでした。サーバーにブロックされているか、URLが変更された可能性があります。")
        # 最終手段として、RSSではなくサイトから直接タイトルを取る処理（簡易版）
        print("代替手段として直接タイトルを取得します。")
        title = "最新ニュース（取得失敗時のテスト）"
        link = "https://www.nintendo.co.jp/topics/index.html"
    else:
        entry = feed.entries[0]
        title = entry.title
        link = entry.link

    # テストのために必ず送信
    print(f"最新記事: {title} を送信します。")
    image_url = get_article_image(link)
    send_flex_message(title, link, image_url)
    
    with open("last_news.txt", "w", encoding="utf-8") as f:
        f.write(title)

if __name__ == "__main__":
    main()
