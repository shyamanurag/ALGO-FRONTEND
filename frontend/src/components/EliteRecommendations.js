import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function EliteRecommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(null);
  const [scanStats, setScanStats] = useState({});

  useEffect(() => {
    fetchEliteRecommendations();
    fetchScanStats();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchEliteRecommendations, 300000);
    return () => clearInterval(interval);
  }, []);

  const fetchEliteRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/elite-recommendations`);
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setLastScanTime(data.scan_timestamp);
    } catch (error) {
      console.error('Error fetching elite recommendations:', error);
      // No fallback data - let component handle empty state
      setRecommendations([]);
      setLastScanTime(new Date().toISOString());
    } finally {
      setLoading(false);
    }
  };

  const fetchScanStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/elite-recommendations/stats`);
      const data = await response.json();
      setScanStats(data);
    } catch (error) {
      console.error('Error fetching scan stats:', error);
      // No fallback data - let component handle empty state
      setScanStats({});
    }
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'BUY': return 'bg-green-100 text-green-800';
      case 'SELL': return 'bg-red-100 text-red-800';
      case 'HOLD': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const calculatePotentialReturn = (currentPrice, targetPrice) => {
    return ((targetPrice - currentPrice) / currentPrice * 100);
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🤖 Elite Autonomous Recommendations</h1>
            <p className="text-gray-600">10/10 Confidence Advisory Signals (Autonomous Generation)</p>
            <div className="flex items-center mt-2 text-sm text-gray-500">
              <div className="w-3 h-3 bg-green-400 rounded-full mr-2 animate-pulse"></div>
              <span>Fully Autonomous - No Human Intervention</span>
            </div>
          </div>
          
          <div className="text-right text-sm text-gray-600">
            <div>Last Autonomous Scan: {lastScanTime ? new Date(lastScanTime).toLocaleTimeString() : 'Scanning...'}</div>
            <div>Next Auto Scan: {new Date(Date.now() + 300000).toLocaleTimeString()}</div>
            <div className="text-xs text-green-600 mt-1">🤖 Autonomous System Active</div>
          </div>
        </div>

        {/* Elite Scan Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">🔍</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Stocks Scanned</p>
                <p className="text-2xl font-bold text-gray-900">{scanStats.total_scanned || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">⭐</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Elite Found</p>
                <p className="text-2xl font-bold text-purple-600">{scanStats.elite_found || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">%</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">{scanStats.success_rate || 0}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Return</p>
                <p className="text-2xl font-bold text-orange-600">{scanStats.historical_performance?.avg_return || 0}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Important Notice */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-8">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-blue-400 text-xl">🤖</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>Fully Autonomous System:</strong> Elite recommendations are generated completely autonomously by our AI algorithms every 5 minutes. 
                These are advisory signals designed for 7-10 day holding periods and are NOT executed automatically by our trading system, which operates exclusively on intraday strategies.
              </p>
            </div>
          </div>
        </div>

        {/* Elite Recommendations Grid */}
        {loading && recommendations.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Autonomous system scanning markets for elite opportunities...</p>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Elite Recommendations</h3>
            <p className="text-gray-600 mb-4">
              Our Elite autonomous engine maintains extremely high standards. Currently, no stocks meet the 10/10 confidence criteria.
            </p>
            <div className="text-sm text-green-600">
              <div className="flex items-center justify-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                Autonomous scanning continues every 5 minutes
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {recommendations.map((recommendation) => (
              <div key={recommendation.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{recommendation.symbol}</h3>
                      <p className="text-sm text-gray-600">{recommendation.timeframe} Target</p>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getRecommendationColor(recommendation.recommendation)}`}>
                        {recommendation.recommendation}
                      </span>
                      <div className="text-xs text-gray-500 mt-1">
                        Confidence: {recommendation.confidence}/10
                      </div>
                    </div>
                  </div>

                  {/* Price Information */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Current Price</p>
                      <p className="text-lg font-bold text-gray-900">₹{recommendation.current_price}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Target Price</p>
                      <p className="text-lg font-bold text-green-600">₹{recommendation.target_price}</p>
                    </div>
                  </div>

                  {/* Potential Return */}
                  <div className="bg-green-50 rounded-lg p-3 mb-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">Potential Return:</span>
                      <span className="text-lg font-bold text-green-600">
                        +{calculatePotentialReturn(recommendation.current_price, recommendation.target_price).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-gray-600">Risk:Reward Ratio:</span>
                      <span className="text-sm font-semibold text-blue-600">1:{recommendation.risk_reward}</span>
                    </div>
                  </div>

                  {/* Analysis */}
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">AI Analysis:</p>
                    <p className="text-sm text-gray-600 leading-relaxed">{recommendation.analysis}</p>
                  </div>

                  {/* Key Reasons */}
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Key Factors:</p>
                    <div className="flex flex-wrap gap-1">
                      {recommendation.reasons.map((reason, index) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Risk Management */}
                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Stop Loss:</span>
                      <span className="text-sm font-semibold text-red-600">₹{recommendation.stop_loss}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span>Generated by AI:</span>
                      <span>{new Date(recommendation.generated_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Action Footer */}
                <div className="bg-gray-50 px-6 py-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">ID: {recommendation.id}</span>
                    <span className="text-xs text-purple-600 font-medium">🤖 AUTONOMOUS ELITE</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Historical Performance */}
        {scanStats.historical_performance && (
          <div className="bg-white rounded-lg shadow mt-8 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Historical Autonomous Performance</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{scanStats.historical_performance.total_recommendations}</div>
                <div className="text-sm text-gray-600">Total Recommendations</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{scanStats.historical_performance.successful}</div>
                <div className="text-sm text-gray-600">Successful</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{scanStats.historical_performance.failed}</div>
                <div className="text-sm text-gray-600">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{scanStats.historical_performance.avg_return}%</div>
                <div className="text-sm text-gray-600">Average Return</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EliteRecommendations;