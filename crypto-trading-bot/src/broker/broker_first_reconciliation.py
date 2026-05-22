"""
Broker-First Reconciliation Module
EA Core Component

Ensures Alpaca is the source of truth for all positions and orders.
Detects and resolves mismatches between broker state and local state.

Capsule: CAPSULE-003 — Broker-First Reconciliation
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Import PositionRecord for type-safe position storage
from core.position_manager import PositionRecord

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of broker-first reconciliation."""
    symbol: str
    broker_qty: float
    local_qty: float
    broker_value: float
    local_value: float
    mismatch: bool
    action: str  # "update_local", "create_local", "remove_local", "warn", "ok"
    reason: str


class BrokerFirstReconciliation:
    """
    Reconciles broker state (Alpaca) with local state.
    
    Hard rule: Broker state wins in all conflicts.
    """
    
    def __init__(self, alpaca_client):
        self.alpaca = alpaca_client
        self.reconciliation_log = []
        
    def reconcile_positions(
        self, 
        local_positions: Dict[str, Dict]
    ) -> Tuple[List[ReconciliationResult], Dict[str, Dict]]:
        """
        Reconcile local positions with broker positions.
        
        Args:
            local_positions: Dict of symbol -> position_data from local state
            
        Returns:
            Tuple of (reconciliation_results, corrected_local_positions)
        """
        # Fetch broker truth
        broker_positions = self.alpaca.get_positions()
        broker_by_symbol = {p['symbol']: p for p in broker_positions}
        
        results = []
        corrected = {}
        
        # Check all broker positions
        for symbol, broker_pos in broker_by_symbol.items():
            local_pos = local_positions.get(symbol)
            
            # Create PositionRecord from broker data
            broker_record = PositionRecord(
                symbol=symbol,
                qty=float(broker_pos['qty']),
                avg_entry_price=float(broker_pos.get('avg_entry_price', broker_pos.get('current_price', 0))),
                current_price=float(broker_pos['current_price']),
                market_value=float(broker_pos['market_value']),
                unrealized_pl=float(broker_pos.get('unrealized_pl', 0)),
                unrealized_plpc=float(broker_pos.get('unrealized_plpc', 0)),
                strategy_id='unknown',  # Will be populated later
                entry_timestamp=datetime.now(timezone.utc).isoformat(),
                last_updated=datetime.now(timezone.utc).isoformat(),
                exit_rules={},
            )
            
            if local_pos is None:
                # Broker has position, local does not -> create local
                result = ReconciliationResult(
                    symbol=symbol,
                    broker_qty=float(broker_pos['qty']),
                    local_qty=0.0,
                    broker_value=float(broker_pos['market_value']),
                    local_value=0.0,
                    mismatch=True,
                    action="create_local",
                    reason=f"Broker has {broker_pos['qty']} {symbol}, local missing. Creating local record."
                )
                corrected[symbol] = broker_record
            else:
                # Both have position -> compare
                # local_pos might be PositionRecord or dict
                local_qty = float(getattr(local_pos, 'qty', local_pos.get('qty', 0)))
                local_value = float(getattr(local_pos, 'market_value', local_pos.get('market_value', 0)))
                
                qty_diff = abs(float(broker_pos['qty']) - local_qty)
                value_diff = abs(float(broker_pos['market_value']) - local_value)
                
                if qty_diff > 0.0001 or value_diff > 1.0:
                    result = ReconciliationResult(
                        symbol=symbol,
                        broker_qty=float(broker_pos['qty']),
                        local_qty=local_qty,
                        broker_value=float(broker_pos['market_value']),
                        local_value=local_value,
                        mismatch=True,
                        action="update_local",
                        reason=f"Mismatch: broker qty={broker_pos['qty']} vs local qty={local_qty}. Updating local to match broker."
                    )
                    corrected[symbol] = broker_record
                else:
                    result = ReconciliationResult(
                        symbol=symbol,
                        broker_qty=float(broker_pos['qty']),
                        local_qty=local_qty,
                        broker_value=float(broker_pos['market_value']),
                        local_value=local_value,
                        mismatch=False,
                        action="ok",
                        reason="Positions match within tolerance."
                    )
                    corrected[symbol] = local_pos if isinstance(local_pos, PositionRecord) else broker_record
            
            results.append(result)
            self._log_reconciliation(result)
        
        # Check for stale local positions (local has, broker doesn't)
        for symbol, local_pos in local_positions.items():
            if symbol not in broker_by_symbol:
                local_qty = float(getattr(local_pos, 'qty', local_pos.get('qty', 0)))
                local_value = float(getattr(local_pos, 'market_value', local_pos.get('market_value', 0)))
                
                result = ReconciliationResult(
                    symbol=symbol,
                    broker_qty=0.0,
                    local_qty=local_qty,
                    broker_value=0.0,
                    local_value=local_value,
                    mismatch=True,
                    action="remove_local",
                    reason=f"Local position {symbol} ({local_qty}) not found in broker. Removing stale local record."
                )
                results.append(result)
                self._log_reconciliation(result)
                # Note: corrected dict doesn't include this symbol (effectively removed)
        
        return results, corrected
    
    def reconcile_account(self, local_account: Optional[Dict]) -> Tuple[bool, Dict, str]:
        """
        Reconcile local account state with broker account.
        
        Returns:
            Tuple of (mismatch, corrected_account, reason)
        """
        broker_account = self.alpaca.get_account()
        
        if local_account is None:
            return True, broker_account, "Local account missing, using broker state."
        
        equity_diff = abs(float(broker_account['equity']) - float(local_account.get('equity', 0)))
        cash_diff = abs(float(broker_account['cash']) - float(local_account.get('cash', 0)))
        
        if equity_diff > 1.0 or cash_diff > 1.0:
            reason = (
                f"Account mismatch: broker equity={broker_account['equity']:.2f} "
                f"vs local={local_account.get('equity', 0):.2f}. "
                f"Using broker state."
            )
            return True, broker_account, reason
        
        return False, local_account, "Account state matches broker."
    
    def check_stale_positions(self, local_positions: Dict[str, Dict]) -> List[str]:
        """
        Check for stale local positions that don't exist in broker.
        Returns list of stale symbols.
        """
        broker_positions = self.alpaca.get_positions()
        broker_symbols = {p['symbol'] for p in broker_positions}
        
        stale = []
        for symbol in local_positions:
            if symbol not in broker_symbols:
                stale.append(symbol)
                logger.warning(f"[BROKER-FIRST] Stale local position detected: {symbol}")
        
        return stale
    
    def can_trade(self, symbol: str, local_positions: Dict[str, Dict]) -> Tuple[bool, str]:
        """
        Check if trading is allowed for a symbol.
        Blocks if broker and local state disagree.
        
        Returns:
            Tuple of (allowed, reason)
        """
        broker_positions = self.alpaca.get_positions()
        broker_by_symbol = {p['symbol']: p for p in broker_positions}
        
        # If local says we have position but broker doesn't -> stale, block
        if symbol in local_positions and symbol not in broker_by_symbol:
            return False, f"Stale local position for {symbol}: broker shows no position. Block new trades until reconciliation."
        
        # If local and broker disagree on qty -> mismatch, block
        if symbol in local_positions and symbol in broker_by_symbol:
            local_qty = float(getattr(local_positions[symbol], 'qty', 0))
            broker_qty = float(broker_by_symbol[symbol]['qty'])
            if abs(local_qty - broker_qty) > 0.0001:
                return False, f"Position mismatch for {symbol}: local={local_qty:.6f} vs broker={broker_qty:.6f}. Block trades until reconciliation."
        
        return True, "Position state consistent with broker."
    
    def _log_reconciliation(self, result: ReconciliationResult):
        """Log reconciliation event."""
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symbol': result.symbol,
            'action': result.action,
            'mismatch': result.mismatch,
            'reason': result.reason,
            'broker_qty': result.broker_qty,
            'local_qty': result.local_qty,
        }
        self.reconciliation_log.append(event)
        
        if result.mismatch:
            logger.warning(
                f"[BROKER-FIRST] {result.action.upper()} for {result.symbol}: {result.reason}"
            )
        else:
            logger.info(f"[BROKER-FIRST] {result.symbol}: OK")
    
    def get_reconciliation_summary(self) -> Dict:
        """Get summary of recent reconciliations."""
        if not self.reconciliation_log:
            return {'status': 'no_reconciliations', 'total': 0}
        
        mismatches = sum(1 for r in self.reconciliation_log if r['mismatch'])
        return {
            'status': 'has_mismatches' if mismatches > 0 else 'all_ok',
            'total': len(self.reconciliation_log),
            'mismatches': mismatches,
            'last_reconciliation': self.reconciliation_log[-1]['timestamp'],
        }
