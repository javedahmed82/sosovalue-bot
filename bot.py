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

# AI Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- FUNCTIONS ---

def get_live_prices():
    """CoinGecko se taaza bhaav layega"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        data = r.json()
        
        prices = (
            f"💰 <b>Market Watch:</b>\n"
            f"• BTC: ${data['bitcoin']['usd']:,}\n"
            f"• ETH: ${data['ethereum']['usd']:,}\n"
            f"• BNB: ${data['binancecoin']['usd']:,}\n"
            f"• SOL: ${data['solana']['usd']:,}"
        )
        return prices
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
    Ye function AI se 2 cheezein mangega:
    1. Lamba Written Summary
    2. Ek Podcast Script (Audio ke liye)
    """
    try:
        prompt = f"""
        You are a senior crypto analyst.
        
        Task 1: Write a detailed summary (80-100 words) of this news. Use bullet points for key details. Make it insightful.
        Task 2: Write a short, conversational script (40 words) for a voice update. Start with "Hey Crypto Fam, here is the update...".
        
        Format your response exactly like this:
        [SUMMARY_START]
        (Your detailed summary here)
        [SUMMARY_END]
        [SCRIPT_START]
        (Your voice script here)
        [SCRIPT_END]
        
        News: {title} - {description}
        """
        response = model.generate_content(prompt)
        text = response.text
        
        # Parsing (Summary aur Script alag karna)
        try:
            summary = text.split("[SUMMARY_START]")[1].split("[SUMMARY_END]")[0].strip()
            script = text.split("[SCRIPT_START]")[1].split("[SCRIPT_END]")[0].strip()
        except IndexError:
            # Agar AI format gadbad kare to fallback
            summary = description
            script = f"Here is the latest update on {title}. Check the channel for details."
            
        return summary, script
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return description, f"Here is the latest update on {title}"

async def generate_audio(text):
    """Text ko MP3 banayega (Male US Voice)"""
    try:
        voice = "en-US-ChristopherNeural" # High quality male voice
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, link, summary, img_url, prices):
    try:
        # 1. Photo + Text Bhejo
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>Deep Dive:</b>\n{summary}\n\n🔗 <a href='{link}'>Read Full Report</a>"
        
        # Telegram API URL
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        if img_url:
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendPhoto", json=payload)
        else:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload)

        # 2. Audio Bhejo (Voice Note)
        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": CHAT_ID, "title": "Crypto Brief", "performer": "AI Analyst"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3") # Delete after sending

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Bot (News + Prices + Voice)...")
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
            
            # Sirf Top 3 news (Voice generation takes time)
            for item in reversed(items[:3]):
                title = item.find("title").text
                link = item.find("link").text
                raw_desc = item.find("description").text or ""
                
                clean_desc = clean_html(raw_desc)
                img_url = extract_image(raw_desc)
                
                if link not in sent_links:
                    print(f"🎙️ Processing: {title[:20]}...")
                    
                    # 1. Live Prices
                    prices = get_live_prices()
                    
                    # 2. AI Content
                    summary, script = get_ai_content(title, clean_desc)
                    
                    # 3. Generate Audio
                    asyncio.run(generate_audio(script))
                    
                    # 4. Send
                    send_telegram(title, link, summary, img_url, prices)
                    
                    new_links.append(link)
                    time.sleep(5)
            
            updated_history = sent_links + new_links
            with open("last_id.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(updated_history[-50:]))
                
    except Exception as e:
        print(f"⚠️ Critical Error: {e}")

if __name__ == "__main__":
    main()
