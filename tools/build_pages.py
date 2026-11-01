"""Build the opponent and season pages, their hub pages, sitemap.xml and robots.txt.

Usage (from the repo root): python3 -I tools/build_pages.py
Reads data/allgames.json plus the season table (SCSV) and titles from tools/page-source.html,
and data/stories.json, and writes vs/, seasons/, stories/, sitemap.xml and robots.txt. Run it after every weekly update.
"""
import json, re, os, shutil, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://thecrimsonledger.com"
games = json.load(open(os.path.join(ROOT, "data/allgames.json")))
src = open(os.path.join(ROOT, "tools/page-source.html")).read()

# ---------- data ----------
scsv = re.search(r"const SCSV=`(.*?)`", src, re.S).group(1).strip().splitlines()
SEASONS = {}
for r in scsv:
    c = r.split(",")
    SEASONS[int(c[0])] = dict(year=int(c[0]), coach=c[1], w=int(c[2]), l=int(c[3]), t=int(c[4]),
                              cw=c[5], cl=c[6], ct=c[7], post=c[8], ap=c[9], vac=bool(c[10].strip()) if len(c) > 10 else False)
SCHED = json.loads(re.search(r"const SCHED=(\[.*?\]);", src).group(1))
TITLES = {int(y) for y in re.findall(r"\[(\d{4}),\"[A-Za-z]+\"\]", re.search(r"const TITLES=\[(.*?)\];", src).group(1))}

G = [dict(d=g[0], s=g[1], opp=g[2], loc=g[3], res=g[4], a=g[5], o=g[6], conf=bool(g[7]), note=g[8], city=g[9], flag=g[10]) for g in games]
for g in G:
    g["coach"] = SEASONS.get(g["s"], {}).get("coach", "")

def slug(o):
    o = o.lower().replace("&", "and")
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", o))

E = html.escape
MON = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
def fdate(d):
    y, m, dd = d.split("-"); return f"{MON[int(m)-1]} {int(dd)}, {y}"
def rec(w, l, t): return f"{w}–{l}" + (f"–{t}" if t else "")
def site_txt(g):
    return {"H": "Home", "A": "Away"}.get(g["loc"], g["city"] or "Neutral")
def score(g): return f"{g['a']}–{g['o']}"
def wl(gs):
    w = sum(g["res"] == "W" for g in gs); l = sum(g["res"] == "L" for g in gs); return w, l, len(gs) - w - l

# ---------- page shell ----------
CSS = """:root{--bg:#EEF0EE;--surface:#fff;--fg:#1A1C1D;--muted:#5F6567;--line:#D0D5D6;--crim:#9E1B32;--board:#17191A;--boardfg:#F2F2F0;--gold:#E9B44C;
--display:"Big Shoulders Display","Arial Narrow",Impact,sans-serif;--body:"Source Serif 4",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#111314;--surface:#1B1E1F;--fg:#E8EAEA;--muted:#9BA2A4;--line:#30353A;--crim:#EC6A80;--board:#08090A;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.55 var(--body)}
.wrap{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.top{background:var(--board);color:var(--boardfg);border-bottom:4px solid #9E1B32}
.top .wrap{display:flex;align-items:center;gap:18px;min-height:56px;flex-wrap:wrap}
.brand{font:900 22px/1 var(--display);text-transform:uppercase;color:var(--boardfg);text-decoration:none;margin-right:auto}.brand span{color:var(--gold)}
.top nav a{font:600 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:#C9CDCD;text-decoration:none;padding:8px 0}
.top nav{display:flex;gap:18px}.top nav a:hover{color:var(--gold)}
.hero{background:var(--board);color:var(--boardfg);padding:36px 0 34px}
.crumbs{font:600 12px/1.4 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}.crumbs a{color:var(--gold);text-decoration:none}
h1{font:800 clamp(38px,7vw,72px)/.95 var(--display);text-transform:uppercase;margin:12px 0 14px}
.lede{max-width:62ch;color:#C9CDCD;margin:0;font-size:18px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:26px}
.tile{border-top:3px solid var(--gold);background:rgba(255,255,255,.05);padding:12px 14px}
.tile b{display:block;font:800 30px/1.1 var(--display);color:#fff}.tile span{font:600 11px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:#A3A9AB}
main{padding:10px 0 40px}
h2{font:800 clamp(28px,4.5vw,40px)/1 var(--display);text-transform:uppercase;margin:44px 0 16px;padding-bottom:10px;border-bottom:3px solid var(--fg);position:relative}
.tbl{overflow-x:auto;background:var(--surface);border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{font:600 11px/1.2 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);background:var(--surface);position:sticky;top:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}td.wrap-ok{white-space:normal;min-width:180px}
.W{color:#1F7A44;font-weight:600}.L{color:var(--crim);font-weight:600}.T{color:var(--muted);font-weight:600}
@media (prefers-color-scheme:dark){.W{color:#5CC98A}}
tr.title td{background:rgba(233,180,76,.12)}
a{color:inherit}td a{text-decoration-color:var(--line);text-underline-offset:3px}td a:hover{text-decoration-color:var(--crim)}
.note{color:var(--muted);font-size:14px;margin:12px 0 0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.fact{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--crim);padding:14px 16px}
.fact span{display:block;font:600 11px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.pn{display:flex;justify-content:space-between;gap:12px;margin-top:28px;font:600 13px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase}
.pn a{text-decoration:none;padding:12px 0}.pn a:hover{color:var(--crim)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.grid a{display:block;background:var(--surface);border:1px solid var(--line);padding:10px 12px;text-decoration:none}
.grid a:hover{border-color:var(--crim)}.grid small{display:block;color:var(--muted);font:12px/1.4 var(--mono)}
.cta{display:inline-block;margin-top:22px;font:600 13px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;text-decoration:none;padding:13px 18px;background:#9E1B32;color:#fff}
footer{color:var(--muted);font-size:14px;padding:36px 0 44px;border-top:1px solid var(--line)}
@media (max-width:560px){.top nav{gap:14px}h1{margin-top:8px}}
"""
CSS += """
.story{max-width:68ch;margin:0 auto}.story p{margin:0 0 1.1em;font-size:19px;line-height:1.65}
.story h2{font-size:clamp(24px,4vw,32px);margin:38px 0 14px}
.story p:first-of-type::first-letter{float:left;font:900 74px/.8 var(--display);color:var(--crim);margin:6px 10px 0 0}
.kicker{font:600 12px/1.4 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:30px 0 0}
.src{max-width:68ch;margin:36px auto 0;font-size:14px;color:var(--muted)}.src ol{padding-left:20px}.src a{text-underline-offset:3px}
.more{max-width:68ch;margin:28px auto 0}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900'
         '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@600&display=swap">')

def page(path, title, desc, crumbs, h1, lede, tiles, body):
    url = SITE + path
    crumb_html = " · ".join(f'<a href="{u}">{E(n)}</a>' for n, u in crumbs)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs + [(h1, path)])]}
    tiles_html = ('<div class="tiles">' + "".join(f"<div class=\"tile\"><b>{E(str(v))}</b><span>{E(k)}</span></div>" for k, v in tiles) + "</div>") if tiles else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/icons/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32.png?v=3">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png?v=3">
<meta name="theme-color" content="#17191A">
{FONTS}
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">Crimson <span>Ledger</span></a>
<nav aria-label="Site"><a href="/">Home</a><a href="/vs/">Opponents</a><a href="/seasons/">Seasons</a><a href="/stories/">Stories</a></nav></div></header>
<section class="hero"><div class="wrap">
<div class="crumbs">{crumb_html}</div>
<h1>{E(h1)}</h1>
<p class="lede">{lede}</p>
{tiles_html}
</div></section>
<main class="wrap">
{body}
</main>
<footer class="wrap">An independent fan history project. Not affiliated with the University of Alabama or the SEC.
Game results from James Howell's college football scores archive (1902 on) and Wikipedia season pages (1892–1901).
Records are on-field results; Alabama's official record excludes wins later vacated or forfeited (1993, 2005–2007).
<br><a href="/">The Crimson Ledger home</a> · <a href="/vs/">All opponents</a> · <a href="/seasons/">All seasons</a></footer>
</body>
</html>
"""

def write(path, text):
    full = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(text)

FLAG = {1: " †", 2: " ‡"}
FLAG_NOTE = '<p class="note">† Result disputed between sources. ‡ Result not independently verified.</p>'

def game_table(gs, show_opp, show_season=False, show_coach=False):
    head = "<tr><th>Date</th>" + ("<th>Opponent</th>" if show_opp else "") + "<th>Site</th><th>Result</th><th class=\"num\">Score</th>" + \
           ("<th>Coach</th>" if show_coach else "") + "<th>Notes</th></tr>"
    rows = []
    for g in gs:
        opp = f'<td><a href="/vs/{slug(g["opp"])}/">{E(g["opp"])}</a></td>' if show_opp else ""
        date = f'<a href="/seasons/{g["s"]}/">{fdate(g["d"])}</a>' if show_season else fdate(g["d"])
        notes = ", ".join(x for x in [g["note"], "Conference game" if g["conf"] and not g["note"] else ""] if x)
        coach = f"<td>{E(g['coach'])}</td>" if show_coach else ""
        rows.append(f'<tr><td>{date}</td>{opp}<td>{E(site_txt(g))}</td><td class="{g["res"]}">{g["res"]}</td>'
                    f'<td class="num">{score(g)}{FLAG.get(g["flag"], "")}</td>{coach}<td class="wrap-ok">{E(notes)}</td></tr>')
    note = FLAG_NOTE if any(g["flag"] for g in gs) else ""
    return f'<div class="tbl"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>{note}'

urls = []

# ---------- opponent pages ----------
OPP = {}
for g in G: OPP.setdefault(g["opp"], []).append(g)
for opp, gs in OPP.items():
    gs.sort(key=lambda g: g["d"])
    w, l, t = wl(gs); n = len(gs)
    first, last = gs[0], gs[-1]
    # streaks
    cur = 1
    while cur < n and gs[-1 - cur]["res"] == last["res"]: cur += 1
    best = run = 0
    for g in gs:
        run = run + 1 if g["res"] == "W" else 0; best = max(best, run)
    wins = [g for g in gs if g["res"] == "W"]; losses = [g for g in gs if g["res"] == "L"]
    bigw = max(wins, key=lambda g: (g["a"] - g["o"], g["d"])) if wins else None
    bigl = max(losses, key=lambda g: (g["o"] - g["a"], g["d"])) if losses else None
    pf = sum(g["a"] for g in gs); pa = sum(g["o"] for g in gs)
    if w > l: lead = f"Alabama leads the all-time series {rec(w, l, t)}"
    elif w < l: lead = f"{E(opp)} leads the all-time series {rec(l, w, t)}"
    else: lead = f"The all-time series is tied {rec(w, l, t)}"
    times = "once" if n == 1 else f"{n} times"
    lede = (f"Alabama and {E(opp)} have met {times}" + (f", first in {first['y'] if 'y' in first else first['d'][:4]}" if n > 1 else f", in {first['d'][:4]}") +
            f". {lead}. " + ("The most recent meeting was" if n > 1 else "That game was") +
            f" a {score(last)} {'win' if last['res']=='W' else 'loss' if last['res']=='L' else 'tie'} for Alabama on {fdate(last['d'])}.")
    res_word = {"W": "Alabama won", "L": f"{opp} won", "T": "tied"}
    tiles = [("All-time record", rec(w, l, t)), ("Games played", n), ("First meeting", first["d"][:4]),
             ("Current streak", f"{res_word[last['res']]} {cur}" if last["res"] != "T" else f"Tie, last game")]
    facts = []
    if bigw: facts.append(("Biggest Alabama win", f"{score(bigw)} on {fdate(bigw['d'])}"))
    if bigl: facts.append((f"Biggest {opp} win", f"{bigl['o']}–{bigl['a']} on {fdate(bigl['d'])}"))
    if best > 1: facts.append(("Longest Alabama win streak", f"{best} straight"))
    facts.append(("Points scored", f"Alabama {pf:,}, {opp} {pa:,}"))
    for code, name in (("H", "In Alabama home games"), ("A", f"At {opp}"), ("N", "At neutral sites")):
        sub = [g for g in gs if g["loc"] == code]
        if sub: facts.append((name, rec(*wl(sub))))
    pc = {}
    for g in gs:
        if g["coach"]: pc.setdefault(g["coach"], []).append(g)
    coach_rows = "".join(f"<tr><td>{E(c)}</td><td class=\"num\">{len(v)}</td><td class=\"num\">{rec(*wl(v))}</td></tr>"
                         for c, v in sorted(pc.items(), key=lambda kv: kv[1][0]["d"]))
    body = ('<h2>Series at a glance</h2><div class="facts">' +
            "".join(f'<div class="fact"><span>{E(k)}</span>{E(v)}</div>' for k, v in facts) + "</div>")
    if len(pc) > 1:
        body += f'<h2>By Alabama coach</h2><div class="tbl"><table><thead><tr><th>Coach</th><th class="num">Games</th><th class="num">Record</th></tr></thead><tbody>{coach_rows}</tbody></table></div>'
    body += f"<h2>Every game</h2>" + game_table(list(reversed(gs)), False, show_season=True, show_coach=True)
    body += '<a class="cta" href="/vs/">All Alabama opponents</a>'
    path = f"/vs/{slug(opp)}/"
    title = f"Alabama vs. {opp} All-Time Series Record ({rec(w, l, t)}) | The Crimson Ledger"
    desc = re.sub("<[^>]+>", "", html.unescape(lede)) + f" Every result since {first['d'][:4]}."
    write(path, page(path, title, desc, [("Home", "/"), ("Opponents", "/vs/")], f"Alabama vs. {opp}", lede, tiles, body))
    urls.append((path, last["d"]))

# ---------- season pages ----------
years = sorted(y for y in SEASONS if any(g["s"] == y for g in G))
for i, y in enumerate(years):
    s = SEASONS[y]; gs = sorted([g for g in G if g["s"] == y], key=lambda g: g["d"])
    title_yr = y in TITLES
    conf = f"{s['cw']}–{s['cl']}" + (f"–{s['ct']}" if s['ct'] not in ("", "0") else "") if s["cw"] != "" else ""
    pf = sum(g["a"] for g in gs); pa = sum(g["o"] for g in gs)
    overall = rec(s["w"], s["l"], s["t"])
    live = y == datetime.date.today().year and s["post"] in ("", "In progress")
    lede = (f"The {y} Alabama Crimson Tide {'is' if live else 'went'} {overall}" + (f" ({conf} in conference)" if conf else "") +
            f" under {E(s['coach'])}" + ("" if not title_yr else " and claimed the national championship") + ". " +
            (f"Final AP ranking: No. {s['ap']}." if s["ap"] else "") +
            ("The season is in progress and this page updates weekly." if live else ""))
    lede = lede.strip()
    if s["vac"]: lede += " Some wins from this season were later vacated or forfeited; the record shown is on-field."
    tiles = [("Overall", overall)] + ([("Conference", conf)] if conf else []) + [("Coach", s["coach"].split()[-1])] + \
            ([("Final AP", f"No. {s['ap']}")] if s["ap"] else []) + [("Points for–against", f"{pf}–{pa}")]
    if title_yr: tiles.insert(0, ("National title", "★ " + str(y)))
    body = ""
    post_games = [g for g in gs if re.search(r"Bowl|Playoff|BCS|Championship", g["note"])]
    if post_games:
        word = {"W": "Won", "L": "Lost", "T": "Tied"}
        body += '<h2>Postseason</h2><div class="facts">' + "".join(
            f'<div class="fact"><span>{E(g["note"])}</span>{word[g["res"]]} {score(g)} vs. <a href="/vs/{slug(g["opp"])}/">{E(g["opp"])}</a> · {fdate(g["d"])}</div>'
            for g in post_games) + "</div>"
    body += "<h2>Schedule and results</h2>" + game_table(gs, True)
    if live:
        played = {g["d"] for g in gs}
        up = [x for x in SCHED if x[0] not in played and x[0] > gs[-1]["d"]]
        if up:
            body += "<h2>Still to play</h2><div class=\"tbl\"><table><thead><tr><th>Date</th><th>Opponent</th><th>Site</th></tr></thead><tbody>" + "".join(
                f'<tr><td>{fdate(d)}</td><td><a href="/vs/{slug(o)}/">{E(o)}</a></td><td>{ {"H": "Home", "A": "Away"}.get(loc, "Neutral") }</td></tr>' for d, o, loc in up) + "</tbody></table></div>"
    prev_ = f'<a href="/seasons/{years[i-1]}/">← {years[i-1]}</a>' if i else "<span></span>"
    next_ = f'<a href="/seasons/{years[i+1]}/">{years[i+1]} →</a>' if i + 1 < len(years) else "<span></span>"
    body += f'<nav class="pn" aria-label="Other seasons">{prev_}<a href="/seasons/">All seasons</a>{next_}</nav>'
    path = f"/seasons/{y}/"
    h1 = f"{y} Alabama Football"
    title = f"{y} Alabama Football: {overall} Record, Schedule and Results | The Crimson Ledger"
    desc = re.sub("<[^>]+>", "", html.unescape(lede)).strip() + " Every game, score and result."
    write(path, page(path, title, desc, [("Home", "/"), ("Seasons", "/seasons/")], h1, lede, tiles, body))
    urls.append((path, gs[-1]["d"]))

# ---------- hubs ----------
opp_sorted = sorted(OPP.items(), key=lambda kv: (-len(kv[1]), kv[0]))
cards = "".join(f'<a href="/vs/{slug(o)}/">{E(o)}<small>{rec(*wl(gs))} · {len(gs)} game{"s" if len(gs) > 1 else ""}</small></a>'
                for o, gs in opp_sorted)
tw, tl, tt = wl(G)
write("/vs/", page("/vs/", "Alabama Football All-Time Record vs. Every Opponent | The Crimson Ledger",
      f"Alabama's all-time head-to-head record against all {len(OPP)} opponents it has played since 1892, from Auburn and Tennessee to one-time meetings.",
      [("Home", "/")], "Every Opponent",
      f"Alabama has played {len(OPP)} different opponents since 1892, with an on-field record of {rec(tw, tl, tt)}. Sorted by how often they've met.",
      [("Opponents", len(OPP)), ("Games", len(G)), ("On-field record", rec(tw, tl, tt))],
      f'<h2>Head-to-head records</h2><div class="grid">{cards}</div>'))
urls.append(("/vs/", G[-1]["d"]))

decades = {}
for y in years: decades.setdefault(y // 10 * 10, []).append(y)
body = ""
for dcd, ys in sorted(decades.items(), reverse=True):
    body += f"<h2>{dcd}s</h2><div class=\"grid\">" + "".join(
        f'<a href="/seasons/{y}/">{y}{" ★" if y in TITLES else ""}<small>{rec(SEASONS[y]["w"], SEASONS[y]["l"], SEASONS[y]["t"])} · {E(SEASONS[y]["coach"])}</small></a>'
        for y in reversed(ys)) + "</div>"
write("/seasons/", page("/seasons/", "Alabama Football Season-by-Season Records | The Crimson Ledger",
      f"Every Alabama football season from {years[0]} to {years[-1]}: record, coach and full schedule with results. ★ marks a claimed national championship.",
      [("Home", "/")], "Every Season",
      f"{len(years)} seasons of Alabama football, {years[0]} to {years[-1]}. No team played in 1898, 1918 or 1943. ★ marks a national championship Alabama claims.",
      [("Seasons", len(years)), ("National titles", len(TITLES))], body))
urls.append(("/seasons/", G[-1]["d"]))

# ---------- stories ----------
def para(t):
    return f"<h2>{E(t[3:])}</h2>" if t.startswith("## ") else f"<p>{E(t)}</p>"
STORIES = json.load(open(os.path.join(ROOT, "data/stories.json")))
GBD = {g["d"]: g for g in G}
if os.path.isdir(os.path.join(ROOT, "stories")): shutil.rmtree(os.path.join(ROOT, "stories"))
for st in STORIES:
    path = f"/stories/{st['slug']}/"
    g = GBD.get(st.get("date") or "")
    links = ""
    if g:
        links = (f'<div class="more facts"><div class="fact"><span>In the Game Book</span>{"Won" if g["res"]=="W" else "Lost" if g["res"]=="L" else "Tied"} {score(g)} '
                 f'{"at" if g["loc"]=="A" else "vs."} <a href="/vs/{slug(g["opp"])}/">{E(g["opp"])}</a> · <a href="/seasons/{g["s"]}/">The {g["s"]} season</a></div></div>')
    srcs = "".join(f'<li><a href="{E(u)}" rel="nofollow">{E(n)}</a></li>' for n, u in st.get("sources", []))
    body = (f'<p class="kicker story">{E(st["era"])}</p><article class="story">' + "".join(para(t) for t in st["body"]) + "</article>"
            + links + (f'<div class="src"><b>Sources</b><ol>{srcs}</ol></div>' if srcs else "")
            + '<div class="more"><a class="cta" href="/stories/">More stories</a></div>')
    title = f"{st['title']}: {fdate(st['date']) if st.get('date') else st['era']} | The Crimson Ledger"
    write(path, page(path, title, st["dek"], [("Home", "/"), ("Stories", "/stories/")], st["title"], E(st["dek"]), st.get("tiles", []), body))
    urls.append((path, st.get("updated", datetime.date.today().isoformat())))
if STORIES:
    eras = {}
    for st in STORIES: eras.setdefault(st["era"], []).append(st)
    cards = "".join(f'<h2>{E(era)}</h2><div class="grid">' + "".join(
        f'<a href="/stories/{st["slug"]}/">{E(st["title"])}<small>{E(st["dek"])}</small></a>' for st in sts) + "</div>" for era, sts in eras.items())
    write("/stories/", page("/stories/", "Alabama Football Stories | The Crimson Ledger",
          "The stories behind Alabama football's biggest moments, told from the record.",
          [("Home", "/")], "The Story Vault", "The stories behind Alabama football's biggest moments, told from the record.",
          [("Stories", len(STORIES))], cards))
    urls.append(("/stories/", max(st.get("updated", "") for st in STORIES) or datetime.date.today().isoformat()))
print(f"stories {len(STORIES)}")

# ---------- sitemap + robots ----------
today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f"<url><loc>{SITE}/</loc><lastmod>{today}</lastmod></url>"]
sm += [f"<url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod></url>" for p, d in urls]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"opponents {len(OPP)}, seasons {len(years)}, sitemap urls {len(urls) + 1}")
