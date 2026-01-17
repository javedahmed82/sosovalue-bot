import requests
import os

# --- CONFIGURATION ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
URL = "https://gw.sosovalue.com/api/v1/research/news?limit=5"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.sosovalue.com/",
        "Origin": "https://m.sosovalue.com"
    }

    # Pichli news ki ID check karna
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r") as f:
            last_id = f.read().strip()
    else:
        last_id = "0"

    try:
        res = requests.get(URL, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            news_list = data.get('data', {}).get('list', [])
            new_last_id = last_id

            # Reverse loop taaki purani pehle post ho
            for news in reversed(news_list):
                curr_id = str(news['id'])
                if curr_id > last_id:
                    title = news['title']
                    content = news.get('content', '')[:400] + "..."
                    msg = f"<b>🚨 SOSOVALUE LIVE</b>\n\n<b>{title}</b>\n\n{content}"
                    
                    # Telegram Post
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                    new_last_id = curr_id

            # File update karna
            with open("last_id.txt", "w") as f:
                f.write(new_last_id)
        else:
            print(f"Fetch failed: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
