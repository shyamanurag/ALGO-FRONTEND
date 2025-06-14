import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function LiveIndicesHeader() {
  const [indices, setIndices] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    fetchLiveIndices();
    // Update every 2 seconds for real-time feel
    const interval = setInterval(fetchLiveIndices, 2000);
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-gray-900">📈 Live Market Data</h2>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${
                isConnected ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'
              }`}>
                {isConnected ? '🟢 CONNECTED' : '🔴 DISCONNECTED'}
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              {Object.entries(indices).map(([symbol, data]) => (
                <div key={symbol} className="flex items-center space-x-2 bg-gray-50 rounded-lg px-3 py-2">
                  <div className="flex flex-col">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-sm text-gray-900">{symbol}</span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium border ${getStatusColor(data.data_source)}`}>
                        {getStatusIcon(data.data_source)} {data.data_source}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-lg font-bold text-gray-900">
                        {data.ltp > 0 ? `₹${data.ltp.toLocaleString()}` : 'N/A'}
                      </span>
                      {data.change !== 0 && (
                        <span className={`text-sm font-medium ${
                          data.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {data.change >= 0 ? '▲' : '▼'} {Math.abs(data.change).toFixed(2)} ({data.change_percent.toFixed(2)}%)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Last Update: {lastUpdate || 'Loading...'}
            </div>
            <button
              onClick={fetchLiveIndices}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm font-medium transition duration-200"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveIndicesHeader;