#!/usr/bin/env python3
"""
TrueData Support - Minimal Test Case
Account: tdwsp697
Run this file to reproduce the exact issue
"""

def test_truedata_libraries():
    """Minimal test case for TrueData support to reproduce the issue"""
    
    print("=" * 50)
    print("TRUEDATA SUPPORT - MINIMAL TEST CASE")
    print("Account: tdwsp697")
    print("=" * 50)
    
    # Test 1: truedata-ws library (recommended approach)
    print("\n1. Testing truedata-ws library...")
    try:
        from truedata_ws.websocket.TD import TD
        
        # Credentials
        login_id = 'tdwsp697'
        password = 'shyam@697'
        
        print("1a. Testing historical data connection...")
        td_hist = TD(login_id, password, live_port=None)
        print("✅ Historical connection: SUCCESS")
        
        print("1b. Testing live data connection (assigned port 8084)...")
        td_live = TD(login_id, password, live_port=8084)
        print("✅ Live connection object created")
        
        print("1c. Testing live data subscription...")
        symbols = ['NIFTY', 'BANKNIFTY']
        req_ids = td_live.start_live_data(symbols)
        print(f"Live data request IDs: {req_ids}")
        
        if req_ids:
            print("✅ Live data subscription: SUCCESS")
            import time
            time.sleep(10)
            
            for req_id in req_ids:
                data = td_live.live_data.get(req_id)
                if data:
                    symbol = data.get('symbol', 'Unknown')
                    ltp = data.get('ltp', 'None')
                    print(f"✅ Data structure received for {symbol} (req_id {req_id})")
                    print(f"   LTP: {ltp}")
                    print(f"   Sample fields: {list(data.keys())[:5]}...")
                    
                    if ltp is None:
                        print(f"   ⚠️ ISSUE: LTP is None - data fields not populating")
                    else:
                        print(f"   ✅ SUCCESS: Live price data flowing!")
                else:
                    print(f"⚠️ No data structure for request {req_id}")
        else:
            print("❌ Live data subscription: FAILED")
            
    except Exception as e:
        print(f"❌ truedata-ws ERROR: {e}")
        import traceback
        print(traceback.format_exc())
    
    # Test 2: Original truedata library
    print("\n2. Testing original truedata library...")
    try:
        from truedata import TD_live
        
        print("2a. Creating TD_live object...")
        td_obj = TD_live('tdwsp697', 'shyam@697')
        print("✅ TD_live created successfully")
        
        print("2b. Testing get_ltp...")
        result = td_obj.get_ltp(['NIFTY'])
        print(f"✅ LTP result: {result}")
        
    except Exception as e:
        print(f"❌ truedata ERROR: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("Please review the above output and confirm:")
    print("1. Should live data work for account 'tdwsp697'?")
    print("2. What is the correct way to access live data?")
    print("3. Are there additional subscription requirements?")
    print("=" * 50)

if __name__ == "__main__":
    test_truedata_libraries()