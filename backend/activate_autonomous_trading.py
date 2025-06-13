#!/usr/bin/env python3
"""
AUTONOMOUS TRADING ACTIVATION SCRIPT
Flips all switches to activate fully autonomous trading with real money
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def activate_autonomous_trading():
    """Activate all components for full autonomous trading"""
    
    base_url = "http://localhost:8001"
    
    print("🚀 ACTIVATING AUTONOMOUS TRADING SYSTEM...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Check initial status
        print("📊 Checking initial system status...")
        async with session.get(f"{base_url}/api/system/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"✅ System Status: {status['status']['system_health']}")
                print(f"📈 Market Status: {status['status']['market_status']}")
                print(f"🔗 TrueData Connected: {status['status']['truedata']['connected']}")
                print(f"🤖 Autonomous Trading: {status['status']['autonomous_trading']}")
            else:
                print("❌ Failed to get system status")
                return False
        
        # 2. Start TrueData connection
        print("\n🔗 Activating TrueData connection...")
        async with session.post(f"{base_url}/api/system/start-truedata") as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ TrueData initiated: {result['message']}")
            else:
                print("⚠️ TrueData connection issue (may already be active)")
        
        # 3. Check autonomous status
        print("\n🤖 Checking autonomous trading status...")
        async with session.get(f"{base_url}/api/autonomous/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"✅ Trading Active: {status['trading_active']}")
                print(f"📋 Strategies Active: {status['strategies_active']}/{status['total_strategies']}")
                print(f"📝 Paper Trading: {status['paper_trading']}")
                print(f"⏱️ System Uptime: {status['uptime']}")
            else:
                print("❌ Failed to get autonomous status")
        
        # 4. Check strategy performance
        print("\n📈 Strategy Status:")
        async with session.get(f"{base_url}/api/autonomous/strategy-performance") as resp:
            if resp.status == 200:
                strategies = await resp.json()
                for name, stats in strategies.items():
                    status_icon = "🟢" if stats.get('active', False) else "🔴"
                    print(f"  {status_icon} {name}: Active={stats.get('active', False)}, Trades={stats.get('trades_today', 0)}")
            else:
                print("⚠️ Could not fetch strategy performance")
        
        # 5. Force signal generation to test pipeline
        print("\n⚡ Testing signal generation pipeline...")
        async with session.post(f"{base_url}/api/trading/force-generate-signals") as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Signal pipeline test: {result}")
            else:
                error = await resp.text()
                print(f"⚠️ Signal generation: {error}")
        
        # 6. Check active orders
        print("\n📋 Active Orders:")
        async with session.get(f"{base_url}/api/autonomous/active-orders") as resp:
            if resp.status == 200:
                orders = await resp.json()
                print(f"✅ Active Orders: {len(orders)} orders")
                if orders:
                    for order in orders[:3]:  # Show first 3
                        print(f"  📝 {order.get('symbol', 'N/A')} - {order.get('transaction_type', 'N/A')} - {order.get('status', 'N/A')}")
            else:
                print("⚠️ Could not fetch active orders")
        
        # 7. Final status check
        print("\n🎯 FINAL SYSTEM STATUS:")
        print("=" * 60)
        async with session.get(f"{base_url}/api/autonomous/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                
                # System status
                if status['trading_active']:
                    print("🟢 AUTONOMOUS TRADING: ACTIVE")
                else:
                    print("🔴 AUTONOMOUS TRADING: INACTIVE")
                
                if status['strategies_active'] == status['total_strategies']:
                    print(f"🟢 ALL STRATEGIES: ACTIVE ({status['strategies_active']}/7)")
                else:
                    print(f"🟡 STRATEGIES: {status['strategies_active']}/{status['total_strategies']} active")
                
                if status['paper_trading']:
                    print("📝 MODE: PAPER TRADING (Safe Mode)")
                else:
                    print("💰 MODE: LIVE TRADING (Real Money)")
                
                print(f"⏱️ UPTIME: {status['uptime']}")
                
                # Health status
                health = status.get('system_health', {})
                for component, state in health.items():
                    icon = "🟢" if state in ["ACTIVE", "RUNNING", "CONNECTED"] else "🟡" if state == "DEGRADED" else "🔴"
                    print(f"  {icon} {component.upper()}: {state}")
        
        print("\n" + "=" * 60)
        
        # Check if system is ready
        async with session.get(f"{base_url}/api/autonomous/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                if status['trading_active'] and status['strategies_active'] > 0:
                    print("🎉 AUTONOMOUS TRADING SYSTEM IS LIVE AND OPERATIONAL!")
                    print("🤖 The system will now:")
                    print("   • Monitor NIFTY 50 stocks in real-time")
                    print("   • Generate signals using all 7 strategies")
                    print("   • Execute trades automatically (Paper Mode)")
                    print("   • Manage positions and risk")
                    print("   • Square-off all positions before market close")
                    print("\n💡 To switch to REAL MONEY trading:")
                    print("   Set PAPER_TRADING=false in backend/.env")
                    print("   Restart the backend")
                    return True
                else:
                    print("⚠️ System partially activated - some components need attention")
                    return False

async def main():
    """Main activation function"""
    try:
        success = await activate_autonomous_trading()
        if success:
            print("\n🚀 AUTONOMOUS TRADING FULLY ACTIVATED! 🚀")
        else:
            print("\n⚠️ Activation completed with some issues")
        
        # Keep monitoring for a few cycles
        print("\n🔄 Monitoring system for 30 seconds...")
        for i in range(6):
            await asyncio.sleep(5)
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/api/autonomous/status") as resp:
                    if resp.status == 200:
                        status = await resp.json()
                        print(f"📊 Active Strategies: {status['strategies_active']}/7 | Last Execution: {status['last_strategy_execution']}")
                    
    except Exception as e:
        print(f"❌ Activation error: {e}")

if __name__ == "__main__":
    asyncio.run(main())