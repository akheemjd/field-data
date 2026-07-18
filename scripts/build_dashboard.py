#!/usr/bin/env python3
"""Field Data — Ag market dashboard. SQLite-backed. 10 modules."""
import sqlite3, os, sys
from datetime import datetime

MODE = sys.argv[1] if len(sys.argv) > 1 else 'production'
STAGING = MODE == 'staging'
BASE = os.path.expanduser('~/grain-data-dashboard')
DATA_DIR = os.path.join(BASE, 'data')
DB_PATH = os.path.join(DATA_DIR, 'fielddata.db')
OUT_DIR = os.path.join(BASE, 'docs', 'v2') if STAGING else os.path.join(BASE, 'docs')
BASE_PATH = '/v2/' if STAGING else '/'
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'index.html')

DB = sqlite3.connect(DB_PATH)
DB.row_factory = sqlite3.Row

def T(s): return str(s) if s is not None else '-'

# === Query latest data ===
now_iso = datetime.utcnow().isoformat()

# Commodity prices (latest per commodity)
coms = {}
for row in DB.execute("SELECT commodity, price FROM (SELECT commodity, price, ROW_NUMBER() OVER (PARTITION BY commodity ORDER BY timestamp DESC) rn FROM commodity_prices) WHERE rn=1"):
    coms[row['commodity']] = row['price']

# Fuel
fuel = {}
for row in DB.execute("SELECT province, price FROM (SELECT province, price, ROW_NUMBER() OVER (PARTITION BY province ORDER BY timestamp DESC) rn FROM fuel_prices WHERE fuel_type='diesel') WHERE rn=1"):
    fuel[row['province']] = row['price']

# Exchange
fx = DB.execute("SELECT rate, day_high, day_low, timestamp FROM exchange_rates ORDER BY timestamp DESC LIMIT 1").fetchone()
fx_rate = fx['rate'] if fx else 1.32
fx_hi = fx['day_high'] if fx else '-'
fx_lo = fx['day_low'] if fx else '-'
fx_ts = fx['timestamp'] if fx else '-'

# Fertilizer
ferts = DB.execute("SELECT product, region, price, (price - LAG(price) OVER (PARTITION BY product, region ORDER BY timestamp)) as change FROM (SELECT product, region, price, timestamp, ROW_NUMBER() OVER (PARTITION BY product, region ORDER BY timestamp DESC) rn FROM fertilizer_prices) WHERE rn<=1").fetchall()

# Rail
rails = DB.execute("SELECT origin, destination, rate, (rate - LAG(rate) OVER (PARTITION BY origin, destination ORDER BY timestamp)) as change FROM (SELECT origin, destination, rate, timestamp, ROW_NUMBER() OVER (PARTITION BY origin, destination ORDER BY timestamp DESC) rn FROM rail_rates) WHERE rn<=1").fetchall()

# Port
ports = DB.execute("SELECT port_name, volume_tonnes, week_ending FROM (SELECT port_name, volume_tonnes, week_ending, ROW_NUMBER() OVER (PARTITION BY port_name ORDER BY week_ending DESC) rn FROM port_volumes) WHERE rn<=1").fetchall()

# Basis
basis_rows = DB.execute("SELECT region, futures_price, cash_price, basis FROM (SELECT region, futures_price, cash_price, basis, ROW_NUMBER() OVER (PARTITION BY region ORDER BY date DESC) rn FROM basis_data) WHERE rn<=1").fetchall()

# GDD
gdds = DB.execute("SELECT city, gdd, normal_gdd FROM (SELECT city, gdd, normal_gdd, ROW_NUMBER() OVER (PARTITION BY city ORDER BY date DESC) rn FROM gdd_data) WHERE rn<=1").fetchall()

# Charts — 30 day canola history
chart_html = ''
canola_hist = DB.execute("SELECT price, timestamp FROM commodity_prices WHERE commodity='canola' ORDER BY timestamp DESC LIMIT 30").fetchall()
if len(canola_hist) >= 2:
    vals = [r['price'] for r in reversed(canola_hist)]
    dates = [r['timestamp'][:10] for r in reversed(canola_hist)]
    mi, mx = min(vals), max(vals)
    rng = mx - mi or 10
    W, H = 600, 140
    pL, pR, pT, pB = 40, 10, 10, 22
    pw, ph = W-pL-pR, H-pT-pB
    s = '<svg viewBox="0 0 '+str(W)+' '+str(H)+'" style="width:100%;height:auto;max-height:160px;">'
    for i in range(3):
        y = pT + ph*(i/2)
        s += '<line x1="'+str(pL)+'" y1="'+str(int(y))+'" x2="'+str(W-pR)+'" y2="'+str(int(y))+'" stroke="var(--line)" stroke-width="0.5"/>'
    s += '<line x1="'+str(pL)+'" y1="'+str(H-pB)+'" x2="'+str(W-pR)+'" y2="'+str(H-pB)+'" stroke="var(--line)" stroke-width="1"/>'
    pts = []
    for i,v in enumerate(vals):
        x = pL + (pw*i/max(1,len(vals)-1))
        y = pT + ph - ((v-mi)/rng*ph)
        pts.append(str(int(x))+','+str(int(y)))
    s += '<polyline points="'+' '.join(pts)+'" fill="none" stroke="var(--sprout)" stroke-width="2"/>'
    for i,v in enumerate(vals):
        x = pL+(pw*i/max(1,len(vals)-1))
        y = pT+ph-((v-mi)/rng*ph)
        s += '<circle cx="'+str(int(x))+'" cy="'+str(int(y))+'" r="2.5" fill="var(--sprout)"/>'
    s += '<text x="'+str(int(pL+pw))+'" y="'+str(int(pT+ph-((vals[-1]-mi)/rng*ph))-6)+'" text-anchor="end" font-size="10" font-weight="600" fill="var(--sprout)">'+str(vals[-1])+'</text>'
    for i in [0, len(dates)-1]:
        x = pL+(pw*i/max(1,len(dates)-1))
        s += '<text x="'+str(int(x))+'" y="'+str(H-6)+'" text-anchor="middle" font-size="7" fill="var(--clay)">'+dates[i][-5:]+'</text>'
    s += '</svg>'
    chart_html = s

# Forecast — simple linear regression on last 14 days
forecast_html = ''
fcast_vals = [r['price'] for r in reversed(canola_hist[:14])]
if len(fcast_vals) >= 7:
    n = len(fcast_vals)
    x_mean = (n-1)/2; y_mean = sum(fcast_vals)/n
    num = sum((i-x_mean)*(y-y_mean) for i,y in enumerate(fcast_vals))
    den = sum((i-x_mean)**2 for i in range(n))
    slope = num/den if den else 0
    intercept = y_mean - slope*x_mean
    fcasts = [round(intercept+slope*(n+i),2) for i in range(7)]
    fhtml = ''.join('<div style="display:flex;justify-content:space-between;padding:4px 8px;font-size:0.75rem;border-bottom:1px solid var(--line);"><span>Day +'+str(i+1)+'</span><span class="val mono">$'+str(f)+'</span></div>' for i,f in enumerate(fcasts))
    trend = '↑' if slope>0 else '↓' if slope<0 else '→'
    cls = 'com-up' if slope>0 else 'com-down' if slope<0 else ''
    forecast_html = '<div style="margin-top:8px;font-size:0.625rem;color:var(--clay);margin-bottom:6px;">Linear regression on 14-day history <span class="'+cls+'">'+trend+'</span></div><div>'+fhtml+'</div>'

DB.close()

# === Build rows ===
commodity_order = ['canola','wheat','durum','barley','oats','corn','soy','lentils','flax','peas']
com_names = ['Canola','Wheat','Durum','Barley','Oats','Corn','Soy','Lentils','Flax','Peas']
com_cards = ''.join('<div class="com-card"><div class="com-label">'+n+'</div><div class="com-price">'+T(coms.get(k))+'<span class="com-unit">/t</span></div></div>\n' for n,k in zip(com_names,commodity_order))

fert_rows = ''.join('<tr><td>'+r['product']+'</td><td class="val">$'+T(r['price'])+'</td><td class="val"><span class="'+('com-up' if r['change'] and r['change']>0 else 'com-down' if r['change'] and r['change']<0 else '')+'">'+('+'+T(r['change']) if r['change'] else '—')+'</span></td><td>'+r['region']+'</td></tr>\n' for r in ferts)

rail_rows = ''.join('<tr><td>'+r['origin']+' → '+r['destination']+'</td><td class="val">$'+T(r['rate'])+'</td><td class="val"><span class="'+('com-up' if r['change'] and r['change']>0 else 'com-down' if r['change'] and r['change']<0 else '')+'">'+('+'+T(r['change']) if r['change'] else '—')+'</span></td></tr>\n' for r in rails)

port_rows = ''.join('<tr><td>'+r['port_name']+'</td><td class="val">'+T(int(r['volume_tonnes']) if r['volume_tonnes'] else '-')+' t</td><td>'+T(r['week_ending'])+'</td></tr>\n' for r in ports)

basis_table = ''.join('<tr><td>'+r['region']+'</td><td class="val">$'+T(r['futures_price'])+'</td><td class="val">$'+T(r['cash_price'])+'</td><td class="val '+('com-up' if r['basis'] and r['basis']>-3 else 'com-down' if r['basis'] and r['basis']<-10 else '')+'">$'+T(r['basis'])+'</td></tr>\n' for r in basis_rows)

gdd_table = ''.join('<tr><td>'+r['city']+'</td><td class="val">'+T(r['gdd'])+'</td><td class="val">'+T(r['normal_gdd'])+'</td><td class="val" style="color:var(--sprout);">+'+T(int(r['gdd']-r['normal_gdd']) if r['gdd'] and r['normal_gdd'] else '-')+' days</td></tr>\n' for r in gdds)

fx_chg = fx['rate'] - 1.315 if fx else 0
fx_cls = 'com-up' if fx_chg > 0 else 'com-down'

CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--soil:#3E2C1C;--wheat:#F5E6D0;--straw:#C4A882;--clay:#8B6914;--sprout:#4A7C3F;--amber:#E8A317;--rust:#B7410E;--line:#D4C4B0;--rad:8px}
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

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
"""+noindex+"""
<title>Field Data — Ag Market Dashboard | SQLite-Backed</title>
<meta name="description" content="Free live dashboard for Canadian agriculture. Grain prices, fertilizer, FX, rail, ports. 90-day history. SQLite-backed.">
<link rel="canonical" href="https://fielddata.co/">
<meta property="og:title" content="Field Data — Ag Market Dashboard">
<meta property="og:description" content="Grain, fertilizer, FX, rail. 90-day history. Free. Always.">
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
  <div style="text-align:center;padding:8px 18px;margin-bottom:18px;font-size:0.875rem;color:var(--clay);">Live grain, fertilizer, FX, rail & port data. 90-day history. SQLite-backed. Free.</div>

  <div class="grid">
    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Commodity Prices</span><span class="pill pill-live">Live</span></div>
      <div class="com-grid">"""+com_cards+"""</div>
      <div class="card-footer">ICE / CME &middot; """+now_iso[:16]+"""</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Fertilizer Index</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Product</th><th class="val">Price</th><th class="val">Change</th><th>Region</th></tr>"""+fert_rows+"""</table>
      <div class="card-footer">USDA / StatsCan &middot; """+now_iso[:16]+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Farm Diesel</span><span class="pill pill-live">Daily</span></div>
      <div style="font-size:2rem;font-weight:600;" class="nums">"""+T(fuel.get('AB'))+"""<span style="font-size:0.875rem;color:var(--clay);"> &cent;/L</span></div>
      <div style="font-size:0.75rem;color:var(--clay);">Alberta avg</div>
      <div class="card-footer">Public surveys</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">CAD / USD</span><span class="pill pill-live">Live</span></div>
      <div style="display:flex;align-items:baseline;gap:10px;">
        <span style="font-size:2.5rem;font-weight:600;">"""+T(fx_rate)+"""</span>
        <span style="font-size:0.875rem;" class=\""""+fx_cls+"""\">"""+('+' if fx_chg>0 else '')+T(round(fx_chg,4))+"""</span>
      </div>
      <div style="font-size:0.75rem;color:var(--clay);margin-top:4px;">H: """+T(fx_hi)+""" &middot; L: """+T(fx_lo)+"""</div>
      <div class="card-footer">Bank of Canada &middot; """+T(fx_ts)[:16]+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Canola Basis</span><span class="pill pill-live">Daily</span></div>
      <table><tr><th>Region</th><th class="val">Futures</th><th class="val">Cash</th><th class="val">Basis</th></tr>"""+basis_table+"""</table>
      <div class="card-footer">Futures minus cash &middot; Today</div>
    </div>

    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Canola — 30 Day Price History</span><span class="pill pill-live">Daily</span></div>
      """+chart_html+"""
      <div class="card-footer">From SQLite history archive</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Canola — 7 Day Forecast</span><span class="pill pill-live">Model</span></div>
      """+forecast_html+"""
      <div class="card-footer">Linear regression &middot; Informational only</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Growing Degree Days</span><span class="pill pill-live">Daily</span></div>
      <table><tr><th>City</th><th class="val">GDD</th><th class="val">Normal</th><th class="val">Ahead</th></tr>"""+gdd_table+"""</table>
      <div class="card-footer">Open-Meteo &middot; Today</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Rail Freight</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Route</th><th class="val">Rate/t</th><th class="val">Change</th></tr>"""+rail_rows+"""</table>
      <div class="card-footer">Ag Transport Coalition</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Grain Ports</span><span class="pill pill-live">Weekly</span></div>
      <table><tr><th>Port</th><th class="val">Volume</th><th class="val">Week</th></tr>"""+port_rows+"""</table>
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
  &copy; 2026 Field Data &middot; SQLite-backed &middot; Data from public sources &middot; Informational use only
</footer>
</body>
</html>"""

with open(OUT,'w') as f:
    f.write(html)

print("[%s] Built: %s (%s bytes)" % (MODE.upper(), OUT, len(html)))
