"""Refresh The Crimson Ledger's Record Book from Wikipedia's Alabama statistical leaders tables.

Usage: python3 -I tools/update_records.py tools/page-source.html data/records.json [--dry-run]

What it does:
  1. Downloads https://en.wikipedia.org/wiki/Alabama_Crimson_Tide_football_statistical_leaders
     (via the MediaWiki API, retrying politely on HTTP 429).
  2. Parses every leader table (career / season / single game) for passing, rushing, receiving,
     total offense, defense and kicking.
  3. Prints every change against the current data/records.json: new entries, entries that
     dropped out, and changed values. Also prints the "updated through" sentence from the page.
  4. Unless --dry-run, writes data/records.json, replaces the REC array in the page, and sets the
     Record Book's "through" label from Wikipedia's "updated through ..." sentence.

Exit code 0 on success (changes or not), 2 if the download or parse fails (nothing is written).
Anything new involving a current player should be checked against a second source before
publishing; the Sunday task does that using the printed change list.
"""
import html, json, re, sys, time, urllib.parse, urllib.request

PAGE, DATA = sys.argv[1], sys.argv[2]
DRY = "--dry-run" in sys.argv
TITLE = "Alabama Crimson Tide football statistical leaders"

def fetch():
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        dict(action="parse", page=TITLE, prop="text|revid", format="json", formatversion=2))
    req = urllib.request.Request(url, headers={"User-Agent": "TheCrimsonLedger/1.0 (fan history site; weekly update)"})
    for attempt in range(6):
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=30).read())
            return d["parse"]["text"], d["parse"]["revid"]
        except Exception as e:
            print("fetch retry:", e, file=sys.stderr); time.sleep(15 * (attempt + 1))
    sys.exit(2)

def clean(s):
    s = re.sub(r"<sup.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

GROUP = {"Passing records": "Passing", "Rushing records": "Rushing", "Receiving records": "Receiving",
         "Total offense (combined passing/rushing stats)": "Total offense", "Interceptions": "Defense",
         "Tackles": "Defense", "Sacks": "Defense", "Field goals": "Kicking",
         "Field goal percentages": "Kicking", "Longest Field goals": "Kicking"}
NAME = {"Combined yards": "Total yards", "Field goal percentages": "Field goal %",
        "Longest Field goals": "Longest field goal"}

def yrs(s):
    ys = re.findall(r"\d{4}", s)
    return ys[0] if len(ys) == 1 else (f"{ys[0]}–{ys[-1][2:]}" if ys else s)

def parse(h):
    h = re.sub(r"<style.*?</style>", "", h, flags=re.S)
    toks = [(m.start(), "h", int(m.group(1)), clean(m.group(2))) for m in re.finditer(r"<h([234])[^>]*>(.*?)</h\1>", h, re.S)]
    toks += [(m.start(), "t", 0, m.group(1)) for m in re.finditer(r"<table[^>]*>(.*?)</table>", h, re.S)]
    toks.sort()
    h3 = h4 = None; out = {}
    for _, kind, lvl, body in toks:
        if kind == "h":
            if lvl == 3: h3, h4 = body, None
            elif lvl == 4: h4 = body
            else: h3 = h4 = None
            continue
        rows = [[clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
                for r in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)]
        rows = [r for r in rows if any(r)]
        if not rows or not h3 or h3 not in GROUP or "Rank" not in " ".join(rows[0]):
            continue
        head = [c.replace("Career ", "") for c in rows[0]]
        hj = " ".join(rows[0])
        span = "career" if ("Career" in hj or "Years" in hj) else ("game" if "Opponent" in hj else "season")
        stat = NAME.get(h4 or h3, h4 or h3); vcol = head[2]; rank = None; ents = []
        for r in rows[1:]:
            if len(r) < len(head): r = [rank] + r
            rank = r[0]; rec = dict(zip(head, r))
            val = rec.get(vcol, ""); extra = rec.get("FGs", "") if vcol == "FG%" else ""
            ents.append([rec["Rank"], rec["Player"], val + (f" ({extra} made)" if extra else ""),
                         yrs(rec.get("Years", rec.get("Year", ""))), rec.get("Opponent", "")])
        key = (GROUP[h3], stat)
        out.setdefault(key, {"g": key[0], "s": stat, "unit": vcol, "v": {}})["v"][span] = ents
    return list(out.values())

text, rev = fetch()
new = parse(text)
if len(new) < 12 or sum(len(r["v"]) for r in new) < 35:
    print("parse looks incomplete; nothing written", file=sys.stderr); sys.exit(2)
plain = re.sub(r"\s+", " ", clean(re.sub(r"<style.*?</style>", "", text, flags=re.S)))
m = re.search(r"updated through ([^.]*?\d{4})", plain)
through = m.group(1).strip() if m else None
print("Wikipedia revision:", rev)
print("Updated through:", through or "(not stated)")

try: old = json.load(open(DATA))
except Exception: old = []
oldmap = {(r["s"], sp): {(e[1], e[3], e[4]): e for e in ents} for r in old for sp, ents in r["v"].items()}
changes = 0
for r in new:
    for sp, ents in r["v"].items():
        o = oldmap.get((r["s"], sp), {})
        n = {(e[1], e[3], e[4]): e for e in ents}
        for k, e in n.items():
            if k not in o: print(f"NEW      {r['s']} / {sp}: #{e[0]} {e[1]} {e[2]} {e[3]} {e[4]}".rstrip()); changes += 1
            elif o[k][2] != e[2] or o[k][0] != e[0]: print(f"CHANGED  {r['s']} / {sp}: {e[1]} {o[k][2]} (#{o[k][0]}) -> {e[2]} (#{e[0]})"); changes += 1
        for k, e in o.items():
            if k not in n: print(f"DROPPED  {r['s']} / {sp}: {e[1]} {e[2]} {e[3]}"); changes += 1
print(f"{changes} change(s)")

if DRY: sys.exit(0)
json.dump(new, open(DATA, "w"), separators=(",", ":"), ensure_ascii=False)
page = open(PAGE).read()
page, k = re.subn(r"const REC=\[.*?\];\n", lambda _: "const REC=" + json.dumps(new, separators=(",", ":"), ensure_ascii=False) + ";\n", page, count=1, flags=re.S)
if k != 1: print("could not find REC in page", file=sys.stderr); sys.exit(2)
if through:
    dm = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})", through)
    ABBR = {"January":"Jan.","February":"Feb.","March":"March","April":"April","May":"May","June":"June","July":"July","August":"Aug.","September":"Sept.","October":"Oct.","November":"Nov.","December":"Dec."}
    short = f"{ABBR[dm.group(1)]} {dm.group(2)}, {dm.group(3)}" if dm else through
    page = re.sub(r'(<span class="label">Individual leaders · through )[^<]*(</span>)', lambda mm: mm.group(1) + html.escape(short, quote=False) + mm.group(2), page, count=1)
    page = re.sub(r"\(updated through [^)]*\)", lambda mm: "(updated through " + html.escape(through, quote=False) + ")", page, count=1)
open(PAGE, "w").write(page)
print("written")
