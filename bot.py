
# bot.py - V5 - أسعار لحظية من Yahoo Finance + إشارات
import os, time, threading, requests
from datetime import datetime
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9138056631:AAE2YjCfoHnwd4Nq5wNV9gur2t0RvgvAOUA")
CHAT_ID = os.environ.get("CHAT_ID", "8698451791")

app = Flask(__name__)
@app.route("/")
def home(): return "Bot V5 alive - Live Prices"
@app.route("/health")
def health(): return "OK"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"Telegram: {r.status_code}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram ERROR: {e}", flush=True)
        return False

# Yahoo Finance - أسعار لحظية مثل منصة التداول
YAHOO = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "XAU/USD": "GC=F",      # الذهب - عقود الذهب
    "GBP/JPY": "GBPJPY=X",
    "BTC/USD": "BTC-USD",
}
PAIRS = list(YAHOO.keys())
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_price(pair):
    sym = YAHOO[pair]
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        price = r["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(price)
    except Exception as e:
        print(f"Yahoo ERROR {pair}: {e}", flush=True)
        return None

last_prices = {}
history = {}
scan_count = 0
last_signal_time = {}

def calc_momentum(lst):
    if len(lst) < 5: return 0
    return ((lst[-1]-lst[-5])/lst[-5])*100 if lst[-5] else 0

def scan_market():
    global scan_count
    scan_count += 1
    print(f"[{datetime.now()}] V5 فحص {scan_count}", flush=True)
    for pair in PAIRS:
        price = get_price(pair)
        if price:
            last_prices[pair] = price
            history.setdefault(pair, []).append(price)
            if len(history[pair]) > 30: history[pair].pop(0)
            print(f"  {pair} = {price}", flush=True)
        time.sleep(0.5)
    print(f"انتهى الفحص {scan_count} - {len(last_prices)} زوج", flush=True)

def check_signals():
    for pair, lst in history.items():
        if len(lst) < 5: continue
        mom = calc_momentum(lst)
        price = last_prices.get(pair, 0)
        now = time.time()
        if now - last_signal_time.get(pair, 0) < 1800: continue
        signal = None
        if mom >= 0.15:
            signal = f"🟢 <b>إشارة صعود قوية</b>\n📊 الزوج: {pair}\n💰 السعر: {price}\n📈 الزخم: +{mom:.2f}% في 5 دقائق\n🎯 ادخل شراء\n⛔ وقف: {price*0.998:.4f}\n✅ هدف: {price*1.004:.4f}"
        elif mom <= -0.15:
            signal = f"🔴 <b>إشارة هبوط قوية</b>\n📊 الزوج: {pair}\n💰 السعر: {price}\n📉 الزخم: {mom:.2f}% في 5 دقائق\n🎯 ادخل بيع\n⛔ وقف: {price*1.002:.4f}\n✅ هدف: {price*0.996:.4f}"
        if signal:
            last_signal_time[pair] = now
            send_telegram(f"🚨 <b>فرصة تداول!</b>\n\n{signal}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}\n⚠️ لا تخاطر بأكثر من 1-2%")
            print(f"SIGNAL {pair} {mom:.2f}%", flush=True)

def bot_loop():
    print("🚀 bot_loop V5 بدأ - أسعار لحظية", flush=True)
    last_hourly = time.time()
    scan_market()
    while True:
        try:
            scan_market()
            check_signals()
            if time.time() - last_hourly >= 3600:
                last_hourly = time.time()
                report = f"🕐 تقرير الساعة\n✅ البوت شغال V5 - أسعار لحظية\n🔍 عدد الفحوصات: {scan_count}\n📊 آخر الأسعار (حية):\n"
                for k, v in last_prices.items():
                    chg = ""
                    if k in history and len(history[k]) >= 2:
                        d = ((v - history[k][0]) / history[k][0]) * 100
                        chg = f" ({d:+.2f}%)"
                    report += f"{k}: {v}{chg}\n"
                report += "\n⏳ نراقب السوق ونرسل إشارة عند أي حركة قوية"
                send_telegram(report)
        except Exception as e:
            print(f"LOOP ERROR: {e}", flush=True)
        time.sleep(60)

if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
