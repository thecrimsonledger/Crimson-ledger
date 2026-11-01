"""Build the opponent and season pages, their hub pages, sitemap.xml and robots.txt.

Usage (from the repo root): python3 -I tools/build_pages.py
Reads data/allgames.json plus the season table (SCSV) and titles from tools/page-source.html,
data/stories.json and data/records.json, and writes vs/, seasons/, stories/, players/, trivia/, sitemap.xml and robots.txt. Run it after every weekly update.
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
.top nav{display:flex;flex-wrap:wrap;gap:4px 18px;max-width:100%}.top nav a:hover{color:var(--gold)}
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
@media (max-width:560px){.top nav{gap:2px 14px}h1{margin-top:8px}}
"""
CSS += """
.story{max-width:68ch;margin:0 auto}.story p{margin:0 0 1.1em;font-size:19px;line-height:1.65}
.story h2{font-size:clamp(24px,4vw,32px);margin:38px 0 14px}
.story p:first-of-type::first-letter{float:left;font:900 74px/.8 var(--display);color:var(--crim);margin:6px 10px 0 0}
.kicker{font:600 12px/1.4 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:30px 0 0}
.src{max-width:68ch;margin:36px auto 0;font-size:14px;color:var(--muted)}.src ol{padding-left:20px}.src a{text-underline-offset:3px}
.more{max-width:68ch;margin:28px auto 0}
.pf{display:flex;flex-wrap:wrap;gap:10px;margin:28px 0 12px}.pf input,.pf select{font:15px var(--mono);padding:10px 12px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:2px;min-width:0}
.pf input{flex:1 1 200px}.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips button{font:600 12px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:9px 12px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:2px;cursor:pointer}
.chips button[aria-pressed="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
[hidden]{display:none!important}
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
<nav aria-label="Site"><a href="/">Home</a><a href="/vs/">Opponents</a><a href="/seasons/">Seasons</a><a href="/stories/">Stories</a><a href="/players/">Players</a><a href="/trivia/">Trivia</a></nav></div></header>
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

def story_link(g):
    st = STORY_BY_GAME.get(g["d"])
    return f'{" · " if g["note"] or g["conf"] else ""}<a href="/stories/{st["slug"]}/">Read the story</a>' if st else ""

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
                    f'<td class="num">{score(g)}{FLAG.get(g["flag"], "")}</td>{coach}<td class="wrap-ok">{E(notes)}{story_link(g)}</td></tr>')
    note = FLAG_NOTE if any(g["flag"] for g in gs) else ""
    return f'<div class="tbl"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>{note}'

urls = []

# ---------- story links (each story attaches to its game's season and opponent, plus any extra seasons/opponents it lists) ----------
STORIES = json.load(open(os.path.join(ROOT, "data/stories.json")))
GBD = {g["d"]: g for g in G}
STORY_BY_SEASON, STORY_BY_OPP, STORY_BY_GAME = {}, {}, {}
for st in STORIES:
    g = GBD.get(st.get("date") or "")
    seasons = st.get("seasons") if "seasons" in st else ([g["s"]] if g else [])
    opps = st.get("opponents") if "opponents" in st else ([g["opp"]] if g else [])
    for y in seasons: STORY_BY_SEASON.setdefault(int(y), []).append(st)
    for o in opps: STORY_BY_OPP.setdefault(o, []).append(st)
    if g and st.get("game_link", True): STORY_BY_GAME[g["d"]] = st
def story_cards(sts):
    if not sts: return ""
    return ('<h2>Stories</h2><div class="grid">' + "".join(
        f'<a href="/stories/{st["slug"]}/">{E(st["title"])}<small>{E(st["dek"])}</small></a>' for st in sts) + "</div>")

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
    body += story_cards(STORY_BY_OPP.get(opp, []))
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
    body += story_cards(STORY_BY_SEASON.get(y, []))
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


# ---------- player pages (from the Record Book in data/records.json) ----------
REC = json.load(open(os.path.join(ROOT, "data/records.json")))
HEIS = {n: int(y) for n, y in re.findall(r'\["([^"]+)",(\d{4})\]', re.search(r"const HEISMAN=\[(.*?)\];", src).group(1))}
SPAN_NAME = {"career": "Career", "season": "Season", "game": "Single game"}
def name_variants(n):
    v = {n}
    base = re.sub(r",? (Jr\.|Sr\.|II|III|IV)$", "", n); v.add(base)
    for x in list(v): v.add(re.sub(r"\b([A-Z])\. ([A-Z])\. ", r"\1\2 ", x))
    return v
def yrs(t):
    m = re.match(r"(\d{4})(?:[–-](\d{2,4}))?$", t.strip())
    if not m: return []
    a = int(m.group(1)); b = m.group(2)
    if not b: return [a]
    b = int(b) if len(b) == 4 else int(str(a)[:2] + b)
    return list(range(a, b + 1))
PLAYERS = {}
for cat in REC:
    for span, rows in cat["v"].items():
        rank = ""
        for row in rows:
            rank = row[0] or rank
            PLAYERS.setdefault(row[1], []).append(dict(g=cat["g"], s=cat["s"], span=span, rank=int(rank) if rank.isdigit() else 99,
                                                        val=row[2], yr=row[3], opp=row[4]))
OPP_SLUGS = {slug(o) for o in OPP}
def opp_link(t):
    o = re.sub(r"\s*\(.*\)$", "", t).strip()
    return f'<a href="/vs/{slug(o)}/">{E(t)}</a>' if slug(o) in OPP_SLUGS else E(t)
def yr_link(t):
    y = yrs(t)
    return f'<a href="/seasons/{y[0]}/">{E(t)}</a>' if len(y) == 1 and y[0] in SEASONS else E(t)
if os.path.isdir(os.path.join(ROOT, "players")): shutil.rmtree(os.path.join(ROOT, "players"))
through = re.search(r"Individual leaders · through ([^<]+)<", src)
through = through.group(1).strip() if through else ""
pinfo = []
for name, ents in PLAYERS.items():
    ents.sort(key=lambda e: (e["rank"], ["career", "season", "game"].index(e["span"])))
    allyrs = sorted({y for e in ents for y in yrs(e["yr"])})
    span_txt = (f"{allyrs[0]}–{allyrs[-1]}" if allyrs[0] != allyrs[-1] else str(allyrs[0])) if allyrs else ""
    recs = [e for e in ents if e["rank"] == 1]
    heis = next((y for hn, y in HEIS.items() if hn in name_variants(name) or name in name_variants(hn)), None)
    vs = name_variants(name)
    sts = [st for st in STORIES if any(v in " ".join(st["body"]) + st["dek"] for v in vs)]
    p_slug = slug(name); path = f"/players/{p_slug}/"
    n = len(ents)
    lede = (f"{E(name)} appears {n} time{'s' if n != 1 else ''} among Alabama's statistical leaders" +
            (f", including {len(recs)} school record{'s' if len(recs) != 1 else ''}" if recs else "") + "." +
            (f" He won the Heisman Trophy in {heis}." if heis else "") +
            (f" Record Book through {E(through)}." if through else ""))
    tiles = ([("Heisman Trophy", heis)] if heis else []) + [("Record Book spots", n), ("School records", len(recs))] + ([("Seasons", span_txt)] if span_txt else [])
    body = ""
    if recs:
        body += '<h2>School records</h2><div class="facts">' + "".join(
            f'<div class="fact"><span>{E(SPAN_NAME[e["span"]])} {E(e["s"].lower())}</span>{E(e["val"])} · {yr_link(e["yr"])}' +
            (f' vs. {opp_link(e["opp"])}' if e["opp"] else "") + "</div>" for e in recs) + "</div>"
    body += ('<h2>In the Record Book</h2><div class="tbl"><table><thead><tr><th class="num">Rank</th><th>Stat</th><th>Type</th>'
             '<th class="num">Total</th><th>Year</th><th>Opponent</th></tr></thead><tbody>' + "".join(
        f'<tr><td class="num">{e["rank"] if e["rank"] < 99 else "—"}</td><td>{E(e["s"])}</td><td>{SPAN_NAME[e["span"]]}</td>'
        f'<td class="num">{E(e["val"])}</td><td>{yr_link(e["yr"])}</td><td class="wrap-ok">{opp_link(e["opp"]) if e["opp"] else ""}</td></tr>' for e in ents) +
        "</tbody></table></div>")
    body += story_cards(sts)
    seas = [y for y in allyrs if y in SEASONS]
    if seas:
        body += '<h2>His seasons</h2><div class="grid">' + "".join(
            f'<a href="/seasons/{y}/">{y}<small>{rec(SEASONS[y]["w"], SEASONS[y]["l"], SEASONS[y]["t"])} · {E(SEASONS[y]["coach"])}</small></a>' for y in seas) + "</div>"
    body += ('<p class="note">Ranks are top-10 Alabama marks from Wikipedia\'s Alabama statistical leaders tables, refreshed weekly. '
             'That page carries a disputed-accuracy notice, so treat lower-ranked entries as unverified until checked against Alabama\'s official record book.</p>'
             '<a class="cta" href="/players/">All players</a>')
    title = f"{name}: Alabama Football Records and Stats | The Crimson Ledger"
    desc = re.sub("<[^>]+>", "", html.unescape(lede))
    write(path, page(path, title, desc, [("Home", "/"), ("Players", "/players/")], name, lede, tiles, body))
    urls.append((path, datetime.date.today().isoformat()))
    pinfo.append((name, p_slug, n, len(recs), heis, span_txt))
GROUP_ORDER = ["Passing", "Rushing", "Receiving", "Defense", "Kicking"]
GROUP_LABEL = {"Passing": "Passing", "Rushing": "Rushing", "Receiving": "Receiving", "Defense": "Defense", "Kicking": "Kicking"}
def primary_group(name):
    cnt = {}
    for e in PLAYERS[name]:
        if e["g"] in GROUP_ORDER: cnt[e["g"]] = cnt.get(e["g"], 0) + 1
    if not cnt: return "Passing"
    if cnt.get("Passing", 0) >= 2: return "Passing"  # quarterbacks who also ran a lot stay with the passers
    return max(cnt, key=lambda g: (cnt[g], -GROUP_ORDER.index(g)))
def first_year(sp): return int(sp[:4]) if sp[:4].isdigit() else 0
def pcard(nm, ps, n, r, hz, sp):
    dec = first_year(sp) // 10 * 10
    return (f'<a href="/players/{ps}/" data-n="{E(nm.lower())}" data-d="{dec}">{E(nm)}{" ★" if hz else ""}<small>{sp} · {n} spot{"s" if n != 1 else ""}' +
            (f" · {r} record{'s' if r != 1 else ''}" if r else "") + "</small></a>")
pkey = lambda x: (-x[3], -x[2], x[0])
heis_p = sorted([x for x in pinfo if x[4]], key=lambda x: x[4])
pgroups = {g: sorted([x for x in pinfo if primary_group(x[0]) == g], key=pkey) for g in GROUP_ORDER}
pdecs = sorted({first_year(x[5]) // 10 * 10 for x in pinfo if first_year(x[5])})
pchips = '<button type="button" data-g="" aria-pressed="true">All</button>' + "".join(
    f'<button type="button" data-g="{g}" aria-pressed="false">{GROUP_LABEL[g]}</button>' for g in GROUP_ORDER if pgroups[g])
PSCRIPT = """<script>(()=>{const q=document.getElementById("pq"),d=document.getElementById("pd"),gb=document.getElementById("pg");let g="";
function run(){const t=q.value.trim().toLowerCase();let any=0;document.querySelectorAll("section[data-sec]").forEach(s=>{
const showSec=!g||s.dataset.sec===g;let n=0;s.querySelectorAll(".grid a").forEach(a=>{const ok=showSec&&(!t||a.dataset.n.includes(t))&&(!d.value||a.dataset.d===d.value);a.hidden=!ok;if(ok)n++});
s.hidden=!n;any+=n});document.getElementById("pnone").hidden=!!any}
q.addEventListener("input",run);d.addEventListener("input",run);
gb.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;g=b.dataset.g;gb.querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed",x===b));run()});})();</script>"""
pbody = ('<div class="pf"><input id="pq" type="search" placeholder="Find a player…" aria-label="Find a player">'
         '<select id="pd" aria-label="Filter by era"><option value="">All eras</option>' +
         "".join(f'<option value="{d}">{d}s</option>' for d in reversed(pdecs)) + '</select></div>'
         f'<div class="chips" id="pg" role="group" aria-label="Filter by category">{pchips}</div>'
         f'<section data-sec="heis"><h2>Heisman Trophy Winners</h2><div class="grid">{"".join(pcard(*x) for x in heis_p)}</div></section>' +
         "".join(f'<section data-sec="{g}"><h2>{GROUP_LABEL[g]}</h2><div class="grid">{"".join(pcard(*x) for x in pgroups[g])}</div></section>'
                 for g in GROUP_ORDER if pgroups[g]) +
         '<p class="note" id="pnone" hidden>No players match.</p>'
         '<p class="note">Each player is listed under the category where most of his Record Book spots come from. Within each category, school records come first, then total top-10 spots. Eras go by first season.</p>' + PSCRIPT)
write("/players/", page("/players/", "Alabama Football Players and Records | The Crimson Ledger",
      "Every player in Alabama football's statistical Record Book, by passing, rushing, receiving, defense and kicking, with school records and Heisman winners.",
      [("Home", "/")], "The Players", f"{len(pinfo)} players appear among Alabama's top-10 statistical leaders. Search by name, or filter by category and era. ★ marks a Heisman Trophy winner.",
      [("Players", len(pinfo)), ("Heisman winners", len(HEIS))], pbody))
urls.append(("/players/", datetime.date.today().isoformat()))
print(f"players {len(pinfo)}")


# ---------- trivia (curated questions from data/trivia.json + questions generated from the game data and Record Book) ----------
import random
CURATED = json.load(open(os.path.join(ROOT, "data/trivia.json")))
STORY_TITLE = {st["slug"]: st["title"] for st in STORIES}
TQ = []
def addq(cat, q, a, wrong, x, link, link_text, key):
    wrong = [w for w in dict.fromkeys(wrong) if w != a]
    if len(wrong) < 3: return
    rnd = random.Random(key)
    TQ.append(dict(c=cat, q=q, a=a, w=rnd.sample(wrong, 3), x=x, l=link, lt=link_text))
for i, t in enumerate(CURATED):
    addq("Stories", t["q"], t["a"], t["w"], t["x"], f"/stories/{t['story']}/", f"Read: {STORY_TITLE.get(t['story'], 'the story')}", f"c{i}")

# Record Book: who holds each school record (skipped when the record is shared)
UNIT_WORD = {"Yards": "yards", "TDs": "touchdowns", "Rec": "catches", "Ints": "interceptions", "Tackles": "tackles", "Sacks": "sacks", "FGs": "field goals"}
SPAN_Q = {"career": "career", "season": "single-season", "game": "single-game"}
for cat in REC:
    for span, rows in cat["v"].items():
        if len(rows) < 4 or rows[1][0] in ("", "1"): continue
        if cat["s"] in ("Total yards", "Field goal %"): continue  # repeat the passing records / awkward to ask
        top = rows[0]
        names = [r[1] for r in rows[1:] if r[1] != top[1]]
        if len(set(names)) < 3: continue
        when = f"{top[3]}" + (f" vs. {top[4]}" if top[4] else "")
        qtext = ("Who kicked the longest field goal in Alabama history?" if cat["s"] == "Longest field goal"
                 else f"Who holds Alabama's {SPAN_Q[span]} record for {cat['s'].lower()}?")
        unit = UNIT_WORD.get(cat["unit"], "")
        addq("Record Book", qtext, top[1], names,
             f"{top[1]}: {top[2]}{' ' + unit if unit and not top[2].endswith('%') else ''} ({when}).", f"/players/{slug(top[1])}/", f"{top[1]}'s records", f"r{cat['s']}{span}")

# National title seasons that ended with a bowl or playoff win
TITLE_COACH = {int(y): c for y, c in re.findall(r'\[(\d{4}),"([A-Za-z]+)"\]', re.search(r"const TITLES=\[(.*?)\];", src).group(1))}
bowl_wins = [g for g in G if g["note"] and g["res"] == "W" and re.search(r"Bowl|Playoff|BCS", g["note"])]
post_all = [g for g in G if g["note"] and re.search(r"Bowl|Playoff|BCS|Championship", g["note"]) and "SEC" not in g["note"]]
for y in sorted(TITLES):
    gs = sorted([g for g in G if g["s"] == y], key=lambda g: g["d"])
    if not gs: continue
    last = gs[-1]
    if last["note"] and last["res"] == "W" and re.search(r"Bowl|Playoff|BCS|Championship", last["note"]):
        addq("Championships", f"Alabama finished its {y} national championship season by beating which team in the {last['note']}?",
             last["opp"], [g["opp"] for g in post_all if g["opp"] != last["opp"] and abs(g["s"] - y) <= 12],
             f"Alabama won {score(last)} on {fdate(last['d'])}.", f"/seasons/{y}/", f"The {y} season", f"t{y}")
coaches = sorted(set(TITLE_COACH.values()))
FULL = {"Wade": "Wallace Wade", "Thomas": "Frank Thomas", "Bryant": "Bear Bryant", "Stallings": "Gene Stallings", "Saban": "Nick Saban"}
for y, c in TITLE_COACH.items():
    if c in FULL and y < 1950:  # later title coaches are too easy to be worth asking
        era_coaches = sorted({v["coach"] for k, v in SEASONS.items() if abs(k - y) <= 30 and v["coach"] != FULL[c]
                              and sum(1 for z in SEASONS.values() if z["coach"] == v["coach"]) >= 3})
        addq("Championships", f"Who coached Alabama's {y} national championship team?", FULL[c], era_coaches,
             f"{y}: {rec(SEASONS[y]['w'], SEASONS[y]['l'], SEASONS[y]['t'])} under {FULL[c]}.", f"/seasons/{y}/", f"The {y} season", f"k{y}")

# Perfect seasons
perfect = [y for y in years if SEASONS[y]["l"] == 0 and SEASONS[y]["t"] == 0 and SEASONS[y]["w"] >= 9]
close = [y for y in years if SEASONS[y]["w"] >= 9 and SEASONS[y]["l"] == 1]
rp = random.Random("perfect")
for y in perfect:
    addq("Seasons", "Which of these Alabama teams finished with a perfect record?", str(y), [str(z) for z in rp.sample(close, min(8, len(close)))],
         f"The {y} team went {SEASONS[y]['w']}–0. The others each lost a game.", f"/seasons/{y}/", f"The {y} season", f"p{y}")

# Series records: never lost to (8+ meetings), and the most-played opponent
recent = lambda gs: max(g["s"] for g in gs) >= 1960
never = [o for o, gs in OPP.items() if len(gs) >= 8 and recent(gs) and not any(g["res"] == "L" for g in gs)]
lost_to = [o for o, gs in OPP.items() if len(gs) >= 8 and recent(gs) and any(g["res"] == "L" for g in gs)]
for o in never:
    w, l, t = wl(OPP[o])
    addq("Rivalries", "Alabama has played each of these teams at least eight times. Which one has never beaten Alabama?", o, lost_to,
         f"Alabama is {rec(w, l, t)} all-time against {o}.", f"/vs/{slug(o)}/", f"Alabama vs. {o}", f"n{o}")
most = sorted(OPP.items(), key=lambda kv: -len(kv[1]))
if len(most[0][1]) > len(most[1][1]):
    addq("Rivalries", "Which opponent has Alabama played more times than any other?", most[0][0], [o for o, _ in most[1:6]],
         f"{len(most[0][1])} meetings, more than any other team.", f"/vs/{slug(most[0][0])}/", f"Alabama vs. {most[0][0]}", "most")
big = max(G, key=lambda g: (g["a"] - g["o"], g["d"]))
others = sorted([g for g in G if g is not big and g["res"] == "W"], key=lambda g: -(g["a"] - g["o"]))[:8]
addq("Rivalries", "What is the most lopsided win in Alabama history?", f"{score(big)} vs. {big['opp']}, {big['d'][:4]}",
     [f"{score(g)} vs. {g['opp']}, {g['d'][:4]}" for g in others], f"Alabama beat {big['opp']} {score(big)} on {fdate(big['d'])}.",
     f"/seasons/{big['s']}/", f"The {big['s']} season", "big")

cats = {}
for q in TQ: cats[q["c"]] = cats.get(q["c"], 0) + 1
TCSS = """<style>
.label{font:600 12px/1.3 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.tq{max-width:640px;margin:28px auto 0}.tq .meta{display:flex;justify-content:space-between;font:600 12px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tq .bar{height:4px;background:var(--line);margin:10px 0 22px}.tq .bar i{display:block;height:100%;background:var(--crim);width:0;transition:width .3s}
.tq h2{border:0;padding:0;margin:0 0 18px;font-size:clamp(24px,5vw,32px);line-height:1.1;text-transform:none}
.opts{display:grid;gap:10px}.opts button{font:17px/1.35 var(--body);text-align:left;padding:14px 16px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:2px;cursor:pointer}
.opts button:hover:not(:disabled){border-color:var(--fg)}.opts button:disabled{cursor:default}
.opts button.ok{border-color:#1F7A44;background:rgba(31,122,68,.12)}.opts button.no{border-color:var(--crim);background:rgba(158,27,50,.1)}
.why{margin-top:16px;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--crim);padding:14px 16px}.why b{font:600 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase}
.why p{margin:6px 0 8px}.why a{font:600 13px/1 var(--mono);text-underline-offset:3px}
.tbtn{font:600 13px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:13px 18px;border:0;background:#9E1B32;color:#fff;border-radius:2px;cursor:pointer;margin-top:18px}
.tbtn.alt{background:transparent;color:var(--fg);border:1px solid var(--fg)}
.done{text-align:center}.done .big{font:900 clamp(72px,18vw,120px)/1 var(--display);color:var(--crim)}.done .sq{font-size:22px;letter-spacing:2px;margin:6px 0 4px}
.tmode{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:8px}.tmode .tbtn{margin-top:10px}
@media (prefers-color-scheme:dark){.opts button.ok{border-color:#5CC98A}}
</style>"""
TJS = """<script>
const Q=__Q__;
(()=>{const $=id=>document.getElementById(id),box=$("tq");
const today=new Date(),ds=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
function rng(seed){let h=1779033703^seed.length;for(let i=0;i<seed.length;i++){h=Math.imul(h^seed.charCodeAt(i),3432918353);h=h<<13|h>>>19}
 return()=>{h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return((h^=h>>>16)>>>0)/4294967296}}
function shuffle(a,r){a=a.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function pick(seed){const r=rng(seed),by={};Q.forEach((q,i)=>(by[q.c]=by[q.c]||[]).push(i));
 const plan={"Stories":4,"Record Book":3,"Championships":1,"Seasons":1,"Rivalries":1},out=[];
 Object.entries(plan).forEach(([c,n])=>out.push(...shuffle(by[c]||[],r).slice(0,n)));
 const rest=shuffle(Q.map((_,i)=>i).filter(i=>!out.includes(i)),r);while(out.length<10&&rest.length)out.push(rest.pop());
 return shuffle(out,r).map(i=>{const q=Q[i];return{...q,o:shuffle([q.a,...q.w],r)}})}
let set,n,score,marks,daily;
function start(isDaily){daily=isDaily;set=pick(isDaily?"daily-"+ds:"r"+Math.random());n=0;score=0;marks=[];show()}
function esc(s){return s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function show(){const q=set[n];box.innerHTML=`<div class="meta"><span>${daily?"Daily 10 · "+ds:"Practice round"}</span><span>${n+1} of ${set.length} · ${score} right</span></div>
 <div class="bar"><i style="width:${n/set.length*100}%"></i></div><div class="label">${esc(q.c)}</div><h2>${esc(q.q)}</h2>
 <div class="opts">${q.o.map((o,i)=>`<button type="button" data-i="${i}">${esc(o)}</button>`).join("")}</div><div id="why"></div>`;
 box.querySelectorAll(".opts button").forEach(b=>b.addEventListener("click",()=>answer(b)))}
function answer(b){const q=set[n],pickd=q.o[+b.dataset.i],ok=pickd===q.a;if(ok)score++;marks.push(ok);
 box.querySelectorAll(".opts button").forEach(x=>{x.disabled=true;if(q.o[+x.dataset.i]===q.a)x.classList.add("ok");else if(x===b)x.classList.add("no")});
 $("why").innerHTML=`<div class="why"><b>${ok?"Correct":"The answer: "+esc(q.a)}</b><p>${esc(q.x)}</p><a href="${q.l}">${esc(q.lt)} →</a></div>
 <button type="button" class="tbtn" id="next">${n+1<set.length?"Next question":"See your score"}</button>`;
 $("next").addEventListener("click",()=>{n++;n<set.length?show():finish()});$("next").focus({preventScroll:true})}
function finish(){const sq=marks.map(m=>m?"🟥":"⬜").join("");let best="";
 if(daily){try{localStorage.setItem("cl-trivia-"+ds,String(score))}catch(e){}}
 const line=score>=9?"Hall of Famer.":score>=7?"All-SEC.":score>=5?"Starter.":"Back to the film room.";
 box.innerHTML=`<div class="done"><div class="label">${daily?"Daily 10 · "+ds:"Practice round"}</div><div class="big">${score}/${set.length}</div>
 <div class="sq">${sq}</div><p>${line}</p>
 <div class="tmode"><button type="button" class="tbtn" id="share">Share your score</button><button type="button" class="tbtn alt" id="again">Practice round</button></div>
 <p class="note" id="sharemsg"></p><p class="note">${daily?"A new Daily 10 comes out every day at midnight.":"Practice rounds are random. The Daily 10 is the same for everyone each day."}</p></div>`;
 $("again").addEventListener("click",()=>start(false));
 $("share").addEventListener("click",async()=>{const t=`The Crimson Ledger ${daily?"Daily 10 · "+ds:"trivia"}: ${score}/${set.length}\\n${sq}\\nthecrimsonledger.com/trivia/`;
  try{if(navigator.share){await navigator.share({text:t});return}await navigator.clipboard.writeText(t);$("sharemsg").textContent="Copied. Paste it anywhere."}
  catch(e){$("sharemsg").textContent=t}})}
let prev=null;try{prev=localStorage.getItem("cl-trivia-"+ds)}catch(e){}
box.innerHTML=`<div class="done"><div class="label">Daily 10 · ${ds}</div><h2 style="text-align:center">Ten questions on Alabama football history</h2>
 <p>Everyone gets the same ten today. Every answer comes from the games, the Record Book or our stories.</p>
 ${prev!==null?`<p class="note">You scored ${prev}/10 on today's set.</p>`:""}
 <div class="tmode"><button type="button" class="tbtn" id="go">${prev!==null?"Play today's again":"Start the Daily 10"}</button><button type="button" class="tbtn alt" id="prac">Practice round</button></div></div>`;
$("go").addEventListener("click",()=>start(true));$("prac").addEventListener("click",()=>start(false));
})();
</script>"""
tbody = (TCSS + '<div class="tq" id="tq" aria-live="polite"></div>' +
         f'<p class="note" style="max-width:640px;margin:28px auto 0">{len(TQ)} questions in the bank: ' +
         ", ".join(f"{v} {k.lower()}" for k, v in cats.items()) +
         ". Record Book questions use the same Wikipedia leader tables as the Record Book, and update with it each week.</p>" +
         TJS.replace("__Q__", json.dumps(TQ, ensure_ascii=False).replace("</", "<\\/")))
write("/trivia/", page("/trivia/", "Alabama Football Trivia: The Daily 10 | The Crimson Ledger",
      "Ten Alabama football history questions every day, from the Rocky Block to the Record Book. Every answer is checked against the games and the stories.",
      [("Home", "/")], "Alabama Trivia", "A new set of ten questions every day, from the Rose Bowl in 1926 to last season's Record Book. Every answer comes with the story behind it.",
      [], tbody))
urls.append(("/trivia/", datetime.date.today().isoformat()))
print(f"trivia {len(TQ)} questions: {cats}")

# ---------- sitemap + robots ----------
today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f"<url><loc>{SITE}/</loc><lastmod>{today}</lastmod></url>"]
sm += [f"<url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod></url>" for p, d in urls]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"opponents {len(OPP)}, seasons {len(years)}, sitemap urls {len(urls) + 1}")
