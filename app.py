#!/usr/bin/env python3
"""
Pivot Boss - Multi-Strategy CPR Terminal
Strategies:
1. 🎯 Inside Value CPR (Multi-Timeframe: Daily & Monthly, Active & Developing)
2. 🛡️ Daily Virgin CPR (Untested CPR formed within max 10 trading days)
Markets:
- 🇮🇳 Indian Equities (NSE F&O / Top 100)
- 🇺🇸 US Russell 2000 (Small-Caps & IWM Leaders)
- 🪙 Crypto (Top 110+ Coins)
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
        "name": "🪙 Top Cryptocurrencies & Altcoins (110+ Pairs)",
        "symbols": [
            "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD",
            "AVAX-USD", "DOT-USD", "LINK-USD", "NEAR-USD", "SUI-USD", "APT-USD",
            "RENDER-USD", "TAO-USD", "UNI-USD", "LTC-USD", "BCH-USD", "AAVE-USD",
            "ICP-USD", "ATOM-USD", "ARB-USD", "OP-USD", "INJ-USD", "RUNE-USD",
            "FET-USD", "KAS-USD", "TIA-USD", "SEI-USD", "ALGO-USD", "XLM-USD", "HBAR-USD",
            "FIL-USD", "STX-USD", "VET-USD", "IMX-USD", "GRT-USD", "FTM-USD", "THETA-USD",
            "SAND-USD", "MANA-USD", "AXS-USD", "GALA-USD", "ENJ-USD", "CHZ-USD",
            "CRV-USD", "MKR-USD", "SNX-USD", "COMP-USD", "LDO-USD", "PENDLE-USD",
            "DYDX-USD", "ENA-USD", "STRK-USD", "BLUR-USD", "JUP-USD", "PYTH-USD",
            "RAY-USD", "ORDI-USD", "WIF-USD", "BOME-USD",
            "POPCAT-USD", "NEO-USD", "IOTA-USD", "EOS-USD", "XTZ-USD", "ZIL-USD",
            "KAVA-USD", "FLOW-USD", "MINA-USD", "QNT-USD", "EGLD-USD", "BEAM-USD", "RON-USD",
            "YFI-USD", "1INCH-USD", "SUSHI-USD", "CAKE-USD", "WOO-USD", "RPL-USD", "SSV-USD",
            "CFX-USD", "ACH-USD", "JASMY-USD", "GNO-USD", "LRC-USD", "ZRX-USD", "BAT-USD",
            "ANKR-USD", "AKT-USD", "ARKM-USD", "WLD-USD", "ONDO-USD", "TRU-USD", "POLYX-USD", "OM-USD"
        ]
    },
    "crypto_coinbase": {
        "name": "🔵 Coinbase Crypto (USD Pairs)",
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
        self.f_ticker_cache = {}
        self.f_ticker_time = 0
        self.funding_cache = {}
        self.funding_time = 0
        self.oi_cache = {}
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
            'fapi.binance.com': resolve_doh('fapi.binance.com'),
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

    def get_futures_tickers(self):
        now = time.time()
        if self.f_ticker_cache and (now - self.f_ticker_time < 30):
            return self.f_ticker_cache
        try:
            r = self.session.get("https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=5)
            data = r.json()
            if isinstance(data, list):
                self.f_ticker_cache = {t["symbol"]: t for t in data}
                self.f_ticker_time = now
        except Exception:
            pass
        return self.f_ticker_cache

    def get_funding_rates(self):
        now = time.time()
        if self.funding_cache and (now - self.funding_time < 60):
            return self.funding_cache
        try:
            r = self.session.get("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=5)
            data = r.json()
            if isinstance(data, list):
                self.funding_cache = {t["symbol"]: t for t in data}
                self.funding_time = now
        except Exception:
            pass
        return self.funding_cache

    def get_open_interest(self, symbol):
        now = time.time()
        cached = self.oi_cache.get(symbol)
        if cached and (now - cached[0] < 60):
            return cached[1]
        try:
            r = self.session.get(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}", timeout=4)
            d = r.json()
            oi = float(d.get("openInterest", 0) or 0)
            self.oi_cache[symbol] = (now, oi)
            return oi
        except Exception:
            return 0.0

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

    def get_crypto_derivatives(self, symbol, fetch_oi=True):
        sym = symbol.replace("-USD", "USDT").replace(".NS", "").replace("^", "")
        if not sym.endswith("USDT"):
            sym = sym + "USDT"

        f_tickers = self.get_futures_tickers()
        funding_map = self.get_funding_rates()

        f_data = f_tickers.get(sym)
        if not f_data and not sym.startswith("1000"):
            sym_1000 = "1000" + sym
            if sym_1000 in f_tickers:
                sym = sym_1000
                f_data = f_tickers[sym]

        if not f_data:
            spot_vol = self.get_spot_volume(symbol)
            if spot_vol > 0:
                return {
                    "oi_usd": 0,
                    "oi_formatted": "-",
                    "vol_24h_usd": spot_vol,
                    "vol_formatted": self.format_usd(spot_vol),
                    "squeeze_ratio": 0.0,
                    "squeeze_badge": "SPOT ONLY",
                    "squeeze_class": "bg-slate-500/20 text-slate-300 border-slate-500/40",
                    "funding_pct": 0.0,
                    "funding_formatted": "-",
                    "funding_bias": "Spot Asset",
                    "squeeze_direction": "Spot Trading",
                    "squeeze_dir_class": "text-slate-400"
                }
            return None

        price = float(f_data.get("lastPrice", 0) or 0)
        vol_usd = float(f_data.get("quoteVolume", 0) or 0)
        
        oi_usd = 0
        squeeze_ratio = 0.0
        if fetch_oi and (sym in self.oi_cache or vol_usd >= 25_000_000):
            oi_coins = self.get_open_interest(sym)
            oi_usd = oi_coins * price
            squeeze_ratio = round(oi_usd / vol_usd, 2) if vol_usd > 0 else 0.0

        fund_info = funding_map.get(sym, {})
        funding_pct = float(fund_info.get("lastFundingRate", 0) or 0) * 100.0

        if squeeze_ratio >= 3.0:
            squeeze_badge = "CRITICAL SQUEEZE"
            squeeze_class = "bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse"
        elif squeeze_ratio >= 1.5:
            squeeze_badge = "HIGH LEVERAGE"
            squeeze_class = "bg-amber-500/20 text-amber-300 border-amber-500/40"
        elif squeeze_ratio >= 0.8:
            squeeze_badge = "HEALTHY"
            squeeze_class = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
        elif squeeze_ratio > 0:
            squeeze_badge = "LOW LEVERAGE"
            squeeze_class = "bg-slate-500/20 text-slate-300 border-slate-500/40"
        else:
            squeeze_badge = "PERP"
            squeeze_class = "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"

        if funding_pct > 0.05:
            funding_bias = "Crowded Longs (Short Squeeze Fuel)"
        elif funding_pct < -0.05:
            funding_bias = "Crowded Shorts (Long Squeeze Fuel)"
        elif funding_pct > 0.005:
            funding_bias = "Mildly Long"
        elif funding_pct < -0.005:
            funding_bias = "Mildly Short"
        else:
            funding_bias = "Neutral Funding"

        return {
            "oi_usd": oi_usd,
            "oi_formatted": self.format_usd(oi_usd) if oi_usd > 0 else "-",
            "vol_24h_usd": vol_usd,
            "vol_formatted": self.format_usd(vol_usd),
            "squeeze_ratio": squeeze_ratio,
            "squeeze_badge": squeeze_badge,
            "squeeze_class": squeeze_class,
            "funding_pct": round(funding_pct, 4),
            "funding_formatted": f"{funding_pct:+.4f}%",
            "funding_bias": funding_bias,
            "squeeze_direction": "Short Squeeze Fuel" if funding_pct < -0.01 else ("Long Squeeze Fuel" if funding_pct > 0.03 else "Balanced"),
            "squeeze_dir_class": "text-emerald-400" if funding_pct < -0.01 else ("text-rose-400" if funding_pct > 0.03 else "text-slate-400")
        }

    def get_crypto_oi_radar(self, search_coin="BTC", watchlist=None):
        f_tickers = self.get_futures_tickers()
        funding_map = self.get_funding_rates()

        all_items = []
        for sym, t in f_tickers.items():
            if not sym.endswith("USDT"):
                continue
            vol = float(t.get("quoteVolume", 0) or 0)
            price = float(t.get("lastPrice", 0) or 0)
            chg = float(t.get("priceChangePercent", 0) or 0)
            if vol < 500_000 or price <= 0:
                continue

            clean = sym.replace("USDT", "")
            fund_info = funding_map.get(sym, {})
            fund_pct = float(fund_info.get("lastFundingRate", 0) or 0) * 100.0

            all_items.append({
                "symbol": sym,
                "clean_symbol": clean,
                "price": price,
                "chg_pct": chg,
                "vol_usd": vol,
                "vol_formatted": self.format_usd(vol),
                "funding_pct": fund_pct,
                "funding_formatted": f"{fund_pct:+.4f}%"
            })

        top_oi = sorted(all_items, key=lambda x: x["vol_usd"], reverse=True)[:5]
        top_funding = sorted(all_items, key=lambda x: abs(x["funding_pct"]), reverse=True)[:5]

        # Top squeeze ratios from high-volume contracts
        top_squeezes = []
        try:
            with ThreadPoolExecutor(max_workers=10) as ex:
                derivs = list(ex.map(lambda it: (it, self.get_crypto_derivatives(it["symbol"])), top_oi[:5]))
                for it, d in derivs:
                    if d and d["squeeze_ratio"] > 0:
                        top_squeezes.append({
                            "clean_symbol": it["clean_symbol"],
                            "squeeze_ratio": d["squeeze_ratio"],
                            "squeeze_badge": d["squeeze_badge"],
                            "squeeze_class": d["squeeze_class"],
                            "funding_formatted": d["funding_formatted"]
                        })
            top_squeezes.sort(key=lambda x: x["squeeze_ratio"], reverse=True)
        except Exception:
            pass

        # Hero coin lookup
        search_sym = search_coin.upper().replace("USDT", "") + "USDT"
        hero_deriv = self.get_crypto_derivatives(search_sym)
        hero = None
        actual_sym = search_sym if search_sym in f_tickers else ("1000" + search_sym)
        if hero_deriv and actual_sym in f_tickers:
            t = f_tickers[actual_sym]
            hero = {
                "symbol": actual_sym,
                "clean_symbol": search_coin.upper().replace("USDT", ""),
                "price": float(t.get("lastPrice", 0) or 0),
                "chg_pct": float(t.get("priceChangePercent", 0) or 0),
                **hero_deriv
            }

        # Watchlist lookup
        wl_items = []
        if watchlist:
            for w in watchlist:
                w_sym = w.upper().replace("USDT", "") + "USDT"
                d = self.get_crypto_derivatives(w_sym)
                actual_w = w_sym if w_sym in f_tickers else ("1000" + w_sym)
                if d and actual_w in f_tickers:
                    t = f_tickers[actual_w]
                    wl_items.append({
                        "symbol": actual_w,
                        "clean_symbol": w.upper().replace("USDT", ""),
                        "price": float(t.get("lastPrice", 0) or 0),
                        "chg_pct": float(t.get("priceChangePercent", 0) or 0),
                        **d
                    })

        return {
            "hero": hero,
            "watchlist": wl_items,
            "leaderboards": {
                "top_squeezes": top_squeezes,
                "top_oi": top_oi,
                "top_funding": top_funding
            }
        }

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
    def get_crypto_market_caps(self):
        """
        Fetches circulating market caps for all currencies from Gate.io spot currencies API.
        Returns dict: { 'BTC': 1620105480119.0, ... }
        Cached for 3600 seconds.
        """
        cache_key = "CRYPTO_MARKET_CAPS"
        now = time.time()
        if cache_key in self.data_cache:
            ts, mc_map = self.data_cache[cache_key]
            if now - ts < 3600:
                return mc_map
        mc_map = {}
        try:
            url = 'https://api.gateio.ws/api/v4/spot/currencies'
            r = self.session.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                for c in data:
                    curr = c.get('currency', '').upper()
                    mc_str = c.get('market_cap', '')
                    if curr and mc_str and not c.get('delisted', False) and not c.get('trade_disabled', False):
                        try:
                            mc = float(mc_str)
                            if mc > 0:
                                mc_map[curr] = mc
                        except Exception:
                            pass
        except Exception:
            pass
        self.data_cache[cache_key] = (now, mc_map)
        return mc_map

    def format_market_cap(self, mc):
        if not mc or mc <= 0:
            return None
        if mc >= 1_000_000_000:
            return f"${mc / 1_000_000_000:.2f}B"
        elif mc >= 1_000_000:
            return f"${mc / 1_000_000:.1f}M"
        elif mc >= 1_000:
            return f"${mc / 1_000:.0f}K"
        return f"${mc:.0f}"

    def get_dynamic_crypto_symbols(self, min_mc=5_000_000, max_coins=1200):
        now = time.time()
        cache_key = f"DYNAMIC_CRYPTO_SYMBOLS_{min_mc}_{max_coins}"
        if cache_key in self.data_cache:
            ts, syms = self.data_cache[cache_key]
            if now - ts < 1800:
                return syms

        base_list = WATCHLISTS["crypto_all"]["symbols"]
        symbols_set = set(base_list)

        mc_map = self.get_crypto_market_caps()

        try:
            url = 'https://api.gateio.ws/api/v4/spot/tickers'
            r = self.session.get(url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                stables_and_junk = {'USDT', 'USDC', 'USD', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'EUR', 'USDE', 'PYUSD', 'PAXG', 'XAUT', 'USDY', 'STETH', 'WBTC', 'WETH', 'RLUSD', 'USDD', 'FRAX', 'LUSD', 'GUSD', 'USDP'}
                candidates = []
                for t in data:
                    pair = t.get('currency_pair', '')
                    if pair.endswith('_USDT'):
                        base = pair.replace('_USDT', '').upper()
                        if base in stables_and_junk: continue
                        if base.endswith('3L') or base.endswith('3S') or base.endswith('5L') or base.endswith('5S'): continue
                        if (base.endswith('G') or base.endswith('ON') or base.endswith('X')) and len(base) >= 3 and any(s in base for s in ['WMT', 'HD', 'LLY', 'QQQ', 'SPY', 'TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'META', 'GLD', 'SLV', 'COIN', 'MSTR', 'PLTR', 'COST', 'HOOD', 'SNDK', 'BRK', 'AVGO']):
                            continue
                        if not base.isascii() or not base.isalnum(): continue
                        
                        coin_mc = mc_map.get(base, 0)
                        # Filter for coins whose Market Cap is >= min_mc (if specified)
                        if min_mc > 0 and coin_mc < min_mc:
                            continue

                        try:
                            vol = float(t.get('quote_volume', 0) or 0)
                            price = float(t.get('last', 0) or 0)
                            if vol >= 1000 and price > 0:
                                candidates.append((f"{base}-USD", coin_mc, vol))
                        except Exception:
                            pass

                # Sort by Market Cap descending (highest institutional quality coins first)
                candidates.sort(key=lambda x: x[1], reverse=True)
                for sym, _, _ in candidates[:max_coins]:
                    symbols_set.add(sym)
        except Exception:
            pass

        final_list = list(symbols_set)
        priority = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "SUI-USD", "NEAR-USD", "PEPE-USD", "LINK-USD", "LTC-USD"]
        sorted_final = [p for p in priority if p in final_list] + [s for s in final_list if s not in priority]
        
        self.data_cache[cache_key] = (now, sorted_final)
        return sorted_final

    def get_crypto_derivatives_data(self):
        """
        Fetches live Open Interest, 24h Volume, and Funding Rate for 1,000+ crypto futures contracts
        from Gate.io public futures ticker API. Cached for 120 seconds.
        """
        cache_key = "CRYPTO_DERIVATIVES_CACHE"
        now = time.time()
        if cache_key in self.data_cache:
            ts, data = self.data_cache[cache_key]
            if now - ts < 120:
                return data

        deriv_map = {}
        mc_map = self.get_crypto_market_caps()
        try:
            url = "https://api.gateio.ws/api/v4/futures/usdt/tickers"
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                tickers = r.json()
                for item in tickers:
                    contract = item.get("contract", "")
                    if not contract.endswith("_USDT"):
                        continue
                    base = contract.split("_")[0].upper()
                    
                    try:
                        total_size = float(item.get("total_size", 0) or 0)
                        multiplier = float(item.get("quanto_multiplier", 1) or 1)
                        last_p = float(item.get("last", 0) or 0)
                        vol_usd = float(item.get("volume_24h_quote", 0) or 0)
                        funding = float(item.get("funding_rate", 0) or 0)
                        
                        oi_usd = total_size * multiplier * last_p
                        funding_pct = round(funding * 100.0, 4)
                        squeeze_ratio = round(oi_usd / vol_usd, 2) if vol_usd > 0 else 0.0
                        
                        # Format OI
                        if oi_usd >= 1_000_000_000:
                            oi_fmt = f"${oi_usd / 1_000_000_000:.2f}B"
                        elif oi_usd >= 1_000_000:
                            oi_fmt = f"${oi_usd / 1_000_000:.2f}M"
                        elif oi_usd >= 1_000:
                            oi_fmt = f"${oi_usd / 1_000:.1f}K"
                        else:
                            oi_fmt = f"${oi_usd:.0f}"

                        # Format Volume
                        if vol_usd >= 1_000_000_000:
                            vol_fmt = f"${vol_usd / 1_000_000_000:.2f}B"
                        elif vol_usd >= 1_000_000:
                            vol_fmt = f"${vol_usd / 1_000_000:.2f}M"
                        elif vol_usd >= 1_000:
                            vol_fmt = f"${vol_usd / 1_000:.1f}K"
                        else:
                            vol_fmt = f"${vol_usd:.0f}"

                        # Squeeze classification
                        if squeeze_ratio >= 3.0:
                            squeeze_badge = "⚡ High Squeeze"
                            squeeze_class = "bg-rose-500/20 text-rose-300 border-rose-500/40"
                            squeeze_risk = "High"
                        elif squeeze_ratio >= 1.5:
                            squeeze_badge = "🔥 Over-leveraged"
                            squeeze_class = "bg-amber-500/20 text-amber-300 border-amber-500/40"
                            squeeze_risk = "Elevated"
                        else:
                            squeeze_badge = "🟢 Balanced"
                            squeeze_class = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            squeeze_risk = "Normal"

                        funding_bias = "Longs Pay" if funding_pct > 0.01 else ("Shorts Pay" if funding_pct < -0.01 else "Neutral")

                        if squeeze_ratio >= 1.5:
                            if funding_pct < -0.005:
                                squeeze_direction = "🚀 Short Squeeze Target"
                                squeeze_dir_class = "text-emerald-400 font-bold"
                            elif funding_pct > 0.015:
                                squeeze_direction = "💥 Long Flush Risk"
                                squeeze_dir_class = "text-rose-400 font-bold"
                            else:
                                squeeze_direction = "⚡ High Leverage Coil"
                                squeeze_dir_class = "text-amber-400 font-medium"
                        chg_pct = round(float(item.get("change_percentage", 0) or 0), 2)
                        high_24h = float(item.get("high_24h", 0) or 0)
                        low_24h = float(item.get("low_24h", 0) or 0)
                        index_p = float(item.get("index_price", last_p) or last_p)
                        mark_p = float(item.get("mark_price", last_p) or last_p)
                        basis_pct = round(((last_p - index_p) / index_p) * 100.0, 3) if index_p > 0 else 0.0
                        annualized_funding = round(funding_pct * 3 * 365.0, 2)

                        if chg_pct > 0 and funding_pct > 0.005:
                            oi_signal = "🚀 Long Accumulation"
                            oi_signal_desc = "Buyers aggressively opening leverage in uptrend"
                            oi_signal_class = "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                        elif chg_pct > 0 and funding_pct <= 0.005:
                            oi_signal = "⚡ Short Covering Rally"
                            oi_signal_desc = "Shorts buying to cover / forced liquidation pump"
                            oi_signal_class = "text-cyan-400 bg-cyan-500/10 border-cyan-500/30"
                        elif chg_pct < 0 and funding_pct < 0.005:
                            oi_signal = "💥 Short Building Flush"
                            oi_signal_desc = "Aggressive bears building short exposure in downtrend"
                            oi_signal_class = "text-rose-400 bg-rose-500/10 border-rose-500/30"
                        elif chg_pct < 0 and funding_pct >= 0.005:
                            oi_signal = "⚠️ Long Capitulation"
                            oi_signal_desc = "Long liquidations flushing over-leveraged buyers"
                            oi_signal_class = "text-amber-400 bg-amber-500/10 border-amber-500/30"
                        else:
                            oi_signal = "🟢 Balanced Orderflow"
                            oi_signal_desc = "Normal institutional rotation without extreme imbalance"
                            oi_signal_class = "text-slate-300 bg-slate-500/10 border-slate-500/30"

                        coin_mc = mc_map.get(base)
                        mc_fmt = self.format_market_cap(coin_mc)

                        deriv_map[base] = {
                            "symbol": f"{base}-USD",
                            "clean_symbol": base,
                            "market_cap": coin_mc,
                            "mc_formatted": mc_fmt,
                            "last_price": last_p,
                            "change_pct": chg_pct,
                            "high_24h": high_24h,
                            "low_24h": low_24h,
                            "mark_price": mark_p,
                            "index_price": index_p,
                            "basis_pct": basis_pct,
                            "contracts_count": int(total_size),
                            "oi_usd": round(oi_usd, 2),
                            "oi_formatted": oi_fmt,
                            "vol_usd": round(vol_usd, 2),
                            "vol_formatted": vol_fmt,
                            "funding_pct": funding_pct,
                            "funding_formatted": f"{funding_pct:+.4f}%",
                            "annualized_funding_pct": f"{annualized_funding:+.2f}%",
                            "funding_bias": funding_bias,
                            "squeeze_ratio": squeeze_ratio,
                            "squeeze_badge": squeeze_badge,
                            "squeeze_class": squeeze_class,
                            "squeeze_risk": squeeze_risk,
                            "squeeze_direction": squeeze_direction,
                            "squeeze_dir_class": squeeze_dir_class,
                            "oi_signal": oi_signal,
                            "oi_signal_desc": oi_signal_desc,
                            "oi_signal_class": oi_signal_class
                        }
                    except Exception:
                        continue
        except Exception:
            pass

        self.data_cache[cache_key] = (now, deriv_map)
        return deriv_map

    def get_crypto_derivatives(self, symbol):
        base = symbol.replace("-USD", "").replace("USDT", "").replace("USD", "").replace(".NS", "").replace("^", "").upper()
        data = self.get_crypto_derivatives_data()
        return data.get(base)

    def get_crypto_oi_radar(self, search_sym="PEPE", watchlist_symbols=None):
        deriv_map = self.get_crypto_derivatives_data()
        valid_items = list(deriv_map.values())

        # Leaderboards
        sq_candidates = [x for x in valid_items if x["vol_usd"] >= 300000]
        top_squeeze = sorted(sq_candidates, key=lambda x: x["squeeze_ratio"], reverse=True)[:8]

        neg_candidates = [x for x in valid_items if x["vol_usd"] >= 150000]
        top_neg_funding = sorted(neg_candidates, key=lambda x: x["funding_pct"])[:8]

        pos_candidates = [x for x in valid_items if x["vol_usd"] >= 150000]
        top_pos_funding = sorted(pos_candidates, key=lambda x: x["funding_pct"], reverse=True)[:8]

        top_oi = sorted(valid_items, key=lambda x: x["oi_usd"], reverse=True)[:8]

        # Search resolution
        clean_search = (search_sym or "PEPE").replace("-USD", "").replace("USDT", "").replace("USD", "").strip().upper()
        searched_coin = deriv_map.get(clean_search)
        if not searched_coin and clean_search:
            for k, v in deriv_map.items():
                if k.startswith(clean_search):
                    searched_coin = v
                    break

        # Tracked Watchlist
        if not watchlist_symbols:
            watchlist_symbols = ["BTC", "ETH", "SOL", "PEPE", "SUI", "DOGE", "NEAR", "INJ"]

        watchlist_coins = []
        for s in watchlist_symbols:
            c_clean = s.replace("-USD", "").replace("USDT", "").replace("USD", "").strip().upper()
            if c_clean in deriv_map:
                watchlist_coins.append(deriv_map[c_clean])

        return {
            "searched_coin": searched_coin,
            "watchlist_coins": watchlist_coins,
            "leaderboards": {
                "top_squeeze": top_squeeze,
                "top_neg_funding": top_neg_funding,
                "top_pos_funding": top_pos_funding,
                "top_oi": top_oi
            }
        }

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
    """Inside Value CPR calculation"""
    is_crypto = symbol.endswith("USDT") or symbol.endswith("USDC") or ("-USD" in symbol)
    if is_crypto:
        if symbol.endswith("-USD"):
            monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
        else:
            monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
    else:
        monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
    
    if timeframe == "quarterly":
        bars_source = monthly_bars if len(monthly_bars) >= 6 else daily_candles
        if not bars_source: return None
        quarterly_dict = {}
        for bar in bars_source:
            date_str = bar.get('date') or bar.get('month', '')
            if not date_str: continue
            yr = date_str[:4]
            mo = int(date_str[5:7])
            q_num = (mo - 1) // 3 + 1
            q_key = f"{yr}-Q{q_num}"
            if q_key not in quarterly_dict:
                quarterly_dict[q_key] = {
                    'quarter': q_key,
                    'time': bar.get('time', 0),
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar.get('volume', 0)
                }
            else:
                quarterly_dict[q_key]['high'] = max(quarterly_dict[q_key]['high'], bar['high'])
                quarterly_dict[q_key]['low'] = min(quarterly_dict[q_key]['low'], bar['low'])
                quarterly_dict[q_key]['close'] = bar['close']
                quarterly_dict[q_key]['volume'] += bar.get('volume', 0)
        sorted_quarters = [quarterly_dict[k] for k in sorted(quarterly_dict.keys())]
        if len(sorted_quarters) < 3: return None
        current_q = sorted_quarters[-1]
        last_q = sorted_quarters[-2]
        prev_q = sorted_quarters[-3]

        last_price = current_q['close']
        if last_price < 0.000001: return None

        dec = 8 if is_crypto and last_price < 0.001 else (6 if is_crypto and last_price < 0.01 else (4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)))

        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(current_q['high'], current_q['low'], current_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(last_q['high'], last_q['low'], last_q['close'], dec)
            target_label = f"Developing Next Qtr ({current_q['quarter']} QTD)"
            base_label = f"Current Qtr ({last_q['quarter']})"
            trigger_h = round(current_q['high'], dec)
            trigger_l = round(current_q['low'], dec)
            trigger_name_h = "QTD High (Buy)"
            trigger_name_l = "QTD Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(last_q['high'], last_q['low'], last_q['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_q['high'], prev_q['low'], prev_q['close'], dec)
            target_label = f"Current Qtr ({last_q['quarter']})"
            base_label = f"Previous Qtr ({prev_q['quarter']})"
            trigger_h = round(last_q['high'], dec)
            trigger_l = round(last_q['low'], dec)
            trigger_name_h = "PQ High (Buy)"
            trigger_name_l = "PQ Low (Sell)"

        base_prev_close = last_q['close']

    elif timeframe == "monthly":
        if len(monthly_bars) < 3: return None
        current_m = monthly_bars[-1]
        last_m = monthly_bars[-2]
        prev_m = monthly_bars[-3]
        
        last_price = current_m['close']
        if last_price < 0.000001: return None
        
        dec = 8 if is_crypto and last_price < 0.001 else (6 if is_crypto and last_price < 0.01 else (4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)))
        curr_m_lbl = current_m.get('month') or current_m.get('date', '')[:7]
        last_m_lbl = last_m.get('month') or last_m.get('date', '')[:7]
        prev_m_lbl = prev_m.get('month') or prev_m.get('date', '')[:7]

        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(current_m['high'], current_m['low'], current_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            target_label = f"Developing Next Month ({curr_m_lbl} MTD)"
            base_label = f"Current Month ({last_m_lbl})"
            trigger_h = round(current_m['high'], dec)
            trigger_l = round(current_m['low'], dec)
            trigger_name_h = "MTD High (Buy)"
            trigger_name_l = "MTD Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_m['high'], prev_m['low'], prev_m['close'], dec)
            target_label = f"Current Month ({last_m_lbl})"
            base_label = f"Previous Month ({prev_m_lbl})"
            trigger_h = round(last_m['high'], dec)
            trigger_l = round(last_m['low'], dec)
            trigger_name_h = "PM High (Buy)"
            trigger_name_l = "PM Low (Sell)"
            
        base_prev_close = last_m['close']

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
            oi_info = BINANCE_MGR.get_crypto_derivatives(symbol)
            if not vol_usd and oi_info:
                vol_usd = (oi_info.get("vol_24h_usd") or 0)
        else:
            oi_info = BINANCE_MGR.get_crypto_derivatives(symbol)
            vol_usd = (oi_info.get("vol_24h_usd") or 0) if oi_info else BINANCE_MGR.get_spot_volume(symbol)
            if not vol_usd:
                vol_usd = COINBASE_MGR.get_spot_volume(symbol)
        market_cap = vol_usd
        mc_formatted = (oi_info["vol_formatted"] + " 24h Vol") if (oi_info and oi_info.get("vol_formatted") and oi_info["vol_formatted"] != "-") else (BINANCE_MGR.format_usd(vol_usd) + " 24h Vol" if vol_usd > 0 else (COINBASE_MGR.format_usd(vol_usd) + " 24h Vol" if vol_usd > 0 else None))
    else:
        oi_info = None
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
        "oi_info": oi_info,
        "candles": daily_candles[-60:]
    }

def process_virgin_cpr_daily(symbol, max_days=10):
    """
    Scans for Daily Virgin CPRs formed within the last max_days completed sessions
    that have NEVER been tested or touched by any subsequent candle up to LTP.
    """
    is_crypto = symbol.endswith("USDT") or symbol.endswith("USDC") or ("-USD" in symbol)
    if is_crypto:
        if symbol.endswith("-USD"):
            monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
        else:
            monthly_bars, daily_candles = BINANCE_MGR.fetch_market_bars(symbol)
            if not daily_candles:
                monthly_bars, daily_candles = COINBASE_MGR.fetch_market_bars(symbol)
    else:
        monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
    if len(daily_candles) < max_days + 2:
        return []

    n = len(daily_candles)
    current_candle = daily_candles[-1]
    ltp = current_candle['close']
    if ltp < 0.000001:
        return []

    dec = 6 if is_crypto and ltp < 0.01 else (4 if is_crypto and ltp < 1.0 else (3 if is_crypto and ltp < 10.0 else 2))
    clean_symbol = symbol.replace("USDT", "").replace("USDC", "").replace("-USD", "").replace(".NS", "").replace("^", "")
    
    if is_crypto:
        if symbol.endswith("-USD"):
            vol_usd = COINBASE_MGR.get_spot_volume(symbol)
            oi_info = BINANCE_MGR.get_crypto_derivatives(symbol)
            if not vol_usd and oi_info:
                vol_usd = (oi_info.get("vol_24h_usd") or 0)
        else:
            oi_info = BINANCE_MGR.get_crypto_derivatives(symbol)
            vol_usd = (oi_info.get("vol_24h_usd") or 0) if oi_info else BINANCE_MGR.get_spot_volume(symbol)
            if not vol_usd:
                vol_usd = COINBASE_MGR.get_spot_volume(symbol)
        market_cap = vol_usd
        mc_formatted = (oi_info["vol_formatted"] + " 24h Vol") if (oi_info and oi_info.get("vol_formatted") and oi_info["vol_formatted"] != "-") else (BINANCE_MGR.format_usd(vol_usd) + " 24h Vol" if vol_usd > 0 else (COINBASE_MGR.format_usd(vol_usd) + " 24h Vol" if vol_usd > 0 else None))
    else:
        oi_info = None
        market_cap = None
        mc_formatted = None

    prev_c_for_change = daily_candles[-2]
    chg = round(ltp - prev_c_for_change['close'], dec)
    chg_pct = round((chg / prev_c_for_change['close']) * 100.0, 2) if prev_c_for_change['close'] > 0 else 0.0

    virgin_setups = []
    # Check candidate sessions from (n - 1 - max_days) to (n - 2)
    for i in range(max(1, n - 1 - max_days), n - 1):
        prev_c = daily_candles[i - 1]
        session_c = daily_candles[i]

        cpr = calculate_cpr_and_pivots(prev_c['high'], prev_c['low'], prev_c['close'], dec)
        top = cpr['cpr_top']
        bot = cpr['cpr_bot']

        # 1. Did price touch the CPR on session i itself?
        # A Virgin CPR means price NEVER touched [bot, top] during session i.
        if not (session_c['low'] > top or session_c['high'] < bot):
            continue

        # 2. Has any subsequent day from (i + 1) up to the current day (n - 1) touched [bot, top]?
        is_still_untested = True
        for k in range(i + 1, n):
            ck = daily_candles[k]
            if ck['high'] >= bot and ck['low'] <= top:
                is_still_untested = False
                break

        if is_still_untested:
            days_ago = (n - 1) - i
            p = cpr['p']
            dist_pct = round(((ltp - p) / p) * 100.0, 2)
            
            if ltp > top:
                role = "Demand / Support"
                role_class = "text-emerald-400 font-semibold"
                role_badge = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                plan = f"Bounce Candidate: Untested Support at [{bot} - {top}]"
            elif ltp < bot:
                role = "Supply / Resistance"
                role_class = "text-rose-400 font-semibold"
                role_badge = "bg-rose-500/20 text-rose-300 border-rose-500/40"
                plan = f"Rejection Candidate: Untested Resistance at [{bot} - {top}]"
            else:
                role = "Currently Testing!"
                role_class = "text-amber-400 font-semibold"
                role_badge = "bg-amber-500/20 text-amber-300 border-amber-500/40"
                plan = f"Live Test in Progress at [{bot} - {top}]"

            virgin_setups.append({
                "symbol": symbol,
                "clean_symbol": clean_symbol,
                "market_cap": market_cap,
                "mc_formatted": mc_formatted,
                "strategy": "virgin_cpr",
                "virgin_date": session_c['date'],
                "days_ago": days_ago,
                "ltp": round(ltp, dec),
                "change": chg,
                "change_pct": chg_pct,
                "curr_cpr": cpr,
                "dist_pct": dist_pct,
                "abs_dist": abs(dist_pct),
                "role": role,
                "role_class": role_class,
                "role_badge": role_badge,
                "plan": plan,
                "pm_high": round(session_c['high'], dec),
                "pm_low": round(session_c['low'], dec),
                "oi_info": oi_info,
                "candles": daily_candles[-60:]
            })

    return virgin_setups

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pivot Boss CPR Terminal • Inside Value & Virgin CPR</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    colors: {
                        navy: { 950: '#030712', 900: '#070d1e', 800: '#0f172a', 700: '#1e293b', 600: '#334155' }
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
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
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center shadow-lg shadow-orange-500/25 ring-1 ring-white/20">
                    <span class="text-black font-black font-mono text-xl" id="logo-letter">V</span>
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-amber-200 to-orange-400 bg-clip-text text-transparent flex items-center gap-2">
                        PIVOT BOSS CPR TERMINAL
                        <span id="header-mode-badge" class="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 font-mono font-medium border border-rose-500/30">BINANCE VIRGIN CPR (≤10D)</span>
                    </h1>
                    <p class="text-xs text-slate-400">Institutional Breakout & Untested Liquidity Engine (100% Official Binance API)</p>
                </div>
            </div>

            <!-- Controls: Strategy, Timeframe, Mode, Market -->
            <div class="flex flex-wrap items-center gap-3">
                
                <!-- Strategy Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setStrategy('virgin_cpr')" id="btn-strat-virgin" class="px-3 py-1.5 rounded-lg transition-all text-white bg-rose-600 font-bold shadow">
                        🛡️ Daily Virgin CPR (≤10d)
                    </button>
                    <button onclick="setStrategy('inside_value')" id="btn-strat-inside" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🎯 Inside Value CPR
                    </button>
                    <button onclick="setStrategy('oi_radar')" id="btn-strat-oi" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        ⚡ Crypto OI Radar
                    </button>
                </div>

                <!-- Sub-Controls for Inside Value (Hidden when Virgin CPR is active) -->
                <div id="inside-value-controls" class="hidden flex items-center gap-2">
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
                        🇮🇳 India
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
        <div class="p-4 rounded-2xl bg-gradient-to-r from-navy-900 via-navy-900 to-navy-950 border border-rose-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg" id="banner-card">
            <div class="flex items-start gap-3">
                <div class="text-2xl mt-0.5" id="banner-icon">🛡️</div>
                <div>
                    <h3 class="text-sm font-bold text-rose-300" id="banner-title">Daily Virgin CPR (Untested Liquidity Magnets ≤ 10 Days Old):</h3>
                    <p class="text-xs text-slate-300 mt-0.5" id="banner-desc">
                        Price has **never touched these CPR pivot ranges** since formation! Virgin CPRs below price act as **Major Support/Demand Zones**, while Virgin CPRs above price act as **Major Resistance/Supply Zones**.
                    </p>
                </div>
            </div>
            <div class="shrink-0 flex items-center gap-2 font-mono text-xs bg-navy-950/80 px-3 py-2 rounded-xl border border-navy-700">
                <span class="text-slate-400">Untested Setups:</span>
                <span id="coils-total" class="text-rose-400 font-bold text-base">0</span>
            </div>
        </div>

        <!-- Table View -->
        <div id="cpr-table-card" class="glass rounded-2xl border border-navy-700/80 overflow-hidden shadow-2xl flex-1 flex flex-col">
            <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex flex-wrap items-center justify-between gap-3">
                <span class="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2" id="table-title">
                    🛡️ Verified Daily Virgin CPRs (Sorted by Nearest Distance to LTP)
                </span>
                <div class="flex items-center gap-2">
                    <!-- Quick Filter Pills -->
                    <div id="quick-filters" class="flex flex-wrap items-center gap-1 bg-navy-950 p-1 rounded-xl border border-navy-700 text-[11px]">
                        <button onclick="setQuickFilter('inside')" id="qf-inside" class="px-2.5 py-1 rounded-lg bg-amber-400 text-black font-bold shadow">⚡ Inside Value</button>
                        <button onclick="setQuickFilter('all')" id="qf-all" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">All 2-Day Trends</button>
                        <button onclick="setQuickFilter('higher')" id="qf-higher" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🚀 Higher Value</button>
                        <button onclick="setQuickFilter('lower')" id="qf-lower" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🐻 Lower Value</button>
                        <button onclick="setQuickFilter('megacoil')" id="qf-megacoil" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">💥 MegaCoil (&gt;70%)</button>
                        <button onclick="setQuickFilter('squeeze')" id="qf-squeeze" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🔥 Squeeze (≥3x)</button>
                        <button onclick="setQuickFilter('magnet')" id="qf-magnet" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🎯 Magnet (&lt;2%)</button>
                    </div>
                    <input type="text" id="search-input" onkeyup="renderTable()" placeholder="Search symbol..." class="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl px-3.5 py-1.5 focus:outline-none focus:border-rose-500 w-40 transition shadow-inner">
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
                                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500 mb-3"></div>
                                <p>Scanning market universe for verified Daily Virgin CPRs...</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Crypto OI Radar View -->
        <div id="oi-radar-view" class="hidden flex flex-col gap-6">
            <!-- Search & Quick Chips Bar -->
            <div class="glass p-4 rounded-2xl border border-navy-700/80 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
                <div class="flex items-center gap-3 w-full md:w-auto flex-1">
                    <div class="text-xl">🔍</div>
                    <div class="relative flex-1 max-w-md">
                        <input type="text" id="oi-search-input" placeholder="Search coin (e.g. PEPE, SUI, BTC, SOL, NEAR, INJ, AERO...)" 
                               class="w-full bg-navy-950 border border-navy-700 text-white text-xs rounded-xl px-4 py-2.5 focus:outline-none focus:border-cyan-400 font-mono shadow-inner uppercase"
                               onkeydown="if(event.key==='Enter') searchOICoin()">
                    </div>
                    <button onclick="searchOICoin()" class="px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs transition shadow active:scale-95">
                        Inspect OI
                    </button>
                </div>
                <!-- Quick Preset Chips -->
                <div class="flex flex-wrap items-center gap-1.5 text-xs font-mono">
                    <span class="text-slate-400 text-[11px] font-sans mr-1">Quick:</span>
                    <button onclick="searchOICoin('BTC')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">BTC</button>
                    <button onclick="searchOICoin('ETH')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">ETH</button>
                    <button onclick="searchOICoin('SOL')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">SOL</button>
                    <button onclick="searchOICoin('PEPE')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-cyan-400 font-bold">PEPE</button>
                    <button onclick="searchOICoin('SUI')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">SUI</button>
                    <button onclick="searchOICoin('INJ')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">INJ</button>
                    <button onclick="searchOICoin('DOGE')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">DOGE</button>
                    <button onclick="searchOICoin('NEAR')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-slate-300">NEAR</button>
                    <button onclick="searchOICoin('AERO')" class="px-2 py-1 rounded-lg bg-navy-950 hover:bg-navy-800 border border-navy-700 text-rose-400">AERO</button>
                </div>
            </div>

            <!-- Searched Coin Deep Dive Hero Card -->
            <div id="oi-hero-card" class="glass rounded-2xl border border-cyan-500/30 overflow-hidden shadow-2xl p-5">
                <!-- Rendered dynamically -->
            </div>

            <!-- My Pinned OI Watchlist Card -->
            <div class="glass rounded-2xl border border-navy-700/80 overflow-hidden shadow-2xl flex flex-col">
                <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex flex-wrap items-center justify-between gap-3">
                    <span class="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                        📌 My Pinned OI Watchlist (Auto-Saved)
                    </span>
                    <span class="text-[11px] text-slate-400 font-sans">120s Live Auto-Refresh • Saved in your browser</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead class="bg-navy-950/90 border-b border-navy-700 text-slate-400 uppercase text-[11px]">
                            <tr>
                                <th class="py-3 px-4">Coin Pair</th>
                                <th class="py-3 px-4">Price & 24h Chg</th>
                                <th class="py-3 px-4">Open Interest (USD)</th>
                                <th class="py-3 px-4">24h Volume (USD)</th>
                                <th class="py-3 px-4">Squeeze Ratio & Risk</th>
                                <th class="py-3 px-4">8h Funding Rate</th>
                                <th class="py-3 px-4">Smart Money Signal</th>
                                <th class="py-3 px-4 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="oi-watchlist-body" class="divide-y divide-navy-700/50 font-mono">
                            <!-- Rendered dynamically -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Institutional Extremes Leaderboards (3-Column Grid) -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6" id="oi-leaderboards">
                <!-- Top Squeeze Ratios Card -->
                <div class="glass rounded-2xl border border-rose-500/30 overflow-hidden shadow-2xl flex flex-col">
                    <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex items-center justify-between">
                        <span class="text-xs font-bold text-rose-400 flex items-center gap-1.5">
                            ⚡ Top Squeeze Ratios (OI / 24h Vol)
                        </span>
                        <span class="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded font-mono">Min $300k Vol</span>
                    </div>
                    <div id="lb-squeeze" class="p-3 space-y-2 divide-y divide-navy-800/80 font-mono text-xs">
                        <!-- Injected -->
                    </div>
                </div>

                <!-- Most Negative Funding Card -->
                <div class="glass rounded-2xl border border-emerald-500/30 overflow-hidden shadow-2xl flex flex-col">
                    <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex items-center justify-between">
                        <span class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                            🚀 Short Squeeze Candidates (Negative Funding)
                        </span>
                        <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-mono">Shorts Paying</span>
                    </div>
                    <div id="lb-neg-funding" class="p-3 space-y-2 divide-y divide-navy-800/80 font-mono text-xs">
                        <!-- Injected -->
                    </div>
                </div>

                <!-- Open Interest Giants Card -->
                <div class="glass rounded-2xl border border-cyan-500/30 overflow-hidden shadow-2xl flex flex-col">
                    <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex items-center justify-between">
                        <span class="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                            👑 Largest Open Interest Giants
                        </span>
                        <span class="text-[10px] bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded font-mono">Market Leaders</span>
                    </div>
                    <div id="lb-top-oi" class="p-3 space-y-2 divide-y divide-navy-800/80 font-mono text-xs">
                        <!-- Injected -->
                    </div>
                </div>
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
                <div><span class="text-slate-400">Virgin TC:</span> <span id="modal-tc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Virgin Pivot (P):</span> <span id="modal-p" class="font-mono text-purple-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Virgin BC:</span> <span id="modal-bc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Status / Distance:</span> <span id="modal-info" class="font-mono text-amber-400 font-semibold"></span></div>
            </div>
            <div id="modal-crypto-row" class="hidden p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-navy-900 border-b border-navy-700 text-xs">
                <div><span class="text-slate-400">Open Interest:</span> <span id="modal-oi" class="font-mono text-cyan-400 font-bold ml-1"></span></div>
                <div><span class="text-slate-400">24h Volume:</span> <span id="modal-vol" class="font-mono text-slate-200 font-semibold ml-1"></span></div>
                <div><span class="text-slate-400">Funding Rate:</span> <span id="modal-funding" class="font-mono font-semibold ml-1"></span></div>
                <div><span class="text-slate-400">Squeeze Risk:</span> <span id="modal-squeeze" class="ml-1"></span></div>
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
                            PIVOT BOSS CRYPTO PLAYBOOK & STRATEGY ROADMAP
                            <span class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono border border-amber-500/40">MASTER ROADMAP</span>
                        </h2>
                        <p class="text-xs text-slate-400">Institutional confluence combining Virgin CPR, Inside Value, Open Interest, Squeeze Ratio & Funding</p>
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
                        <div class="text-rose-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🛡️ Virgin CPR (≤ 10d)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">A Central Pivot Range where price <strong class="text-white">never traded through</strong> during that daily session. Untested CPRs are institutional liquidity magnets.</p>
                        <div class="mt-2 text-[11px] text-emerald-400 font-medium">• Below LTP = High-Probability Demand / Support</div>
                        <div class="text-[11px] text-rose-400 font-medium">• Above LTP = High-Probability Supply / Resistance</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700">
                        <div class="text-amber-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>🎯 Inside Value (Daily, Monthly & Quarterly)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">The new CPR is <strong class="text-white">completely engulfed</strong> inside the prior period CPR. Extreme volatility compression coiling energy before an explosive directional breakout.</p>
                        <div class="mt-2 text-[11px] text-purple-300 font-medium">• Daily & Monthly: High-velocity intraweek trend expansions</div>
                        <div class="text-[11px] text-amber-300 font-medium">• Quarterly: Macro multi-month institutional mega trends</div>
                    </div>
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700">
                        <div class="text-cyan-400 font-bold text-sm mb-1.5 flex items-center gap-1.5">
                            <span>⚡ Squeeze Ratio & OI</span>
                        </div>
                        <p class="text-slate-400 leading-normal"><strong class="text-white">Squeeze Ratio = OI (USD) / 24h Volume (USD)</strong>. When &ge; 3.0x, open speculative leverage heavily outweighs real liquidity.</p>
                        <div class="mt-2 text-[11px] text-emerald-400 font-medium">• Negative Funding + Breakout = 🚀 Short Squeeze Target</div>
                        <div class="text-[11px] text-rose-400 font-medium">• Positive Funding + Breakdown = 💥 Long Flush Cascade</div>
                    </div>
                </div>

                <!-- 3 High Probability Crypto Setups -->
                <div class="p-5 rounded-xl bg-navy-950/80 border border-navy-700 space-y-4">
                    <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        🔥 3 Institutional Crypto Trade Setups (Rules & Execution)
                    </h3>

                    <!-- Strategy 1 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-rose-400 text-sm">Setup 1: Virgin CPR Magnet Bounce / Rejection (Mean Reversion)</span>
                            <span class="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded border border-rose-500/40">Win Rate: ~75%</span>
                        </div>
                        <p class="text-slate-300">When price trends away from a fresh Virgin CPR (1–10 days old), aggressive traders get overextended. Price gets pulled back like a rubber band into the untested zone.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry:</strong> Wait for price to touch Virgin CPR [BC • TC]. Enter on 5m/15m reversal candle closing outside the band.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> 0.4% beyond the outer CPR band (beyond BC for longs, beyond TC for shorts).</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Prior Day High/Low or Next Pivot (R1/S1). Risk/Reward: 1:2.5 to 1:4.</div>
                        </div>
                    </div>

                    <!-- Strategy 2 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-purple-400 text-sm">Setup 2: Inside Value Volatility Breakout + Squeeze (Trend Expansion)</span>
                            <span class="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/40">Momentum Explosions</span>
                        </div>
                        <p class="text-slate-300">Inside Value means the market had an indecision / coiling session. When combined with <strong class="text-cyan-300">Squeeze Ratio &ge; 2.0x</strong>, the breakout is fueled by aggressive forced market orders.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Long Entry:</strong> 15m candle close above PDH (Prior Day High). <br><strong class="text-white">Short Entry:</strong> 15m candle close below PDL.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> Back inside Today's Central Pivot (P) or opposite trigger.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Camarilla H4, Pivot R2, or R3. Expected gain: 6% – 18%.</div>
                        </div>
                    </div>

                    <!-- Strategy 3 -->
                    <div class="p-4 rounded-lg bg-navy-900 border border-navy-700/80 space-y-2">
                        <div class="flex items-center justify-between font-bold text-slate-200">
                            <span class="text-emerald-400 text-sm">Setup 3: Trapped Trader Liquidation Cascade (Short Squeeze / Long Flush)</span>
                            <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/40">High-Conviction Squeeze</span>
                        </div>
                        <p class="text-slate-300">Look for coins flagged with <strong class="text-emerald-400 font-mono">🚀 Short Squeeze Target</strong> (Negative Funding + High Squeeze Ratio &ge; 3.0x). Shorts are paying longs every 8 hours while price refuses to drop.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px]">
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Entry:</strong> Price reclaims and breaks above CPR Top Central (TC) or PDH.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Stop Loss:</strong> 0.5% below the breakout candle low.</div>
                            <div class="p-2.5 rounded bg-navy-950 border border-navy-800"><strong class="text-white">Take Profit:</strong> Trail behind 15m candle low until liquidation volume spike subsides.</div>
                        </div>
                    </div>
                </div>

                <!-- Daily Workflow & Rules -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700 space-y-2">
                        <div class="text-amber-400 font-bold text-sm flex items-center gap-1.5">
                            <span>📋 Daily 5-Minute Morning Screening Routine</span>
                        </div>
                        <ol class="list-decimal list-inside space-y-1 text-slate-400">
                            <li><strong class="text-white">Check BTC-USD first:</strong> If BTC is above CPR, focus on Long setups. If BTC is below CPR, focus on Short setups.</li>
                            <li><strong class="text-white">Click 🎯 Magnet (&lt;2%):</strong> See which coins are actively approaching or touching untested Virgin CPR levels right now.</li>
                            <li><strong class="text-white">Click ⚡ Squeeze (≥3x):</strong> Identify over-leveraged coins with pending liquidation squeeze risks.</li>
                            <li><strong class="text-white">Launch TV ↗:</strong> Open the selected coin directly in TradingView to fine-tune entry timing on the 5m chart.</li>
                        </ol>
                    </div>

                    <div class="p-4 rounded-xl bg-navy-950/70 border border-navy-700 space-y-2">
                        <div class="text-rose-400 font-bold text-sm flex items-center gap-1.5">
                            <span>🛡️ Golden Risk Management Rules</span>
                        </div>
                        <ul class="space-y-1 text-slate-400">
                            <li><strong class="text-white">Maximum 1% - 1.5% Risk:</strong> Never risk more than 1.5% of total portfolio on an individual altcoin position.</li>
                            <li><strong class="text-white">Respect Breakeven:</strong> Once price reaches 1.5R or tests S1/R1, immediately move Stop Loss to Breakeven.</li>
                            <li><strong class="text-white">Beware Weekend Chop:</strong> Virgin CPRs work best during high-volume sessions (Mon–Fri). Beware low-liquidity weekend stop hunts.</li>
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
        let currentStrategy = 'virgin_cpr'; // 'virgin_cpr' or 'inside_value'
        let currentTimeframe = 'daily';
        let currentMode = 'developing';
        let currentMarket = 'crypto_all';
        let currentMinMC = 0; // 0 for all Binance USDT pairs
        let currentSort = { column: 'abs_dist', ascending: true };
        let scanData = [];
        let chartInstance = null;
        let currentQuickFilter = 'inside'; // default to 'inside' on Inside Value strategy

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
            if (currentStrategy === 'inside_value') {
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
        }

        function syncQuickFilterUI() {
            ['all', 'inside', 'higher', 'lower', 'squeeze', 'magnet', 'megacoil'].forEach(id => {
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

        let currentOISearch = 'PEPE';
        let oiRadarData = null;

        function getStoredOIWatchlist() {
            try {
                const raw = localStorage.getItem('tracked_oi_coins');
                if (raw) return JSON.parse(raw);
            } catch (e) {}
            return ['BTC', 'ETH', 'SOL', 'PEPE', 'SUI', 'INJ', 'DOGE', 'NEAR', 'AERO'];
        }

        function saveStoredOIWatchlist(list) {
            try {
                localStorage.setItem('tracked_oi_coins', JSON.stringify(list));
            } catch (e) {}
        }

        async function loadOIRadar() {
            const heroEl = document.getElementById('oi-hero-card');
            if (heroEl) {
                heroEl.innerHTML = `
                    <div class="py-12 text-center text-slate-400 font-sans">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mb-3"></div>
                        <p>Loading real-time institutional derivatives metrics & leaderboards...</p>
                    </div>
                `;
            }
            const watchlist = getStoredOIWatchlist();
            try {
                const res = await fetch(`/api/crypto/oi?search=${encodeURIComponent(currentOISearch)}&watchlist=${encodeURIComponent(watchlist.join(','))}`);
                const data = await res.json();
                oiRadarData = data;
                renderOIHero(data.searched_coin);
                renderOIWatchlist(data.watchlist_coins);
                renderOILeaderboards(data.leaderboards);
            } catch (e) {
                if (heroEl) heroEl.innerHTML = `<div class="py-8 text-center text-rose-400">Failed to load OI data. Please retry.</div>`;
            }
        }

        function searchOICoin(sym) {
            const input = document.getElementById('oi-search-input');
            const target = (sym || (input ? input.value : '') || 'PEPE').trim().toUpperCase();
            if (!target) return;
            currentOISearch = target;
            if (input) input.value = target;
            loadOIRadar();
        }

        function togglePinCoin(sym) {
            let list = getStoredOIWatchlist();
            const clean = sym.toUpperCase();
            if (list.includes(clean)) {
                list = list.filter(s => s !== clean);
            } else {
                list.push(clean);
            }
            saveStoredOIWatchlist(list);
            loadOIRadar();
        }

        function renderOIHero(coin) {
            const heroEl = document.getElementById('oi-hero-card');
            if (!heroEl) return;
            if (!coin) {
                heroEl.innerHTML = `
                    <div class="py-8 text-center text-slate-400">
                        <div class="text-2xl mb-1">🔍</div>
                        <p class="text-sm font-semibold text-slate-200">No futures contract found for "${currentOISearch}".</p>
                        <p class="text-xs text-slate-500 mt-1">Try BTC, ETH, SOL, PEPE, SUI, DOGE, NEAR, AERO...</p>
                    </div>
                `;
                return;
            }

            const list = getStoredOIWatchlist();
            const isPinned = list.includes(coin.clean_symbol);
            const chgColor = coin.change_pct >= 0 ? 'text-emerald-400' : 'text-rose-400';
            const chgSign = coin.change_pct >= 0 ? '+' : '';
            const sqRatio = coin.squeeze_ratio || 0;
            const sqBarPct = Math.min(100, Math.round((sqRatio / 5.0) * 100));

            heroEl.innerHTML = `
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-navy-700/80">
                    <div class="flex items-center gap-3">
                        <div class="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-black text-base font-mono shadow-lg shadow-cyan-500/20">
                            ${coin.clean_symbol.slice(0, 3)}
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h2 class="text-lg font-bold text-white font-mono tracking-tight">${coin.clean_symbol} / USDT</h2>
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${coin.squeeze_class} font-sans">
                                    ${coin.squeeze_badge}
                                </span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${coin.oi_signal_class} font-sans">
                                    ${coin.oi_signal}
                                </span>
                            </div>
                            <div class="flex items-center gap-3 text-xs mt-0.5 font-mono">
                                <span class="text-slate-100 font-bold">$${coin.last_price.toLocaleString()}</span>
                                <span class="${chgColor} font-semibold">${chgSign}${coin.change_pct}% (24h)</span>
                                <span class="text-slate-500 text-[11px] font-sans">Mark: $${coin.mark_price.toLocaleString()} • Index: $${coin.index_price.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="togglePinCoin('${coin.clean_symbol}')" class="px-3.5 py-1.5 rounded-xl border ${isPinned ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' : 'bg-navy-950 text-slate-300 border-navy-700 hover:text-white'} text-xs font-semibold font-sans transition flex items-center gap-1.5 shadow">
                            <span>${isPinned ? '📌 Pinned' : '+ Pin to Watchlist'}</span>
                        </button>
                        <a href="https://www.tradingview.com/chart/?symbol=BINANCE:${coin.clean_symbol}USDT" target="_blank" rel="noopener" class="px-3 py-1.5 rounded-xl bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                            TV ↗
                        </a>
                    </div>
                </div>

                <!-- 6 Metric Cards Grid -->
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-4 text-xs font-mono">
                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">Open Interest (USD)</div>
                        <div class="text-cyan-400 font-bold text-sm mt-1">${coin.oi_formatted}</div>
                        <div class="text-[10px] text-slate-500 font-sans mt-0.5">${coin.contracts_count.toLocaleString()} contracts</div>
                    </div>

                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">24h Trading Vol</div>
                        <div class="text-slate-100 font-bold text-sm mt-1">${coin.vol_formatted}</div>
                        <div class="text-[10px] text-slate-500 font-sans mt-0.5">USD Turnover</div>
                    </div>

                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">Squeeze Ratio</div>
                        <div class="text-amber-400 font-bold text-sm mt-1">${coin.squeeze_ratio}x</div>
                        <div class="w-full bg-navy-900 rounded-full h-1.5 mt-1 overflow-hidden">
                            <div class="bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500 h-1.5 rounded-full" style="width: ${sqBarPct}%"></div>
                        </div>
                    </div>

                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">8h Funding Rate</div>
                        <div class="font-bold text-sm mt-1 ${coin.funding_pct > 0 ? 'text-emerald-400' : (coin.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${coin.funding_formatted}</div>
                        <div class="text-[10px] text-slate-400 font-sans mt-0.5">${coin.funding_bias} (${coin.annualized_funding_pct} APR)</div>
                    </div>

                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">Futures Basis</div>
                        <div class="text-purple-300 font-bold text-sm mt-1">${coin.basis_pct > 0 ? '+' : ''}${coin.basis_pct}%</div>
                        <div class="text-[10px] text-slate-500 font-sans mt-0.5">${coin.basis_pct >= 0 ? 'Futures Premium' : 'Futures Discount'}</div>
                    </div>

                    <div class="p-3 rounded-xl bg-navy-950/70 border border-navy-800">
                        <div class="text-[11px] text-slate-400 font-sans">Direction Risk</div>
                        <div class="text-xs font-bold mt-1 ${coin.squeeze_dir_class}">${coin.squeeze_direction}</div>
                        <div class="text-[10px] text-slate-500 font-sans mt-0.5 leading-tight">${coin.oi_signal_desc}</div>
                    </div>
                </div>
            `;
        }

        function renderOIWatchlist(coins) {
            const tbody = document.getElementById('oi-watchlist-body');
            if (!tbody) return;
            if (!coins || coins.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-10 text-slate-400 font-sans">
                            No coins pinned in your watchlist yet. Search a coin above and click "+ Pin to Watchlist".
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = coins.map(coin => {
                const chgColor = coin.change_pct >= 0 ? 'text-emerald-400' : 'text-rose-400';
                const chgSign = coin.change_pct >= 0 ? '+' : '';
                return `
                    <tr class="hover:bg-navy-800/80 transition group cursor-pointer" onclick="searchOICoin('${coin.clean_symbol}')">
                        <td class="py-3 px-4">
                            <div class="font-bold text-white text-sm">${coin.clean_symbol}</div>
                            <div class="text-[10px] text-slate-500 font-sans">${coin.symbol}</div>
                        </td>
                        <td class="py-3 px-4">
                            <div class="font-bold text-slate-100">$${coin.last_price.toLocaleString()}</div>
                            <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${coin.change_pct}%</div>
                        </td>
                        <td class="py-3 px-4">
                            <div class="text-cyan-400 font-bold">${coin.oi_formatted}</div>
                            <div class="text-[10px] text-slate-400 font-sans">${coin.contracts_count.toLocaleString()} cntr</div>
                        </td>
                        <td class="py-3 px-4">
                            <div class="text-slate-200 font-semibold">${coin.vol_formatted}</div>
                        </td>
                        <td class="py-3 px-4">
                            <div><span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${coin.squeeze_class} font-sans">${coin.squeeze_badge} (${coin.squeeze_ratio}x)</span></div>
                            <div class="text-[10px] ${coin.squeeze_dir_class} font-sans mt-0.5">${coin.squeeze_direction}</div>
                        </td>
                        <td class="py-3 px-4">
                            <div class="font-semibold ${coin.funding_pct > 0 ? 'text-emerald-400' : (coin.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${coin.funding_formatted}</div>
                            <div class="text-[10px] text-slate-500 font-sans">${coin.funding_bias}</div>
                        </td>
                        <td class="py-3 px-4">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${coin.oi_signal_class} font-sans">
                                ${coin.oi_signal}
                            </span>
                        </td>
                        <td class="py-3 px-4 text-center" onclick="event.stopPropagation()">
                            <div class="flex items-center justify-center gap-1.5">
                                <a href="https://www.tradingview.com/chart/?symbol=BINANCE:${coin.clean_symbol}USDT" target="_blank" rel="noopener" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                    TV ↗
                                </a>
                                <button onclick="togglePinCoin('${coin.clean_symbol}')" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-rose-500 hover:text-white text-slate-400 font-sans text-xs transition border border-navy-700 shadow" title="Remove from watchlist">
                                    ✕
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function renderOILeaderboards(lb) {
            if (!lb) return;

            const elSq = document.getElementById('lb-squeeze');
            if (elSq) {
                elSq.innerHTML = (lb.top_squeeze || []).map(coin => `
                    <div class="flex items-center justify-between py-1.5 cursor-pointer hover:bg-navy-800/50 px-1 rounded transition" onclick="searchOICoin('${coin.clean_symbol}')">
                        <div>
                            <span class="text-white font-bold">${coin.clean_symbol}</span>
                            <span class="text-[10px] text-slate-400 font-sans ml-1">${coin.vol_formatted} Vol</span>
                        </div>
                        <div class="text-right">
                            <span class="text-rose-400 font-bold">${coin.squeeze_ratio}x</span>
                            <div class="text-[10px] text-cyan-400 font-sans">OI: ${coin.oi_formatted}</div>
                        </div>
                    </div>
                `).join('');
            }

            const elNeg = document.getElementById('lb-neg-funding');
            if (elNeg) {
                elNeg.innerHTML = (lb.top_neg_funding || []).map(coin => `
                    <div class="flex items-center justify-between py-1.5 cursor-pointer hover:bg-navy-800/50 px-1 rounded transition" onclick="searchOICoin('${coin.clean_symbol}')">
                        <div>
                            <span class="text-white font-bold">${coin.clean_symbol}</span>
                            <span class="text-[10px] text-slate-400 font-sans ml-1">${coin.squeeze_ratio}x sq</span>
                        </div>
                        <div class="text-right">
                            <span class="text-emerald-400 font-bold">${coin.funding_formatted}</span>
                            <div class="text-[10px] text-slate-400 font-sans">OI: ${coin.oi_formatted}</div>
                        </div>
                    </div>
                `).join('');
            }

            const elTop = document.getElementById('lb-top-oi');
            if (elTop) {
                elTop.innerHTML = (lb.top_oi || []).map(coin => `
                    <div class="flex items-center justify-between py-1.5 cursor-pointer hover:bg-navy-800/50 px-1 rounded transition" onclick="searchOICoin('${coin.clean_symbol}')">
                        <div>
                            <span class="text-white font-bold">${coin.clean_symbol}</span>
                            <span class="text-[10px] text-slate-400 font-sans ml-1">${coin.funding_formatted}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-cyan-400 font-bold">${coin.oi_formatted}</span>
                            <div class="text-[10px] text-slate-400 font-sans">Vol: ${coin.vol_formatted}</div>
                        </div>
                    </div>
                `).join('');
            }
        }

        function updateUIState() {
            const btnVirgin = document.getElementById('btn-strat-virgin');
            const btnInside = document.getElementById('btn-strat-inside');
            const btnOi = document.getElementById('btn-strat-oi');
            const ivControls = document.getElementById('inside-value-controls');
            const cprTable = document.getElementById('cpr-table-card');
            const oiRadarView = document.getElementById('oi-radar-view');
            const badge = document.getElementById('header-mode-badge');
            const bannerCard = document.getElementById('banner-card');
            const bannerTitle = document.getElementById('banner-title');
            const bannerDesc = document.getElementById('banner-desc');
            const bannerIcon = document.getElementById('banner-icon');
            const tableTitle = document.getElementById('table-title');
            const logo = document.getElementById('logo-letter');

            if (currentStrategy === 'oi_radar') {
                btnOi.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-cyan-400 font-bold shadow';
                btnVirgin.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                btnInside.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                ivControls.classList.add('hidden');
                cprTable.classList.add('hidden');
                oiRadarView.classList.remove('hidden');

                logo.innerText = 'OI';
                badge.innerText = 'CRYPTO OI RADAR (1,000+ FUTURES)';
                badge.className = 'px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-300 font-mono font-medium border border-cyan-500/30';

                bannerCard.className = 'p-4 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-navy-900 to-navy-900 border border-cyan-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg';
                bannerIcon.innerText = '⚡';
                bannerTitle.className = 'text-sm font-bold text-cyan-300';
                bannerTitle.innerText = 'Institutional Crypto Open Interest (OI) & Squeeze Radar:';
                bannerDesc.innerHTML = 'Track live open interest capital, 24h leverage squeeze ratios, and 8h funding rates across 1,000+ liquid futures pairs. Search any coin or pin to your custom watchlist.';
                document.getElementById('coils-total').innerText = '1,024+';
                document.getElementById('coils-total').className = 'text-cyan-400 font-bold text-base';
            } else {
                cprTable.classList.remove('hidden');
                oiRadarView.classList.add('hidden');
                btnOi.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                document.getElementById('coils-total').className = currentStrategy === 'virgin_cpr' ? 'text-rose-400 font-bold text-base' : 'text-amber-400 font-bold text-base';

                if (currentStrategy === 'virgin_cpr') {
                    btnVirgin.className = 'px-3 py-1.5 rounded-lg transition-all text-white bg-rose-600 font-bold shadow';
                    btnInside.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    ivControls.classList.add('hidden');
                    
                    logo.innerText = 'V';
                    badge.innerText = 'DAILY VIRGIN CPR (≤10D)';
                    badge.className = 'px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 font-mono font-medium border border-rose-500/30';

                    bannerCard.className = 'p-4 rounded-2xl bg-gradient-to-r from-navy-900 via-navy-900 to-navy-950 border border-rose-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg';
                    bannerIcon.innerText = '🛡️';
                    bannerTitle.className = 'text-sm font-bold text-rose-300';
                    bannerTitle.innerText = 'Daily Virgin CPR (Untested Liquidity Magnets ≤ 10 Days Old):';
                    bannerDesc.innerHTML = 'Price has <strong>never touched these CPR pivot ranges</strong> since formation! Untested CPRs below price act as <strong>Major Demand/Support</strong>, and untested CPRs above price act as <strong>Major Supply/Resistance</strong>.';
                    tableTitle.innerText = '🛡️ Verified Daily Virgin CPRs (Sorted by Nearest Distance to LTP)';
                    tableTitle.className = 'text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2';
                } else {
                    btnInside.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                    btnVirgin.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    ivControls.classList.remove('hidden');

                    // Timeframe buttons
                    const btnDaily = document.getElementById('btn-tf-daily');
                    const btnMonthly = document.getElementById('btn-tf-monthly');
                    const btnQuarterly = document.getElementById('btn-tf-quarterly');
                    [btnDaily, btnMonthly, btnQuarterly].forEach(b => {
                        if (b) b.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    });

                    if (currentTimeframe === 'daily') {
                        if (btnDaily) btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                        logo.innerText = 'D';
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
                }

                // Crypto market banner adjustments
                if (currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase') {
                    const isCoinbase = currentMarket === 'crypto_coinbase';
                    const exchangeName = isCoinbase ? 'Coinbase' : 'Binance';
                    const totalLabel = isCoinbase ? '400+ Pairs' : '700+ Pairs';
                    const volLabel = currentMinMC >= 1000000 ? `$${(currentMinMC/1e6).toFixed(0)}M` : (currentMinMC > 0 ? `$${currentMinMC}` : 'All');
                    if (currentStrategy === 'virgin_cpr') {
                        tableTitle.innerText = `🛡️ Verified ${exchangeName} Daily Virgin CPRs (${volLabel === 'All' ? totalLabel : `24h Vol ≥ ${volLabel}`})`;
                        bannerDesc.innerHTML = `Price has <strong>never touched these CPR pivot ranges</strong> since formation! Tracking ${exchangeName} pairs with <strong>${volLabel === 'All' ? 'All Liquid Pairs' : `24h Turnover ≥ ${volLabel}`}</strong> via official ${exchangeName} API.`;
                    } else {
                        const tfName = currentTimeframe === 'daily' ? 'DAILY' : (currentTimeframe === 'monthly' ? 'MONTHLY' : 'QUARTERLY');
                        const modeName = currentMode === 'developing' ? 'DEVELOPING' : 'ACTIVE';
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
                        } else {
                            tableTitle.innerText = `🔥 Verified ${exchangeName} ${tfName} ${modeName} Inside Value (${volLabel === 'All' ? totalLabel : `24h Vol ≥ ${volLabel}`})`;
                            bannerDesc.innerHTML = `Scanning volatility compression coils across <strong>${exchangeName} Pairs</strong> with <strong>Live Pivot Boss CPR Calculations</strong>.`;
                        }
                    }
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
            if ((currentMarket === 'crypto_all' || currentMarket === 'crypto_coinbase') && currentStrategy !== 'oi_radar') {
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

        function setStrategy(strat) {
            currentStrategy = strat;
            if (strat === 'virgin_cpr') {
                currentSort = { column: 'abs_dist', ascending: true };
                currentQuickFilter = 'all';
            } else if (strat === 'inside_value') {
                currentSort = { column: 'compression_pct', ascending: false };
                currentQuickFilter = 'inside';
            }
            syncQuickFilterUI();
            updateUIState();
            if (strat === 'oi_radar') {
                loadOIRadar();
            } else {
                runScan();
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

            // Set Table Head according to strategy & market
            if (currentStrategy === 'virgin_cpr') {
                if (isCrypto) {
                    thead.innerHTML = `
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('market_cap')">Coin Pair & 24h Vol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('days_ago')">Virgin Date & Age ↕</th>
                            <th class="py-3.5 px-4">Untested CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('abs_dist')">Dist to LTP ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('oi_usd')">Open Interest ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('squeeze_ratio')">Squeeze Risk ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('funding_pct')">Funding Rate ↕</th>
                            <th class="py-3.5 px-4 text-center">Chart</th>
                        </tr>
                    `;
                } else {
                    thead.innerHTML = `
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Asset Symbol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('days_ago')">Virgin Date & Age ↕</th>
                            <th class="py-3.5 px-4">Untested CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('role')">Role (Demand / Supply) ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('abs_dist')">Distance to LTP ↕</th>
                            <th class="py-3.5 px-4">Trade Plan</th>
                            <th class="py-3.5 px-4 text-center">Chart</th>
                        </tr>
                    `;
                }
            } else {
                if (isCrypto) {
                    thead.innerHTML = `
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('market_cap')">Coin Pair & 24h Vol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('relationship')">CPR Relationship ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('cpr_width_pct')">Target CPR Band & Width ↕</th>
                            <th class="py-3.5 px-4">Breakout Triggers</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('oi_usd')">Open Interest ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('squeeze_ratio')">Squeeze Risk ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('funding_pct')">Funding Rate ↕</th>
                            <th class="py-3.5 px-4 text-center">Chart</th>
                        </tr>
                    `;
                } else {
                    thead.innerHTML = `
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Asset Symbol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('compression_pct')">Compression % ↕</th>
                            <th class="py-3.5 px-4">Target CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4">Base CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4">Breakout Triggers</th>
                            <th class="py-3.5 px-4">Targets (S1 • R1)</th>
                            <th class="py-3.5 px-4 text-center">Chart</th>
                        </tr>
                    `;
                }
            }

            tbody.innerHTML = `
                <tr>
                    <td colspan="${isCrypto ? 9 : 8}" class="text-center py-16 text-slate-400 font-sans">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500 mb-3"></div>
                        <p>Scanning ${currentMarket.toUpperCase()} for ${currentStrategy === 'virgin_cpr' ? 'Daily Virgin CPRs' : 'Inside Value CPRs'}...</p>
                    </td>
                </tr>
            `;

            try {
                const response = await fetch(`/api/scan?strategy=${currentStrategy}&market=${currentMarket}&timeframe=${currentTimeframe}&mode=${currentMode}&min_mc=${currentMinMC}`);
                const data = await response.json();
                scanData = data.results || [];
                document.getElementById('coils-total').innerText = scanData.length;
                updateFilterCounts();
                renderTable();
            } catch (err) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="${isCrypto ? 9 : 8}" class="text-center py-12 text-rose-400 font-sans">
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
                currentSort.ascending = (column === 'abs_dist' || column === 'days_ago') ? true : false;
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
                } else if (currentQuickFilter === 'squeeze') {
                    if (!item.oi_info || item.oi_info.squeeze_ratio < 3.0) return false;
                } else if (currentQuickFilter === 'magnet') {
                    if ((item.abs_dist === undefined ? 999 : item.abs_dist) > 2.0) return false;
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
                } else if (currentSort.column === 'days_ago') {
                    valA = a.days_ago || 0; valB = b.days_ago || 0;
                } else if (currentSort.column === 'abs_dist') {
                    valA = a.abs_dist || 0; valB = b.abs_dist || 0;
                } else if (currentSort.column === 'compression_pct') {
                    valA = a.compression_pct || 0; valB = b.compression_pct || 0;
                } else if (currentSort.column === 'cpr_width_pct') {
                    valA = a.cpr_width_pct !== undefined ? a.cpr_width_pct : (a.curr_cpr ? a.curr_cpr.cpr_width_pct : 0);
                    valB = b.cpr_width_pct !== undefined ? b.cpr_width_pct : (b.curr_cpr ? b.curr_cpr.cpr_width_pct : 0);
                } else if (currentSort.column === 'relationship') {
                    valA = a.relationship || ''; valB = b.relationship || '';
                } else if (currentSort.column === 'market_cap') {
                    valA = a.market_cap || 0; valB = b.market_cap || 0;
                } else if (currentSort.column === 'role') {
                    valA = a.role || ''; valB = b.role || '';
                } else if (currentSort.column === 'oi_usd') {
                    valA = (a.oi_info && a.oi_info.oi_usd) || 0;
                    valB = (b.oi_info && b.oi_info.oi_usd) || 0;
                } else if (currentSort.column === 'squeeze_ratio') {
                    valA = (a.oi_info && a.oi_info.squeeze_ratio) || 0;
                    valB = (b.oi_info && b.oi_info.squeeze_ratio) || 0;
                } else if (currentSort.column === 'funding_pct') {
                    valA = (a.oi_info && a.oi_info.funding_pct) || 0;
                    valB = (b.oi_info && b.oi_info.funding_pct) || 0;
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
                         Market Context: The crypto market had a coordinated directional drop yesterday, so ${lowerCount} coins formed <strong>Lower Value CPRs</strong> today.
                       </span>
                       <div class="mt-4 flex flex-wrap items-center justify-center gap-3">
                         <button onclick="setMode('developing')" class="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs shadow transition-all cursor-pointer">⚡ Switch to Tomorrow (Developing Inside Value)</button>
                         <button onclick="setQuickFilter('all')" class="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow transition-all cursor-pointer">📊 View All ${scanData.length} 2-Day Trends</button>
                         <button onclick="setQuickFilter('lower')" class="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow transition-all cursor-pointer">🐻 View ${lowerCount} Lower Value Trends</button>
                       </div>`
                    : `No matching setups found right now.<br><span class="text-xs text-slate-500 mt-1 inline-block">Try switching filter pill, market or strategy.</span>`;
                tbody.innerHTML = `
                    <tr>
                        <td colspan="${isCrypto ? 9 : 8}" class="text-center py-16 text-slate-400 font-sans">
                            <div class="text-3xl mb-2">🔍</div>
                            <p class="text-sm font-semibold text-slate-300">${emptyMsg}</p>
                        </td>
                    </tr>
                `;
                return;
            }

            if (currentStrategy === 'virgin_cpr') {
                tbody.innerHTML = filtered.map(item => {
                    const chgColor = item.change >= 0 ? 'text-emerald-400' : 'text-rose-400';
                    const chgSign = item.change >= 0 ? '+' : '';
                    const distColor = item.dist_pct > 0 ? 'text-emerald-400' : 'text-rose-400';
                    const tvUrl = isCrypto ? `https://www.tradingview.com/chart/?symbol=${tvExchange}:${currentMarket === 'crypto_coinbase' ? `${item.clean_symbol}USD` : `${item.clean_symbol}USDT`}` : '';

                    if (isCrypto) {
                        let radarBadge = '';
                        if (item.abs_dist <= 0.75) {
                            radarBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/30 text-emerald-300 border border-emerald-400/50 animate-pulse font-sans"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Live Test</span></div>`;
                        } else if (item.abs_dist <= 2.0) {
                            radarBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30 font-sans"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Imminent</span></div>`;
                        }

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
                                    <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${item.change} (${chgSign}${item.change_pct}%)</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="text-white font-semibold font-mono">${item.virgin_date}</div>
                                    <div class="text-rose-400 font-sans text-[10px] font-medium">${item.days_ago} ${item.days_ago === 1 ? 'day' : 'days'} ago</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="text-slate-200 font-semibold"><span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_bot)}</span> • <span class="text-purple-400 font-bold font-mono">${formatCryptoNum(item.curr_cpr.p)}</span> • <span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_top)}</span></div>
                                    <div class="text-[10px] text-slate-400 font-sans mt-0.5">Width: ${item.curr_cpr.cpr_width_pct}%</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="${distColor} font-bold font-mono">${item.dist_pct > 0 ? '+' : ''}${item.dist_pct}%</div>
                                    <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${item.role_badge} font-sans mt-0.5">
                                        ${item.role}
                                    </span>
                                    ${radarBadge}
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="text-cyan-400 font-bold font-mono">${item.oi_info.oi_formatted}</div>
                                        <div class="text-[10px] text-slate-400 font-mono">Vol: ${item.oi_info.vol_formatted}</div>
                                    ` : `<span class="text-slate-500 font-mono">-</span>`}
                                </td>
                                <td class="py-3.5 px-4">
                                    ${item.oi_info ? `
                                        <div><span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.oi_info.squeeze_class} font-sans">${item.oi_info.squeeze_badge} (${item.oi_info.squeeze_ratio}x)</span></div>
                                        <div class="text-[10px] ${item.oi_info.squeeze_dir_class} font-sans mt-0.5">${item.oi_info.squeeze_direction}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="font-mono font-semibold ${item.oi_info.funding_pct > 0 ? 'text-emerald-400' : (item.oi_info.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${item.oi_info.funding_formatted}</div>
                                        <div class="text-[10px] text-slate-500 font-sans">${item.oi_info.funding_bias}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-center">
                                    <div class="flex items-center justify-center gap-1.5">
                                        <a href="${tvUrl}" target="_blank" rel="noopener" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold" title="Open TradingView">
                                            TV ↗
                                        </a>
                                        <button onclick="openChart('${item.symbol}', '${item.virgin_date}')" class="px-2.5 py-1 rounded-lg bg-navy-800 hover:bg-rose-500 hover:text-white text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
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
                                <div class="font-bold text-slate-100">${item.ltp.toLocaleString()}</div>
                                <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${item.change} (${chgSign}${item.change_pct}%)</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-white font-semibold">${item.virgin_date}</div>
                                <div class="text-rose-400 font-sans text-[10px] font-medium">${item.days_ago} ${item.days_ago === 1 ? 'day' : 'days'} ago</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-slate-200 font-semibold"><span class="text-blue-400">${item.curr_cpr.cpr_bot}</span> • <span class="text-purple-400 font-bold">${item.curr_cpr.p}</span> • <span class="text-blue-400">${item.curr_cpr.cpr_top}</span></div>
                                <div class="text-[10px] text-slate-400 font-sans mt-0.5">Width: ${item.curr_cpr.cpr_width_pct}%</div>
                            </td>
                            <td class="py-3.5 px-4">
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.role_badge} font-sans">
                                    ${item.role}
                                </span>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="${distColor} font-bold">${item.dist_pct > 0 ? '+' : ''}${item.dist_pct}%</div>
                                <div class="text-[10px] text-slate-400 font-sans">to Virgin Pivot (${item.curr_cpr.p})</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px] font-sans text-slate-300">
                                ${item.plan}
                            </td>
                            <td class="py-3.5 px-4 text-center">
                                <button onclick="openChart('${item.symbol}', '${item.virgin_date}')" class="px-3 py-1 rounded-lg bg-navy-800 hover:bg-rose-500 hover:text-white text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                    View
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            } else {
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
                                    <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${item.change} (${chgSign}${item.change_pct}%)</div>
                                </td>
                                <td class="py-3.5 px-4">
                                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.rel_badge || item.quality_tag.badge} font-sans">
                                        ${item.rel_icon || '⚡'} ${item.relationship || item.quality_tag.text}
                                    </span>
                                    <div class="text-[10px] font-sans mt-0.5 ${item.compression_pct > 0 ? 'text-amber-400' : 'text-slate-400'}">${item.compression_pct > 0 ? `-${item.compression_pct}% Compressed` : `+${Math.abs(item.compression_pct)}% Wider`}</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="text-slate-200 font-semibold"><span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_bot)}</span> • <span class="text-purple-400 font-bold font-mono">${formatCryptoNum(item.curr_cpr.p)}</span> • <span class="text-blue-400 font-mono">${formatCryptoNum(item.curr_cpr.cpr_top)}</span></div>
                                    <div class="text-[10px] text-slate-400 font-sans mt-0.5">Base CPR: <span class="text-slate-300 font-mono">${formatCryptoNum(item.prev_cpr.cpr_bot)} • ${formatCryptoNum(item.prev_cpr.p)} • ${formatCryptoNum(item.prev_cpr.cpr_top)}</span></div>
                                    <div class="text-[10px] text-cyan-400 font-sans mt-0.5 font-medium">Width: ${(item.cpr_width_pct !== undefined ? item.cpr_width_pct : item.curr_cpr.cpr_width_pct)}% (${item.compression_pct > 0 ? `-${item.compression_pct}% compressed` : `+${Math.abs(item.compression_pct)}% wider`})</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div><span class="text-slate-400 font-sans">${item.trigger_name_h}:</span> <span class="text-emerald-400 font-bold font-mono">${formatCryptoNum(item.pm_high)}</span></div>
                                    <div><span class="text-slate-400 font-sans">${item.trigger_name_l}:</span> <span class="text-rose-400 font-bold font-mono">${formatCryptoNum(item.pm_low)}</span></div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="text-cyan-400 font-bold font-mono">${item.oi_info.oi_formatted}</div>
                                        <div class="text-[10px] text-slate-400 font-mono">Vol: ${item.oi_info.vol_formatted}</div>
                                    ` : `<span class="text-slate-500 font-mono">-</span>`}
                                </td>
                                <td class="py-3.5 px-4">
                                    ${item.oi_info ? `
                                        <div><span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.oi_info.squeeze_class} font-sans">${item.oi_info.squeeze_badge} (${item.oi_info.squeeze_ratio}x)</span></div>
                                        <div class="text-[10px] ${item.oi_info.squeeze_dir_class} font-sans mt-0.5">${item.oi_info.squeeze_direction}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="font-mono font-semibold ${item.oi_info.funding_pct > 0 ? 'text-emerald-400' : (item.oi_info.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${item.oi_info.funding_formatted}</div>
                                        <div class="text-[10px] text-slate-500 font-sans">${item.oi_info.funding_bias}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
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
                                <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${item.change} (${chgSign}${item.change_pct}%)</div>
                            </td>
                            <td class="py-3.5 px-4">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${item.quality_tag.badge} font-sans">
                                    ⚡ -${item.compression_pct}% Compressed
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
                                <div><span class="text-slate-400 font-sans">R1:</span> <span class="text-emerald-400 font-medium">${item.curr_cpr.r1}</span></div>
                                <div><span class="text-slate-400 font-sans">S1:</span> <span class="text-rose-400 font-medium">${item.curr_cpr.s1}</span></div>
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
        }

        function openChart(symbol, optDate) {
            const item = scanData.find(s => s.symbol === symbol && (!optDate || s.virgin_date === optDate));
            if (!item) return;

            document.getElementById('modal-symbol').innerText = `${item.clean_symbol} (${item.symbol})`;
            const badge = document.getElementById('modal-badge');
            
            if (item.strategy === 'virgin_cpr') {
                badge.innerText = `🛡️ Untested Virgin CPR (${item.virgin_date} • ${item.days_ago}d ago)`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border ${item.role_badge}`;
                document.getElementById('modal-info').innerText = `${item.role} (${item.dist_pct}%)`;
            } else {
                if (item.is_strict || item.relationship === 'Inside Value') {
                    badge.innerText = `⚡ Inside Value: -${item.compression_pct}% Compressed`;
                    badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border bg-purple-500/20 text-purple-300 border-purple-500/40`;
                } else {
                    badge.innerText = `${item.rel_icon || '📊'} ${item.relationship}: ${item.compression_pct > 0 ? `-${item.compression_pct}% Compressed` : `+${Math.abs(item.compression_pct)}% Wider`}`;
                    badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border ${item.rel_badge || 'border-slate-500'}`;
                }
                document.getElementById('modal-info').innerText = `Triggers: ${item.pm_high} / ${item.pm_low}`;
            }

            document.getElementById('modal-tc').innerText = item.curr_cpr.cpr_top;
            document.getElementById('modal-p').innerText = item.curr_cpr.p;
            document.getElementById('modal-bc').innerText = item.curr_cpr.cpr_bot;

            // Crypto Derivatives row in Modal
            const cryptoRow = document.getElementById('modal-crypto-row');
            if (item.oi_info) {
                cryptoRow.classList.remove('hidden');
                document.getElementById('modal-oi').innerText = item.oi_info.oi_formatted;
                document.getElementById('modal-vol').innerText = item.oi_info.vol_formatted;
                const fRateEl = document.getElementById('modal-funding');
                fRateEl.innerText = `${item.oi_info.funding_formatted} (${item.oi_info.funding_bias})`;
                fRateEl.className = `font-mono font-semibold ml-1 ${item.oi_info.funding_pct > 0 ? 'text-emerald-400' : (item.oi_info.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}`;
                
                const sqEl = document.getElementById('modal-squeeze');
                sqEl.innerHTML = `<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${item.oi_info.squeeze_class}">${item.oi_info.squeeze_badge} (${item.oi_info.squeeze_ratio}x)</span>`;
            } else {
                cryptoRow.classList.add('hidden');
            }

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
                title: item.strategy === 'virgin_cpr' ? 'Virgin TC' : 'TC'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.p,
                color: '#a855f7',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: item.strategy === 'virgin_cpr' ? 'Virgin Pivot' : 'PIVOT'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.cpr_bot,
                color: '#38bdf8',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: item.strategy === 'virgin_cpr' ? 'Virgin BC' : 'BC'
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
            currentQuickFilter = currentStrategy === 'inside_value' ? 'inside' : 'all';
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

    try:
        cb_m, cb_d = COINBASE_MGR.fetch_market_bars("BTC-USD")
        info["coinbase_btc_bars"] = {
            "daily_bars": len(cb_d),
            "monthly_bars": len(cb_m)
        }
    except Exception as e:
        info["coinbase_btc_bars"] = {"error": str(e)}

    return jsonify(info)

@app.route("/api/scan")
def api_scan():
    import traceback
    try:
        strategy = request.args.get("strategy", "virgin_cpr")
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
            if strategy == "virgin_cpr":
                futures = [executor.submit(process_virgin_cpr_daily, sym, 10) for sym in symbols]
                for f in futures:
                    res_list = f.result()
                    if res_list:
                        results.extend(res_list)
                results.sort(key=lambda x: x['abs_dist'])
            else:
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
            "strategy": strategy,
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

@app.route("/api/crypto/oi")
def api_crypto_oi():
    search = request.args.get("search", "BTC").strip()
    watchlist_raw = request.args.get("watchlist", "")
    watchlist_list = [w.strip() for w in watchlist_raw.split(",") if w.strip()] if watchlist_raw else None
    data = BINANCE_MGR.get_crypto_oi_radar(search, watchlist_list)
    return jsonify(data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print("\n=======================================================")
    print("🚀 PIVOT BOSS - MULTI-STRATEGY CPR TERMINAL (VIRGIN & INSIDE VALUE)")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
