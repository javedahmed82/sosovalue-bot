import os
import requests
from playwright.sync_api import sync_playwright
import time

# --- CONFIG ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
TARGET_URL = "https://sosovalue.com/research/news"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("🚀 Starting Smart Browser...")
    
    # 1. Load Old News (Memory)
    processed_news = []
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r", encoding="utf-8") as f:
            processed_news = f.read().splitlines()

    new_items_found = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"🌐 Visiting: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=90000) # 90 sec wait
            
            print("⏳ Waiting for content...")
            time.sleep(15) # Page load hone ka intezaar

            # 2. Extract Text
            # Hum page ka sara text nikal kar analysis karenge
            content = page.inner_text("body")
            lines = content.split('\n')
            
            print(f"🔍 Scanning {len(lines)} lines of text...")
            
            # 3. Smart Parsing Logic
            # Pattern: "7 minutes ago" -> Next line is Title
            for i, line in enumerate(lines):
                line = line.strip()
                # Check for timestamps
                if "minutes ago" in line or "seconds ago" in line or "hour ago" in line or "Just now" in line:
                    
                    # Timestamp mil gaya, ab agli line check karte hain
                    if i + 1 < len(lines):
                        title = lines[i+1].strip()
                        
                        # Kabhi kabhi title ke baad description hoti hai
                        # Hum sirf title uthayenge jo thoda lamba ho
                        if len(title) > 10 and title not in processed_news:
                            print(f"🔥 Found New: {title[:30]}...")
                            
                            # Message Format
                            msg = f"<b>🚨 SOSO NEWS</b>\n\n<b>{title}</b>\n\n<i>(Source: {line})</i>"
                            send_telegram(msg)
                            
                            # Add to memory
                            new_items_found.append(title)
                            processed_news.append(title)
            
            if not new_items_found:
                print("✅ No new news found.")
            else:
                print(f"✅ Posted {len(new_items_found)} new updates.")

            # 4. Save Memory (Top 20 items rakhenge taaki file bhari na ho)
            with open("last_id.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(processed_news[-20:]))

        except Exception as e:
            print(f"⚠️ Browser Error: {e}")
            # Error telegram par na bhejein taaki spam na ho, bas log me dikhe
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()
