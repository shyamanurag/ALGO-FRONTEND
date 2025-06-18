# TRUEDATA SUPPORT TICKET - EXACT CODE & ERROR REPRODUCTION

## Account Details
- **Login ID**: `tdwsp697`
- **Password**: `shyam@697`
- **Reported Issue**: Live data subscription shows as active but returns "User Subscription Expired"

## Environment Details
- **Python Version**: 3.11+
- **truedata Library**: 7.0.0
- **truedata-ws Library**: 5.0.11
- **Operating System**: Linux (Kubernetes container)
- **Date/Time**: 2025-06-18 11:25:00 UTC

## EXACT CODE BEING USED

### Test 1: Official TrueData Library (truedata==7.0.0)

```python
from truedata import TD_live

# Credentials
login_id = 'tdwsp697'
password = 'shyam@697'

# This is the exact code that fails
td_obj = TD_live(login_id, password)

# Attempting to get LTP
result = td_obj.get_ltp(['NIFTY'])
```

**EXACT ERROR OUTPUT:**
```
2025-06-18 11:23:59,414 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:04,686 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:09,970 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:15,246 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:20,517 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:25,788 - ERROR - [Errno 111] Connection refused - goodbye
2025-06-18 11:24:31,086 - ERROR - [Errno 111] Connection refused - goodbye
```

### Test 2: TrueData-WS Library (truedata-ws==5.0.11)

```python
from truedata_ws.websocket.TD import TD

# Credentials
login_id = 'tdwsp697'
password = 'shyam@697'

# Test 1: Historical data (THIS WORKS)
td_historical = TD(login_id, password, live_port=None)
# Result: ✅ SUCCESS - "Connected successfully to TrueData Historical Data Service"

# Test 2: Live data on default port (THIS FAILS)
td_live = TD(login_id, password, live_port=8082)

# Attempting to start live data
symbols = ['NIFTY']
req_ids = td_live.start_live_data(symbols)
```

**EXACT ERROR OUTPUT:**
```
(2025-06-18 11:24:47,903) WARNING :: Connected successfully to TrueData Historical Data Service...
(2025-06-18 11:24:49,000) ERROR :: The request encountered an error - User Subscription Expired
(2025-06-18 11:24:51,150) ERROR :: The request encountered an error - User Subscription Expired
(2025-06-18 11:24:53,279) ERROR :: The request encountered an error - User Subscription Expired
(2025-06-18 11:24:55,320) ERROR :: The request encountered an error - User Subscription Expired
[...continues repeating every 2 seconds...]
```

## ANALYSIS

### What Works ✅
1. **Library Import**: Both libraries import successfully
2. **Historical Data Connection**: `TD(login_id, password, live_port=None)` connects successfully
3. **Authentication**: Credentials are accepted for historical data
4. **Connection Message**: "Connected successfully to TrueData Historical Data Service"

### What Fails ❌
1. **Official truedata Library**: Complete connection failure with "Connection refused"
2. **Live Data Subscription**: "User Subscription Expired" error on all live ports
3. **Live Ports Tested**: 8082, 8084, 8086 (all return same error)

## SPECIFIC QUESTIONS FOR TRUEDATA SUPPORT

1. **Subscription Status**: 
   - Is live data subscription actually active for account `tdwsp697`?
   - What is the difference between historical and live data subscriptions?

2. **Port Configuration**:
   - Which ports should be used for live data access in 2025?
   - Are there account-specific port assignments?

3. **Library Compatibility**:
   - Which library version should be used: `truedata==7.0.0` or `truedata-ws==5.0.11`?
   - Are there known issues with the current versions?

4. **Connection Method**:
   - Is the connection code correct for the current API?
   - Are there additional authentication steps required?

## CURRENT IMPACT
- Historical data access is working fine
- Live data access is completely blocked
- This is preventing real-time trading operations
- Need urgent resolution for live trading to proceed

## REQUEST
Please confirm:
1. The exact subscription status for live data on account `tdwsp697`
2. The correct code pattern for live data access in 2025
3. Any account-specific configuration requirements
4. Expected timeline for resolution

---
**Generated**: 2025-06-18 11:25:00 UTC  
**Contact**: Development Team  
**Priority**: High - Production Impact