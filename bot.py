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

# --- AI SETUP (WITH SAFETY OFF) ---
if not GEMINI_API_KEY:
    print("❌ CRITICAL ERROR: Gemini API Key is MISSING in Secrets!")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Safety Filters ko OFF kar rahe hain taaki wo news block na kare
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)
except Exception as e:
    print(f"❌ AI Configuration Error: {e}")

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
    Ab ye function Safety Filters bypass karega.
    """
    try:
        if not GEMINI_API_KEY:
            return description, f"Hey, here is the update on {title}"

        prompt = f"""
        You are a funny, energetic, and sarcastic crypto news anchor.
        
        Input: {title} - {description}
        
        Task 1: Summarize this news in 150 words. Be detailed, use bullet points, and explain WHY it matters.
        Task 2: Write a funny voice script (100 words). Start with "Listen up Crypto Fam!". Don't just read the title, explain the drama!
        
        Use exactly "||||" to separate Task 1 and Task 2.
        """
        
        response = model.generate_content(prompt)
        text = response.text
        
        if "||||" in text:
            parts = text.split("||||")
            summary = parts[0].strip()
            script = parts[1].strip()
        else:
            summary = text
            script = f"Wow, big news coming in! {title}. Check the text for details!"

        return summary, script

    except Exception as e:
        print(f"⚠️ AI Generation Error: {e}") # Ye logs me dikhega
        return description, f"Breaking news update on {title}"

async def generate_audio(text):
    try:
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>The Full Scoop:</b>\n{summary}\n\n📢 <i>Sound On for the Roast! 🔊</i>"
        
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        if img_url:
            if len(caption) > 1000:
                caption = caption[:1000] + "... (Audio suno!)"
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendPhoto", json=payload)
        else:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload)

        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": CHAT_ID, "title": "🎙️ The Funny Take", "performer": "AI Anchor"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Bot (Safety OFF Mode)...")
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
