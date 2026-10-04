import time
import telebot
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === BOT CONFIGURATION ===
BOT_TOKEN = "8431563306:AAHlF_s8Ryc-6fS_beekBC3WGaeiXc9rh5g"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# === ADMIN & AUTHORIZED USERS ===
ADMIN_IDS = {6081767690}  # 👈 Yahan apna Telegram User ID daalein
AUTHORIZED_USERS = set(ADMIN_IDS)

# === RATE LIMIT CONFIG ===
COOLDOWN_SECONDS = 30
user_cooldowns = {}

# === OPTIMIZED REQUESTS SESSION ===
session = requests.Session()
retries = Retry(
    total=2,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
session.mount("https://", adapter)
session.mount("http://", adapter)

# === NORMALIZE NUMBER ===
def clean_number(num):
    num = str(num)
    if num.startswith("91") and len(num) > 10:
        num = num[-10:]
    return num.strip()

# === VALIDATE NUMBER ===
def validate_mobile(mobile):
    return mobile.isdigit() and len(mobile) == 10

# === FORMAT RESULT ===
def format_result(data, index):
    if not isinstance(data, dict):
        return ""

    return f"""🔍 <b>RESULT #{index}</b>

👤 Name: {data.get('name') or 'N/A'}
👨 Father: {data.get('fname') or data.get('father_name') or 'N/A'}
📱 Mobile: {data.get('mobile') or 'N/A'}
📞 Alt: {data.get('alt') or data.get('alternate') or 'N/A'}
📧 Email: {data.get('email') or 'N/A'}
📍 Address: {data.get('address') or 'N/A'}
📡 Circle: {data.get('circle') or 'N/A'}
🪪 ID: {data.get('id') or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━"""

# === FETCH DATA WITH NESTED JSON PARSING ===
def fetch_data(mobile):
    url = f"https://free.proapis.bond/num?number={mobile}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        response = session.get(url, headers=headers, timeout=8)

        if response.status_code != 200:
            return "⚠️ API Server busy or maintenance mode. Try later."

        try:
            json_data = response.json()
        except Exception:
            return "⚠️️ Invalid API response (not JSON)."

        if not isinstance(json_data, dict):
            return "⚠️️ Server returned unexpected data format."

        # 🔄 SAFE EXTRACTION (Handles nested 'result' -> 'result' -> 'Main_Records')
        results = []
        res_level1 = json_data.get("result")

        if isinstance(res_level1, dict):
            res_level2 = res_level1.get("result")
            if isinstance(res_level2, dict):
                results = res_level2.get("Main_Records", [])
            elif isinstance(res_level2, list):
                results = res_level2
            else:
                results = res_level1.get("Main_Records", [])
        elif isinstance(res_level1, list):
            results = res_level1

        if not results or not isinstance(results, list):
            return "⚠️ No data found for this number."

        # Smart Matching
        matched = []
        for r in results:
            if not isinstance(r, dict):
                continue
            mob1 = clean_number(r.get("mobile", ""))
            mob2 = clean_number(r.get("alt", r.get("alternate", "")))

            if mobile == mob1 or mobile == mob2:
                matched.append(r)

        target_list = matched if matched else [r for r in results if isinstance(r, dict)]

        # Deduplication
        seen = set()
        unique = []

        for r in target_list:
            key = (r.get("name"), r.get("address"))
            if key not in seen:
                seen.add(key)
                unique.append(r)

            if len(unique) == 5:
                break

        if not unique:
            return "⚠️ No match found."

        final_results = [
            formatted for i, data in enumerate(unique)
            if (formatted := format_result(data, i + 1))
        ]

        if not final_results:
            return "⚠️ Invalid data format received."

        final = "\n".join(final_results)
        signature = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n<b>🔴 RDX_RUPESH</b>\n👑 Owner: <a href='https://t.me/RDXB0T'>@RDXB0T</a>"

        return f"📊 Total Results: {len(unique)}\n\n{final}{signature}"

    except requests.exceptions.Timeout:
        return "⚠️ API Server timed out. Try again."
    except requests.exceptions.ConnectionError:
        return "⚠️ Connection error to API."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# === ADMIN COMMANDS ===
@bot.message_handler(commands=['auth'])
def authorize_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Only Admins can use this command!")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/auth <USER_ID>`", parse_mode="Markdown")
            return

        target_id = int(args[1])
        AUTHORIZED_USERS.add(target_id)
        bot.reply_to(message, f"✅ User <code>{target_id}</code> is now authorized!")
    except ValueError:
        bot.reply_to(message, "❌ Invalid User ID format.")

@bot.message_handler(commands=['unauth'])
def unauthorize_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Only Admins can use this command!")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/unauth <USER_ID>`", parse_mode="Markdown")
            return

        target_id = int(args[1])
        if target_id in AUTHORIZED_USERS and target_id not in ADMIN_IDS:
            AUTHORIZED_USERS.remove(target_id)
            bot.reply_to(message, f"🚫 Access revoked for <code>{target_id}</code>.")
        else:
            bot.reply_to(message, "⚠️ User not found or is an Admin.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid User ID format.")

# === START COMMAND ===
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in AUTHORIZED_USERS:
        bot.reply_to(message, "🔒 Access Denied! Contact Admin for access.")
        return
    bot.reply_to(message, "👋 Welcome! Send a 10-digit mobile number to search 🔍")

# === HANDLE MESSAGES ===
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id

    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "🔒 Access Denied! Ask Admin to authorize your Telegram User ID.")
        return

    current_time = time.time()

    if user_id not in ADMIN_IDS and user_id in user_cooldowns:
        elapsed = current_time - user_cooldowns[user_id]
        if elapsed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - elapsed)
            bot.reply_to(message, f"⏳ Please wait <b>{remaining} seconds</b> before searching again!")
            return

    mobile = message.text.strip()

    if not validate_mobile(mobile):
        bot.reply_to(message, "❌ Enter valid 10-digit number.")
        return

    user_cooldowns[user_id] = current_time

    try:
        bot.send_chat_action(message.chat.id, 'typing')
    except Exception:
        pass

    result = fetch_data(mobile)
    bot.reply_to(message, result)

# === RUN BOT ===
if __name__ == "__main__":
    print("🤖 Bot running with Nested JSON Parsing Fix...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
