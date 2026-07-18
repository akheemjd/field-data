#!/usr/bin/env python3
"""Initialize Field Data database and seed with sample data."""
import sqlite3, os, random, json
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser('~/grain-data-dashboard/data/fielddata.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    with open(os.path.join(os.path.dirname(__file__), '..', 'schema.sql')) as f:
        conn.executescript(f.read())

    # Seed commodity prices — 90 days of history
    base = {'canola':615,'wheat':285,'durum':315,'barley':235,'oats':180,'corn':190,'soy':440,'lentils':770,'flax':600,'peas':400}
    conn.executemany(
        "INSERT OR IGNORE INTO commodity_prices (commodity, exchange, price, previous_close, day_high, day_low, timestamp) VALUES (?,?,?,?,?,?,?)",
        [(c,'ICE',base[c]+random.uniform(-10,10),base[c]+random.uniform(-8,8),base[c]+random.uniform(5,15),base[c]+random.uniform(-15,-5),(datetime.utcnow()-timedelta(days=d)).isoformat())
         for c in base for d in range(1,91)]
    )

    # Seed fuel prices — 30 days
    provinces = {'BC':178.5,'AB':158.9,'SK':162.3,'MB':164.1,'ON':170.2,'QC':172.8,'NB':174.5,'NS':175.2,'PE':176.0,'NL':179.3}
    conn.executemany(
        "INSERT OR IGNORE INTO fuel_prices (province, fuel_type, price, trend, timestamp) VALUES (?,?,?,?,?)",
        [(p,'diesel',v+random.uniform(-3,3),'--',(datetime.utcnow()-timedelta(days=d)).isoformat())
         for p,v in provinces.items() for d in range(1,31)]
    )

    # Exchange rates — 90 days
    conn.executemany(
        "INSERT OR IGNORE INTO exchange_rates (rate, day_high, day_low, timestamp) VALUES (?,?,?,?)",
        [(1.3215+random.uniform(-0.02,0.02),1.3240,1.3190,(datetime.utcnow()-timedelta(days=d)).isoformat()) for d in range(1,91)]
    )

    # Fertilizer — 8 weekly samples
    fert = [('Urea','Prairies',585),('Potash','SK',425),('DAP','Prairies',720),('MAP','Prairies',695),('Anhydrous','MB',890)]
    conn.executemany(
        "INSERT OR IGNORE INTO fertilizer_prices (product, region, price, timestamp) VALUES (?,?,?,?)",
        [(f[0],f[1],f[2]+random.uniform(-15,15),(datetime.utcnow()-timedelta(weeks=w)).isoformat()) for f in fert for w in range(1,9)]
    )

    # Rail rates
    routes = [('Regina','Vancouver',42.50,'CP'),('Saskatoon','Churchill',38.25,'CN'),('Winnipeg','Thunder Bay',35.00,'CN'),('Calgary','Vancouver',28.75,'CP'),('Edmonton','Prince Rupert',32.00,'CN')]
    conn.executemany(
        "INSERT OR IGNORE INTO rail_rates (origin, destination, rate, carrier, timestamp) VALUES (?,?,?,?,?)",
        [(r[0],r[1],r[2]+random.uniform(-2,2),r[3],(datetime.utcnow()-timedelta(weeks=w)).isoformat()) for r in routes for w in range(1,9)]
    )

    # Port volumes
    ports = [('Vancouver','canola',142000),('Prince Rupert','wheat',89000),('Montreal','canola',67000),('Thunder Bay','wheat',118000)]
    conn.executemany(
        "INSERT OR IGNORE INTO port_volumes (port_name, grain_type, volume_tonnes, week_ending, timestamp) VALUES (?,?,?,?,?)",
        [(p[0],p[1],int(p[2]+random.uniform(-10000,10000)),(datetime.utcnow()-timedelta(weeks=w)).date().isoformat(),(datetime.utcnow()-timedelta(weeks=w)).isoformat()) for p in ports for w in range(1,9)]
    )

    # GDD
    cities = [('Saskatoon',1185,1120),('Regina',1210,1155),('Winnipeg',1260,1190),('Brandon',1140,1080),('Edmonton',980,950),('Lethbridge',1320,1250),('Swift Current',1150,1100),('Prince Albert',1050,1010)]
    conn.executemany(
        "INSERT OR IGNORE INTO gdd_data (city, gdd, normal_gdd, date, timestamp) VALUES (?,?,?,?,?)",
        [(c[0],c[1]+random.uniform(-20,20),c[2],(datetime.utcnow()-timedelta(days=d)).date().isoformat(),(datetime.utcnow()-timedelta(days=d)).isoformat()) for c in cities for d in range(1,31)]
    )

    # Basis
    regions = [('Central SK',642.50,638.00),('Southern AB',642.50,636.75),('SW Manitoba',642.50,640.25),('Peace Region',642.50,622.00),('Northern SK',642.50,632.50),('Eastern MB',642.50,639.00)]
    conn.executemany(
        "INSERT OR IGNORE INTO basis_data (region, futures_price, cash_price, date, timestamp) VALUES (?,?,?,?,?)",
        [(r[0],r[1]+random.uniform(-5,5),r[2]+random.uniform(-5,5),(datetime.utcnow()-timedelta(days=d)).date().isoformat(),(datetime.utcnow()-timedelta(days=d)).isoformat()) for r in regions for d in range(1,31)]
    )

    # Collection health
    sources = ['commodity_prices','fuel_prices','exchange_rates','fertilizer_prices','rail_rates','port_volumes','gdd_data','basis_data']
    conn.executemany(
        "INSERT OR IGNORE INTO collection_health (source, last_success, consecutive_failures) VALUES (?,?,0)",
        [(s, datetime.utcnow().isoformat()) for s in sources]
    )

    conn.commit()
    rows = conn.execute("SELECT COUNT(*) FROM commodity_prices").fetchone()[0]
    print(f"Database initialized: {rows} commodity price rows across 90 days")
    print(f"  Tables: {', '.join(s for s in sources)}")
    conn.close()

if __name__ == '__main__':
    init_db()
