import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Positions = ({ positions, marketData }) => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(false);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour12: true
    });
  };

  // Calculate portfolio metrics
  const totalInvestment = positions.reduce((sum, pos) => 
    sum + (Math.abs(pos.quantity) * pos.average_price), 0
  );
  
  const currentValue = positions.reduce((sum, pos) => 
    sum + (Math.abs(pos.quantity) * pos.current_price), 0
  );
  
  const totalPnL = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const totalPnLPercent = totalInvestment > 0 ? (totalPnL / totalInvestment) * 100 : 0;

  const longPositions = positions.filter(pos => pos.quantity > 0);
  const shortPositions = positions.filter(pos => pos.quantity < 0);

  const handleSquareOffPosition = async (symbol) => {
    if (!window.confirm(`Are you sure you want to square off ${symbol}?`)) {
      return;
    }

    try {
      setLoading(true);
      const position = positions.find(p => p.symbol === symbol);
      
      const response = await fetch(`${BACKEND_URL}/api/manual-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: symbol,
          action: position.quantity > 0 ? 'SELL' : 'BUY',
          quantity: Math.abs(position.quantity)
        })
      });

      if (response.ok) {
        alert(`Position ${symbol} squared off successfully`);
      } else {
        const error = await response.json();
        alert(`Square off failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error squaring off position:', error);
      alert('Error squaring off position. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSquareOffAll = async () => {
    if (!window.confirm('Are you sure you want to square off ALL positions?')) {
      return;
    }

    try {
      setLoading(true);
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
      console.error('Error squaring off all positions:', error);
      alert('Error squaring off all positions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="positions-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Portfolio Positions</h1>
        <p className="dashboard-subtitle">
          Detailed view of all current positions and trading history
        </p>
      </div>

      {/* Portfolio Summary */}
      <div className="metrics-grid mb-5">
        <div className="metric-card">
          <div className="metric-value neutral">
            {formatCurrency(totalInvestment)}
          </div>
          <div className="metric-label">Total Investment</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            {formatCurrency(currentValue)}
          </div>
          <div className="metric-label">Current Value</div>
        </div>
        
        <div className="metric-card">
          <div className={`metric-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(totalPnL)}
          </div>
          <div className="metric-label">Total P&L</div>
        </div>
        
        <div className="metric-card">
          <div className={`metric-value ${totalPnLPercent >= 0 ? 'positive' : 'negative'}`}>
            {totalPnLPercent.toFixed(2)}%
          </div>
          <div className="metric-label">P&L Percentage</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-4">
        <button 
          onClick={handleSquareOffAll}
          className="btn btn-danger"
          disabled={loading || positions.filter(p => p.quantity !== 0).length === 0}
        >
          {loading ? 'Processing...' : 'Square Off All Positions'}
        </button>
      </div>

      {/* All Positions */}
      <div className="card mb-5">
        <div className="card-header">
          <h2 className="card-title">All Positions</h2>
          <span className="card-subtitle">
            {positions.filter(p => p.quantity !== 0).length} active positions
          </span>
        </div>
        
        {positions.filter(p => p.quantity !== 0).length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Avg Price</th>
                  <th>Current Price</th>
                  <th>Investment</th>
                  <th>Current Value</th>
                  <th>P&L</th>
                  <th>% Change</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {positions.filter(p => p.quantity !== 0).map((position, index) => {
                  const investment = Math.abs(position.quantity) * position.average_price;
                  const currentVal = Math.abs(position.quantity) * position.current_price;
                  const pnlPercent = ((position.current_price - position.average_price) / position.average_price) * 100;
                  const positionType = position.quantity > 0 ? 'LONG' : 'SHORT';
                  
                  return (
                    <tr key={index}>
                      <td className="font-weight-bold">{position.symbol}</td>
                      <td>
                        <span className={`badge ${positionType === 'LONG' ? 'badge-success' : 'badge-danger'}`}>
                          {positionType}
                        </span>
                      </td>
                      <td>{Math.abs(position.quantity)}</td>
                      <td>₹{position.average_price?.toFixed(2)}</td>
                      <td>₹{position.current_price?.toFixed(2)}</td>
                      <td>{formatCurrency(investment)}</td>
                      <td>{formatCurrency(currentVal)}</td>
                      <td className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>
                        {formatCurrency(position.pnl)}
                      </td>
                      <td className={pnlPercent >= 0 ? 'text-success' : 'text-danger'}>
                        {pnlPercent.toFixed(2)}%
                      </td>
                      <td>
                        <button
                          onClick={() => handleSquareOffPosition(position.symbol)}
                          className="btn btn-danger btn-sm"
                          disabled={loading}
                        >
                          Square Off
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-muted p-5">
            <div className="mb-3">📊</div>
            <h3>No Active Positions</h3>
            <p>Start trading to see your positions here</p>
          </div>
        )}
      </div>

      {/* Long vs Short Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Long Positions */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title text-success">Long Positions</h3>
            <span className="card-subtitle">{longPositions.length} positions</span>
          </div>
          
          {longPositions.length > 0 ? (
            <div className="space-y-3">
              {longPositions.map((position, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-green-900 bg-opacity-20 rounded border border-green-800">
                  <div>
                    <div className="font-semibold">{position.symbol}</div>
                    <div className="text-sm text-muted">
                      {position.quantity} @ ₹{position.average_price?.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>
                      {formatCurrency(position.pnl)}
                    </div>
                    <div className="text-sm text-muted">
                      ₹{position.current_price?.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted p-4">
              No long positions
            </div>
          )}
        </div>

        {/* Short Positions */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title text-danger">Short Positions</h3>
            <span className="card-subtitle">{shortPositions.length} positions</span>
          </div>
          
          {shortPositions.length > 0 ? (
            <div className="space-y-3">
              {shortPositions.map((position, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-red-900 bg-opacity-20 rounded border border-red-800">
                  <div>
                    <div className="font-semibold">{position.symbol}</div>
                    <div className="text-sm text-muted">
                      {Math.abs(position.quantity)} @ ₹{position.average_price?.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>
                      {formatCurrency(position.pnl)}
                    </div>
                    <div className="text-sm text-muted">
                      ₹{position.current_price?.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted p-4">
              No short positions
            </div>
          )}
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">Risk Metrics</h3>
          <span className="card-subtitle">Portfolio risk analysis</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {((Math.abs(totalPnL) / totalInvestment) * 100).toFixed(2)}%
            </div>
            <div className="text-sm text-muted">Risk Exposure</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {positions.filter(p => p.quantity !== 0).length}
            </div>
            <div className="text-sm text-muted">Active Symbols</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {longPositions.length}
            </div>
            <div className="text-sm text-muted">Long Positions</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {shortPositions.length}
            </div>
            <div className="text-sm text-muted">Short Positions</div>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-yellow-900 bg-opacity-20 border border-yellow-800 rounded">
          <div className="text-sm text-warning">
            <strong>Risk Management:</strong><br/>
            • Daily stop loss: 2% of capital<br/>
            • Auto square-off: 3:15 PM - 3:25 PM<br/>
            • Maximum position size per trade: Based on volatility<br/>
            • All trades are intraday (MIS product)
          </div>
        </div>
      </div>
    </div>
  );
};

export default Positions;
