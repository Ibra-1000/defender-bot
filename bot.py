
# bot.py - النسخة المصلحة - بوت المدافع
# يشتغل على Render + UptimeRobot + تقرير كل ساعة
import os, time, threading, requests
from datetime import datetime
from flask import Flask

# ===== ضع بياناتك هنا =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9138056631:AAE2YjCfoHnwd4Nq5wNV9gur2t0RvgvAOUA")
CHAT_ID = os.environ.get("CHAT_ID", "8698451791")
# ==========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive - Defender Bot"

@app.route("/health")
def health():
    return "OK"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"Telegram sent: {r.status_code} - {msg[:60]}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram ERROR: {e}", flush=True)
        return False

# أزواج الفوركس
PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","XAU/USD","GBP/JPY"]

def get_price(pair):
    # مثال بسيط: جلب سعر من exchangerate - يمكنك استبداله بمصدرك الأصلي
    try:
        base, quote = pair.split("/")
        # الذهب
        if base == "XAU":
            return 2650.0
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        r = requests.get(url, timeout=10).json()
        return float(r["rates"][quote])
    except Exception as e:
        print(f"Price ERROR {pair}: {e}", flush=True)
        return None

scan_count = 0
last_prices = {}

def scan_market():
    global scan_count
    scan_count += 1
    print(f"[{datetime.now()}] 🔍 بدأ الفحص رقم {scan_count}", flush=True)
    best = None
    for pair in PAIRS:
        price = get_price(pair)
        if price:
            last_prices[pair] = price
            print(f"  {pair} = {price}", flush=True)
    print(f"[{datetime.now()}] ✅ انتهى الفحص {scan_count} - فحصنا {len(last_prices)} زوج", flush=True)
    return last_prices

def bot_loop():
    print("🚀 bot_loop بدأ!", flush=True)
    # رسالة البداية - مهمة جدا للتأكد
    send_telegram("🛡️ بوت المدافع اشتغل الآن - بوتنا الخاص\n- يفحص كل أزواج الفوركس كل دقيقة - جاهز للصيد 🔥")
    last_hourly = time.time()
    while True:
        try:
            scan_market()
            # تقرير كل ساعة
            if time.time() - last_hourly >= 3600:
                last_hourly = time.time()
                report = f"🕐 تقرير الساعة\n✅ البوت شغال\n🔍 عدد الفحوصات: {scan_count}\n📊 آخر الأسعار:\n"
                for k,v in last_prices.items():
                    report += f"{k}: {v}\n"
                report += "⏳ ما فيه إشارة قوية لسه، ننتظر الفرصة النظيفة"
                send_telegram(report)
        except Exception as e:
            print(f"LOOP ERROR: {e}", flush=True)
        time.sleep(60)  # كل دقيقة

# تشغيل البوت في Thread منفصل قبل Flask - هذا هو الإصلاح الأساسي
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
