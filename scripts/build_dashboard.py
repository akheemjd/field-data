#!/usr/bin/env python3
"""Field Data — Ag market dashboard. Farmer-friendly. SQLite-backed."""
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

def T(s, dec=None): 
    if s is None: return '—'
    if dec is not None: return f"${s:,.{dec}f}" if isinstance(s,(int,float)) else str(s)
    return str(s) if not isinstance(s,float) else f"${s:,.2f}"

now_iso = datetime.utcnow().isoformat()[:16]

# === Commodities ===
coms = {}
for row in DB.execute("SELECT commodity, price FROM (SELECT commodity, price, ROW_NUMBER() OVER (PARTITION BY commodity ORDER BY timestamp DESC) rn FROM commodity_prices) WHERE rn=1"):
    coms[row['commodity']] = row['price']

# Commodity labels and friendly names
com_info = [
    ('canola','Canola','Canada\'s biggest crop. Used for cooking oil and biodiesel.'),
    ('wheat','Wheat','Milling wheat. Bread, pasta, export markets.'),
    ('durum','Durum','Premium wheat for pasta. Mostly exported.'),
    ('barley','Barley','Feed grain and malting. Beer and livestock.'),
    ('oats','Oats','Food and feed. Growing export demand.'),
    ('corn','Corn','Feed and ethanol. Mostly Ontario and Quebec.'),
    ('soy','Soybeans','Protein and oil. Strong demand from Asia.'),
    ('lentils','Lentils','Pulse crop. India is the biggest buyer.'),
    ('flax','Flax','Oilseed. Food-grade and industrial uses.'),
    ('peas','Field Peas','Protein crop. Growing market for plant-based food.'),
]

com_cards = ''
for key, name, desc in com_info:
    price = coms.get(key)
    val = f"${price:,.2f}" if isinstance(price,(int,float)) else '—'
    com_cards += '<div class="com-card"><div class="com-label">'+name+'</div><div class="com-sub">'+desc+'</div><div class="com-price">'+str(val)+'</div></div>\n'

# === Fertilizer ===
ferts = DB.execute("SELECT product, region, price, (price - LAG(price) OVER (PARTITION BY product, region ORDER BY timestamp)) as change FROM (SELECT product, region, price, timestamp, ROW_NUMBER() OVER (PARTITION BY product, region ORDER BY timestamp DESC) rn FROM fertilizer_prices) WHERE rn<=1").fetchall()

fert_names = {'Urea':'Urea 46-0-0','Potash':'Potash 0-0-60','DAP':'DAP 18-46-0','MAP':'MAP 11-52-0','Anhydrous':'NH3 82-0-0'}
fert_rows = ''
for r in ferts:
    name = fert_names.get(r['product'], r['product'])
    price = f"${r['price']:,.0f}" if r['price'] else '—'
    chg = r['change']
    arrow = '↑' if chg and chg>0 else '↓' if chg and chg<0 else '—'
    cls = 'com-up' if chg and chg>0 else 'com-down' if chg and chg<0 else ''
    chg_str = f"+${abs(chg):,.0f}" if chg and chg>0 else f"-${abs(chg):,.0f}" if chg and chg<0 else 'steady'
    fert_rows += f'<tr><td>{name}</td><td class="val">{price}/t</td><td class="val {cls}">{arrow} {chg_str}</td></tr>\n'

# === Fuel ===
fuel_row = DB.execute("SELECT price FROM fuel_prices WHERE province='AB' AND fuel_type='diesel' ORDER BY timestamp DESC LIMIT 1").fetchone()
fuel_p = fuel_row['price'] if fuel_row else 158.9

# === Exchange ===
fx = DB.execute("SELECT rate, day_high, day_low FROM exchange_rates ORDER BY timestamp DESC LIMIT 1").fetchone()
fx_rate = fx['rate'] if fx else 1.3215
fx_prev = DB.execute("SELECT rate FROM exchange_rates ORDER BY timestamp DESC LIMIT 1 OFFSET 1").fetchone()
fx_prev_rate = fx_prev['rate'] if fx_prev else fx_rate
fx_chg = fx_rate - fx_prev_rate
fx_cls = 'com-up' if fx_chg>0 else 'com-down'
fx_dir = 'up' if fx_chg>0 else 'down'

# === Chart ===
chart_html = ''
canola_hist = DB.execute("SELECT price, timestamp FROM commodity_prices WHERE commodity='canola' ORDER BY timestamp DESC LIMIT 30").fetchall()
if len(canola_hist) >= 2:
    vals = [r['price'] for r in reversed(canola_hist)]
    dates = [r['timestamp'][:10] for r in reversed(canola_hist)]
    mi, mx = min(vals), max(vals)
    rng = mx-mi or 10
    W,H, pL,pR,pT,pB = 580,130, 44,12,8,20
    pw,ph = W-pL-pR, H-pT-pB
    s = f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;max-height:150px;">'
    for i in range(3):
        y = int(pT+ph*(i/2))
        s += f'<line x1="{pL}" y1="{y}" x2="{W-pR}" y2="{y}" stroke="var(--line)" stroke-width="0.5"/>'
    s += f'<line x1="{pL}" y1="{H-pB}" x2="{W-pR}" y2="{H-pB}" stroke="var(--line)" stroke-width="1"/>'
    dots = ''
    for i,v in enumerate(vals):
        x = int(pL+pw*i/max(1,len(vals)-1))
        y = int(pT+ph-((v-mi)/rng*ph))
        dots += f' {x},{y}'
    s += f'<polyline points="{dots.strip()}" fill="var(--sprout)" fill-opacity="0.08" stroke="var(--sprout)" stroke-width="2.5" stroke-linejoin="round"/>'
    for i,v in enumerate(vals):
        if i%3==0 or i==len(vals)-1:
            x=int(pL+pw*i/max(1,len(vals)-1))
            y=int(pT+ph-((v-mi)/rng*ph))
            s+='<circle cx="'+str(x)+'" cy="'+str(y)+'" r="3" fill="var(--sprout)"/>'
    
    last_x = int(pL+pw); last_y = int(pT+ph-((vals[-1]-mi)/rng*ph))
    s += f'<text x="{last_x+2}" y="{last_y}" font-size="11" font-weight="700" fill="var(--sprout)">${vals[-1]:.2f}</text>'
    for i in [0, len(dates)-1]:
        x = int(pL+pw*i/max(1,len(dates)-1))
        s += f'<text x="{x}" y="{H-6}" text-anchor="middle" font-size="7" fill="var(--clay)">{dates[i][5:]}</text>'
    s += '</svg>'
    chart_html = s

# === Forecast ===
forecast_html = ''
if canola_hist and len(canola_hist) >= 7:
    fvals = [r['price'] for r in reversed(canola_hist[:14])]
    n = len(fvals)
    x_mean = (n-1)/2; y_mean = sum(fvals)/n
    num = sum((i-x_mean)*(y-y_mean) for i,y in enumerate(fvals))
    den = sum((i-x_mean)**2 for i in range(n))
    slope = num/den if den else 0
    intercept = y_mean-slope*x_mean
    fcasts = [round(intercept+slope*(n+i),2) for i in range(7)]
    trend = 'rising' if slope>0 else 'falling' if slope<0 else 'steady'
    trend_cls = 'com-up' if slope>0 else 'com-down' if slope<0 else ''
    fhtml = ''
    for i, f in enumerate(fcasts):
        diff = f-fvals[-1]
        label = ['Tomorrow','Day 2','Day 3','Day 4','Day 5','Day 6','Next week'][i]
        arrow = '↑' if diff>0 else '↓' if diff<0 else '→'
        fhtml += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 10px;font-size:0.875rem;border-bottom:1px solid var(--line);"><span>{label}</span><span style="display:flex;gap:8px;align-items:center;"><span class="val">${f:,.2f}</span><span class="{trend_cls}" style="font-size:0.75rem;">{arrow} ${abs(diff):.2f}</span></span></div>'
    forecast_html = f'<div style="margin-top:6px;font-size:0.75rem;color:var(--clay);margin-bottom:8px;">Based on the last 14 days, prices look like they\'re <span class="{trend_cls}">{trend}</span>.</div><div>{fhtml}</div>'

# === Basis ===
basis_data = DB.execute("SELECT region, futures_price, cash_price, basis FROM (SELECT region, futures_price, cash_price, basis, ROW_NUMBER() OVER (PARTITION BY region ORDER BY date DESC) rn FROM basis_data) WHERE rn<=1").fetchall()
basis_rows = ''
for r in basis_data:
    b = r['basis'] if r['basis'] is not None else 0
    if b > -5: cls = 'com-up'
    elif b > -12: cls = ''
    else: cls = 'com-down'
    basis_rows += '<tr><td>'+r['region']+'</td><td class="val">$'+'{:,.2f}'.format(r['futures_price'])+'</td><td class="val">$'+'{:,.2f}'.format(r['cash_price'])+'</td><td class="val '+cls+'">-$'+'{:,.2f}'.format(abs(b))+'</td></tr>\n'

# === GDD ===
gdds = DB.execute("SELECT city, gdd, normal_gdd FROM (SELECT city, gdd, normal_gdd, ROW_NUMBER() OVER (PARTITION BY city ORDER BY date DESC) rn FROM gdd_data) WHERE rn<=1").fetchall()
gdd_rows = ''
for g in gdds:
    ahead = int(g['gdd']-g['normal_gdd']) if g['gdd'] and g['normal_gdd'] else 0
    gdd_rows += f'<tr><td>{g["city"]}</td><td class="val">{g["gdd"]:,.0f}</td><td class="val">{g["normal_gdd"]:,.0f}</td><td class="val" style="color:var(--sprout);">+{ahead} days ahead</td></tr>\n'

# === Rail ===
rails = DB.execute("SELECT origin, destination, rate, (rate - LAG(rate) OVER (PARTITION BY origin, destination ORDER BY timestamp)) as change FROM (SELECT origin, destination, rate, timestamp, ROW_NUMBER() OVER (PARTITION BY origin, destination ORDER BY timestamp DESC) rn FROM rail_rates) WHERE rn<=1").fetchall()
rail_rows = ''
for r in rails:
    chg = r['change']
    arrow = '↑' if chg and chg>0 else '↓' if chg and chg<0 else '—'
    cls = 'com-up' if chg and chg>0 else 'com-down' if chg and chg<0 else ''
    chg_s = f'+${abs(chg):,.0f}' if chg and chg>0 else f'-${abs(chg):,.0f}' if chg and chg<0 else 'steady'
    rail_rows += f'<tr><td>{r["origin"]} → {r["destination"]}</td><td class="val">${r["rate"]:,.2f}/t</td><td class="val {cls}">{arrow} {chg_s}</td></tr>\n'

# === Ports ===
ports = DB.execute("SELECT port_name, volume_tonnes, week_ending FROM (SELECT port_name, volume_tonnes, week_ending, ROW_NUMBER() OVER (PARTITION BY port_name ORDER BY week_ending DESC) rn FROM port_volumes) WHERE rn<=1").fetchall()
port_rows = ''
for p in ports:
    v = int(p['volume_tonnes']) if p['volume_tonnes'] else 0
    week = p['week_ending'] or '—'
    port_rows += f'<tr><td>{p["port_name"]}</td><td class="val">{v:,} tonnes</td><td>{week}</td></tr>\n'

DB.close()

CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--soil:#3E2C1C;--wheat:#F5E6D0;--straw:#C4A882;--clay:#8B6914;--sprout:#4A7C3F;--amber:#E8A317;--rust:#B7410E;--line:#D4C4B0;--rad:8px}
body{background:var(--wheat);color:var(--soil);font-family:'Inter',-apple-system,sans-serif;font-size:0.9375rem;line-height:1.55;-webkit-font-smoothing:antialiased}
*{font-variant-numeric:tabular-nums}
.nums{font-family:'Barlow Condensed',sans-serif;font-weight:600}
.mono{font-family:'IBM Plex Mono',monospace}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--wheat)}::-webkit-scrollbar-thumb{background:var(--straw);border-radius:3px}
*{scrollbar-width:thin;scrollbar-color:var(--straw) var(--wheat)}
.banner{background:#FFF8F0;border-bottom:1px solid var(--line);padding:0 24px;display:flex;align-items:center;justify-content:center;height:60px;position:sticky;top:0;z-index:999}
.banner h1{font-size:0.8125rem;font-weight:700;color:var(--soil);font-family:'IBM Plex Mono',monospace}
nav{background:#FFF8F0;border-bottom:1px solid var(--line);padding:0 24px;display:flex;justify-content:center;gap:36px}
nav a{color:var(--clay);text-decoration:none;font-size:0.75rem;font-weight:500;padding:8px 0;border-bottom:2px solid transparent;transition:all .15s}
nav a:hover{border-color:var(--soil);color:var(--soil)}
.main{max-width:1200px;margin:0 auto;padding:20px 20px 40px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.module{background:#FFF8F0;border:1px solid var(--line);border-radius:var(--rad);padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.02)}
.module.hero{grid-column:span 12}.module.wide{grid-column:span 8}.module.standard{grid-column:span 4}
.eyebrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.eyebrow-label{font-size:0.6875rem;color:var(--soil);font-weight:600}
.pill{font-size:0.5625rem;padding:2px 8px;border-radius:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.pill-live{color:var(--sprout);background:rgba(74,124,63,.1)}
.card-footer{margin-top:10px;padding-top:6px;border-top:1px solid var(--line);font-size:0.625rem;color:var(--clay);font-family:'IBM Plex Mono',monospace}
.com-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
.com-card{background:var(--soil);color:var(--wheat);padding:16px;border-radius:6px}
.com-label{font-size:0.8125rem;font-weight:600}.com-sub{font-size:0.5625rem;color:var(--straw);text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px}
.com-price{font-size:1.5rem;line-height:1.15;font-family:'Barlow Condensed',sans-serif}

.com-up{color:var(--sprout)}.com-down{color:var(--rust)}
table{width:100%;border-collapse:collapse;font-size:0.8125rem}
th{text-align:left;padding:6px 10px;border-bottom:2px solid var(--line);font-size:0.625rem;text-transform:uppercase;letter-spacing:.06em;color:var(--clay);font-weight:600}
td{padding:7px 10px;border-bottom:1px solid var(--line)}
.val{font-family:'IBM Plex Mono',monospace;text-align:right;font-weight:500}
@media(max-width:900px){.module{grid-column:span 12!important}.main{padding:12px 12px 32px}.com-price{font-size:1.25rem}.com-grid{grid-template-columns:repeat(auto-fill,minmax(130px,1fr))}}
"""

noindex = '<meta name="robots" content="noindex">' if STAGING else ''
badge = '<div style="position:fixed;bottom:8px;right:8px;background:var(--amber);color:#fff;padding:4px 8px;border-radius:4px;font-size:0.625rem;font-weight:600;z-index:9999;">STAGING</div>' if STAGING else ''

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
"""+noindex+"""
<title>Field Data — Free Ag Market Prices for Canadian Farmers</title>
<meta name="description" content="Free grain prices, fertilizer costs, diesel, and rail rates. Built for Canadian farmers. Updated live. No signup.">
<link rel="canonical" href="https://fielddata.co/">
<meta property="og:title" content="Field Data — Grain Prices for Canadian Farmers">
<meta property="og:description" content="Canola, wheat, fertilizer, diesel. Live and free.">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>"""+CSS+"""</style>
</head>
<body>
"""+badge+"""

<div class="banner"><h1>FIELD DATA</h1></div>
<nav><a href="#">Today's Prices</a><a href="#">Weekly Report</a><a href="#">About</a></nav>

<div class="main">
  <div style="text-align:center;padding:6px 18px;margin-bottom:18px;font-size:0.9375rem;color:var(--clay);">Canadian grain markets &middot; Updated live</div>

  <div class="grid">
    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Grain Prices</span><span class="pill pill-live">Today</span></div>
      <div class="com-grid">"""+com_cards+"""</div>
      <div class="card-footer">Prices in Canadian dollars per tonne &middot; """+now_iso+"""</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Fertilizer</span></div>
      <table><tr><th>Product</th><th class="val">Price</th><th class="val">Change</th></tr>"""+fert_rows+"""</table>
      <div class="card-footer">Prairie farm supply prices &middot; """+now_iso+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Diesel</span></div>
      <div style="font-size:2.25rem;font-weight:600;line-height:1;" class="nums">"""+T(fuel_p)+"""<span style="font-size:1rem;color:var(--clay);"> ¢/L</span></div>
      <div style="font-size:0.875rem;color:var(--clay);margin-top:4px;">Alberta farm price</div>
      <div style="margin-top:12px;font-size:0.8125rem;color:var(--soil);"><div style="font-size:0.8125rem;color:var(--clay);margin-top:4px;">Alberta rack price. Provincial rates vary.</div>
      <div class="card-footer">""" + now_iso + """</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">CAD / USD</span></div>
      <div style="display:flex;align-items:baseline;gap:10px;">
        <span style="font-size:2.25rem;font-weight:600;">"""+T(fx_rate)+"""</span>
        <span style="font-size:0.9375rem;" class=\""""+fx_cls+"""\">"""+fx_dir+""" """+T(abs(fx_chg),4)+"""</span>
      </div>
      <div style="font-size:0.875rem;color:var(--clay);margin-top:4px;">Cross-border grain sales and input costs.</div>
      <div class="card-footer">Bank of Canada &middot; """+now_iso+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Canola Basis</span></div>
      
      <table><tr><th>Region</th><th class="val">Futures</th><th class="val">Cash</th><th class="val">Basis</th></tr>"""+basis_rows+"""</table>
      <div class="card-footer">Futures minus cash &middot; Canola</div>
    </div>

    <div class="module hero">
      <div class="eyebrow"><span class="eyebrow-label">Canola Price History</span></div>
      """+chart_html+"""
      <div class="card-footer">Closing prices, Canadian dollars per tonne</div>
    </div>



    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Crop Development</span></div>
      
      <table><tr><th>City</th><th class="val">This Year</th><th class="val">Normal</th><th class="val">Progress</th></tr>"""+gdd_rows+"""</table>
      <div class="card-footer">Base 5°C &middot; """+now_iso+"""</div>
    </div>

    <div class="module wide">
      <div class="eyebrow"><span class="eyebrow-label">Grain Freight</span></div>
      <table><tr><th>Route</th><th class="val">Rate</th><th class="val">Change</th></tr>"""+rail_rows+"""</table>
      <div class="card-footer">Grain rates per tonne &middot; """+now_iso+"""</div>
    </div>

    <div class="module standard">
      <div class="eyebrow"><span class="eyebrow-label">Export Volumes</span></div>
      <table><tr><th>Port</th><th class="val">Volume</th><th class="val">Week</th></tr>"""+port_rows+"""</table>
      <div class="card-footer">Weekly grain shipments</div>
    </div>
  </div>
</div>

<div style="text-align:center;max-width:480px;margin:32px auto 0;padding:28px;background:#FFF8F0;border:1px solid var(--line);border-radius:var(--rad);">
  <div style="font-size:0.75rem;color:var(--clay);margin-bottom:10px;">📬 Forward this to another farmer</div>
  <div style="font-size:1rem;font-weight:600;color:var(--soil);margin-bottom:4px;">Get the Weekly Grain Report</div>
  <div style="font-size:0.8125rem;color:var(--clay);margin-bottom:18px;">Prices, trends, and what it means for your operation. Every Wednesday morning.</div>
</div>

<footer style="padding:16px 24px;text-align:center;font-size:0.625rem;color:var(--clay);border-top:1px solid var(--line);font-family:'IBM Plex Mono',monospace;">
  Field Data &middot; Market data for Canadian agriculture &middot; Prices from public exchanges
</footer>
</body>
</html>"""

with open(OUT,'w') as f:
    f.write(html)

print("[%s] Built: %s (%s bytes)" % (MODE.upper(), OUT, len(html)))
