#!/usr/bin/env python3
"""Build rest-of-season projections for every rostered player.

Marcel-style (Tom Tango's baseline): weight the last three seasons, regress the
rate toward league average by a fixed number of plate appearances, and apply an
age curve. Everything comes from the MLB Stats API — the same source the notebook
already scores from.

The output is deliberately NOT a point estimate. For each player we emit the
parameters of a Gamma posterior over his true rate and a Beta posterior over how
often he plays, so the simulation draws a *rate* and a *workload* before it draws
a *count*. Poisson noise alone understates real variance badly and makes trailing
teams read as exactly 0%; the uncertainty lives in the parameters, not the dice.

Playing time is split in two so injuries are not counted twice:
  pa_per_game  — how much he bats when he is in the lineup (stable)
  play_rate    — how often he is in the lineup at all (where injuries live)

Writes data/projections_2026.csv, read by docs/index.html. Touches neither the
daily notebook nor the email.
"""
import csv, json, sys, unicodedata, difflib, urllib.request, re
from datetime import date
from pathlib import Path

SEASON, SEASON_END = 2026, date(2026, 9, 27)
WEIGHTS = {2026: 5, 2025: 4, 2024: 3}     # recent seasons count for more
REG_PA_HR, REG_PA_HBP = 1200, 800         # PA of league average added as a prior
PA_PER_GAME_PRIOR, PA_PER_GAME_REG = 3.9, 40   # regress part-timers' PA/G
# Games a player is expected to still miss from his current status.
IL_MISS = {"Injured 7-Day": 8, "Injured 10-Day": 12, "Injured 15-Day": 18,
           "Injured 60-Day": 55, "Reassigned to Minors": 40, "Suspended # days": 10}
REPO = Path(__file__).resolve().parent.parent


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dingers-projections"})
    return json.load(urllib.request.urlopen(req, timeout=45))


def norm(s):
    return (unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
            .lower().replace(".", "").replace("'", "").strip())


def league_rates():
    d = get(f"https://statsapi.mlb.com/api/v1/teams/stats?season={SEASON}"
            f"&group=hitting&stats=season&sportIds=1")
    pa = hr = hbp = 0
    for s in d["stats"][0]["splits"]:
        pa += s["stat"].get("plateAppearances", 0)
        hr += s["stat"].get("homeRuns", 0)
        hbp += s["stat"].get("hitByPitch", 0)
    return hr / pa, hbp / pa


def team_games():
    d = get(f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"
            f"&season={SEASON}&standingsTypes=regularSeason")
    out = {}
    for rec in d["records"]:
        for t in rec["teamRecords"]:
            gp = t.get("gamesPlayed") or (t["wins"] + t["losses"])
            out[t["team"]["id"]] = gp
    return out


def rosters_and_swaps():
    nb = json.loads((REPO / "Dingers_2026.ipynb").read_text())
    c1 = "".join(nb["cells"][1]["source"])
    lists = {m.group(1): re.findall(r'"([^"]+)"', m.group(2))
             for m in re.finditer(r"^(\w+_team)\s*=\s*\[(.*?)\]", c1, re.S | re.M)}
    TEAM = {"ethan_team": "Swank's Tanks", "bo_team": "Bo", "dave_team": "Kid Named Dinger",
            "teheng_team": "Swank's Shanks", "swank_team": "deep drivers"}
    swaps = list(csv.DictReader(open(REPO / "data/swaps_2026.csv")))
    sub = {s["out_player"]: s["in_player"] for s in swaps}
    return {TEAM[k]: {"players": [sub.get(p, p) for p in v],
                      "hbp": sub.get(v[-1], v[-1])} for k, v in lists.items()}


def player_index():
    d = get(f"https://statsapi.mlb.com/api/v1/sports/1/players?season={SEASON}")
    idx = {}
    for p in d["people"]:
        idx.setdefault(norm(p["fullName"]), p)
    return idx


def resolve(name, idx):
    n = norm(name)
    if n in idx:
        return idx[n]
    m = difflib.get_close_matches(n, idx.keys(), n=1, cutoff=0.82)
    return idx[m[0]] if m else None


def history(pid):
    d = get(f"https://statsapi.mlb.com/api/v1/people/{pid}"
            f"?hydrate=stats(group=[hitting],type=[yearByYear]),currentTeam")
    p = d["people"][0]
    years = {}
    for st in p.get("stats", []):
        for sp in st.get("splits", []):
            if sp.get("sport", {}).get("id") != 1:      # MLB only, not the minors
                continue
            a = years.setdefault(int(sp["season"]), {"pa": 0, "hr": 0, "hbp": 0, "g": 0})
            s = sp["stat"]
            a["pa"] += s.get("plateAppearances", 0)
            a["hr"] += s.get("homeRuns", 0)
            a["hbp"] += s.get("hitByPitch", 0)
            a["g"] += s.get("gamesPlayed", 0)
    return p, years


def age_factor(age):
    # Marcel's curve: peak at 29, gentle decline after, gentle growth before.
    if age is None:
        return 1.0
    return 1 - 0.003 * (age - 29) if age > 29 else 1 + 0.006 * (29 - age)


def status_index():
    st = {}
    for t in get(f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={SEASON}")["teams"]:
        try:
            r = get(f"https://statsapi.mlb.com/api/v1/teams/{t['id']}/roster"
                    f"?rosterType=fullSeason&season={SEASON}")
        except Exception:
            continue
        for e in r.get("roster", []):
            st[e["person"]["id"]] = (e.get("status", {}).get("description", "Active"), t["id"])
    return st


def main():
    run_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    lg_hr, lg_hbp = league_rates()
    idx, status, tgames = player_index(), status_index(), team_games()
    teams = rosters_and_swaps()
    frozen = {s["out_player"] for s in csv.DictReader(open(REPO / "data/swaps_2026.csv"))}
    print(f"league HR/PA={lg_hr:.5f} HBP/PA={lg_hbp:.5f}", file=sys.stderr)

    rows, missing = [], []
    for team, info in teams.items():
        for name in info["players"]:
            p = resolve(name, idx)
            if not p:
                missing.append(name); continue
            person, years = history(p["id"])
            bd = person.get("birthDate")
            age = None
            if bd:
                b = date.fromisoformat(bd)
                age = SEASON - b.year - ((7, 1) < (b.month, b.day))

            num_hr = num_hbp = den = 0.0
            for y, w in WEIGHTS.items():
                a = years.get(y)
                if a and a["pa"]:
                    num_hr += w * a["hr"]; num_hbp += w * a["hbp"]; den += w * a["pa"]

            # Gamma posterior on the true per-PA rate. The league-average
            # pseudo-counts ARE the regression: a thin record lands near league
            # average with a wide posterior; a long record barely moves.
            hr_a, hr_b = num_hr + lg_hr * REG_PA_HR, den + REG_PA_HR
            hbp_a, hbp_b = num_hbp + lg_hbp * REG_PA_HBP, den + REG_PA_HBP

            cur = years.get(SEASON, {"pa": 0, "g": 0})
            st, team_id = status.get(p["id"], ("Active", None))
            tg = tgames.get(team_id, 96)
            games_left = max(0, 162 - tg)

            # How much he bats when he plays, regressed for small samples.
            pa_pg = ((cur["pa"] + PA_PER_GAME_PRIOR * PA_PER_GAME_REG)
                     / (cur["g"] + PA_PER_GAME_REG))

            # How often he's in the lineup. Beta posterior over his play rate;
            # this is where injury risk lives, kept separate from pa_pg so a
            # missed month isn't punished twice.
            played, sat = cur["g"], max(0, tg - cur["g"])
            av_a, av_b = played + 6.0, sat + 2.0

            miss = IL_MISS.get(st, 0 if st == "Active" else 10)
            eff_games = max(0, games_left - miss)

            rows.append({
                "as_of": run_date.isoformat(),
                "days_left_at_build": max(0, (SEASON_END - run_date).days),
                "player": name, "team": team, "mlb_id": p["id"],
                "is_hbp_slot": int(name == info["hbp"]), "is_frozen": int(name in frozen),
                "age": age if age is not None else "",
                "hr_alpha": round(hr_a, 4), "hr_beta": round(hr_b, 1),
                "hbp_alpha": round(hbp_a, 4), "hbp_beta": round(hbp_b, 1),
                "age_factor": round(age_factor(age), 4),
                "pa_per_game": round(pa_pg, 4),
                "avail_a": round(av_a, 1), "avail_b": round(av_b, 1),
                "games_left": eff_games, "status": st,
                "proj_hr": round((hr_a / hr_b) * age_factor(age) * pa_pg * eff_games
                                 * (av_a / (av_a + av_b)), 1),
                "proj_hbp": round((hbp_a / hbp_b) * pa_pg * eff_games
                                  * (av_a / (av_a + av_b)), 1),
            })

    if missing:
        print(f"UNRESOLVED: {missing}", file=sys.stderr); sys.exit(1)
    out = REPO / "data/projections_2026.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {out} — {len(rows)} players", file=sys.stderr)


if __name__ == "__main__":
    main()
