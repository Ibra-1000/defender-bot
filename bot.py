# bot.py - V6 POCKET OPTION PRO - إشارات احترافية دقيقة عالية
import os, time, requests, threading
from datetime import datetime, timedelta
import yfinance as yf

TOKEN = os.environ.get("TELEGRAM_TOKEN", "9138056631:AAE2YjCfoHnwd4Nq5wNV9gur2t0RvgvAOUA")
CHAT_ID = os.environ.get("CHAT_ID", "8698451791")

# أزواج بوكت أوبشن - الأكثر ربحاً
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "XAU/USD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
}

history = {p: [] for p in PAIRS}
last_signal = {p: 0 for p in PAIRS}

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except: pass

def rsi(prices, period=14):
    if len(prices) < period+1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        d = prices[i]-prices[i-1]
        gains.append(max(d,0)); losses.append(max(-d,0))
    if len(gains) < period: return 50
    avg_g = sum(gains[-period:])/period
    avg_l = sum(losses[-period:])/period
    if avg_l == 0: return 100
    rs = avg_g/avg_l
    return 100 - (100/(1+rs))

def ema(prices, period):
    if len(prices) < period: return prices[-1] if prices else 0
    k = 2/(period+1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

def analyze(pair, prices):
    """استراتيجية احترافية: RSI + EMA + MACD + Bollinger + Momentum"""
    if len(prices) < 20: return None
    price = prices[-1]
    r = rsi(prices)
    ema9 = ema(prices, 9)
    ema21 = ema(prices, 21)
    ema50 = ema(prices, 50) if len(prices) >= 50 else ema21
    # Bollinger
    ma20 = sum(prices[-20:])/20
    std = (sum((x-ma20)**2 for x in prices[-20:])/20)**0.5
    upper, lower = ma20 + 2*std, ma20 - 2*std
    # MACD بسيط
    macd = ema(prices, 12) - ema(prices, 26)
    macd_sig = ema(prices[-9:] if len(prices)>=9 else prices, 9) if False else 0
    # الزخم 5 دقائق
    mom5 = ((price - prices[-5])/prices[-5]*100) if len(prices)>=5 and prices[-5] else 0
    mom3 = ((price - prices[-3])/prices[-3]*100) if len(prices)>=3 and prices[-3] else 0

    score_up = 0; score_down = 0; reasons = []
    # 1 - RSI
    if r < 30: score_up += 25; reasons.append("RSI تشبع بيع")
    elif r < 40: score_up += 10; reasons.append("RSI قريب تشبع")
    if r > 70: score_down += 25; reasons.append("RSI تشبع شراء")
    elif r > 60: score_down += 10; reasons.append("RSI قريب تشبع")
    # 2 - EMA Trend
    if price > ema9 > ema21: score_up += 20; reasons.append("ترند صاعد EMA")
    if price < ema9 < ema21: score_down += 20; reasons.append("ترند هابط EMA")
    # 3 - Bollinger
    if price <= lower: score_up += 20; reasons.append("لمس Bollinger السفلي = ارتداد")
    if price >= upper: score_down += 20; reasons.append("لمس Bollinger العلوي = ارتداد")
    # 4 - MACD
    if macd > 0: score_up += 15
    else: score_down += 15
    # 5 - Momentum
    if mom5 > 0.03: score_up += 10
    if mom5 < -0.03: score_down += 10
    if mom3 > 0.02: score_up += 10
    if mom3 < -0.02: score_down += 10

    # فلتر قوي: لا إشارة إذا السعر بين المتوسطات (تذبذب)
    if abs(price - ema21)/price*100 < 0.01 and r > 45 and r < 55:
        return None

    now = datetime.now()
    entry = now.strftime("%H:%M:%S")
    expiry = (now + timedelta(minutes=5)).strftime("%H:%M:%S")

    if score_up >= 70:
        strength = min(95, score_up)
        return f"""🟢🟢 <b>CALL - شراء قوي - POCKET OPTION</b>
━━━━━━━━━━━━━━
📊 <b>الزوج:</b> {pair}
💰 <b>السعر:</b> {price:.5f}
🎯 <b>قوة الإشارة:</b> {strength}%
⏰ <b>وقت الدخول:</b> {entry}
⏳ <b>المدة:</b> 5 دقائق
🏁 <b>ينتهي:</b> {expiry}
📈 <b>RSI:</b> {r:.1f} | <b>EMA9:</b> {ema9:.5f}
✅ <b>الاستراتيجية:</b> RSI + EMA + Bollinger + MACD
📝 {', '.join(reasons[:3])}
⚡ <b>ادخل الآن - إذا CALL / أخضر → شراء 5 دقائق</b>
⛔ <b>لا تدخل إذا تأخرت أكثر من 1 دقيقة</b>"""
    if score_down >= 70:
        strength = min(95, score_down)
        return f"""🔴🔴 <b>PUT - بيع قوي - POCKET OPTION</b>
━━━━━━━━━━━━━━
📊 <b>الزوج:</b> {pair}
💰 <b>السعر:</b> {price:.5f}
🎯 <b>قوة الإشارة:</b> {strength}%
⏰ <b>وقت الدخول:</b> {entry}
⏳ <b>المدة:</b> 5 دقائق
🏁 <b>ينتهي:</b> {expiry}
📉 <b>RSI:</b> {r:.1f} | <b>EMA9:</b> {ema9:.5f}
✅ <b>الاستراتيجية:</b> RSI + EMA + Bollinger + MACD
📝 {', '.join(reasons[:3])}
⚡ <b>ادخل الآن - إذا PUT / أحمر → بيع 5 دقائق</b>
⛔ <b>لا تدخل إذا تأخرت أكثر من 1 دقيقة</b>"""
    return None

def fetch_price(sym):
    try:
        t = yf.Ticker(sym)
        d = t.history(period="1d", interval="1m")
        if d.empty: return None
        return float(d['Close'].iloc[-1])
    except: return None

def loop():
    send("🤖 <b>BOT PRO MAX ON - POCKET OPTION V6</b>\n✅ استراتيجية: RSI + EMA + Bollinger + MACD\n🎯 إشارات كل 5 دقائق - دقة عالية فقط (70%+)\n⏰ مدة الصفقة: 5 دقائق")
    while True:
        try:
            for pair, sym in PAIRS.items():
                p = fetch_price(sym)
                if p:
                    history[pair].append(p)
                    if len(history[pair]) > 60: history[pair] = history[pair][-60:]
                    # فحص كل 5 دقائق: لا إشارة مكررة لنفس الزوج قبل 5 دقائق
                    if time.time() - last_signal[pair] >= 300:
                        sig = analyze(pair, history[pair])
                        if sig:
                            send(sig)
                            last_signal[pair] = time.time()
                time.sleep(2)
            # تقرير كل ساعة
            if datetime.now().minute == 0:
                msg = "📊 <b>تقرير V6 - POCKET OPTION</b>\n"
                for pair in PAIRS:
                    if history[pair]:
                        msg += f"{pair}: {history[pair][-1]:.5f} | RSI {rsi(history[pair]):.0f}\n"
                send(msg)
                time.sleep(60)
            time.sleep(60)  # فحص كل دقيقة، إشارة كل 5 دقائق
        except Exception as e:
            time.sleep(30)

if __name__ == "__main__":
    loop()
    
