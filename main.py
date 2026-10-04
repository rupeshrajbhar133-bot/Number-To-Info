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

TELEGRAM_BOT_TOKEN = "8431563306:AAFAV_b_JF2zBj6VNyHXNjUWThyA48a8F-U"

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

    # Proper deep parsing according to your JSON structure
    try:
        res_level1 = raw_data.get("result", {})
        res_level2 = res_level1.get("result", {}) if isinstance(res_level1, dict) else {}
        
        main_records = res_level2.get("Main_Records", [])
        alt_records = res_level2.get("Alt_Records", [])
        
        main_rec = main_records[0] if isinstance(main_records, list) and len(main_records) > 0 else {}
        alt_rec = alt_records[0] if isinstance(alt_records, list) and len(alt_records) > 0 else {}

        name = main_rec.get("name") or alt_rec.get("name") or "NA"
        fname = main_rec.get("fname") or alt_rec.get("fname") or "NA"
        address = main_rec.get("address") or alt_rec.get("address") or "NA"
        alt_num = main_rec.get("alt") or alt_rec.get("alt") or "NA"
        id_proof = alt_rec.get("id") or "NA"
        gmail = alt_rec.get("email") or "NA"
    except Exception:
        name, fname, address, alt_num, id_proof, gmail = "NA", "NA", "NA", "NA", "NA", "NA"

    if name == "NA" and address == "NA":
        await wait_msg.edit_text(f"❌ **No details found for number:** `{mobile}`", parse_mode="Markdown")
        return

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
    response_text += f"↔️↔️↔️↔️↔️↔️️↔️↔️\n"
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
