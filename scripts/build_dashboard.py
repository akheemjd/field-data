#!/usr/bin/env python3
"""Field Data — Ag market dashboard for Canadian and US grain producers.
Architecture mirrors NMM. Free. No signup. Newsletter-first.
"""
import json, os, sys, csv
from datetime import datetime
from collections import OrderedDict

MODE = sys.argv[1] if len(sys.argv) > 1 else 'production'
STAGING = MODE == 'staging'
BASE = os.path.expanduser('~/grain-data-dashboard')
DATA_DIR = os.path.join(BASE, 'data')

if STAGING:
    OUT_DIR = os.path.join(BASE, 'docs', 'v2')
    BASE_PATH = '/v2/'
else:
    OUT_DIR = os.path.join(BASE, 'docs')
    BASE_PATH = '/'

os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'index.html')

def load(name):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

# === Load data ===
commodities = load('commodities.json')
fuel = load('fuel.json')
weather = load('weather.json')
rail = load('rail.json')
port = load('port.json')
killswitch = load('killswitch.json')

# === Kill switch ===
if killswitch.get('publish') == False:
    html = "<!DOCTYPE html><html><body style='background:#FFF8F0;color:#5C4033;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;'><h1>Dashboard Paused</h1></body></html>"
    with open(OUT, 'w') as f: f.write(html)
    sys.exit(0)

# === History archive ===
now_iso = datetime.utcnow().isoformat()
def archive_append(filename, headers, row):
    history_dir = os.path.join(DATA_DIR, 'history')
    os.makedirs(history_dir, exist_ok=True)
    path = os.path.join(history_dir, filename)
    exists = os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if not exists: w.writerow(headers)
        w.writerow(row)

if commodities.get('canola'):
    archive_append('commodities.csv', ['timestamp','canola','wheat','corn','soy'],
        [now_iso, commodities.get('canola',''), commodities.get('wheat',''), commodities.get('corn',''), commodities.get('soy','')])

# === CSS ===
CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --soil:#3E2C1C;--wheat:#F5E6D0;--straw:#C4A882;--clay:#8B6914;--field:#5C4033;
  --sprout:#4A7C3F;--amber:#E8A317;--rust:#B7410E;--line:#D4C4B0;
  --rad:8px
}
body{background:var(--wheat);color:var(--soil);font-family:'Inter',-apple-system,sans-serif;font-size:0.875rem;line-height:1.5;-webkit-font-smoothing:antialiased}
*{font-variant-numeric:tabular-nums}
.nums{font-family:'Barlow Condensed',sans-serif;font-weight:600}
.mono{font-family:'IBM Plex Mono',monospace}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--wheat)}::-webkit-scrollbar-thumb{background:var(--straw);border-radius:3px}
*{scrollbar-width:thin;scrollbar-color:var(--straw) var(--wheat)}

.banner{background:#FFF8F0;border-bottom:1px solid var(--line);padding:0 24px;display:flex;align-items:center;justify-content:center;height:64px;position:sticky;top:0;z-index:999}
.banner h1{font-size:0.875rem;font-weight:700;color:var(--soil);font-family:'IBM Plex Mono',monospace}

nav{background:#FFF8F0;border-bottom:1px solid var(--line);padding:0 24px;display:flex;justify-content:center;gap:32px}
nav a{color:var(--clay);text-decoration:none;font-size:0.75rem;font-weight:500;padding:8px 0;border-bottom:2px solid transparent;transition:all .15s}
nav a:hover{border-color:var(--soil);color:var(--soil)}

.main{max-width:1200px;margin:0 auto;padding:20px 20px 40px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}

.module{background:#FFF8F0;border:1px solid var(--line);border-radius:var(--rad);padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.module.hero{grid-column:span 12}
.module.wide{grid-column:span 8}
.module.standard{grid-column:span 4}

.eyebrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.eyebrow-label{font-size:0.625rem;color:var(--clay);text-transform:uppercase;letter-spacing:.08em;font-weight:600}
.pill{font-size:0.5rem;padding:2px 7px;border-radius:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
.pill-live{color:var(--sprout);background:rgba(74,124,63,.1)}

.card-footer{margin-top:10px;padding-top:6px;border-top:1px solid var(--line);font-size:0.625rem;color:var(--clay);font-family:'IBM Plex Mono',monospace}

/* Commodity grid */
.com-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.com-card{background:var(--soil);color:var(--wheat);padding:16px;border-radius:6px}
.com-label{font-size:0.625rem;text-transform:uppercase;letter-spacing:.06em;opacity:.7}
.com-price{font-size:2rem;line-height:1.1;margin:4px 0}.com-unit{font-size:0.75rem;opacity:.7}
.com-change{font-size:0.75rem;font-weight:600}.com-up{color:var(--sprout)}.com-down{color:var(--rust)}

table{width:100%;border-collapse:collapse;font-size:0.75rem}
th{text-align:left;padding:5px 8px;border-bottom:2px solid var(--line);font-size:0.625rem;text-transform:uppercase;letter-spacing:.05em;color:var(--clay)}
td{padding:6px 8px;border-bottom:1px solid var(--line)}
.val{font-family:'IBM Plex Mono',monospace;text-align:right;font-weight:600}

@media(max-width:900px){
  .module{grid-column:span 12!important}
  .main{padding:12px 12px 32px}
  .com-price{font-size:1.5rem}
}
"""

# === HTML ===
noindex = '<meta name="robots" content="noindex">' if STAGING else ''
staging_badge = '<div style="position:fixed;bottom:8px;right:8px;background:var(--amber);color:#fff;padding:4px 8px;border-radius:4px;font-size:0.625rem;font-weight:600;z-index:9999;">STAGING</div>' if STAGING else ''

# Commodity cards
com_cards = ''
cdata = {'Canola': commodities.get('canola','—'), 'Wheat': commodities.get('wheat','—'), 'Corn': commodities.get('corn','—'), 'Soy': commodities.get('soy','—')}
for name, price in cdata.items():
    chg = 0  # placeholder — real data later
    up = chg >= 0
    com_cards += f'''<div class="com-card">
  <div class="com-label">{name}</div>
  <div class="com-price">{price}<span class="com-unit"> /bu</span></div>
  <div class="com-change {'com-up' if up else 'com-down'}">{'+' if up else ''}{chg}</div>
</div>'''

# Rail table
rail_rows = ''
for r in rail.get('routes', []):
    rail_rows += f'<tr><td>{r["route"]}</td><td class="val">${r.get("rate","—")}</td><td class="val">{r.get("change","—")}</td></tr>\n'

# Port volumes
port_rows = ''
for p in port.get('ports', []):
    port_rows += f'<tr><td>{p["name"]}</td><td class="val">{p.get("volume","—")}</td><td>{p.get("trend","—")}</td></tr>\n'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
{noindex}
<title>Field Data — Canadian Ag Market Dashboard | Grain Prices, Rail Rates, Port Volumes</title>
<meta name="description" content="Free live dashboard for Canadian agriculture. Grain prices, rail freight rates, port volumes, weather. No signup.">
<link rel="canonical" href="https://fielddata.co/">
<meta property="og:title" content="Field Data — Canadian Ag Market Dashboard">
<meta property="og:description" content="Grain prices, rail rates, port volumes. Free. Always.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="{BASE_PATH}favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600&family=IBM+Plex+Mono:wght@400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{staging_badge}

<div class="banner">
  <h1>FIELD DATA</h1>
</div>
<nav>
  <a href="#">Home</a>
  <a href="#">About</a>
  <a href="#">Blog</a>
</nav>

<div class="main">

  <div style="text-align:center;padding:8px 18px;margin-bottom:18px;font-size:0.875rem;color:var(--clay);">
    Live grain prices, rail rates, and port volumes. Free. Always.
  </div>

  <div class="grid">

    <!-- Commodities — HERO -->
    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Commodity Prices</span><span class="pill pill-live">Live</span></div>
      <div class="com-grid">{com_cards}</div>
      <div class="card-footer">Updated {commodities.get('updated','—')[:16]}</div>
    </div>

    <!-- Weather — WIDE -->
    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Weather & GDD</span><span class="pill pill-live">Live</span></div>
      <div style="color:var(--clay);font-size:0.75rem;">Prairie growing regions — coming soon</div>
      <div class="card-footer">Data from Open-Meteo</div>
    </div>

    <!-- Diesel — STANDARD -->
    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Farm Diesel</span><span class="pill pill-live">Daily</span></div>
      <div style="font-size:2rem;font-weight:600;" class="nums">{fuel.get('diesel_ab','—')}<span style="font-size:0.875rem;color:var(--clay);"> ¢/L</span></div>
      <div style="font-size:0.75rem;color:var(--clay);">Alberta farm diesel</div>
      <div class="card-footer">Source: public surveys</div>
    </div>

    <!-- Rail Rates — WIDE -->
    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Rail Freight</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Route</th><th class="val">Rate/tonne</th><th class="val">Change</th></tr>{rail_rows}</table>
      <div class="card-footer">Ag Transport Coalition</div>
    </div>

    <!-- Port Volumes — STANDARD -->
    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Grain Port Volumes</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Port</th><th class="val">Volume</th><th class="val">Trend</th></tr>{port_rows}</table>
      <div class="card-footer">Port authorities</div>
    </div>

  </div>
</div>

<div style="text-align:center;max-width:480px;margin:32px auto 0;padding:24px;background:#FFF8F0;border:1px solid var(--line);border-radius:var(--rad);">
  <div style="font-size:0.625rem;color:var(--clay);margin-bottom:12px;">Know someone who would use this? Forward them the link.</div>
  <div style="font-size:0.875rem;font-weight:600;color:var(--soil);margin-bottom:4px;">Get the Weekly Grain Report</div>
  <div style="font-size:0.75rem;color:var(--clay);margin-bottom:16px;">Commodity prices, rail rates, and what it means. Every Wednesday.</div>
  <!-- Ghost signup embed will go here -->
</div>

<footer style="padding:16px 24px;text-align:center;font-size:0.625rem;color:var(--clay);border-top:1px solid var(--line);font-family:'IBM Plex Mono',monospace;">
  &copy; 2026 Field Data &middot; Data from public sources &middot; Informational use only
</footer>
</body>
</html>"""

with open(OUT, 'w') as f:
    f.write(html)

print(f"[{MODE.upper()}] Dashboard built: {OUT}")
print(f"  Size: {len(html):,} bytes")
