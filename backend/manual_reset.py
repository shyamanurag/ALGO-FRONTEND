#!/usr/bin/env python3
"""
Manual Reset Script for Autonomous Trading Engine
Clears all phantom trading data and resets for clean state
"""

import sys
import os
sys.path.append('/app/backend')

async def reset_autonomous_engine():
    """Reset the autonomous engine completely"""
    try:
        from autonomous_trading_engine import get_autonomous_engine
        
        engine = get_autonomous_engine()
        
        print("🔄 Resetting autonomous trading engine...")
        
        # Reset all strategy data
        for strategy_name in engine.strategies:
            engine.strategies[strategy_name].update({
                "trades_today": 0,
                "pnl": 0.0,
                "win_rate": 0.0,
                "last_signal_time": None,
                "active": False  # Deactivate strategies
            })
        
        # Clear all positions and history
        engine.active_positions.clear()
        engine.trade_history.clear()
        engine.daily_pnl = 0.0
        engine.used_capital = 0.0
        engine.market_data_buffer.clear()
        engine.running = False
        
        print("✅ Autonomous engine reset complete!")
        print("📊 All strategies deactivated")
        print("💰 P&L reset to ₹0")
        print("📈 Trade history cleared")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting engine: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(reset_autonomous_engine())
    
    if success:
        print("\n🎉 Reset successful! Autonomous Monitor should now show clean data.")
    else:
        print("\n❌ Reset failed!")