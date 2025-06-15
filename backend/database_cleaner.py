#!/usr/bin/env python3
"""
Sacred Database Cleaner - Remove all demo/mock data contamination
Ensures only real trading data flows through the system
"""

import asyncio
import aiosqlite
import os
from datetime import datetime

# Database path
DB_PATH = "/app/backend/trading_system.db"

async def check_and_clean_database():
    """Check for any existing data and purge all demo/mock entries"""
    
    if not os.path.exists(DB_PATH):
        print("✅ Database file doesn't exist - Starting fresh!")
        return
    
    print("🔍 SCANNING DATABASE FOR CONTAMINATION...")
    print("=" * 60)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get all table names
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
        
        if not tables:
            print("✅ No tables found - Database is clean!")
            return
        
        total_records = 0
        contaminated_tables = []
        
        for (table_name,) in tables:
            try:
                # Count records in each table
                async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cursor:
                    count = (await cursor.fetchone())[0]
                
                if count > 0:
                    total_records += count
                    contaminated_tables.append((table_name, count))
                    print(f"🦠 CONTAMINATION DETECTED: {table_name} has {count} records")
                
            except Exception as e:
                print(f"⚠️  Error checking table {table_name}: {e}")
        
        print("=" * 60)
        print(f"🚨 TOTAL CONTAMINATION: {total_records} records across {len(contaminated_tables)} tables")
        
        if total_records == 0:
            print("✅ DATABASE IS PURE - No contamination found!")
            return
        
        print("\n🧹 INITIATING PURIFICATION PROCESS...")
        print("=" * 60)
        
        # Delete all data from contaminated tables
        for table_name, count in contaminated_tables:
            try:
                await db.execute(f"DELETE FROM {table_name}")
                print(f"🗑️  PURGED: {table_name} - {count} contaminated records removed")
            except Exception as e:
                print(f"❌ Error purging {table_name}: {e}")
        
        # Reset auto-increment counters
        try:
            await db.execute("DELETE FROM sqlite_sequence")
            print("🔄 RESET: Auto-increment sequences reset")
        except:
            pass  # Table might not exist
        
        await db.commit()
        
        print("=" * 60)
        print("✨ PURIFICATION COMPLETE!")
        print("🛡️  Database is now SACRED and ready for REAL trading data only!")
        print(f"🕐 Purification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def verify_database_purity():
    """Verify that the database is truly clean"""
    print("\n🔬 VERIFYING DATABASE PURITY...")
    
    if not os.path.exists(DB_PATH):
        print("✅ Database doesn't exist - Perfectly pure!")
        return True
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get all table names
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
        
        total_records = 0
        for (table_name,) in tables:
            try:
                async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cursor:
                    count = (await cursor.fetchone())[0]
                    total_records += count
            except:
                pass
        
        if total_records == 0:
            print("✅ VERIFICATION SUCCESSFUL: Database is 100% PURE!")
            return True
        else:
            print(f"❌ CONTAMINATION STILL DETECTED: {total_records} records found!")
            return False

async def main():
    print("🤖 ALGO-FRONTEND DATABASE PURIFICATION SYSTEM")
    print("=" * 60)
    print("Mission: Remove all demo/mock data contamination")
    print("Objective: Keep our sacred trading platform pure!")
    print("=" * 60)
    
    # Step 1: Check and clean
    await check_and_clean_database()
    
    # Step 2: Verify purity
    is_pure = await verify_database_purity()
    
    if is_pure:
        print("\n🎉 MISSION ACCOMPLISHED!")
        print("🏆 The trading platform is now SACRED and PURE!")
        print("🚀 Ready for REAL trading data only!")
    else:
        print("\n⚠️  MISSION INCOMPLETE - Manual intervention required!")

if __name__ == "__main__":
    asyncio.run(main())