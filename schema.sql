-- Field Data Database Schema
-- SQLite. Single file. Zero infrastructure.

-- Commodity prices (daily close)
CREATE TABLE IF NOT EXISTS commodity_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity TEXT NOT NULL,    -- canola, wheat, durum, barley, oats, corn, soy, lentils, flax, peas
    exchange TEXT NOT NULL,     -- ICE, CME
    contract TEXT,              -- NOV26, DEC26
    price REAL NOT NULL,        -- CAD per tonne
    previous_close REAL,
    day_high REAL,
    day_low REAL,
    volume INTEGER,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(commodity, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_cp_commodity_date ON commodity_prices(commodity, timestamp);

-- Provincial fuel prices
CREATE TABLE IF NOT EXISTS fuel_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,     -- BC, AB, SK, MB, ON, QC, NB, NS, PE, NL
    fuel_type TEXT NOT NULL,    -- diesel, gasoline
    price REAL NOT NULL,
    trend TEXT,                 -- up, down, stable
    source TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(province, fuel_type, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_fuel_province_date ON fuel_prices(province, fuel_type, timestamp);

-- Exchange rates (CAD/USD)
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair TEXT NOT NULL DEFAULT 'CAD/USD',
    rate REAL NOT NULL,
    day_high REAL,
    day_low REAL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fx_date ON exchange_rates(timestamp);

-- Fertilizer prices
CREATE TABLE IF NOT EXISTS fertilizer_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,      -- urea, potash, DAP, MAP, anhydrous
    region TEXT NOT NULL,       -- Prairies, SK, MB, AB
    price REAL NOT NULL,
    unit TEXT DEFAULT '/t',
    previous_price REAL,
    source TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(product, region, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_fert_product_date ON fertilizer_prices(product, region, timestamp);

-- Rail freight rates
CREATE TABLE IF NOT EXISTS rail_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    rate REAL NOT NULL,         -- CAD per tonne
    previous_rate REAL,
    carrier TEXT,               -- CN, CP
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(origin, destination, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_rail_route_date ON rail_rates(origin, destination, timestamp);

-- Port grain volumes
CREATE TABLE IF NOT EXISTS port_volumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    port_name TEXT NOT NULL,    -- Vancouver, Prince Rupert, Montreal, Thunder Bay
    volume_tonnes REAL,
    grain_type TEXT,            -- wheat, canola, durum, pulses
    week_ending TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(port_name, grain_type, week_ending)
);

CREATE INDEX IF NOT EXISTS idx_port_date ON port_volumes(port_name, week_ending);

-- Growing degree days
CREATE TABLE IF NOT EXISTS gdd_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    gdd REAL NOT NULL,
    normal_gdd REAL NOT NULL,
    date TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(city, date)
);

CREATE INDEX IF NOT EXISTS idx_gdd_city_date ON gdd_data(city, date);

-- Basis data (futures minus cash by region)
CREATE TABLE IF NOT EXISTS basis_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT NOT NULL,
    commodity TEXT NOT NULL DEFAULT 'canola',
    futures_price REAL NOT NULL,
    cash_price REAL NOT NULL,
    basis REAL,
    date TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(region, commodity, date)
);

CREATE INDEX IF NOT EXISTS idx_basis_region_date ON basis_data(region, commodity, date);

-- Collection health tracking
CREATE TABLE IF NOT EXISTS collection_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,       -- commodity_prices, fuel_prices, exchange_rates, etc.
    last_success TEXT,
    last_attempt TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_health_source ON collection_health(source);
