import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RealTradingDashboard = () => {
  const [systemHealth, setSystemHealth] = useState(null);
  const [realSignals, setRealSignals] = useState([]);
  const [eliteRecommendations, setEliteRecommendations] = useState([]);
  const [liveMarketData, setLiveMarketData] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [strategyMetrics, setStrategyMetrics] = useState([]);
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
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setSystemHealth(healthData);
      }

      // Fetch live market data (indices)
      try {
        const marketResponse = await fetch(`${BACKEND_URL}/api/market-data/live`);
        if (marketResponse.ok) {
          const marketDataResponse = await marketResponse.json();
          setLiveMarketData(marketDataResponse.indices || {});
        }
      } catch (e) {
        console.log('Market data endpoint not available');
      }

      // Fetch real trading signals
      try {
        const signalsResponse = await fetch(`${BACKEND_URL}/api/trading-signals/active`);
        if (signalsResponse.ok) {
          const signalsData = await signalsResponse.json();
          setRealSignals(signalsData.signals || []);
        }
      } catch (e) {
        console.log('Trading signals endpoint not available');
      }

      // Fetch elite recommendations
      try {
        const eliteResponse = await fetch(`${BACKEND_URL}/api/elite-recommendations`);
        if (eliteResponse.ok) {
          const eliteData = await eliteResponse.json();
          setEliteRecommendations(eliteData.recommendations || []);
        }
      } catch (e) {
        console.log('Elite recommendations endpoint not available');
      }

      // Fetch recent orders
      try {
        const ordersResponse = await fetch(`${BACKEND_URL}/api/trading/orders`);
        if (ordersResponse.ok) {
          const ordersData = await ordersResponse.json();
          setRecentOrders(ordersData.orders || []);
        }
      } catch (e) {
        console.log('Orders endpoint not available');
      }

      // Fetch positions
      try {
        const positionsResponse = await fetch(`${BACKEND_URL}/api/positions`);
        if (positionsResponse.ok) {
          const positionsData = await positionsResponse.json();
          setPositions(positionsData.positions || []);
        }
      } catch (e) {
        console.log('Positions endpoint not available');
      }

      // Fetch strategy metrics
      try {
        const metricsResponse = await fetch(`${BACKEND_URL}/api/strategies/metrics`);
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setStrategyMetrics(metricsData.strategies || []);
        }
      } catch (e) {
        console.log('Strategy metrics endpoint not available');
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

  const squareOffAllPositions = async () => {
    if (!window.confirm('Are you sure you want to square off ALL positions? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/trading/square-off-all`, {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success) {
        await fetchRealTradingData(); // Refresh data
        alert('All positions squared off successfully');
      } else {
        setError(data.error || 'Failed to square off positions');
      }
    } catch (err) {
      setError('Failed to square off positions: ' + err.message);
    }
  };

  // Calculate portfolio metrics
  const totalInvestment = positions.reduce((sum, pos) => 
    sum + (Math.abs(pos.quantity) * pos.average_entry_price), 0
  );
  
  const totalPnL = positions.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
  const totalPnLPercent = totalInvestment > 0 ? (totalPnL / totalInvestment) * 100 : 0;

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
        <p className="dashboard-subtitle">Real-time Trading System with Live Data Integration</p>
      </div>

      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
          <button 
            onClick={() => setError(null)} 
            className="ml-4 text-sm underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Portfolio Overview */}
      <div className="metrics-grid mb-5">
        <div className="metric-card">
          <div className="metric-value neutral">
            ₹{totalInvestment.toLocaleString()}
          </div>
          <div className="metric-label">Total Investment</div>
        </div>
        
        <div className="metric-card">
          <div className={`metric-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
            ₹{totalPnL.toLocaleString()}
          </div>
          <div className="metric-label">Unrealized P&L</div>
        </div>
        
        <div className="metric-card">
          <div className={`metric-value ${totalPnLPercent >= 0 ? 'positive' : 'negative'}`}>
            {totalPnLPercent.toFixed(2)}%
          </div>
          <div className="metric-label">P&L Percentage</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">{positions.filter(p => p.quantity !== 0).length}</div>
          <div className="metric-label">Active Positions</div>
        </div>
      </div>

      {/* Live Market Data Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📈 Live Market Indices</h2>
          <span className="text-info">Real-time Data Feed</span>
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
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">📡 Market data will appear when data feed is connected</p>
          </div>
        )}
      </div>

      {/* Trading Controls */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">⚡ Trading Controls</h2>
          <div className="flex gap-3">
            <button 
              className={`btn ${signalingInProgress ? 'btn-warning' : 'btn-success'} btn-sm`} 
              onClick={generateSignals}
              disabled={signalingInProgress}
            >
              {signalingInProgress ? '🔄 Generating...' : '🎯 Generate Signals'}
            </button>
            <button 
              className="btn btn-danger btn-sm" 
              onClick={squareOffAllPositions}
              disabled={positions.filter(p => p.quantity !== 0).length === 0}
            >
              🔴 Square Off All
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className="alert alert-info">
            <strong>Live Trading System:</strong> This system integrates with real market data and broker APIs. 
            All signals are generated by sophisticated algorithms and executed with proper risk management.
          </div>
        </div>
      </div>

      {/* Strategy Performance */}
      {strategyMetrics.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📊 Strategy Performance</h2>
            <span className="text-success">Real-time Metrics</span>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Status</th>
                  <th>Signals Today</th>
                  <th>Win Rate</th>
                  <th>P&L Today</th>
                  <th>Avg Quality</th>
                  <th>Last Signal</th>
                </tr>
              </thead>
              <tbody>
                {strategyMetrics.map((strategy, index) => (
                  <tr key={index}>
                    <td>
                      <span className="strategy-badge">{strategy.name}</span>
                    </td>
                    <td>
                      <span className={`strategy-status ${strategy.active ? 'active' : 'inactive'}`}>
                        {strategy.active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </td>
                    <td>{strategy.signals_today || 0}</td>
                    <td className={strategy.win_rate >= 70 ? 'text-success' : strategy.win_rate >= 50 ? 'text-warning' : 'text-danger'}>
                      {strategy.win_rate?.toFixed(1)}%
                    </td>
                    <td className={strategy.pnl_today >= 0 ? 'text-success' : 'text-danger'}>
                      ₹{strategy.pnl_today?.toLocaleString()}
                    </td>
                    <td>{strategy.avg_quality?.toFixed(1)}/10</td>
                    <td>{strategy.last_signal ? new Date(strategy.last_signal).toLocaleTimeString() : 'No signals'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Active Trading Signals */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">⚡ Active Signals ({realSignals.length})</h2>
          <span className="text-success">Real-time Generation</span>
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
            <p className="text-muted">🔍 No active signals. Click "Generate Signals" to run the strategy engine.</p>
          </div>
        )}
      </div>

      {/* Elite Recommendations */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">💎 Elite Recommendations ({eliteRecommendations.length})</h2>
          <span className="text-info">10/10 Quality Signals</span>
        </div>
        {eliteRecommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {eliteRecommendations.map((rec, index) => (
              <div key={index} className="border border-gold rounded-lg p-4 bg-yellow-50">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-lg">{rec.symbol}</h4>
                  <span className="text-xs bg-yellow-600 text-white px-2 py-1 rounded">
                    ELITE {rec.confidence_score}/10
                  </span>
                </div>
                <div className="text-sm space-y-1">
                  <div><strong>Direction:</strong> {rec.direction}</div>
                  <div><strong>Entry:</strong> ₹{rec.entry_price}</div>
                  <div><strong>Stop Loss:</strong> ₹{rec.stop_loss}</div>
                  <div><strong>Target:</strong> ₹{rec.primary_target}</div>
                  <div><strong>Strategy:</strong> {rec.strategy}</div>
                  <div><strong>Timeframe:</strong> {rec.timeframe}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">💎 Elite recommendations will appear here when high-quality signals are detected.</p>
          </div>
        )}
      </div>

      {/* Current Positions */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📊 Current Positions ({positions.filter(p => p.quantity !== 0).length})</h2>
          <span className="text-info">Live P&L Tracking</span>
        </div>
        {positions.filter(p => p.quantity !== 0).length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Avg Price</th>
                  <th>Current Price</th>
                  <th>Investment</th>
                  <th>Current Value</th>
                  <th>P&L</th>
                  <th>% Change</th>
                  <th>Strategy</th>
                </tr>
              </thead>
              <tbody>
                {positions.filter(p => p.quantity !== 0).map((position, index) => {
                  const investment = Math.abs(position.quantity) * position.average_entry_price;
                  const currentVal = Math.abs(position.quantity) * position.current_price;
                  const pnlPercent = position.average_entry_price > 0 
                    ? ((position.current_price - position.average_entry_price) / position.average_entry_price) * 100 
                    : 0;
                  
                  return (
                    <tr key={index}>
                      <td className="font-weight-bold">{position.symbol}</td>
                      <td className={position.quantity > 0 ? 'text-success' : 'text-danger'}>
                        {position.quantity}
                      </td>
                      <td>₹{position.average_entry_price?.toFixed(2)}</td>
                      <td>₹{position.current_price?.toFixed(2)}</td>
                      <td>₹{investment.toLocaleString()}</td>
                      <td>₹{currentVal.toLocaleString()}</td>
                      <td className={position.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}>
                        ₹{position.unrealized_pnl?.toFixed(2)}
                      </td>
                      <td className={pnlPercent >= 0 ? 'text-success' : 'text-danger'}>
                        {pnlPercent.toFixed(2)}%
                      </td>
                      <td>
                        <span className="strategy-badge">{position.strategy_name || 'Manual'}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">📊 No active positions. Start trading to see your positions here.</p>
          </div>
        )}
      </div>

      {/* Recent Orders */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📋 Recent Orders ({recentOrders.length})</h2>
          <span className="text-info">Order Execution History</span>
        </div>
        {recentOrders.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Quantity</th>
                  <th>Type</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th>Strategy</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.slice(0, 10).map((order, index) => (
                  <tr key={index}>
                    <td className="text-info font-weight-bold">{order.symbol}</td>
                    <td className={order.side === 'BUY' ? 'text-success' : 'text-danger'}>
                      <strong>{order.side}</strong>
                    </td>
                    <td>{order.quantity}</td>
                    <td>{order.order_type}</td>
                    <td>₹{order.price?.toFixed(2) || 'Market'}</td>
                    <td>
                      <span className={`strategy-status ${order.status === 'FILLED' ? 'active' : 'inactive'}`}>
                        {order.status}
                      </span>
                    </td>
                    <td>
                      <span className="strategy-badge">{order.strategy_name || 'Manual'}</span>
                    </td>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-muted">📝 No recent orders. Order history will appear here after trading activity.</p>
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
              <div className="metric-value positive">{systemHealth.tables_created ? '✅' : '❌'}</div>
              <div className="metric-label">Trading Schema</div>
            </div>
            <div className="metric-card">
              <div className="metric-value neutral">{realSignals.length}</div>
              <div className="metric-label">Active Signals</div>
            </div>
            <div className="metric-card">
              <div className="metric-value neutral">{recentOrders.length}</div>
              <div className="metric-label">Recent Orders</div>
            </div>
            <div className="metric-card">
              <div className={`metric-value ${systemHealth.truedata?.connected ? 'positive' : 'negative'}`}>
                {systemHealth.truedata?.connected ? '🟢' : '🔴'}
              </div>
              <div className="metric-label">Market Data</div>
            </div>
            <div className="metric-card">
              <div className="metric-value neutral">{Object.keys(liveMarketData).length}</div>
              <div className="metric-label">Live Indices</div>
            </div>
          </div>
        ) : (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}
      </div>

      {/* Trading Mode Status */}
      <div className="card border-warning">
        <div className="card-header">
          <h2 className="card-title text-warning">⚠️ Trading Mode Status</h2>
        </div>
        <div className="p-4">
          <div className={`alert ${systemHealth?.paper_trading ? 'alert-success' : 'alert-danger'}`}>
            <strong>
              {systemHealth?.paper_trading ? 'PAPER TRADING ACTIVE' : 'LIVE TRADING ACTIVE'}:
            </strong> 
            {systemHealth?.paper_trading 
              ? ' All orders are simulated. No real money at risk.' 
              : ' Real money trading with live broker integration.'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTradingDashboard;