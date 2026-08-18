import os
from flask import Flask, request
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")

app = Flask(__name__)


def tg(method, data):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        json=data,
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def send(chat_id, text):
    tg(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


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

    # Check normal messages
    message = update.get("message")

    if message:

        chat = message.get("chat")

        if chat:

            chat_id = chat.get("id")
            chat_type = chat.get("type")
            chat_title = chat.get("title", "Unknown")

            # Send Channel ID to the bot owner/admin
            if chat_type in ["channel", "group", "supergroup"]:

                send(
                    chat_id,
                    f"Channel/Chat Information\n\n"
                    f"Title: {chat_title}\n"
                    f"Type: {chat_type}\n"
                    f"Chat ID: {chat_id}"
                )

                return "ok"

        # /start from private chat
        if message.get("text") == "/start":

            send(
                message["chat"]["id"],
                "Send a message in your channel to get its Chat ID."
            )

            return "ok"

    # Check channel posts
    channel_post = update.get("channel_post")

    if channel_post:

        chat = channel_post.get("chat")

        if chat:

            chat_id = chat.get("id")
            chat_title = chat.get("title", "Unknown")

            # This sends the ID to the channel itself
            # temporarily for testing.
            tg(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text":
                    f"Channel ID:\n{chat_id}\n\n"
                    f"Channel: {chat_title}"
                }
            )

            return "ok"

    return "ok"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000"))
            )
