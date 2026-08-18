import os
from flask import Flask, request
import requests

BOT_TOKEN=os.environ["BOT_TOKEN"]
WEBHOOK_SECRET=os.environ.get("WEBHOOK_SECRET","change_me")
CHANNEL_1="https://t.me/+EVGePIY_vgk4MDU9"
CHANNEL_2="https://t.me/+XVkf38u9H6s2Y2Q1"
app=Flask(__name__)
users={}

def tg(method,data):
    r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",json=data,timeout=30)
    r.raise_for_status()
    return r.json()

def send(chat_id,text,markup=None):
    d={"chat_id":chat_id,"text":text}
    if markup:d["reply_markup"]={"inline_keyboard":markup}
    tg("sendMessage",d)

@app.get("/")
def health(): return "Telegram demo bot is running."

@app.post("/telegram")
def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token")!=WEBHOOK_SECRET:return "forbidden",403
    u=request.get_json(silent=True) or {}
    m=u.get("message"); c=u.get("callback_query")
    if m:
        chat=m["chat"]["id"]; uid=m["from"]["id"]
        if m.get("text")=="/start":
            users[uid]={"photo":False,"reference":False}
            send(chat,"📸 પહેલા તમારી photo upload કરો.\n\nઆ Demo/Test Bot છે — કોઈ actual clothes-change result આપશે નહીં.")
            return "ok"
        if m.get("photo"):
            s=users.setdefault(uid,{"photo":False,"reference":False})
            if not s["photo"]:
                s["photo"]=True; send(chat,"✅ Your photo received.\n\n🖼️ હવે reference clothes photo upload કરો.")
            elif not s["reference"]:
                s["reference"]=True
                send(chat,"✅ Reference photo received.",[[{"text":"👕 Change Clothes","callback_data":"change"}]])
            return "ok"
    if c:
        chat=c["message"]["chat"]["id"]; uid=c["from"]["id"]; data=c.get("data")
        tg("answerCallbackQuery",{"callback_query_id":c["id"]})
        s=users.setdefault(uid,{"photo":False,"reference":False})
        if data=="change":
            if not(s["photo"] and s["reference"]): send(chat,"પહેલા બંને photos upload કરો.")
            else: send(chat,"📢 Demo આગળ વધારવા માટે બંને channels join કરો:",[
                [{"text":"🔵 Join Channel 1","url":CHANNEL_1}],
                [{"text":"🔵 Join Channel 2","url":CHANNEL_2}],
                [{"text":"✅ I Joined / Verify","callback_data":"verify"}]])
        elif data=="verify":
            send(chat,"⏳ Demo Processing શરૂ થયું...\n\nEstimated time: 15–30 minutes.")
            send(chat,"❌ Demo Token Limit Reached\n\nઆ Demo/Test Bot છે. કોઈ actual clothes-change result generate કરવામાં આવ્યો નથી.")
        return "ok"
    return "ok"

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")))
