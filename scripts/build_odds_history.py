#!/usr/bin/env python3
"""Replay the season and record the title/last odds after every day.

For each dated snapshot in data/daily/ we take the standings and the roster that
actually existed on that day, give every player his current projected rate, and
simulate the rest of that season. The result is a retrospective probability
curve: "given where everyone stood on that date, how often does each team win?"

Talent estimates are today's, so this is a look back with what we know now, not a
record of what we'd have said at the time. Every point on the line is computed the
same way, so the shape of the race is honest.

Vectorised with numpy: ~115 dates x 4,000 seasons is far too slow otherwise, and
this runs in CI rather than the browser.

Writes data/odds_history_2026.csv.
"""
import csv, sys
from datetime import date
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parent.parent
SEASON_START, SEASON_END = date(2026, 3, 25), date(2026, 9, 27)
FULL_SEASON_DAYS = (SEASON_END - SEASON_START).days
SIMS = 4000
RNG = np.random.default_rng(20260715)      # fixed: the curve shouldn't jitter between builds
# Team renames: old CSV name -> current name, so the season's history stays on one line.
ALIASES = {"Swank": "deep drivers"}


def main():
    proj = {r["player"]: r for r in csv.DictReader(open(REPO / "data/projections_2026.csv"))}
    swaps = list(csv.DictReader(open(REPO / "data/swaps_2026.csv")))
    swap_date = {s["out_player"]: s["swap_date"] for s in swaps}
    swap_in = {s["out_player"]: s["in_player"] for s in swaps}

    latest = max(f.stem.replace("points_", "") for f in (REPO / "data/daily").glob("points_*.csv"))
    global TODAY_DAYS_LEFT
    TODAY_DAYS_LEFT = max(1, (SEASON_END - date.fromisoformat(latest)).days)

    files = sorted((REPO / "data/daily").glob("points_*.csv"))
    out_rows = []
    for f in files:
        d = f.stem.replace("points_", "")
        rows = list(csv.DictReader(open(f)))
        if not rows:
            continue
        for r in rows:
            r["team"] = ALIASES.get(r["team"], r["team"])
        # Scale each player's healthy games-left back to this date, then subtract
        # the same injury he's carrying today. At the latest date this lands on
        # exactly the games_left the live card uses, so the curve meets the card.
        days_left = max(0, (SEASON_END - date.fromisoformat(d)).days)
        scale = days_left / TODAY_DAYS_LEFT if TODAY_DAYS_LEFT else 0

        teams = sorted({r["team"] for r in rows})
        totals = {t: np.zeros(SIMS) for t in teams}
        for t in teams:
            tr = [r for r in rows if r["team"] == t]
            totals[t] += sum(int(r["points"]) for r in tr)          # banked points, frozen included
            names = {r["player"] for r in tr}

            # Rebuild the slots exactly as the site does. A frozen player never
            # gets an arm; if his replacement isn't in the CSV yet, the
            # replacement takes the slot at zero. This keeps the HBP slot last
            # and the roster at 11 in every state.
            active = []
            for r in tr:
                n = r["player"]
                if n in swap_date and d >= swap_date[n]:
                    in_p = swap_in.get(n)
                    if in_p and in_p not in names:
                        active.append(in_p)                          # not scored yet: starts at 0
                    continue                                         # frozen: banked, no arm
                active.append(n)
            if not active:
                continue
            hbp_name = active[-1]

            for name in active:
                p = proj.get(name)
                if not p:
                    continue
                is_hbp = name == hbp_name
                a = float(p["hbp_alpha"] if is_hbp else p["hr_alpha"])
                b = float(p["hbp_beta"] if is_hbp else p["hr_beta"])
                agef = 1.0 if is_hbp else float(p["age_factor"] or 1)
                games_left = max(0.0, float(p["games_left_healthy"]) * scale - float(p["il_miss"]))
                rate = RNG.gamma(a, 1.0 / b, SIMS) * agef
                avail = RNG.beta(float(p["avail_a"]), float(p["avail_b"]), SIMS)
                pa = float(p["pa_per_game"]) * games_left * avail
                cnt = RNG.poisson(np.maximum(rate * pa, 0))
                totals[t] += cnt * (3 if is_hbp else 1)

        M = np.vstack([totals[t] for t in teams])                   # teams x sims
        best, worst = M.max(axis=0), M.min(axis=0)
        for i, t in enumerate(teams):
            win_ties = (M == best).sum(axis=0)
            last_ties = (M == worst).sum(axis=0)
            win = np.where(M[i] == best, 1.0 / win_ties, 0.0).sum() / SIMS
            last = np.where(M[i] == worst, 1.0 / last_ties, 0.0).sum() / SIMS
            out_rows.append({"date": d, "team": t,
                             "win_pct": round(float(win), 5),
                             "last_pct": round(float(last), 5)})

    out = REPO / "data/odds_history_2026.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "team", "win_pct", "last_pct"])
        w.writeheader(); w.writerows(out_rows)
    print(f"wrote {out} — {len(files)} dates x {len(set(r['team'] for r in out_rows))} teams", file=sys.stderr)


if __name__ == "__main__":
    main()
