import os
import requests
import xml.etree.ElementTree as ET
import time
import re
import google.generativeai as genai
import asyncio
import edge_tts

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RSS_URL = "https://cointelegraph.com/rss"

# AI Config
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- FUNCTIONS ---

def get_live_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        data = r.json()
        return (f"💰 <b>Market Watch:</b>\n"
                f"• BTC: ${data['bitcoin']['usd']:,}\n"
                f"• ETH: ${data['ethereum']['usd']:,}\n"
                f"• BNB: ${data['binancecoin']['usd']:,}\n"
                f"• SOL: ${data['solana']['usd']:,}")
    except:
        return "💰 Prices currently unavailable."

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def extract_image(description):
    img_match = re.search(r'src="(.*?)"', description)
    return img_match.group(1) if img_match else None

def get_ai_content(title, description):
    """
    DEBUG MODE: Error ko chupayega nahi, seedha bhejega.
    """
    # 1. Check agar Key hi nahi hai
    if not GEMINI_API_KEY:
        error_msg = "❌ Error: GEMINI_API_KEY Secrets me missing hai!"
        return error_msg, "I cannot speak because the API Key is missing."

    try:
        prompt = f"""
        Act as a funny crypto news anchor.
        News: {title} - {description}
        
        Task 1: Detailed Summary (150 words).
        Task 2: Funny Voice Script (100 words).
        
        Separator: ||||
        """
        
        response = model.generate_content(prompt)
        text = response.text
        
        if "||||" in text:
            parts = text.split("||||")
            return parts[0].strip(), parts[1].strip()
        else:
            return text, "Hey, check this news out!"

    except Exception as e:
        # YAHAN HAI MAGIC: Asli Error Telegram par dikhega
        error_message = f"⚠️ AI ERROR (Screenshot bhejo): {str(e)}"
        print(error_message)
        return error_message, f"I encountered an error: {str(e)}"

async def generate_audio(text):
    try:
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        # Caption me ab Error dikhega agar aaya to
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>AI Report:</b>\n{summary}\n\n📢 <i>Debug Mode On</i>"
        
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        if img_url:
            if len(caption) > 1000:
                caption = caption[:1000] + "..."
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendPhoto", json=payload)
        else:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload)

        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": CHAT_ID, "title": "🎙️ AI Voice", "performer": "Debug Bot"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Debug Bot...")
    sent_links = []
    
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r", encoding="utf-8") as f:
            sent_links = f.read().splitlines()

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(RSS_URL, headers=headers, timeout=20)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.find("channel").findall("item")
            new_links = []
            
            for item in reversed(items[:3]):
                title = item.find("title").text
                link = item.find("link").text
                raw_desc = item.find("description").text or ""
                
                clean_desc = clean_html(raw_desc)
                img_url = extract_image(raw_desc)
                
                if link not in sent_links:
                    print(f"Processing: {title[:20]}...")
                    prices = get_live_prices()
                    summary, script = get_ai_content(title, clean_desc)
                    asyncio.run(generate_audio(script))
                    send_telegram(title, summary, img_url, prices)
                    new_links.append(link)
                    time.sleep(5)
            
            updated_history = sent_links + new_links
            with open("last_id.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(updated_history[-50:]))
                
    except Exception as e:
        print(f"⚠️ Critical Error: {e}")

if __name__ == "__main__":
    main()
