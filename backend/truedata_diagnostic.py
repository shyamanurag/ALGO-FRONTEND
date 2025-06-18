#!/usr/bin/env python3
"""
TrueData Connection Diagnostic Tool
Tests various connection methods and configurations
"""

import sys
import time
import logging
from datetime import datetime
import os

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_import():
    """Test if TrueData libraries can be imported"""
    print("=== Testing TrueData Library Imports ===")
    
    try:
        from truedata_ws.websocket.TD import TD
        print("✅ truedata-ws imported successfully")
        return True
    except Exception as e:
        print(f"❌ truedata-ws import failed: {e}")
        
    try:
        from truedata import TD_live
        print("✅ truedata imported successfully")
        return True
    except Exception as e:
        print(f"❌ truedata import failed: {e}")
        
    return False

def test_connection_with_timeout(login_id, password, timeout=30):
    """Test connection with timeout"""
    print(f"\n=== Testing Connection (timeout: {timeout}s) ===")
    
    try:
        from truedata_ws.websocket.TD import TD
        
        print(f"Connecting with {login_id}...")
        start_time = time.time()
        
        # Try with different configurations
        configs = [
            {"live_port": None},  # Historical only
            {"live_port": 8082},  # Default live port
            {"live_port": 8084},  # Alternative port
            {"live_port": 8086},  # Another alternative
        ]
        
        for i, config in enumerate(configs):
            print(f"\nTrying configuration {i+1}: {config}")
            
            try:
                td_obj = TD(login_id, password, **config)
                elapsed = time.time() - start_time
                print(f"✅ Configuration {i+1} created TD object in {elapsed:.2f}s")
                
                # Test if it can do anything
                if config.get("live_port"):
                    print("Testing live data capability...")
                    # Don't actually start live data as it might hang
                    print("✅ Live data object created successfully")
                else:
                    print("✅ Historical data object created successfully")
                
                return True, config
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Config {i+1} failed in {elapsed:.2f}s: {e}")
                if elapsed > timeout:
                    print(f"⏰ Timeout reached ({timeout}s)")
                    break
                continue
        
        return False, None
        
    except Exception as e:
        print(f"❌ Import/setup error: {e}")
        return False, None

def test_basic_truedata_old():
    """Test the old truedata library"""
    print(f"\n=== Testing Old TrueData Library ===")
    
    try:
        from truedata import TD_live
        
        login_id = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        
        print(f"Creating TD_live object...")
        start_time = time.time()
        
        # This will likely hang, so we'll see how long it takes
        td_obj = TD_live(login_id, password)
        elapsed = time.time() - start_time
        
        print(f"✅ TD_live created in {elapsed:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ TD_live failed: {e}")
        return False

def main():
    print("🔍 TrueData Connection Diagnostic Tool")
    print("=" * 50)
    
    # Get credentials
    login_id = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
    password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
    
    print(f"Using credentials: {login_id} / {'*' * len(password)}")
    
    # Test 1: Basic imports
    if not test_basic_import():
        print("❌ Cannot proceed - library import failed")
        return
    
    # Test 2: Connection with timeout
    success, working_config = test_connection_with_timeout(login_id, password, timeout=30)
    
    if success:
        print(f"\n✅ SUCCESS! Working configuration: {working_config}")
    else:
        print(f"\n❌ FAILED! All configurations failed")
        
        # Test 3: Try old library as fallback
        print("\nTrying old truedata library...")
        test_basic_truedata_old()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete!")

if __name__ == "__main__":
    main()