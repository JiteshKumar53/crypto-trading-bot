import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from pipeline_controller import PipelineController
from unittest.mock import patch, MagicMock
import pandas as pd

print('=== EA CORE INTEGRATION TEST — FORCING STAGE 6 ===')
print()

controller = PipelineController(
    use_agents=False,
    use_backtest=False,  # Skip backtest to reach Stage 6 faster
    use_risk_governor=False,  # Skip Risk Governor to reach Stage 6
    paper_only=True
)

print('EA Core active:', controller.ea_core_active)
print()

# Mock data fetcher to return valid data
mock_data = pd.DataFrame({
    'open': [77000] * 100,
    'high': [77500] * 100,
    'low': [76500] * 100,
    'close': [77200] * 100,
    'volume': [1000] * 100
})

# Mock the data fetcher
with patch.object(controller.data_fetcher, 'fetch_hourly_bars', return_value=mock_data):
    with patch.object(controller.data_fetcher, 'get_latest_price', return_value=77200):
        # Also need to mock orchestrator to approve
        with patch.object(controller.orchestrator, 'run_pipeline', return_value={
            'status': 'APPROVED',
            'decision_id': 'test-123',
            'reason': 'Test approval'
        }):
            print('Running cycle with mocked dependencies...')
            result = controller.run_cycle('BTC/USD')

print()
print('Result keys:', list(result.keys()))
print('Success:', result.get('success'))
print()

if 'stages' in result and 'BTC/USD' in result['stages']:
    stages = result['stages']['BTC/USD']
    print('Stages present:')
    for stage, data in stages.items():
        if isinstance(data, dict):
            print('  ' + stage + ': status=' + str(data.get('status', 'N/A')))
        else:
            print('  ' + stage + ': ' + str(data))
    
    if 'ea_core' in stages:
        print()
        print('✅ EA Core WAS CALLED')
        print('   Approved:', stages['ea_core'].get('approved'))
    else:
        print()
        print('❌ EA Core NOT in stages')
    
    if 'execution' in stages:
        print()
        print('Execution:', stages['execution'])

print()
print('=== TEST COMPLETE ===')
