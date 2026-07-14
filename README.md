# Dingers ⚾

A home-run fantasy baseball league among friends, tracked automatically.

**📊 Live standings: https://dwq2002.github.io/Dingers/**

## How It Works

- Each manager drafts a team of 11 hitters before the season starts.
- **Scoring:** 1 point per home run.
- **The HBP wrinkle:** each team designates one player who scores **3 points per hit-by-pitch** instead of home runs.
- Highest total at the end of the regular season wins.

## Roster Rules

- Rosters are locked all season, with one exception: at the **All-Star break**, you may swap out any player who is on the injured list, in the minors, or out of the league entirely.
- Replacements must play the **same position** and can't already be on another team in the league.
- Swaps are made in **reverse standings order** (last place picks first).

## Under the Hood

- A GitHub Actions workflow runs `Dingers_2026.ipynb` daily at 11:00 UTC, pulling season stats from the MLB Stats API.
- Daily points snapshots are written to `data/daily/` and a standings email goes out to the league.
- The standings site (`docs/`) is served via GitHub Pages and updates from the daily CSVs, including automatic swap detection on rosters.

## Teams (2026)

Kid Named Dinger · Swank's Shanks · deep drivers · Bo · Swank's Tanks
