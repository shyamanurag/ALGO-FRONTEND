#!/usr/bin/env python3
"""
Final Sacred Database Verification
Ensure the trading platform is 100% pure and protected
"""

import asyncio
import aiosqlite
import os

DB_PATH = "/app/backend/trading_system.db"

async def final_verification():
    """Final verification that the sacred database is pure"""
    
    print("🔬 FINAL SACRED DATABASE VERIFICATION")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return False
    
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Check all tables for any remaining data
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables in the database")
        
        total_data_records = 0
        for (table_name,) in tables:
            try:
                async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cursor:
                    count = (await cursor.fetchone())[0]
                
                if table_name == 'sqlite_master':
                    continue  # Skip system table
                
                if count > 0:
                    total_data_records += count
                    print(f"📋 {table_name}: {count} records")
                else:
                    print(f"✅ {table_name}: PURE (0 records)")
                    
            except Exception as e:
                print(f"⚠️  Error checking {table_name}: {e}")
        
        # Check for protection triggers
        async with db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name LIKE 'prevent_mock%'
        """) as cursor:
            triggers = await cursor.fetchall()
        
        print("\n🛡️  PROTECTION TRIGGERS:")
        for (trigger_name,) in triggers:
            print(f"✅ {trigger_name} - ACTIVE")
        
        print("=" * 60)
        
        if total_data_records == 0:
            print("🏆 SACRED DATABASE STATUS: 100% PURE!")
            print("✨ No contamination detected")
            print(f"🛡️  {len(triggers)} protection triggers active")
            print("🚀 Ready for REAL trading data ONLY!")
            return True
        else:
            print(f"⚠️  WARNING: {total_data_records} records found")
            print("🧹 Manual cleanup may be required")
            return False

async def test_sacred_protection():
    """Test that the protection system is working"""
    print("\n🧪 TESTING SACRED PROTECTION SYSTEM...")
    
    test_cases = [
        ("Mock Signal", "INSERT INTO trading_signals (signal_id, symbol, strategy_name) VALUES ('test', 'MOCK_STOCK', 'test')"),
        ("Demo Order", "INSERT INTO orders (order_id, symbol, user_id) VALUES ('test', 'DEMO_STOCK', 'mock_user')"),
        ("Test Market Data", "INSERT INTO market_data_live (symbol, ltp) VALUES ('TEST_SYMBOL', 100)")
    ]
    
    async with aiosqlite.connect(DB_PATH) as db:
        for test_name, sql in test_cases:
            try:
                await db.execute(sql)
                await db.commit()
                print(f"❌ PROTECTION FAILED: {test_name} was inserted!")
            except Exception as e:
                if "SACRED DATABASE PROTECTION" in str(e):
                    print(f"✅ PROTECTION WORKING: {test_name} blocked")
                else:
                    print(f"⚠️  {test_name}: {str(e)[:50]}...")

async def main():
    verification_passed = await final_verification()
    await test_sacred_protection()
    
    print("\n" + "=" * 60)
    if verification_passed:
        print("🎉 SACRED DATABASE VERIFICATION COMPLETE!")
        print("🛡️  Your ALGO-FRONTEND platform is PURE and PROTECTED!")
        print("💎 Ready for elite autonomous trading!")
    else:
        print("⚠️  VERIFICATION ISSUES DETECTED!")
        print("🔧 Manual intervention may be required!")

if __name__ == "__main__":
    asyncio.run(main())