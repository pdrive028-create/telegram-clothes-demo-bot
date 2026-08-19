import os
from flask import Flask, request
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")

# Admin Telegram User ID
ADMIN_ID = 8455046701

# Channel IDs
CHANNEL_1_ID = -1004456013133
CHANNEL_2_ID = -1004341825293

# Channel invite links
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


# --------------------------------------------------
# TELEGRAM API
# --------------------------------------------------

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


# --------------------------------------------------
# CHECK CHANNEL MEMBERSHIP
# --------------------------------------------------

def is_joined(user_id, channel_id):

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

    channel1 = is_joined(user_id, CHANNEL_1_ID)
    channel2 = is_joined(user_id, CHANNEL_2_ID)

    return channel1 and channel2


# --------------------------------------------------
# JOIN + UPLOAD MENU
# --------------------------------------------------

def join_menu():

    return [
        [
            {
                "text": "🔵 Join Channel 1",
                "url": CHANNEL_1
            },
            {
                "text": "🔵 Join Channel 2",
                "url": CHANNEL_2
            }
        ],
        [
            {
                "text": "📤 Upload Your Photo",
                "callback_data": "upload_photo"
            }
        ]
    ]


# --------------------------------------------------
# PHOTO UPLOAD MENU
# --------------------------------------------------

def upload_menu():

    return [
        [
            {
                "text": "📸 Upload Your Photo",
                "callback_data": "my_photo"
            }
        ],
        [
            {
                "text": "🖼️ Upload Reference Photo",
                "callback_data": "reference_photo"
            }
        ]
    ]


# --------------------------------------------------
# START
# --------------------------------------------------

@app.get("/")
def health():

    return "Telegram Clothes Bot is running."


# --------------------------------------------------
# WEBHOOK
# --------------------------------------------------

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


    # ==================================================
    # MESSAGE HANDLER
    # ==================================================

    if message:

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]


        # ----------------------------------------------
        # /start
        # ----------------------------------------------

        if message.get("text") == "/start":

            users[user_id] = {
                "photo": False,
                "reference": False,
                "waiting_for": None
            }

            stats["starts"] += 1

            send(
                chat_id,
                "📢 Please join both channels first.\n\n"
                "After joining both channels, tap "
                "\"Upload Your Photo\" to continue.",
                join_menu()
            )

            return "ok"


        # ----------------------------------------------
        # /stats
        # ----------------------------------------------

        if message.get("text") == "/stats":

            if user_id != ADMIN_ID:
                return "ok"

            send(
                chat_id,
                "📊 BOT STATISTICS\n\n"
                f"👤 Total Users: {len(users)}\n"
                f"⭐ Total Starts: {stats['starts']}\n"
                f"📸 Photo Uploads: {stats['photo_uploads']}\n"
                f"🖼️ Reference Uploads: {stats['reference_uploads']}\n"
                f"👕 Remove Clothes Clicks: {stats['remove_clicks']}\n"
                f"🔎 Verify Attempts: {stats['verify_attempts']}\n"
                f"✅ Successful Verifications: "
                f"{stats['successful_verifications']}"
            )

            return "ok"


        # ----------------------------------------------
        # PHOTO MESSAGE
        # ----------------------------------------------

        if message.get("photo"):

            user = users.setdefault(
                user_id,
                {
                    "photo": False,
                    "reference": False,
                    "waiting_for": None
                }
            )


            # Check membership before accepting photo

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "📢 Please join both channels first.\n\n"
                    "You must join both channels before "
                    "uploading photos.",
                    join_menu()
                )

                return "ok"


            # ------------------------------------------
            # User photo
            # ------------------------------------------

            if user["waiting_for"] == "my_photo":

                user["photo"] = True
                user["waiting_for"] = None

                stats["photo_uploads"] += 1

                send(
                    chat_id,
                    "✅ Your photo has been received.\n\n"
                    "Now upload your reference clothes photo.",
                    [
                        [
                            {
                                "text": "🖼️ Upload Reference Photo",
                                "callback_data": "reference_photo"
                            }
                        ]
                    ]
                )

                return "ok"


            # ------------------------------------------
            # Reference photo
            # ------------------------------------------

            if user["waiting_for"] == "reference_photo":

                user["reference"] = True
                user["waiting_for"] = None

                stats["reference_uploads"] += 1

                send(
                    chat_id,
                    "✅ Reference clothes photo received.",
                    [
                        [
                            {
                                "text": "👕 Remove Clothes",
                                "callback_data": "remove_clothes"
                            }
                        ]
                    ]
                )

                return "ok"


            # ------------------------------------------
            # Photo sent without pressing upload
            # ------------------------------------------

            send(
                chat_id,
                "📢 Please use the upload button first.",
                upload_menu()
            )

            return "ok"


    # ==================================================
    # BUTTON HANDLER
    # ==================================================

    if callback:

        chat_id = callback["message"]["chat"]["id"]
        user_id = callback["from"]["id"]
        data = callback.get("data")


        # Remove Telegram loading

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
                "reference": False,
                "waiting_for": None
            }
        )


        # ----------------------------------------------
        # UPLOAD YOUR PHOTO
        # ----------------------------------------------

        if data == "upload_photo":

            stats["verify_attempts"] += 1

            # IMPORTANT:
            # Check both channels before allowing upload

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "📢 Please join both channels first.\n\n"
                    "After joining both channels, tap "
                    "\"Upload Your Photo\" again.",
                    join_menu()
                )

            else:

                send(
                    chat_id,
                    "✅ Both channels joined successfully.\n\n"
                    "Now choose what you want to upload:",
                    upload_menu()
                )

            return "ok"


        # ----------------------------------------------
        # MY PHOTO
        # ----------------------------------------------

        if data == "my_photo":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "📢 Please join both channels first.",
                    join_menu()
                )

                return "ok"


            user["waiting_for"] = "my_photo"

            send(
                chat_id,
                "📸 Please send your photo now."
            )

            return "ok"


        # ----------------------------------------------
        # REFERENCE PHOTO
        # ----------------------------------------------

        if data == "reference_photo":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "📢 Please join both channels first.",
                    join_menu()
                )

                return "ok"


            user["waiting_for"] = "reference_photo"

            send(
                chat_id,
                "🖼️ Please send your reference clothes photo now."
            )

            return "ok"


        # ----------------------------------------------
        # REMOVE CLOTHES
        # ----------------------------------------------

        if data == "remove_clothes":

            if not both_channels_joined(user_id):

                send(
                    chat_id,
                    "📢 Please join both channels first.",
                    join_menu()
                )

                return "ok"


            if not user["photo"]:

                send(
                    chat_id,
                    "📸 Please upload your photo first.",
                    upload_menu()
                )

                return "ok"


            if not user["reference"]:

                send(
                    chat_id,
                    "🖼️ Please upload your reference clothes photo first.",
                    upload_menu()
                )

                return "ok"


            stats["remove_clicks"] += 1

            send(
                chat_id,
                "⏳ Processing your request...\n\n"
                "Please wait while your request is being processed."
            )

            return "ok"


    return "ok"


# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000"))
    )
