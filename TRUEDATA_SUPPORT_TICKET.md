# TRUEDATA SUPPORT TICKET - UPDATED WITH PORT 8084 RESULTS

## Account Details
- **Login ID**: `tdwsp697`
- **Password**: `shyam@697`
- **Assigned Port**: `8084` (as provided by TrueData)
- **Issue**: Live data connection successful but data fields return None

## 🎉 **BREAKTHROUGH - PORT 8084 WORKS!**

### ✅ What Now Works (After Using Port 8084)

```python
from truedata_ws.websocket.TD import TD

# Using TrueData assigned port 8084
td_obj = TD('tdwsp697', 'shyam@697', live_port=8084)

# Live data subscription
symbols = ['NIFTY', 'BANKNIFTY']
req_ids = td_obj.start_live_data(symbols)
# Returns: [2000, 2001] ✅ SUCCESS!
```

**RESULT:**
- ✅ Connection to port 8084: **SUCCESS**
- ✅ Live data subscription: **SUCCESS** 
- ✅ Request IDs returned: `[2000, 2001]`
- ✅ Data objects received with correct symbol names

### ⚠️ Current Issue - Data Fields Are None

**Data Structure Received:**
```python
{
    'symbol': 'NIFTY',          # ✅ Correct
    'ltp': None,                # ❌ Should have price
    'day_open': None,           # ❌ Should have price  
    'day_high': None,           # ❌ Should have price
    'day_low': None,            # ❌ Should have price
    'best_bid_price': None,     # ❌ Should have price
    'best_ask_price': None,     # ❌ Should have price
    'oi': None,                 # ❌ Should have value
    'volume': None,             # ❌ Should have value
    # ... all other fields are None
}
```

## Environment Details
- **Python Version**: 3.11+
- **truedata-ws Library**: 5.0.11
- **Operating System**: Linux (Kubernetes container)
- **Date/Time**: 2025-06-18 11:32:00 UTC
- **Test Time**: During market hours (Indian market)

## Specific Questions for TrueData Support

### 1. **Data Population**
- Why are all price/volume fields returning `None`?
- Is there a delay before data starts populating?
- Are there additional steps needed after `start_live_data()`?

### 2. **Market Timing**
- Does live data only flow during active market hours?
- Should we expect data during pre-market or after-hours?
- What timezone does the data service operate in?

### 3. **Symbol Format**
- Are we using the correct symbol names ('NIFTY', 'BANKNIFTY')?
- Should we use different formats like 'NIFTY-I' or token IDs?

### 4. **Account Configuration**
- Is our account fully activated for live data on port 8084?
- Are there any account-specific settings we need to configure?

## Code That Works (For TrueData Testing)

```python
from truedata_ws.websocket.TD import TD
import time

# Connection code that works
td_obj = TD('tdwsp697', 'shyam@697', live_port=8084)

# Start live data
req_ids = td_obj.start_live_data(['NIFTY', 'BANKNIFTY'])
print(f"Request IDs: {req_ids}")  # Should show [2000, 2001]

# Wait and check data
time.sleep(10)
for req_id in req_ids:
    data = td_obj.live_data.get(req_id)
    print(f"Data for {req_id}: {data}")
    # All fields show None - this is the issue to resolve
```

## Request for TrueData Support

Since the connection is now working with port 8084, we need guidance on:

1. **How to get actual price data to populate in the fields**
2. **Whether there are market timing restrictions**  
3. **If additional authentication/activation steps are needed**
4. **Expected data update frequency**

This is now a **data population issue** rather than a connection issue.

---
**Updated**: 2025-06-18 11:32:00 UTC  
**Status**: Connection Working, Data Fields Empty  
**Priority**: Medium - Technical Configuration