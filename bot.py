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

    # last_id check (Integer conversion)
    last_id = 0
    if os.path.exists("last_id.txt"):
        try:
            with open("last_id.txt", "r") as f:
                content = f.read().strip()
                if content:
                    last_id = int(content)
        except:
            last_id = 0

    print(f"DEBUG: Checking news newer than ID: {last_id}")

    try:
        res = requests.get(URL, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            news_list = data.get('data', {}).get('list', [])
            print(f"DEBUG: Found {len(news_list)} items on Server")
            
            new_last_id = last_id
            
            # Reverse loop to post oldest first
            for news in reversed(news_list):
                try:
                    curr_id = int(news['id'])
                    title = news.get('title', 'No Title')
                    
                    # Log comparison
                    # print(f"DEBUG: Comparing New {curr_id} > Old {last_id}")

                    if curr_id > last_id:
                        print(f"🚀 New News Found: {title[:20]}...")
                        msg = f"<b>🚨 SOSOVALUE UPDATE</b>\n\n<b>{title}</b>"
                        
                        # Telegram Post
                        tel_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
                        
                        post_res = requests.post(tel_url, json=payload)
                        
                        if post_res.status_code == 200:
                            print(f"✅ Sent to Telegram. ID: {curr_id}")
                            new_last_id = curr_id
                        else:
                            print(f"❌ Telegram Error: {post_res.status_code}")
                    else:
                        pass # Skipping old news silently
                except Exception as e:
                    print(f"Skipping item due to error: {e}")

            # Save the NEWEST ID
            with open("last_id.txt", "w") as f:
                f.write(str(new_last_id))
        else:
            print(f"❌ SoSoValue Blocked/Error: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")

if __name__ == "__main__":
    main()
