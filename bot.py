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
    AI ab Funny aur Detailed mode mein kaam karega.
    """
    try:
        prompt = f"""
        You are a witty, sarcastic, and energetic crypto news anchor (like a cool YouTuber).
        
        **Task 1 (The Text Post):** Write a comprehensive, long summary (around 150-200 words) of this news. 
        - Make it professional but engaging. 
        - Use Bullet points for key facts. 
        - NO EXTERNAL LINKS.
        
        **Task 2 (The Voice Script):** Write a funny, conversational script (around 100-120 words) that explains the FULL story.
        - Style: Use humor, rhetorical questions, and excitement. 
        - Don't just read the headline, explain "Why this matters" in a fun way.
        - Start with something punchy like "Hold your bags fam!" or "Guess what happened?".
        
        **Format:**
        [SUMMARY_START]
        (Detailed Text Summary)
        [SUMMARY_END]
        [SCRIPT_START]
        (Funny Voice Script)
        [SCRIPT_END]
        
        News: {title} - {description}
        """
        response = model.generate_content(prompt)
        text = response.text
        
        # Parsing
        try:
            summary = text.split("[SUMMARY_START]")[1].split("[SUMMARY_END]")[0].strip()
            script = text.split("[SCRIPT_START]")[1].split("[SCRIPT_END]")[0].strip()
        except IndexError:
            summary = description
            script = f"Hey everyone, here is the update on {title}. It looks like a big move for the market."
            
        return summary, script
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return description, f"Update on {title}"

async def generate_audio(text):
    """Text ko Funny/Energetic Voice banayega"""
    try:
        # 'en-US-GuyNeural' thoda zyada energetic/casual voice hai Christopher se
        voice = "en-US-GuyNeural" 
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        # Link hata diya gaya hai. Sirf Summary aur Prices rahenge.
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>The Full Scoop:</b>\n{summary}\n\n📢 <i>Stay tuned for more!</i>"
        
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        # 1. Photo Bhejo
        if img_url:
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendPhoto", json=payload)
        else:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload)

        # 2. Audio Bhejo (Funny Anchor)
        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                # Title mein "Funny Take" likh diya taaki user play kare
                data = {"chat_id": CHAT_ID, "title": "🎙️ Listen: The Funny Truth", "performer": "Crypto Bro AI"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Bot (Funny Edition)...")
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
            
            # Top 3 News
            for item in reversed(items[:3]):
                title = item.find("title").text
                link = item.find("link").text
                raw_desc = item.find("description").text or ""
                
                clean_desc = clean_html(raw_desc)
                img_url = extract_image(raw_desc)
                
                if link not in sent_links:
                    print(f"🎙️ Roasting: {title[:20]}...")
                    
                    # 1. Prices
                    prices = get_live_prices()
                    
                    # 2. AI Magic (Funny)
                    summary, script = get_ai_content(title, clean_desc)
                    
                    # 3. Audio Generation
                    asyncio.run(generate_audio(script))
                    
                    # 4. Send (Bina Link ke)
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
