# The Crimson Ledger

Every Alabama football game since 1892: season records, head-to-head history, a player record book, strange-but-true facts, game-week previews and on-this-day. An independent fan history project, not affiliated with the University of Alabama or the SEC.

Live at https://thecrimsonledger.com

## Layout
- `index.html` – the site (static, no build step)
- `data/allgames.json` – every game: date, season, opponent, site, result, scores, conference flag, postseason label, neutral city, source flag
- `data/records.json` – individual statistical leaders
- `tools/update.py` – adds new results to the page and data
- `tools/cards.py` – makes vertical social cards from the data
- `tools/build_site.py` – rebuilds `index.html` from `tools/page-source.html`
- `tools/build_pages.py` – builds `vs/` (one page per opponent), `seasons/` (one page per season), `stories/`, `players/`, `trivia/`, `coaches/`, `sitemap.xml` and `robots.txt`, and makes `games/` (the Game Book) and `records/` (the Record Book) from the built `index.html`. Run it after `build_site.py`, every weekly update.
- Site nav and footer links live once in `tools/page-source.html` (between the `SITENAV` markers); `build_pages.py` copies them into every other page.

## Sources
Game results from James Howell's college football scores archive (1902 on) and Wikipedia season pages (1892–1901); 2026 results checked against two live score sources. Season records and statistical leaders from Wikipedia.
