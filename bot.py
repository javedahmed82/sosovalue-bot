import os
import requests
import xml.etree.ElementTree as ET
import time

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
RSS_URL = "https://cointelegraph.com/rss"

def send_telegram(title, link):
    try:
        msg = f"<b>🚨 CRYPTO NEWS UPDATE</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Read More</a>"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Connecting to CoinTelegraph RSS...")
    sent_links = []
    
    # Last ID file read karna
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r", encoding="utf-8") as f:
            sent_links = f.read().splitlines()

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(RSS_URL, headers=headers, timeout=20)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            items = channel.findall("item")
            
            new_links = []
            
            # Loop
            for item in reversed(items[:10]):
                title = item.find("title").text
                link = item.find("link").text
                
                if link not in sent_links:
                    print(f"🔥 New News: {title[:30]}...")
                    send_telegram(title, link)
                    new_links.append(link)
                    time.sleep(1)
            
            # Save History
            updated_history = sent_links + new_links
            with open("last_id.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(updated_history[-50:]))
                
        else:
            print(f"❌ Error Fetching RSS: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
