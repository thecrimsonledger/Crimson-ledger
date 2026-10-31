"""The Crimson Ledger share cards: 1080x1920 vertical graphics for TikTok, Reels, Stories and Shorts."""
import json, os, sys
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "cards")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
BOARD, FG, MUTED, LINE = (20, 22, 23), (242, 242, 240), (163, 169, 171), (52, 57, 61)
CRIM, PINK, GOLD, BLUE = (158, 27, 50), (236, 106, 128), (233, 180, 76), (147, 175, 200)

def disp(size, weight=800):
    f = ImageFont.truetype(os.path.join(FONTS, "BigShoulders.ttf"), size)
    f.set_variation_by_axes([weight]); return f
def mono(size, bold=False):
    return ImageFont.truetype(os.path.join(FONTS, "PlexMono-SemiBold.ttf" if bold else "PlexMono-Regular.ttf"), size)

NICK = {"1926-01-01":"The South's arrival","1962-01-01":"Bryant's first title capper","1966-01-01":"Back-to-back titles","1967-12-02":"Run in the Mud","1972-12-02":"Punt Bama Punt","1979-01-01":"The Goal Line Stand","1981-11-28":"Bryant's 315th win","1985-11-30":"Van Tiffin's 52-yarder","1993-01-01":"Upsetting the champs","2009-12-05":"Saban's first SEC title","2010-01-07":"Title No. 13","2010-11-26":"The Camback","2011-11-05":"Game of the Century","2012-01-09":"The rematch shutout","2013-01-07":"Back-to-back","2013-11-30":"Kick Six","2016-01-11":"The onside kick","2018-01-08":"2nd and 26","2021-01-11":"The COVID-season title","2021-11-27":"Four overtimes","2023-11-25":"4th and 31","2023-12-02":"Ending Georgia's 29-game streak","2024-01-01":"Saban's last game","1893-02-22":"The first Iron Bowl","1948-12-04":"The series returns"}
RAW = json.load(open(os.path.join(HERE, "allgames.json")))
GAMES = [dict(d=r[0], s=r[1], y=int(r[0][:4]), opp=r[2], loc=r[3], res=r[4], a=r[5], o=r[6], note=r[8], site=r[9], n=NICK.get(r[0], "")) for r in RAW]

def at(g): return "at" if g["loc"] == "A" else "vs."
def rescol(g): return PINK if g["res"] == "W" else BLUE if g["res"] == "L" else MUTED
def rec(w, l, t): return f"{w}–{l}" + (f"–{t}" if t else "")
MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()

def base(kicker):
    im = Image.new("RGB", (W, H), BOARD); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=CRIM)
    d.text((72, 92), "THE CRIMSON LEDGER", font=disp(54, 900), fill=FG)
    d.text((W - 72, 106), kicker, font=mono(26, True), fill=MUTED, anchor="ra")
    d.line([72, 176, W - 72, 176], fill=LINE, width=2)
    d.rectangle([0, H - 150, W, H], fill=CRIM)
    d.text((72, H - 75), "Every Alabama game since 1892", font=mono(28), fill=FG, anchor="lm")
    return im, d

def fit(d, text, maxw, size, weight=800):
    while size > 30:
        f = disp(size, weight)
        if d.textlength(text, font=f) <= maxw: return f
        size -= 4
    return disp(size, weight)

def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])

def otd_card(md):
    games = sorted([g for g in GAMES if g["d"][5:] == md], key=lambda g: g["d"], reverse=True)
    if not games: return None
    top = (next((g for g in games if g["n"]), None) or next((g for g in games if g["note"]), None)
           or max(games, key=lambda g: (g["res"] == "W", g["a"] - g["o"])))
    m, dd = int(md[:2]), int(md[3:])
    im, d = base("ON THIS DAY")
    d.text((72, 230), f"{MON[m-1]} {dd}", font=disp(300, 900), fill=GOLD)
    w = sum(g["res"] == "W" for g in games); l = sum(g["res"] == "L" for g in games)
    d.text((76, 560), f"{len(games)} GAME{'S' if len(games)>1 else ''} ON THIS DATE  ·  {rec(w,l,len(games)-w-l)}", font=mono(30, True), fill=MUTED)
    y = 660
    d.text((72, y), str(top["y"]), font=disp(150, 900), fill=FG); y += 170
    head = top["n"] or top["note"] or ("Biggest win on this date" if top["res"] == "W" else "From the archive")
    f = fit(d, head.upper(), W - 144, 92)
    for ln in wrap(d, head.upper(), f, W - 144)[:2]:
        d.text((72, y), ln, font=f, fill=FG); y += f.size + 6
    y += 14
    word = "Won" if top["res"] == "W" else "Lost" if top["res"] == "L" else "Tied"
    d.text((72, y), f"{word} {top['a']}–{top['o']} {at(top)} {top['opp']}", font=mono(38, True), fill=rescol(top)); y += 60
    if top["note"] and top["n"]:
        d.text((72, y), top["note"], font=mono(30), fill=MUTED); y += 50
    others = [g for g in games if g is not top]
    if others:
        y = max(y + 60, 1100)
        d.line([72, y, W - 72, y], fill=LINE, width=2); y += 30
        fitn = min(len(others), (H - 230 - y - 56) // 52)
        d.text((72, y), "ALSO ON THIS DATE" + (f"  ·  LATEST {fitn} OF {len(others)}" if fitn < len(others) else ""), font=mono(26, True), fill=MUTED); y += 56
        for g in others[:fitn]:
            d.text((72, y), str(g["y"]), font=mono(32, True), fill=rescol(g))
            d.text((200, y), f"{g['res']} {g['a']}–{g['o']} {at(g)} {g['opp']}"[:40], font=mono(32), fill=FG); y += 52
    name = f"otd-{md}.png"; im.save(os.path.join(OUT, name)); return name, games, top

def series(opp):
    gs = [g for g in GAMES if g["opp"] == opp]
    w = sum(g["res"] == "W" for g in gs); l = sum(g["res"] == "L" for g in gs); t = len(gs) - w - l
    k, r = 0, gs[-1]["res"]
    for g in reversed(gs):
        if g["res"] != r: break
        k += 1
    return gs, w, l, t, f"{r}{k}"

def series_cards(opp, when, where):
    gs, w, l, t, streak = series(opp)
    names = []
    # 1. overview
    im, d = base("GAME WEEK")
    d.text((72, 230), "ALABAMA", font=disp(170, 900), fill=FG)
    d.text((72, 400), f"{'AT' if where=='A' else 'VS.'} {opp.upper()}", font=fit(d, f"AT {opp.upper()}", W-144, 170, 900), fill=GOLD)
    d.text((76, 600), when.upper(), font=mono(30, True), fill=MUTED)
    d.text((72, 720), "ALL-TIME SERIES", font=mono(28, True), fill=MUTED)
    d.text((72, 760), rec(w, l, t), font=disp(260, 900), fill=PINK)
    stats = [("Meetings", str(len(gs))), ("First meeting", str(gs[0]["y"])),
             ("Current streak", f"{'Won' if streak[0]=='W' else 'Lost' if streak[0]=='L' else 'Tied'} {streak[1:]}"),
             ("Last meeting", f"{gs[-1]['res']} {gs[-1]['a']}–{gs[-1]['o']}, {gs[-1]['y']}")]
    home = [g for g in gs if g["loc"] == where]
    hw = sum(g["res"] == "W" for g in home); hl = sum(g["res"] == "L" for g in home)
    stats.append(("At their place" if where == "A" else "At home", rec(hw, hl, len(home)-hw-hl)))
    y = 1110
    for k_, v in stats:
        d.line([72, y, W-72, y], fill=LINE, width=2)
        d.text((72, y + 26), k_.upper(), font=mono(28, True), fill=MUTED)
        d.text((W-72, y + 18), v, font=disp(56, 800), fill=FG, anchor="ra"); y += 110
    n = f"week-{opp.lower().replace(' ','-')}-1-series.png"; im.save(os.path.join(OUT, n)); names.append(n)
    # 2. biggest wins and closest games
    im, d = base("GAME WEEK")
    d.text((72, 230), f"VS. {opp.upper()}", font=fit(d, f"VS. {opp.upper()}", W-144, 150, 900), fill=GOLD)
    y = 430
    for title, rows in [("BIGGEST WINS", sorted([g for g in gs if g["res"]=="W"], key=lambda g: -(g["a"]-g["o"]))[:5]),
                        ("CLOSEST FINISHES", sorted([g for g in gs if g["res"]!="T"], key=lambda g: (abs(g["a"]-g["o"]), -g["y"]))[:6])]:
        d.text((72, y), title, font=disp(72, 900), fill=FG); y += 100
        for g in rows:
            d.text((72, y), str(g["y"]), font=mono(36, True), fill=rescol(g))
            d.text((220, y), f"{g['res']} {g['a']}–{g['o']}", font=mono(36), fill=FG)
            tag = g["n"] or ("OT" if False else "")
            if g["n"]: d.text((W-72, y+4), g["n"], font=mono(26), fill=MUTED, anchor="ra")
            y += 62
        y += 50
    n = f"week-{opp.lower().replace(' ','-')}-2-extremes.png"; im.save(os.path.join(OUT, n)); names.append(n)
    # 3. last 10 meetings
    im, d = base("GAME WEEK")
    d.text((72, 230), "THE LAST 10", font=disp(170, 900), fill=FG)
    d.text((76, 420), f"ALABAMA VS. {opp.upper()}", font=mono(32, True), fill=GOLD)
    last = gs[-10:][::-1]; lw = sum(g["res"]=="W" for g in last); ll = sum(g["res"]=="L" for g in last)
    d.text((76, 470), f"{rec(lw, ll, len(last)-lw-ll)} IN THE LAST {len(last)}", font=mono(32, True), fill=MUTED)
    y = 580
    for g in last:
        d.line([72, y, W-72, y], fill=LINE, width=2)
        d.rectangle([72, y+22, 84, y+86], fill=rescol(g))
        d.text((110, y+22), str(g["y"]), font=disp(64, 800), fill=FG)
        d.text((290, y+30), f"{g['res']} {g['a']}–{g['o']}", font=mono(40, True), fill=rescol(g))
        d.text((W-72, y+36), {"H":"Home","A":"Away","N":"Neutral"}[g["loc"]], font=mono(30), fill=MUTED, anchor="ra")
        y += 108
    n = f"week-{opp.lower().replace(' ','-')}-3-last10.png"; im.save(os.path.join(OUT, n)); names.append(n)
    return names, (gs, w, l, t, streak)

if __name__ == "__main__":
    start = date.fromisoformat(sys.argv[1]); days = int(sys.argv[2])
    report = {"otd": [], "week": None}
    for i in range(days):
        dt = start + timedelta(days=i); r = otd_card(dt.strftime("%m-%d"))
        if r:
            name, games, top = r
            report["otd"].append(dict(date=dt.isoformat(), file=name, n=len(games), top=top, games=games))
        else:
            report["otd"].append(dict(date=dt.isoformat(), file=None))
    if len(sys.argv) > 3:
        names, (gs, w, l, t, streak) = series_cards(sys.argv[3], sys.argv[4], sys.argv[5])
        report["week"] = dict(files=names, w=w, l=l, t=t, streak=streak, n=len(gs), first=gs[0]["y"], last=gs[-1],
                              biggest=sorted([g for g in gs if g["res"]=="W"], key=lambda g: -(g["a"]-g["o"]))[:3],
                              last10=gs[-10:])
    json.dump(report, open(os.path.join(OUT, "report.json"), "w"), indent=1)
    for o in report["otd"]: print(o["date"], o.get("file"), o.get("n"), o.get("top", {}).get("y") if o.get("top") else "")
    if report["week"]: print(report["week"]["files"], rec(w, l, t), streak)
