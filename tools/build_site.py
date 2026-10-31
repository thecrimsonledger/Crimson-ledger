"""Turn the artifact page into a standalone website folder: build_site.py PAGE.html OUT_DIR"""
import re, sys, os, shutil

page, out = sys.argv[1], sys.argv[2]
body = open(page).read()
body = re.sub(r"<title>.*?</title>\n?", "", body, count=1)
body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
links = re.match(r"((?:<link[^>]*>\n)+)", body).group(1); body = body[len(links):]
style = re.match(r"(<style>.*?</style>\n)", body, re.S).group(1); body = body[len(style):]
desc = ("Every Alabama football game since 1892: records, head-to-head history, player record book, "
        "strange-but-true facts and game-week previews. An independent fan history project.")
fav = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
       "%3Crect width='64' height='64' rx='8' fill='%2317191A'/%3E%3Crect y='54' width='64' height='10' fill='%239E1B32'/%3E"
       "%3Ctext x='32' y='44' font-family='Impact,Arial Narrow,sans-serif' font-size='36' font-weight='900' "
       "text-anchor='middle' fill='%23E9B44C'%3ECL%3C/text%3E%3C/svg%3E")
reset = (":root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
         "body{margin:0;font:14px/1.5 system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}\n")
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Crimson Ledger</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="The Crimson Ledger">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{fav}">
<link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#17191A">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Crimson Ledger">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
{links}<style>{reset}</style>
{style}</head>
<body>
{body}</body>
</html>
"""
if os.path.isdir(out): shutil.rmtree(out)
os.makedirs(out)
open(os.path.join(out, "index.html"), "w").write(html)
print("built", os.path.join(out, "index.html"), len(html))
