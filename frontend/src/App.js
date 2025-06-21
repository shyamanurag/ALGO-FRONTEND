import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminDashboard from './components/AdminDashboard';
import AutonomousMonitoring from './components/AutonomousMonitoring';
import EliteRecommendations from './components/EliteRecommendations';
import Navigation from './components/Navigation';
import AdminLogin from './components/AdminLogin';
import LiveIndicesHeader from './components/LiveIndicesHeader';
import LiveAutonomousStatus from './components/LiveAutonomousStatus';
import StrategyMonitoring from './components/StrategyMonitoring';
import AccountManagement from './components/AccountManagement';
import AnalyticsReports from './components/AnalyticsReports';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true); // Set to true for testing
  const [user, setUser] = useState({ name: 'Admin User', role: 'admin' }); // Default user for testing
  const [userRole, setUserRole] = useState('admin');
  const [systemStatus, setSystemStatus] = useState({});
  const [backendConnected, setBackendConnected] = useState(false);
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [realTimeData, setRealTimeData] = useState({});

  // Test API connectivity on startup
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/`);
        const data = await response.json();
        console.log('✅ Backend connection successful:', data);
      } catch (error) {
        console.error('❌ Backend connection failed:', error);
      }
    };
    
    testConnection();
  }, []);

  // WebSocket connection for real-time autonomous trading data  
  useEffect(() => {
    if (!isAuthenticated) return;

    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws/autonomous-data';
    let ws = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    const connectWebSocket = () => {
      try {
        console.log('🔌 Attempting WebSocket connection to:', wsUrl);
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('✅ Autonomous Trading WebSocket connected');
          reconnectAttempts = 0;
          
          // Send initial ping to establish connection
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
              case 'autonomous_trade_executed':
                setRealTimeData(prev => ({
                  ...prev,
                  [`trade_${data.user_id}`]: data.trade_data
                }));
                break;
              case 'strategy_performance_update':
                setRealTimeData(prev => ({
                  ...prev,
                  [`performance_${data.user_id}`]: data.performance_data
                }));
                break;
              case 'account_status_change':
                setConnectedAccounts(prev => 
                  prev.map(account => 
                    account.user_id === data.user_id 
                      ? { ...account, status: data.status }
                      : account
                  )
                );
                break;
              case 'risk_alert':
                console.warn(`Risk Alert for User ${data.user_id}: ${data.message}`);
                break;
              case 'initial_data':
              case 'autonomous_update':
                if (data.system_health) {
                  setSystemStatus(prev => ({
                    ...prev,
                    system_health: data.system_health,
                    trading_active: data.trading_active,
                    last_update: new Date().toISOString()
                  }));
                }
                break;
              case 'pong':
                // Keep-alive response
                break;
              case 'system_status_update':
                // Handle system status updates
                if (data.system_health || data.autonomous_trading !== undefined) {
                  setSystemStatus(prev => ({
                    ...prev,
                    system_health: data.system_health || prev.system_health,
                    autonomous_trading: data.autonomous_trading !== undefined ? data.autonomous_trading : prev.autonomous_trading,
                    trading_active: data.trading_active !== undefined ? data.trading_active : prev.trading_active,
                    last_update: new Date().toISOString()
                  }));
                }
                break;
              case 'autonomous_started':
                // Handle autonomous system start notification
                console.log('✅ Autonomous trading started:', data.message);
                setSystemStatus(prev => ({
                  ...prev,
                  autonomous_trading: true,
                  trading_active: true,
                  system_health: 'OPERATIONAL',
                  last_update: new Date().toISOString()
                }));
                break;
              default:
                console.log('Unknown autonomous data type:', data.type);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = (event) => {
          console.log('🔌 Autonomous Trading WebSocket disconnected:', event.code, event.reason);
          
          // Auto-reconnect logic
          if (reconnectAttempts < maxReconnectAttempts && isAuthenticated) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            
            reconnectTimeout = setTimeout(() => {
              reconnectAttempts++;
              connectWebSocket();
            }, delay);
          } else {
            console.error('❌ WebSocket max reconnection attempts reached');
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket connection error:', error);
        };

      } catch (error) {
        console.error('❌ WebSocket initialization failed:', error);
      }
    };

    // Initial connection
    connectWebSocket();

    // Cleanup function
    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [isAuthenticated, BACKEND_URL]);

  // Fetch system status and connected accounts
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchSystemData = async () => {
      try {
        const healthResponse = await fetch(`${BACKEND_URL}/api/health`);
        const healthData = await healthResponse.json();
        
        const systemResponse = await fetch(`${BACKEND_URL}/api/system/status`);
        const systemData = await systemResponse.json();
        
        // Fix: Extract data from nested response structure
        setBackendConnected(true);
        
        // Update system status with comprehensive data from both endpoints
        setSystemStatus({
          status: healthData.status,
          database: healthData.database || healthData.components?.database,
          timestamp: healthData.timestamp,
          // Enhanced system status from system endpoint (extract from data field)
          system_health: systemData.data?.system_health || healthData.status,
          autonomous_trading: systemData.data?.autonomous_trading || healthData.autonomous_trading,
          paper_trading: systemData.data?.paper_trading || healthData.paper_trading || true,
          market_status: systemData.data?.market_open ? 'OPEN' : 'CLOSED',
          current_time: healthData.timestamp,
          uptime: healthData.uptime,
          last_update: new Date().toISOString(),
          data_source: systemData.data?.data_source || 'NO_DATA',
          symbols_tracked: healthData.symbols_tracked,
          truedata: healthData.truedata || { status: 'DISCONNECTED', connected: false },
          truedata_connected: systemData.data?.truedata_connected || false,
          zerodha_connected: systemData.data?.zerodha_connected || false,
          websocket_connections: systemData.data?.websocket_connections || 0,
          trading_stats: healthData.trading_stats,
          // Add component status
          components: healthData.components || {}
        });
        
      } catch (error) {
        console.error('Error fetching system data:', error);
        setSystemStatus({ 
          status: 'error', 
          database: 'disconnected',
          system_health: 'UNHEALTHY',
          last_error: error.message,
          last_update: new Date().toISOString()
        });
      }
    };

    fetchSystemData();
    const interval = setInterval(fetchSystemData, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [isAuthenticated, BACKEND_URL]);

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
    setUserRole(userData.role || 'admin');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setUserRole(null);
    setSystemStatus({});
    setConnectedAccounts([]);
    setRealTimeData({});
  };

  // TrueData connection handlers
  const handleTrueDataConnect = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/truedata/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Connection failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log('✅ TrueData connected successfully');
        // Update system status immediately
        setSystemStatus(prev => ({
          ...prev,
          truedata_connected: true,
          truedata: { status: 'CONNECTED', connected: true }
        }));
      } else {
        console.error('❌ TrueData connection failed:', data.message);
      }
      
      return data;
    } catch (error) {
      console.error('❌ Error connecting TrueData:', error);
      return { success: false, error: error.message };
    }
  };

  const handleTrueDataDisconnect = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/truedata/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Disconnection failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log('✅ TrueData disconnected successfully');
        // Update system status immediately
        setSystemStatus(prev => ({
          ...prev,
          truedata_connected: false,
          truedata: { status: 'DISCONNECTED', connected: false }
        }));
      }
      
      return data;
    } catch (error) {
      console.error('❌ Error disconnecting TrueData:', error);
      return { success: false, error: error.message };
    }
  };

  if (!isAuthenticated) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Navigation 
          user={user} 
          userRole={userRole}
          systemStatus={systemStatus}
          connectedAccounts={connectedAccounts}
          onLogout={handleLogout}
          onTrueDataConnect={handleTrueDataConnect}
          onTrueDataDisconnect={handleTrueDataDisconnect}
        />
        {/* Live Indices Header - Shows real-time data across all pages */}
        <LiveIndicesHeader />
        <div className="main-content">
          <Routes>
            {/* Autonomous Trading Routes Only */}
            <Route 
              path="/" 
              element={<LiveAutonomousStatus />}
            />
            <Route 
              path="/live-status" 
              element={<LiveAutonomousStatus />}
            />
            <Route 
              path="/strategy-monitoring" 
              element={<StrategyMonitoring />} 
            />
            
            {/* Admin Routes */}
            <Route 
              path="/admin" 
              element={
                <AdminDashboard 
                  systemStatus={systemStatus}
                  connectedAccounts={connectedAccounts}
                  realTimeData={realTimeData}
                  onTrueDataConnect={handleTrueDataConnect}
                  onTrueDataDisconnect={handleTrueDataDisconnect}
                />
              } 
            />
            <Route 
              path="/accounts" 
              element={
                <AccountManagement 
                  connectedAccounts={connectedAccounts}
                  setConnectedAccounts={setConnectedAccounts}
                />
              } 
            />
            <Route 
              path="/autonomous-monitoring" 
              element={
                <AutonomousMonitoring 
                  systemStatus={systemStatus}
                  connectedAccounts={connectedAccounts}
                  realTimeData={realTimeData}
                />
              } 
            />
            <Route 
              path="/elite-recommendations" 
              element={
                <EliteRecommendations />
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <AnalyticsReports />
              } 
            />
            
            {/* Default redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;