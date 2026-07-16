# Dingers ⚾

A home-run fantasy baseball league among friends. Drafted once, scored automatically, argued about daily.

### 📊 **[Live standings & season race →](https://dwq2002.github.io/Dingers/)**

A bot pulls every roster's stats from the MLB Stats API each morning, updates the site, and emails the league the overnight damage.

---

## 🏆 Champions

| Year | Winner |
|:----:|:-------|
| 2023 | **Ethan** |
| 2024 | **Bo** |
| 2025 | **Swank** |
| 2026 | *in progress* |

## Scoring

| | |
|:--|:--|
| **Home run** | 1 point |
| **HBP slot** | 3 points per hit-by-pitch — and **no** points for homers |

Highest total at the end of the MLB regular season wins. Last place gets the punishment.

**Tiebreaker:** most walks by your drafted pitcher. He scores nothing otherwise — he exists purely to break ties.

## Rosters

Twelve picks, one per slot:

```
C · 1B · 2B · 3B · SS · LF · CF · RF · DH · UTIL · HBP · Pitcher (tiebreaker)
```

- A player is drafted at **the position he played the most games at last season**. That's how the league defines eligibility — not whatever the MLB API lists him at today.
- **One player per team**, meaning nobody can be on two rosters.
- The **HBP slot** is its own thing: that player scores only on hit-by-pitches, at 3 points each.

## Swaps

Rosters are locked all season, with two windows:

- **Until opening day** — injury swaps allowed.
- **At the All-Star break** — unlimited swaps, but only for players who are **injured or in the minors**. Replacements must be the **same drafted position** and unrostered.

Swaps do **not** reshuffle points. The player you drop **freezes** at the points he'd already banked and your team keeps them forever. The player you add **starts from zero**, so only what he does from the swap onward counts. Your total doesn't move on swap day.

> Aaron Judge was dropped at 17 points. Kid Named Dinger still has those 17. Jac Caglianone started at 0.

## Teams (2026)

| Team | Manager |
|:--|:--|
| Kid Named Dinger | Dave (DQ) |
| Swank's Shanks | Jack |
| deep drivers | Swank |
| Bo | Bo |
| Swank's Tanks | Ethan |

## The site

- **Standings & season race** — filter by date range, or since the break.
- **Team rosters** — every slot with its draft position. Swapped slots show the dropped player struck through with his frozen points, an arrow, and what his replacement has added since.
- **Positional breakdown** — who's winning at each spot.
- **Projected finish** — odds of taking it and odds of coming last, from 10,000 simulated seasons, with a 5th–95th percentile band.
- **Odds over time** — how the title race and the last-place race have moved all season.

### How the projections work

Each player gets a [Marcel-style](http://www.tangotiger.net/archives/stud0346.shtml) projection: his last three MLB seasons weighted 5/4/3 toward the present, regressed toward league average (hard for thin records, barely at all for veterans), and age-adjusted. That rate is applied to the plate appearances he's expected to get across his team's remaining games. Injured players are docked the games they're likely to miss; frozen players add nothing.

The season is then simulated 10,000 times. Each run re-draws both a player's *true rate* and *how much he plays* before drawing homers — so the odds carry genuine uncertainty rather than dice-roll noise, and nobody who isn't mathematically eliminated reads as a flat 0%.

Everything recomputes from the live CSVs on every page load, so the odds move as the season does: a big night shifts them, and they harden as the days run out.

The **Odds Over Time** chart replays every past date with the standings and roster that existed then. Talent estimates are today's, so it's a look back with what we know now rather than a record of what we'd have said at the time — but every point is computed identically, so the shape of the race is honest.

## Under the hood

| Path | What |
|:--|:--|
| `Dingers_2026.ipynb` | Scores every roster off the MLB Stats API, writes the daily CSV, builds the email |
| `data/daily/` | One points snapshot per day, plus `latest.csv` |
| `data/swaps_2026.csv` | Swap ledger — source of truth for frozen points and baselines |
| `data/positions_2026.csv` | Draft position for all 55 players |
| `data/projections_2026.csv` | Rest-of-season projections, rebuilt daily |
| `data/odds_history_2026.csv` | Title/last odds after every day of the season |
| `scripts/build_projections.py` | Builds the projections from the MLB Stats API |
| `scripts/build_odds_history.py` | Replays the season to build the odds chart |
| `docs/index.html` | The standings site (GitHub Pages) |

**Workflows:** `run-notebook.yml` scores and emails at 11:00 UTC daily. `projections.yml` rebuilds projections at 13:00 UTC, deliberately kept separate so it can never take the email down with it.

### Recording a swap

Add one row to `data/swaps_2026.csv`, and swap the player in the roster list in `Dingers_2026.ipynb`:

```csv
team,out_player,out_points_frozen,in_player,in_baseline_hr,swap_date
Swank's Tanks,Nolan Gorman,7,Ozzie Albies,14,2026-07-15
```

- `out_points_frozen` — the points he had when dropped. Kept by the team, forever.
- `in_baseline_hr` — the new player's season HR total at the swap. Subtracted out, so he starts from zero.

The site, the email, the positional table, and the projections all pick it up from there. Nothing else to edit.
