import os
import requests
import xml.etree.ElementTree as ET
import time
import re
from groq import Groq
import asyncio
import edge_tts

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
RSS_URL = "https://cointelegraph.com/rss"

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

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

def get_groq_content(title, description):
    """
    UPDATED MODEL: llama-3.3-70b-versatile (Latest & Supported)
    """
    if not client:
        return f"❌ Error: GROQ_API_KEY Missing!", "System Failure."

    try:
        prompt = f"""
        Act as a funny crypto news anchor.
        News: {title} - {description}
        
        Task 1: Detailed Summary (150 words). Bullet points. Explain "Why it matters".
        Task 2: Funny Voice Script (100 words). Conversational style. Start with "Yo Crypto Fam!".
        
        IMPORTANT: Separate Task 1 and Task 2 with exactly "||||".
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            # 👇 YAHAN CHANGE KIYA HAI (Naya Model)
            model="llama-3.3-70b-versatile", 
            temperature=0.7,
        )
        
        text = chat_completion.choices[0].message.content
        
        if "||||" in text:
            parts = text.split("||||")
            return parts[0].strip(), parts[1].strip()
        else:
            return text, "Check the text report!"

    except Exception as e:
        error_msg = str(e)
        print(f"🔥 GROQ FAILURE: {error_msg}")
        return f"⚠️ <b>GROQ ERROR:</b>\n{error_msg[:300]}", "System Error"

async def generate_audio(text):
    try:
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        # Message Format
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>Report:</b>\n{summary}\n\n📢 <i>Llama-3.3 Power 🦙</i>"
        
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
                data = {"chat_id": CHAT_ID, "title": "🎙️ Crypto Update", "performer": "AI Anchor"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Bot (Llama 3.3 Update)...")
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
                desc = item.find("description").text or ""
                clean_desc = clean_html(desc)
                img_url = extract_image(desc)
                if link not in sent_links:
                    print(f"Processing: {title[:20]}...")
                    prices = get_live_prices()
                    summary, script = get_groq_content(title, clean_desc)
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
