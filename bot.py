import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "8878142336:AAEovrL0CQ1wTrwd21xukj2323DeTQlM3oQ")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "8713122338").split(",") if x.strip()}
PAGE_SIZE = 4

API_KEY = ""

# Safe number-inventory manager. No OTP interception or verification bypass.
numbers = []
used = set()
lock = threading.Lock()
user_pos = {}

app = Flask(__name__)

@app.get("/")
def health():
    return "RS Number Manager is running"

def available():
    return [n for i, n in enumerate(numbers) if i not in used]

def main_menu(user_id):
    rows = [
        [InlineKeyboardButton("📞 GET NUMBER", callback_data="get"),
         InlineKeyboardButton("📈 TRAFFIC", callback_data="traffic")],
        [InlineKeyboardButton("💰 WALLET", callback_data="wallet"),
         InlineKeyboardButton("📊 STATISTICS", callback_data="stats")],
        [InlineKeyboardButton("👍 TOP USERS", callback_data="top"),
         InlineKeyboardButton("💰 REFER & EARN", callback_data="refer")],
        [InlineKeyboardButton("🔵 SUPPORT", callback_data="support"),
         InlineKeyboardButton("🗃️ BULK NUMBER", callback_data="bulk")]
    ]
    if user_id in ADMIN_IDS:
        rows.append([InlineKeyboardButton("⚙️ ADMIN / UPLOAD TXT", callback_data="admin")])
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    text = f"👋 Welcome {u.first_name or 'User'}!\n\n📞 Safe Number Manager\n🆔 ID: {u.id}\n\nChoose an option:"
    await update.message.reply_text(text, reply_markup=main_menu(u.id))

async def send_number(update, context):
    q = update.callback_query
    uid = q.from_user.id

    # Atomically claim exactly one number. It becomes unavailable immediately.
    with lock:
        free = [i for i in range(len(numbers)) if i not in used]
        if not free:
            await q.answer("No numbers available.", show_alert=True)
            return
        idx = free[0]
        used.add(idx)
        value = numbers[idx]

    # Copy only: Telegram's native copy button does not send a callback.
    kb = [[InlineKeyboardButton("📋 COPY NUMBER",
                                copy_text=CopyTextButton(text=value))],
          [InlineKeyboardButton("➡️ NEXT", callback_data="get")],
          [InlineKeyboardButton("🏠 MENU", callback_data="menu")]]
    await q.answer()
    await q.message.reply_text(
        f"📞 Number\n\n`{value}`\n\n"
        "Tap COPY NUMBER to copy it.\n"
        "This number is already reserved and will not be shown again.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    if data == "get":
        await send_number(update, context)
    elif data == "menu":
        await q.answer()
        await q.message.reply_text("🏠 Main Menu", reply_markup=main_menu(q.from_user.id))
    elif data == "stats":
        with lock:
            total = len(numbers)
            used_n = len(used)
            free = total - used_n
        await q.answer()
        await q.message.reply_text(
            f"📊 Statistics\n\nTotal: {total}\nUsed/Reserved: {used_n}\nAvailable: {free}"
        )
    elif data == "traffic":
        await q.answer()
        await q.message.reply_text("📈 Traffic is available for this safe inventory manager.")
    elif data == "wallet":
        await q.answer()
        await q.message.reply_text("💰 Wallet is disabled in the safe build.")
    elif data == "top":
        await q.answer()
        await q.message.reply_text("👍 Top Users is disabled in the safe build.")
    elif data == "refer":
        await q.answer()
        await q.message.reply_text("💰 Refer & Earn is disabled in the safe build.")
    elif data == "support":
        await q.answer()
        await q.message.reply_text("🔵 Support: contact your bot administrator.")
    elif data == "bulk":
        await q.answer()
        await q.message.reply_text("🗃️ Bulk Number: use the admin TXT upload.")
    elif data == "admin":
        if q.from_user.id not in ADMIN_IDS:
            await q.answer("Admin only.", show_alert=True)
            return
        await q.answer()
        await q.message.reply_text(
            "⚙️ Admin\nSend a .txt file. Each non-empty line becomes one number."
        )

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only.")
        return
    doc = update.message.document
    if not doc.file_name.lower().endswith(".txt"):
        await update.message.reply_text("❌ Only .txt files are accepted.")
        return

    f = await doc.get_file()
    raw = await f.download_as_bytearray()
    new_numbers = [x.strip() for x in raw.decode("utf-8", errors="ignore").splitlines() if x.strip()]

    with lock:
        numbers.clear()
        used.clear()
        numbers.extend(new_numbers)

    await update.message.reply_text(
        f"✅ TXT loaded.\nTotal numbers: {len(numbers)}\nAll numbers reset to available."
    )

def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Document.ALL, upload))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
