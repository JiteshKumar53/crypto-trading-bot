"""
Smart EA Bot Company — Core Configuration
All risk limits are hard-coded and require code changes to modify.
"""

# --- Assets ---
ASSETS = ["BTCUSD", "ETHUSD"]

# --- Timeframes ---
PRIMARY_TIMEFRAME = "5Min"
CONFIRMATION_TIMEFRAME = "15Min"

# --- Risk Limits (HARD-CODED) ---
MAX_POSITIONS_TOTAL = 2
MAX_POSITIONS_PER_ASSET = 1
RISK_PER_TRADE_PCT = 0.25          # 0.25% of equity
DAILY_MAX_LOSS_PCT = 1.0            # Stop trading after 1% daily loss
WEEKLY_MAX_LOSS_PCT = 3.0           # Stop trading after 3% weekly loss
MAX_HOLD_TIME_MINUTES = 30          # Force exit after 30 min
COOLDOWN_MINUTES = 15               # Wait 15 min between trades
NO_MARTINGALE = True
NO_AVERAGING_DOWN = True
NO_REVENGE_TRADING = True

# --- Session Filter (US market hours, ET) ---
SESSION_START = "09:30"
SESSION_END = "16:00"
TIMEZONE = "America/New_York"

# --- Alpaca Paper Trading ---
ALPACA_PAPER = True
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# --- Fee Model (Alpaca crypto) ---
FEE_PER_TRADE_PCT = 0.10            # 0.1% per side
SLIPPAGE_PCT = 0.05                 # 0.05% estimated slippage

# --- Backtest Defaults ---
BACKTEST_START_DAYS = 90
INITIAL_EQUITY = 10000.0

# --- Logging ---
LOG_LEVEL = "INFO"
TRADE_LOG_PATH = "logs/simple_ea_trades.csv"
DAILY_REPORT_PATH = "logs/simple_ea_daily_reports.txt"
