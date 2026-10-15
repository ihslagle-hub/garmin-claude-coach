#!/usr/bin/env python3
"""Range backfill: activities (+VO2 max), weekly VO2 max, race predictions for a past window."""
import argparse
import datetime as dt
import time

import garmin_daily_pull as g0

g0.TABLE_KEYS["vo2"] = ("garmin_vo2max", "date")


def chunks(start, end, days):
    d = start
    while d <= end:
        e = min(d + dt.timedelta(days=days - 1), end)
        yield d, e
        d = e + dt.timedelta(days=1)


def act_row(a):
    return {
        "activity_id": a.get("activityId"),
        "activity_date": (a.get("startTimeLocal") or "")[:10] or None,
        "started_at": a.get("startTimeLocal"),
        "activity_type": (a.get("activityType") or {}).get("typeKey"),
        "name": a.get("activityName"),
        "duration_s": g0._i(a.get("duration")),
        "distance_m": g0._i(a.get("distance")),
        "avg_hr": g0._i(a.get("averageHR")),
        "max_hr": g0._i(a.get("maxHR")),
        "calories": g0._i(a.get("calories")),
        "elevation_gain_m": g0._i(a.get("elevationGain")),
        "aerobic_te": a.get("aerobicTrainingEffect"),
        "anaerobic_te": a.get("anaerobicTrainingEffect"),
        "training_load": a.get("activityTrainingLoad"),
        "moderate_min": g0._i(a.get("moderateIntensityMinutes")),
        "vigorous_min": g0._i(a.get("vigorousIntensityMinutes")),
        "vo2max": a.get("vO2MaxValue"),
    }


def vo2_from(m):
    item = m[0] if isinstance(m, list) and m else m
    if not isinstance(item, dict):
        return None
    gen = item.get("generic") or {}
    return gen.get("vo2MaxPreciseValue") or gen.get("vo2MaxValue")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start)
    end = dt.date.fromisoformat(a.end)
    g = g0.connect_with_retry()

    n_act = 0
    for s, e in chunks(start, end, 30):
        res = g0._safe(g.get_activities_by_date, s.isoformat(), e.isoformat(), label="activities") or []
        rows = [act_row(x) for x in res]
        g0.upsert("activities", rows)
        n_act += len(rows)
        time.sleep(1.5)

    vo = []
    d = start
    while d <= end:
        m = g0._safe(g.get_max_metrics, d.isoformat(), label="max_metrics")
        v = vo2_from(m)
        if v:
            vo.append({"date": d.isoformat(), "vo2max": v})
        d += dt.timedelta(days=7)
        time.sleep(1.0)
    g0.upsert("vo2", vo)

    preds = []
    for s, e in chunks(start, end, 180):
        res = g0._safe(g.get_race_predictions, s.isoformat(), e.isoformat(), "daily", label="race_predictions")
        for r in (res if isinstance(res, list) else []):
            if r.get("calendarDate"):
                preds.append({
                    "date": r.get("calendarDate"),
                    "time_5k_s": g0._i(r.get("time5K")),
                    "time_10k_s": g0._i(r.get("time10K")),
                    "time_half_s": g0._i(r.get("timeHalfMarathon")),
                    "time_full_s": g0._i(r.get("timeMarathon")),
                })
        time.sleep(1.5)
    g0.upsert("race", preds)
    print(f"[backfill] activities={n_act} vo2_snapshots={len(vo)} race_predictions={len(preds)}")


if __name__ == "__main__":
    main()
