import feedparser
import requests
import os

# 設定（後ほどGitHubの秘密変数から読み込みます）
LINE_TOKEN = os.environ["LINE_ACCESS_TOKEN"]
USER_ID = os.environ["USER_ID"]

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

def main():
    RSS_URL = "https://www.nintendo.co.jp/news/whatsnew.xml"
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        return

    # 最新記事のタイトルとURL
    latest_entry = feed.entries[0]
    title = latest_entry.title
    link = latest_entry.link

    # 前回保存したタイトルを読み込む
    last_title = ""
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    # 新着があれば通知
    if title != last_title:
        msg = f"【任天堂ニュース新着】\n{title}\n{link}"
        send_line(msg)
        # 今回のタイトルを保存
        with open("last_news.txt", "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
