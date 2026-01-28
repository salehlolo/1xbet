# Betting Analysis Pipeline (Mock-Ready)

> **Important**: هذا المشروع للتحليل والاختبار والمحاكاة والتنبيهات فقط. لا يتضمن أي رهانات حقيقية أو تسجيل دخول أو التفاف على أنظمة مواقع مراهنات.

## المتطلبات
- Python 3.11+

## الإعداد
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## الإعدادات (Environment)
ضع المتغيرات في `.env` أو صدّرها في البيئة:
- `MOCK_MODE=1` لتفعيل القراءة من `app/api/mock_data/`.
- `DB_PATH=data/app.db`
- `API_BASE_URL` و `API_KEY` و endpoints عند ربط مزود API الحقيقي.
- `MATCH_URL_TEMPLATE` لبناء رابط المباراة (مثال: `https://your-site.com/match/{event_id}`).

## تشغيل سريع (Mock Mode)
```bash
export MOCK_MODE=1
python -m app.cli fetch --sport soccer --days 1
python -m app.cli map-markets --sport soccer
python -m app.cli backtest --sport soccer --from 2025-01-01 --to 2025-06-01
```

## CLI
- `python -m app.cli fetch --sport soccer --days 1`
- `python -m app.cli map-markets --sport soccer`
- `python -m app.cli backtest --sport soccer --from 2025-01-01 --to 2025-06-01`
- `python -m app.cli alerts --sport soccer`
- `python -m app.cli telegram-test`
- `python -m app.cli send-matches --sport soccer --days 1 --limit 20`

## أين أضع الـ API الحقيقي؟
- عدّل متغيرات البيئة:
  - `API_BASE_URL`
  - `API_KEY`
  - `API_EVENTS_ENDPOINT`، `API_ODDS_ENDPOINT`، `API_RESULTS_ENDPOINT`
- يمكن تمرير mapping مخصص عبر `API_MAPPING_PATH` (JSON) لتحديد أسماء المفاتيح المختلفة.

## Telegram Setup
1) إنشاء بوت عبر BotFather:
   - افتح BotFather على تيليجرام وأرسل `/newbot` ثم اتبع التعليمات للحصول على `TELEGRAM_BOT_TOKEN`.
2) الحصول على `chat_id`:
   - أرسل رسالة إلى البوت ثم استخدم أحد أدوات جلب الـ updates أو بوت مساعد لمعرفة `chat_id`.
   - إذا كنت تستخدم قناة، اجعل البوت Admin ثم استخدم `@channelusername` كقيمة `TELEGRAM_CHAT_ID`.
3) مثال إعدادات:
```bash
TELEGRAM_ENABLED=1
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=yyyyy
MATCH_URL_TEMPLATE="https://your-site.com/match/{event_id}"
```
> إذا كان الـ API يوفر رابط مباشر للمباراة، سيتم استخدامه تلقائيًا بدل `MATCH_URL_TEMPLATE`.

## هيكلية المشروع
```
app/
  api/
    base.py
    http_client.py
    generic_adapter.py
    mock_data/
  db/
    schema.py
    repo.py
  markets/
    mapper.py
    overround.py
    filters.py
  strategies/
    base.py
    totals_baseline.py
  backtest/
    engine.py
    metrics.py
  alerts/
    notifier.py
  cli.py
```

## الاختبارات
```bash
pytest
```
