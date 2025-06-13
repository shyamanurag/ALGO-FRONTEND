import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function LiveMarketDataStatus() {
  const [marketDataStatus, setMarketDataStatus] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMarketDataStatus();
    const interval = setInterval(fetchMarketDataStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMarketDataStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/market-data/status`);
      const data = await response.json();
      setMarketDataStatus(data);
    } catch (error) {
      console.error('Error fetching market data status:', error);
      setMarketDataStatus({
        truedata_connected: false,
        data_provider_enabled: false,
        market_hours: false,
        error: 'Failed to fetch status'
      });
    } finally {
      setLoading(false);
    }
  };

  const testDataFeed = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/market-data/test-feed`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        alert('Market data feed test successful!');
        fetchMarketDataStatus(); // Refresh status
      } else {
        alert('Market data feed test failed');
      }
    } catch (error) {
      console.error('Error testing data feed:', error);
      alert('Error testing data feed');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    if (marketDataStatus.truedata_connected) return 'text-green-600';
    if (marketDataStatus.data_provider_enabled) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusIcon = () => {
    if (marketDataStatus.truedata_connected) return '🟢';
    if (marketDataStatus.data_provider_enabled) return '🟡';
    return '🔴';
  };

  const getDataSourceText = () => {
    if (marketDataStatus.truedata_connected) return 'TrueData Live Feed';
    return 'No Data Available';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-8">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Live Market Data Status</h3>
        <button
          onClick={testDataFeed}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
        >
          Test Data Feed
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Connection Status */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{getStatusIcon()}</span>
            <div>
              <div className="text-sm font-medium text-gray-600">Data Source</div>
              <div className={`text-sm font-bold ${getStatusColor()}`}>
                {getDataSourceText()}
              </div>
            </div>
          </div>
        </div>

        {/* Market Hours */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">
              {marketDataStatus.market_hours ? '🕘' : '🕐'}
            </span>
            <div>
              <div className="text-sm font-medium text-gray-600">Market Status</div>
              <div className={`text-sm font-bold ${
                marketDataStatus.market_hours ? 'text-green-600' : 'text-red-600'
              }`}>
                {marketDataStatus.market_hours ? 'OPEN' : 'CLOSED'}
              </div>
            </div>
          </div>
        </div>

        {/* Symbols Tracked */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">📊</span>
            <div>
              <div className="text-sm font-medium text-gray-600">Symbols Tracked</div>
              <div className="text-sm font-bold text-blue-600">
                {marketDataStatus.symbols_tracked || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Last Update */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">⏰</span>
            <div>
              <div className="text-sm font-medium text-gray-600">Last Update</div>
              <div className="text-sm font-bold text-gray-900">
                {marketDataStatus.data_age_minutes !== undefined 
                  ? `${marketDataStatus.data_age_minutes.toFixed(1)}m ago`
                  : 'Unknown'
                }
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TrueData Configuration */}
      {marketDataStatus.truedata_config && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-900 mb-2">TrueData Configuration</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-blue-700 font-medium">Username:</span>
              <div className="text-blue-900">{marketDataStatus.truedata_config.username}</div>
            </div>
            <div>
              <span className="text-blue-700 font-medium">URL:</span>
              <div className="text-blue-900">{marketDataStatus.truedata_config.url}</div>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Port:</span>
              <div className="text-blue-900">{marketDataStatus.truedata_config.port}</div>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Sandbox:</span>
              <div className="text-blue-900">
                {marketDataStatus.truedata_config.sandbox ? 'Yes' : 'No'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Symbols */}
      {marketDataStatus.live_symbols && marketDataStatus.live_symbols.length > 0 && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <h4 className="font-semibold text-green-900 mb-2">Live Symbols</h4>
          <div className="flex flex-wrap gap-2">
            {marketDataStatus.live_symbols.map((symbol, index) => (
              <span 
                key={index}
                className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full"
              >
                {symbol}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default LiveMarketDataStatus;