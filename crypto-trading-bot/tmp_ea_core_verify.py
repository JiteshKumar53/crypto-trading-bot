import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from pipeline_controller_v2 import PipelineController

print('=== EA CORE INTEGRATION VERIFICATION ===')
print()

controller = PipelineController(
    use_agents=False,
    use_backtest=False,
    use_risk_governor=False,
    paper_only=True
)

print('1. EA Core active:', controller.ea_core_active)
print('2. EA Core instance:', controller.ea_core is not None)
print('3. Broker Recon:', controller.broker_recon is not None)
print('4. Position Manager:', controller.position_manager is not None)
print()

if controller.ea_core_active:
    print('Running cycle for BTC/USD...')
    result = controller.run_cycle('BTC/USD')
    
    print()
    print('Result keys:', list(result.keys()))
    print()
    
    if 'BTC/USD' in result.get('stages', {}):
        symbol_result = result['stages']['BTC/USD']
        print('Symbol result keys:', list(symbol_result.keys()))
        
        # EA Core stage is in the NESTED stages dict
        nested_stages = symbol_result.get('stages', {})
        print()
        print('Nested stages:')
        for stage, data in nested_stages.items():
            if isinstance(data, dict):
                print('  ' + stage + ': status=' + str(data.get('status', 'N/A')))
            else:
                print('  ' + stage + ': ' + str(data))
        
        if 'ea_core' in nested_stages:
            print()
            print('✅ EA Core WAS CALLED (Stage 2)')
            print('   Approved:', nested_stages['ea_core'].get('approved'))
            
            ea_stages = nested_stages['ea_core'].get('stages', {})
            if ea_stages:
                print('   EA Core sub-stages:')
                for s, d in ea_stages.items():
                    if isinstance(d, dict):
                        print('     ' + s + ': ' + str(d.get('status', 'N/A')))
                    else:
                        print('     ' + s + ': ' + str(d))
            
            # Check if execution was EA Core routed
            if 'execution' in nested_stages:
                exec_data = nested_stages['execution']
                print()
                print('Execution:', exec_data)
                if exec_data.get('ea_core_routed'):
                    print('✅ Order routed through EA Core')
                else:
                    print('⚠️  Execution not EA Core routed')
        else:
            print()
            print('❌ EA Core NOT in stages')
    
    print()
    if result.get('success'):
        print('✅ Cycle APPROVED')
    else:
        print('ℹ️  Cycle not approved')
else:
    print('❌ EA Core NOT ACTIVE')

print()
print('=== VERIFICATION COMPLETE ===')
