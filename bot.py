import os
import requests
import xml.etree.ElementTree as ET
import time
import re
import html
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
    MODEL: llama-3.3-70b-versatile
    STYLE: Money Maker AI
    UPDATES: Fixes empty 'Why This Pays Off', Long Audio (600 words)
    """
    if not client:
        return f"❌ Error: GROQ_API_KEY Missing!", "System Failure."

    try:
        prompt = f"""
        Act as a high-energy crypto investor running a channel "Money Maker AI".
        News: {title} - {description}
        
        Task 1: WRITTEN REPORT (Clean Text Only)
        - Write a summary with Bullet points and Emojis (🚀, 💎, 📉).
        - DO NOT use headers like "Written Report" or "Summary".
        - DO NOT use markdown formatting like **bold** or ## headers.
        - MANDATORY: End with "💡 Why This Pays Off: [Explain here in 1 sentence why this is good for investors]".

        Task 2: PODCAST SCRIPT (Target: 600+ Words for 3+ Minutes Audio)
        - Start: "Welcome back to Money Maker AI!".
        - Structure: 
          1. High Energy Hook.
          2. Detailed Breakdown (Explain the "Why" and "How" in depth).
          3. Market Sentiment Analysis.
          4. Personal Prediction/Roast.
          5. Conclusion.
        - Make it conversational and VERY LONG. Elaborate on every point.
        - DO NOT read instructions like "Task 2".
        
        IMPORTANT: Separate Task 1 and Task 2 with exactly "||||".
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.7,
        )
        
        text = chat_completion.choices[0].message.content
        
        if "||||" in text:
            parts = text.split("||||")
            summary = parts[0].strip()
            script = parts[1].strip()
            
            # --- SAFAI ABHIYAAN (Cleaning Summary) ---
            summ_cleaners = ["Written Report:", "Written Report", "**", "##"]
            for word in summ_cleaners:
                summary = summary.replace(word, "")
            summary = summary.strip()

            # --- SAFAI ABHIYAAN (Cleaning Script) ---
            script_cleaners = ["Task 2:", "Task 2", "PODCAST SCRIPT", "Podcast Script", "Analysis:", "**", "##"]
            for word in script_cleaners:
                script = script.replace(word, "")
            
            return summary, script.strip()
        else:
            return text, "Check the text report!"

    except Exception as e:
        error_msg = str(e)
        print(f"🔥 GROQ FAILURE: {error_msg}")
        return f"⚠️ <b>GROQ ERROR:</b>\n{error_msg[:300]}", "System Error"

async def generate_audio(text):
    try:
        # Voice: GuyNeural (Funny/Casual)
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        await communicate.save("update.mp3")
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def send_telegram(title, summary, img_url, prices):
    try:
        base_url = f"https://api.telegram.org/bot{TOKEN}"
        
        # SAFETY STEP: HTML Escape
        safe_summary = html.escape(summary)
        
        # Caption Construction (HEADER CHANGED + BOLD SUMMARY)
        caption = f"<b>🚨 {title}</b>\n\n{prices}\n\n📝 <b>Money Maker Ai Summary Report:</b>\n<b>{safe_summary}</b>\n\n📢 <i>Money Maker Ai Power 🦙</i>"
        
        # 1. Try Sending Photo first
        sent_successfully = False
        
        if img_url:
            if len(caption) > 1024:
                caption = caption[:1020] + "..."
                
            payload = {"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(f"{base_url}/sendPhoto", json=payload)
            
            if r.status_code == 200:
                sent_successfully = True
            else:
                print(f"⚠️ Photo Failed ({r.text}). Trying Text Only...")
        
        # 2. Fallback: Agar Photo fail hui, to Text bhejo
        if not sent_successfully:
            payload = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
            r = requests.post(f"{base_url}/sendMessage", json=payload)

        # 3. Audio Bhejo
        if os.path.exists("update.mp3"):
            with open("update.mp3", "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": CHAT_ID, "title": "🎙️ Money Maker Daily", "performer": "AI Analyst"}
                requests.post(f"{base_url}/sendAudio", data=data, files=files)
            os.remove("update.mp3")

    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def main():
    print("📡 Starting Money Maker Bot (Final Fix)...")
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
