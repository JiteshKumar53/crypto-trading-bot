"""
Smart EA Bot Company — Trend Pullback Scalper v2
EMA 20/50/200 trend filter + RSI pullback + ATR-based SL/TP
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate EMA."""
    if len(prices) < period:
        return [sum(prices[:len(prices)]) / len(prices)] * len(prices)
    emas = [sum(prices[:period]) / period]
    mult = 2 / (period + 1)
    for i in range(period, len(prices)):
        emas.append(prices[i] * mult + emas[-1] * (1 - mult))
    return [emas[0]] * (period - 1) + emas


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI."""
    if len(prices) < period + 1:
        return [50.0] * len(prices)
    rsis = [50.0] * period
    for i in range(period, len(prices)):
        gains = [max(0, prices[j] - prices[j - 1]) for j in range(i - period + 1, i + 1)]
        losses = [abs(min(0, prices[j] - prices[j - 1])) for j in range(i - period + 1, i + 1)]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        rsis.append(100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss else 100)
    return rsis


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ATR."""
    atrs = [0.0] * period
    for i in range(period, len(bars)):
        trs = []
        for j in range(i - period + 1, i + 1):
            bar = bars[j]
            tr = max(
                bar["high"] - bar["low"],
                abs(bar["high"] - bars[j - 1]["close"]),
                abs(bar["low"] - bars[j - 1]["close"])
            )
            trs.append(tr)
        atrs.append(sum(trs) / period)
    return atrs


def calculate_adx(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ADX. Returns values 0-100."""
    n = len(bars)
    if n < period * 3:
        return [20.0] * n

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr_values = [0.0] * n

    for i in range(1, n):
        high = bars[i]["high"]
        low = bars[i]["low"]
        prev_high = bars[i - 1]["high"]
        prev_low = bars[i - 1]["low"]
        prev_close = bars[i - 1]["close"]

        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm[i] = up_move if up_move > down_move and up_move > 0 else 0.0
        minus_dm[i] = down_move if down_move > up_move and down_move > 0 else 0.0
        tr_values[i] = max(high - low, abs(high - prev_close), abs(low - prev_close))

    # Wilder's smoothing
    tr_smooth = [0.0] * n
    plus_smooth = [0.0] * n
    minus_smooth = [0.0] * n

    tr_smooth[period] = sum(tr_values[1:period + 1])
    plus_smooth[period] = sum(plus_dm[1:period + 1])
    minus_smooth[period] = sum(minus_dm[1:period + 1])

    for i in range(period + 1, n):
        tr_smooth[i] = tr_smooth[i - 1] - tr_smooth[i - 1] / period + tr_values[i]
        plus_smooth[i] = plus_smooth[i - 1] - plus_smooth[i - 1] / period + plus_dm[i]
        minus_smooth[i] = minus_smooth[i - 1] - minus_smooth[i - 1] / period + minus_dm[i]

    # DX
    dx = [0.0] * n
    for i in range(period, n):
        if tr_smooth[i] == 0:
            dx[i] = 0.0
        else:
            plus_di = 100.0 * plus_smooth[i] / tr_smooth[i]
            minus_di = 100.0 * minus_smooth[i] / tr_smooth[i]
            dx[i] = 100.0 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0.0

    # ADX
    adx = [20.0] * n
    adx[period * 2] = sum(dx[period + 1:period * 2 + 1]) / period

    for i in range(period * 2 + 1, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period

    return adx


def trend_pullback_v2_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Pullback Scalper v2 — Trend-Only Strategy.
    EMA 20/50/200 + RSI pullback + ATR SL/TP.
    Enters on pullbacks TO (not through) EMA20 in established trends.
    """
    if len(bars) < 210:
        return [{"action": "hold"} for _ in bars]

    closes = [bar["close"] for bar in bars]
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    ema200 = calculate_ema(closes, 200)
    rsi = calculate_rsi(closes, 14)
    atr = calculate_atr(bars, 14)
    adx = calculate_adx(bars, 14)

    signals = []

    for i in range(len(bars)):
        signal = {"action": "hold"}

        if i < 210 or i >= len(bars) - 1:
            signals.append(signal)
            continue

        price = closes[i]
        e20 = ema20[i]
        e50 = ema50[i]
        e200 = ema200[i]
        current_rsi = rsi[i]
        current_atr = atr[i]
        current_adx = adx[i]

        # EMA slope check (last 10 bars)
        if i >= 10:
            e20_slope = (e20 - ema20[i - 10]) / e20 * 100 if e20 > 0 else 0
        else:
            e20_slope = 0

        # Trend strength — require ADX > 25 (strong trend)
        strong_trend = current_adx > 25

        if not strong_trend:
            signals.append(signal)
            continue

        # --- UPTREND: price > EMA20 > EMA50 > EMA200 ---
        uptrend = price > e20 and e20 > e50 and e50 > e200 and e20_slope > 0

        # --- DOWNTREND: price < EMA20 < EMA50 < EMA200 ---
        downtrend = price < e20 and e20 < e50 and e50 < e200 and e20_slope < 0

        if not uptrend and not downtrend:
            signals.append(signal)
            continue

        # Pullback definition: price approaches EMA20
        # In uptrend: price is ABOVE EMA20 but within ATR distance (cooling off toward EMA20)
        # In downtrend: price is BELOW EMA20 but within ATR distance (rallying toward EMA20)
        atr_mult = 1.0  # How close to EMA20 qualifies as "pullback"

        pullback_long = uptrend and price > e20 and (price - e20) <= current_atr * atr_mult
        pullback_short = downtrend and price < e20 and (e20 - price) <= current_atr * atr_mult

        # RSI confirmation — in pullback, RSI should have pulled back from extremes
        # In uptrend pullback: RSI was > 60 recently, now 35-55 (cooled off but not oversold)
        # In downtrend pullback: RSI was < 40 recently, now 45-65 (warmed up but not overbought)
        if i >= 5:
            recent_rsi = rsi[i - 5:i + 1]
            rsi_was_high = max(recent_rsi[:5]) > 60 if len(recent_rsi) >= 5 else False
            rsi_was_low = min(recent_rsi[:5]) < 40 if len(recent_rsi) >= 5 else False
        else:
            rsi_was_high = False
            rsi_was_low = False

        rsi_pullback_long = 35 <= current_rsi <= 55 and rsi_was_high
        rsi_pullback_short = 45 <= current_rsi <= 65 and rsi_was_low

        # Not too deep — price still respects the larger EMA
        not_too_deep_long = price > e50
        not_too_deep_short = price < e50

        atr_mult_sl = 1.5
        atr_mult_tp = 2.5

        # Long entry: uptrend, price near EMA20 (pullback), RSI cooled off
        if uptrend and pullback_long and rsi_pullback_long and not_too_deep_long:
            signal = {
                "action": "buy",
                "stop_loss": price - (current_atr * atr_mult_sl),
                "take_profit": price + (current_atr * atr_mult_tp),
                "max_hold_bars": 6,  # 30 minutes
                "reason": "tps_v2_pullback_long",
            }

        # Short entry: downtrend, price near EMA20 (pullback), RSI warmed up
        elif downtrend and pullback_short and rsi_pullback_short and not_too_deep_short:
            signal = {
                "action": "sell",
                "stop_loss": price + (current_atr * atr_mult_sl),
                "take_profit": price - (current_atr * atr_mult_tp),
                "max_hold_bars": 6,
                "reason": "tps_v2_pullback_short",
            }

        signals.append(signal)

    return signals
