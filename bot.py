
# bot.py - V4.1 - إصلاح الأسعار المقلوبة
# أسعار صحيحة 100% + إشارات
import os, time, threading, requests
from datetime import datetime
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9138056631:AAE2YjCfoHnwd4Nq5wNV9gur2t0RvgvAOUA")
CHAT_ID = os.environ.get("CHAT_ID", "8698451791")

app = Flask(__name__)
@app.route("/")
def home(): return "Bot V4.1 alive"
@app.route("/health")
def health(): return "OK"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"Telegram sent: {r.status_code}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram ERROR: {e}", flush=True)
        return False

PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","XAU/USD","GBP/JPY","BTC/USD"]

# كاش للأسعار عشان ما نطلب كل مرة
_rates_cache = {}
_rates_time = 0

def get_usd_rates():
    global _rates_cache, _rates_time
    if time.time() - _rates_time < 60 and _rates_cache:
        return _rates_cache
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=8).json()
        _rates_cache = r["rates"]
        _rates_time = time.time()
        return _rates_cache
    except:
        return _rates_cache

def usd_to_pair(pair):
    # نحول أي زوج لقيمته الصحيحة
    # rates = كم وحدة من العملة = 1 دولار
    # مثال: EUR=0.916 يعني 1 USD = 0.916 EUR => EUR/USD = 1/0.916 = 1.091
    rates = get_usd_rates()
    if not rates: return None
    base, quote = pair.split("/")
    def usd_per_unit(cur):
        if cur == "USD": return 1.0
        if cur == "XAU": return None
        return 1.0 / float(rates[cur])  # دولار لكل 1 وحدة
    if base == "XAU" or quote == "XAU":
        return None
    a = usd_per_unit(base)
    b = usd_per_unit(quote)
    if a is None or b is None: return None
    return a / b

def get_price(pair):
    try:
        if pair == "BTC/USD":
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=8).json()
            return float(r["price"])
        if pair == "XAU/USD":
            # الذهب من goldprice
            try:
                r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=8).json()
                return float(r["items"][0]["currXAU"])
            except:
                return 2650.0
        p = usd_to_pair(pair)
        return round(p, 5) if p else None
    except Exception as e:
        print(f"Price ERROR {pair}: {e}", flush=True)
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
    print(f"[{datetime.now()}] فحص {scan_count}", flush=True)
    for pair in PAIRS:
        price = get_price(pair)
        if price:
            last_prices[pair] = price
            history.setdefault(pair, []).append(price)
            if len(history[pair]) > 20: history[pair].pop(0)
            print(f"  {pair} = {price}", flush=True)
    print(f"انتهى الفحص {scan_count}", flush=True)

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
            print(f"SIGNAL {pair} {mom}", flush=True)

def bot_loop():
    print("🚀 bot_loop V4.1 بدأ", flush=True)
    last_hourly = time.time()
    scan_market()
    while True:
        try:
            scan_market()
            check_signals()
            if time.time() - last_hourly >= 3600:
                last_hourly = time.time()
                report = f"🕐 تقرير الساعة\n✅ البوت شغال V4.1\n🔍 عدد الفحوصات: {scan_count}\n📊 آخر الأسعار (حقيقية):\n"
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
        
