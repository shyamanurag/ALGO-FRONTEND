import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RealTradingDashboard = () => {
  const [systemHealth, setSystemHealth] = useState(null);
  const [realSignals, setRealSignals] = useState([]);
  const [eliteRecommendations, setEliteRecommendations] = useState([]);
  const [liveMarketData, setLiveMarketData] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [signalingInProgress, setSignalingInProgress] = useState(false);

  useEffect(() => {
    fetchRealTradingData();
    const interval = setInterval(fetchRealTradingData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchRealTradingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch health status
      const healthResponse = await fetch(`${BACKEND_URL}/api/health`);
      const healthData = await healthResponse.json();
      setSystemHealth(healthData);

      // Fetch live market data (indices)
      try {
        const marketResponse = await fetch(`${BACKEND_URL}/api/market-data/live`);
        if (marketResponse.ok) {
          const marketDataResponse = await marketResponse.json();
          setLiveMarketData(marketDataResponse.indices || {});
        }
      } catch (e) {
        console.log('Market data endpoint error:', e);
      }

      // Fetch real trading signals
      try {
        const signalsResponse = await fetch(`${BACKEND_URL}/api/trading-signals/active`);
        if (signalsResponse.ok) {
          const signalsData = await signalsResponse.json();
          setRealSignals(signalsData.signals || []);
        }
      } catch (e) {
        console.log('Trading signals endpoint error:', e);
      }

      // Fetch elite recommendations
      try {
        const eliteResponse = await fetch(`${BACKEND_URL}/api/elite-recommendations`);
        if (eliteResponse.ok) {
          const eliteData = await eliteResponse.json();
          setEliteRecommendations(eliteData.recommendations || []);
        }
      } catch (e) {
        console.log('Elite recommendations endpoint error:', e);
      }

      // Fetch recent orders
      try {
        const ordersResponse = await fetch(`${BACKEND_URL}/api/trading/orders`);
        if (ordersResponse.ok) {
          const ordersData = await ordersResponse.json();
          setRecentOrders(ordersData.orders || []);
        }
      } catch (e) {
        console.log('Orders endpoint error:', e);
      }

    } catch (err) {
      setError('Failed to fetch trading data: ' + err.message);
      console.error('Error fetching trading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateSignals = async () => {
    try {
      setSignalingInProgress(true);
      const response = await fetch(`${BACKEND_URL}/api/trading/force-generate-signals`, {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success) {
        await fetchRealTradingData(); // Refresh data to show new signals
      }
    } catch (err) {
      setError('Failed to generate signals: ' + err.message);
    } finally {
      setSignalingInProgress(false);
    }
  };

  if (loading && !systemHealth) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading Elite Trading Platform...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">🚀 Elite Autonomous Trading Platform</h1>
        <p className="dashboard-subtitle">Live Trading System with Automated Signal Generation & Execution</p>
      </div>

      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Live Market Data Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📈 Live Market Indices</h2>
          <span className="text-info">Real-time TrueData Feed</span>
        </div>
        {Object.keys(liveMarketData).length > 0 ? (
          <div className="market-grid">
            {Object.entries(liveMarketData).map(([symbol, data]) => (
              <div key={symbol} className="market-item">
                <div className="market-symbol">{data.symbol}</div>
                <div className="market-details">
                  <div className="market-detail">
                    <div className="market-detail-label">LTP</div>
                    <div className="market-detail-value">₹{data.ltp?.toLocaleString()}</div>
                  </div>
                  <div className="market-detail">
                    <div className="market-detail-label">Change</div>
                    <div className={`market-detail-value ${data.change >= 0 ? 'text-success' : 'text-danger'}`}>
                      {data.change >= 0 ? '+' : ''}₹{data.change?.toFixed(2)}
                    </div>
                  </div>
                  <div className="market-detail">
                    <div className="market-detail-label">Volume</div>
                    <div className="market-detail-value">{(data.volume / 1000000).toFixed(1)}M</div>
                  </div>
                  <div className="market-detail">
                    <div className="market-detail-label">Status</div>
                    <div className={`market-detail-value ${data.market_status === 'OPEN' ? 'text-success' : 'text-warning'}`}>
                      {data.market_status}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">📡 Connecting to live market data feeds...</p>
          </div>
        )}
      </div>

      {/* Autonomous Trading Flow Explanation */}
      <div className="card border-info">
        <div className="card-header">
          <h2 className="card-title text-info">🤖 Autonomous Trading Flow</h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-lg font-semibold mb-3">📊 Intraday Trading (Auto-Executed)</h3>
              <div className="flow-steps">
                <div className="step">1. TrueData → Live market data feed</div>
                <div className="step">2. Algorithm Engine → Analyzes all parameters</div>
                <div className="step">3. Signal Generation → Creates intraday signals</div>
                <div className="step">4. Multi-Account Execution → Zerodha API across all users</div>
                <div className="step">5. Auto Square-off → Before 3:15 PM</div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">💎 Elite Recommendations (Dashboard Only)</h3>
              <div className="flow-steps">
                <div className="step">1. Deep Analysis → Long-term market structure</div>
                <div className="step">2. Elite Signals → 5-10 day validity</div>
                <div className="step">3. Dashboard Display → No auto-execution</div>
                <div className="step">4. Manual Review → User decides execution</div>
                <div className="step">5. Quality Score → 9.5+ confidence only</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Signal Generation Controls */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">⚡ Autonomous Signal Generation</h2>
          <button 
            className={`btn ${signalingInProgress ? 'btn-warning' : 'btn-success'} btn-sm`} 
            onClick={generateSignals}
            disabled={signalingInProgress}
          >
            {signalingInProgress ? '🔄 Generating...' : '🎯 Run Algorithm Engine'}
          </button>
        </div>
        <div className="p-4">
          <div className="alert alert-info">
            <strong>Autonomous Trading Active:</strong> The system uses TrueData live feeds and runs 7 elite algorithms. 
            Intraday signals are auto-executed across multiple Zerodha accounts. Elite recommendations (5-10 days) are displayed here for manual review.
          </div>
        </div>
      </div>

      {/* Real Trading Signals Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">⚡ Intraday Signals ({realSignals.length})</h2>
          <span className="text-success">Auto-Executed via Zerodha Multi-Account</span>
        </div>
        {realSignals.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Symbol</th>
                  <th>Action</th>
                  <th>Quality Score</th>
                  <th>Entry Price</th>
                  <th>Stop Loss %</th>
                  <th>Target %</th>
                  <th>Status</th>
                  <th>Generated</th>
                </tr>
              </thead>
              <tbody>
                {realSignals.map((signal, index) => (
                  <tr key={index}>
                    <td>
                      <span className="strategy-badge">{signal.strategy_name}</span>
                    </td>
                    <td className="text-info font-weight-bold">{signal.symbol}</td>
                    <td className={signal.action === 'BUY' ? 'text-success' : 'text-danger'}>
                      <strong>{signal.action}</strong>
                    </td>
                    <td>
                      <span className={signal.quality_score >= 8 ? 'text-success' : signal.quality_score >= 6 ? 'text-warning' : 'text-danger'}>
                        <strong>{signal.quality_score}/10</strong>
                      </span>
                    </td>
                    <td>₹{signal.entry_price?.toLocaleString()}</td>
                    <td className="text-danger">{signal.stop_loss_percent}%</td>
                    <td className="text-success">{signal.target_percent}%</td>
                    <td>
                      <span className={`strategy-status ${signal.status === 'GENERATED' ? 'active' : 'inactive'}`}>
                        {signal.status}
                      </span>
                    </td>
                    <td>{new Date(signal.generated_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">🔍 No active signals. Click "Generate Trading Signals" to see the autonomous system in action.</p>
          </div>
        )}
      </div>

      {/* Recent Orders Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📋 Recent Paper Trades ({recentOrders.length})</h2>
          <span className="text-info">Automated Execution</span>
        </div>
        {recentOrders.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th>Strategy</th>
                  <th>Executed</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((order, index) => (
                  <tr key={index}>
                    <td className="text-info font-weight-bold">{order.symbol}</td>
                    <td className={order.side === 'BUY' ? 'text-success' : 'text-danger'}>
                      <strong>{order.side}</strong>
                    </td>
                    <td>{order.filled_quantity}</td>
                    <td>₹{order.average_price?.toFixed(2)}</td>
                    <td>
                      <span className={`strategy-status ${order.status === 'FILLED' ? 'active' : 'inactive'}`}>
                        {order.status}
                      </span>
                    </td>
                    <td>
                      <span className="strategy-badge">{order.strategy_name}</span>
                    </td>
                    <td>{new Date(order.filled_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">📝 No recent orders. Generate signals to see paper trade executions.</p>
          </div>
        )}
      </div>

      {/* System Health Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">🏥 System Health</h2>
          <button className="btn btn-secondary btn-sm" onClick={fetchRealTradingData}>
            Refresh
          </button>
        </div>
        {systemHealth ? (
          <div className="metrics-grid">
            <div className="metric-card">
              <div className={`metric-value ${systemHealth.database === 'connected' ? 'positive' : 'negative'}`}>
                {systemHealth.database === 'connected' ? '✅' : '❌'}
              </div>
              <div className="metric-label">Database</div>
            </div>
            <div className="metric-card">
              <div className="metric-value positive">{systemHealth.tables_count || 0}</div>
              <div className="metric-label">Trading Tables</div>
            </div>
            <div className="metric-card">
              <div className="metric-value neutral">{realSignals.length}</div>
              <div className="metric-label">Active Signals</div>
            </div>
            <div className="metric-card">
              <div className="metric-value neutral">{recentOrders.length}</div>
              <div className="metric-label">Recent Trades</div>
            </div>
          </div>
        ) : (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}
      </div>

      {/* Risk Disclaimer */}
      <div className="card border-warning">
        <div className="card-header">
          <h2 className="card-title text-warning">⚠️ Trading Mode: PAPER TRADING</h2>
        </div>
        <div className="p-4">
          <div className="alert alert-success">
            <strong>PAPER TRADING ACTIVE:</strong> All signals and executions are simulated. No real money is at risk. 
            This is a safe environment to test and validate the autonomous trading system before going live.
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTradingDashboard;