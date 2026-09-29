"""One-off: the 2026 season-over email. Builds email/final_2026.html from the
final daily CSV. Sent by .github/workflows/final-email.yml."""
import csv
from pathlib import Path

FINAL_CSV = "data/daily/points_2026-09-28.csv"   # games through 2026-09-27, the last day
SITE = "https://dwq2002.github.io/Dingers/"
INK, TEXT, MUTED = "#1a237e", "#1f2333", "#6a7086"
TRACK, DIVIDE = "#e9ebf6", "#eef0f7"
GOLD, GOLD_BG = "#b7860b", "#fffae9"
LAST, LAST_BG = "#8a1c1c", "#fdecec"
FONT = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

LOGOS = {
    "Kid Named Dinger": "https://raw.githubusercontent.com/Dwq2002/Dingers/main/assets/team_icons/Kid_Named_Dinger.JPEG",
    "deep drivers":    "https://github.com/user-attachments/assets/03d3f450-bde2-4da9-a21e-785f599db9ef",
    "Swank's Shanks":  "https://raw.githubusercontent.com/Dwq2002/Dingers/main/assets/team_icons/Swanks_Shanks.JPG",
    "Swank's Tanks":   "https://raw.githubusercontent.com/Dwq2002/Dingers/main/assets/team_icons/Swanks_Tanks.JPEG",
    "Bo":              "https://github.com/user-attachments/assets/aa5ab7d8-a7bc-4172-af3f-7f5003c3e031",
}
MANAGERS = {"Kid Named Dinger": "Dave (DQ)", "Swank's Shanks": "Jack", "deep drivers": "Swank",
            "Bo": "Bo", "Swank's Tanks": "Ethan"}
CHAMPIONS = [("2026", "Jack", "Swank's Shanks"), ("2025", "Swank", ""), ("2024", "Bo", ""), ("2023", "Ethan", "")]

totals = {}
with open(FINAL_CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        totals[r["team"]] = totals.get(r["team"], 0) + int(r["points"])
standings = sorted(totals.items(), key=lambda kv: -kv[1])
(win, win_pts), (lose, lose_pts) = standings[0], standings[-1]
assert standings[1][1] != win_pts and standings[-2][1] != lose_pts, "tie: needs the pitcher-walks tiebreaker"

def logo(team, size, radius):
    return (f'<img src="{LOGOS[team]}" width="{size}" height="{size}" alt="" '
            f'style="display:block;margin:0 auto;border-radius:{radius};object-fit:cover">')

def h3(t):
    return f'<h3 style="margin:28px 0 10px;font:700 15px {FONT};color:{INK};letter-spacing:.02em">{t}</h3>'

# Winner + loser headline
def headline(tag, team, pts, fg, bg):
    return (f'<td width="49%" style="background:{bg};border:2px solid {fg};border-radius:12px;'
            f'padding:14px 8px;text-align:center;vertical-align:top">'
            f'<div style="font:700 11px {FONT};color:{fg};letter-spacing:.08em;text-transform:uppercase">{tag}</div>'
            f'<div style="margin:8px 0">{logo(team, 64, "50%")}</div>'
            f'<div style="font:800 16px {FONT};color:{TEXT}">{team}</div>'
            f'<div style="font:400 13px {FONT};color:{MUTED}">{MANAGERS[team]}</div>'
            f'<div style="margin-top:6px;font:800 22px {FONT};color:{INK}">{pts} pts</div></td>')
headline_html = ('<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                 + headline("🏆 Champion", win, win_pts, GOLD, GOLD_BG)
                 + '<td width="2%"></td>'
                 + headline("💀 Last place", lose, lose_pts, LAST, LAST_BG)
                 + '</tr></table>')

# Olympic podium: 2nd | 1st | 3rd, step heights 1st > 2nd > 3rd
def step(place, medal, team, pts, height, bg):
    return (f'<td width="33%" valign="bottom" style="padding:0 3px;text-align:center">'
            f'{logo(team, 52, "50%")}'
            f'<div style="margin:6px 0 2px;font:700 13px {FONT};color:{TEXT}">{team}</div>'
            f'<div style="margin-bottom:6px;font:400 12px {FONT};color:{MUTED}">{pts} pts</div>'
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td height="{height}" style="height:{height}px;background:{bg};border-radius:8px 8px 0 0;'
            f'text-align:center;vertical-align:top;padding-top:8px;font:800 22px {FONT};color:#ffffff">'
            f'{medal}<div style="font:800 20px {FONT};color:#ffffff">{place}</div></td></tr></table></td>')
(t1, p1), (t2, p2), (t3, p3) = standings[:3]
podium_html = ('<table width="100%" cellpadding="0" cellspacing="0"><tr>'
               + step("2nd", "🥈", t2, p2, 80, "#6b7288")
               + step("1st", "🥇", t1, p1, 112, INK)
               + step("3rd", "🥉", t3, p3, 58, "#8a93ad")
               + '</tr></table>')

# Final standings, winner and loser rows marked
rows = ""
for rank, (team, pts) in enumerate(standings, 1):
    if team == win:
        bg, border, tag = GOLD_BG, GOLD, f'<span style="font:700 11px {FONT};color:{GOLD}">🏆 CHAMPION</span>'
    elif team == lose:
        bg, border, tag = LAST_BG, LAST, f'<span style="font:700 11px {FONT};color:{LAST}">💀 LAST PLACE</span>'
    else:
        bg, border, tag = "#ffffff", DIVIDE, ""
    gap = "" if rank == 1 else f'{win_pts - pts} back'
    rows += (f'<tr style="background:{bg}">'
             f'<td style="padding:10px 6px 10px 10px;border-left:4px solid {border};border-bottom:1px solid {DIVIDE};'
             f'font:700 14px {FONT};color:{MUTED};width:18px">{rank}</td>'
             f'<td style="padding:10px 8px 10px 0;border-bottom:1px solid {DIVIDE};width:30px">'
             f'<img src="{LOGOS[team]}" width="28" height="28" alt="" style="border-radius:6px;object-fit:cover;vertical-align:middle"></td>'
             f'<td style="padding:10px 8px 10px 0;border-bottom:1px solid {DIVIDE}">'
             f'<div style="font:600 14px {FONT};color:{TEXT}">{team}</div>'
             f'<div style="font:400 12px {FONT};color:{MUTED}">{MANAGERS[team]}{" · " + gap if gap else ""}</div>{tag}</td>'
             f'<td align="right" style="padding:10px 12px 10px 0;border-bottom:1px solid {DIVIDE};'
             f'font:800 18px {FONT};color:{INK}">{pts}</td></tr>')
standings_html = f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">{rows}</table>'

# Past champions
crows = ""
for year, mgr, team in CHAMPIONS:
    new = year == "2026"
    crows += (f'<tr style="background:{GOLD_BG if new else "#ffffff"}">'
              f'<td style="padding:8px 10px;border-bottom:1px solid {DIVIDE};font:700 14px {FONT};color:{MUTED};width:50px">{year}</td>'
              f'<td style="padding:8px 0;border-bottom:1px solid {DIVIDE};font:600 14px {FONT};color:{TEXT}">🏆 {mgr}'
              + (f' <span style="font-weight:400;color:{MUTED};font-size:12px">· {team} · NEW</span>' if new else "")
              + '</td></tr>')
champs_html = f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">{crows}</table>'

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f2f3f8">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f2f3f8"><tr><td align="center" style="padding:16px 10px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px">
<tr><td style="padding:22px 18px 24px">
  <div style="font:800 26px {FONT};color:{INK};text-align:center">⚾ Dingers 2026 is final</div>
  <p style="margin:6px 0 18px;font:400 14px {FONT};color:{MUTED};text-align:center">
    The regular season ended September 27. Here is how it finished.</p>
  {headline_html}
  <p style="margin:14px 0 0;font:400 14px {FONT};color:{TEXT};text-align:center">
    Congratulations to <b>{MANAGERS[win]}</b>, who wins it by {win_pts - standings[1][1]} points.
    <b>{MANAGERS[lose]}</b> finishes last and takes the punishment.</p>
  {h3("🏅 The podium")}
  {podium_html}
  {h3("📊 Final standings")}
  {standings_html}
  {h3("🏆 League champions")}
  {champs_html}
  <p style="margin:24px 0 0;font:600 14px {FONT};text-align:center">
    <a href="{SITE}" style="color:{INK};text-decoration:none">See the full season on the site &rarr;</a></p>
  <p style="margin:16px 0 0;font:400 12px {FONT};color:{MUTED};text-align:center">
    This is the last email of the season. See you next spring.</p>
</td></tr></table></td></tr></table></body></html>"""

Path("email/final_2026.html").write_text(html, encoding="utf-8")
print("built email/final_2026.html:", standings)
