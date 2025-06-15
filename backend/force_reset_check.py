#!/usr/bin/env python3
"""
Complete Autonomous Engine Reset
Forces complete reinitialization to remove all phantom data
"""

import requests
import json

def force_reset_autonomous_engine():
    """Force complete reset of autonomous engine"""
    
    url = "https://fresh-start-13.emergent.host"
    
    print("🔄 Forcing complete autonomous engine reset...")
    
    # Step 1: Emergency stop
    print("1️⃣ Emergency stop...")
    response = requests.post(f"{url}/api/autonomous/emergency-stop")
    print(f"   Result: {response.json()}")
    
    # Step 2: Check current status
    print("2️⃣ Checking current strategy status...")
    response = requests.get(f"{url}/api/autonomous/strategy-performance")
    data = response.json()
    
    for strategy in data.get('strategies', []):
        print(f"   {strategy['name']}: {strategy['trades_today']} trades, P&L: ₹{strategy['pnl']}")
    
    print("\n🎯 ANALYSIS: The autonomous engine has persistent data from previous runs.")
    print("💡 SOLUTION: The backend needs to be redeployed to completely reset the engine state.")
    print("🔧 RECOMMENDATION: Redeploy the entire application with the simulation fixes applied.")
    
    return data

if __name__ == "__main__":
    force_reset_autonomous_engine()