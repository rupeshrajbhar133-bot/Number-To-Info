from flask import Flask, jsonify
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio
import threading
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "running",
        "service": "Mobile Info Telegram Bot API",
        "developer": "@RD3B4T"
    }), 200

def get_mobile_details(mobile_number: str) -> dict:
    clean_num = mobile_number.strip().replace("+91", "").replace(" ", "")
    url = f"https://free.proapis.bond/num?number={clean_num}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
    except Exception:
        pass
    return {"error": "No details found"}

# Token added here securely
TELEGRAM_BOT_TOKEN = "8496632773:AAHdTKxY_iNN3-sSsJmgzBw4zmOIZeB5mrY"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Welcome to Mobile Number Info Bot** ✨\n\n"
        "🚀 Send me any 10-digit Mobile Number (e.g., `9876543210`) to get complete details.\n\n"
        "⚡ **DEVELOPER**: @RD3B4T",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mobile = text.replace("+91", "").strip()
    
    if not mobile.isdigit() or len(mobile) < 10:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid 10-digit mobile number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Searching database for details, please hold on...**", parse_mode="Markdown")

    raw_data = await asyncio.to_thread(get_mobile_details, mobile)

    if not raw_data or (isinstance(raw_data, dict) and "error" in raw_data):
        await wait_msg.edit_text(f"❌ **No details found for number:** `{mobile}`", parse_mode="Markdown")
        return

    data = raw_data.get("data", raw_data) if isinstance(raw_data, dict) else {}
    if not isinstance(data, dict):
        data = {}

    name = data.get("name") or data.get("full_name") or data.get("owner_name") or "NA"
    fname = data.get("fname") or data.get("father_name") or data.get("fathers_name") or "NA"
    address = data.get("address") or data.get("permanent_address") or data.get("full_address") or "NA"
    alt_num = data.get("alt_num") or data.get("alternate_number") or data.get("alt_number") or "NA"
    id_proof = data.get("id") or data.get("id_number") or data.get("aadhaar") or "NA"
    gmail = data.get("gmail") or data.get("email") or "NA"

    response_text = f"📱 ᴍᴏʙɪʟᴇ ɴᴜᴍʙᴇʀ ʟᴏᴏᴋᴜᴘ\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n\n"
    response_text += f"🔍 Qᴜᴇʀʏ: {mobile}\n\n"
    response_text += f"✨ ᴅᴇᴛᴀɪʟꜱ:\n"
    response_text += f"• ɴᴀᴍᴇ: {name}\n"
    response_text += f"• ꜰᴀᴛʜᴇʀ'ꜱ ɴᴀᴍᴇ: {fname}\n"
    response_text += f"• ᴀᴅᴅʀᴇꜱꜱ: {address}\n"
    response_text += f"• ᴀʟᴛ ɴᴜᴍʙᴇʀ: {alt_num}\n"
    response_text += f"• ɪᴅ: {id_proof}\n"
    response_text += f"• ɢᴍᴀɪʟ: {gmail}\n\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n"
    response_text += f"💻 @RD3B4T"

    await wait_msg.edit_text(response_text)

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def main_bot():
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        await application.initialize()
        await application.start()
        print("🤖 Telegram Bot is running smoothly using manual polling...")
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)

    loop.run_until_complete(main_bot())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False)
