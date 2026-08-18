import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_1 = "https://t.me/+EVGePIY_vgk4MDU9"
CHANNEL_2 = "https://t.me/+XVkf38u9H6s2Y2Q1"

users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id] = {"photo": None, "reference": None, "verified": False}
    await update.message.reply_text(
        "📸 પહેલા તમારી photo upload કરો.\n\n"
        "આ Demo/Test Bot છે — કોઈ actual clothes-change result આપશે નહીં."
    )

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = users.setdefault(uid, {"photo": None, "reference": None, "verified": False})
    if not state["photo"]:
        state["photo"] = True
        await update.message.reply_text("✅ Your photo received.\n\n🖼️ હવે reference clothes photo upload કરો.")
    elif not state["reference"]:
        state["reference"] = True
        kb = [[InlineKeyboardButton("👕 Change Clothes", callback_data="change")]]
        await update.message.reply_text(
            "✅ Reference photo received.",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    kb=[
        [InlineKeyboardButton("🔵 Join Channel 1", url=CHANNEL_1)],
        [InlineKeyboardButton("🔵 Join Channel 2", url=CHANNEL_2)],
        [InlineKeyboardButton("✅ I Joined / Verify", callback_data="verify")]
    ]
    await q.message.reply_text(
        "📢 Demo આગળ વધારવા માટે બંને channels join કરો:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if uid not in users or not users[uid]["photo"] or not users[uid]["reference"]:
        await q.message.reply_text("પહેલા બંને photos upload કરો.")
        return
    # Telegram membership check requires the bot to be admin in both channels.
    # Private invite links above are used for joining; channel IDs must be configured
    # for strict automatic verification.
    await q.message.reply_text(
        "⏳ Demo Processing શરૂ થયું...\n\n"
        "Estimated time: 15–30 minutes."
    )
    await asyncio.sleep(5)
    await q.message.reply_text(
        "❌ Demo Token Limit Reached\n\n"
        "આ Demo/Test Bot છે. કોઈ actual clothes-change result generate કરવામાં આવ્યો નથી."
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(change, pattern="^change$"))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.run_polling()

if __name__ == "__main__":
    main()
