import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const StrategyMonitoring = () => {
  const [strategies, setStrategies] = useState([]);
  const [strategyDetails, setStrategyDetails] = useState({});
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStrategies();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStrategies, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/strategies/performance`);
      if (response.ok) {
        const data = await response.json();
        setStrategies(data.strategies || []);
      } else {
        setStrategies([]);
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setError('Failed to fetch strategy data');
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategyDetails = async (strategyName) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies/${strategyName}/details`);
      if (response.ok) {
        const data = await response.json();
        setStrategyDetails(prev => ({
          ...prev,
          [strategyName]: data
        }));
      }
    } catch (error) {
      console.error('Error fetching strategy details:', error);
    }
  };

  const toggleStrategyStatus = async (strategyName, currentStatus) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies/${strategyName}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ active: !currentStatus })
      });

      if (response.ok) {
        fetchStrategies(); // Refresh the list
      } else {
        setError('Failed to toggle strategy status');
      }
    } catch (error) {
      setError('Error toggling strategy: ' + error.message);
    }
  };

  const resetStrategy = async (strategyName) => {
    if (!window.confirm(`Are you sure you want to reset strategy ${strategyName}? This will clear all performance metrics.`)) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies/${strategyName}/reset`, {
        method: 'POST'
      });

      if (response.ok) {
        fetchStrategies(); // Refresh the list
        alert(`Strategy ${strategyName} has been reset successfully`);
      } else {
        setError('Failed to reset strategy');
      }
    } catch (error) {
      setError('Error resetting strategy: ' + error.message);
    }
  };

  const getStrategyStatusColor = (active) => {
    return active ? 'text-green-600' : 'text-red-600';
  };

  const getPerformanceColor = (value) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Strategy Performance Monitoring</h1>
            <p className="text-gray-600">Real-time monitoring of all trading strategies</p>
          </div>
          <button
            onClick={fetchStrategies}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
          >
            Refresh Data
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
            <button 
              onClick={() => setError(null)} 
              className="ml-4 text-sm underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading strategy data...</p>
          </div>
        )}

        {/* Strategy Overview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {strategies.map((strategy, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{strategy.name}</h3>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-medium ${getStrategyStatusColor(strategy.active)}`}>
                    {strategy.active ? '🟢 ACTIVE' : '🔴 INACTIVE'}
                  </span>
                  <button
                    onClick={() => toggleStrategyStatus(strategy.name, strategy.active)}
                    className={`text-xs px-2 py-1 rounded ${
                      strategy.active 
                        ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {strategy.active ? 'Disable' : 'Enable'}
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Signals Today:</span>
                  <span className="font-medium">{strategy.signals_today || 0}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Win Rate:</span>
                  <span className={`font-medium ${
                    strategy.win_rate >= 70 ? 'text-green-600' : 
                    strategy.win_rate >= 50 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {strategy.win_rate?.toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">P&L Today:</span>
                  <span className={`font-medium ${getPerformanceColor(strategy.pnl_today)}`}>
                    ₹{strategy.pnl_today?.toLocaleString() || '0'}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Quality:</span>
                  <span className="font-medium">{strategy.avg_quality?.toFixed(1) || '0'}/10</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Trades:</span>
                  <span className="font-medium">{strategy.total_trades || 0}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Signal:</span>
                  <span className="text-sm text-gray-500">
                    {strategy.last_signal 
                      ? new Date(strategy.last_signal).toLocaleString()
                      : 'No signals'
                    }
                  </span>
                </div>
              </div>

              <div className="mt-4 flex space-x-2">
                <button
                  onClick={() => {
                    setSelectedStrategy(strategy.name);
                    fetchStrategyDetails(strategy.name);
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-2 rounded transition duration-200"
                >
                  View Details
                </button>
                <button
                  onClick={() => resetStrategy(strategy.name)}
                  className="bg-gray-600 hover:bg-gray-700 text-white text-sm px-3 py-2 rounded transition duration-200"
                >
                  Reset
                </button>
              </div>
            </div>
          ))}
        </div>

        {strategies.length === 0 && !loading && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Strategy Data Available</h2>
            <p className="text-gray-600">Strategy performance metrics will appear here once trading begins</p>
          </div>
        )}

        {/* Strategy Details Modal */}
        {selectedStrategy && strategyDetails[selectedStrategy] && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">{selectedStrategy} - Detailed Performance</h2>
                  <button
                    onClick={() => setSelectedStrategy(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="p-6">
                {strategyDetails[selectedStrategy] ? (
                  <div className="space-y-6">
                    {/* Performance Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {strategyDetails[selectedStrategy].total_signals || 0}
                        </div>
                        <div className="text-sm text-gray-600">Total Signals</div>
                      </div>
                      
                      <div className="text-center">
                        <div className={`text-2xl font-bold ${getPerformanceColor(strategyDetails[selectedStrategy].total_pnl)}`}>
                          ₹{strategyDetails[selectedStrategy].total_pnl?.toLocaleString() || '0'}
                        </div>
                        <div className="text-sm text-gray-600">Total P&L</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {strategyDetails[selectedStrategy].sharpe_ratio?.toFixed(2) || '0'}
                        </div>
                        <div className="text-sm text-gray-600">Sharpe Ratio</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {strategyDetails[selectedStrategy].max_drawdown?.toFixed(2) || '0'}%
                        </div>
                        <div className="text-sm text-gray-600">Max Drawdown</div>
                      </div>
                    </div>

                    {/* Recent Signals */}
                    {strategyDetails[selectedStrategy].recent_signals && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Signals</h3>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quality</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Generated</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {strategyDetails[selectedStrategy].recent_signals.map((signal, index) => (
                                <tr key={index}>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {signal.symbol}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                      signal.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                    }`}>
                                      {signal.action}
                                    </span>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {signal.quality_score}/10
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {signal.status}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(signal.generated_at).toLocaleString()}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2 text-gray-600">Loading detailed strategy data...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyMonitoring;