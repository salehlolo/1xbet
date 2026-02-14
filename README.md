# BetsAPI 1xBet Signal Monitor (Python 3.11)

مشروع تحليل بيانات وأسعار فقط (بدون أي تنفيذ رهانات أو تسجيل دخول لمواقع مراهنة).

## ماذا يفعل؟
- يجلب مباريات live وupcoming من BetsAPI endpoints الخاصة بـ 1xBet.
- يطبّع الأودز إلى implied probabilities ثم يزيل الهامش (vig) لإنتاج fair probabilities.
- يكتشف إشارات:
  - Steam movement
  - Consensus outlier
  - Positive EV
- يخزن snapshots في SQLite لحساب المقارنات التاريخية وCLV.
- يرسل تنبيهات Telegram منظمة.

## مهم
هذا المشروع **لا يضع رهانات** ولا يفتح جلسات دخول لأي موقع مراهنات. هو لأغراض التحليل فقط.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```
ثم عدّل `.env`.

## إعدادات `.env`
- `BETS_API_KEY` (مطلوب)
- `BETS_API_BASE_URL` (افتراضي: `https://api.betsapi.com`)
- `BETS_INPLAY_ENDPOINT=/v1/1xbet/inplay`
- `BETS_UPCOMING_ENDPOINT=/v1/1xbet/upcoming`
- `BETS_EVENT_ENDPOINT=/v1/1xbet/event`
- `BETS_RESULT_ENDPOINT=/v1/1xbet/result`
- `SPORTS_IDS=1,18,13,4,16`
- حدود الإشارات: `EV_THRESHOLD`, `OUTLIER_THRESHOLD`, `STEAM_PROB_DELTA`
- `COOLDOWN_MINUTES` لمنع تكرار التنبيه لنفس السوق بسرعة.

## Telegram
- `TELEGRAM_ENABLED=1`
- `TELEGRAM_BOT_TOKEN=...`
- `TELEGRAM_CHAT_ID=...`

## تشغيل
```bash
python -m app.main
```

## Structure
- `app/config.py`
- `app/models.py`
- `app/fetcher.py`
- `app/normalizer.py`
- `app/signals.py`
- `app/database.py`
- `app/telegram.py`
- `app/main.py`

## اختبارات
```bash
pytest
```

## Risk Disclaimer
Sports betting carries financial risk and outcomes are uncertain even when using data-driven analysis. This project provides analytics only and does not guarantee profits. See: https://www.versussportssimulator.com/articles/what-financial-risks-come-with-sports-bets-and-attempts-to-win-back-losses
