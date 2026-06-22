"""
Strategy Validation Gate.

The institutional fix for this project's root cause (see DEEP_ANALYSIS_2026-06-20.md):
no strategy may trade until it is PROVEN, on honest cost-aware metrics, to be
worth trading. A strategy must beat buy-and-hold of the same asset net of fees,
have a real edge (profit factor / expectancy), controlled drawdown, enough
trades to be meaningful, and be stable across walk-forward folds.

This module is pure and importable: feed it a metrics dict (from
backtest.metrics.MetricsCalculator) plus the buy-and-hold benchmark return and
an optional list of per-fold returns, and it returns a structured PASS/FAIL with
a reason for every gate. The live pipeline should refuse to size any strategy
that does not return passed=True here.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Thresholds — deliberately strict. A strategy that cannot clear these has no
# business risking capital (paper or live).
GATES = {
    "min_closed_trades": 10,      # enough round trips to be statistically meaningful
    "min_profit_factor": 1.30,    # gross win / gross loss after fees
    "max_drawdown": 0.25,         # 25% peak-to-trough cap
    "min_walk_forward_pass": 0.60,  # fraction of folds that must be positive
}


@dataclass
class GateResult:
    name: str
    passed: bool
    reason: str


@dataclass
class ValidationResult:
    strategy: str
    symbol: str
    passed: bool
    gates: List[GateResult] = field(default_factory=list)

    @property
    def failed_reasons(self) -> List[str]:
        return [g.reason for g in self.gates if not g.passed]

    def summary(self) -> str:
        status = "PASS ✓" if self.passed else "FAIL ✗"
        lines = [f"[{status}] {self.strategy} on {self.symbol}"]
        for g in self.gates:
            mark = "✓" if g.passed else "✗"
            lines.append(f"    {mark} {g.name}: {g.reason}")
        return "\n".join(lines)


def validate_strategy(
    strategy: str,
    symbol: str,
    metrics: Dict,
    benchmark_total_return: float,
    walk_forward_returns: Optional[List[float]] = None,
) -> ValidationResult:
    """
    Returns a ValidationResult. passed=True only if EVERY gate passes.

    Args:
        metrics: dict from MetricsCalculator.calculate (needs total_return,
            profit_factor, max_drawdown, closed_trades, expectancy).
        benchmark_total_return: buy-and-hold total return on the same data/costs.
        walk_forward_returns: optional list of per-fold total returns for stability.
    """
    gates: List[GateResult] = []

    # 1. Beats buy-and-hold (the only benchmark that matters)
    ret = metrics.get("total_return", 0.0)
    beats = ret > benchmark_total_return
    gates.append(GateResult(
        "beats_buy_and_hold",
        beats,
        f"return {ret*100:.1f}% vs HODL {benchmark_total_return*100:.1f}%"
        + ("" if beats else " — does not beat holding"),
    ))

    # 2. Enough trades to mean anything
    n = metrics.get("closed_trades", 0)
    enough = n >= GATES["min_closed_trades"]
    gates.append(GateResult(
        "min_closed_trades", enough,
        f"{n} closed trades (need >= {GATES['min_closed_trades']})",
    ))

    # 3. Profit factor (real edge after fees)
    pf = metrics.get("profit_factor", 0.0)
    pf_ok = pf >= GATES["min_profit_factor"]
    pf_disp = "inf" if pf == float("inf") else f"{pf:.2f}"
    gates.append(GateResult(
        "profit_factor", pf_ok,
        f"PF {pf_disp} (need >= {GATES['min_profit_factor']})",
    ))

    # 4. Positive expectancy
    exp = metrics.get("expectancy", 0.0)
    exp_ok = exp > 0
    gates.append(GateResult(
        "positive_expectancy", exp_ok,
        f"expectancy ${exp:.2f}/trade" + ("" if exp_ok else " — negative"),
    ))

    # 5. Drawdown control
    dd = metrics.get("max_drawdown", 1.0)
    dd_ok = dd <= GATES["max_drawdown"]
    gates.append(GateResult(
        "max_drawdown", dd_ok,
        f"maxDD {dd*100:.1f}% (cap {GATES['max_drawdown']*100:.0f}%)",
    ))

    # 6. Walk-forward stability (optional but recommended)
    if walk_forward_returns:
        pos = sum(1 for r in walk_forward_returns if r > 0)
        rate = pos / len(walk_forward_returns)
        wf_ok = rate >= GATES["min_walk_forward_pass"]
        gates.append(GateResult(
            "walk_forward_stability", wf_ok,
            f"{pos}/{len(walk_forward_returns)} folds positive "
            f"({rate*100:.0f}%, need >= {GATES['min_walk_forward_pass']*100:.0f}%)",
        ))

    passed = all(g.passed for g in gates)
    return ValidationResult(strategy=strategy, symbol=symbol, passed=passed, gates=gates)
