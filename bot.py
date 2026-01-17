import requests
import os

# --- CONFIG ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
URL = "https://gw.sosovalue.com/api/v1/research/news?limit=5"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.sosovalue.com/",
        "Origin": "https://m.sosovalue.com"
    }

    # last_id check
    last_id = "1"
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r") as f:
            last_id = f.read().strip()
            if not last_id: last_id = "1"

    print(f"DEBUG: Checking news newer than {last_id}")

    try:
        res = requests.get(URL, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            news_list = data.get('data', {}).get('list', [])
            print(f"DEBUG: Found {len(news_list)} items")
            
            new_last_id = last_id
            for news in reversed(news_list):
                curr_id = str(news['id'])
                if curr_id > last_id:
                    title = news.get('title', 'No Title')
                    msg = f"<b>🚨 SOSOVALUE UPDATE</b>\n\n<b>{title}</b>"
                    
                    # Telegram Post
                    tel_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    post_res = requests.post(tel_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                    
                    if post_res.status_code == 200:
                        print(f"✅ Success: Posted ID {curr_id}")
                        new_last_id = curr_id
                    else:
                        print(f"❌ Telegram Error: {post_res.status_code}")
                else:
                    print(f"DEBUG: Skipping old ID {curr_id}")

            with open("last_id.txt", "w") as f:
                f.write(new_last_id)
        else:
            print(f"❌ SoSoValue Blocked/Error: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")

if __name__ == "__main__":
    main()
                    
                    # Telegram Post
                    tel_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    post_res = requests.post(tel_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                    
                    if post_res.status_code == 200:
                        print(f"✅ Success: Posted ID {curr_id}")
                        new_last_id = curr_id
                    else:
                        print(f"❌ Telegram Error: {post_res.status_code}")
                else:
                    print(f"DEBUG: Skipping old ID {curr_id}")

            with open("last_id.txt", "w") as f:
                f.write(new_last_id)
        else:
            print(f"❌ SoSoValue Blocked/Error: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")

if __name__ == "__main__":
    main()
                
                # Telegram Post with Debugging
                tel_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                post_res = requests.post(tel_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                
                if post_res.status_code == 200:
                    print(f"Successfully posted news ID: {curr_id}")
                    new_last_id = curr_id
                else:
                    print(f"Telegram API Error: {post_res.status_code} - {post_res.text}")

        with open("last_id.txt", "w") as f:
            f.write(new_last_id)
    else:
        print(f"Failed to fetch from SoSoValue. Status: {res.status_code}")

if __name__ == "__main__":
    main()
