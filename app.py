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

                        deriv_map[base] = {
                            "symbol": f"{base}-USD",
                            "clean_symbol": base,
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
                    <div id="quick-filters" class="flex items-center gap-1 bg-navy-950 p-1 rounded-xl border border-navy-700 text-[11px]">
                        <button onclick="setQuickFilter('all')" id="qf-all" class="px-2.5 py-1 rounded-lg bg-navy-800 text-white font-semibold">All</button>
                        <button onclick="setQuickFilter('squeeze')" id="qf-squeeze" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">⚡ Squeeze (≥3x)</button>
                        <button onclick="setQuickFilter('magnet')" id="qf-magnet" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🎯 Magnet (&lt;2%)</button>
                        <button onclick="setQuickFilter('megacoil')" id="qf-megacoil" class="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white">🔥 Coil (&gt;70%)</button>
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
                            <span>🎯 Inside Value (Coil)</span>
                        </div>
                        <p class="text-slate-400 leading-normal">The new CPR is <strong class="text-white">completely engulfed</strong> inside the prior period CPR. Extreme volatility compression coiling energy before an explosive directional breakout.</p>
                        <div class="mt-2 text-[11px] text-purple-300 font-medium">• Compression &gt; 70% = Mega Coil Explosion Imminent</div>
                        <div class="text-[11px] text-slate-300 font-medium">• Triggers: Buy &gt; PDH / Sell &lt; PDL</div>
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
        let currentMarket = 'india_all';
        let currentSort = { column: 'abs_dist', ascending: true };
        let scanData = [];
        let chartInstance = null;
        let currentQuickFilter = 'all'; // 'all', 'squeeze', 'magnet', 'megacoil'

        function openPlaybookModal() {
            document.getElementById('playbook-modal').classList.remove('hidden');
        }

        function closePlaybookModal() {
            document.getElementById('playbook-modal').classList.add('hidden');
        }

        function setQuickFilter(qf) {
            currentQuickFilter = qf;
            ['all', 'squeeze', 'magnet', 'megacoil'].forEach(id => {
                const btn = document.getElementById(`qf-${id}`);
                if (btn) {
                    if (id === qf) {
                        btn.className = 'px-2.5 py-1 rounded-lg bg-amber-400 text-black font-bold shadow';
                    } else {
                        btn.className = 'px-2.5 py-1 rounded-lg text-slate-400 hover:text-white';
                    }
                }
            });
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
            } else if (strat === 'inside_value') {
                currentSort = { column: 'compression_pct', ascending: false };
            }
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
                if (currentQuickFilter === 'squeeze') {
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
                            <p class="text-xs text-slate-500 mt-1">Try switching filter pill, market or strategy.</p>
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
                        let radarBadge = '';
                        if (item.abs_dist <= 0.75) {
                            radarBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/30 text-emerald-300 border border-emerald-400/50 animate-pulse font-sans"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Live Test</span></div>`;
                        } else if (item.abs_dist <= 2.0) {
                            radarBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30 font-sans"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Imminent</span></div>`;
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
                                <td class="py-3.5 px-4 text-[11px]">
                                    <div class="${distColor} font-bold">${item.dist_pct > 0 ? '+' : ''}${item.dist_pct}%</div>
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
                                        <a href="https://www.tradingview.com/chart/?symbol=BINANCE:${item.clean_symbol}USDT" target="_blank" rel="noopener" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold" title="Open TradingView">
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
                                        <a href="https://www.tradingview.com/chart/?symbol=BINANCE:${item.clean_symbol}USDT" target="_blank" rel="noopener" class="px-2 py-1 rounded-lg bg-navy-800 hover:bg-sky-600 hover:text-white text-slate-300 font-sans text-xs transition border border-navy-700 shadow font-semibold" title="Open TradingView">
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

@app.route("/api/crypto/oi")
def api_crypto_oi():
    search = request.args.get("search", "PEPE").strip()
    watchlist_raw = request.args.get("watchlist", "")
    watchlist_list = [w.strip() for w in watchlist_raw.split(",") if w.strip()] if watchlist_raw else None
    data = YAHOO_MGR.get_crypto_oi_radar(search, watchlist_list)
    return jsonify(data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print("\n=======================================================")
    print("🚀 PIVOT BOSS - MULTI-STRATEGY CPR TERMINAL (VIRGIN & INSIDE VALUE)")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
