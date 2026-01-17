import os
import requests
from playwright.sync_api import sync_playwright
import time

# --- CONFIG ---
TOKEN = "8269485479:AAGCDQSlfB53PfS3X6Ysexr2QBX4pwkRya4"
CHAT_ID = "-1002341209589"
TARGET_URL = "https://sosovalue.com/research/news" # Frontend URL

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def main():
    print("🚀 Starting Chromium Browser...")
    
    with sync_playwright() as p:
        # Browser Launch (Headless = Dikhai nahi dega, background me chalega)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"🌐 Visiting: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000) # 60 sec wait
            
            # Wait for content to load
            print("⏳ Waiting for news to load...")
            time.sleep(10) # Thoda extra wait taaki JavaScript load ho jaye

            # Page ka Title check karte hain confirm karne ke liye
            page_title = page.title()
            print(f"✅ Page Loaded: {page_title}")

            # NOTE: SoSoValue ka HTML structure dekhna padega. 
            # Filhal hum poore page ka text utha kar check karte hain.
            # Agar 'Cloudflare' detect hua to bata dega.
            
            content = page.content()
            
            if "Just a moment" in page_title or "Cloudflare" in content:
                print("❌ Cloudflare Detected! GitHub IP is blocked.")
                send_telegram("⚠️ <b>Bot Alert:</b> Cloudflare Blocked the Browser.")
            else:
                # Yahan hum ek screenshot le sakte hain debugging ke liye
                # Lekin abhi ke liye hum bas Title bhej kar confirm karte hain
                msg = f"<b>✅ Browser Access Success!</b>\n\nPage Title: {page_title}\n\n(Ab hum specific news element dhundh sakte hain)"
                print("📩 Sending Success Msg...")
                send_telegram(msg)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            send_telegram(f"⚠️ Script Error: {str(e)[:100]}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()
