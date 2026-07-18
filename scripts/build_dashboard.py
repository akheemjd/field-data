#!/usr/bin/env python3
"""Field Data — Ag market dashboard. 11 modules: commodities, fx, fertilizer, diesel, basis, gdd, rail, ports."""
import json, os, sys, csv
from datetime import datetime

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

commodities = load('commodities.json'); fuel = load('fuel.json')
rail = load('rail.json'); port = load('port.json')
fertilizer = load('fertilizer.json'); exchange = load('exchange.json')
basis = load('basis.json'); gdd = load('gdd.json')
killswitch = load('killswitch.json')

if killswitch.get('publish') == False:
    with open(OUT,'w') as f: f.write("<!DOCTYPE html><html><body style='background:#FFF8F0'><h1>Paused</h1></body></html>")
    sys.exit(0)

# History
now_iso = datetime.utcnow().isoformat()
hd = os.path.join(DATA_DIR,'history'); os.makedirs(hd,exist_ok=True)
keys = ['canola','wheat','durum','barley','oats','corn','soy','lentils','flax','peas']
p = os.path.join(hd,'commodities.csv'); exists = os.path.exists(p)
with open(p,'a',newline='') as f:
    w = csv.writer(f)
    if not exists: w.writerow(['t']+keys)
    w.writerow([now_iso]+[commodities.get(k,'') for k in keys])

def T(s): return str(s)

# Data rows
com_cards = ''.join('<div class="com-card"><div class="com-label">'+n+'</div><div class="com-price">'+T(commodities.get(k,'-'))+'<span class="com-unit">/t</span></div></div>\n' for n,k in zip(['Canola','Wheat','Durum','Barley','Oats','Corn','Soy','Lentils','Flax','Peas'],keys))

fert_rows = ''.join('<tr><td>'+f['name']+'</td><td class="val">$'+T(f['price'])+'</td><td class="val"><span class="'+('com-up' if T(f.get('change','-')).startswith('+') else 'com-down' if T(f.get('change','-')).startswith('-') else '')+'">'+T(f.get('change','-'))+'</span></td><td>'+f['region']+'</td></tr>\n' for f in fertilizer.get('fertilizers',[]))

rail_rows = ''.join('<tr><td>'+r['route']+'</td><td class="val">$'+T(r.get('rate','-'))+'</td><td class="val">'+T(r.get('change','-'))+'</td></tr>\n' for r in rail.get('routes',[]))
port_rows = ''.join('<tr><td>'+p['name']+'</td><td class="val">'+T(p.get('volume','-'))+'</td><td>'+T(p.get('trend','-'))+'</td></tr>\n' for p in port.get('ports',[]))
basis_rows = ''.join('<tr><td>'+b['name']+'</td><td class="val">$'+T(b['futures'])+'</td><td class="val">$'+T(b['cash'])+'</td><td class="val '+('com-up' if b.get('trend')=='↑' else 'com-down' if b.get('trend')=='↓' else '')+'">'+T(b.get('basis','-'))+' '+T(b.get('trend','-'))+'</td></tr>\n' for b in basis.get('regions',[]))
gdd_rows = ''.join('<tr><td>'+g['city']+'</td><td class="val">'+T(g['gdd'])+'</td><td class="val">'+T(g['normal'])+'</td><td class="val" style="color:var(--sprout);">+'+T(g.get('days_ahead',''))+' days</td></tr>\n' for g in gdd.get('cities',[]))

fx_rate = exchange.get('rate','-'); fx_chg = T(exchange.get('change','-'))
fx_cls = 'com-up' if fx_chg.startswith('+') else 'com-down'
fuel_p = fuel.get('diesel_ab','-')

CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--soil:#3E2C1C;--wheat:#F5E6D0;--straw:#C4A882;--clay:#8B6914;--field:#5C4033;--sprout:#4A7C3F;--amber:#E8A317;--rust:#B7410E;--line:#D4C4B0;--rad:8px}
body{background:var(--wheat);color:var(--soil);font-family:'Inter',-apple-system,sans-serif;font-size:0.875rem;line-height:1.5}
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


# === 30-day canola price chart (SVG) ===
import csv as _csv
from collections import OrderedDict as _OD

def build_price_chart():
    path = os.path.join(DATA_DIR, "history", "commodities.csv")
    if not os.path.exists(path):
        return '<div style="color:var(--clay);font-size:0.75rem;">History accumulating — chart will fill over time.</div>'
    dates, vals = [], []
    with open(path) as fh:
        for row in _csv.DictReader(fh):
            dates.append(row["t"][:10])
            vals.append(float(row.get("canola",0)))
    dates = dates[-30:]; vals = vals[-30:]
    if len(vals) < 2:
        return '<div style="color:var(--clay);font-size:0.75rem;">Need more data for chart.</div>'
    mi, mx = min(vals), max(vals)
    rng = mx - mi or 10
    W, H = 600, 140
    pL, pR, pT, pB = 40, 10, 10, 22
    pw, ph = W-pL-pR, H-pT-pB
    s = '<svg viewBox="0 0 '+str(W)+' '+str(H)+'" style="width:100%;height:auto;max-height:160px;">'
    # Grid lines
    for i in range(3):
        y = pT + ph * (i/2)
        s += '<line x1="'+str(pL)+'" y1="'+str(int(y))+'" x2="'+str(W-pR)+'" y2="'+str(int(y))+'" stroke="var(--line)" stroke-width="0.5"/>'
    # Baseline
    s += '<line x1="'+str(pL)+'" y1="'+str(H-pB)+'" x2="'+str(W-pR)+'" y2="'+str(H-pB)+'" stroke="var(--line)" stroke-width="1"/>'
    # Price line
    pts = []
    for i, v in enumerate(vals):
        x = pL + (pw * i / max(1, len(vals)-1))
        y = pT + ph - ((v-mi)/rng * ph)
        pts.append(str(int(x))+','+str(int(y)))
    s += '<polyline points="'+' '.join(pts)+'" fill="none" stroke="var(--sprout)" stroke-width="2" stroke-linejoin="round"/>'
    # Dots
    for i, v in enumerate(vals):
        x = pL + (pw * i / max(1, len(vals)-1))
        y = pT + ph - ((v-mi)/rng * ph)
        s += '<circle cx="'+str(int(x))+'" cy="'+str(int(y))+'" r="2.5" fill="var(--sprout)"/>'
    # Last value label
    s += '<text x="'+str(int(pL+pw))+'" y="'+str(int(pT+ph-((vals[-1]-mi)/rng*ph))-6)+'" text-anchor="end" font-size="10" font-weight="600" fill="var(--sprout)">'+str(vals[-1])+'</text>'
    # Date labels
    for i in [0, len(dates)-1]:
        x = pL + (pw * i / max(1, len(dates)-1))
        s += '<text x="'+str(int(x))+'" y="'+str(H-6)+'" text-anchor="middle" font-size="7" fill="var(--clay)">'+dates[i][-5:]+'</text>'
    s += '</svg>'
    return s

# === 7-day forecast using linear regression ===
def build_forecast():
    path = os.path.join(DATA_DIR, "history", "commodities.csv")
    if not os.path.exists(path):
        return ""
    vals = []
    with open(path) as fh:
        for row in _csv.DictReader(fh):
            vals.append(float(row.get("canola",0)))
    vals = vals[-14:]
    if len(vals) < 7:
        return ""
    n = len(vals)
    x_mean = (n-1)/2; y_mean = sum(vals)/n
    num, den = 0, 0
    for i, y in enumerate(vals):
        num += (i-x_mean)*(y-y_mean)
        den += (i-x_mean)**2
    slope = num/den if den else 0
    intercept = y_mean - slope*x_mean
    fcast = [round(intercept + slope*(n+i), 2) for i in range(7)]
    items = ''.join('<div style="display:flex;justify-content:space-between;padding:4px 8px;font-size:0.75rem;border-bottom:1px solid var(--line);"><span>Day +'+str(i+1)+'</span><span class="val mono">$'+str(f)+'</span></div>' for i,f in enumerate(fcast))
    trend = '↑' if slope > 0 else '↓' if slope < 0 else '→'
    cls = 'com-up' if slope > 0 else 'com-down' if slope < 0 else ''
    return '<div style="margin-top:8px;font-size:0.625rem;color:var(--clay);margin-bottom:6px;">Linear regression on 14-day history <span class="'+cls+'">'+trend+'</span></div><div>'+items+'</div>'

_price_chart = build_price_chart()
_forecast = build_forecast()

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
"""+noindex+"""
<title>Field Data — Ag Market Dashboard | Grain, FX, Fertilizer, Rail, Ports</title>
<meta name="description" content="Free live dashboard for Canadian agriculture. Grain prices, fertilizer index, rail rates, port volumes, weather. No signup.">
<link rel="canonical" href="https://fielddata.co/">
<meta property="og:title" content="Field Data — Ag Market Dashboard">
<meta property="og:description" content="Grain, fertilizer, FX, rail. Free. Always.">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600&family=IBM+Plex+Mono:wght@400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>"""+CSS+"""</style>
</head>
<body>
"""+badge+"""

<div class="banner"><h1>FIELD DATA</h1></div>
<nav><a href="#">Home</a><a href="#">About</a><a href="#">Blog</a></nav>

<div class="main">
  <div style="text-align:center;padding:8px 18px;margin-bottom:18px;font-size:0.875rem;color:var(--clay);">Live grain, fertilizer, FX, rail & port data. Free. Always.</div>

  <div class="grid">
    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Commodity Prices</span><span class="pill pill-live">Live</span></div>
      <div class="com-grid">"""+com_cards+"""</div>
      <div class="card-footer">Updated """+commodities.get('updated','-')[:16]+""" &middot; ICE / CME</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Fertilizer Index</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Product</th><th class="val">Price</th><th class="val">Change</th><th>Region</th></tr>"""+fert_rows+"""</table>
      <div class="card-footer">"""+fertilizer.get('updated','-')[:16]+""" &middot; USDA / StatsCan</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Farm Diesel</span><span class="pill pill-live">Daily</span></div>
      <div style="font-size:2rem;font-weight:600;" class="nums">"""+T(fuel_p)+"""<span style="font-size:0.875rem;color:var(--clay);"> &cent;/L</span></div>
      <div style="font-size:0.75rem;color:var(--clay);">Alberta avg &middot; Cross-linked with NMM</div>
      <div class="card-footer">Public surveys</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">CAD / USD</span><span class="pill pill-live">Live</span></div>
      <div style="display:flex;align-items:baseline;gap:10px;">
        <span style="font-size:2.5rem;font-weight:600;">"""+T(fx_rate)+"""</span>
        <span style="font-size:0.875rem;" class=\""""+fx_cls+"""\">"""+fx_chg+"""</span>
      </div>
      <div style="font-size:0.75rem;color:var(--clay);margin-top:4px;">H: """+T(exchange.get('day_high','-'))+""" &middot; L: """+T(exchange.get('day_low','-'))+"""</div>
      <div class="card-footer">Bank of Canada &middot; """+exchange.get('updated','-')[:16]+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Canola Basis</span><span class="pill pill-live">Daily</span></div>
      <table><tr><th>Region</th><th class="val">Futures</th><th class="val">Cash</th><th class="val">Basis</th></tr>"""+basis_rows+"""</table>
      <div class="card-footer">"""+basis.get('updated','-')[:16]+""" &middot; Futures minus cash</div>
    </div>

    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Canola Price History — 30 Days</span><span class="pill pill-live">Daily</span></div>
      """+_price_chart+"""
      <div class="card-footer">From history archive &middot; Updated every 30 minutes</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Canola Forecast — 7 Days</span><span class="pill pill-live">Model</span></div>
      """+_forecast+"""
      <div class="card-footer">Statistical projection &middot; Informational only</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Growing Degree Days</span><span class="pill pill-live">Daily</span></div>
      <table><tr><th>City</th><th class="val">GDD</th><th class="val">Normal</th><th class="val">Ahead</th></tr>"""+gdd_rows+"""</table>
      <div class="card-footer">"""+gdd.get('updated','-')[:16]+""" &middot; Base 5°C &middot; Open-Meteo</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Rail Freight</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Route</th><th class="val">Rate/t</th><th class="val">Change</th></tr>"""+rail_rows+"""</table>
      <div class="card-footer">Ag Transport Coalition &middot; """+rail.get('updated','-')[:16]+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Grain Ports</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Port</th><th class="val">Volume</th><th class="val">Trend</th></tr>"""+port_rows+"""</table>
      <div class="card-footer">Port authorities &middot; """+port.get('updated','-')[:16]+"""</div>
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

with open(OUT,'w') as f:
    f.write(html)

print("[%s] Built: %s (%s bytes)" % (MODE.upper(), OUT, len(html)))
