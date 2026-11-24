
# bot.py - V4 - بوت المدافع - نسخة الإشارات الحقيقية
# أسعار حقيقية من Binance + إشارة عند كل فرصة + تقرير كل ساعة
import os, time, threading, requests
from datetime import datetime
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9138056631:AAE2YjCfoHnwd4Nq5wNV9gur2t0RvgvAOUA")
CHAT_ID = os.environ.get("CHAT_ID", "8698451791")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot V4 alive - Defender Bot"

@app.route("/health")
def health():
    return "OK"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
        print(f"Telegram sent: {r.status_code} - {msg[:80]}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram ERROR: {e}", flush=True)
        return False

# أزواج من Binance - أسعار حقيقية لحظية
PAIRS = {
    "EUR/USD": "EURUSDT",
    "GBP/USD": "GBPUSDT",
    "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSDT",
    "USD/CAD": "USDCAD",
    "EUR/GBP": "EURGBP",
    "XAU/USD": "XAUUSDT",  # الذهب
    "GBP/JPY": "GBPJPY",
    "BTC/USD": "BTCUSDT",
}

# للفوركس اللي مو موجود في Binance نجيبه من exchangerate كبديل
FALLBACK_URL = "https://api.exchangerate-api.com/v4/latest/USD"

def get_price_binance(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=8).json()
        return float(r["price"])
    except:
        return None

def get_price_fallback(pair):
    # pair مثل EUR/USD
    try:
        base, quote = pair.split("/")
        if base == "XAU":
            # الذهب من مصدر بديل
            r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=8).json()
            return float(r["items"][0]["currXAU"])
        r = requests.get(FALLBACK_URL, timeout=8).json()
        rates = r["rates"]
        # نحول كل شي مقابل الدولار
        if base == "USD":
            return 1.0 / float(rates[quote]) if quote != "USD" else 1.0
        if quote == "USD":
            return float(rates[base])
        # متقاطع مثل EUR/GBP
        return float(rates[base]) / float(rates[quote])
    except Exception as e:
        print(f"Fallback ERROR {pair}: {e}", flush=True)
        return None

def get_price(pair):
    symbol = PAIRS.get(pair)
    p = get_price_binance(symbol) if symbol else None
    if p:
        return p
    return get_price_fallback(pair)

# ذاكرة الأسعار لحساب التغير
last_prices = {}
prev_prices = {}  # قبل دقيقة
history = {}  # لكل زوج قائمة آخر 20 سعر لحساب الزخم
scan_count = 0
last_signal_time = {}  # عشان ما نكرر نفس الإشارة كل دقيقة

def calc_momentum(prices_list):
    if len(prices_list) < 5:
        return 0
    # تغير آخر 5 فحوصات بالنسبة المئوية
    old = prices_list[-5]
    new = prices_list[-1]
    return ((new - old) / old) * 100 if old else 0

def scan_market():
    global scan_count
    scan_count += 1
    print(f"[{datetime.now()}] 🔍 فحص رقم {scan_count}", flush=True)
    for pair in PAIRS:
        price = get_price(pair)
        if price:
            prev_prices[pair] = last_prices.get(pair, price)
            last_prices[pair] = price
            if pair not in history:
                history[pair] = []
            history[pair].append(price)
            if len(history[pair]) > 20:
                history[pair].pop(0)
            print(f"  {pair} = {price}", flush=True)
    print(f"✅ انتهى الفحص {scan_count} - {len(last_prices)} زوج", flush=True)
    return last_prices

def check_signals():
    # نفحص كل زوج: اذا تحرك بقوة في آخر 5 دقائق نرسل إشارة
    for pair, prices in history.items():
        if len(prices) < 5:
            continue
        mom = calc_momentum(prices)
        price = last_prices.get(pair, 0)
        now = time.time()
        # لا نرسل نفس الإشارة قبل 30 دقيقة
        if now - last_signal_time.get(pair, 0) < 1800:
            continue
        # شروط الإشارة - حساسة عشان تجي إشارات
        signal = None
        if mom >= 0.15:
            signal = f"🟢 <b>إشارة صعود قوية</b>\n📊 الزوج: {pair}\n💰 السعر: {price}\n📈 الزخم: +{mom:.2f}% في آخر 5 دقائق\n🎯 ادخل شراء\n⛔ وقف: {price*0.998:.4f}\n✅ هدف: {price*1.004:.4f}"
        elif mom <= -0.15:
            signal = f"🔴 <b>إشارة هبوط قوية</b>\n📊 الزوج: {pair}\n💰 السعر: {price}\n📉 الزخم: {mom:.2f}% في آخر 5 دقائق\n🎯 ادخل بيع\n⛔ وقف: {price*1.002:.4f}\n✅ هدف: {price*0.996:.4f}"
        if signal:
            last_signal_time[pair] = now
            send_telegram(f"🚨 <b>فرصة تداول!</b>\n\n{signal}\n\n⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}\n⚠️ إدارة رأس مال: لا تخاطر بأكثر من 1-2%")
            print(f"SIGNAL sent for {pair} mom={mom}", flush=True)

def bot_loop():
    print("🚀 bot_loop V4 بدأ - مع الإشارات!", flush=True)
    print("Startup message disabled - V4", flush=True)
    last_hourly = time.time()
    # فحص أولي سريع
    scan_market()
    while True:
        try:
            scan_market()
            check_signals()
            if time.time() - last_hourly >= 3600:
                last_hourly = time.time()
                report = f"🕐 تقرير الساعة\n✅ البوت شغال V4\n🔍 عدد الفحوصات: {scan_count}\n📊 آخر الأسعار (حقيقية):\n"
                for k, v in last_prices.items():
                    # نحسب التغير من أول سعر
                    chg = ""
                    if k in history and len(history[k]) >= 2:
                        diff = ((v - history[k][0]) / history[k][0]) * 100
                        chg = f" ({diff:+.2f}%)"
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
            
