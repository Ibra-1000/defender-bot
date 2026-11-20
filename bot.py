from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive"
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
# بوت المدافع - بوتنا الخاص - Ibrahim & Meta AI
# استراتيجية خرافية: تأكيد ثلاثي + فلتر قوة + فلتر وقت
# بدون SL / TP - نفس نظام البوت القديم - CALL / PUT - 5 دقائق

import os, asyncio, time, logging
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

class ta:
    @staticmethod
    def ema(close, length=9):
        return close.ewm(span=length, adjust=False).mean()
    @staticmethod
    def rsi(close, length=14):
        delta = close.diff()
        gain = delta.where(delta > 0, 0).ewm(alpha=1/length, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/length, adjust=False).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    @staticmethod
    def macd(close, fast=12, slow=26, signal=9):
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        line = ema_fast - ema_slow
        sig = line.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({'MACD_12_26_9': line, 'MACDs_12_26_9': sig}, index=close.index)
    @staticmethod
    def bbands(close, length=20, std=2):
        mid = close.rolling(length).mean()
        s = close.rolling(length).std()
        return pd.DataFrame({'BBL_20_2.0': mid - s*std, 'BBU_20_2.0': mid + s*std}, index=close.index)
    @staticmethod
    def atr(high, low, close, length=14):
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/length, adjust=False).mean()
    @staticmethod
    def adx(high, low, close, length=14):
        up = high.diff()
        down = -low.diff()
        plus_dm = up.where((up > down) & (up > 0), 0)
        minus_dm = down.where((down > up) & (down > 0), 0)
        atr_v = ta.atr(high, low, close, length)
        plus_di = 100 * plus_dm.ewm(alpha=1/length, adjust=False).mean() / atr_v
        minus_di = 100 * minus_dm.ewm(alpha=1/length, adjust=False).mean() / atr_v
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx_v = dx.ewm(alpha=1/length, adjust=False).mean()
        return pd.DataFrame({'ADX_14': adx_v}, index=close.index)
    @staticmethod
    def stoch(high, low, close, k=14, d=3, smooth_k=3):
        lowest = low.rolling(k).min()
        highest = high.rolling(k).max()
        k_val = 100 * (close - lowest) / (highest - lowest)
        k_val = k_val.rolling(smooth_k).mean()
        return pd.DataFrame({'STOCHk_14_3_3': k_val}, index=close.index)
from telegram import Bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("DefenderBot")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))  # كل 60 ثانية يفحص

# كل أزواج الفوركس + ذهب + بيتكوين - 28 زوج
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "EUR/AUD": "EURAUD=X",
    "GBP/AUD": "GBPAUD=X",
    "EUR/CAD": "EURCAD=X",
    "GBP/CAD": "GBPCAD=X",
    "AUD/CAD": "AUDCAD=X",
    "NZD/JPY": "NZDJPY=X",
    "EUR/NZD": "EURNZD=X",
    "GBP/NZD": "GBPNZD=X",
    "AUD/NZD": "AUDNZD=X",
    "USD/MXN": "USDMXN=X",
    "USD/TRY": "USDTRY=X",
    "USD/ZAR": "USDZAR=X",
    "EUR/CHF": "EURCHF=X",
    "GBP/CHF": "GBPCHF=X",
    "CAD/JPY": "CADJPY=X",
    "CHF/JPY": "CHFJPY=X",
    "XAU/USD - ذهب": "GC=F",
    "BTC/USD - بيتكوين": "BTC-USD",
    "ETH/USD - ايثريوم": "ETH-USD",
}

last_signal_time = {}  # منع التكرار - إشارة واحدة كل 30 دقيقة لكل زوج

def is_good_trading_time():
    # فلتر الوقت: لا تداول وقت الأخبار القوية جدا - السبت والاحد السوق مغلق
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:  # سبت / أحد
        return False
    # تجنب أول 30 دقيقة بعد افتتاح لندن ونيويورك - تذبذب عالي
    return True

def analyze_pair(symbol):
    try:
        # بيانات 5 دقائق + 15 دقيقة للتأكيد
        df5 = yf.download(symbol, period="2d", interval="5m", progress=False, auto_adjust=True)
        df15 = yf.download(symbol, period="5d", interval="15m", progress=False, auto_adjust=True)
        if df5.empty or len(df5) < 50:
            return None
        if isinstance(df5.columns, pd.MultiIndex):
            df5.columns = df5.columns.get_level_values(0)
            df15.columns = df15.columns.get_level_values(0)

        close = df5['Close']
        # --- المؤشرات الخرافية ---
        # 1. EMA 9 / 21 / 50
        ema9 = ta.ema(close, length=9)
        ema21 = ta.ema(close, length=21)
        ema50 = ta.ema(close, length=50)
        # 2. RSI
        rsi = ta.rsi(close, length=14)
        # 3. MACD
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        macd_line = macd['MACD_12_26_9']
        macd_sig = macd['MACDs_12_26_9']
        # 4. Bollinger
        bb = ta.bbands(close, length=20, std=2)
        bb_low = bb['BBL_20_2.0']
        bb_high = bb['BBU_20_2.0']
        # 5. ADX - قوة الترند
        adx_df = ta.adx(df5['High'], df5['Low'], close, length=14)
        adx = adx_df['ADX_14'] if adx_df is not None else pd.Series([0]*len(close))
        # 6. ATR - فلتر التذبذب
        atr = ta.atr(df5['High'], df5['Low'], close, length=14)
        # 7. Stochastic
        stoch = ta.stoch(df5['High'], df5['Low'], close, k=14, d=3)
        stoch_k = stoch['STOCHk_14_3_3']

        i = -1  # آخر شمعة مغلقة
        price = float(close.iloc[i])
        r = float(rsi.iloc[i]) if not pd.isna(rsi.iloc[i]) else 50
        e9 = float(ema9.iloc[i]); e21 = float(ema21.iloc[i]); e50 = float(ema50.iloc[i])
        m = float(macd_line.iloc[i]); ms = float(macd_sig.iloc[i])
        a = float(adx.iloc[i]) if not pd.isna(adx.iloc[i]) else 0
        s_k = float(stoch_k.iloc[i]) if not pd.isna(stoch_k.iloc[i]) else 50
        atr_val = float(atr.iloc[i])
        atr_avg = float(atr.rolling(20).mean().iloc[i])
        bbl = float(bb_low.iloc[i]); bbh = float(bb_high.iloc[i])

        # تأكيد الفريم الأكبر 15 دقيقة - الترند العام
        close15 = df15['Close']
        ema21_15 = ta.ema(close15, length=21)
        trend15_up = float(close15.iloc[-1]) > float(ema21_15.iloc[-1])
        trend15_down = float(close15.iloc[-1]) < float(ema21_15.iloc[-1])

        score_buy = 0
        score_sell = 0
        reasons_buy = []
        reasons_sell = []

        # شرط 1: ترتيب المتوسطات
        if e9 > e21 > e50:
            score_buy += 2; reasons_buy.append("EMA صاعد 9>21>50")
        if e9 < e21 < e50:
            score_sell += 2; reasons_sell.append("EMA هابط 9<21<50")
        # شرط 2: MACD
        if m > ms:
            score_buy += 1; reasons_buy.append("MACD فوق الإشارة")
        if m < ms:
            score_sell += 1; reasons_sell.append("MACD تحت الإشارة")
        # شرط 3: RSI + Stochastic - لا تدخل في تشبع إلا مع ارتداد
        if 50 < r < 70 and s_k > 50:
            score_buy += 1; reasons_buy.append(f"RSI {r:.0f} قوة شراء")
        if 30 < r < 50 and s_k < 50:
            score_sell += 1; reasons_sell.append(f"RSI {r:.0f} قوة بيع")
        # شرط 4: بولنجر - ارتداد من الأطراف
        if price <= bbl * 1.001 and r < 35:
            score_buy += 2; reasons_buy.append("ارتداد من حد بولنجر السفلي")
        if price >= bbh * 0.999 and r > 65:
            score_sell += 2; reasons_sell.append("ارتداد من حد بولنجر العلوي")
        # شرط 5: ADX - قوة الترند لازم تكون فوق 20
        if a > 22:
            if trend15_up: score_buy += 1; reasons_buy.append(f"ADX {a:.0f} ترند قوي")
            if trend15_down: score_sell += 1; reasons_sell.append(f"ADX {a:.0f} ترند قوي")
        # شرط 6: ATR - تذبذب صحي، مو ميت ومو مجنون
        if atr_val > atr_avg * 0.7:
            score_buy += 0.5; score_sell += 0.5

        # القرار: لازم 4 نقاط على الأقل + تأكيد فريم 15 دقيقة + ADX فوق 20
        direction = None
        score = 0
        reasons = []
        if score_buy >= 4 and trend15_up and a > 20:
            direction = "CALL"
            score = score_buy
            reasons = reasons_buy
        elif score_sell >= 4 and trend15_down and a > 20:
            direction = "PUT"
            score = score_sell
            reasons = reasons_sell

        if direction:
            strength = "🔥🔥🔥 قوية جدا" if score >= 5 else "🔥🔥 قوية" if score >= 4.5 else "✅ جيدة"
            return {"price": price, "direction": direction, "score": score, "strength": strength,
                    "rsi": r, "adx": a, "reasons": reasons}
        return None
    except Exception as e:
        logger.error(f"Error {symbol}: {e}")
        return None

async def send_signal(bot, pair_name, result):
    now_utc = datetime.now(timezone.utc)
    entry = now_utc.strftime("%H:%M:%S")
    expiry = (now_utc + timedelta(minutes=5)).strftime("%H:%M:%S")
    emoji = "🟢" if result['direction'] == "CALL" else "🔴"
    arabic = "اخضر / CALL" if result['direction'] == "CALL" else "احمر / PUT"
    action = "شراء" if result['direction'] == "CALL" else "بيع"
    trend = "صاعد 📈" if result['direction'] == "CALL" else "هابط 📉"
    reasons_text = "\n".join([f"• {x}" for x in result['reasons']])
    msg = f"""{emoji} {pair_name} - {arabic}

💰 سعر الدخول: {result['price']:.4f}
⏰ وقت الدخول: {entry}
⏰ وقت الاغلاق: {expiry}
⌛ المدة: 5 دقائق
📈 الاتجاه: {trend}
✅ اذا قال {arabic} <- ادخل صفقة {action} 5 دقائق في نفس وقت الدخول
⚠️ لا تدخل اذا تأخرت اكثر من 1 دقيقة عن وقت الدخول

🎯 قوة الإشارة: {result['strength']} ({result['score']:.1f}/6)
📊 RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}
🧠 لماذا؟ 
{reasons_text}

🛡️ بوت المدافع - بوتنا الخاص"""
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    logger.info(f"Sent {pair_name} {result['direction']}")

async def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("حط TELEGRAM_TOKEN و TELEGRAM_CHAT_ID في Render Env")
        return
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🛡️ بوت المدافع اشتغل الآن - بوتنا الخاص - يفحص كل أزواج الفوركس كل دقيقة - جاهز للصيد 🔥")
    while True:
        try:
            if not is_good_trading_time():
                await asyncio.sleep(300)
                continue
            for pair_name, symbol in PAIRS.items():
                now = time.time()
                if pair_name in last_signal_time and now - last_signal_time[pair_name] < 1800:
                    continue
                res = analyze_pair(symbol)
                if res:
                    await send_signal(bot, pair_name, res)
                    last_signal_time[pair_name] = now
                    await asyncio.sleep(2)
            await asyncio.sleep(SCAN_INTERVAL)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
