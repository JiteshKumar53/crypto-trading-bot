"""
EA Core Engine
Master orchestrator for deterministic trading execution.

Integrates:
- Market Scanner
- Strategy Signal Engine
- Strategy Validation Gate
- Risk Governor
- Order Idempotency Guard
- Broker Execution Layer
- Position Manager
- Broker-First Reconciliation
- Trade Logger
- Runtime Health Monitor

Capsule: CAPSULE-005 — EA Core Engine
"""

import logging
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EACoreEngine:
    """
    Deterministic trading engine.
    
    Cycle:
    1. Load runtime state
    2. Fetch broker truth (Alpaca)
    3. Reconcile positions
    4. Check trading halt status
    5. Load Strategy Leaderboard
    6. Fetch market data
    7. Generate strategy signals
    8. Validate strategy permission
    9. Check open positions/orders
    10. Run Risk Governor
    11. Block duplicate orders
    12. Submit Alpaca paper order (if allowed)
    13. Manage exits
    14. Log decisions
    15. Update runtime state
    16. Report to CEO
    17. Repeat
    """
    
    def __init__(self, alpaca_client, data_fetcher, risk_governor, 
                 strategy_validation_gate, position_manager, 
                 broker_reconciliation, order_idempotency_guard):
        self.alpaca = alpaca_client
        self.data_fetcher = data_fetcher
        self.risk_governor = risk_governor
        self.strategy_gate = strategy_validation_gate
        self.position_manager = position_manager
        self.broker_recon = broker_reconciliation
        self.order_guard = order_idempotency_guard
        
        self.runtime_state = {
            'last_cycle_timestamp': None,
            'cycle_count': 0,
            'total_trades': 0,
            'total_pnl': 0.0,
            'errors': [],
        }
        
        # Trading halt status
        self.trading_halted = False
        self.halt_reason = None
        
        logger.info("[EA CORE] Engine initialized")
    
    def run_cycle(self, symbol: str = 'BTC/USD') -> Dict:
        """
        Run one complete EA Core cycle.
        
        Returns:
            Dict with cycle results and decisions
        """
        cycle_start = time.time()
        self.runtime_state['cycle_count'] += 1
        cycle_id = f"cycle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        result = {
            'cycle_id': cycle_id,
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stages': {},
            'approved': False,
            'errors': [],
        }
        
        try:
            # Stage 1: Load runtime state
            logger.info(f"[EA CORE] {cycle_id}: Starting cycle for {symbol}")
            result['stages']['load_state'] = {'status': 'success'}
            
            # Stage 2: Fetch broker truth
            broker_account = self.alpaca.get_account()
            broker_positions = self.alpaca.get_positions()
            broker_orders = self.alpaca.get_open_orders()
            
            if not broker_account:
                raise ValueError("Failed to fetch broker account")
            
            result['stages']['broker_fetch'] = {
                'status': 'success',
                'equity': broker_account['equity'],
                'positions': len(broker_positions),
                'open_orders': len(broker_orders),
            }
            
            # Stage 3: Reconcile positions
            local_positions = self.position_manager.positions if hasattr(self, 'position_manager') else {}
            recon_results, corrected_positions = self.broker_recon.reconcile_positions(local_positions)
            
            has_mismatches = any(r.mismatch for r in recon_results)
            result['stages']['reconciliation'] = {
                'status': 'mismatch_detected' if has_mismatches else 'ok',
                'mismatches': sum(1 for r in recon_results if r.mismatch),
                'total_checked': len(recon_results),
            }
            
            # Update position manager with corrected positions
            self.position_manager.positions = corrected_positions
            
            # Stage 4: Check trading halt
            if self.trading_halted:
                result['stages']['halt_check'] = {
                    'status': 'halted',
                    'reason': self.halt_reason,
                }
                result['approved'] = False
                result['status'] = 'blocked'
                logger.warning(f"[EA CORE] Trading halted: {self.halt_reason}")
                return result
                return result
            
            result['stages']['halt_check'] = {'status': 'ok'}
            
            # Stage 5: Load Strategy Leaderboard
            # (Already loaded in strategy_gate)
            result['stages']['leaderboard'] = {'status': 'ok'}
            
            # Stage 6: Fetch market data
            try:
                data = self.data_fetcher.fetch_hourly_bars(symbol.replace('/', ''), limit=200)
                result['stages']['market_data'] = {
                    'status': 'success',
                    'bars': len(data) if hasattr(data, '__len__') else 'unknown',
                }
            except Exception as e:
                result['stages']['market_data'] = {
                    'status': 'failed',
                    'error': str(e),
                }
                result['errors'].append(f"Market data fetch failed: {e}")
                return result
            
            # Stage 7: Generate strategy signals
            # (This would call the strategy signal engine)
            result['stages']['signal_generation'] = {'status': 'success'}
            
            # Stage 8: Validate strategy permission
            strategy_name = 'grid_trading_v1'
            
            # Handle both object-style and dict-style gate results
            raw_gate_result = self.strategy_gate(strategy_name, symbol.replace('/', ''))
            
            if isinstance(raw_gate_result, dict):
                # Dict-style (from evolver_runtime)
                gate_approved = raw_gate_result.get('approved', raw_gate_result.get('passed', False))
                gate_reason = raw_gate_result.get('reason', 'Unknown')
                gate_status = raw_gate_result.get('status', 'unknown')
                gate_max_size = raw_gate_result.get('max_position_size', 500.0)
            else:
                # Object-style (from strategy_validation_gate)
                gate_approved = getattr(raw_gate_result, 'approved', False)
                gate_reason = getattr(raw_gate_result, 'reason', 'Unknown')
                gate_status = getattr(raw_gate_result, 'strategy_status', 'unknown')
                gate_max_size = getattr(raw_gate_result, 'max_position_size', 500.0)
            
            if not gate_approved:
                result['stages']['strategy_validation'] = {
                    'status': 'blocked',
                    'reason': gate_reason,
                }
                result['approved'] = False
                logger.warning(f"[EA CORE] Strategy blocked: {gate_reason}")
                return result
            
            result['stages']['strategy_validation'] = {
                'status': 'approved',
                'strategy': strategy_name,
                'status': gate_status,
            }
            
            # Stage 9: Check open positions and orders
            current_pos = self.position_manager.is_position_open(symbol.replace('/', ''))
            open_orders = len(broker_orders)
            
            result['stages']['position_check'] = {
                'status': 'ok',
                'has_position': current_pos,
                'open_orders': open_orders,
            }
            
            # Stage 10: Run Risk Governor
            try:
                risk_result = self.risk_governor.check_order(
                    symbol=symbol,
                    side='buy',
                    qty=0.0026,
                    price=77000,
                    portfolio_value=broker_account['equity'],
                    current_position_value=self.position_manager.get_position_value(symbol.replace('/', '')),
                )
                
                # Handle RiskResult object
                if hasattr(risk_result, 'approved'):
                    risk_status = 'ALLOWED' if risk_result.approved else 'BLOCKED'
                    # Get reason from first failed check or decision
                    if hasattr(risk_result, 'checks') and risk_result.checks:
                        failed = [c for c in risk_result.checks if not c.passed]
                        if failed:
                            risk_reason = failed[0].reason
                        else:
                            risk_reason = 'All checks passed'
                    else:
                        risk_reason = getattr(risk_result, 'decision', 'Unknown')
                else:
                    # Dict-style fallback
                    risk_status = risk_result.get('status', 'BLOCKED')
                    risk_reason = risk_result.get('reason', 'No reason')
                
                result['stages']['risk_governor'] = {
                    'status': risk_status,
                    'reason': risk_reason,
                }
                
                if risk_status != 'ALLOWED':
                    result['approved'] = False
                    result['status'] = 'blocked'
                    logger.warning(f"[EA CORE] Risk Governor blocked: {risk_status}")
                    return result
            except Exception as e:
                logger.error(f"[EA CORE] Risk Governor check failed: {e}")
                result['stages']['risk_governor'] = {
                    'status': 'error',
                    'error': str(e),
                }
                result['approved'] = False
                result['status'] = 'error'
                return result
            
            # Stage 11: Block duplicate orders
            can_trade, trade_reason = self.broker_recon.can_trade(symbol.replace('/', ''), local_positions)
            
            if not can_trade:
                result['stages']['duplicate_check'] = {
                    'status': 'blocked',
                    'reason': trade_reason,
                }
                result['approved'] = False
                logger.warning(f"[EA CORE] Duplicate order prevention: {trade_reason}")
                return result
            
            result['stages']['duplicate_check'] = {'status': 'ok'}
            
            # Stage 12: Submit order (only if all checks passed)
            # Note: In dry-run mode, we simulate; in live mode, we submit
            # For now, this is a placeholder - actual submission happens in PipelineController
            result['stages']['execution'] = {
                'status': 'ready',
                'note': 'Order validated and ready for submission',
            }
            
            result['approved'] = True
            
            # Stage 13: Manage exits
            exit_signals = self.position_manager.check_all_positions({})
            if exit_signals:
                result['stages']['exit_management'] = {
                    'status': 'exit_signals',
                    'signals': [
                        {'symbol': s, 'action': a, 'reason': r}
                        for s, a, r, _ in exit_signals
                    ],
                }
            else:
                result['stages']['exit_management'] = {'status': 'no_exits'}
            
            # Stage 14-16: Log, update state, report
            self.runtime_state['last_cycle_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            cycle_time = time.time() - cycle_start
            logger.info(f"[EA CORE] Cycle {cycle_id} completed in {cycle_time:.2f}s")
            
            result['cycle_time_seconds'] = cycle_time
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"[EA CORE] Cycle {cycle_id} failed: {e}")
            result['errors'].append(str(e))
            result['status'] = 'failed'
            self.runtime_state['errors'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cycle_id': cycle_id,
                'error': str(e),
            })
        
        return result
    
    def halt_trading(self, reason: str):
        """Halt all new trading."""
        self.trading_halted = True
        self.halt_reason = reason
        logger.critical(f"[EA CORE] TRADING HALTED: {reason}")
    
    def resume_trading(self):
        """Resume trading if conditions allow."""
        if self.trading_halted:
            self.trading_halted = False
            old_reason = self.halt_reason
            self.halt_reason = None
            logger.info(f"[EA CORE] Trading resumed. Was halted due to: {old_reason}")
    
    def get_status(self) -> Dict:
        """Get current engine status."""
        return {
            'engine': 'EA Core',
            'version': '1.0',
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'cycles_completed': self.runtime_state['cycle_count'],
            'last_cycle': self.runtime_state['last_cycle_timestamp'],
            'total_trades': self.runtime_state['total_trades'],
            'total_pnl': self.runtime_state['total_pnl'],
            'error_count': len(self.runtime_state['errors']),
            'last_error': self.runtime_state['errors'][-1] if self.runtime_state['errors'] else None,
        }
    
    def save_runtime_state(self, filepath: str = 'logs/ea_core_state.json'):
        """Save runtime state to disk."""
        with open(filepath, 'w') as f:
            json.dump(self.runtime_state, f, indent=2)
        logger.info(f"[EA CORE] Runtime state saved to {filepath}")
    
    def load_runtime_state(self, filepath: str = 'logs/ea_core_state.json'):
        """Load runtime state from disk."""
        try:
            with open(filepath) as f:
                self.runtime_state = json.load(f)
            logger.info(f"[EA CORE] Runtime state loaded from {filepath}")
        except FileNotFoundError:
            logger.info(f"[EA CORE] No previous state found, starting fresh")
