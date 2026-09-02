# 🚀 Pivot Boss - Inside Value CPR Terminal

An institutional-grade **Multi-Timeframe Inside Value CPR (Central Pivot Range)** Screener and Real-Time Breakout Terminal based on Frank Ochoa's book *Secrets of a Pivot Boss*.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Features

- **Multi-Timeframe Support**:
  - `⚡ Daily CPR`: Intraday breakout & compression engine.
  - `🗓️ Monthly CPR`: Positional multi-week swing setups.
- **Two Calculation Modes**:
  - `📍 Active (Current Period)`: Filters assets currently in strict inside value compression.
  - `🔮 Developing (Next Period Forecast)`: Calculates upcoming period CPR in real-time from current Month-to-Date (MTD) or Day-to-Date price action.
- **3 Global Markets Covered**:
  - 🇮🇳 **Indian Equities**: Nifty 50, Bank Nifty & Top 100 F&O stocks.
  - 🇺🇸 **US Russell 2000**: Small-Caps and high-beta growth leaders.
  - 🪙 **Crypto Markets**: Top 110+ liquid coins (BTC, ETH, SOL, ADA, LTC, BCH, DeFi & Layer 1s).
- **Interactive TradingView Charts**:
  - Real-time candlestick charts with TC, Pivot, BC lines and Breakout / Breakdown trigger levels ($H, L$).
- **Zero-Latency In-Memory Caching & Multi-Threaded Engine**.

---

## 🛠️ Quick Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pms5566/pivot-boss-cpr-terminal.git
   cd pivot-boss-cpr-terminal
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python app.py
   ```

4. **Open in browser**:
   Navigate to `http://127.0.0.1:5001`.

---

## ☁️ 1-Click Cloud Deployment (Render.com / Railway)

- **Render.com**: Connect this repository, set Build Command to `pip install -r requirements.txt` and Start Command to `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`.
- **Railway.app**: Select this repo and click Deploy (auto-detects `Procfile`).

---

## 📜 License
MIT License
