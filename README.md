# بوت المدافع - بوتنا الخاص

## طريقة التشغيل في 3 دقائق

### 1. GitHub
- انشئ ريبو جديد باسم defender-bot
- ارفع ملفات bot.py + requirements.txt + render.yaml

### 2. Telegram
- روح @BotFather وسوي بوت جديد وخذ التوكن
- ارسل اي رسالة لبوتك ثم افتح https://api.telegram.org/bot<TOKEN>/getUpdates وخذ chat_id

### 3. Render
- ادخل render.com -> New -> Blueprint -> اختر ريبو GitHub
- في Environment حط TELEGRAM_TOKEN و TELEGRAM_CHAT_ID
- Deploy وخلاص - البوت يشتغل 24 ساعة

## المميزات الخرافية
- 30 زوج فوركس + ذهب + بيتكوين + ايثريوم
- تأكيد ثلاثي: EMA + MACD + RSI + Bollinger + ADX + Stochastic + فريم 15 دقيقة
- فلتر ADX فوق 20 (لا إشارة ضعيفة)
- فلتر وقت (لا سبت/أحد)
- منع التكرار: إشارة واحدة كل 30 دقيقة لكل زوج
- بدون SL / TP مثل ما طلبت
