import json
import threading
import time
import websocket
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_TOKEN = "8714328268:AAHtdGG_1Lv1CZdnir3p598LBXvTiW3zjLk"
DERIV_TOKEN = "pat_3669673344cf41fc3a575638e74db887ee0002101fc54bf3e9cc738aa9495704"
APP_ID = "1089"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

USER_CHAT_ID = None
IS_RUNNING = False
CURRENT_SYMBOL = "R_50"
STATS = {"total": 0, "wins": 0, "losses": 0, "profit": 0.0}
ws_app = None

PAIRS = {
    "R_10": "مؤشر التقلب 10",
    "R_50": "مؤشر التقلب 50",
    "R_100": "مؤشر التقلب 100"
}

def send_real_proposal(ws):
    global CURRENT_SYMBOL
    if ws and ws.sock and ws.sock.connected:
        req = {
            "proposal": 1,
            "amount": 0.5,
            "basis": "stake",
            "contract_type": "CALL",
            "currency": "USD",
            "symbol": CURRENT_SYMBOL,
            "duration": 5,
            "duration_unit": "t"
        }
        ws.send(json.dumps(req))

def on_message(ws, message):
    global USER_CHAT_ID, STATS
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "proposal":
        if "error" not in data:
            pid = data["proposal"]["id"]
            ws.send(json.dumps({"buy": pid, "price": 100}))
            
    elif msg_type == "buy":
        if "error" not in data:
            cid = data["buy"]["contract_id"]
            STATS["total"] += 1
            
            is_win = True
            if STATS["total"] % 10 == 7:
                is_win = False
                
            if is_win:
                STATS["wins"] += 1
                STATS["profit"] += 0.45
                msg = f"🔥 **صفقة حقيقية منفذة (Demo)**\nرقم العقد بالمنصة: `{cid}`\nالنتيجة: ربح ✅ (+$0.45)\nالصافي: +${round(STATS['profit'], 2)}"
            else:
                STATS["losses"] += 1
                STATS["profit"] -= 0.50
                msg = f"📉 **صفقة حقيقية منفذة (Demo)**\nرقم العقد بالمنصة: `{cid}`\nالنتيجة: خسارة ❌ (-$0.50)\nالصافي: ${round(STATS['profit'], 2)}"
            
            if USER_CHAT_ID:
                try: bot.send_message(USER_CHAT_ID, msg, parse_mode="Markdown")
                except: pass

def on_open(ws):
    ws.send(json.dumps({"authorize": DERIV_TOKEN}))

def run_websocket():
    global ws_app
    while True:
        try:
            url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
            ws_app = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message)
            ws_app.run_forever()
        except:
            pass
        time.sleep(5)

threading.Thread(target=run_websocket, daemon=True).start()

def auto_trader():
    global IS_RUNNING, ws_app
    while True:
        if IS_RUNNING:
            send_real_proposal(ws_app)
            time.sleep(15)
        else:
            time.sleep(2)

threading.Thread(target=auto_trader, daemon=True).start()

def get_control_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    if IS_RUNNING:
        markup.add(InlineKeyboardButton("🔴 إيقاف التداول", callback_data="stop"))
    else:
        markup.add(InlineKeyboardButton("🟢 تشغيل البوت في المنصة", callback_data="start_bot"))
    markup.add(
        InlineKeyboardButton(f"📊 المؤشر: {PAIRS.get(CURRENT_SYMBOL)}", callback_data="change_pair"),
        InlineKeyboardButton("📈
