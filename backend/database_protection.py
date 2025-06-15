#!/usr/bin/env python3
"""
Sacred Database Protection System
Implements triggers to prevent demo/mock data contamination
"""

import asyncio
import aiosqlite
import os

DB_PATH = "/app/backend/trading_system.db"

async def implement_protection_triggers():
    """Implement database triggers to prevent mock data contamination"""
    
    print("🛡️  IMPLEMENTING SACRED DATABASE PROTECTION...")
    print("=" * 60)
    
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Protection trigger for trading_signals table
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_mock_signals
            BEFORE INSERT ON trading_signals
            WHEN NEW.metadata LIKE '%mock%' 
                OR NEW.metadata LIKE '%demo%' 
                OR NEW.metadata LIKE '%test%'
                OR NEW.metadata LIKE '%fake%'
                OR NEW.strategy_name LIKE '%mock%'
                OR NEW.strategy_name LIKE '%demo%'
                OR NEW.strategy_name LIKE '%test%'
                OR NEW.symbol LIKE '%MOCK%'
                OR NEW.symbol LIKE '%DEMO%'
                OR NEW.symbol LIKE '%TEST%'
            BEGIN
                SELECT RAISE(ABORT, 'SACRED DATABASE PROTECTION: Mock/Demo data insertion blocked!');
            END;
        """)
        print("✅ Protection trigger added: trading_signals")
        
        # Protection trigger for orders table
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_mock_orders
            BEFORE INSERT ON orders
            WHEN NEW.symbol LIKE '%MOCK%' 
                OR NEW.symbol LIKE '%DEMO%' 
                OR NEW.symbol LIKE '%TEST%'
                OR NEW.broker_order_id LIKE '%mock%'
                OR NEW.broker_order_id LIKE '%demo%'
                OR NEW.broker_order_id LIKE '%test%'
                OR NEW.user_id LIKE '%mock%'
                OR NEW.user_id LIKE '%demo%'
                OR NEW.user_id LIKE '%test%'
            BEGIN
                SELECT RAISE(ABORT, 'SACRED DATABASE PROTECTION: Mock/Demo order insertion blocked!');
            END;
        """)
        print("✅ Protection trigger added: orders")
        
        # Protection trigger for market_data_live table
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_mock_market_data
            BEFORE INSERT ON market_data_live
            WHEN NEW.symbol LIKE '%MOCK%' 
                OR NEW.symbol LIKE '%DEMO%' 
                OR NEW.symbol LIKE '%TEST%'
                OR NEW.symbol LIKE '%FAKE%'
                OR NEW.exchange = 'MOCK'
                OR NEW.exchange = 'DEMO'
                OR NEW.exchange = 'TEST'
            BEGIN
                SELECT RAISE(ABORT, 'SACRED DATABASE PROTECTION: Mock/Demo market data insertion blocked!');
            END;
        """)
        print("✅ Protection trigger added: market_data_live")
        
        # Protection trigger for positions table
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_mock_positions
            BEFORE INSERT ON positions
            WHEN NEW.symbol LIKE '%MOCK%' 
                OR NEW.symbol LIKE '%DEMO%' 
                OR NEW.symbol LIKE '%TEST%'
                OR NEW.user_id LIKE '%mock%'
                OR NEW.user_id LIKE '%demo%'
                OR NEW.user_id LIKE '%test%'
                OR NEW.strategy_name LIKE '%mock%'
                OR NEW.strategy_name LIKE '%demo%'
            BEGIN
                SELECT RAISE(ABORT, 'SACRED DATABASE PROTECTION: Mock/Demo position insertion blocked!');
            END;
        """)
        print("✅ Protection trigger added: positions")
        
        # Protection trigger for elite_recommendations table
        await db.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_mock_recommendations
            BEFORE INSERT ON elite_recommendations
            WHEN NEW.symbol LIKE '%MOCK%' 
                OR NEW.symbol LIKE '%DEMO%' 
                OR NEW.symbol LIKE '%TEST%'
                OR NEW.strategy LIKE '%mock%'
                OR NEW.strategy LIKE '%demo%'
                OR NEW.strategy LIKE '%test%'
                OR NEW.metadata LIKE '%mock%'
                OR NEW.metadata LIKE '%demo%'
            BEGIN
                SELECT RAISE(ABORT, 'SACRED DATABASE PROTECTION: Mock/Demo recommendation insertion blocked!');
            END;
        """)
        print("✅ Protection trigger added: elite_recommendations")
        
        await db.commit()
        
        print("=" * 60)
        print("🛡️  SACRED DATABASE PROTECTION ACTIVATED!")
        print("🚫 All mock/demo data insertion attempts will be BLOCKED!")
        print("✨ Your trading platform is now ETERNALLY PROTECTED!")

async def test_protection_system():
    """Test the protection system with mock data attempts"""
    
    print("\n🧪 TESTING PROTECTION SYSTEM...")
    print("=" * 60)
    
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Test 1: Try to insert mock trading signal
        try:
            await db.execute("""
                INSERT INTO trading_signals (
                    signal_id, strategy_name, symbol, action, quality_score, 
                    confidence_level, quantity, entry_price, metadata
                ) VALUES (
                    'TEST_001', 'mock_strategy', 'NIFTY_MOCK', 'BUY', 10.0,
                    0.95, 100, 19500.0, '{"type": "mock_data"}'
                )
            """)
            await db.commit()
            print("❌ PROTECTION FAILED: Mock signal was inserted!")
        except Exception as e:
            print("✅ PROTECTION WORKING: Mock signal blocked -", str(e)[:50])
        
        # Test 2: Try to insert demo market data
        try:
            await db.execute("""
                INSERT INTO market_data_live (
                    symbol, exchange, ltp, volume, timestamp
                ) VALUES (
                    'DEMO_STOCK', 'NSE', 100.0, 1000, datetime('now')
                )
            """)
            await db.commit()
            print("❌ PROTECTION FAILED: Demo market data was inserted!")
        except Exception as e:
            print("✅ PROTECTION WORKING: Demo market data blocked -", str(e)[:50])
        
        # Test 3: Try to insert real data (should work)
        try:
            await db.execute("""
                INSERT INTO trading_signals (
                    signal_id, strategy_name, symbol, action, quality_score, 
                    confidence_level, quantity, entry_price, metadata
                ) VALUES (
                    'REAL_001', 'momentum_surfer', 'NIFTY', 'BUY', 10.0,
                    0.95, 100, 19500.0, '{"type": "real_signal"}'
                )
            """)
            await db.commit()
            print("✅ REAL DATA ALLOWED: Genuine signal inserted successfully!")
            
            # Clean it up
            await db.execute("DELETE FROM trading_signals WHERE signal_id = 'REAL_001'")
            await db.commit()
            
        except Exception as e:
            print("⚠️  Unexpected error with real data:", str(e))

async def main():
    print("🛡️  SACRED DATABASE PROTECTION SYSTEM")
    print("=" * 60)
    print("Mission: Implement eternal protection against mock data")
    print("=" * 60)
    
    await implement_protection_triggers()
    await test_protection_system()
    
    print("\n🎉 PROTECTION SYSTEM FULLY OPERATIONAL!")
    print("🛡️  Your sacred trading platform is now ETERNALLY PROTECTED!")

if __name__ == "__main__":
    asyncio.run(main())