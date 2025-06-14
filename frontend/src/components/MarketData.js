import React, { useState, useEffect } from 'react';

const MarketData = ({ marketData }) => {
  const [historicalData, setHistoricalData] = useState({});
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');
  const [priceHistory, setPriceHistory] = useState({});

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  const formatNumber = (value) => {
    if (value >= 10000000) {
      return `${(value / 10000000).toFixed(1)}Cr`;
    } else if (value >= 100000) {
      return `${(value / 100000).toFixed(1)}L`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value?.toLocaleString('en-IN') || '0';
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Store price history for trending
  useEffect(() => {
    Object.entries(marketData).forEach(([symbol, data]) => {
      setPriceHistory(prev => {
        const history = prev[symbol] || [];
        const newHistory = [...history, {
          price: data.ltp,
          timestamp: data.timestamp || new Date().toISOString()
        }].slice(-50); // Keep last 50 data points
        
        return {
          ...prev,
          [symbol]: newHistory
        };
      });
    });
  }, [marketData]);

  const calculatePriceChange = (symbol) => {
    const history = priceHistory[symbol];
    if (!history || history.length < 2) return { change: 0, changePercent: 0 };
    
    const current = history[history.length - 1].price;
    const previous = history[history.length - 2].price;
    const change = current - previous;
    const changePercent = (change / previous) * 100;
    
    return { change, changePercent };
  };

  const getMarketStatus = () => {
    const now = new Date();
    const timeInIST = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Kolkata"}));
    const currentHour = timeInIST.getHours();
    const currentMinute = timeInIST.getMinutes();
    const currentTime = currentHour * 100 + currentMinute;
    
    if (currentTime >= 915 && currentTime <= 1530) {
      return { status: 'OPEN', color: 'text-success' };
    } else if (currentTime > 1530 && currentTime <= 1600) {
      return { status: 'CLOSING', color: 'text-warning' };
    } else {
      return { status: 'CLOSED', color: 'text-danger' };
    }
  };

  const marketStatus = getMarketStatus();

  const getOrderBookDepth = (symbol) => {
    // No simulated order book - return empty
    return { bids: [], asks: [] };
  };

  return (
    <div className="market-data-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Market Data</h1>
        <p className="dashboard-subtitle">
          Real-time F&O market data and analytics
        </p>
      </div>

      {/* Market Status */}
      <div className="card mb-5">
        <div className="card-header">
          <h2 className="card-title">Market Status</h2>
          <span className={`card-subtitle ${marketStatus.color}`}>
            {marketStatus.status}
          </span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {formatTime(new Date().toISOString())}
            </div>
            <div className="text-sm text-muted">Current Time (IST)</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              09:15 AM
            </div>
            <div className="text-sm text-muted">Market Open</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              03:30 PM
            </div>
            <div className="text-sm text-muted">Market Close</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral">
              {Object.keys(marketData).length}
            </div>
            <div className="text-sm text-muted">Symbols Tracked</div>
          </div>
        </div>
      </div>

      {/* Live Market Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
        {Object.entries(marketData).map(([symbol, data]) => {
          const priceChange = calculatePriceChange(symbol);
          
          return (
            <div key={symbol} className="card">
              <div className="card-header">
                <h3 className="card-title">{symbol}</h3>
                <span className={`card-subtitle ${priceChange.changePercent >= 0 ? 'text-success' : 'text-danger'}`}>
                  {priceChange.changePercent >= 0 ? '↗' : '↘'} {priceChange.changePercent.toFixed(2)}%
                </span>
              </div>
              
              <div className="space-y-3">
                {/* Current Price */}
                <div className="text-center">
                  <div className="text-3xl font-bold text-neutral">
                    ₹{data.ltp?.toFixed(2)}
                  </div>
                  <div className={`text-sm ${priceChange.change >= 0 ? 'text-success' : 'text-danger'}`}>
                    {priceChange.change >= 0 ? '+' : ''}{priceChange.change.toFixed(2)}
                  </div>
                </div>
                
                {/* Bid/Ask */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 bg-red-900 bg-opacity-20 rounded border border-red-800">
                    <div className="text-sm text-muted">BID</div>
                    <div className="font-semibold text-danger">₹{data.bid?.toFixed(2)}</div>
                  </div>
                  <div className="text-center p-2 bg-green-900 bg-opacity-20 rounded border border-green-800">
                    <div className="text-sm text-muted">ASK</div>
                    <div className="font-semibold text-success">₹{data.ask?.toFixed(2)}</div>
                  </div>
                </div>
                
                {/* Volume & OI */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-muted">Volume</div>
                    <div className="font-semibold">{formatNumber(data.volume)}</div>
                  </div>
                  <div>
                    <div className="text-muted">Open Interest</div>
                    <div className="font-semibold">{formatNumber(data.oi)}</div>
                  </div>
                </div>
                
                {/* Last Update */}
                <div className="text-center text-xs text-muted">
                  Last Updated: {formatTime(data.timestamp || new Date().toISOString())}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Symbol Selector for Detailed View */}
      <div className="card mb-5">
        <div className="card-header">
          <h3 className="card-title">Detailed Market Data</h3>
          <select 
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="form-select w-auto"
          >
            {Object.keys(marketData).map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
        </div>
        
        {marketData[selectedSymbol] && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Order Book */}
            <div>
              <h4 className="text-lg font-semibold mb-3">Order Book</h4>
              
              <div className="grid grid-cols-2 gap-4">
                {/* Bids */}
                <div>
                  <div className="text-center mb-2 text-danger font-semibold">BIDS</div>
                  <div className="space-y-1">
                    {getOrderBookDepth(selectedSymbol).bids.map((bid, index) => (
                      <div key={index} className="flex justify-between text-sm p-2 bg-red-900 bg-opacity-10 rounded">
                        <span>₹{bid.price.toFixed(2)}</span>
                        <span>{bid.quantity}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Asks */}
                <div>
                  <div className="text-center mb-2 text-success font-semibold">ASKS</div>
                  <div className="space-y-1">
                    {getOrderBookDepth(selectedSymbol).asks.map((ask, index) => (
                      <div key={index} className="flex justify-between text-sm p-2 bg-green-900 bg-opacity-10 rounded">
                        <span>₹{ask.price.toFixed(2)}</span>
                        <span>{ask.quantity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Price Movement */}
            <div>
              <h4 className="text-lg font-semibold mb-3">Price Movement</h4>
              
              <div className="space-y-4">
                {/* Price History Chart (Simple) */}
                <div className="h-32 bg-gray-800 rounded p-3 flex items-end justify-between">
                  {priceHistory[selectedSymbol]?.slice(-10).map((point, index) => {
                    const height = 80; // Simple fixed height for demo
                    return (
                      <div
                        key={index}
                        className="bg-blue-500 w-6 rounded-t"
                        style={{ height: `${height}%` }}
                        title={`₹${point.price.toFixed(2)}`}
                      />
                    );
                  })}
                </div>
                
                {/* Statistics */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-gray-800 rounded">
                    <div className="text-muted">Day High</div>
                    <div className="font-semibold text-success">
                      {marketData[selectedSymbol].high ? `₹${marketData[selectedSymbol].high.toFixed(2)}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-800 rounded">
                    <div className="text-muted">Day Low</div>
                    <div className="font-semibold text-danger">
                      {marketData[selectedSymbol].low ? `₹${marketData[selectedSymbol].low.toFixed(2)}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-800 rounded">
                    <div className="text-muted">Open</div>
                    <div className="font-semibold">
                      {marketData[selectedSymbol].open ? `₹${marketData[selectedSymbol].open.toFixed(2)}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-800 rounded">
                    <div className="text-muted">Volume</div>
                    <div className="font-semibold">
                      {formatNumber(marketData[selectedSymbol].volume)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Market Summary */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Market Summary</h3>
          <span className="card-subtitle">Overall market metrics</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-900 bg-opacity-20 rounded border border-blue-800">
            <div className="text-2xl font-bold text-info">F&O</div>
            <div className="text-sm text-muted">Futures & Options</div>
            <div className="mt-2 text-sm">
              Primary trading segment
            </div>
          </div>
          
          <div className="text-center p-4 bg-purple-900 bg-opacity-20 rounded border border-purple-800">
            <div className="text-2xl font-bold text-purple-400">NSE</div>
            <div className="text-sm text-muted">Exchange</div>
            <div className="mt-2 text-sm">
              National Stock Exchange
            </div>
          </div>
          
          <div className="text-center p-4 bg-yellow-900 bg-opacity-20 rounded border border-yellow-800">
            <div className="text-2xl font-bold text-warning">LIVE</div>
            <div className="text-sm text-muted">Data Feed</div>
            <div className="mt-2 text-sm">
              Real-time tick data
            </div>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-gray-800 rounded">
          <div className="text-sm text-muted">
            <strong>Data Source:</strong> TrueData via WebSocket connection<br/>
            <strong>Update Frequency:</strong> Real-time tick-by-tick data<br/>
            <strong>Symbols:</strong> NIFTY, BANKNIFTY, FINNIFTY derivatives<br/>
            <strong>Market Hours:</strong> 9:15 AM - 3:30 PM IST (Monday to Friday)
          </div>
        </div>
      </div>

      {Object.keys(marketData).length === 0 && (
        <div className="card">
          <div className="text-center text-muted p-5">
            <div className="mb-3">📊</div>
            <h3>No Market Data Available</h3>
            <p>Waiting for real-time market data feed...</p>
            <div className="mt-3">
              <div className="spinner"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketData;
