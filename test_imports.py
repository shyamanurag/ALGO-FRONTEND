#!/usr/bin/env python3
import sys
sys.path.append('/app/backend')

try:
    from src.core.order_manager import OrderManager
    print("✅ OrderManager imported successfully")
except Exception as e:
    print(f"❌ OrderManager import failed: {e}")

try:
    from src.core.risk_manager import RiskManager
    print("✅ RiskManager imported successfully")
except Exception as e:
    print(f"❌ RiskManager import failed: {e}")

try:
    from src.core.position_tracker import PositionTracker
    print("✅ PositionTracker imported successfully")
except Exception as e:
    print(f"❌ PositionTracker import failed: {e}")