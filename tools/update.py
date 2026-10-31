"""Add new Alabama results to The Crimson Ledger.

Usage: python3 -I update.py PAGE.html allgames.json NEW_GAMES.json
NEW_GAMES.json is a list of rows:
  [date "YYYY-MM-DD", season, opponent, site "H"/"A"/"N", result "W"/"L"/"T",
   alabama_pts, opp_pts, conference_game 0/1, postseason label or "", neutral city or "", 0]
Opponent names must match the site's spelling (e.g. "LSU", "Ole Miss", "Vanderbilt").
The script merges the rows (skipping dates already present), rewrites the page's
game data, and recomputes the current season's line in the season table.
"""
import json, re, sys

page, data, newf = sys.argv[1:4]
games = json.load(open(data))
new = json.load(open(newf))
have = {g[0] for g in games}
added = [n for n in new if n[0] not in have]
games = sorted(games + added, key=lambda g: g[0])
json.dump(games, open(data, "w"), separators=(",", ":"), ensure_ascii=False)

h = open(page).read()
h = re.sub(r"const RAW=\[.*?\];\n",
           lambda m: "const RAW=" + json.dumps(games, separators=(",", ":"), ensure_ascii=False) + ";\n",
           h, count=1, flags=re.S)

for season in sorted({n[1] for n in added}):
    gs = [g for g in games if g[1] == season]
    w = sum(g[4] == "W" for g in gs); l = sum(g[4] == "L" for g in gs); t = len(gs) - w - l
    conf = [g for g in gs if g[7]]
    cw = sum(g[4] == "W" for g in conf); cl = sum(g[4] == "L" for g in conf); ct = len(conf) - cw - cl
    post = "; ".join(f"{g[4]} {g[8]}" for g in gs if g[8] and "SEC Championship" not in g[8]) or "In progress"
    m = re.search(rf"\n{season},([^,\n]+),[^\n`]*", h)
    if m:
        coach = m.group(1)
        old = m.group(0)
        ap = old.split(",")[9] if len(old.split(",")) > 9 else ""
        h = h.replace(old, f"\n{season},{coach},{w},{l},{t},{cw},{cl},{ct},{post},{ap},", 1)
open(page, "w").write(h)
print(f"added {len(added)} game(s); total {len(games)}")
for a in added:
    print("  ", a[0], a[2], a[4], f"{a[5]}-{a[6]}")
