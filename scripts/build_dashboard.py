#!/usr/bin/env python3
"""Field Data — Ag market dashboard. Grain prices, fertilizer, rail, ports, diesel, weather."""
import json, os, sys, csv
from datetime import datetime
from collections import OrderedDict

MODE = sys.argv[1] if len(sys.argv) > 1 else 'production'
STAGING = MODE == 'staging'
BASE = os.path.expanduser('~/grain-data-dashboard')
DATA_DIR = os.path.join(BASE, 'data')
OUT_DIR = os.path.join(BASE, 'docs', 'v2') if STAGING else os.path.join(BASE, 'docs')
BASE_PATH = '/v2/' if STAGING else '/'

os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'index.html')

def load(name):
    path = os.path.join(DATA_DIR, name)
    return json.load(open(path)) if os.path.exists(path) else {}

commodities = load('commodities.json')
fuel = load('fuel.json')
weather = load('weather.json')
rail = load('rail.json')
port = load('port.json')
fertilizer = load('fertilizer.json')
killswitch = load('killswitch.json')

if killswitch.get('publish') == False:
    with open(OUT, 'w') as f: f.write("<!DOCTYPE html><html><body style='background:#FFF8F0'><h1>Paused</h1></body></html>")
    sys.exit(0)

# History
now_iso = datetime.utcnow().isoformat()
hd = os.path.join(DATA_DIR, 'history'); os.makedirs(hd, exist_ok=True)
for fname, hdr, row in [('commodities.csv',['t','canola','wheat','durum','barley','oats','corn','soy','lentils','flax','peas'],[now_iso]+[commodities.get(k,'') for k in ['canola','wheat','durum','barley','oats','corn','soy','lentils','flax','peas']])]:
    p = os.path.join(hd, fname); exists = os.path.exists(p)
    with open(p, 'a', newline='') as f:
        w = csv.writer(f)
        if not exists: w.writerow(hdr)
        w.writerow(row)

# Commodity cards
com_cards = ''
for name, key in zip(['Canola','Wheat','Durum','Barley','Oats','Corn','Soy','Lentils','Flax','Peas'],
                     ['canola','wheat','durum','barley','oats','corn','soy','lentils','flax','peas']):
    price = commodities.get(key,'-')
    com_cards += '<div class="com-card"><div class="com-label">'+name+'</div><div class="com-price">'+str(price)+'<span class="com-unit">/t</span></div></div>\n'

# Fertilizer
fert_rows = ''
for f in fertilizer.get('fertilizers', []):
    chg = str(f.get('change','-'))
    cls = 'com-up' if chg.startswith('+') else 'com-down' if chg.startswith('-') else ''
    fert_rows += '<tr><td>'+f['name']+'</td><td class="val">$'+str(f['price'])+'</td><td class="val"><span class="'+cls+'">'+chg+'</span></td><td>'+f['region']+'</td></tr>\n'

# Rail
rail_rows = ''
for r in rail.get('routes', []):
    rail_rows += '<tr><td>'+r['route']+'</td><td class="val">$'+str(r.get('rate','-'))+'</td><td class="val">'+str(r.get('change','-'))+'</td></tr>\n'

# Port
port_rows = ''
for p in port.get('ports', []):
    port_rows += '<tr><td>'+p['name']+'</td><td class="val">'+str(p.get('volume','-'))+'</td><td>'+str(p.get('trend','-'))+'</td></tr>\n'

CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--soil:#3E2C1C;--wheat:#F5E6D0;--straw:#C4A882;--clay:#8B6914;--field:#5C4033;--sprout:#4A7C3F;--amber:#E8A317;--rust:#B7410E;--line:#D4C4B0;--rad:8px}
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
.module.hero{grid-column:span 12}.module.wide{grid-column:span 8}.module.standard{grid-column:span 4}
.eyebrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.eyebrow-label{font-size:0.625rem;color:var(--clay);text-transform:uppercase;letter-spacing:.08em;font-weight:600}
.pill{font-size:0.5rem;padding:2px 7px;border-radius:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.pill-live{color:var(--sprout);background:rgba(74,124,63,.1)}
.card-footer{margin-top:10px;padding-top:6px;border-top:1px solid var(--line);font-size:0.625rem;color:var(--clay);font-family:'IBM Plex Mono',monospace}
.com-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.com-card{background:var(--soil);color:var(--wheat);padding:14px;border-radius:6px}
.com-label{font-size:0.625rem;text-transform:uppercase;letter-spacing:.06em;opacity:.7}
.com-price{font-size:1.75rem;line-height:1.1;margin:4px 0}.com-unit{font-size:0.625rem;opacity:.7}
.com-up{color:var(--sprout)}.com-down{color:var(--rust)}
table{width:100%;border-collapse:collapse;font-size:0.75rem}
th{text-align:left;padding:5px 8px;border-bottom:2px solid var(--line);font-size:0.625rem;text-transform:uppercase;letter-spacing:.05em;color:var(--clay)}
td{padding:6px 8px;border-bottom:1px solid var(--line)}
.val{font-family:'IBM Plex Mono',monospace;text-align:right;font-weight:600}
@media(max-width:900px){.module{grid-column:span 12!important}.main{padding:12px 12px 32px}.com-price{font-size:1.25rem}}
"""

noindex = '<meta name="robots" content="noindex">' if STAGING else ''
badge = '<div style="position:fixed;bottom:8px;right:8px;background:var(--amber);color:#fff;padding:4px 8px;border-radius:4px;font-size:0.625rem;font-weight:600;z-index:9999;">STAGING</div>' if STAGING else ''

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
"""+noindex+"""
<title>Field Data — Ag Market Dashboard | Grain, Fertilizer, Rail, Ports</title>
<meta name="description" content="Free live dashboard for Canadian agriculture. Grain prices, fertilizer index, rail rates, port volumes. No signup.">
<link rel="canonical" href="https://fielddata.co/">
<meta property="og:title" content="Field Data — Ag Market Dashboard">
<meta property="og:description" content="Grain prices, fertilizer costs, rail rates. Free. Always.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href=\""""+BASE_PATH+"""favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600&family=IBM+Plex+Mono:wght@400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>"""+CSS+"""</style>
</head>
<body>
"""+badge+"""

<div class="banner"><h1>FIELD DATA</h1></div>
<nav><a href="#">Home</a><a href="#">About</a><a href="#">Blog</a></nav>

<div class="main">
  <div style="text-align:center;padding:8px 18px;margin-bottom:18px;font-size:0.875rem;color:var(--clay);">Live grain, fertilizer, rail, and port data. Free. Always.</div>

  <div class="grid">
    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Commodity Prices</span><span class="pill pill-live">Live</span></div>
      <div class="com-grid">"""+com_cards+"""</div>
      <div class="card-footer">Updated """+commodities.get('updated','-')[:16]+""" &middot; ICE / CME</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Fertilizer Index</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Product</th><th class="val">Price</th><th class="val">Change</th><th>Region</th></tr>"""+fert_rows+"""</table>
      <div class="card-footer">Updated """+fertilizer.get('updated','-')[:16]+""" &middot; USDA / StatsCan</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Farm Diesel</span><span class="pill pill-live">Daily</span></div>
      <div style="font-size:2rem;font-weight:600;" class="nums">"""+str(fuel.get('diesel_ab','-'))+"""<span style="font-size:0.875rem;color:var(--clay);"> &cent;/L</span></div>
      <div style="font-size:0.75rem;color:var(--clay);">Alberta average</div>
      <div class="card-footer">Public surveys</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Rail Freight</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Route</th><th class="val">Rate/t</th><th class="val">Change</th></tr>"""+rail_rows+"""</table>
      <div class="card-footer">Ag Transport Coalition</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Grain Ports</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Port</th><th class="val">Volume</th><th class="val">Trend</th></tr>"""+port_rows+"""</table>
      <div class="card-footer">Port authorities</div>
    </div>
  </div>
</div>

<div style="text-align:center;max-width:480px;margin:32px auto 0;padding:24px;background:#FFF8F0;border:1px solid var(--line);border-radius:var(--rad);">
  <div style="font-size:0.625rem;color:var(--clay);margin-bottom:12px;">Know someone who would use this? Forward them the link.</div>
  <div style="font-size:0.875rem;font-weight:600;color:var(--soil);margin-bottom:4px;">Get the Weekly Grain Report</div>
  <div style="font-size:0.75rem;color:var(--clay);margin-bottom:16px;">Commodity prices, rail rates, and what it means. Every Wednesday.</div>
</div>

<footer style="padding:16px 24px;text-align:center;font-size:0.625rem;color:var(--clay);border-top:1px solid var(--line);font-family:'IBM Plex Mono',monospace;">
  &copy; 2026 Field Data &middot; Data from public sources &middot; Informational use only
</footer>
</body>
</html>"""

with open(OUT, 'w') as f:
    f.write(html)

print("[%s] Built: %s (%s bytes)" % (MODE.upper(), OUT, len(html)))
