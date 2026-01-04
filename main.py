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
    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image["content"]
    except:
        pass
    return "https://www.nintendo.co.jp/common/img/i/icon_nintendo.png"

def send_flex_message(title, link, image_url):
    """LINEにFlex Messageを送る（レスポンス確認付き）"""
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
    
    # 送信と結果の表示
    print("--- LINE送信テスト開始 ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス内容: {response.text}")
    print("--- LINE送信テスト終了 ---")

def main():
    # トークンチェック
    if not LINE_TOKEN or not USER_ID:
        print("エラー: LINE_ACCESS_TOKEN または USER_ID が設定されていません。")
        return

    RSS_URL = "https://www.nintendo.co.jp/data/rss/topics.xml"
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("記事が見つかりませんでした。")
        return

    entry = feed.entries[0]
    title = entry.title
    link = entry.link

    # テストのために必ず送信（if True）
    if True:
        print(f"最新記事: {title} を送信します。")
        image_url = get_article_image(link)
        send_flex_message(title, link, image_url)
        
        # 最後にタイトルを保存（通常運用のため）
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
