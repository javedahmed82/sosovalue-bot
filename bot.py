import requests
import xml.etree.ElementTree as ET
import os
import time

# --- CONFIG ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
RSS_URL = "https://cointelegraph.com/rss"

def send_telegram(title, link):
    try:
        msg = f"<b>🚨 CRYPTO NEWS UPDATE</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Read More</a>"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": False}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Connecting to CoinTelegraph RSS...")
    
    # 1. Load History (Taaki purani news dubara na bheje)
    sent_links = []
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r", encoding="utf-8") as f:
            sent_links = f.read().splitlines()

    try:
        # 2. Fetch News (XML Format)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(RSS_URL, headers=headers, timeout=20)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            items = channel.findall("item")
            
            print(f"✅ Feed Fetched. Found {len(items)} items.")
            
            new_links = []
            
            # 3. Process News (Sirf nayi news bhejenge)
            # Hum loop ko reverse kar rahe hain taaki purani pehle check ho, aur nayi baad mein
            for item in reversed(items[:10]): # Sirf top 10 check karenge
                title = item.find("title").text
                link = item.find("link").text
                
                if link not in sent_links:
                    print(f"🔥 New News Found: {title[:30]}...")
                    send_telegram(title, link)
                    new_links.append(link)
                    # Thoda break lete hain taaki Telegram spam na samjhe
                    time.sleep(1)
            
            if not new_links:
                print("💤 No new updates.")
            
            # 4. Save Memory
            # Purani list + Nayi list milakar wapas save karte hain (Max 50 items)
            updated_history = sent_links + new_links
            with open("last_id.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(updated_history[-50:]))
                
        else:
            print(f"❌ Error Fetching RSS: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Critical Error: {e}")

if __name__ == "__main__":
    main()
