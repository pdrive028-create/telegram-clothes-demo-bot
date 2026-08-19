import os
from flask import Flask, request
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CHANNEL_1_ID = -1004456013133
CHANNEL_2_ID = -1004341825293

CHANNEL_1 = "https://t.me/+EVGePIY_vgk4MDU9"
CHANNEL_2 = "https://t.me/+XVkf38u9H6s2Y2Q1"

app = Flask(__name__)

users = {}

stats = {
    "starts": 0,
    "photo_uploads": 0,
    "reference_uploads": 0,
    "remove_clicks": 0,
    "verify_attempts": 0,
    "successful_verifications": 0
}


def tg(method, data):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        json=data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def send(chat_id, text, markup=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if markup:
        data["reply_markup"] = {
            "inline_keyboard": markup
        }

    tg("sendMessage", data)


def is_member(channel_id, user_id):
    try:
        result = tg(
            "getChatMember",
            {
                "chat_id": channel_id,
                "user_id": user_id
            }
        )

        if not result.get("ok"):
            return False

        status = result["result"]["status"]

        return status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception:
        return False


def both_channels_joined(user_id):
    return (
        is_member(CHANNEL_1_ID, user_id)
        and is_member(CHANNEL_2_ID, user_id)
    )


def join_screen():
    return [
        [
            {
                "text": "🔵 Join Channel 1",
                "url": CHANNEL_1
            }
        ],
        [
            {
                "text": "🔵 Join Channel 2",
                "url": CHANNEL_2
            }
        ],
        [
            {
                "text": "📤 Upload Your Photo",
                "callback_data": "upload"
            }
        ]
    ]


def upload_screen():
    return [
        [
            {
                "text": "📸 Upload Your Photo",
                "callback_data": "photo_info"
            }
        ],
        [
            {
                "text": "🖼️ Upload Reference Photo",
                "callback_data": "reference_info"
            }
        ],
        [
            {
                "text": "👕 Remove Clothes",
                "callback_data": "remove"
            }
        ]
    ]


@app.get("/")
def health():
    return "Telegram bot is running."


@app.post("/telegram")
def webhook():

    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:
        return "forbidden", 403

    update = request.get_json(silent=True) or {}

    message = update.get("message")
    callback = update.get("callback_query")

    # =========================
    # MESSAGE HANDLER
    # =========================

    if message:

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]

        # /start
        if message.get("text") == "/start":

            stats["starts"] += 1

            users[user_id] = {
                "photo": False,
                "reference": False
            }

            send(
                chat_id,
                "📢 Please join both channels first.\n\n"
                "After joining both channels, "
                "tap \"Upload Your Photo\" to continue.",
                join_screen()
            )

            return "ok"

        # =========================
        # PHOTO UPLOAD
        # =========================

        if message.get("photo"):

            user = users.setdefault(
                user_id,
                {
                    "photo": False,
                    "reference": False
                }
            )

            # Check membership before accepting uploads
            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "❌ Please join both channels first.\n\n"
                    "After joining both channels, "
                    "tap \"Upload Your Photo\" again.",
                    join_screen()
                )

                return "ok"

            # First photo
            if not user["photo"]:

                user["photo"] = True
                stats["photo_uploads"] += 1

                send(
                    chat_id,
                    "✅ Your photo has been received.\n\n"
                    "🖼️ Now upload your reference clothes photo.",
                    upload_screen()
                )

            # Second photo
            elif not user["reference"]:

                user["reference"] = True
                stats["reference_uploads"] += 1

                send(
                    chat_id,
                    "✅ Reference clothes photo has been received.\n\n"
                    "You can now tap \"Remove Clothes\".",
                    upload_screen()
                )

            return "ok"

    # =========================
    # BUTTON HANDLER
    # =========================

    if callback:

        chat_id = callback["message"]["chat"]["id"]
        user_id = callback["from"]["id"]
        data = callback.get("data")

        tg(
            "answerCallbackQuery",
            {
                "callback_query_id": callback["id"]
            }
        )

        user = users.setdefault(
            user_id,
            {
                "photo": False,
                "reference": False
            }
        )

        # =========================
        # UPLOAD BUTTON
        # =========================

        if data == "upload":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "❌ Please join both channels first.\n\n"
                    "You must join both channels before "
                    "uploading your photo.",
                    join_screen()
                )

            else:

                send(
                    chat_id,
                    "📤 Upload section\n\n"
                    "Please upload your photo and then "
                    "your reference clothes photo.",
                    upload_screen()
                )

        # =========================
        # PHOTO INFO BUTTON
        # =========================

        elif data == "photo_info":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "❌ Please join both channels first.",
                    join_screen()
                )

            else:

                send(
                    chat_id,
                    "📸 Please send your photo here."
                )

        # =========================
        # REFERENCE INFO BUTTON
        # =========================

        elif data == "reference_info":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "❌ Please join both channels first.",
                    join_screen()
                )

            else:

                send(
                    chat_id,
                    "🖼️ Please send your reference clothes photo here."
                )

        # =========================
        # REMOVE CLOTHES
        # =========================

        elif data == "remove":

            stats["remove_clicks"] += 1

            # Check membership again
            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "❌ Please join both channels first.",
                    join_screen()
                )

                return "ok"

            if not user["photo"]:

                send(
                    chat_id,
                    "📸 Please upload your photo first.",
                    upload_screen()
                )

                return "ok"

            if not user["reference"]:

                send(
                    chat_id,
                    "🖼️ Please upload your reference clothes photo first.",
                    upload_screen()
                )

                return "ok"

            stats["verify_attempts"] += 1
            stats["successful_verifications"] += 1

            send(
                chat_id,
                "⏳ Processing your request...\n\n"
                "Please wait while your request is being processed."
            )

        # =========================
        # ADMIN STATS
        # =========================

        elif data == "stats":

            if user_id != ADMIN_ID:
                return "ok"

            send(
                chat_id,
                f"📊 Bot Statistics\n\n"
                f"👤 Total Users: {len(users)}\n"
                f"⭐ Total Starts: {stats['starts']}\n"
                f"📸 Photo Uploads: {stats['photo_uploads']}\n"
                f"🖼️ Reference Uploads: {stats['reference_uploads']}\n"
                f"👕 Remove Clothes Clicks: {stats['remove_clicks']}\n"
                f"🔗 Verify Attempts: {stats['verify_attempts']}\n"
                f"✅ Successfully Verified: "
                f"{stats['successful_verifications']}"
            )

        return "ok"

    return "ok"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000"))
    )
