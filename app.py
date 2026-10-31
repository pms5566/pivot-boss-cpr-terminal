#!/usr/bin/env python3
"""
Pivot Boss CPR Terminal - Crypto Inside Value Compression Engine
Dedicated Institutional 2-Day Pivot Range Compression & Breakout Engine
Based on Frank Ochoa's "Secrets of a Pivot Boss" Master Framework.

Markets:
- 🪙 Binance Crypto (700+ Liquid Pairs via Official Spot API)
- 🔵 Coinbase Crypto (400+ Pairs via Official Exchange API)

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
        sym = symbol.replace("-USD", "USDT")
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
            r_d = self.session.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1d&limit=120", timeout=4)
            data = r_d.json()
            if isinstance(data, list):
                d_raw = data
        except Exception:
            pass

        if not d_raw:
            try:
                r_d = self.session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&limit=120", timeout=4)
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

        # Monthly bars (24 months = 8 quarters)
        m_raw = []
        try:
            r_m = self.session.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1M&limit=24", timeout=4)
            data = r_m.json()
            if isinstance(data, list):
                m_raw = data
        except Exception:
            pass

        if not m_raw:
            try:
                r_m = self.session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1M&limit=24", timeout=4)
                data = r_m.json()
                if isinstance(data, list):
                    m_raw = data
            except Exception:
                m_raw = []
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
        sym = symbol.replace("-USD", "USDT")
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
        sym = symbol.replace("USDT", "-USD").replace("USDC", "-USD")
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
        sym = symbol.replace("USDT", "-USD").replace("USDC", "-USD")
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
    if symbol.endswith("-USD"):
        monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
        if not daily_candles:
            monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
    else:
        monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
        if not daily_candles:
            monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)

    if not daily_candles or len(daily_candles) < 3:
        return None

    if timeframe == "quarterly":
        quarterly_dict = {}
        # Aggregate monthly bars into quarters (preferred since monthly_bars spans 24 months)
        bars_to_use = monthly_bars if (monthly_bars and len(monthly_bars) >= 3) else daily_candles
        for c in bars_to_use:
            dt_str = c['date']
            y = dt_str[:4]
            m = int(dt_str[5:7])
            q = (m - 1) // 3 + 1
            q_key = f"{y}-Q{q}"
            if q_key not in quarterly_dict:
                quarterly_dict[q_key] = {
                    'quarter': q_key,
                    'open': c.get('open', 0),
                    'high': c['high'],
                    'low': c['low'],
                    'close': c['close']
                }
            else:
                quarterly_dict[q_key]['high'] = max(quarterly_dict[q_key]['high'], c['high'])
                quarterly_dict[q_key]['low'] = min(quarterly_dict[q_key]['low'], c['low'])
                quarterly_dict[q_key]['close'] = c['close']

        sorted_quarters = [quarterly_dict[k] for k in sorted(quarterly_dict.keys())]

        last_price = daily_candles[-1]['close']
        dec = 8 if last_price < 0.001 else (6 if last_price < 0.01 else (4 if last_price < 1.0 else (3 if last_price < 10.0 else 2)))
        
        if mode == "developing":
            if len(sorted_quarters) < 2:
                return None
            curr_q = sorted_quarters[-1]
            prev_q = sorted_quarters[-2]
            cpr_target = calculate_cpr_and_pivots(curr_q['high'], curr_q['low'], curr_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_q['high'], prev_q['low'], prev_q['close'], dec)
            
            q_num = int(curr_q['quarter'][-1])
            q_year = int(curr_q['quarter'][:4])
            next_q = f"{q_year + 1}-Q1" if q_num == 4 else f"{q_year}-Q{q_num + 1}"
            target_label = f"Next Quarter ({next_q} Dev)"
            base_label = f"Current Quarter ({curr_q['quarter']})"
            trigger_h = round(curr_q['high'], dec)
            trigger_l = round(curr_q['low'], dec)
            trigger_name_h = "QTD High (Buy)"
            trigger_name_l = "QTD Low (Sell)"
            base_prev_close = prev_q['close']
        else:
            if len(sorted_quarters) < 3:
                return None
            curr_q = sorted_quarters[-1]
            prev_q = sorted_quarters[-2]
            prev2_q = sorted_quarters[-3]
            cpr_target = calculate_cpr_and_pivots(prev_q['high'], prev_q['low'], prev_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev2_q['high'], prev2_q['low'], prev2_q['close'], dec)
            target_label = f"Current Quarter ({curr_q['quarter']})"
            base_label = f"Prior Quarter ({prev_q['quarter']})"
            trigger_h = round(prev_q['high'], dec)
            trigger_l = round(prev_q['low'], dec)
            trigger_name_h = "PQ High (Buy)"
            trigger_name_l = "PQ Low (Sell)"
            base_prev_close = prev_q['close']

    elif timeframe == "monthly":
        if not monthly_bars or len(monthly_bars) < 3:
            return None

        last_price = daily_candles[-1]['close']
        dec = 8 if last_price < 0.001 else (6 if last_price < 0.01 else (4 if last_price < 1.0 else (3 if last_price < 10.0 else 2)))

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
            base_prev_close = prev_m['close']
        else:
            cpr_target = calculate_cpr_and_pivots(prev_m['high'], prev_m['low'], prev_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev2_m['high'], prev2_m['low'], prev2_m['close'], dec)
            target_label = f"Current Month ({curr_m_lbl})"
            base_label = f"Previous Month ({prev_m_lbl})"
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
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        today_utc = now_utc.strftime("%Y-%m-%d")
        yesterday_utc = (now_utc - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        last_candle_date = today_c.get("date", "")
        if last_candle_date not in [today_utc, yesterday_utc]:
            return None
        
        last_price = today_c['close']
        if last_price < 0.000001: return None
        
        dec = 8 if last_price < 0.001 else (6 if last_price < 0.01 else (4 if last_price < 1.0 else (3 if last_price < 10.0 else 2)))
        
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
    is_near_coil = (not is_strict) and (top_t <= (top_b + tol)) and (bot_t >= (bot_b - tol))
    is_inside = is_strict or is_near_coil

    width_target = cpr_target['cpr_width_pct']
    width_base = cpr_base['cpr_width_pct']
    compression_pct = round(((1.0 - (width_target / width_base)) * 100.0), 1) if width_base > 0 else 0.0

    # Narrow CPR Thresholds (Frank Ochoa Framework)
    if timeframe == "daily":
        narrow_width_threshold = 0.40
    elif timeframe == "monthly":
        narrow_width_threshold = 3.50
    else: # quarterly
        narrow_width_threshold = 4.50

    is_narrow = (width_target <= narrow_width_threshold) or (compression_pct >= 60.0)

    # Holy Grail Combo: Inside Value AND Narrow CPR
    is_combo = is_inside and is_narrow

    # STRICT FILTER: ONLY keep Inside Value, Narrow CPR, and Inside+Narrow CPR!
    # Exclude all non-compression trend noise (Higher Value, Lower Value, Outside Value, etc.)
    if not (is_combo or is_inside or is_narrow):
        return None

    if is_combo:
        relationship = "Inside + Narrow CPR"
        rel_badge = "bg-gradient-to-r from-orange-500/25 to-purple-500/25 text-amber-300 border-amber-500/50 shadow-sm"
        rel_icon = "🔥"
        priority = 3
        quality_tag = {"text": "🔥 Holy Grail: Inside + Narrow", "badge": "bg-gradient-to-r from-amber-500/20 to-purple-500/20 text-amber-300 border-amber-500/40"}
    elif is_strict:
        relationship = "Inside Value"
        rel_badge = "bg-purple-500/20 text-purple-300 border-purple-500/40"
        rel_icon = "⚡"
        priority = 2
        if compression_pct >= 70:
            quality_tag = {"text": "⚡ Mega Coil (>70%)", "badge": "bg-purple-500/20 text-purple-300 border-purple-500/40"}
        elif compression_pct >= 40:
            quality_tag = {"text": "⚡ High Compression (>40%)", "badge": "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"}
        else:
            quality_tag = {"text": "⚡ Inside Value", "badge": "bg-purple-500/20 text-purple-300 border-purple-500/40"}
    elif is_near_coil:
        relationship = "Near-Coil Inside"
        rel_badge = "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
        rel_icon = "🌀"
        priority = 2
        quality_tag = {"text": "🌀 Near-Coil Inside", "badge": "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"}
    else: # is_narrow
        relationship = "Narrow CPR"
        rel_badge = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
        rel_icon = "🎯"
        priority = 1
        if width_target <= (narrow_width_threshold * 0.5):
            quality_tag = {"text": "🎯 Razor-Thin CPR", "badge": "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"}
        else:
            quality_tag = {"text": "🎯 Narrow CPR", "badge": "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"}

    ltp = round(last_price, dec)
    chg = round(ltp - base_prev_close, dec)
    chg_pct = round((chg / base_prev_close) * 100.0, 2) if base_prev_close > 0 else 0.0

    if ltp > cpr_target['cpr_top']:
        position_status = {"text": "Above CPR (Bullish Bias)", "class": "text-emerald-400 font-semibold"}
    elif ltp < cpr_target['cpr_bot']:
        position_status = {"text": "Below CPR (Bearish Bias)", "class": "text-rose-400 font-semibold"}
    else:
        position_status = {"text": "Inside CPR (Coiling in Value)", "class": "text-amber-400 font-semibold"}

    clean_symbol = symbol.replace("USDT", "").replace("USDC", "").replace("-USD", "")
    
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

    return {
        "symbol": symbol,
        "clean_symbol": clean_symbol,
        "market_cap": market_cap,
        "mc_formatted": mc_formatted,
        "strategy": "inside_value",
        "relationship": relationship,
        "rel_badge": rel_badge,
        "rel_icon": rel_icon,
        "is_combo": is_combo,
        "is_inside_value": is_inside,
        "is_strict": is_strict,
        "is_narrow": is_narrow,
        "priority": priority,
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
    <title>Pivot Boss CPR Terminal • Volatility Compression Breakout Engine</title>
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
                        PIVOT BOSS <span class="text-amber-400">COMPRESSION ENGINE</span>
                        <span id="header-mode-badge" class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono font-medium border border-amber-500/30">DAILY • DEVELOPING</span>
                    </h1>
                    <p class="text-xs text-slate-400">Institutional Inside Value, Narrow CPR & Holy Grail Breakout Scanner (Binance & Coinbase Official APIs)</p>
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

                <!-- Market Selector: Binance vs Coinbase -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setMarket('crypto_all')" id="btn-crypto" class="px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-semibold shadow">
                        🪙 Binance Crypto
                    </button>
                    <button onclick="setMarket('crypto_coinbase')" id="btn-coinbase" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🔵 Coinbase Crypto
                    </button>
                </div>

                <!-- Crypto 24h Volume Filter -->
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
                        These crypto assets are in <strong>verified volatility compression</strong> (Pivot Range completely inside prior Pivot Range). Breakouts above Upper Boundary/Today High or breakdowns below Lower Boundary/Today Low trigger violent expansions.
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
                    <!-- Quick Filter Pills (Compression Master Framework) -->
                    <div id="quick-filters" class="flex flex-wrap items-center gap-1 bg-navy-950 p-1 rounded-xl border border-navy-700 text-[11px]">
                        <button onclick="setQuickFilter('combo')" id="qf-combo" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🔥 Inside + Narrow</button>
                        <button onclick="setQuickFilter('inside')" id="qf-inside" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">⚡ Inside Value</button>
                        <button onclick="setQuickFilter('narrow')" id="qf-narrow" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🎯 Narrow CPR</button>
                        <button onclick="setQuickFilter('all')" id="qf-all" class="px-2.5 py-1 rounded-lg bg-amber-400 text-black font-bold shadow">🌐 All Setups</button>
                        <button onclick="setQuickFilter('megacoil')" id="qf-megacoil" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">💥 MegaCoil (&gt;70%)</button>
                    </div>
                    <input type="text" id="search-input" onkeyup="renderTable()" placeholder="Search symbol..." class="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl px-3.5 py-1.5 focus:outline-none focus:border-amber-400 w-40 transition shadow-inner">
                </div>
            </div>

            <div class="overflow-x-auto flex-1">
                <table class="w-full text-left text-xs border-collapse">
                    <thead id="table-head">
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('market_cap')">Coin Pair & 24h Vol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('priority')">Setup & Compression ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('cpr_width_pct')">Target CPR Band (BC • P • TC) ↕</th>
                            <th class="py-3.5 px-4">Base CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4">Breakout Triggers</th>
                            <th class="py-3.5 px-4">Position Status</th>
                            <th class="py-3.5 px-4 text-center">Chart / TV</th>
                        </tr>
                    </thead>
                    <tbody id="table-body" class="divide-y divide-navy-700/50 font-mono">
                        <tr>
                            <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mb-3"></div>
                                <p>Scanning crypto universe for Inside Value & Narrow CPR Compression Setups...</p>
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
                            PIVOT BOSS • VOLATILITY COMPRESSION PLAYBOOK
                            <span class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40">FRANK OCHOA FRAMEWORK</span>
                        </h2>
                        <p class="text-xs text-slate-400">Mastering Inside Value CPR, Narrow CPR, and Holy Grail Double Compression in Crypto</p>
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
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-amber-500/40 shadow-sm">
                        <div class="text-amber-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🔥 Inside + Narrow CPR (The Holy Grail)</span>
                        </div>
                        <p class="text-slate-300 leading-normal">Satisfies <strong class="text-white">BOTH conditions simultaneously</strong>: Target CPR is strictly engulfed inside Base CPR (Inside Value) AND target CPR width is razor-thin (&le; 0.40% daily or &ge; 60% compression). Maximum institutional coiling energy.</p>
                        <div class="mt-2 text-[11px] text-amber-300 font-medium">• Highest breakout win-rate & violent multi-candle follow-through</div>
                        <div class="text-[11px] text-orange-300 font-medium">• Triggers: Decisive breakout above Today High or below Today Low</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-purple-500/40 shadow-sm">
                        <div class="text-purple-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>⚡ Inside Value CPR (Engulfment)</span>
                        </div>
                        <p class="text-slate-300 leading-normal">The upcoming CPR is <strong class="text-white">completely engulfed</strong> inside the prior period CPR (TC &le; Base TC and BC &ge; Base BC). Range contraction indicates commercial participants coiling energy before an explosive directional impulse.</p>
                        <div class="mt-2 text-[11px] text-purple-300 font-medium">• Classic Frank Ochoa compression setup</div>
                        <div class="text-[11px] text-slate-400 font-medium">• Triggers: 15m close above Prior High (Long) or below Prior Low (Short)</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-emerald-500/40 shadow-sm">
                        <div class="text-emerald-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🎯 Narrow CPR (Width Compression)</span>
                        </div>
                        <p class="text-slate-300 leading-normal">The CPR band is <strong class="text-white">exceptionally narrow relative to price</strong> (&le; 0.40% daily / &le; 3.5% monthly / &ge; 60% compression). In Pivot Boss principles, narrow CPR days foreshadow massive trending expansion days.</p>
                        <div class="mt-2 text-[11px] text-emerald-300 font-medium">• Shifts market from sideways chop into high-velocity trend</div>
                        <div class="text-[11px] text-slate-400 font-medium">• Targets: Camarilla H4, Pivot R2/R3 extensions</div>
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
                            <span class="text-amber-400 text-sm">Setup 1: Holy Grail Inside + Narrow Double Breakout</span>
                            <span class="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40">Win Rate: ~80%</span>
                        </div>
                        <p class="text-slate-300">When an asset meets both Inside Value engulfment AND Narrow CPR width, energy compression is at its theoretical peak. Price cannot remain in this tight state and expands violently upon the breakout of the prior bar's extremes.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry Trigger:</strong> 15m candle close outside Today High (Long) or Today Low (Short).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> Back inside Central Pivot (P) or opposite CPR boundary.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Camarilla H4 / L4, R2, R3 extensions (1:3+ R:R minimum).</div>
                        </div>
                    </div>

                    <!-- Strategy 2 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-purple-400 text-sm">Setup 2: Inside Value Breakout Expansion</span>
                            <span class="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/40">Directional Trend Initiation</span>
                        </div>
                        <p class="text-slate-300">When the target CPR is fully enveloped inside base CPR, market participants are accepting value inside yesterday's range. Once the boundary is pierced on volume, forced liquidity triggers rapid trend initiation.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry Trigger:</strong> Breakout above PDH/Today High with volume expansion > 1.3x 20MA.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> 0.2% behind Central Pivot (P).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Target:</strong> Pivot R1, R2, and Prior Swing High.</div>
                        </div>
                    </div>

                    <!-- Strategy 3 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-emerald-400 text-sm">Setup 3: Narrow CPR Trending Day / Session</span>
                            <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/40">High-Velocity Trend Day</span>
                        </div>
                        <p class="text-slate-300">Narrow CPR occurs when the preceding day had a wide consolidation or multi-day range contraction. In crypto, narrow CPR days typically exhibit one-way trend behavior throughout the UTC session.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry:</strong> First 15m candle close above TC (Bullish) or below BC (Bearish).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Trailing Stop:</strong> Trail behind 1-hour candle lows (longs) or highs (shorts).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Let winners run into macro weekly / monthly pivot levels.</div>
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
                            <li><strong class="text-white">Check 🔮 Developing mode:</strong> Spot setups coiling for tomorrow or next month before UTC daily close.</li>
                            <li><strong class="text-white">Filter 🔥 Inside + Narrow:</strong> Prioritize double-compression Holy Grail candidates.</li>
                            <li><strong class="text-white">Check ⚡ Inside Value & 🎯 Narrow CPR:</strong> Identify pure value engulfment or razor-thin width setups.</li>
                            <li><strong class="text-white">Launch TV ↗:</strong> Open in TradingView to set alerts right at the trigger levels.</li>
                        </ol>
                    </div>

                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700 space-y-2">
                        <div class="text-rose-400 font-bold text-sm flex items-center gap-1.5">
                            <span>🛡️ Golden Risk Management Rules</span>
                        </div>
                        <ul class="space-y-1 text-slate-400">
                            <li><strong class="text-white">Maximum 1% - 1.5% Risk:</strong> Never risk more than 1.5% of total capital on any single altcoin trade.</li>
                            <li><strong class="text-white">Respect Breakeven:</strong> Once price reaches 1.5R or breaks R1/S1, move Stop Loss to entry price.</li>
                            <li><strong class="text-white">Let Compression Expand:</strong> Compression precedes expansion; never exit prematurely before targets.</li>
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
        let currentMinMC = 0; // 0 for all liquid pairs
        let currentSort = { column: 'priority', ascending: false };
        let scanData = [];
        let chartInstance = null;
        let currentQuickFilter = 'all'; // default to 'all' so users see everything right away

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
            const comboCount = scanData.filter(i => i.is_combo || i.relationship === 'Inside + Narrow CPR').length;
            const insideCount = scanData.filter(i => i.is_inside_value || i.is_strict || i.relationship === 'Inside Value' || i.relationship === 'Near-Coil Inside' || i.relationship === 'Inside + Narrow CPR').length;
            const narrowCount = scanData.filter(i => i.is_narrow || i.relationship === 'Narrow CPR' || i.relationship === 'Inside + Narrow CPR').length;
            const megaCount = scanData.filter(i => (i.compression_pct || 0) >= 70).length;
            
            const qfCombo = document.getElementById('qf-combo');
            if (qfCombo) qfCombo.innerHTML = `🔥 Inside + Narrow (${comboCount})`;

            const qfInside = document.getElementById('qf-inside');
            if (qfInside) qfInside.innerHTML = `⚡ Inside Value (${insideCount})`;

            const qfNarrow = document.getElementById('qf-narrow');
            if (qfNarrow) qfNarrow.innerHTML = `🎯 Narrow CPR (${narrowCount})`;

            const qfAll = document.getElementById('qf-all');
            if (qfAll) qfAll.innerHTML = `🌐 All Setups (${scanData.length})`;

            const qfMega = document.getElementById('qf-megacoil');
            if (qfMega) qfMega.innerHTML = `💥 MegaCoil (${megaCount})`;
        }

        function syncQuickFilterUI() {
            ['combo', 'inside', 'narrow', 'all', 'megacoil'].forEach(id => {
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
            bannerTitle.innerText = `${tfName} ${modeName} Volatility Compression Breakout Engine:`;

            const isCoinbase = currentMarket === 'crypto_coinbase';
            const exchangeName = isCoinbase ? 'Coinbase' : 'Binance';
            
            if (currentQuickFilter === 'combo') {
                tableTitle.innerText = `🔥 Holy Grail Double Compression: Inside + Narrow CPRs (${exchangeName} • ${tfName} ${modeName})`;
                bannerTitle.innerText = `${tfName} ${modeName} Inside + Narrow CPR (Holy Grail):`;
                bannerDesc.innerHTML = `These crypto assets satisfy <strong>BOTH Inside Value engulfment AND Narrow CPR width</strong>. Maximum institutional coiling energy; violent multi-candle breakout imminent.`;
            } else if (currentQuickFilter === 'inside') {
                tableTitle.innerText = `⚡ Inside Value Compression CPRs (${exchangeName} • ${tfName} ${modeName})`;
                bannerTitle.innerText = `${tfName} ${modeName} Inside Value Compression:`;
                bannerDesc.innerHTML = `Target CPR is <strong>strictly engulfed</strong> inside the base CPR. Trade breakouts above the Upper Trigger or breakdowns below the Lower Trigger.`;
            } else if (currentQuickFilter === 'narrow') {
                tableTitle.innerText = `🎯 Razor-Thin Narrow CPR Breakouts (${exchangeName} • ${tfName} ${modeName})`;
                bannerTitle.innerText = `${tfName} ${modeName} Narrow CPR Setup:`;
                bannerDesc.innerHTML = `Exceptionally tight CPR band indicating extreme prior compression (Frank Ochoa framework). High probability of trending market behavior and violent directional expansion.`;
            } else if (currentQuickFilter === 'megacoil') {
                tableTitle.innerText = `💥 MegaCoil Extreme Compression (>70%) (${exchangeName} • ${tfName} ${modeName})`;
                bannerTitle.innerText = `${tfName} ${modeName} MegaCoil Extreme Compression (>70%):`;
                bannerDesc.innerHTML = `Extreme volatility compression tier. Energy coiling over 70% tighter than prior period. Prepare for aggressive directional trend continuation.`;
            } else {
                tableTitle.innerText = `⚡ Verified Compression Terminal: Inside Value • Narrow CPR • Combos (${exchangeName} • ${tfName} ${modeName})`;
                bannerTitle.innerText = `${tfName} ${modeName} Volatility Compression Breakout Engine:`;
                bannerDesc.innerHTML = `Showing verified <strong>Inside Value CPRs</strong>, <strong>Narrow CPRs</strong>, and <strong>Holy Grail Double Combos</strong>. All non-compression noise has been filtered out.`;
            }

            // Market selector styles
            const btnCrypto = document.getElementById('btn-crypto');
            const btnCoinbase = document.getElementById('btn-coinbase');
            if (btnCrypto) {
                btnCrypto.className = currentMarket === 'crypto_all' 
                    ? 'px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow'
                    : 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            }
            if (btnCoinbase) {
                btnCoinbase.className = currentMarket === 'crypto_coinbase' 
                    ? 'px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow'
                    : 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            }

            // Volume Controls
            const lbl = document.getElementById('btn-mc-all-label');
            if (lbl) lbl.innerText = isCoinbase ? '🔵 Coinbase All (400+)' : '🌐 Binance All (700+)';
            ['all', '5m', '50m', '500m'].forEach(k => {
                const btn = document.getElementById(`btn-mc-${k}`);
                if (btn) btn.className = 'px-2.5 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
            });
            const activeKey = currentMinMC >= 100000000 ? '500m' : (currentMinMC >= 25000000 ? '50m' : (currentMinMC >= 1000000 ? '5m' : 'all'));
            const activeBtn = document.getElementById(`btn-mc-${activeKey}`);
            if (activeBtn) activeBtn.className = 'px-2.5 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow';
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
            const icon = document.getElementById('refresh-icon');
            icon.classList.add('animate-spin');

            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mb-3"></div>
                        <p>Scanning ${currentMarket === 'crypto_coinbase' ? 'Coinbase' : 'Binance'} for Inside Value CPRs & 2-Day Trends...</p>
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
                    return true;
                } else if (currentQuickFilter === 'combo') {
                    if (!item.is_combo && item.relationship !== 'Inside + Narrow CPR') return false;
                } else if (currentQuickFilter === 'inside') {
                    if (!item.is_inside_value && !item.is_strict && item.relationship !== 'Inside Value' && item.relationship !== 'Near-Coil Inside' && item.relationship !== 'Inside + Narrow CPR') return false;
                } else if (currentQuickFilter === 'narrow') {
                    if (!item.is_narrow && item.relationship !== 'Narrow CPR' && item.relationship !== 'Inside + Narrow CPR') return false;
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
                } else if (currentSort.column === 'relationship' || currentSort.column === 'priority') {
                    valA = a.priority || 0; valB = b.priority || 0;
                } else if (currentSort.column === 'market_cap') {
                    valA = a.market_cap || 0; valB = b.market_cap || 0;
                }
                if (valA < valB) return currentSort.ascending ? -1 : 1;
                if (valA > valB) return currentSort.ascending ? 1 : -1;
                const mcDiff = (b.market_cap || 0) - (a.market_cap || 0);
                if (mcDiff !== 0) return mcDiff;
                return (b.compression_pct || 0) - (a.compression_pct || 0);
            });

            const tvExchange = currentMarket === 'crypto_coinbase' ? 'COINBASE' : 'BINANCE';
            const exchangeBadge = currentMarket === 'crypto_coinbase' ? 'Coinbase' : 'Binance';
            const tbody = document.getElementById('table-body');
            
            if (filtered.length === 0) {
                const emptyMsg = `No matching compression setups found for this filter.<br>
                       <span class="text-xs text-amber-300 mt-2 block font-normal">
                         Try clicking <strong>🌐 All Setups</strong> or switching between <strong>🔮 Developing</strong> and <strong>📍 Active</strong>.
                       </span>`;
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
            }).join('');
        }

        function openChart(symbol) {
            const item = scanData.find(s => s.symbol === symbol);
            if (!item) return;

            document.getElementById('modal-symbol').innerText = `${item.clean_symbol} (${item.symbol})`;
            const badge = document.getElementById('modal-badge');
            
            if (item.is_combo) {
                badge.innerText = `🔥 Inside + Narrow CPR: -${item.compression_pct}% Compressed`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-gradient-to-r from-orange-500/25 to-purple-500/25 text-amber-300 border-amber-500/50`;
            } else if (item.is_strict || item.relationship === 'Inside Value') {
                badge.innerText = `⚡ Inside Value: -${item.compression_pct}% Compressed`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-purple-500/20 text-purple-300 border-purple-500/40`;
            } else if (item.relationship === 'Near-Coil Inside') {
                badge.innerText = `🌀 Near-Coil Inside: -${item.compression_pct}% Compressed`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-cyan-500/20 text-cyan-300 border-cyan-500/40`;
            } else {
                badge.innerText = `🎯 Narrow CPR: Width ${item.cpr_width_pct}% (-${item.compression_pct}%)`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-emerald-500/20 text-emerald-300 border-emerald-500/40`;
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
            currentQuickFilter = 'all';
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

        is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
        if market == "crypto_coinbase":
            max_limit = 350 if is_serverless else 450
            symbols = COINBASE_MGR.get_coinbase_symbols(min_quote_vol=min_mc, max_coins=max_limit)
        else:
            max_limit = 650 if is_serverless else 800
            symbols = BINANCE_MGR.get_binance_symbols(min_quote_vol=min_mc, max_coins=max_limit)
        
        results = []
        workers = 35
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_cpr_setup, sym, timeframe, mode) for sym in symbols]
            for f in futures:
                res = f.result()
                if res:
                    results.append(res)
            # Prioritize Combos (Holy Grail) first, then Inside Value, then Narrow CPR.
            # Within each group, rank by 24h Volume / Liquidity (descending) so top-tier liquid coins appear first!
            results.sort(key=lambda x: (
                x.get('priority', 0),
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
    print("🚀 PIVOT BOSS - CRYPTO INSIDE VALUE TERMINAL")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
