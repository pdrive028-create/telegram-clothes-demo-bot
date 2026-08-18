import os
from flask import Flask, request
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")

CHANNEL_1_ID = -1004456013133
CHANNEL_2_ID = -1004341825293

CHANNEL_1 = "https://t.me/+EVGePIY_vgk4MDU9"
CHANNEL_2 = "https://t.me/+XVkf38u9H6s2Y2Q1"

app = Flask(__name__)

users = {}


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


@app.get("/")
def health():
    return "Telegram bot is running."


@app.post("/telegram")
def webhook():

    # Verify Telegram webhook secret
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

            users[user_id] = {
                "photo": False,
                "reference": False
            }

            send(
                chat_id,
                "📸 Please upload your photo first."
            )

            return "ok"

        # Photo upload
        if message.get("photo"):

            user = users.setdefault(
                user_id,
                {
                    "photo": False,
                    "reference": False
                }
            )

            # First photo
            if not user["photo"]:

                user["photo"] = True

                send(
                    chat_id,
                    "✅ Your photo has been received.\n\n"
                    "🖼️ Now please upload the reference clothes photo."
                )

            # Second photo
            elif not user["reference"]:

                user["reference"] = True

                send(
                    chat_id,
                    "✅ Reference clothes photo has been received.",
                    [
                        [
                            {
                                "text": "👕 Change Clothes",
                                "callback_data": "change"
                            }
                        ]
                    ]
                )

            return "ok"

    # =========================
    # BUTTON HANDLER
    # =========================

    if callback:

        chat_id = callback["message"]["chat"]["id"]
        user_id = callback["from"]["id"]
        data = callback.get("data")

        # Remove Telegram button loading
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
        # CHANGE CLOTHES
        # =========================

        if data == "change":

            if not (
                user["photo"]
                and user["reference"]
            ):

                send(
                    chat_id,
                    "Please upload both photos first."
                )

            else:

                send(
                    chat_id,
                    "📢 Please join both channels to continue:",
                    [
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
                                "text": "✅ I Joined / Verify",
                                "callback_data": "verify"
                            }
                        ]
                    ]
                )

        # =========================
        # VERIFY MEMBERSHIP
        # =========================

        elif data == "verify":

            channel_1_joined = is_member(
                CHANNEL_1_ID,
                user_id
            )

            channel_2_joined = is_member(
                CHANNEL_2_ID,
                user_id
            )

            # User has NOT joined both channels
            if not (
                channel_1_joined
                and channel_2_joined
            ):

                send(
                    chat_id,
                    "❌ Please join both channels first.\n\n"
                    "After joining both channels, "
                    "tap \"I Joined / Verify\" again."
                )

                return "ok"

            # Both channels joined
            send(
                chat_id,
                "⏳ Processing your request...\n\n"
                "Please wait while your request is being processed."
            )

        return "ok"

    return "ok"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000"))
    )
