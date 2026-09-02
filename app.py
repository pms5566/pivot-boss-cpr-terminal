#!/usr/bin/env python3
"""
Pivot Boss - Multi-Timeframe Inside Value CPR Terminal
Supports:
1. Timeframes:
   - 🗓️ Monthly CPR
   - ⚡ Daily CPR
2. Modes:
   - 📍 Active Inside Value (Current Period vs Prior Period)
   - 🔮 Developing Inside Value (Next Period Forecast vs Current Period)
3. Markets:
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
            return self.crumb

    def fetch_market_bars(self, symbol):
        cache_key = f"{symbol}_DAILY_HISTORY"
        now = time.time()
        if cache_key in self.data_cache:
            ts, bars = self.data_cache[cache_key]
            if now - ts < 600:
                return bars

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
    """
    timeframe: 'monthly' or 'daily'
    mode: 'active' or 'developing'
    """
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
            # Target is Developing Next Month CPR (from Current MTD data)
            cpr_target = calculate_cpr_and_pivots(current_m['high'], current_m['low'], current_m['close'], dec)
            # Base is Current Month CPR (from Last Month data)
            cpr_base = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            target_label = f"Developing Next Month ({current_m['month']} MTD)"
            base_label = f"Current Month ({last_m['month']})"
            trigger_h = round(current_m['high'], dec)
            trigger_l = round(current_m['low'], dec)
            trigger_name_h = "MTD High (Buy)"
            trigger_name_l = "MTD Low (Sell)"
        else:
            # Target is Current Month CPR (from Last Month data)
            cpr_target = calculate_cpr_and_pivots(last_m['high'], last_m['low'], last_m['close'], dec)
            # Base is Previous Month CPR (from 2 Months Ago data)
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
            # Target is Developing Tomorrow's CPR (from Today's candle)
            cpr_target = calculate_cpr_and_pivots(today_c['high'], today_c['low'], today_c['close'], dec)
            # Base is Today's CPR (from Yesterday's candle)
            cpr_base = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            target_label = f"Developing Tomorrow ({today_c['date']})"
            base_label = f"Today ({yesterday_c['date']})"
            trigger_h = round(today_c['high'], dec)
            trigger_l = round(today_c['low'], dec)
            trigger_name_h = "Today High (Buy)"
            trigger_name_l = "Today Low (Sell)"
        else:
            # Target is Today's CPR (from Yesterday's candle)
            cpr_target = calculate_cpr_and_pivots(yesterday_c['high'], yesterday_c['low'], yesterday_c['close'], dec)
            # Base is Yesterday's CPR (from Day Before candle)
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

    return {
        "symbol": symbol,
        "clean_symbol": clean_symbol,
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
    <title>Pivot Boss Inside Value CPR Terminal • Multi-Timeframe</title>
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
                    <span class="text-black font-black font-mono text-xl" id="logo-letter">D</span>
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-amber-200 to-orange-400 bg-clip-text text-transparent flex items-center gap-2">
                        INSIDE VALUE CPR TERMINAL
                        <span id="header-mode-badge" class="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-mono font-medium border border-purple-500/30">DAILY DEVELOPING</span>
                    </h1>
                    <p class="text-xs text-slate-400">Institutional Volatility Compression & Breakout Forecast Engine</p>
                </div>
            </div>

            <!-- Controls: Timeframe, Mode, Market -->
            <div class="flex flex-wrap items-center gap-3">
                
                <!-- Timeframe Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setTimeframe('daily')" id="btn-tf-daily" class="px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow">
                        ⚡ Daily CPR
                    </button>
                    <button onclick="setTimeframe('monthly')" id="btn-tf-monthly" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        🗓️ Monthly CPR
                    </button>
                </div>

                <!-- Mode Selector -->
                <div class="flex bg-navy-950 p-1 rounded-xl border border-navy-700 text-xs font-medium shadow-inner">
                    <button onclick="setMode('developing')" id="btn-mode-dev" class="px-3 py-1.5 rounded-lg transition-all text-white bg-purple-600 font-bold shadow">
                        🔮 Developing (Next)
                    </button>
                    <button onclick="setMode('active')" id="btn-mode-act" class="px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white">
                        📍 Active (Current)
                    </button>
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
        <div class="p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 via-navy-900 to-navy-900 border border-amber-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg">
            <div class="flex items-start gap-3">
                <div class="text-2xl mt-0.5" id="banner-icon">⚡</div>
                <div>
                    <h3 class="text-sm font-bold text-amber-300" id="banner-title">Developing Daily Inside Value CPR (Tomorrow's Forecast):</h3>
                    <p class="text-xs text-slate-300 mt-0.5" id="banner-desc">
                        Based on today's price range, these assets are <strong>forming an Inside Value CPR for TOMORROW</strong>! 
                        Prepare for tomorrow's open: <strong>🟢 Buy Trigger</strong> on breakout above Today's High, <strong>🔴 Short Trigger</strong> on breakdown below Today's Low.
                    </p>
                </div>
            </div>
            <div class="shrink-0 flex items-center gap-2 font-mono text-xs bg-navy-950/80 px-3 py-2 rounded-xl border border-navy-700">
                <span class="text-slate-400">Verified Setups:</span>
                <span id="coils-total" class="text-amber-400 font-bold text-base">0</span>
            </div>
        </div>

        <!-- Table View -->
        <div class="glass rounded-2xl border border-navy-700/80 overflow-hidden shadow-2xl flex-1 flex flex-col">
            <div class="p-3.5 bg-navy-900/90 border-b border-navy-700 flex items-center justify-between gap-4">
                <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2" id="table-title">
                    🔥 Verified Inside Value Setups (Sorted by Compression %)
                </span>
                <input type="text" id="search-input" onkeyup="renderTable()" placeholder="Search symbol..." class="bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl px-3.5 py-1.5 focus:outline-none focus:border-amber-500 w-52 transition shadow-inner">
            </div>

            <div class="overflow-x-auto flex-1">
                <table class="w-full text-left text-xs border-collapse">
                    <thead>
                        <tr class="bg-navy-950/90 border-b border-navy-700 text-slate-400 font-semibold tracking-wider uppercase">
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('clean_symbol')">Asset Symbol ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('ltp')">Current LTP & Change ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('compression_pct')">Compression % ↕</th>
                            <th class="py-3.5 px-4 cursor-pointer hover:text-white" onclick="sortTable('curr_width')">Target CPR Band (BC • P • TC) ↕</th>
                            <th class="py-3.5 px-4">Base CPR Band (BC • P • TC)</th>
                            <th class="py-3.5 px-4">Breakout Triggers (High / Low)</th>
                            <th class="py-3.5 px-4">Target Pivots (S1 • R1)</th>
                            <th class="py-3.5 px-4 text-center">Chart</th>
                        </tr>
                    </thead>
                    <tbody id="table-body" class="divide-y divide-navy-700/50 font-mono">
                        <tr>
                            <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3"></div>
                                <p>Scanning market universe for verified Inside Value setups...</p>
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
                    <span id="modal-compression" class="px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40"></span>
                </div>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-navy-800 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-navy-950/60 border-b border-navy-700 text-xs">
                <div><span class="text-slate-400">Target CPR Top (TC):</span> <span id="modal-tc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Target Pivot (P):</span> <span id="modal-p" class="font-mono text-purple-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Target CPR Bot (BC):</span> <span id="modal-bc" class="font-mono text-blue-400 font-semibold"></span></div>
                <div><span class="text-slate-400">Key Triggers (High / Low):</span> <span id="modal-pmhl" class="font-mono text-amber-400 font-semibold"></span></div>
            </div>
            <div id="chart-container" class="w-full h-96 p-2 bg-navy-950"></div>
        </div>
    </div>

    <script>
        let currentTimeframe = 'daily';
        let currentMode = 'developing';
        let currentMarket = 'india_all';
        let currentSort = { column: 'compression_pct', ascending: false };
        let scanData = [];
        let chartInstance = null;

        function updateUIState() {
            // Timeframe buttons
            const btnDaily = document.getElementById('btn-tf-daily');
            const btnMonthly = document.getElementById('btn-tf-monthly');
            if (currentTimeframe === 'daily') {
                btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                btnMonthly.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                document.getElementById('logo-letter').innerText = 'D';
            } else {
                btnMonthly.className = 'px-3 py-1.5 rounded-lg transition-all text-black bg-amber-400 font-bold shadow';
                btnDaily.className = 'px-3 py-1.5 rounded-lg transition-all text-slate-400 hover:text-white';
                document.getElementById('logo-letter').innerText = 'M';
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

            // Header Badge & Banner text
            const badge = document.getElementById('header-mode-badge');
            const bannerTitle = document.getElementById('banner-title');
            const bannerDesc = document.getElementById('banner-desc');
            const tableTitle = document.getElementById('table-title');

            const tfName = currentTimeframe === 'daily' ? 'DAILY' : 'MONTHLY';
            const modeName = currentMode === 'developing' ? 'DEVELOPING (NEXT)' : 'ACTIVE (CURRENT)';
            badge.innerText = `${tfName} • ${modeName}`;

            if (currentTimeframe === 'daily' && currentMode === 'developing') {
                bannerTitle.innerText = "Developing Daily Inside Value CPR (Tomorrow's Forecast):";
                bannerDesc.innerHTML = "Based on today's price range, these assets are <strong>forming an Inside Value CPR for TOMORROW</strong>! Buy trigger on break of Today's High, short trigger on break of Today's Low.";
            } else if (currentTimeframe === 'daily' && currentMode === 'active') {
                bannerTitle.innerText = "Active Daily Inside Value CPR (Today vs Yesterday):";
                bannerDesc.innerHTML = "These assets have <strong>Today's CPR strictly inside Yesterday's CPR</strong>. High volatility expansion is expected today!";
            } else if (currentTimeframe === 'monthly' && currentMode === 'developing') {
                bannerTitle.innerText = "Developing Monthly Inside Value CPR (Next Month MTD Forecast):";
                bannerDesc.innerHTML = "Based on Month-to-Date data, these assets are <strong>forming an Inside Value CPR for NEXT MONTH</strong>! Early warning for multi-week mega breakout setups.";
            } else {
                bannerTitle.innerText = "Active Monthly Inside Value CPR (Current Month vs Prev Month):";
                bannerDesc.innerHTML = "These assets are in <strong>active multi-week compression</strong>. Trade breakouts above PMH or breakdowns below PML.";
            }
            tableTitle.innerText = `🔥 Verified ${tfName} ${modeName} Setups (Sorted by Compression %)`;

            // Markets
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
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3"></div>
                        <p>Scanning ${currentMarket.toUpperCase()} (${currentTimeframe.toUpperCase()} • ${currentMode.toUpperCase()})...</p>
                    </td>
                </tr>
            `;

            try {
                const response = await fetch(`/api/scan?market=${currentMarket}&timeframe=${currentTimeframe}&mode=${currentMode}`);
                const data = await response.json();
                scanData = data.results || [];
                document.getElementById('coils-total').innerText = scanData.length;
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
                return true;
            });

            filtered.sort((a, b) => {
                let valA, valB;
                if (currentSort.column === 'clean_symbol') {
                    valA = a.clean_symbol; valB = b.clean_symbol;
                } else if (currentSort.column === 'ltp') {
                    valA = a.ltp; valB = b.ltp;
                } else if (currentSort.column === 'compression_pct') {
                    valA = a.compression_pct; valB = b.compression_pct;
                } else if (currentSort.column === 'curr_width') {
                    valA = a.curr_cpr.cpr_width_pct; valB = b.curr_cpr.cpr_width_pct;
                }
                if (valA < valB) return currentSort.ascending ? -1 : 1;
                if (valA > valB) return currentSort.ascending ? 1 : -1;
                return 0;
            });

            const tbody = document.getElementById('table-body');
            if (filtered.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-16 text-slate-400 font-sans">
                            <div class="text-3xl mb-2">🔍</div>
                            <p class="text-sm font-semibold text-slate-300">No Inside Value setups for this selection right now.</p>
                            <p class="text-xs text-slate-500 mt-1">Try switching between Daily/Monthly or Active/Developing modes.</p>
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
                            <div class="text-[10px] text-amber-400 font-sans mt-0.5 font-medium">${item.target_label} (Width: ${item.curr_cpr.cpr_width_pct}%)</div>
                        </td>
                        <td class="py-3.5 px-4 text-[11px]">
                            <div class="text-slate-400"><span class="text-slate-500">${item.prev_cpr.cpr_bot}</span> • <span class="text-slate-400">${item.prev_cpr.p}</span> • <span class="text-slate-500">${item.prev_cpr.cpr_top}</span></div>
                            <div class="text-[10px] text-slate-500 font-sans mt-0.5">${item.base_label} (Width: ${item.prev_cpr.cpr_width_pct}%)</div>
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

        function openChart(symbol) {
            const item = scanData.find(s => s.symbol === symbol);
            if (!item) return;

            document.getElementById('modal-symbol').innerText = `${item.clean_symbol} (${item.symbol})`;
            const compBadge = document.getElementById('modal-compression');
            compBadge.innerText = `🔥 Inside Value: -${item.compression_pct}% Compressed`;

            document.getElementById('modal-tc').innerText = item.curr_cpr.cpr_top;
            document.getElementById('modal-p').innerText = item.curr_cpr.p;
            document.getElementById('modal-bc').innerText = item.curr_cpr.cpr_bot;
            document.getElementById('modal-pmhl').innerText = `${item.pm_high} / ${item.pm_low}`;

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

            candleSeries.createPriceLine({
                price: item.curr_cpr.cpr_top,
                color: '#38bdf8',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'TC'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.p,
                color: '#a855f7',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: 'PIVOT'
            });
            candleSeries.createPriceLine({
                price: item.curr_cpr.cpr_bot,
                color: '#38bdf8',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: 'BC'
            });

            candleSeries.createPriceLine({
                price: item.pm_high,
                color: '#22c55e',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.LargeDashed,
                axisLabelVisible: true,
                title: item.trigger_name_h
            });
            candleSeries.createPriceLine({
                price: item.pm_low,
                color: '#ef4444',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.LargeDashed,
                axisLabelVisible: true,
                title: item.trigger_name_l
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
    market = request.args.get("market", "india_all")
    timeframe = request.args.get("timeframe", "daily")
    mode = request.args.get("mode", "developing")
    watchlist_info = WATCHLISTS.get(market, WATCHLISTS["india_all"])
    symbols = watchlist_info["symbols"]
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_cpr_setup, sym, timeframe, mode) for sym in symbols]
        for f in futures:
            res = f.result()
            if res:
                results.append(res)
                
    results.sort(key=lambda x: x['compression_pct'], reverse=True)
    
    return jsonify({
        "market": market,
        "timeframe": timeframe,
        "mode": mode,
        "setup": "INSIDE_VALUE_ONLY",
        "count": len(results),
        "results": results
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print("\n=======================================================")
    print("🚀 PIVOT BOSS - MULTI-TIMEFRAME INSIDE VALUE CPR TERMINAL")
    print(f"👉 Open Dashboard: http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
