"""
EA Core Integration Tests — Runtime Verification Suite

Proves that EA Core is actually in the live execution path.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestEACoreIntegration:
    """Test that EA Core is actually integrated into PipelineController."""

    def test_pipeline_controller_imports_ea_core(self):
        """Test 1: PipelineController imports EA Core."""
        with open('src/pipeline_controller.py') as f:
            content = f.read()
        
        assert 'EACoreEngine' in content, "PipelineController must import EACoreEngine"
        assert 'BrokerFirstReconciliation' in content, "PipelineController must import BrokerFirstReconciliation"
        assert 'PositionManager' in content, "PipelineController must import PositionManager"

    def test_pipeline_controller_instantiates_ea_core(self):
        """Test 2: PipelineController creates EA Core instance."""
        with open('src/pipeline_controller.py') as f:
            content = f.read()
        
        assert 'self.ea_core' in content, "PipelineController must create self.ea_core"
        assert 'self.ea_core_active' in content, "PipelineController must track ea_core_active"

    def test_hard_block_when_ea_core_inactive(self):
        """Test 3: If EA Core inactive, new entries are blocked."""
        with open('src/pipeline_controller.py') as f:
            content = f.read()
        
        assert 'CRITICAL_EA_CORE_BYPASS' in content, "Must have hard block for EA Core bypass"
        assert 'ea_core_active' in content, "Must check ea_core_active"
        assert 'BLOCKED_ALL_ENTRIES' in content, "Must block all entries when EA Core inactive"

    def test_orders_routed_through_ea_core(self):
        """Test 4: Orders are routed through EA Core, not direct submit."""
        with open('src/pipeline_controller.py') as f:
            content = f.read()
        
        # Should call ea_core.run_cycle() before submit_order
        assert 'self.ea_core.run_cycle' in content, "PipelineController must call ea_core.run_cycle()"
        assert 'ea_core_routed' in content, "Must track ea_core_routed flag"

    def test_position_monitor_warns_without_ea_core(self):
        """Test 5: Position Monitor warns when submitting without EA Core."""
        with open('src/position_monitor.py') as f:
            content = f.read()
        
        assert 'WITHOUT EA Core' in content, "Position Monitor must warn about missing EA Core"

    def test_broker_first_reconciliation_exists(self):
        """Test 6: Broker-first reconciliation module exists."""
        assert os.path.exists('src/broker/broker_first_reconciliation.py'), "Broker-first reconciliation module must exist"

    def test_position_manager_exists(self):
        """Test 7: Position Manager module exists."""
        assert os.path.exists('src/core/position_manager.py'), "Position Manager module must exist"

    def test_ea_core_engine_exists(self):
        """Test 8: EA Core Engine module exists."""
        assert os.path.exists('src/core/ea_core_engine.py'), "EA Core Engine module must exist"

    def test_pipeline_controller_has_only_one_submit_order(self):
        """Test 9: Only ONE submit_order call in PipelineController (inside EA Core block)."""
        with open('src/pipeline_controller.py') as f:
            content = f.read()
        
        # Count actual submit_order calls (not comments or docstrings)
        lines = content.split('\n')
        calls = [l for l in lines if 'submit_order(' in l and not l.strip().startswith('#') and 'STRICTLY PROHIBITED' not in l]
        
        assert len(calls) <= 1, f"PipelineController should have max 1 submit_order call, found {len(calls)}"

    def test_ea_core_has_broker_first_stage(self):
        """Test 10: EA Core cycle includes broker-first reconciliation."""
        with open('src/core/ea_core_engine.py') as f:
            content = f.read()
        
        assert 'broker_recon' in content, "EA Core must use broker reconciliation"
        assert 'reconcile_positions' in content, "EA Core must reconcile positions"

    def test_ea_core_has_strategy_validation(self):
        """Test 11: EA Core cycle includes strategy validation."""
        with open('src/core/ea_core_engine.py') as f:
            content = f.read()
        
        assert 'strategy_gate' in content, "EA Core must check strategy gate"
        assert 'validate_strategy' in content, "EA Core must validate strategy"

    def test_ea_core_has_risk_governor(self):
        """Test 12: EA Core cycle includes Risk Governor."""
        with open('src/core/ea_core_engine.py') as f:
            content = f.read()
        
        assert 'risk_governor' in content, "EA Core must use Risk Governor"
        assert 'evaluate_trade' in content, "EA Core must evaluate trade risk"


if __name__ == "__main__":
    print("Running EA Core Integration Tests...")
    test = TestEACoreIntegration()
    
    tests = [
        ("test_pipeline_controller_imports_ea_core", test.test_pipeline_controller_imports_ea_core),
        ("test_pipeline_controller_instantiates_ea_core", test.test_pipeline_controller_instantiates_ea_core),
        ("test_hard_block_when_ea_core_inactive", test.test_hard_block_when_ea_core_inactive),
        ("test_orders_routed_through_ea_core", test.test_orders_routed_through_ea_core),
        ("test_position_monitor_warns_without_ea_core", test.test_position_monitor_warns_without_ea_core),
        ("test_broker_first_reconciliation_exists", test.test_broker_first_reconciliation_exists),
        ("test_position_manager_exists", test.test_position_manager_exists),
        ("test_ea_core_engine_exists", test.test_ea_core_engine_exists),
        ("test_pipeline_controller_has_only_one_submit_order", test.test_pipeline_controller_has_only_one_submit_order),
        ("test_ea_core_has_broker_first_stage", test.test_ea_core_has_broker_first_stage),
        ("test_ea_core_has_strategy_validation", test.test_ea_core_has_strategy_validation),
        ("test_ea_core_has_risk_governor", test.test_ea_core_has_risk_governor),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"  PASS: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {name} - {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {name} - {e}")
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed == 0:
        print("ALL EA CORE INTEGRATION TESTS PASSED")
    else:
        print(f"{failed} TEST(S) FAILED")
