import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from pipeline_controller import PipelineController

print('=== QUICK EA CORE INTEGRATION TEST ===')
print()

controller = PipelineController(
    use_agents=False,
    use_backtest=True,
    use_risk_governor=True,
    paper_only=True
)

print('EA Core active:', controller.ea_core_active)
print('EA Core instance:', controller.ea_core is not None)
print()

# Run cycle for BTC/USD
print('Running cycle for BTC/USD...')
result = controller.run_cycle('BTC/USD')

print()
print('Result keys:', list(result.keys()))
print('Success:', result.get('success'))
print('Errors:', result.get('errors'))
print()

# Check if EA Core was called
if 'stages' in result and 'BTC/USD' in result['stages']:
    stages = result['stages']['BTC/USD']
    print('BTC/USD stages:')
    for stage, data in stages.items():
        if isinstance(data, dict):
            print('  ' + stage + ': status=' + str(data.get('status', 'N/A')))
        else:
            print('  ' + stage + ': ' + str(data))
    
    if 'ea_core' in stages:
        print()
        print('✅ EA Core WAS CALLED')
        print('   Approved:', stages['ea_core'].get('approved'))
        ea_stages = stages['ea_core'].get('stages', {})
        print('   EA Core stages:')
        for s, d in ea_stages.items():
            if isinstance(d, dict):
                print('     ' + s + ': ' + str(d.get('status', 'N/A')))
            else:
                print('     ' + s + ': ' + str(d))
    else:
        print()
        print('❌ EA Core NOT in stages')
    
    if 'execution' in stages:
        print()
        print('Execution:', stages['execution'])
else:
    print('No stages found')

print()
print('=== TEST COMPLETE ===')
