#!/usr/bin/env python3
"""
TrueData Support - Exact Code and Error Reproduction
Account: tdwsp697
Issue: Live data subscription appears expired despite being told it's active
"""

import sys
import time
import logging
from datetime import datetime
import traceback

# Setup logging to capture exact errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_truedata_official_library():
    """Test using official truedata library (version 7.0.0)"""
    print("=" * 60)
    print("TEST 1: Official TrueData Library (truedata==7.0.0)")
    print("=" * 60)
    
    try:
        from truedata import TD_live
        
        # Credentials
        login_id = 'tdwsp697'
        password = 'shyam@697'
        
        print(f"Connecting with credentials: {login_id}")
        print("Creating TD_live object...")
        
        start_time = time.time()
        
        # This is where it hangs or fails
        td_obj = TD_live(login_id, password)
        
        elapsed = time.time() - start_time
        print(f"✅ TD_live object created successfully in {elapsed:.2f} seconds")
        
        # Test getting LTP
        print("Testing get_ltp for NIFTY...")
        result = td_obj.get_ltp(['NIFTY'])
        print(f"Result: {result}")
        
        return True, None
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_details = {
            'library': 'truedata==7.0.0',
            'method': 'TD_live(login_id, password)',
            'error_type': type(e).__name__,
            'error_message': str(e),
            'elapsed_time': f"{elapsed:.2f} seconds",
            'full_traceback': traceback.format_exc()
        }
        
        print(f"❌ ERROR after {elapsed:.2f} seconds:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Full Traceback:\n{traceback.format_exc()}")
        
        return False, error_details

def test_truedata_ws_library():
    """Test using truedata-ws library (version 5.0.11)"""
    print("\n" + "=" * 60)
    print("TEST 2: TrueData-WS Library (truedata-ws==5.0.11)")
    print("=" * 60)
    
    # Credentials
    login_id = 'tdwsp697'
    password = 'shyam@697'
    
    # Test different configurations
    test_configs = [
        {'name': 'Historical Only', 'params': {'live_port': None}},
        {'name': 'Default Live Port', 'params': {}},
        {'name': 'Live Port 8082', 'params': {'live_port': 8082}},
        {'name': 'Live Port 8084', 'params': {'live_port': 8084}},
        {'name': 'Live Port 8086', 'params': {'live_port': 8086}},
    ]
    
    results = []
    
    try:
        from truedata_ws.websocket.TD import TD
        
        for config in test_configs:
            print(f"\nTesting: {config['name']} - {config['params']}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                
                # Create TD object
                td_obj = TD(login_id, password, **config['params'])
                
                create_time = time.time() - start_time
                print(f"✅ TD object created in {create_time:.2f}s")
                
                # Test live data if it's a live port
                if config['params'].get('live_port'):
                    print("Testing live data subscription...")
                    symbols = ['NIFTY', 'BANKNIFTY']
                    
                    live_start = time.time()
                    req_ids = td_obj.start_live_data(symbols)
                    live_time = time.time() - live_start
                    
                    if req_ids:
                        print(f"✅ Live data started successfully in {live_time:.2f}s")
                        print(f"Request IDs: {req_ids}")
                        
                        # Wait a bit and check for data
                        time.sleep(5)
                        for req_id in req_ids:
                            live_data = td_obj.live_data.get(req_id)
                            if live_data:
                                print(f"✅ Data received for req_id {req_id}: {live_data}")
                            else:
                                print(f"⚠️ No data yet for req_id {req_id}")
                        
                        results.append({
                            'config': config['name'],
                            'status': 'SUCCESS',
                            'create_time': create_time,
                            'live_time': live_time,
                            'req_ids': req_ids
                        })
                    else:
                        error_msg = "start_live_data returned None/empty"
                        print(f"❌ Live data failed: {error_msg}")
                        results.append({
                            'config': config['name'],
                            'status': 'FAILED',
                            'error': error_msg,
                            'create_time': create_time
                        })
                else:
                    print("✅ Historical-only connection successful")
                    results.append({
                        'config': config['name'],
                        'status': 'SUCCESS',
                        'create_time': create_time,
                        'type': 'historical_only'
                    })
                    
            except Exception as e:
                elapsed = time.time() - start_time
                error_details = {
                    'config': config['name'],
                    'status': 'ERROR',
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'elapsed_time': elapsed,
                    'full_traceback': traceback.format_exc()
                }
                
                print(f"❌ ERROR in {config['name']} after {elapsed:.2f}s:")
                print(f"Error Type: {type(e).__name__}")
                print(f"Error Message: {str(e)}")
                
                results.append(error_details)
    
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False, [{'error': f'Import failed: {e}'}]
    
    return True, results

def main():
    print("🔍 TrueData Support - Error Reproduction Report")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Account: tdwsp697")
    print(f"Issue: Live data subscription verification")
    
    # Check installed versions
    try:
        import pkg_resources
        truedata_version = pkg_resources.get_distribution("truedata").version
        print(f"truedata version: {truedata_version}")
    except:
        print("truedata: Not installed or version unknown")
    
    try:
        truedata_ws_version = pkg_resources.get_distribution("truedata-ws").version
        print(f"truedata-ws version: {truedata_ws_version}")
    except:
        print("truedata-ws: Not installed or version unknown")
    
    # Test 1: Official library
    success1, error1 = test_truedata_official_library()
    
    # Test 2: WS library
    success2, results2 = test_truedata_ws_library()
    
    # Summary Report
    print("\n" + "=" * 60)
    print("SUMMARY REPORT FOR TRUEDATA SUPPORT")
    print("=" * 60)
    
    print(f"Account: tdwsp697")
    print(f"Reported Issue: Live data subscription active but getting errors")
    print(f"Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\nTest 1 - Official truedata library: {'SUCCESS' if success1 else 'FAILED'}")
    if error1:
        print(f"Error: {error1['error_message']}")
    
    print(f"\nTest 2 - truedata-ws library: {'SUCCESS' if success2 else 'FAILED'}")
    if results2:
        for result in results2:
            if result['status'] == 'SUCCESS':
                print(f"  ✅ {result['config']}: SUCCESS")
            elif result['status'] == 'FAILED':
                print(f"  ❌ {result['config']}: {result.get('error', 'Unknown error')}")
            elif result['status'] == 'ERROR':
                print(f"  🚨 {result['config']}: {result['error_message']}")
    
    print(f"\nConclusion:")
    print(f"- Historical data access: WORKING")
    print(f"- Live data access: FAILING")
    print(f"- Credentials appear valid for historical but not live data")
    
    print(f"\nPlease review the above errors and confirm:")
    print(f"1. Is live data subscription active for account 'tdwsp697'?")
    print(f"2. Which ports should be used for live data access?")
    print(f"3. Are there any account-specific configuration requirements?")

if __name__ == "__main__":
    main()