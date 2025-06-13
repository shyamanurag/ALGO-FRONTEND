import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminDashboard from './components/AdminDashboard';
import UserDashboard from './components/UserDashboard';
import AccountManagement from './components/AccountManagement';
import AutonomousMonitoring from './components/AutonomousMonitoring';
import UserReports from './components/UserReports';
import EliteRecommendations from './components/EliteRecommendations';
import Navigation from './components/Navigation';
import AdminLogin from './components/AdminLogin';
import RealTradingDashboard from './components/RealTradingDashboard';
import LiveIndicesHeader from './components/LiveIndicesHeader';
import LiveAutonomousStatus from './components/LiveAutonomousStatus';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true); // Set to true for testing
  const [user, setUser] = useState({ name: 'Admin User', role: 'admin' }); // Default user for testing
  const [userRole, setUserRole] = useState('admin');
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [systemStatus, setSystemStatus] = useState({});
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
    
    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Autonomous Trading WebSocket connected');
      };

      ws.onmessage = (event) => {
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
          default:
            console.log('Unknown autonomous data type:', data.type);
        }
      };

      ws.onclose = () => {
        console.log('Autonomous Trading WebSocket disconnected');
      };

      ws.onerror = (error) => {
        console.warn('WebSocket connection failed:', error);
      };

      return () => {
        try {
          ws.close();
        } catch (e) {
          console.warn('Error closing WebSocket:', e);
        }
      };
    } catch (error) {
      console.warn('WebSocket initialization failed:', error);
    }
  }, [isAuthenticated, BACKEND_URL]);

  // Fetch system status and connected accounts
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchSystemData = async () => {
      try {
        // Try to fetch health status instead of potentially problematic endpoints
        const healthResponse = await fetch(`${BACKEND_URL}/api/health`);
        const healthData = await healthResponse.json();
        
        setSystemStatus({
          status: healthData.status,
          database: healthData.database,
          timestamp: healthData.timestamp,
          // Add the full system status
          system_health: healthData.system_health,
          autonomous_trading: healthData.autonomous_trading,
          paper_trading: healthData.paper_trading,
          market_status: healthData.market_status,
          current_time: healthData.current_time,
          uptime: healthData.uptime,
          last_update: healthData.last_update,
          data_source: healthData.data_source,
          symbols_tracked: healthData.symbols_tracked,
          truedata: healthData.truedata,
          trading_stats: healthData.trading_stats
        });
        
      } catch (error) {
        console.error('Error fetching system data:', error);
        setSystemStatus({ status: 'error', database: 'disconnected' });
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
    setSelectedUserId(null);
    setSystemStatus({});
    setConnectedAccounts([]);
    setRealTimeData({});
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
        />
        {/* Live Indices Header - Shows real-time data across all pages */}
        <LiveIndicesHeader />
        <div className="main-content">
          <Routes>
            {/* Real Trading Dashboard - Main Route */}
            <Route 
              path="/trading" 
              element={<RealTradingDashboard />} 
            />
            
            {/* Admin Routes */}
            <>
              <Route 
                path="/" 
                element={<LiveAutonomousStatus />}
              />
              <Route 
                path="/admin" 
                element={
                  <AdminDashboard 
                    systemStatus={systemStatus}
                    connectedAccounts={connectedAccounts}
                    realTimeData={realTimeData}
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
                path="/user/:userId" 
                element={
                  <UserDashboard 
                    connectedAccounts={connectedAccounts}
                    realTimeData={realTimeData}
                  />
                } 
              />
              <Route 
                path="/reports/:userId" 
                element={
                  <UserReports 
                    connectedAccounts={connectedAccounts}
                    realTimeData={realTimeData}
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
                path="/live-status" 
                element={<LiveAutonomousStatus />}
              />
            </>
            
            {/* Redirect to trading dashboard by default */}
            <Route path="*" element={<Navigate to="/trading" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;