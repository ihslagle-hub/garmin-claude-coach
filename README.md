# Garmin → Claude: the daily pull

Pull your own Garmin Connect data **directly** — no manual export, no email — and land
it in Supabase so Claude (or any tool) can read it and coach you off your real numbers.

This is the automation behind the build: **watch → Garmin cloud → daily pull → your database → Claude.**
It replaces the "log in and request a data export" chore with a single script on a timer.

What it pulls, every day, on its own:

- **Activities** — runs, swims, rides, gym (distance, duration, HR, training load)
- **Sleep** — deep / light / REM / awake + sleep score
- **Daily stats** — resting HR, steps, calories, intensity minutes
- **HRV** — last-night average + status
- **Race predictors** — 5k / 10k / half / full estimates
- **Body composition** — weight, muscle mass and body fat off the Garmin Index scale
  *(the half most setups skip — it's what lets Claude answer "is my muscle holding while my fat drops?")*

---

## Quick start

```bash
pip install garminconnect requests

# 1. credentials (see .env.example)
cp .env.example .env      # then fill it in

# 2. one-time login (handles MFA, caches a token for ~a year)
python garmin_daily_pull.py --login

# 3. create the tables in your Supabase project (SQL editor)
#    paste schema.sql

# 4. pull + write
python garmin_daily_pull.py            # yesterday + today
python garmin_daily_pull.py --days 30  # backfill 30 days
python garmin_daily_pull.py --dry-run  # pull + print, write nothing
```

Then schedule `python garmin_daily_pull.py` once a day. Simplest is your computer's
**Task Scheduler / cron**; for an always-on version (and to deliver a morning coach)
import the ready-made workflow in [`n8n/garmin-coach.workflow.json`](n8n/garmin-coach.workflow.json).
Because it writes daily, a free Supabase project also stays warm and won't auto-pause.

Once the data's landing, the payoff is asking it questions — grab the 18 copy-paste
coaching prompts in [`PROMPTS.md`](PROMPTS.md).

---

## How it works

`python-garminconnect` logs into Garmin's cloud with your login and reads the same data the
Connect app shows, then the script normalises it and upserts it into the tables in `schema.sql`.

A few things worth knowing:

- **It reads Garmin's cloud, not the watch.** Sync your watch to the Connect app first (your
  phone does this automatically) or there's nothing new to pull.
- **First login may ask for an MFA code.** After that the cached token runs headless.
- **Garmin rate-limits logins.** If you see `429`, wait and try again — don't hammer it.
- **Keys stay yours.** The service key writes server-side; never ship it to a browser. RLS on.

---

## Files

| File | What |
|------|------|
| `garmin_daily_pull.py` | the pull (login, pull, upsert; `--login` / `--days N` / `--dry-run`) |
| `schema.sql` | the six tables the pull writes to |
| `.env.example` | the four env vars you need |
| `PROMPTS.md` | the 18-prompt coaching pack — the payoff |
| `n8n/garmin-coach.workflow.json` | importable n8n workflow: daily pull + morning coach (secrets-free template) |

---

## Then what?

The point of getting the data out is to ask it questions. Once it's in one place, Claude reads
it and coaches off it — session breakdowns, overtraining checks, body-comp reads, week-vs-month
trends, a morning plan that adjusts to your recovery. The pull is step one; the prompts are the
payoff → **[`PROMPTS.md`](PROMPTS.md)** (18 of them). For the hands-off morning coach, import
**[`n8n/garmin-coach.workflow.json`](n8n/garmin-coach.workflow.json)**.

Built by [aaronautomates](https://github.com/aaronparton2-sketch). MIT — do what you like with it.

---

**Built by [Mycelium AI](https://www.myceliumai.com.au)**, a Perth agency that builds websites, runs Google and Meta ads, and automates the admin for small businesses. Follow the builds on Instagram at [@aaronautomates](https://www.instagram.com/aaronautomates/).
