# ZarinPal Insight

A production-oriented analytics dashboard for the ZarinPal challenge. It models payment data at **session level** (payment intent) while retaining attempt-level evidence for traceability.

## What it does

- Payment health overview
- First-attempt success, retry and recovery analysis
- Lost payment opportunity estimation
- Peer benchmarking by category and merchant-volume band
- PSP performance analysis with minimum-sample safeguards
- Time and amount opportunity analysis
- Explainability drawer with formula, filters and evidence sessions
- Transaction/session timeline modal
- Responsive desktop/mobile UI
- AI-ready insight payloads (the UI uses deterministic insight facts; an LLM can be added later)

## Data model

`row = payment attempt`, `session_key = payment intent`.

Successful attempt/session statuses are `Verified` or `Paid`. `Reversed` is kept separate.
`adjusted_fee` is **not** presented as ZarinPal's real fee; it is only used for relative analysis if enabled.

## Quick start

### 1. Put the challenge dataset in `data/`

The loader automatically detects the first supported dataset in `data/`. Supported formats:

- `.csv`
- `.csv.gz`
- `.parquet`

If the file has a different name, no rename is required. You can also select it explicitly with `DATA_FILE`.

```bash
# optional downloader if its URL is configured
python scripts/download_data.py
```

### 2. Build DuckDB analytics database

```bash
python scripts/build_db.py
```

This creates `data/analytics.duckdb` and materializes session-level facts.

### 3. Backend + LLM

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` from `.env.example` and set `OPENAI_API_KEY`. The assistant uses the OpenAI Responses API and sends only a grounded analytical context built from DuckDB. The default model is `gpt-5.6-luna`; change it with `OPENAI_MODEL` if needed.

Then run:

```bash
uvicorn app:app --reload --port 8000
```

### 4. Frontend

Requires Node 20+.

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Environment

Frontend API URL defaults to `http://localhost:8000/api` and can be overridden with `VITE_API_URL`.

Backend DB path can be overridden with `ZP_DB_PATH`.

## Important analytical rules

- Never aggregate raw attempt rows as if they were unique payments.
- Session-level amount is taken once per session.
- First attempt is the minimum `try_seq` among actual attempts (`try_seq > 0`).
- Final session status is based on the session's terminal state.
- Recovery means first actual attempt was not successful, but a later attempt was successful.
- Peer benchmarks require a comparable category and a volume band; tiny peer groups are suppressed.

## Demo flow

1. Overview → identify the biggest opportunity.
2. Open `How was this calculated?`.
3. Drill into evidence sessions.
4. Open one session → inspect attempt timeline.
5. Benchmark → compare with peer median.
6. Payments → inspect trend and funnel.
7. Mobile viewport → repeat the same flow.


## نسخه تکمیل‌شده UI

این نسخه همان ساختار اصلی React + FastAPI + DuckDB پروژه را حفظ می‌کند و UI/UX را گسترش می‌دهد:

- Merchant selector واقعی از API
- Overview حرفه‌ای با KPI، Health Score و نمودار فروش
- PSP Analytics
- تحلیل ساعت و مبلغ
- Insight Engine + Evidence Modal
- Drill-down از Insight به Session
- Session Explorer با search/filter/pagination
- Session Timeline و Attempt-level evidence
- Benchmark و peer table
- Customer analytics بر اساس payer_card_key شبه‌ناشناس
- Segmentation پایه VIP / Loyal / New
- Assistant تحلیلی متصل به LLM با context واقعی DuckDB
- Dark/Light theme
- Responsive mobile-first
- Vazirmatn
- Skeleton loading
- Tooltip و Modal
- بدون ساختن دیتای جعلی برای KPIها

### ترتیب ساخت دیتابیس

```bash
python scripts/build_db.py
python scripts/build_metrics.py
python scripts/build_evidence.py
```

بعد Backend و Frontend را اجرا کن.


## LLM setup

Copy `backend/.env.example` to `backend/.env` and set `OPENAI_API_KEY`. The `/api/merchants/{merchant_id}/ask` POST endpoint sends a grounded context containing merchant KPIs, recent daily metrics, hourly metrics, PSP metrics, customer aggregates, peer metrics and existing insights to the model. The model is explicitly instructed not to invent statistics.

The frontend Assistant page calls this endpoint; it is no longer a deterministic keyword-answer demo.

## Real charts

All dashboard charts are API-backed. The frontend does not contain mock chart datasets. Daily, hourly, amount-distribution, monthly, weekday and PSP charts are computed from `sessions`/`attempts` in DuckDB. Empty datasets render an explicit empty state instead of fabricated values.
