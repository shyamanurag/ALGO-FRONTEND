import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function LiveIndicesHeader() {
  const [indices, setIndices] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    fetchLiveIndices();
    // Update every 3 seconds for better performance
    const interval = setInterval(fetchLiveIndices, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchLiveIndices = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/market-data/live`);
      const data = await response.json();
      
      if (data.success && data.indices) {
        // Process all indices data
        const processedIndices = {};
        
        ['NIFTY', 'BANKNIFTY', 'FINNIFTY'].forEach(symbol => {
          const symbolData = data.indices[symbol];
          if (symbolData) {
            processedIndices[symbol] = {
              symbol,
              ltp: symbolData.ltp || 0,
              change: symbolData.change || 0,
              change_percent: symbolData.change_percent || 0,
              volume: symbolData.volume || 0,
              data_source: symbolData.data_source || 'NO_DATA',
              market_status: symbolData.market_status || 'CLOSED'
            };
          } else {
            // Show that we're trying to connect but no data yet
            processedIndices[symbol] = {
              symbol,
              ltp: 0,
              change: 0,
              change_percent: 0,
              volume: 0,
              data_source: 'CONNECTING',
              market_status: data.market_status || 'OPEN'
            };
          }
        });
        
        setIndices(processedIndices);
        setLastUpdate(new Date().toLocaleTimeString());
        setIsConnected(data.data_provider_status === 'CONNECTED');
      }
    } catch (error) {
      console.error('Error fetching live indices:', error);
      setIsConnected(false);
      // Set empty state for all indices
      const emptyIndices = {};
      ['NIFTY', 'BANKNIFTY', 'FINNIFTY'].forEach(symbol => {
        emptyIndices[symbol] = {
          symbol,
          ltp: 0,
          change: 0,
          change_percent: 0,
          volume: 0,
          data_source: 'NO_DATA',
          market_status: 'UNKNOWN'
        };
      });
      setIndices(emptyIndices);
    }
  };

  const getStatusColor = (dataSource) => {
    switch (dataSource) {
      case 'TRUEDATA_LIVE': return 'bg-green-100 text-green-800 border-green-200';
      case 'CONNECTING': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'NO_DATA': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (dataSource) => {
    switch (dataSource) {
      case 'TRUEDATA_LIVE': return '🟢';
      case 'CONNECTING': return '🟡';
      case 'NO_DATA': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-2">
          {/* Header section with connection status */}
          <div className="flex items-center space-x-4 mb-2 sm:mb-0">
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-gray-900 hidden sm:block">📈 Live Market Data</h2>
              <h2 className="text-xs font-bold text-gray-900 sm:hidden">📈 Market</h2>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${
                isConnected ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'
              }`}>
                {isConnected ? '🟢' : '🔴'} {isConnected ? 'LIVE' : 'OFF'}
              </span>
            </div>
          </div>
          
          {/* Indices data - Compact layout */}
          <div className="flex items-center justify-between w-full sm:w-auto">
            <div className="flex items-center space-x-3 overflow-x-auto">
              {Object.entries(indices).map(([symbol, data]) => (
                <div key={symbol} className="flex-shrink-0 bg-gray-50 rounded-lg px-2 py-1.5">
                  <div className="flex items-center space-x-2">
                    <div className="flex flex-col">
                      <div className="flex items-center space-x-1">
                        <span className="font-bold text-xs text-gray-900">{symbol}</span>
                        <span className={`inline-flex items-center px-1 py-0.5 rounded text-xs ${getStatusColor(data.data_source)}`}>
                          {getStatusIcon(data.data_source)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-sm font-bold text-gray-900">
                          {data.ltp > 0 ? `₹${data.ltp.toLocaleString('en-IN', {maximumFractionDigits: 2})}` : 'N/A'}
                        </span>
                        {data.change !== 0 && (
                          <span className={`text-xs font-medium ${
                            data.change >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {data.change >= 0 ? '▲' : '▼'} {data.change_percent.toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Control section */}
            <div className="flex items-center space-x-2 ml-4">
              <div className="text-xs text-gray-600 hidden sm:block">
                {lastUpdate && `${lastUpdate.split(':').slice(0,2).join(':')}`}
              </div>
              <button
                onClick={fetchLiveIndices}
                className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium transition duration-200 flex-shrink-0"
                title="Refresh market data"
              >
                ↻
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveIndicesHeader;