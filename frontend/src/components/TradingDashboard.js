import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TradingDashboard = ({ marketData, positions, systemStatus }) => {
  const [recentTrades, setRecentTrades] = useState([]);
  const [manualOrder, setManualOrder] = useState({
    symbol: 'NIFTY',
    action: 'BUY',
    quantity: 25
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-IN').format(value || 0);
  };

  // Calculate portfolio metrics
  const totalPnL = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const totalValue = positions.reduce((sum, pos) => 
    sum + (pos.quantity * pos.current_price), 0
  );
  const activePositions = positions.filter(pos => pos.quantity !== 0).length;

  const handleManualOrder = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/manual-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: manualOrder.symbol,
          action: manualOrder.action,
          quantity: parseInt(manualOrder.quantity)
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Order placed successfully: ${result.order_id}`);
        
        // Reset form
        setManualOrder({
          symbol: 'NIFTY',
          action: 'BUY',
          quantity: 25
        });
      } else {
        const error = await response.json();
        alert(`Order failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Error placing order. Please try again.');
    }
  };

  const handleSquareOffAll = async () => {
    if (!window.confirm('Are you sure you want to square off all positions?')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/square-off-all`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('All positions squared off successfully');
      } else {
        const error = await response.json();
        alert(`Square off failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error squaring off positions:', error);
      alert('Error squaring off positions. Please try again.');
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Trading Dashboard</h1>
        <p className="dashboard-subtitle">
          Real-time portfolio monitoring and trade execution
        </p>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className={`metric-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(totalPnL)}
          </div>
          <div className="metric-label">Total P&L</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            {formatCurrency(totalValue)}
          </div>
          <div className="metric-label">Portfolio Value</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            {activePositions}
          </div>
          <div className="metric-label">Active Positions</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            {Object.keys(marketData).length}
          </div>
          <div className="metric-label">Symbols Tracked</div>
        </div>
      </div>

      {/* Real-time Market Data */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Live Market Data</h2>
          <span className="card-subtitle">Real-time F&O prices</span>
        </div>
        
        <div className="market-grid">
          {Object.entries(marketData).map(([symbol, data]) => (
            <div key={symbol} className="market-item">
              <div className="market-symbol">{symbol}</div>
              <div className="market-details">
                <div className="market-detail">
                  <div className="market-detail-label">LTP</div>
                  <div className="market-detail-value">₹{data.ltp?.toFixed(2)}</div>
                </div>
                <div className="market-detail">
                  <div className="market-detail-label">Volume</div>
                  <div className="market-detail-value">{formatNumber(data.volume)}</div>
                </div>
                <div className="market-detail">
                  <div className="market-detail-label">Bid</div>
                  <div className="market-detail-value">₹{data.bid?.toFixed(2)}</div>
                </div>
                <div className="market-detail">
                  <div className="market-detail-label">Ask</div>
                  <div className="market-detail-value">₹{data.ask?.toFixed(2)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {Object.keys(marketData).length === 0 && (
          <div className="text-center text-muted p-4">
            Waiting for market data feed...
          </div>
        )}
      </div>

      {/* Manual Trading */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Manual Trading</h2>
          <span className="card-subtitle">Place orders manually</span>
        </div>
        
        <form onSubmit={handleManualOrder} className="flex gap-3 items-end">
          <div className="form-group flex-1">
            <label className="form-label">Symbol</label>
            <select 
              value={manualOrder.symbol}
              onChange={(e) => setManualOrder({...manualOrder, symbol: e.target.value})}
              className="form-select"
            >
              <option value="NIFTY">NIFTY</option>
              <option value="BANKNIFTY">BANKNIFTY</option>
              <option value="FINNIFTY">FINNIFTY</option>
            </select>
          </div>
          
          <div className="form-group flex-1">
            <label className="form-label">Action</label>
            <select 
              value={manualOrder.action}
              onChange={(e) => setManualOrder({...manualOrder, action: e.target.value})}
              className="form-select"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          
          <div className="form-group flex-1">
            <label className="form-label">Quantity</label>
            <input
              type="number"
              value={manualOrder.quantity}
              onChange={(e) => setManualOrder({...manualOrder, quantity: e.target.value})}
              className="form-input"
              min="25"
              step="25"
            />
          </div>
          
          <button type="submit" className="btn btn-primary">
            Place Order
          </button>
        </form>
      </div>

      {/* Current Positions Summary */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Active Positions</h2>
          <div className="flex gap-2">
            <span className="card-subtitle">Current holdings</span>
            <button 
              onClick={handleSquareOffAll}
              className="btn btn-danger btn-sm"
            >
              Square Off All
            </button>
          </div>
        </div>
        
        {positions.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Avg Price</th>
                  <th>Current Price</th>
                  <th>P&L</th>
                  <th>% Change</th>
                </tr>
              </thead>
              <tbody>
                {positions.filter(pos => pos.quantity !== 0).map((position, index) => {
                  const pnlPercent = ((position.current_price - position.average_price) / position.average_price) * 100;
                  
                  return (
                    <tr key={index}>
                      <td className="font-weight-bold">{position.symbol}</td>
                      <td>{position.quantity}</td>
                      <td>₹{position.average_price?.toFixed(2)}</td>
                      <td>₹{position.current_price?.toFixed(2)}</td>
                      <td className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>
                        {formatCurrency(position.pnl)}
                      </td>
                      <td className={pnlPercent >= 0 ? 'text-success' : 'text-danger'}>
                        {pnlPercent.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-muted p-4">
            No active positions
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">System Status</h2>
          <span className="card-subtitle">Platform health monitoring</span>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="flex justify-between">
            <span>Autonomous Trading:</span>
            <span className={systemStatus.autonomous_trading ? 'text-success' : 'text-danger'}>
              {systemStatus.autonomous_trading ? 'ACTIVE' : 'INACTIVE'}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span>Paper Trading:</span>
            <span className={systemStatus.paper_trading ? 'text-info' : 'text-muted'}>
              {systemStatus.paper_trading ? 'ON' : 'OFF'}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span>Active Connections:</span>
            <span className="text-neutral">{systemStatus.active_connections || 0}</span>
          </div>
          
          <div className="flex justify-between">
            <span>Market Data Symbols:</span>
            <span className="text-neutral">{systemStatus.market_data_symbols || 0}</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-900 bg-opacity-20 border border-blue-800 rounded">
          <div className="text-sm text-info">
            <strong>Trading Hours:</strong> 9:15 AM - 3:30 PM IST<br/>
            <strong>Auto Square-off:</strong> 3:15 PM - 3:25 PM<br/>
            <strong>Daily Stop Loss:</strong> 2% of capital
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;
