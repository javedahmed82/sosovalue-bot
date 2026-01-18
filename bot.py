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
    Ab ye function fail nahi hoga. Simple separation use karega.
    """
    try:
        # Prompt ko force kiya hai ki wo EXPAND kare (kyunki RSS input chota hota hai)
        prompt = f"""
        You are a sarcastic, funny, and smart crypto news anchor (like a YouTuber).
        The input news is short, so use your internal knowledge to EXPAND on it.
        
        Input News: {title} - {description}

        Task 1: Write a detailed summary (120-150 words). 
        - Explain the background and why this matters. 
        - Use emojis and bullet points. 
        - Tone: Professional but engaging.
        
        Task 2: Write a Voice Script (100+ words). 
        - Do NOT just read the headline. Tell a story.
        - Start with a funny hook (e.g., "Oh boy, here we go again...").
        - Explain the news simply to a friend.
        
        IMPORTANT: Separate Task 1 and Task 2 with exactly four pipes "||||".
        
        Output Format:
        (Your Detailed Summary Here)
        ||||
        (Your Voice Script Here)
        """
        
        response = model.generate_content(prompt)
        text = response.text
        
        # Simple Splitter (Zada reliable hai)
        if "||||" in text:
            parts = text.split("||||")
            summary = parts[0].strip()
            script = parts[1].strip()
        else:
            # Agar AI separator bhool gaya, to pura text summary maan lenge
            summary = text
            script = f"Hey guys, check this out. {title}. It's a big update, read the text for more!"

        return summary, script

    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        # Fallback agar AI bilkul hi mar jaye
        return f"Could not generate summary. News: {title}", f"Breaking news on {title}"

async def generate_audio(text):
    try:
        # Voice: GuyNeural (Funny/Casual tone ke liye best)
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        # Caption Message
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>The Full Scoop:</b>\n{summary}\n\n📢 <i>Sound On for the Roast! 🔊</i>"
        
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        # 1. Photo Bhejo
        if img_url:
            # Caption limit hoti hai (1024 chars). Agar summary bahut badi hai to trim kar denge.
            if len(caption) > 1000:
                caption = caption[:1000] + "... (Read more in audio)"
            
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendPhoto", json=payload)
        else:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload)

        # 2. Audio Bhejo
        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": CHAT_ID, "title": "🎙️ The Funny Take", "performer": "AI Anchor"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Bot (Robust Version)...")
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
            
            # Top 3 News Check
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
