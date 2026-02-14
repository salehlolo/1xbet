# BetsAPI 1xBet Signal Monitor (Python 3.11)

مشروع **تحليل بيانات وتنبيهات فقط**. لا يقوم بتسجيل دخول أو تنفيذ رهانات.

## الميزات
- جلب مباريات in-play و upcoming من BetsAPI (1xBet endpoints).
- تحويل الأودز إلى احتمالات ضمنية، وإزالة الـvig لاستخراج الاحتمالات العادلة.
- اكتشاف إشارات: `positive_ev` و `outlier` و `steam`.
- طبقة تحليل إضافية (`app/brain/analyst.py`) لإنتاج `overall_score` و `confidence`.
- تخزين snapshots/alerts/CLV في SQLite.
- إشعارات Telegram مع نظام cooldown.
- انضباط تنبيهات: حد يومي `MAX_ALERTS_PER_DAY`.

## تنبيه مسؤولية
النتائج الرياضية غير مؤكدة. هذا المشروع يقدّم أدوات تحليل فقط ولا يضمن الربحية.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## إعداد `.env`
- `BETS_API_KEY` (إلزامي)
- `SPORTS_IDS` مثال: `1,3,2`
- `ALLOWED_MARKET_GROUPS` مثال: `1X2,totals,handicap`
- `LOOKAHEAD_MINUTES` (فلترة المباريات القادمة)
- `MIN_MINUTES_TO_KICKOFF` (استبعاد المباريات التي ستبدأ خلال دقائق قليلة جدًا)
- `MAX_ALERTS_PER_DAY`
- `MIN_SCORE_THRESHOLD`
- `MAX_OVERROUND`
- `MAX_ANALYST_EVALS_PER_CYCLE` (تحديد أعلى عدد فرص تدخل طبقة التحليل المتقدم في كل دورة)
- `UPCOMING_ONLY=1` لتشغيل وضع المباريات القادمة فقط وتقليل الضغط
- `STEAM_PROB_DELTA`, `OUTLIER_THRESHOLD`, `EV_THRESHOLD`
- `COOLDOWN_MINUTES`
- Telegram: `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## التشغيل
```bash
python -m app.main
```

للوضع الموصى به (مباريات قريبة فقط):
- `LOOKAHEAD_MINUTES=60`
- `MIN_MINUTES_TO_KICKOFF=5`
- `UPCOMING_ONLY=1`
- `MAX_EVENTS_PER_CYCLE=120`
- `MAX_ANALYST_EVALS_PER_CYCLE=30`

## تقرير الأداء (CLV)
يوجد تجميع لأداء CLV في قاعدة البيانات عبر `Database.report_performance(days=7)` ويمكن ربطه لاحقًا بأمر CLI.

## الهيكل
- `app/config.py`
- `app/fetcher.py`
- `app/normalizer.py`
- `app/signals.py`
- `app/brain/analyst.py`
- `app/database.py`
- `app/telegram.py`
- `app/main.py`

## اختبارات
```bash
pytest
```

## مصدر توعية بالمخاطر
https://www.versussportssimulator.com/articles/what-financial-risks-come-with-sports-bets-and-attempts-to-win-back-losses
