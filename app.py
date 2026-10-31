#!/usr/bin/env python3
"""
Pivot Boss CPR Terminal - Inside Value Compression Engine
Dedicated Institutional 2-Day Pivot Range Compression & Breakout Engine
Based on Frank Ochoa's "Secrets of a Pivot Boss" Master Framework.

Markets:
- 🪙 Binance Crypto (700+ Liquid Pairs via Official Spot API)
- 🔵 Coinbase Crypto (400+ Pairs via Official Exchange API)
- 🇮🇳 Indian Equities (NSE F&O / Top 100)
- 🇺🇸 US Russell 2000 (Small-Caps & Growth Leaders)

Timeframes:
- ⚡ Daily CPR (Developing & Active)
- 🗓️ Monthly CPR (Developing & Active)
- 📊 Quarterly CPR (Developing & Active)
"""

import os
import time
import json
import datetime
import threading
import requests
import urllib.parse
from urllib3.util import connection
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

WATCHLISTS = {
    "india_all": {
        "name": "🇮🇳 Indian Equities & Indices (NSE F&O / Top 100)",
        "symbols": [
            "^NSEI", "^NSEBANK", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "INFY.NS", "TCS.NS", "LT.NS", "SBIN.NS", "BHARTIARTL.NS",
            "AXISBANK.NS", "KOTAKBANK.NS", "ITC.NS", "HINDUNILVR.NS", "TATAMOTORS.NS",
            "M&M.NS", "SUNPHARMA.NS", "BAJFINANCE.NS", "MARUTI.NS", "TITAN.NS",
            "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "ADANIPORTS.NS",
            "COALINDIA.NS", "ONGC.NS", "JSWSTEEL.NS", "BAJAJFINSV.NS", "TECHM.NS",
            "HCLTECH.NS", "WIPRO.NS", "DRREDDY.NS", "CIPLA.NS", "ULTRACEMCO.NS",
            "GRASIM.NS", "NESTLEIND.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "DIVISLAB.NS",
            "APOLLOHOSP.NS", "HINDALCO.NS", "BPCL.NS", "BRITANNIA.NS", "ASIANPAINT.NS",
            "BEL.NS", "TRENT.NS", "SHRIRAMFIN.NS", "HAL.NS", "ZOMATO.NS",
            "INDUSINDBK.NS", "PNB.NS", "BANKBARODA.NS", "AUBANK.NS", "FEDERALBNK.NS",
            "IDFCFIRSTB.NS", "BANDHANBNK.NS", "VEDL.NS", "JINDALSTEL.NS", "NMDC.NS",
            "SAIL.NS", "TATACOMM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS",
            "LTIM.NS", "DIXON.NS", "POLYCAB.NS", "HAVELLS.NS", "VOLTAS.NS",
            "AUROPHARMA.NS", "LUPIN.NS", "BIOCON.NS", "TORNTPHARM.NS", "ALKEM.NS",
            "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS",
            "PFC.NS", "RECLTD.NS", "CANBK.NS", "UNIONBANK.NS", "IOC.NS",
            "GAIL.NS", "PETRONET.NS", "TATAPOWER.NS", "ADANIGREEN.NS", "SIEMENS.NS",
            "ABB.NS", "CUMMINSIND.NS", "INDIGO.NS", "IRCTC.NS", "JUBLFOOD.NS",
            "BOSCHLTD.NS", "COLPAL.NS", "DABUR.NS", "MARICO.NS", "PIDILITIND.NS",
            "LALPATHLAB.NS", "MOTHERSON.NS"
        ]
    },
    "us_russell2000": {
        "name": "🇺🇸 US Russell 2000 (Small-Caps & Growth Leaders)",
        "symbols": [
            "IWM", "TNA", "TZA", "RKLB", "AFRM", "UPST", "SOFI", "CVNA", "HOOD", "IONQ", "ASTS",
            "HIMS", "SNDX", "MARA", "RIOT", "CLSK", "HUT", "BITF", "AXSM", "INSM", "VRT",
            "POWI", "SAIA", "BOOT", "MEDP", "BLD", "FIX", "FTAI", "SYM", "CRDO", "ALAB",
            "TEM", "ROOT", "KTOS", "POWL", "LUMN", "CAVA", "WING", "SHAK", "BROS", "BLMN",
            "TXRH", "RXRX", "DNA", "RGTI", "QUBT", "JOBY", "ACHR", "CELH", "ELF", "DUOL", "APP",
            "CHPT", "PLUG", "RUN", "ENPH", "SEDG", "NOVA", "BE", "STEM", "QS", "LCID",
            "RIVN", "DKNG", "PENN", "WYNN", "CROX", "DECK", "ONON",
            "SKX", "ANF", "AEO", "GPS", "URBN", "GAP", "CPNG", "PATH", "AI", "BBAI",
            "SOUN", "SMCI", "MSTR", "VRNA", "MDGL", "KROS", "KRYS", "PCVX", "ADMA"
        ]
    },
    "crypto_all": {
        "name": "🪙 Binance Crypto (700+ Liquid Pairs)",
        "symbols": []
    },
    "crypto_coinbase": {
        "name": "🔵 Coinbase Crypto (400+ Pairs)",
        "symbols": []
    }
}

class BinanceAPIManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=60, pool_maxsize=60, max_retries=1)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self._init_dns()
        self.ticker_cache = []
        self.ticker_time = 0
        self.bars_cache = {}

    def _init_dns(self):
        def resolve_doh(domain):
            try:
                r = requests.get(f'https://1.1.1.1/dns-query?name={domain}&type=A', headers={'accept': 'application/dns-json'}, timeout=4)
                return [ans['data'] for ans in r.json().get('Answer', []) if '.' in ans.get('data', '') and not ans.get('data', '').endswith('.net.')]
            except Exception:
                return []

        self.dns_cache = {
            'api.binance.com': resolve_doh('api.binance.com'),
            'data-api.binance.vision': resolve_doh('data-api.binance.vision'),
            'api.exchange.coinbase.com': resolve_doh('api.exchange.coinbase.com'),
            'api.coinbase.com': resolve_doh('api.coinbase.com')
        }
        _orig = connection.create_connection
        dns_map = self.dns_cache
        def patched(addr, *args, **kwargs):
            h, p = addr
            if h in dns_map and dns_map[h]:
                return _orig((dns_map[h][0], p), *args, **kwargs)
            return _orig(addr, *args, **kwargs)
        connection.create_connection = patched

    def get_binance_symbols(self, min_quote_vol=0, max_coins=800):
        now = time.time()
        if self.ticker_cache and isinstance(self.ticker_cache, list) and (now - self.ticker_time < 60):
            tickers = self.ticker_cache
        else:
            tickers = []
            try:
                r = self.session.get("https://data-api.binance.vision/api/v3/ticker/24hr", timeout=5)
                data = r.json()
                if isinstance(data, list):
                    tickers = data
                    self.ticker_cache = tickers
                    self.ticker_time = now
            except Exception:
                pass

            if not tickers:
                try:
                    r = self.session.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
                    data = r.json()
                    if isinstance(data, list):
                        tickers = data
                        self.ticker_cache = tickers
                        self.ticker_time = now
                except Exception:
                    pass

        symbols = []
        stables_junk = {
            'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'USDPUSDT', 'EURUSDT', 'BUSDUSDT', 'AEURUSDT', 'DAIUSDT',
            'RLUSDUSDT', 'UUSDT', 'USD1USDT', 'BFUSDUSDT', 'RWUSDUSDT', 'XUSDUSDT', 'USDEUSDT', 'PYUSDUSDT',
            'PAXGUSDT', 'XAUTUSDT', 'USDYUSDT', 'STETHUSDT', 'WBTCUSDT', 'WETHUSDT', 'USDDUSDT', 'FRAXUSDT',
            'LUSDUSDT', 'GUSDUSDT', 'EURIUSDT', 'USDSUSDT'
        }
        if isinstance(tickers, list):
            for t in tickers:
                if not isinstance(t, dict): continue
                sym = t.get("symbol", "")
                if not sym.endswith("USDT") or sym in stables_junk:
                    continue
                # Exclude leveraged tokens and synthetic tokens
                if "UPUSDT" in sym or "DOWNUSDT" in sym or "BULLUSDT" in sym or "BEARUSDT" in sym:
                    continue
                if sym.endswith("BUSDT") and len(sym) > 8:
                    continue
                base = sym.replace("USDT", "")
                if not base.isascii() or not base.isalnum():
                    continue

                # Exclude dead/delisted symbols with zero bid/ask
                bid = float(t.get("bidPrice", 0) or 0)
                ask = float(t.get("askPrice", 0) or 0)
                if bid == 0 and ask == 0:
                    continue

                q_vol = float(t.get("quoteVolume", 0) or 0)
                price = float(t.get("lastPrice", 0) or 0)
                if q_vol >= min_quote_vol and price > 0:
                    symbols.append((sym, q_vol))
        
        symbols.sort(key=lambda x: x[1], reverse=True)
        priority = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "PEPEUSDT", "LINKUSDT", "LTCUSDT"]
        sym_list = [s[0] for s in symbols]
        sorted_symbols = [p for p in priority if p in sym_list] + [s for s in sym_list if s not in priority]
        return sorted_symbols[:max_coins]

    def fetch_market_bars(self, symbol):
        sym = symbol.replace("-USD", "USDT").replace(".NS", "").replace("^", "")
        if not sym.endswith("USDT") and not sym.endswith("USDC"):
            sym = sym + "USDT"

        now = time.time()
        if sym in self.bars_cache:
            ts, m_bars, d_bars = self.bars_cache[sym]
            if now - ts < 60:
                return m_bars, d_bars

        # Daily bars
        d_raw = []
        try:
            r_d = self.session.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1d&limit=45", timeout=4)
            data = r_d.json()
            if isinstance(data, list):
                d_raw = data
        except Exception:
            pass

        if not d_raw:
            try:
                r_d = self.session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&limit=45", timeout=4)
                data = r_d.json()
                if isinstance(data, list):
                    d_raw = data
            except Exception:
                d_raw = []

        if not isinstance(d_raw, list) or len(d_raw) < 5:
            return [], []

        daily_candles = []
        for b in d_raw:
            dt = datetime.datetime.fromtimestamp(b[0] / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
            daily_candles.append({
                "date": dt,
                "time": int(b[0] / 1000),
                "open": float(b[1]),
                "high": float(b[2]),
                "low": float(b[3]),
                "close": float(b[4]),
                "volume": float(b[5])
            })

        # Monthly bars
        m_raw = []
        try:
            r_m = self.session.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1M&limit=12", timeout=4)
            data = r_m.json()
            if isinstance(data, list):
                m_raw = data
        except Exception:
            pass

        if not m_raw:
            try:
                r_m = self.session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1M&limit=12", timeout=4)
                data = r_m.json()
                if isinstance(data, list):
                    m_raw = data
            except Exception:
                m_raw = []

        monthly_bars = []
        if isinstance(m_raw, list):
            for b in m_raw:
                dt = datetime.datetime.fromtimestamp(b[0] / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
                monthly_bars.append({
                    "date": dt,
                    "month": dt[:7],
                    "time": int(b[0] / 1000),
                    "open": float(b[1]),
                    "high": float(b[2]),
                    "low": float(b[3]),
                    "close": float(b[4]),
                    "volume": float(b[5])
                })

        self.bars_cache[sym] = (now, monthly_bars, daily_candles)
        return monthly_bars, daily_candles

    def format_usd(self, val):
        if val is None or val <= 0:
            return None
        if val >= 1_000_000_000:
            return f"${val / 1_000_000_000:.2f}B"
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        if val >= 1_000:
            return f"${val / 1_000:.0f}K"
        return f"${val:.1f}"

    def get_spot_volume(self, symbol):
        sym = symbol.replace("-USD", "USDT").replace(".NS", "").replace("^", "")
        if not sym.endswith("USDT"):
            sym = sym + "USDT"
        now = time.time()
        if not self.ticker_cache or not isinstance(self.ticker_cache, list) or (now - self.ticker_time >= 60):
            try:
                r = self.session.get("https://data-api.binance.vision/api/v3/ticker/24hr", timeout=5)
                tickers = r.json()
                if isinstance(tickers, list):
                    self.ticker_cache = tickers
                    self.ticker_time = now
            except Exception:
                try:
                    r = self.session.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
                    tickers = r.json()
                    if isinstance(tickers, list):
                        self.ticker_cache = tickers
                        self.ticker_time = now
                except Exception:
                    pass
        if isinstance(self.ticker_cache, list):
            for t in self.ticker_cache:
                if isinstance(t, dict) and t.get("symbol") == sym:
                    return float(t.get("quoteVolume", 0) or 0)
        return 0.0

BINANCE_MGR = BinanceAPIManager()

class CoinbaseAPIManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=60, pool_maxsize=60, max_retries=1)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.ticker_cache = []
        self.ticker_time = 0
        self.vol_cache = {}
        self.price_cache = {}
        self.bars_cache = {}

    def get_coinbase_symbols(self, min_quote_vol=0, max_coins=800):
        now = time.time()
        if self.ticker_cache and (now - self.ticker_time < 60):
            filtered = [s for s, v in self.ticker_cache if v >= min_quote_vol]
            return filtered[:max_coins]

        prod_list = []
        try:
            r = self.session.get("https://api.exchange.coinbase.com/products", timeout=5)
            if r.status_code == 200:
                prod_list = r.json()
        except Exception:
            pass

        vol_map = {}
        try:
            r_vol = self.session.get("https://api.exchange.coinbase.com/products/volume-summary", timeout=5)
            if r_vol.status_code == 200:
                vol_data = r_vol.json()
                if isinstance(vol_data, list):
                    vol_map = {v.get("id"): float(v.get("spot_volume_24hour") or 0) for v in vol_data if isinstance(v, dict)}
        except Exception:
            pass

        price_map = {}
        try:
            r_rates = self.session.get("https://api.coinbase.com/v2/exchange-rates?currency=USD", timeout=5)
            if r_rates.status_code == 200:
                rates = r_rates.json().get("data", {}).get("rates", {})
                for base, rate_str in rates.items():
                    try:
                        r_val = float(rate_str)
                        if r_val > 0:
                            price_map[base] = 1.0 / r_val
                    except Exception:
                        pass
        except Exception:
            pass

        stables_junk = {
            "USDC-USD", "USDT-USD", "USD-USDT", "USD-USDC", "EUR-USD", "USDC-USDT",
            "USDT-USDC", "EURC-EUR", "PYUSD-USD", "DAI-USD", "FDUSD-USD", "USD1-USD",
            "RLUSD-USD", "USDD-USD", "GUSD-USD", "PAXG-USD", "WAXL-USD", "WBTC-USD", "WETH-USD"
        }

        symbols_with_vol = []
        if isinstance(prod_list, list):
            for p in prod_list:
                if not isinstance(p, dict):
                    continue
                pid = p.get("id", "")
                quote = p.get("quote_currency", "")
                base = p.get("base_currency", "")
                if quote in ["USD", "USDC", "USDT"] and pid not in stables_junk and p.get("status") == "online":
                    base_vol = vol_map.get(pid, 0.0)
                    price = price_map.get(base, 0.0)
                    usd_vol = base_vol * price
                    self.vol_cache[pid] = usd_vol
                    if price > 0:
                        self.price_cache[pid] = price
                    symbols_with_vol.append((pid, usd_vol))

        symbols_with_vol.sort(key=lambda x: x[1], reverse=True)
        self.ticker_cache = symbols_with_vol
        self.ticker_time = now

        priority = [
            "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "ADA-USD",
            "AVAX-USD", "SUI-USD", "NEAR-USD", "PEPE-USD", "LINK-USD", "LTC-USD",
            "HYPE-USD", "UNI-USD", "BCH-USD", "AAVE-USD", "DOT-USD"
        ]
        sym_list = [s[0] for s in symbols_with_vol if s[1] >= min_quote_vol]
        sorted_symbols = [p for p in priority if p in sym_list] + [s for s in sym_list if s not in priority]
        return sorted_symbols[:max_coins]

    def fetch_market_bars(self, symbol):
        sym = symbol.replace("USDT", "-USD").replace("USDC", "-USD").replace(".NS", "").replace("^", "")
        if not sym.endswith("-USD"):
            sym = sym + "-USD"

        now = time.time()
        if sym in self.bars_cache:
            ts, m_bars, d_bars = self.bars_cache[sym]
            if now - ts < 60:
                return m_bars, d_bars

        raw_candles = []
        try:
            r = self.session.get(f"https://api.exchange.coinbase.com/products/{sym}/candles?granularity=86400", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) >= 5:
                    raw_candles = data
        except Exception:
            pass

        if not raw_candles:
            try:
                r = self.session.get(f"https://api.coinbase.com/api/v3/brokerage/market/products/{sym}/candles?granularity=ONE_DAY", timeout=4)
                if r.status_code == 200:
                    data = r.json()
                    c_list = data.get("candles", [])
                    if isinstance(c_list, list) and len(c_list) >= 5:
                        raw_candles = [
                            [int(c["start"]), float(c["low"]), float(c["high"]), float(c["open"]), float(c["close"]), float(c["volume"])]
                            for c in c_list if "start" in c
                        ]
            except Exception:
                pass

        if not raw_candles or len(raw_candles) < 5:
            return [], []

        raw_candles.sort(key=lambda x: x[0])

        daily_candles = []
        for c in raw_candles:
            dt = datetime.datetime.fromtimestamp(c[0], tz=datetime.timezone.utc).strftime("%Y-%m-%d")
            daily_candles.append({
                "date": dt,
                "time": int(c[0]),
                "open": float(c[3]),
                "high": float(c[2]),
                "low": float(c[1]),
                "close": float(c[4]),
                "volume": float(c[5])
            })

        monthly_dict = {}
        for c in daily_candles:
            mo_key = c['date'][:7]
            if mo_key not in monthly_dict:
                monthly_dict[mo_key] = {
                    'month': mo_key,
                    'date': c['date'],
                    'time': c['time'],
                    'open': c['open'],
                    'high': c['high'],
                    'low': c['low'],
                    'close': c['close'],
                    'volume': c['volume']
                }
            else:
                monthly_dict[mo_key]['high'] = max(monthly_dict[mo_key]['high'], c['high'])
                monthly_dict[mo_key]['low'] = min(monthly_dict[mo_key]['low'], c['low'])
                monthly_dict[mo_key]['close'] = c['close']
                monthly_dict[mo_key]['volume'] += c['volume']

        monthly_bars = [monthly_dict[k] for k in sorted(monthly_dict.keys())]

        self.bars_cache[sym] = (now, monthly_bars, daily_candles)
        return monthly_bars, daily_candles

    def get_spot_volume(self, symbol):
        sym = symbol.replace("USDT", "-USD").replace("USDC", "-USD").replace(".NS", "").replace("^", "")
        if not sym.endswith("-USD"):
            sym = sym + "-USD"
        now = time.time()
        if not self.vol_cache or (now - self.ticker_time >= 60):
            self.get_coinbase_symbols()
        return self.vol_cache.get(sym, 0.0)

    def format_usd(self, val):
        if val is None or val <= 0:
            return None
        if val >= 1_000_000_000:
            return f"${val / 1_000_000_000:.2f}B"
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        if val >= 1_000:
            return f"${val / 1_000:.0f}K"
        return f"${val:.1f}"

COINBASE_MGR = CoinbaseAPIManager()

class YahooSessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=60, pool_maxsize=60, max_retries=1)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.crumb = None
        self.crumb_time = 0
        self.lock = threading.Lock()
        self.data_cache = {}

    def ensure_crumb(self):
        with self.lock:
            now = time.time()
            if self.crumb and (now - self.crumb_time < 3600):
                return self.crumb
            try:
                self.session.get('https://fc.yahoo.com', timeout=6)
                r = self.session.get('https://query2.finance.yahoo.com/v1/test/getcrumb', timeout=6)
                txt = r.text.strip()
                if txt and 'Too Many Requests' not in txt and '<html' not in txt:
                    self.crumb = txt
                    self.crumb_time = now
                    return self.crumb
            except Exception:
                pass

    def fetch_crypto_direct(self, symbol):
        """
        Direct native crypto exchange pipeline:
        Tries Binance API -> Gate.io API -> falls back to Yahoo Finance.
        Returns (sorted_months, daily_candles).
        """
        base = symbol.replace('-USD', '').replace('USDT', '').replace('USD', '')
        binance_pair = f"{base}USDT"
        gate_pair = f"{base}_USDT"

        daily_candles = []

        # 1. Try Binance
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_pair}&interval=1d&limit=730"
            r = self.session.get(url, timeout=3)
            if r.status_code == 200:
                for k in r.json():
                    ts = int(k[0]) // 1000
                    o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
                    if o > 0 and h > 0 and l > 0 and c > 0:
                        daily_candles.append({
                            "time": ts,
                            "date": datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                            "open": o, "high": h, "low": l, "close": c,
                            "volume": int(float(k[5]))
                        })
        except Exception:
            pass

        # 2. Try Gate.io (unrestricted global exchange)
        if not daily_candles:
            try:
                url = f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={gate_pair}&interval=1d&limit=730"
                r = self.session.get(url, timeout=3)
                if r.status_code == 200:
                    for k in r.json():
                        ts = int(k[0])
                        o, h, l, c = float(k[5]), float(k[3]), float(k[4]), float(k[2])
                        if o > 0 and h > 0 and l > 0 and c > 0:
                            daily_candles.append({
                                "time": ts,
                                "date": datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                                "open": o, "high": h, "low": l, "close": c,
                                "volume": int(float(k[1]))
                            })
            except Exception:
                pass

        if daily_candles:
            monthly_dict = {}
            for candle in daily_candles:
                m_key = candle['date'][:7]
                if m_key not in monthly_dict:
                    monthly_dict[m_key] = {
                        'month': m_key,
                        'date': candle.get('date', f"{m_key}-01"),
                        'time': candle['time'],
                        'open': candle['open'],
                        'high': candle['high'],
                        'low': candle['low'],
                        'close': candle['close'],
                        'volume': candle['volume']
                    }
                else:
                    monthly_dict[m_key]['high'] = max(monthly_dict[m_key]['high'], candle['high'])
                    monthly_dict[m_key]['low'] = min(monthly_dict[m_key]['low'], candle['low'])
                    monthly_dict[m_key]['close'] = candle['close']
                    monthly_dict[m_key]['volume'] += candle['volume']
            sorted_months = [monthly_dict[k] for k in sorted(monthly_dict.keys())]
            return (sorted_months, daily_candles)

        return ([], [])

    def fetch_market_bars(self, symbol):
        cache_key = f"{symbol}_DAILY_HISTORY"
        now = time.time()
        if cache_key in self.data_cache:
            ts, bars = self.data_cache[cache_key]
            if now - ts < 600:
                return bars

        # Direct Crypto Exchange Pipeline (Binance / Gate.io)
        if "-USD" in symbol or "USDT" in symbol:
            months, candles = self.fetch_crypto_direct(symbol)
            if months and candles:
                self.data_cache[cache_key] = (now, (months, candles))
                return (months, candles)

        crumb = self.ensure_crumb()
        encoded_sym = urllib.parse.quote(symbol)
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{encoded_sym}?range=2y&interval=1d"
        if crumb:
            url += f"&crumb={crumb}"

        try:
            r = self.session.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                res = data['chart']['result'][0]
                timestamps = res.get('timestamp', [])
                quote = res['indicators']['quote'][0]
                
                monthly_dict = {}
                daily_candles = []
                
                for i in range(len(timestamps)):
                    t = timestamps[i]
                    o = quote.get('open', [])[i] if i < len(quote.get('open', [])) else None
                    h = quote.get('high', [])[i] if i < len(quote.get('high', [])) else None
                    l = quote.get('low', [])[i] if i < len(quote.get('low', [])) else None
                    c = quote.get('close', [])[i] if i < len(quote.get('close', [])) else None
                    v = quote.get('volume', [])[i] if i < len(quote.get('volume', [])) else None

                    if o is not None and h is not None and l is not None and c is not None:
                        if o > 0 and h > 0 and l > 0 and c > 0:
                            candle = {
                                "time": t, "date": datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d'),
                                "open": float(o), "high": float(h), "low": float(l), "close": float(c),
                                "volume": int(v or 0)
                            }
                            daily_candles.append(candle)
                            
                            m_key = datetime.datetime.fromtimestamp(t).strftime('%Y-%m')
                            c_date = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d')
                            if m_key not in monthly_dict:
                                monthly_dict[m_key] = {
                                    'month': m_key, 'date': c_date, 'time': t, 'open': float(o),
                                    'high': float(h), 'low': float(l), 'close': float(c),
                                    'volume': int(v or 0)
                                }
                            else:
                                monthly_dict[m_key]['high'] = max(monthly_dict[m_key]['high'], float(h))
                                monthly_dict[m_key]['low'] = min(monthly_dict[m_key]['low'], float(l))
                                monthly_dict[m_key]['close'] = float(c)
                                monthly_dict[m_key]['volume'] += int(v or 0)

                sorted_months = [monthly_dict[k] for k in sorted(monthly_dict.keys())]
                if sorted_months and daily_candles:
                    payload = (sorted_months, daily_candles)
                    self.data_cache[cache_key] = (now, payload)
                    return payload
        except Exception:
            pass
        return ([], [])

YAHOO_MGR = YahooSessionManager()

def calculate_cpr_and_pivots(h, l, c, decimals=2):
    p = (h + l + c) / 3.0
    bc = (h + l) / 2.0
    tc = (p - bc) + p
    cpr_top = max(tc, bc)
    cpr_bottom = min(tc, bc)
    cpr_width = cpr_top - cpr_bottom
    cpr_width_pct = (cpr_width / p) * 100.0 if p > 0 else 0.0

    rng = h - l
    r1 = 2 * p - l
    s1 = 2 * p - h
    r2 = p + rng
    s2 = p - rng
    r3 = r1 + rng
    s3 = s1 - rng

    h4 = c + (rng * 1.1 / 2.0)
    l4 = c - (rng * 1.1 / 2.0)
    h3 = c + (rng * 1.1 / 4.0)
    l3 = c - (rng * 1.1 / 4.0)

    return {
        "p": round(p, decimals),
        "tc": round(tc, decimals),
        "bc": round(bc, decimals),
        "cpr_top": round(cpr_top, decimals),
        "cpr_bot": round(cpr_bottom, decimals),
        "cpr_width": round(cpr_width, decimals),
        "cpr_width_pct": round(cpr_width_pct, 2),
        "r1": round(r1, decimals), "s1": round(s1, decimals),
        "r2": round(r2, decimals), "s2": round(s2, decimals),
        "r3": round(r3, decimals), "s3": round(s3, decimals),
        "h3": round(h3, decimals), "l3": round(l3, decimals),
        "h4": round(h4, decimals), "l4": round(l4, decimals)
    }

def process_cpr_setup(symbol, timeframe="monthly", mode="active"):
    """Inside Value CPR calculation following Frank Ochoa's Master Framework"""
    is_crypto = symbol.endswith("USDT") or symbol.endswith("USDC") or ("-USD" in symbol)
    if is_crypto:
        if symbol.endswith("-USD"):
            monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
        else:
            monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
    else:
        monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)

    if not daily_candles or len(daily_candles) < 3:
        return None

    if timeframe == "quarterly":
        quarterly_dict = {}
        for c in daily_candles:
            dt_str = c['date']
            y = dt_str[:4]
            m = int(dt_str[5:7])
            q = (m - 1) // 3 + 1
            q_key = f"{y}-Q{q}"
            if q_key not in quarterly_dict:
                quarterly_dict[q_key] = {
                    'quarter': q_key,
                    'high': c['high'],
                    'low': c['low'],
                    'close': c['close']
                }
            else:
                quarterly_dict[q_key]['high'] = max(quarterly_dict[q_key]['high'], c['high'])
                quarterly_dict[q_key]['low'] = min(quarterly_dict[q_key]['low'], c['low'])
                quarterly_dict[q_key]['close'] = c['close']

        sorted_quarters = [quarterly_dict[k] for k in sorted(quarterly_dict.keys())]
        if len(sorted_quarters) < 3:
            return None

        last_price = daily_candles[-1]['close']
        dec = 8 if is_crypto and last_price < 0.001 else (6 if is_crypto and last_price < 0.01 else (4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)))
        
        curr_q = sorted_quarters[-1]
        prev_q = sorted_quarters[-2]
        prev2_q = sorted_quarters[-3]
        
        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(curr_q['high'], curr_q['low'], curr_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_q['high'], prev_q['low'], prev_q['close'], dec)
            target_label = f"Next Quarter ({curr_q['quarter']})"
            base_label = f"Current Quarter ({prev_q['quarter']})"
            trigger_h = round(curr_q['high'], dec)
            trigger_l = round(curr_q['low'], dec)
            trigger_name_h = "QTD High (Buy)"
            trigger_name_l = "QTD Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(prev_q['high'], prev_q['low'], prev_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev2_q['high'], prev2_q['low'], prev2_q['close'], dec)
            target_label = f"Current Quarter ({prev_q['quarter']})"
            base_label = f"Prior Quarter ({prev2_q['quarter']})"
            trigger_h = round(prev_q['high'], dec)
            trigger_l = round(prev_q['low'], dec)
            trigger_name_h = "PQ High (Buy)"
            trigger_name_l = "PQ Low (Sell)"
            
        base_prev_close = prev_q['close']

    elif timeframe == "monthly":
        if not monthly_bars or len(monthly_bars) < 3:
            return None

        last_price = daily_candles[-1]['close']
        dec = 8 if is_crypto and last_price < 0.001 else (6 if is_crypto and last_price < 0.01 else (4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)))

        curr_m = monthly_bars[-1]
        prev_m = monthly_bars[-2]
        prev2_m = monthly_bars[-3]

        curr_m_lbl = curr_m.get('month', curr_m.get('date', '')[:7])
        prev_m_lbl = prev_m.get('month', prev_m.get('date', '')[:7])
        prev2_m_lbl = prev2_m.get('month', prev2_m.get('date', '')[:7])

        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(curr_m['high'], curr_m['low'], curr_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_m['high'], prev_m['low'], prev_m['close'], dec)
            target_label = f"Next Month (Developing)"
            base_label = f"Current Month ({curr_m_lbl})"
            trigger_h = round(curr_m['high'], dec)
            trigger_l = round(curr_m['low'], dec)
            trigger_name_h = "MTD High (Buy)"
            trigger_name_l = "MTD Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(prev_m['high'], prev_m['low'], prev_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev2_m['high'], prev2_m['low'], prev2_m['close'], dec)
            target_label = f"Current Month ({prev_m_lbl})"
            base_label = f"Previous Month ({prev2_m_lbl})"
            trigger_h = round(prev_m['high'], dec)
            trigger_l = round(prev_m['low'], dec)
            trigger_name_h = "PM High (Buy)"
            trigger_name_l = "PM Low (Sell)"
            
        base_prev_close = prev_m['close']

    else: # timeframe == "daily"
        if len(daily_candles) < 3: return None
        today_c = daily_candles[-1]
        yesterday_c = daily_candles[-2]
        day_before_c = daily_candles[-3]
        
        # Guard: In crypto, ensure the last candle is active (today or yesterday)
        if is_crypto:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            today_utc = now_utc.strftime("%Y-%m-%d")
            yesterday_utc = (now_utc - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            last_candle_date = today_c.get("date", "")
            if last_candle_date not in [today_utc, yesterday_utc]:
                return None
        
        last_price = today_c['close']
        if last_price < 0.000001: return None
        
        dec = 8 if is_crypto and last_price < 0.001 else (6 if is_crypto and last_price < 0.01 else (4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)))
        
        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(today_c['high'], today_c['low'], today_c['close'], dec)
            cpr_base = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            target_label = f"Tomorrow (Developing)"
            base_label = f"Today's CPR ({today_c.get('date', '')})"
            trigger_h = round(today_c['high'], dec)
            trigger_l = round(today_c['low'], dec)
            trigger_name_h = "Today High (Buy)"
            trigger_name_l = "Today Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            cpr_base = calculate_cpr_and_pivots(day_before_c['high'], day_before_c['low'], day_before_c['close'], dec)
            target_label = f"Today's CPR ({today_c.get('date', '')})"
            base_label = f"Prior Day CPR ({yesterday_c.get('date', '')})"
            trigger_h = round(yesterday_c['high'], dec)
            trigger_l = round(yesterday_c['low'], dec)
            trigger_name_h = "PD High (Buy)"
            trigger_name_l = "PD Low (Sell)"
            
        base_prev_close = yesterday_c['close']

    # 2-Day Pivot Range Relationships (Frank Ochoa's Master Framework)
    top_t, bot_t = cpr_target['cpr_top'], cpr_target['cpr_bot']
    top_b, bot_b = cpr_base['cpr_top'], cpr_base['cpr_bot']
    p_b = cpr_base['p']

    is_strict = (top_t <= top_b) and (bot_t >= bot_b)
    tol = p_b * 0.003
    is_near_coil = (top_t <= (top_b + tol)) and (bot_t >= (bot_b - tol))

    if is_strict:
        relationship = "Inside Value"
        rel_badge = "bg-purple-500/20 text-purple-300 border-purple-500/40"
        rel_icon = "⚡"
    elif is_near_coil:
        relationship = "Near Coil (95%+)"
        rel_badge = "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
        rel_icon = "🌀"
    elif bot_t > top_b:
        relationship = "Higher Value"
        rel_badge = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
        rel_icon = "🚀"
    elif top_t < bot_b:
        relationship = "Lower Value"
        rel_badge = "bg-rose-500/20 text-rose-300 border-rose-500/40"
        rel_icon = "🐻"
    elif top_t >= top_b and bot_t <= bot_b:
        relationship = "Outside Value"
        rel_badge = "bg-orange-500/20 text-orange-300 border-orange-500/40"
        rel_icon = "💥"
    elif bot_t > bot_b:
        relationship = "Overlap Higher"
        rel_badge = "bg-teal-500/20 text-teal-300 border-teal-500/40"
        rel_icon = "↗️"
    else:
        relationship = "Overlap Lower"
        rel_badge = "bg-amber-500/20 text-amber-300 border-amber-500/40"
        rel_icon = "↘️"

    width_target = cpr_target['cpr_width_pct']
    width_base = cpr_base['cpr_width_pct']
    compression_pct = round(((1.0 - (width_target / width_base)) * 100.0), 1) if width_base > 0 else 0.0

    ltp = round(last_price, dec)
    chg = round(ltp - base_prev_close, dec)
    chg_pct = round((chg / base_prev_close) * 100.0, 2) if base_prev_close > 0 else 0.0

    if ltp > cpr_target['cpr_top']:
        position_status = {"text": "Above CPR (Bullish Bias)", "class": "text-emerald-400 font-semibold"}
    elif ltp < cpr_target['cpr_bot']:
        position_status = {"text": "Below CPR (Bearish Bias)", "class": "text-rose-400 font-semibold"}
    else:
        position_status = {"text": "Inside CPR (Coiling in Value)", "class": "text-amber-400 font-semibold"}

    if is_strict:
        if compression_pct >= 70:
            quality_tag = {"text": "⚡ Mega Coil (>70%)", "badge": "bg-purple-500/20 text-purple-300 border-purple-500/40"}
        elif compression_pct >= 40:
            quality_tag = {"text": "🔥 High Compression (>40%)", "badge": "bg-amber-500/20 text-amber-300 border-amber-500/40"}
        else:
            quality_tag = {"text": "🟡 Strict Inside Value", "badge": "bg-yellow-500/20 text-yellow-300 border-yellow-500/40"}
    else:
        quality_tag = {"text": f"{rel_icon} {relationship}", "badge": rel_badge}

    clean_symbol = symbol.replace("USDT", "").replace("USDC", "").replace("-USD", "").replace(".NS", "").replace("^", "")
    
    if is_crypto:
        if symbol.endswith("-USD"):
            vol_usd = COINBASE_MGR.get_spot_volume(symbol)
            if not vol_usd:
                vol_usd = BINANCE_MGR.get_spot_volume(symbol)
            mc_formatted = (COINBASE_MGR.format_usd(vol_usd) + " 24h Vol") if vol_usd > 0 else None
        else:
            vol_usd = BINANCE_MGR.get_spot_volume(symbol)
            if not vol_usd:
                vol_usd = COINBASE_MGR.get_spot_volume(symbol)
            mc_formatted = (BINANCE_MGR.format_usd(vol_usd) + " 24h Vol") if vol_usd > 0 else None
        market_cap = vol_usd
    else:
        market_cap = None
        mc_formatted = None

    return {
        "symbol": symbol,
        "clean_symbol": clean_symbol,
        "market_cap": market_cap,
        "mc_formatted": mc_formatted,
        "strategy": "inside_value",
        "relationship": relationship,
        "rel_badge": rel_badge,
        "rel_icon": rel_icon,
        "is_inside_value": is_strict,
        "is_strict": is_strict,
        "cpr_width_pct": width_target,
        "timeframe": timeframe,
        "mode": mode,
        "target_label": target_label,
        "base_label": base_label,
        "ltp": ltp,
        "change": chg,
        "change_pct": chg_pct,
        "curr_cpr": cpr_target,
        "prev_cpr": cpr_base,
        "compression_pct": compression_pct,
        "quality_tag": quality_tag,
        "position_status": position_status,
        "pm_high": trigger_h,
        "pm_low": trigger_l,
        "trigger_name_h": trigger_name_h,
        "trigger_name_l": trigger_name_l,
        "candles": daily_candles[-60:]
    }

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pivot Boss CPR Terminal • Inside Value Compression Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        navy: {
                            700: '#1e293b',
                            800: '#0f172a',
                            900: '#0a0f1d',
                            950: '#030712'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #070d1e; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
        .glass { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px); }
    </style>
</head>
<body class="bg-navy-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-amber-500 selection:text-black">

    <!-- Header -->
    <header class="border-b border-navy-700/80 bg-navy-900/90 sticky top-0 z-40 backdrop-blur-md px-6 py-3.5 shadow-xl">
        <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            
            <!-- Branding -->
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-purple-600 flex items-center justify-center shadow-lg shadow-orange-500/25 ring-1 ring-white/20">
                    <span class="text-black font-black font-mono text-xl" id="logo-letter">⚡</span>
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-amber-200 to-orange-400 bg-clip-text text-transparent flex items-center gap-2">
                        PIVOT BOSS CPR TERMINAL
                        <span id="header-mode-badge" class="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-mono font-medium border border-purple-500/30">INSIDE VALUE COMPRESSION</span>
                    </h1>
                    <p class="text-xs text-slate-400">Institutional 2-Day Pivot Range Compression & Breakout Engine (Frank Ochoa Framework)</p>
                </div>
            </div>

            <!-- Controls: Timeframe, Mode, Market, Volume Filter, Playbook, Scan -->
            <div class="flex flex-wrap items-center gap-3">
                
                <!-- Timeframe Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setTimeframe('daily')" id="btn-tf-daily" class="px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow">
                        ⚡ Daily
                    </button>
                    <button onclick="setTimeframe('monthly')" id="btn-tf-monthly" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🗓️ Monthly
                    </button>
                    <button onclick="setTimeframe('quarterly')" id="btn-tf-quarterly" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        📊 Quarterly
                    </button>
                </div>

                <!-- Mode Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setMode('developing')" id="btn-mode-dev" class="px-3 py-1.5 rounded-lg transition-all text-white bg-purple-600 font-bold shadow">
                        🔮 Developing
                    </button>
                    <button onclick="setMode('active')" id="btn-mode-act" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        📍 Active
                    </button>
                </div>

                <!-- Market Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setMarket('crypto_all')" id="btn-crypto" class="px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-semibold shadow">
                        🪙 Binance Crypto
                    </button>
                    <button onclick="setMarket('crypto_coinbase')" id="btn-coinbase" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🔵 Coinbase Crypto
                    </button>
                    <button onclick="setMarket('india_all')" id="btn-india" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🇮🇳 India NSE
                    </button>
                    <button onclick="setMarket('us_russell2000')" id="btn-us" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🇺🇸 Russell 2000
                    </button>
                </div>

                <!-- Crypto 24h Volume Filter (Visible when Crypto is active) -->
                <div id="crypto-mc-controls" class="flex items-center bg-navy-950 p-1 rounded-xl border border-indigo-500/30 text-xs font-medium shadow-inner">
                    <button onclick="setMinMC(0)" id="btn-mc-all" class="px-2.5 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow" title="All Liquid Pairs">
                        <span id="btn-mc-all-label">🌐 All Pairs</span>
                    </button>
                    <button onclick="setMinMC(1000000)" id="btn-mc-5m" class="px-2.5 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white" title="High Liquidity >= $1M 24h Volume">
                        🔥 ≥ $1M Vol
                    </button>
                    <button onclick="setMinMC(25000000)" id="btn-mc-50m" class="px-2.5 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white" title="Mid-Cap Volume >= $25M 24h Volume">
                        💎 ≥ $25M Vol
                    </button>
                    <button onclick="setMinMC(100000000)" id="btn-mc-500m" class="px-2.5 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white" title="Large-Cap Giants >= $100M 24h Volume">
                        👑 ≥ $100M Vol
                    </button>
                </div>

                <button onclick="openPlaybookModal()" class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-amber-300 font-semibold text-xs border border-amber-500/30 transition shadow shadow-amber-950/20 active:scale-95">
                    📖 Playbook
                </button>
                <button onclick="runScan()" id="btn-refresh" class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-black font-bold text-xs shadow-lg shadow-orange-950/30 transition-all active:scale-95">
                    <svg id="refresh-icon" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    <span>Scan</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-6 py-6 w-full flex-1 flex flex-col gap-6">

        <!-- Strategy Alert Banner -->
        <div class="p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-navy-900 to-navy-900 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg" id="banner-card">
            <div class="flex items-start gap-3">
                <div class="text-2xl mt-0.5" id="banner-icon">🎯</div>
                <div>
                    <h3 class="text-sm font-bold text-amber-300" id="banner-title">Daily Developing Inside Value CPR Setup:</h3>
                    <p class="text-xs text-slate-300 mt-0.5" id="banner-desc">
                        These assets are in <strong>verified volatility compression</strong> (Pivot Range completely inside prior Pivot Range). Breakouts above Upper Boundary/Today High or breakdowns below Lower Boundary/Today Low trigger violent expansions.
                    </p>
                </div>
            </div>
            <div class="shrink-0 flex items-center gap-2 font-mono text-xs bg-navy-950/80 px-3 py-2 rounded-xl border border-navy-700">
                <span class="text-slate-400">Total Setups:</span>
                <span id="coils-total" class="text-amber-400 font-bold text-base">0</span>
            </div>
        </div>

        <!-- Table View -->
        <div id="cpr-table-card" class="glass rounded-2xl border border-navy-700/80 overflow-hidden shadow-2xl flex-1 flex flex-col">
            <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex flex-wrap items-center justify-between gap-3">
                <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2" id="table-title">
                    ⚡ Verified Inside Value CPRs & 2-Day Trends
                </span>
                <div class="flex items-center gap-2">
                    <!-- Quick Filter Pills (Frank Ochoa Framework) -->
                    <div id="quick-filters" class="flex flex-wrap items-center gap-1 bg-navy-950 p-1 rounded-xl border border-navy-700 text-[11px]">
                        <button onclick="setQuickFilter('inside')" id="qf-inside" class="px-2.5 py-1 rounded-lg bg-amber-400 text-black font-bold shadow">⚡ Inside Value</button>
                        <button onclick="setQuickFilter('all')" id="qf-all" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">All 2-Day Trends</button>
                        <button onclick="setQuickFilter('higher')" id="qf-higher" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🚀 Higher Value</button>
                        <button onclick="setQuickFilter('lower')" id="qf-lower" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🐻 Lower Value</button>
                        <button onclick="setQuickFilter('megacoil')" id="qf-megacoil" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">💥 MegaCoil (&gt;70%)</button>
                    </div>
                    <input type="text" id="search-input" onkeyup="renderTable()" placeholder="Search symbol..." class="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl px-3.5 py-1.5 focus:outline-none focus:border-amber-400 w-40 transition shadow-inner">
                </div>
            </div>

            <div class="overflow-x-auto flex-1">
                <table class="w-full text-left text-xs border-collapse">
                    <thead id="table-head">
                        <!-- Rendered dynamically -->
                    </thead>
                    <tbody id="table-body" class="divide-y divide-navy-700/50 font-mono">
                        <tr>
                            <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mb-3"></div>
                                <p>Scanning market universe for Inside Value CPRs & 2-Day Trends...</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <!-- Chart Modal -->
    <div id="chart-modal" class="fixed inset-0 bg-black/85 z-50 hidden backdrop-blur-md flex items-center justify-center p-4">
        <div class="bg-navy-900 border border-navy-700 rounded-2xl w-full max-w-5xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
            <div class="flex items-center justify-between px-6 py-4 border-b border-navy-700 bg-navy-950/80">
                <div class="flex items-center gap-3">
                    <span id="modal-symbol" class="text-lg font-bold text-white font-mono"></span>
                    <span id="modal-badge" class="px-2.5 py-1 rounded-md text-xs font-semibold"></span>
                </div>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-navy-800 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-navy-950/60 border-b border-navy-700 text-xs">
                <div><span class="text-slate-400">Target TC:</span> <span id="modal-tc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Target Pivot (P):</span> <span id="modal-p" class="font-mono text-purple-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Target BC:</span> <span id="modal-bc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Triggers:</span> <span id="modal-info" class="font-mono text-amber-400 font-semibold"></span></div>
            </div>
            <div id="chart-container" class="w-full h-96 p-2 bg-navy-950"></div>
        </div>
    </div>

    <!-- Playbook & Roadmap Modal -->
    <div id="playbook-modal" class="fixed inset-0 bg-black/85 z-50 hidden backdrop-blur-md flex items-center justify-center p-4">
        <div class="bg-navy-900 border border-amber-500/40 rounded-2xl w-full max-w-5xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
            <div class="flex items-center justify-between px-6 py-4 border-b border-navy-700 bg-navy-950/90">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">📖</span>
                    <div>
                        <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
                            PIVOT BOSS • INSIDE VALUE CPR & 2-DAY PIVOT RANGE PLAYBOOK
                            <span class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40">FRANK OCHOA FRAMEWORK</span>
                        </h2>
                        <p class="text-xs text-slate-400">Mastering institutional volatility compression, 2-day pivot relationships, and breakout execution</p>
                    </div>
                </div>
                <button onclick="closePlaybookModal()" class="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-navy-800 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            
            <!-- Playbook Body (Scrollable) -->
            <div class="p-6 overflow-y-auto space-y-6 text-xs text-slate-300 leading-relaxed font-sans">
                <!-- Grid 1: The Core Metrics -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700">
                        <div class="text-purple-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>⚡ Inside Value CPR (Engulfment)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">The upcoming CPR is <strong class="text-white">completely engulfed</strong> inside the prior period CPR (TC &le; Base TC and BC &ge; Base BC). Extreme volatility compression coiling energy before an explosive directional breakout.</p>
                        <div class="mt-2 text-[11px] text-purple-300 font-medium">• High-velocity multi-candle trend expansion imminent</div>
                        <div class="text-[11px] text-amber-300 font-medium">• Triggers: Breakout above Prior High or below Prior Low</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700">
                        <div class="text-emerald-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🚀 Higher Value (Bullish Continuation)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">The target Bottom Central (BC) is strictly <strong class="text-white">higher than the base Top Central (TC)</strong>. Market participants have accepted higher value, signaling aggressive accumulation.</p>
                        <div class="mt-2 text-[11px] text-emerald-300 font-medium">• Look for morning pullbacks into Central Pivot (P) / BC</div>
                        <div class="text-[11px] text-slate-400 font-medium">• Avoid shorting; focus strictly on bullish trend continuation</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700">
                        <div class="text-rose-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🐻 Lower Value (Bearish Continuation)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">The target Top Central (TC) is strictly <strong class="text-white">lower than the base Bottom Central (BC)</strong>. Value is descending, confirming that institutions are distributing into rallies.</p>
                        <div class="mt-2 text-[11px] text-rose-300 font-medium">• Look for morning bounces into Central Pivot (P) / TC to short</div>
                        <div class="text-[11px] text-slate-400 font-medium">• Targets: S1, S2, and prior swing lows</div>
                    </div>
                </div>

                <!-- 3 High Probability Setups -->
                <div class="p-5 rounded-xl bg-navy-950/80 border border-navy-700 space-y-4">
                    <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        🔥 3 High-Probability Trade Setups (Rules & Execution)
                    </h3>

                    <!-- Strategy 1 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-amber-400 text-sm">Setup 1: Inside Value Breakout Expansion (Trend Initiation)</span>
                            <span class="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40">Win Rate: ~75%</span>
                        </div>
                        <p class="text-slate-300">When CPR width compresses dramatically inside the prior CPR, price is coiling like a spring. Once price breaks the prior boundary, forced stops trigger rapid directional momentum.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Long Trigger:</strong> 15m candle close above Today High / PDH. <br><strong class="text-white">Short Trigger:</strong> 15m candle close below Today Low / PDL.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> Back inside Central Pivot (P) or opposite trigger.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Camarilla H4, Pivot R1, R2. Expected move: 1:3+ Risk/Reward.</div>
                        </div>
                    </div>

                    <!-- Strategy 2 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-purple-400 text-sm">Setup 2: MegaCoil (>70% Compression) Super-Trend Expansion</span>
                            <span class="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/40">Massive Expansion</span>
                        </div>
                        <p class="text-slate-300">Assets coiling with over 70% CPR width compression relative to the prior period are in extreme energy storage. Multi-timeframe confluence (Daily inside Monthly) produces multi-day institutional runs.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry:</strong> Confirm breakout on volume > 1.5x 20-period moving average.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Trailing Stop:</strong> Trail behind 1-hour candle lows (for longs) or candle highs (for shorts).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Target:</strong> Hold partial runners for multi-session expansion into macro weekly/monthly pivots.</div>
                        </div>
                    </div>

                    <!-- Strategy 3 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-emerald-400 text-sm">Setup 3: Higher / Lower Value Pullback Continuation</span>
                            <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/40">Trend Following</span>
                        </div>
                        <p class="text-slate-300">In Higher Value relationships, price often pulls back during the morning session to test the Central Pivot Range. A clean rejection candle at BC or P offers an optimal low-risk trend-following entry.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Long Entry:</strong> Bullish hammer or engulfing candle at P or BC.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> 0.3% below the Bottom Central (BC) line.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Prior High, R1, or R2.</div>
                        </div>
                    </div>
                </div>

                <!-- Daily Workflow & Rules -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700 space-y-2">
                        <div class="text-amber-400 font-bold text-sm flex items-center gap-1.5">
                            <span>📋 5-Minute Screening Routine</span>
                        </div>
                        <ol class="list-decimal list-inside space-y-1 text-slate-400">
                            <li><strong class="text-white">Check 🔮 Developing mode:</strong> See what coins/stocks are coiling for tomorrow or next month before the session begins.</li>
                            <li><strong class="text-white">Click ⚡ Inside Value:</strong> Pinpoint assets with strict inside value compression.</li>
                            <li><strong class="text-white">Check 💥 MegaCoil:</strong> Identify candidates with &gt; 70% compression for massive expansion potential.</li>
                            <li><strong class="text-white">Launch TV ↗:</strong> Open the selected asset directly in TradingView to fine-tune entry timing on the 5m/15m chart.</li>
                        </ol>
                    </div>

                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700 space-y-2">
                        <div class="text-rose-400 font-bold text-sm flex items-center gap-1.5">
                            <span>🛡️ Golden Risk Management Rules</span>
                        </div>
                        <ul class="space-y-1 text-slate-400">
                            <li><strong class="text-white">Maximum 1% - 1.5% Risk:</strong> Never risk more than 1.5% of total portfolio on an individual trade.</li>
                            <li><strong class="text-white">Respect Breakeven:</strong> Once price reaches 1.5R or tests S1/R1, immediately move Stop Loss to Breakeven.</li>
                            <li><strong class="text-white">Never Trade Against Trend:</strong> If market forms Lower Value, take only sell-side setups. If Higher Value, take only buy-side setups.</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="p-4 border-t border-navy-700 bg-navy-950/90 flex justify-end">
                <button onclick="closePlaybookModal()" class="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-300 text-black font-bold text-xs transition shadow active:scale-95">
                    Close Playbook & Trade
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentTimeframe = 'daily';
        let currentMode = 'developing';
        let currentMarket = 'crypto_all';
        let currentMinMC = 0; // 0 for all Binance USDT pairs
        let currentSort = { column: 'compression_pct', ascending: false };
        let scanData = [];
        let chartInstance = null;
        let currentQuickFilter = 'inside'; // default to 'inside'

        function formatCryptoNum(val) {
            if (val === null || val === undefined || isNaN(val)) return '-';
            const num = Number(val);
            if (num < 0.00001) return num.toFixed(8);
            if (num < 0.01) return num.toFixed(6);
            if (num < 1.0) return num.toFixed(4);
            if (num < 10.0) return num.toFixed(3);
            return num.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        function updateFilterCounts() {
            const strictCount = scanData.filter(i => i.is_strict || i.relationship === 'Inside Value').length;
            const nearCount = scanData.filter(i => i.relationship === 'Near Coil (95%+)').length;
            const higherCount = scanData.filter(i => i.relationship === 'Higher Value').length;
            const lowerCount = scanData.filter(i => i.relationship === 'Lower Value').length;
            const megaCount = scanData.filter(i => (i.compression_pct || 0) >= 70).length;
            
            const qfInside = document.getElementById('qf-inside');
            if (qfInside) {
                if (strictCount > 0) {
                    qfInside.innerHTML = `⚡ Inside Value (${strictCount})`;
                } else if (nearCount > 0) {
                    qfInside.innerHTML = `🌀 Near Coil (${nearCount})`;
                } else {
                    qfInside.innerHTML = `⚡ Inside Value (0)`;
                }
            }
            const qfAll = document.getElementById('qf-all');
            if (qfAll) qfAll.innerHTML = `All 2-Day Trends (${scanData.length})`;
            const qfHigher = document.getElementById('qf-higher');
            if (qfHigher) qfHigher.innerHTML = `🚀 Higher Value (${higherCount})`;
            const qfLower = document.getElementById('qf-lower');
            if (qfLower) qfLower.innerHTML = `🐻 Lower Value (${lowerCount})`;
            const qfMega = document.getElementById('qf-megacoil');
            if (qfMega) qfMega.innerHTML = `💥 MegaCoil (${megaCount})`;
        }

        function syncQuickFilterUI() {
            ['inside', 'all', 'higher', 'lower', 'megacoil'].forEach(id => {
                const btn = document.getElementById(`qf-${id}`);
                if (btn) {
                    if (id === currentQuickFilter) {
                        btn.className = 'px-2.5 py-1 rounded-lg bg-amber-400 text-black font-bold shadow';
                    } else {
                        btn.className = 'px-2.5 py-1 rounded-lg text-slate-400 hover:text-white';
                    }
                }
            });
        }

        function setMinMC(mc) {
            currentMinMC = mc;
            updateUIState();
            runScan();
        }

        function openPlaybookModal() {
            document.getElementById('playbook-modal').classList.remove('hidden');
        }

        function closePlaybookModal() {
            document.getElementById('playbook-modal').classList.add('hidden');
        }

        function setQuickFilter(qf) {
            currentQuickFilter = qf;
            syncQuickFilterUI();
            updateUIState();
            renderTable();
        }

        function updateUIState() {
            const badge = document.getElementById('header-mode-badge');
            const bannerCard = document.getElementById('banner-card');
            const bannerTitle = document.getElementById('banner-title');
            const bannerDesc = document.getElementById('banner-desc');
            const bannerIcon = document.getElementById('banner-icon');
            const tableTitle = document.getElementById('table-title');
            const logo = document.getElementById('logo-letter');

            // Timeframe buttons
            const btnDaily = document.getElementById('btn-tf-daily');
            const btnMonthly = document.getElementById('btn-tf-monthly');
            const btnQuarterly = document.getElementById('btn-tf-quarterly');
            [btnDaily, btnMonthly, btnQuarterly].forEach(b => {
                if (b) b.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            });

            if (currentTimeframe === 'daily') {
                if (btnDaily) btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                logo.innerText = '⚡';
            } else if (currentTimeframe === 'monthly') {
                if (btnMonthly) btnMonthly.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                logo.innerText = 'M';
            } else if (currentTimeframe === 'quarterly') {
                if (btnQuarterly) btnQuarterly.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                logo.innerText = 'Q';
            }

            // Mode buttons
            const btnDev = document.getElementById('btn-mode-dev');
            const btnAct = document.getElementById('btn-mode-act');
            if (currentMode === 'developing') {
                btnDev.className = 'px-3 py-1.5 rounded-lg transition-all text-white bg-purple-600 font-bold shadow';
                btnAct.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            } else {
                btnAct.className = 'px-3 py-1.5 rounded-lg transition-all text-white bg-emerald-600 font-bold shadow';
                btnDev.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            }

            const tfName = currentTimeframe === 'daily' ? 'DAILY' : (currentTimeframe === 'monthly' ? 'MONTHLY' : 'QUARTERLY');
            const modeName = currentMode === 'developing' ? 'DEVELOPING (NEXT)' : 'ACTIVE (CURRENT)';
            badge.innerText = `${tfName} • ${modeName}`;
            badge.className = 'px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono font-medium border border-amber-500/30';

            bannerCard.className = 'p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-navy-900 to-navy-900 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg';
            bannerIcon.innerText = '🎯';
            bannerTitle.className = 'text-sm font-bold text-amber-300';
            bannerTitle.innerText = `${tfName} ${modeName} Inside Value CPR Setup:`;
            if (currentTimeframe === 'quarterly') {
                bannerDesc.innerHTML = 'Quarterly Inside Value CPRs represent <strong>multi-month macro volatility compression</strong>. Breakouts above PQH/QTD High or breakdowns below PQL/QTD Low trigger massive institutional trend expansions.';
            } else {
                bannerDesc.innerHTML = 'These assets are in <strong>verified volatility compression</strong>. Trade breakouts above PMH/Today High or breakdowns below PML/Today Low.';
            }
            tableTitle.innerText = `🔥 Verified ${tfName} ${modeName} Inside Value Setups`;
            tableTitle.className = 'text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2';

            // Crypto market banner adjustments
            if (currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase') {
                const isCoinbase = currentMarket === 'crypto_coinbase';
                const exchangeName = isCoinbase ? 'Coinbase' : 'Binance';
                const totalLabel = isCoinbase ? '400+ Pairs' : '700+ Pairs';
                const volLabel = currentMinMC >= 1000000 ? `$${(currentMinMC/1e6).toFixed(0)}M` : (currentMinMC > 0 ? `$${currentMinMC}` : 'All');
                
                if (currentQuickFilter === 'inside') {
                    const hasStrict = scanData.some(i => i.is_strict || i.relationship === 'Inside Value');
                    if (hasStrict) {
                        tableTitle.innerText = `⚡ Verified Strict Inside Value CPRs (${exchangeName} • ${tfName} ${modeName})`;
                        bannerTitle.innerText = `${tfName} ${modeName} Strict Inside Value CPR Setup:`;
                        bannerDesc.innerHTML = `These assets are in <strong>verified volatility compression</strong> (Pivot Range completely inside prior Pivot Range). Breakouts above Upper Boundary/Today High or breakdowns below Lower Boundary/Today Low trigger violent expansions.`;
                    } else {
                        tableTitle.innerText = `🌀 95%+ Near-Coil CPRs (${exchangeName} • ${tfName} ${modeName})`;
                        bannerTitle.innerText = `${tfName} ${modeName} Near-Coil Setups (0 Strict Inside Today):`;
                        bannerDesc.innerHTML = `Due to yesterday's trend day, 0 coins formed 100% strict inside value. Showing <strong>closest 95%+ Near-Coil candidates</strong> coiling within 0.3% of prior CPR.`;
                    }
                } else if (currentQuickFilter === 'all') {
                    tableTitle.innerText = `📊 ${exchangeName} ${tfName} ${modeName} - All 2-Day Relationships`;
                    bannerTitle.innerText = `Two-Day Pivot Range Master Framework (${exchangeName}):`;
                    bannerDesc.innerHTML = `Tracking all 7 Frank Ochoa Two-Day Relationships (Inside Value, Outside Value, Higher Value, Lower Value, Overlap Higher, Overlap Lower).`;
                } else if (currentQuickFilter === 'higher') {
                    tableTitle.innerText = `🚀 ${exchangeName} Higher Value Bullish Continuations`;
                } else if (currentQuickFilter === 'lower') {
                    tableTitle.innerText = `🐻 ${exchangeName} Lower Value Bearish Continuations`;
                } else if (currentQuickFilter === 'megacoil') {
                    tableTitle.innerText = `💥 ${exchangeName} MegaCoil Setups (>70% Compression)`;
                }
            }

            // Market selector styles
            ['india', 'us', 'crypto', 'coinbase'].forEach(m => {
                const btn = document.getElementById(`btn-${m}`);
                if (btn) {
                    if ((m === 'india' && currentMarket === 'india_all') ||
                        (m === 'us' && currentMarket === 'us_russell2000') ||
                        (m === 'crypto' && currentMarket === 'crypto_all') ||
                        (m === 'coinbase' && currentMarket === 'crypto_coinbase')) {
                        btn.className = 'px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow';
                    } else {
                        btn.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    }
                }
            });

            // Crypto 24h Volume Filter Controls
            const mcControls = document.getElementById('crypto-mc-controls');
            if (currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase') {
                if (mcControls) mcControls.classList.remove('hidden');
                const lbl = document.getElementById('btn-mc-all-label');
                if (lbl) lbl.innerText = currentMarket === 'crypto_coinbase' ? '🔵 Coinbase All (400+)' : '🌐 Binance All (700+)';
                ['all', '5m', '50m', '500m'].forEach(k => {
                    const btn = document.getElementById(`btn-mc-${k}`);
                    if (btn) btn.className = 'px-2.5 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                });
                const activeKey = currentMinMC >= 100000000 ? '500m' : (currentMinMC >= 25000000 ? '50m' : (currentMinMC >= 1000000 ? '5m' : 'all'));
                const activeBtn = document.getElementById(`btn-mc-${activeKey}`);
                if (activeBtn) activeBtn.className = 'px-2.5 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow';
            } else {
                if (mcControls) mcControls.classList.add('hidden');
            }
        }

        function setTimeframe(tf) {
            currentTimeframe = tf;
            updateUIState();
            runScan();
        }

        function setMode(mode) {
            currentMode = mode;
            updateUIState();
            runScan();
        }

        function setMarket(market) {
            currentMarket = market;
            updateUIState();
            runScan();
        }

        async function runScan() {
            const tbody = document.getElementById('table-body');
            const thead = document.getElementById('table-head');
            const icon = document.getElementById('refresh-icon');
            icon.classList.add('animate-spin');
            
            const isCrypto = currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase';

            if (isCrypto) {
                thead.innerHTML = `
                    <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('market_cap')">Coin Pair & 24h Vol ↕</th>
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('compression_pct')">Compression % & Setup ↕</th>
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('cpr_width_pct')">Target CPR Band (BC • P • TC) ↕</th>
                        <th class="py-3.5 px-4">Base CPR Band (BC • P • TC)</th>
                        <th class="py-3.5 px-4">Breakout Triggers</th>
                        <th class="py-3.5 px-4">Position Status</th>
                        <th class="py-3.5 px-4 text-center">Chart / TV</th>
                    </tr>
                `;
            } else {
                thead.innerHTML = `
                    <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Asset Symbol ↕</th>
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                        <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('compression_pct')">Compression % & Setup ↕</th>
                        <th class="py-3.5 px-4">Target CPR Band (BC • P • TC)</th>
                        <th class="py-3.5 px-4">Base CPR Band (BC • P • TC)</th>
                        <th class="py-3.5 px-4">Breakout Triggers</th>
                        <th class="py-3.5 px-4">Targets (S1 • R1)</th>
                        <th class="py-3.5 px-4 text-center">Chart / TV</th>
                    </tr>
                `;
            }

            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mb-3"></div>
                        <p>Scanning ${currentMarket.toUpperCase()} for Inside Value CPRs & 2-Day Trends...</p>
                    </td>
                </tr>
            `;

            try {
                const response = await fetch(`/api/scan?market=${currentMarket}&timeframe=${currentTimeframe}&mode=${currentMode}&min_mc=${currentMinMC}`);
                const data = await response.json();
                scanData = data.results || [];
                document.getElementById('coils-total').innerText = scanData.length;
                updateFilterCounts();
                renderTable();
            } catch (err) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-12 text-rose-400 font-sans">
                            Failed to fetch market data. Please retry.
                        </td>
                    </tr>
                `;
            } finally {
                icon.classList.remove('animate-spin');
            }
        }

        function sortTable(column) {
            if (currentSort.column === column) {
                currentSort.ascending = !currentSort.ascending;
            } else {
                currentSort.column = column;
                currentSort.ascending = false;
            }
            renderTable();
        }

        function renderTable() {
            const query = (document.getElementById('search-input').value || '').toUpperCase();
            let filtered = scanData.filter(item => {
                if (query && !item.symbol.toUpperCase().includes(query) && !item.clean_symbol.toUpperCase().includes(query)) {
                    return false;
                }
                if (currentQuickFilter === 'all') {
                    // Show all coins
                } else if (currentQuickFilter === 'inside') {
                    const hasStrict = scanData.some(i => i.is_strict || i.relationship === 'Inside Value');
                    if (hasStrict) {
                        if (!item.is_strict && item.relationship !== 'Inside Value') return false;
                    } else {
                        // Fallback: If 0 strict inside value exist, display Near Coils (95%+ Coils)
                        if (item.relationship !== 'Near Coil (95%+)') return false;
                    }
                } else if (currentQuickFilter === 'higher') {
                    if (item.relationship !== 'Higher Value') return false;
                } else if (currentQuickFilter === 'lower') {
                    if (item.relationship !== 'Lower Value') return false;
                } else if (currentQuickFilter === 'megacoil') {
                    if ((item.compression_pct || 0) < 70) return false;
                }
                return true;
            });

            filtered.sort((a, b) => {
                let valA, valB;
                if (currentSort.column === 'clean_symbol') {
                    valA = a.clean_symbol; valB = b.clean_symbol;
                } else if (currentSort.column === 'ltp') {
                    valA = a.ltp; valB = b.ltp;
                } else if (currentSort.column === 'compression_pct') {
                    valA = a.compression_pct || 0; valB = b.compression_pct || 0;
                } else if (currentSort.column === 'cpr_width_pct') {
                    valA = a.cpr_width_pct !== undefined ? a.cpr_width_pct : (a.curr_cpr ? a.curr_cpr.cpr_width_pct : 0);
                    valB = b.cpr_width_pct !== undefined ? b.cpr_width_pct : (b.curr_cpr ? b.curr_cpr.cpr_width_pct : 0);
                } else if (currentSort.column === 'relationship') {
                    valA = a.relationship || ''; valB = b.relationship || '';
                } else if (currentSort.column === 'market_cap') {
                    valA = a.market_cap || 0; valB = b.market_cap || 0;
                }
                if (valA < valB) return currentSort.ascending ? -1 : 1;
                if (valA > valB) return currentSort.ascending ? 1 : -1;
                return 0;
            });

            const isCrypto = currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase';
            const tvExchange = currentMarket === 'crypto_coinbase' ? 'COINBASE' : 'BINANCE';
            const exchangeBadge = currentMarket === 'crypto_coinbase' ? 'Coinbase' : 'Binance';
            const tbody = document.getElementById('table-body');
            
            if (filtered.length === 0) {
                const lowerCount = scanData.filter(i => i.relationship === 'Lower Value').length;
                const higherCount = scanData.filter(i => i.relationship === 'Higher Value').length;
                const emptyMsg = currentQuickFilter === 'inside' 
                    ? `0 Strict Inside Value CPRs found for this selection.<br>
                       <span class="text-xs text-amber-300 mt-2 block font-normal">
                         Market Context: The market had a strong directional move in the prior session, so ${lowerCount} coins formed <strong>Lower Value CPRs</strong>.
                       </span>
                       <div class="mt-4 flex flex-wrap items-center justify-center gap-3">
                         <button onclick="setMode('developing')" class="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs shadow transition-all cursor-pointer">⚡ Switch to Tomorrow (Developing Inside Value)</button>
                         <button onclick="setQuickFilter('all')" class="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow transition-all cursor-pointer">📊 View All ${scanData.length} 2-Day Trends</button>
                         <button onclick="setQuickFilter('lower')" class="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow transition-all cursor-pointer">🐻 View ${lowerCount} Lower Value Trends</button>
                       </div>`
                    : `No matching setups found right now.<br><span class="text-xs text-slate-500 mt-1 inline-block">Try switching filter pill, timeframe or market.</span>`;
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                            <div class="text-3xl mb-2">🔍</div>
                            <p class="text-sm font-semibold text-slate-300">${emptyMsg}</p>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = filtered.map(item => {
                const chgColor = item.change >= 0 ? 'text-emerald-400' : 'text-rose-400';
                const chgSign = item.change >= 0 ? '+' : '';

                if (isCrypto) {
                    return `
                        <tr class="hover:bg-navy-800/80 transition group">
                            <td class="py-3.5 px-4">
                                <div class="font-bold text-white text-sm tracking-tight flex items-center gap-1.5">
                                    <span>${item.clean_symbol}</span>
                                    ${item.mc_formatted ? `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${item.mc_formatted}</span>` : ''}
                                </div>
                                <div class="text-[10px] text-slate-500 font-sans">${item.symbol} • ${exchangeBadge}</div>
                            </td>
                            <td class="py-3.5 px-4">
                                <div class="font-bold text-slate-100 font-mono">${formatCryptoNum(item.ltp)}</div>
                                <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${formatCryptoNum(item.change)} (${chgSign}${item.change_pct}%)</div>
                            </td>
                            <td class="py-3.5 px-4">
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.rel_badge || item.quality_tag.badge} font-sans">
                                    ${item.rel_icon || '⚡'} ${item.relationship || item.quality_tag.text}
                                </span>
                                <div class="text-[10px] font-sans mt-0.5 ${item.compression_pct > 0 ? 'text-amber-400' : 'text-slate-400'}">${item.compression_pct > 0 ? `-${item.compression_pct}% Compressed` : `+${Math.abs(item.compression_pct)}% Wider`}</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-slate-200 font-semibold"><span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_bot)}</span> • <span class="text-purple-400 font-bold font-mono">${formatCryptoNum(item.curr_cpr.p)}</span> • <span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_top)}</span></div>
                                <div class="text-[10px] text-amber-400 font-sans mt-0.5 font-medium">${item.target_label} (Width: ${(item.cpr_width_pct !== undefined ? item.cpr_width_pct : item.curr_cpr.cpr_width_pct)}%)</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-slate-400 font-mono"><span class="text-slate-500">${formatCryptoNum(item.prev_cpr.cpr_bot)}</span> • <span class="text-slate-400">${formatCryptoNum(item.prev_cpr.p)}</span> • <span class="text-slate-500">${formatCryptoNum(item.prev_cpr.cpr_top)}</span></div>
                                <div class="text-[10px] text-slate-500 font-sans mt-0.5">${item.base_label}</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div><span class="text-slate-400 font-sans">${item.trigger_name_h}:</span> <span class="text-emerald-400 font-bold font-mono">${formatCryptoNum(item.pm_high)}</span></div>
                                <div><span class="text-slate-400 font-sans">${item.trigger_name_l}:</span> <span class="text-rose-400 font-bold font-mono">${formatCryptoNum(item.pm_low)}</span></div>
                            </td>
                            <td class="py-3.5 px-4">
                                <div class="${item.position_status.class} text-[11px] font-sans">${item.position_status.text}</div>
                                <div class="text-[10px] text-slate-500 font-sans mt-0.5">R1: ${formatCryptoNum(item.curr_cpr.r1)} • S1: ${formatCryptoNum(item.curr_cpr.s1)}</div>
                            </td>
                            <td class="py-3.5 px-4 text-center">
                                <div class="flex items-center justify-center gap-1.5">
                                    <a href="https://www.tradingview.com/chart/?symbol=${tvExchange}:${currentMarket === 'crypto_coinbase' ? `${item.clean_symbol}USD` : `${item.clean_symbol}USDT`}" target="_blank" rel="noopener" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold" title="Open TradingView">
                                        TV ↗
                                    </a>
                                    <button onclick="openChart('${item.symbol}')" class="px-2.5 py-1 rounded-lg bg-navy-800 hover:bg-amber-500 hover:text-black text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                        View
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }

                return `
                    <tr class="hover:bg-navy-800/80 transition group">
                        <td class="py-3.5 px-4">
                            <div class="font-bold text-white text-sm tracking-tight">${item.clean_symbol}</div>
                            <div class="text-[10px] text-slate-500 font-sans">${item.symbol}</div>
                        </td>
                        <td class="py-3.5 px-4">
                            <div class="font-bold text-slate-100 font-mono">${formatCryptoNum(item.ltp)}</div>
                            <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${formatCryptoNum(item.change)} (${chgSign}${item.change_pct}%)</div>
                        </td>
                        <td class="py-3.5 px-4">
                            <span class="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${item.rel_badge || item.quality_tag.badge} font-sans">
                                ${item.rel_icon || '⚡'} ${item.relationship || item.quality_tag.text}
                            </span>
                            <div class="${item.position_status.class} text-[10px] font-sans mt-0.5">${item.position_status.text}</div>
                        </td>
                        <td class="py-3.5 px-4 text-[11px]">
                            <div class="text-slate-200 font-semibold"><span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_bot)}</span> • <span class="text-purple-400 font-bold font-mono">${formatCryptoNum(item.curr_cpr.p)}</span> • <span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_top)}</span></div>
                            <div class="text-[10px] text-amber-400 font-sans mt-0.5 font-medium">${item.target_label}</div>
                        </td>
                        <td class="py-3.5 px-4 text-[11px]">
                            <div class="text-slate-400 font-mono"><span class="text-slate-500">${formatCryptoNum(item.prev_cpr.cpr_bot)}</span> • <span class="text-slate-400">${formatCryptoNum(item.prev_cpr.p)}</span> • <span class="text-slate-500">${formatCryptoNum(item.prev_cpr.cpr_top)}</span></div>
                            <div class="text-[10px] text-slate-500 font-sans mt-0.5">${item.base_label}</div>
                        </td>
                        <td class="py-3.5 px-4 text-[11px]">
                            <div><span class="text-slate-400 font-sans">${item.trigger_name_h}:</span> <span class="text-emerald-400 font-bold font-mono">${formatCryptoNum(item.pm_high)}</span></div>
                            <div><span class="text-slate-400 font-sans">${item.trigger_name_l}:</span> <span class="text-rose-400 font-bold font-mono">${formatCryptoNum(item.pm_low)}</span></div>
                        </td>
                        <td class="py-3.5 px-4 text-[11px]">
                            <div><span class="text-slate-400 font-sans">R1:</span> <span class="text-emerald-400 font-medium">${formatCryptoNum(item.curr_cpr.r1)}</span></div>
                            <div><span class="text-slate-400 font-sans">S1:</span> <span class="text-rose-400 font-medium">${formatCryptoNum(item.curr_cpr.s1)}</span></div>
                        </td>
                        <td class="py-3.5 px-4 text-center">
                            <button onclick="openChart('${item.symbol}')" class="px-3 py-1 rounded-lg bg-navy-800 hover:bg-amber-500 hover:text-black text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function openChart(symbol) {
            const item = scanData.find(s => s.symbol === symbol);
            if (!item) return;

            document.getElementById('modal-symbol').innerText = `${item.clean_symbol} (${item.symbol})`;
            const badge = document.getElementById('modal-badge');
            
            if (item.is_strict || item.relationship === 'Inside Value') {
                badge.innerText = `⚡ Inside Value: -${item.compression_pct}% Compressed`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-purple-500/20 text-purple-300 border-purple-500/40`;
            } else {
                badge.innerText = `${item.rel_icon || '📊'} ${item.relationship}: ${item.compression_pct > 0 ? `-${item.compression_pct}% Compressed` : `+${Math.abs(item.compression_pct)}% Wider`}`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border ${item.rel_badge || 'border-slate-500'}`;
            }
            document.getElementById('modal-info').innerText = `${item.trigger_name_h}: ${formatCryptoNum(item.pm_high)} • ${item.trigger_name_l}: ${formatCryptoNum(item.pm_low)}`;

            document.getElementById('modal-tc').innerText = formatCryptoNum(item.curr_cpr.cpr_top);
            document.getElementById('modal-p').innerText = formatCryptoNum(item.curr_cpr.p);
            document.getElementById('modal-bc').innerText = formatCryptoNum(item.curr_cpr.cpr_bot);

            const modal = document.getElementById('chart-modal');
            modal.classList.remove('hidden');

            const container = document.getElementById('chart-container');
            container.innerHTML = '';

            chartInstance = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 380,
                layout: { background: { color: '#030712' }, textColor: '#94a3b8' },
                grid: { vertLines: { color: '#0f172a' }, horzLines: { color: '#0f172a' } },
                timeScale: { borderColor: '#1e293b', timeVisible: true },
                rightPriceScale: { borderColor: '#1e293b' }
            });

            const candleSeries = chartInstance.addCandlestickSeries({
                upColor: '#10b981', downColor: '#f43f5e',
                borderUpColor: '#10b981', borderDownColor: '#f43f5e',
                wickUpColor: '#10b981', wickDownColor: '#f43f5e',
            });

            const candleData = item.candles.map(c => ({
                time: c.time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            }));
            candleSeries.setData(candleData);

            // CPR Price Lines
            if (item.prev_cpr) {
                candleSeries.createPriceLine({
                    price: item.prev_cpr.cpr_top,
                    color: '#f59e0b',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: 'Base TC'
                });
                candleSeries.createPriceLine({
                    price: item.prev_cpr.cpr_bot,
                    color: '#f59e0b',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: 'Base BC'
                });
            }
            candleSeries.createPriceLine({
                price: item.curr_cpr.cpr_top,
                color: '#38bdf8',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'Target TC'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.p,
                color: '#a855f7',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: 'Target PIVOT'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.cpr_bot,
                color: '#38bdf8',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'Target BC'
            });

            chartInstance.timeScale().fitContent();
        }

        function closeModal() {
            document.getElementById('chart-modal').classList.add('hidden');
            if (chartInstance) {
                chartInstance.remove();
                chartInstance = null;
            }
        }

        window.onload = () => {
            currentQuickFilter = 'inside';
            syncQuickFilterUI();
            updateUIState();
            runScan();
        };
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route("/api/debug")
def api_debug():
    import traceback
    info = {}
    try:
        r2 = requests.get("https://data-api.binance.vision/api/v3/ticker/24hr", timeout=5)
        tickers = r2.json()
        info["binance_vision_tickers"] = {
            "status": r2.status_code,
            "is_list": isinstance(tickers, list),
            "count": len(tickers) if isinstance(tickers, list) else 0
        }
    except Exception as e:
        info["binance_vision_tickers"] = {"error": str(e)}

    try:
        r_k = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=5", timeout=5)
        k_data = r_k.json()
        info["binance_vision_klines"] = {
            "status": r_k.status_code,
            "bars": len(k_data) if isinstance(k_data, list) else 0
        }
    except Exception as e:
        info["binance_vision_klines"] = {"error": str(e)}

    try:
        cb_syms = COINBASE_MGR.get_coinbase_symbols(max_coins=10)
        info["coinbase_products"] = {
            "status": 200 if cb_syms else 500,
            "sample_count": len(cb_syms),
            "sample": cb_syms[:5]
        }
    except Exception as e:
        info["coinbase_products"] = {"error": str(e)}

    return jsonify(info)

@app.route("/api/scan")
def api_scan():
    import traceback
    try:
        market = request.args.get("market", "crypto_all")
        timeframe = request.args.get("timeframe", "daily")
        mode = request.args.get("mode", "developing")
        min_mc = float(request.args.get("min_mc", 0))

        if market == "crypto_all":
            # On serverless environments, limit max_coins to prevent function execution timeout
            is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
            max_limit = 650 if is_serverless else 800
            symbols = BINANCE_MGR.get_binance_symbols(min_quote_vol=min_mc, max_coins=max_limit)
        elif market == "crypto_coinbase":
            is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
            max_limit = 350 if is_serverless else 450
            symbols = COINBASE_MGR.get_coinbase_symbols(min_quote_vol=min_mc, max_coins=max_limit)
        else:
            watchlist_info = WATCHLISTS.get(market, WATCHLISTS["india_all"])
            symbols = watchlist_info["symbols"]
        
        results = []
        workers = 35 if (market in ["crypto_all", "crypto_coinbase"]) else 10
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_cpr_setup, sym, timeframe, mode) for sym in symbols]
            for f in futures:
                res = f.result()
                if res:
                    results.append(res)
            # Prioritize strict Inside Value setups first, then Near Coils, then others.
            # Within each group, rank by 24h Volume / Liquidity (descending) so top-tier liquid coins appear first!
            results.sort(key=lambda x: (
                1 if x.get('is_strict') else (0.5 if x.get('relationship') == 'Near Coil (95%+)' else 0),
                min(x.get('market_cap') or 0, 500_000_000),
                x.get('compression_pct', 0)
            ), reverse=True)
        
        return jsonify({
            "strategy": "inside_value",
            "market": market,
            "timeframe": timeframe,
            "mode": mode,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print("\n=======================================================")
    print("🚀 PIVOT BOSS - INSIDE VALUE CPR TERMINAL")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
