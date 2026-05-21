#!/usr/bin/env python3
"""
EA Core Live Proof Script
Runs ONE cycle through the live PipelineController (v2)
Logs all stages for CEO verification.
"""
import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

import logging
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

print('=' * 80)
print('CEO EA CORE LIVE PROOF')
print('Timestamp:', datetime.now(timezone.utc).isoformat())
print('=' * 80)
print()

# Import live PipelineController (v2)
from pipeline_controller import PipelineController

print('1. IMPORT CHECK')
print('   PipelineController imported from: pipeline_controller (v2)')
print('   File:', PipelineController.__module__)
print()

# Initialize
print('2. INITIALIZING PIPELINE CONTROLLER...')
controller = PipelineController(
    use_agents=False,
    use_backtest=False,
    use_risk_governor=False,
    paper_only=True
)
print('   EA Core active:', controller.ea_core_active)
print('   Broker Recon:', controller.broker_recon is not None)
print('   Position Manager:', controller.position_manager is not None)
print()

# Check for hard block
print('3. HARD BLOCK CHECK')
if controller.ea_core_active:
    print('   ✅ EA Core is ACTIVE — hard block NOT triggered')
else:
    print('   ❌ EA Core INACTIVE — hard block WOULD trigger')
print()

# Run one cycle
print('4. RUNNING ONE CYCLE...')
result = controller.run_cycle('BTC/USD')
print()

# Analyze result
print('5. CYCLE RESULT ANALYSIS')
print('   Result keys:', list(result.keys()))
print('   Success:', result.get('success'))
print()

if 'BTC/USD' in result.get('stages', {}):
    symbol_result = result['stages']['BTC/USD']
    nested = symbol_result.get('stages', {})
    
    print('6. STAGE-BY-STAGE VERIFICATION')
    for stage, data in nested.items():
        if isinstance(data, dict):
            print(f'   {stage}: {data.get("status", "N/A")}')
        else:
            print(f'   {stage}: {data}')
    
    print()
    print('7. EA CORE VERIFICATION')
    if 'ea_core' in nested:
        ea = nested['ea_core']
        print('   ✅ EA Core WAS CALLED (Stage 2)')
        print('   Approved:', ea.get('approved'))
        print('   Status:', ea.get('status'))
        print('   EA Core routed:', ea.get('ea_core_routed'))
        
        ea_sub = ea.get('stages', {})
        if ea_sub:
            print('   EA Core internal stages:')
            for s, d in ea_sub.items():
                if isinstance(d, dict):
                    print(f'     {s}: {d.get("status", "N/A")}')
                else:
                    print(f'     {s}: {d}')
        
        # Verify all critical gates
        print()
        print('8. SAFETY GATE VERIFICATION')
        gates = {
            'broker_fetch': 'Broker-First Reconciliation',
            'strategy_validation': 'Strategy Validation Gate',
            'risk_governor': 'Risk Governor',
            'duplicate_check': 'Duplicate Order Prevention',
        }
        for gate, name in gates.items():
            if gate in ea_sub:
                status = ea_sub[gate].get('status', 'N/A') if isinstance(ea_sub[gate], dict) else str(ea_sub[gate])
                if status in ['success', 'ok', 'ALLOWED', 'active']:
                    print(f'   ✅ {name}: {status}')
                else:
                    print(f'   ⚠️  {name}: {status}')
            else:
                print(f'   ❌ {name}: NOT FOUND')
        
        print()
        print('9. EXECUTION VERIFICATION')
        if 'execution' in ea_sub:
            exec_data = ea_sub['execution']
            print('   Execution status:', exec_data.get('status', 'N/A') if isinstance(exec_data, dict) else exec_data)
            if isinstance(exec_data, dict) and exec_data.get('ea_core_routed'):
                print('   ✅ Order routed through EA Core')
            else:
                print('   ℹ️  Execution data:', exec_data)
        else:
            print('   ℹ️  No execution stage (order not ready)')
    else:
        print('   ❌ EA Core NOT in stages')

print()
print('10. PAPER MODE VERIFICATION')
print('   Paper only:', controller.paper_only)
print('   Alpaca paper:', controller.alpaca.is_paper() if controller.alpaca else 'N/A')
print()

print('=' * 80)
print('END OF PROOF')
print('=' * 80)
