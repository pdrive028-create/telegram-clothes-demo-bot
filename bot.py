import os
from flask import Flask, request
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")

CHANNEL_1 = "https://t.me/+EVGePIY_vgk4MDU9"
CHANNEL_2 = "https://t.me/+XVkf38u9H6s2Y2Q1"

app = Flask(__name__)

users = {}


def tg(method, data):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        json=data,
        timeout=30
    )
    r.raise_for_status()
    return r.json()


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


@app.get("/")
def health():
    return "Telegram demo bot is running."


@app.post("/telegram")
def webhook():

    # Verify Telegram webhook secret
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return "forbidden", 403

    update = request.get_json(silent=True) or {}

    message = update.get("message")
    callback = update.get("callback_query")

    # -------------------------
    # MESSAGE HANDLER
    # -------------------------
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
                "📸 Please upload your photo first.\n\n"
                "This is a Demo/Test Bot — "
                "no actual clothes-change result will be generated."
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

    # -------------------------
    # BUTTON HANDLER
    # -------------------------
    if callback:

        chat_id = callback["message"]["chat"]["id"]
        user_id = callback["from"]["id"]
        data = callback.get("data")

        # Remove button loading
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

        # Change Clothes button
        if data == "change":

            if not (user["photo"] and user["reference"]):

                send(
                    chat_id,
                    "Please upload both photos first."
                )

            else:

                send(
                    chat_id,
                    "📢 To continue the demo, please join both channels:",
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

        # Verify button
        elif data == "verify":

            send(
                chat_id,
                "⏳ Demo processing has started...\n\n"
                "Estimated time: 15–30 minutes."
            )

            send(
                chat_id,
                "❌ Demo Token Limit Reached\n\n"
                "This is a Demo/Test Bot. "
                "No actual clothes-change result has been generated."
            )

        return "ok"

    return "ok"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000"))
        )
