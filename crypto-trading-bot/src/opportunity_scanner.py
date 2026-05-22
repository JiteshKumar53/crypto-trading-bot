"""
Opportunity Scanner — Lightweight 15-minute signal visibility
Agent: Jarvis (Junior CEO)

Purpose: Provide signal status between 4-hour trading cycles.
- Does NOT bypass EA Core or Risk Governor
- Does NOT place orders
- Reports: signal strength, trend, volatility, regime for each asset
- Runs independently via cron every 15 minutes
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')

from broker.alpaca_client import AlpacaPaperClient
from data.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

SCAN_LOG = Path('/data/.openclaw/workspace/crypto-trading-bot/logs/opportunity_scan.jsonl')
ASSETS = ['BTC/USD', 'ETH/USD', 'SOL/USD']


def calculate_signal_metrics(data) -> Dict:
    """Calculate basic signal metrics from OHLCV data."""
    if data is None or len(data) < 20:
        return {
            'trend': 'unknown',
            'rsi': None,
            'volatility': 'unknown',
            'regime': 'unknown',
            'signal_strength': 0.0,
            'recommendation': 'no_data',
        }
    
    try:
        import pandas as pd
        import numpy as np
        
        # Ensure data is DataFrame
        if not isinstance(data, pd.DataFrame):
            return {
                'trend': 'unknown',
                'rsi': None,
                'volatility': 'unknown',
                'regime': 'unknown',
                'signal_strength': 0.0,
                'recommendation': 'data_error',
            }
        
        # Calculate RSI
        close = data['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        
        # Calculate volatility (ATR-like)
        high_low = data['high'] - data['low']
        volatility = high_low.rolling(window=14).mean().iloc[-1]
        avg_price = close.mean()
        vol_pct = (volatility / avg_price * 100) if avg_price > 0 else 0
        
        # Determine regime
        if vol_pct > 5:
            regime = 'high_volatility'
        elif vol_pct < 1:
            regime = 'low_volatility'
        else:
            regime = 'normal'
        
        # Determine trend
        sma20 = close.rolling(window=20).mean().iloc[-1]
        sma50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else sma20
        
        if close.iloc[-1] > sma20 * 1.02:
            trend = 'uptrend'
        elif close.iloc[-1] < sma20 * 0.98:
            trend = 'downtrend'
        else:
            trend = 'ranging'
        
        # Signal strength (-1 to +1)
        signal_strength = 0.0
        if current_rsi < 30 and trend != 'downtrend':
            signal_strength = (30 - current_rsi) / 30 * 0.5
        elif current_rsi > 70 and trend != 'uptrend':
            signal_strength = -(current_rsi - 70) / 30 * 0.5
        
        # Add trend component
        if trend == 'uptrend':
            signal_strength += 0.3
        elif trend == 'downtrend':
            signal_strength -= 0.3
        
        signal_strength = max(-1.0, min(1.0, signal_strength))
        
        # Recommendation
        if signal_strength > 0.5:
            recommendation = 'strong_buy'
        elif signal_strength > 0.2:
            recommendation = 'weak_buy'
        elif signal_strength < -0.5:
            recommendation = 'strong_sell'
        elif signal_strength < -0.2:
            recommendation = 'weak_sell'
        else:
            recommendation = 'neutral'
        
        return {
            'trend': trend,
            'rsi': round(current_rsi, 2),
            'volatility': f'{vol_pct:.2f}%',
            'regime': regime,
            'signal_strength': round(signal_strength, 3),
            'recommendation': recommendation,
            'sma20': round(sma20, 2),
            'current_price': round(close.iloc[-1], 2),
        }
    except Exception as e:
        logger.warning(f"Error calculating metrics: {e}")
        return {
            'trend': 'error',
            'rsi': None,
            'volatility': 'unknown',
            'regime': 'unknown',
            'signal_strength': 0.0,
            'recommendation': 'error',
            'error': str(e),
        }


def scan_opportunities() -> Dict:
    """Run opportunity scan for all assets."""
    client = AlpacaPaperClient()
    fetcher = DataFetcher(client)
    
    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'assets': {},
        'summary': {
            'strong_signals': 0,
            'weak_signals': 0,
            'neutral': 0,
            'errors': 0,
        }
    }
    
    for asset in ASSETS:
        try:
            logger.info(f"[SCANNER] Scanning {asset}...")
            # Use asset with slash for data fetcher
            data = fetcher.fetch_hourly_bars(asset, limit=168)
            metrics = calculate_signal_metrics(data)
            
            results['assets'][asset] = metrics
            
            # Update summary
            rec = metrics['recommendation']
            if rec in ['strong_buy', 'strong_sell']:
                results['summary']['strong_signals'] += 1
            elif rec in ['weak_buy', 'weak_sell']:
                results['summary']['weak_signals'] += 1
            elif rec == 'error':
                results['summary']['errors'] += 1
            else:
                results['summary']['neutral'] += 1
                
        except Exception as e:
            logger.warning(f"[SCANNER] Failed to scan {asset}: {e}")
            results['assets'][asset] = {
                'recommendation': 'error',
                'error': str(e),
            }
            results['summary']['errors'] += 1
    
    return results


def save_scan(results: Dict):
    """Save scan results to log file."""
    SCAN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SCAN_LOG, 'a') as f:
        f.write(json.dumps(results, default=str) + '\n')


def generate_scan_report(results: Dict) -> str:
    """Generate human-readable scan report."""
    lines = [
        "---",
        "",
        "# OPPORTUNITY SCAN REPORT",
        "",
        f"**Scan time:** {results['timestamp']}",
        "",
        "## SUMMARY",
        "",
        f"- **Strong signals:** {results['summary']['strong_signals']}",
        f"- **Weak signals:** {results['summary']['weak_signals']}",
        f"- **Neutral:** {results['summary']['neutral']}",
        f"- **Errors:** {results['summary']['errors']}",
        "",
        "## ASSET DETAILS",
        "",
    ]
    
    for asset, metrics in results['assets'].items():
        lines.append(f"### {asset}")
        lines.append("")
        if 'error' in metrics:
            lines.append(f"- **Status:** ❌ Error — {metrics['error']}")
        else:
            rec = metrics['recommendation']
            rec_emoji = {
                'strong_buy': '🟢 STRONG BUY',
                'weak_buy': '🟡 WEAK BUY',
                'neutral': '⚪ NEUTRAL',
                'weak_sell': '🟡 WEAK SELL',
                'strong_sell': '🔴 STRONG SELL',
            }.get(rec, rec)
            
            lines.append(f"- **Recommendation:** {rec_emoji}")
            lines.append(f"- **Signal strength:** {metrics['signal_strength']:+.3f}")
            lines.append(f"- **Trend:** {metrics['trend']}")
            lines.append(f"- **RSI:** {metrics['rsi']}")
            lines.append(f"- **Volatility:** {metrics['volatility']}")
            lines.append(f"- **Regime:** {metrics['regime']}")
            lines.append(f"- **Price:** ${metrics['current_price']:,.2f} (SMA20: ${metrics['sma20']:,.2f})")
        lines.append("")
    
    lines.extend([
        "---",
        "*Opportunity Scanner — Does NOT place orders. Signals for visibility only.*",
        "",
    ])
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    results = scan_opportunities()
    save_scan(results)
    report = generate_scan_report(results)
    print(report)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    main()
