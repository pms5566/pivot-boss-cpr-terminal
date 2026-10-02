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

import time
import json
import datetime
import threading
import requests
import urllib.parse
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
    }
}

class YahooSessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
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
    def get_dynamic_crypto_symbols(self, max_coins=250):
        now = time.time()
        if "DYNAMIC_CRYPTO_SYMBOLS" in self.data_cache:
            ts, syms = self.data_cache["DYNAMIC_CRYPTO_SYMBOLS"]
            if now - ts < 3600:
                return syms

        base_list = WATCHLISTS["crypto_all"]["symbols"]
        symbols_set = set(base_list)

        try:
            url = 'https://api.gateio.ws/api/v4/spot/tickers'
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                stables_and_junk = {'USDT', 'USDC', 'USD', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'EUR', 'USDE', 'PYUSD', 'PAXG', 'XAUT', 'USDY'}
                candidates = []
                for t in data:
                    pair = t.get('currency_pair', '')
                    if pair.endswith('_USDT'):
                        base = pair.replace('_USDT', '')
                        if base in stables_and_junk: continue
                        if base.endswith('3L') or base.endswith('3S') or base.endswith('5L') or base.endswith('5S'): continue
                        if (base.endswith('G') or base.endswith('ON') or base.endswith('X')) and len(base) >= 3 and any(s in base for s in ['WMT', 'HD', 'LLY', 'QQQ', 'SPY', 'TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'META', 'GLD', 'SLV', 'COIN', 'MSTR', 'PLTR', 'COST', 'HOOD', 'SNDK', 'BRK', 'AVGO']):
                            continue
                        if not base.isascii() or not base.isalnum(): continue
                        try:
                            vol = float(t.get('quote_volume', 0))
                            price = float(t.get('last', 0))
                            if vol >= 200000 and price > 0:
                                candidates.append((f"{base}-USD", vol))
                        except Exception:
                            pass
                candidates.sort(key=lambda x: x[1], reverse=True)
                for sym, _ in candidates[:max_coins]:
                    symbols_set.add(sym)
        except Exception:
            pass

        final_list = list(symbols_set)
        priority = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "SUI-USD", "NEAR-USD", "PEPE-USD", "LINK-USD", "LTC-USD"]
        sorted_final = [p for p in priority if p in final_list] + [s for s in final_list if s not in priority]
        
        self.data_cache["DYNAMIC_CRYPTO_SYMBOLS"] = (now, sorted_final)
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

                        deriv_map[base] = {
                            "oi_usd": round(oi_usd, 2),
                            "oi_formatted": oi_fmt,
                            "vol_usd": round(vol_usd, 2),
                            "vol_formatted": vol_fmt,
                            "funding_pct": funding_pct,
                            "funding_formatted": f"{funding_pct:+.4f}%",
                            "funding_bias": funding_bias,
                            "squeeze_ratio": squeeze_ratio,
                            "squeeze_badge": squeeze_badge,
                            "squeeze_class": squeeze_class,
                            "squeeze_risk": squeeze_risk
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
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_pair}&interval=1d&limit=365"
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
                url = f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={gate_pair}&interval=1d&limit=365"
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
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{encoded_sym}?range=1y&interval=1d"
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
                            if m_key not in monthly_dict:
                                monthly_dict[m_key] = {
                                    'month': m_key, 'time': t, 'open': float(o),
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
    monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
    
    if timeframe == "monthly":
        if len(monthly_bars) < 3: return None
        current_m = monthly_bars[-1]
        last_m = monthly_bars[-2]
        prev_m = monthly_bars[-3]
        
        last_price = current_m['close']
        if last_price < 0.001: return None
        
        is_crypto = "-USD" in symbol
        dec = 4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)
        
        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(current_m['high'], current_m['low'], current_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            target_label = f"Developing Next Month ({current_m['month']} MTD)"
            base_label = f"Current Month ({last_m['month']})"
            trigger_h = round(current_m['high'], dec)
            trigger_l = round(current_m['low'], dec)
            trigger_name_h = "MTD High (Buy)"
            trigger_name_l = "MTD Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            cpr_base = calculate_cpr_and_pivots(prev_m['high'], prev_m['low'], prev_m['close'], dec)
            target_label = f"Current Month ({last_m['month']})"
            base_label = f"Previous Month ({prev_m['month']})"
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
        
        last_price = today_c['close']
        if last_price < 0.001: return None
        
        is_crypto = "-USD" in symbol
        dec = 4 if is_crypto and last_price < 1.0 else (3 if is_crypto and last_price < 10.0 else 2)
        
        if mode == "developing":
            cpr_target = calculate_cpr_and_pivots(today_c['high'], today_c['low'], today_c['close'], dec)
            cpr_base = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            target_label = f"Developing Tomorrow ({today_c['date']})"
            base_label = f"Today ({yesterday_c['date']})"
            trigger_h = round(today_c['high'], dec)
            trigger_l = round(today_c['low'], dec)
            trigger_name_h = "Today High (Buy)"
            trigger_name_l = "Today Low (Sell)"
        else:
            cpr_target = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            cpr_base = calculate_cpr_and_pivots(day_before_c['high'], day_before_c['low'], day_before_c['close'], dec)
            target_label = f"Today ({yesterday_c['date']})"
            base_label = f"Yesterday ({day_before_c['date']})"
            trigger_h = round(yesterday_c['high'], dec)
            trigger_l = round(yesterday_c['low'], dec)
            trigger_name_h = "PD High (Buy)"
            trigger_name_l = "PD Low (Sell)"
            
        base_prev_close = yesterday_c['close']

    # Strict Inside Value Condition
    top_t, bot_t = cpr_target['cpr_top'], cpr_target['cpr_bot']
    top_b, bot_b = cpr_base['cpr_top'], cpr_base['cpr_bot']

    is_inside_value = (top_t <= top_b) and (bot_t >= bot_b)
    if not is_inside_value:
        return None

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

    if compression_pct >= 70:
        quality_tag = {"text": "⚡ Mega Coil (>70%)", "badge": "bg-purple-500/20 text-purple-300 border-purple-500/40"}
    elif compression_pct >= 40:
        quality_tag = {"text": "🔥 High Compression (>40%)", "badge": "bg-amber-500/20 text-amber-300 border-amber-500/40"}
    else:
        quality_tag = {"text": "🟡 Inside Value", "badge": "bg-yellow-500/20 text-yellow-300 border-yellow-500/40"}

    clean_symbol = symbol.replace(".NS", "").replace("^", "")
    oi_info = YAHOO_MGR.get_crypto_derivatives(symbol) if is_crypto else None

    return {
        "symbol": symbol,
        "clean_symbol": clean_symbol,
        "strategy": "inside_value",
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
    monthly_bars, daily_candles = YAHOO_MGR.fetch_market_bars(symbol)
    if len(daily_candles) < max_days + 2:
        return []

    n = len(daily_candles)
    current_candle = daily_candles[-1]
    ltp = current_candle['close']
    if ltp < 0.001:
        return []

    is_crypto = "-USD" in symbol
    dec = 4 if is_crypto and ltp < 1.0 else (3 if is_crypto and ltp < 10.0 else 2)
    clean_symbol = symbol.replace(".NS", "").replace("^", "")
    oi_info = YAHOO_MGR.get_crypto_derivatives(symbol) if is_crypto else None

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
                        <span id="header-mode-badge" class="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 font-mono font-medium border border-rose-500/30">VIRGIN CPR (≤10D)</span>
                    </h1>
                    <p class="text-xs text-slate-400">Institutional Breakout & Untested Liquidity Magnet Engine</p>
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
                    <button onclick="setMarket('india_all')" id="btn-india" class="px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-semibold shadow">
                        🇮🇳 India
                    </button>
                    <button onclick="setMarket('us_russell2000')" id="btn-us" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🇺🇸 Russell 2000
                    </button>
                    <button onclick="setMarket('crypto_all')" id="btn-crypto" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🪙 Crypto
                    </button>
                </div>

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
        <div class="glass rounded-2xl border border-navy-700/80 overflow-hidden shadow-2xl flex-1 flex flex-col">
            <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex items-center justify-between gap-4">
                <span class="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2" id="table-title">
                    🛡️ Verified Daily Virgin CPRs (Sorted by Nearest Distance to LTP)
                </span>
                <input type="text" id="search-input" onkeyup="renderTable()" placeholder="Search symbol..." class="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl px-3.5 py-1.5 focus:outline-none focus:border-rose-500 w-52 transition shadow-inner">
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

    <script>
        let currentStrategy = 'virgin_cpr'; // 'virgin_cpr' or 'inside_value'
        let currentTimeframe = 'daily';
        let currentMode = 'developing';
        let currentMarket = 'india_all';
        let currentSort = { column: 'abs_dist', ascending: true };
        let scanData = [];
        let chartInstance = null;

        function updateUIState() {
            const btnVirgin = document.getElementById('btn-strat-virgin');
            const btnInside = document.getElementById('btn-strat-inside');
            const ivControls = document.getElementById('inside-value-controls');
            const badge = document.getElementById('header-mode-badge');
            const bannerCard = document.getElementById('banner-card');
            const bannerTitle = document.getElementById('banner-title');
            const bannerDesc = document.getElementById('banner-desc');
            const bannerIcon = document.getElementById('banner-icon');
            const tableTitle = document.getElementById('table-title');
            const logo = document.getElementById('logo-letter');

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
                if (currentTimeframe === 'daily') {
                    btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                    btnMonthly.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    logo.innerText = 'D';
                } else {
                    btnMonthly.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                    btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    logo.innerText = 'M';
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

                const tfName = currentTimeframe === 'daily' ? 'DAILY' : 'MONTHLY';
                const modeName = currentMode === 'developing' ? 'DEVELOPING (NEXT)' : 'ACTIVE (CURRENT)';
                badge.innerText = `${tfName} • ${modeName}`;
                badge.className = 'px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono font-medium border border-amber-500/30';

                bannerCard.className = 'p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-navy-900 to-navy-900 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg';
                bannerIcon.innerText = '🎯';
                bannerTitle.className = 'text-sm font-bold text-amber-300';
                bannerTitle.innerText = `${tfName} ${modeName} Inside Value CPR Setup:`;
                bannerDesc.innerHTML = 'These assets are in <strong>verified volatility compression</strong>. Trade breakouts above PMH/Today High or breakdowns below PML/Today Low.';
                tableTitle.innerText = `🔥 Verified ${tfName} ${modeName} Inside Value Setups`;
                tableTitle.className = 'text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2';
            }

            // Crypto market banner adjustments
            if (currentMarket === 'crypto_all') {
                if (currentStrategy === 'virgin_cpr') {
                    tableTitle.innerText = '🛡️ Verified Daily Virgin CPRs + Derivatives Squeeze Risk (200+ Liquid Coins)';
                    bannerDesc.innerHTML = 'Price has <strong>never touched these CPR pivot ranges</strong> since formation! Track <strong>Open Interest, 24h Squeeze Ratio, and Funding Rates</strong> to catch high-conviction breakout bounces.';
                } else {
                    const tfName = currentTimeframe === 'daily' ? 'DAILY' : 'MONTHLY';
                    const modeName = currentMode === 'developing' ? 'DEVELOPING' : 'ACTIVE';
                    tableTitle.innerText = `🔥 Verified ${tfName} ${modeName} Inside Value + Derivatives Squeeze Risk (200+ Liquid Coins)`;
                    bannerDesc.innerHTML = 'Scan volatility compression coils alongside <strong>Live Open Interest, Leverage Ratios, and Funding Rates</strong> before big liquidation squeezes.';
                }
            }

            // Market selector styles
            ['india', 'us', 'crypto'].forEach(m => {
                const btn = document.getElementById(`btn-${m}`);
                if (btn) {
                    if ((m === 'india' && currentMarket === 'india_all') ||
                        (m === 'us' && currentMarket === 'us_russell2000') ||
                        (m === 'crypto' && currentMarket === 'crypto_all')) {
                        btn.className = 'px-3 py-1.5 rounded-lg transition-all text-white bg-indigo-600 font-bold shadow';
                    } else {
                        btn.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                    }
                }
            });
        }

        function setStrategy(strat) {
            currentStrategy = strat;
            if (strat === 'virgin_cpr') {
                currentSort = { column: 'abs_dist', ascending: true };
            } else {
                currentSort = { column: 'compression_pct', ascending: false };
            }
            updateUIState();
            runScan();
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
            
            const isCrypto = currentMarket === 'crypto_all';

            // Set Table Head according to strategy & market
            if (currentStrategy === 'virgin_cpr') {
                if (isCrypto) {
                    thead.innerHTML = `
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Coin Pair ↕</th>
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
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Coin Pair ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Chg ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('compression_pct')">Compression % ↕</th>
                            <th class="py-3.5 px-4">Target CPR Band (BC • P • TC)</th>
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
                const response = await fetch(`/api/scan?strategy=${currentStrategy}&market=${currentMarket}&timeframe=${currentTimeframe}&mode=${currentMode}`);
                const data = await response.json();
                scanData = data.results || [];
                document.getElementById('coils-total').innerText = scanData.length;
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

            const isCrypto = currentMarket === 'crypto_all';
            const tbody = document.getElementById('table-body');
            if (filtered.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="${isCrypto ? 9 : 8}" class="text-center py-16 text-slate-400 font-sans">
                            <div class="text-3xl mb-2">🔍</div>
                            <p class="text-sm font-semibold text-slate-300">No matching setups found right now.</p>
                            <p class="text-xs text-slate-500 mt-1">Try switching market or strategy.</p>
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

                    if (isCrypto) {
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
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="${distColor} font-bold">${item.dist_pct > 0 ? '+' : ''}${item.dist_pct}%</div>
                                    <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${item.role_badge} font-sans mt-0.5">
                                        ${item.role}
                                    </span>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="text-cyan-400 font-bold font-mono">${item.oi_info.oi_formatted}</div>
                                        <div class="text-[10px] text-slate-400 font-mono">Vol: ${item.oi_info.vol_formatted}</div>
                                    ` : `<span class="text-slate-500 font-mono">-</span>`}
                                </td>
                                <td class="py-3.5 px-4">
                                    ${item.oi_info ? `
                                        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.oi_info.squeeze_class} font-sans">
                                            ${item.oi_info.squeeze_badge} (${item.oi_info.squeeze_ratio}x)
                                        </span>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="font-mono font-semibold ${item.oi_info.funding_pct > 0 ? 'text-emerald-400' : (item.oi_info.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${item.oi_info.funding_formatted}</div>
                                        <div class="text-[10px] text-slate-500 font-sans">${item.oi_info.funding_bias}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-center">
                                    <button onclick="openChart('${item.symbol}', '${item.virgin_date}')" class="px-3 py-1 rounded-lg bg-navy-800 hover:bg-rose-500 hover:text-white text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                        View
                                    </button>
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
                                    <div class="font-bold text-white text-sm tracking-tight">${item.clean_symbol}</div>
                                    <div class="text-[10px] text-slate-500 font-sans">${item.symbol}</div>
                                </td>
                                <td class="py-3.5 px-4">
                                    <div class="font-bold text-slate-100">${item.ltp.toLocaleString()}</div>
                                    <div class="${chgColor} text-[11px] font-sans font-medium">${chgSign}${item.change} (${chgSign}${item.change_pct}%)</div>
                                </td>
                                <td class="py-3.5 px-4">
                                    <span class="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${item.quality_tag.badge} font-sans">
                                        ⚡ -${item.compression_pct}%
                                    </span>
                                    <div class="${item.position_status.class} text-[10px] font-sans mt-0.5">${item.position_status.text}</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="text-slate-200 font-semibold"><span class="text-blue-400">${item.curr_cpr.cpr_bot}</span> • <span class="text-purple-400 font-bold">${item.curr_cpr.p}</span> • <span class="text-blue-400">${item.curr_cpr.cpr_top}</span></div>
                                    <div class="text-[10px] text-amber-400 font-sans mt-0.5 font-medium">${item.target_label}</div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div><span class="text-slate-400 font-sans">${item.trigger_name_h}:</span> <span class="text-emerald-400 font-bold">${item.pm_high}</span></div>
                                    <div><span class="text-slate-400 font-sans">${item.trigger_name_l}:</span> <span class="text-rose-400 font-bold">${item.pm_low}</span></div>
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="text-cyan-400 font-bold font-mono">${item.oi_info.oi_formatted}</div>
                                        <div class="text-[10px] text-slate-400 font-mono">Vol: ${item.oi_info.vol_formatted}</div>
                                    ` : `<span class="text-slate-500 font-mono">-</span>`}
                                </td>
                                <td class="py-3.5 px-4">
                                    ${item.oi_info ? `
                                        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${item.oi_info.squeeze_class} font-sans">
                                            ${item.oi_info.squeeze_badge} (${item.oi_info.squeeze_ratio}x)
                                        </span>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-[11px]">
                                    ${item.oi_info ? `
                                        <div class="font-mono font-semibold ${item.oi_info.funding_pct > 0 ? 'text-emerald-400' : (item.oi_info.funding_pct < 0 ? 'text-rose-400' : 'text-slate-300')}">${item.oi_info.funding_formatted}</div>
                                        <div class="text-[10px] text-slate-500 font-sans">${item.oi_info.funding_bias}</div>
                                    ` : `<span class="text-slate-500 font-mono text-xs">-</span>`}
                                </td>
                                <td class="py-3.5 px-4 text-center">
                                    <button onclick="openChart('${item.symbol}')" class="px-3 py-1 rounded-lg bg-navy-800 hover:bg-amber-500 hover:text-black text-slate-200 font-sans text-xs transition border border-navy-700 shadow font-semibold">
                                        View
                                    </button>
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
                            <td class="py-3.5 px-4">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-semibold border ${item.quality_tag.badge} font-sans">
                                    ⚡ -${item.compression_pct}% Compressed
                                </span>
                                <div class="${item.position_status.class} text-[10px] font-sans mt-0.5">${item.position_status.text}</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-slate-200 font-semibold"><span class="text-blue-400">${item.curr_cpr.cpr_bot}</span> • <span class="text-purple-400 font-bold">${item.curr_cpr.p}</span> • <span class="text-blue-400">${item.curr_cpr.cpr_top}</span></div>
                                <div class="text-[10px] text-amber-400 font-sans mt-0.5 font-medium">${item.target_label}</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div class="text-slate-400"><span class="text-slate-500">${item.prev_cpr.cpr_bot}</span> • <span class="text-slate-400">${item.prev_cpr.p}</span> • <span class="text-slate-500">${item.prev_cpr.cpr_top}</span></div>
                                <div class="text-[10px] text-slate-500 font-sans mt-0.5">${item.base_label}</div>
                            </td>
                            <td class="py-3.5 px-4 text-[11px]">
                                <div><span class="text-slate-400 font-sans">${item.trigger_name_h}:</span> <span class="text-emerald-400 font-bold">${item.pm_high}</span></div>
                                <div><span class="text-slate-400 font-sans">${item.trigger_name_l}:</span> <span class="text-rose-400 font-bold">${item.pm_low}</span></div>
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
                badge.innerText = `🔥 Inside Value: -${item.compression_pct}% Compressed`;
                badge.className = `px-2.5 py-1 rounded-md text-xs font-semibold border ${item.quality_tag.badge}`;
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

@app.route("/api/scan")
def api_scan():
    strategy = request.args.get("strategy", "virgin_cpr")
    market = request.args.get("market", "india_all")
    timeframe = request.args.get("timeframe", "daily")
    mode = request.args.get("mode", "developing")
    if market == "crypto_all":
        symbols = YAHOO_MGR.get_dynamic_crypto_symbols(250)
    else:
        watchlist_info = WATCHLISTS.get(market, WATCHLISTS["india_all"])
        symbols = watchlist_info["symbols"]
    
    results = []
    workers = 16 if market == "crypto_all" else 10
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
            results.sort(key=lambda x: x['compression_pct'], reverse=True)
    
    return jsonify({
        "strategy": strategy,
        "market": market,
        "timeframe": timeframe,
        "mode": mode,
        "count": len(results),
        "results": results
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print("\n=======================================================")
    print("🚀 PIVOT BOSS - MULTI-STRATEGY CPR TERMINAL (VIRGIN & INSIDE VALUE)")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
