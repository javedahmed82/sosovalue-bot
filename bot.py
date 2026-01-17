import requests
import os
import json

# --- CONFIGURATION ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
URL = "https://gw.sosovalue.com/api/v1/research/news?limit=10"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.sosovalue.com/",
        "Origin": "https://m.sosovalue.com"
    }

    # ID Check
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r") as f:
            last_id = f.read().strip()
    else:
        last_id = "1" # Forcing it to fetch old news for the first run

    print(f"DEBUG: Last ID used is {last_id}")

    try:
        res = requests.get(URL, headers=headers, timeout=20)
        print(f"DEBUG: Fetch Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            # Yaha hum logs mein pura data print karenge taaki structure dikhe
            news_list = data.get('data', {}).get('list', [])
            print(f"DEBUG: Total News Found: {len(news_list)}")
            
            new_last_id = last_id

            for news in reversed(news_list):
                curr_id = str(news.get('id'))
                print(f"DEBUG: Checking News ID: {curr_id}")
                
                if curr_id > last_id:
                    title = news.get('title', 'No Title')
                    # Post karna
                    msg = f"<b>🚨 SOSOVALUE UPDATE</b>\n\n<b>{title}</b>"
                    
                    tel_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    post_res = requests.post(tel_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                    
                    if post_res.status_code == 200:
                        print(f"✅ Success: Posted ID {curr_id}")
                        new_last_id = curr_id
                    else:
                        print(f"❌ Telegram Error: {post_res.status_code} - {post_res.text}")
                else:
                    print(f"DEBUG: ID {curr_id} is not newer than {last_id}")

            # File update
            with open("last_id.txt", "w") as f:
                f.write(new_last_id)
        else:
            print(f"DEBUG: API Blocked or Error: {res.text[:200]}")
            
    except Exception as e:
        print(f"DEBUG: Exception Occurred: {e}")

if __name__ == "__main__":
    main()
                    
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
