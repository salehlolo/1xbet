# BetsAPI 1xBet Signal Monitor (Python 3.11)

مشروع **تحليل بيانات وتنبيهات فقط**. لا يقوم بتسجيل دخول أو تنفيذ رهانات.

## تنبيه مسؤولية
النتائج الرياضية غير مؤكدة. هذا المشروع يقدّم أدوات تحليل فقط ولا يضمن الربحية.

## إعداد سريع

### Linux / macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

ثم افتح `.env` وضع القيم الحقيقية فقط من البيئة لديك (بدون وضع أي أسرار داخل الكود):
- `BETS_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `UPCOMING_ONLY=1`
- `LOOKAHEAD_MINUTES=60`
- `MIN_MINUTES_TO_KICKOFF=5`

## التشغيل الصحيح
يمكنك التشغيل بأي من الطريقتين:
```bash
python -m app.main
```
أو:
```bash
python run.py
```


## فحص سريع لقيم البيئة
```bash
python run.py
python -c "from dotenv import find_dotenv, load_dotenv; import os; load_dotenv(find_dotenv('.env', usecwd=True), override=True); print('TELEGRAM_ENABLED=', os.getenv('TELEGRAM_ENABLED'))"
```

## ما الذي يتم فحصه عند البدء؟
Startup healthcheck يطبع فقط (بدون أسرار):
- هل `BETS_API_KEY` محمّل؟ `True/False`
- هل Telegram مفعل؟ `True/False`
- وضع التشغيل `UPCOMING_ONLY`
- قيم `LOOKAHEAD_MINUTES` و `MIN_MINUTES_TO_KICKOFF`

إذا هناك إعدادات ناقصة سيظهر اسم الإعداد الناقص فقط (مثل `BETS_API_KEY`) بدون طباعة القيم السرية.

## أهم الإعدادات
- `UPCOMING_ONLY=1` لتشغيل وضع المباريات القادمة فقط.
- `LOOKAHEAD_MINUTES=60` نافذة البحث القادمة.
- `MIN_MINUTES_TO_KICKOFF=5` لتجنب المباريات التي ستبدأ فورًا.
- `MAX_EVENTS_PER_CYCLE` لتقليل حمل fetch.
- `MAX_ANALYST_EVALS_PER_CYCLE` لتقليل حمل التحليل المتقدم.

## الاختبارات
```bash
pytest
```

## مصدر توعية بالمخاطر
https://www.versussportssimulator.com/articles/what-financial-risks-come-with-sports-bets-and-attempts-to-win-back-losses
