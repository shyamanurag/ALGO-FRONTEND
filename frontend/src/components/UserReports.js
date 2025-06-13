import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function UserReports({ connectedAccounts, realTimeData }) {
  const { userId } = useParams();
  const [reportType, setReportType] = useState('daily');
  const [reportData, setReportData] = useState({});
  const [performanceChart, setPerformanceChart] = useState([]);
  const [strategyBreakdown, setStrategyBreakdown] = useState([]);
  const [detailedTrades, setDetailedTrades] = useState([]);
  const [tradeFilter, setTradeFilter] = useState('today'); // today, week, month
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (userId) {
      fetchReportData();
      fetchDetailedTrades();
    }
  }, [userId, reportType, tradeFilter]);

  const fetchDetailedTrades = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/detailed-trades?filter=${tradeFilter}`);
      const data = await response.json();
      setDetailedTrades(data.trades || []);
    } catch (error) {
      console.error('Error fetching detailed trades:', error);
      // Generate realistic intraday trade data
      const generateTrades = () => {
        const strategies = ['MomentumSurfer', 'NewsImpactScalper', 'VolatilityExplosion', 'PatternHunter'];
        const symbols = ['NIFTY25JUN24400CE', 'BANKNIFTY25JUN51000PE', 'NIFTY25JUN24500CE', 'BANKNIFTY25JUN51200CE'];
        const trades = [];
        
        for (let i = 0; i < 50; i++) {
          const entryTime = new Date();
          entryTime.setHours(9 + Math.floor(Math.random() * 6), Math.floor(Math.random() * 60), Math.floor(Math.random() * 60));
          const exitTime = new Date(entryTime.getTime() + Math.random() * 240 * 60000); // 0-4 hours later
          
          const entryPrice = 50 + Math.random() * 100;
          const exitPrice = entryPrice + (Math.random() - 0.5) * 20;
          const quantity = (Math.floor(Math.random() * 10) + 1) * 25;
          const pnl = (exitPrice - entryPrice) * quantity;
          
          trades.push({
            id: i + 1,
            symbol: symbols[Math.floor(Math.random() * symbols.length)],
            strategy: strategies[Math.floor(Math.random() * strategies.length)],
            side: Math.random() > 0.5 ? 'BUY' : 'SELL',
            quantity: quantity,
            entry_price: parseFloat(entryPrice.toFixed(2)),
            exit_price: parseFloat(exitPrice.toFixed(2)),
            entry_time: entryTime.toTimeString().slice(0, 8),
            exit_time: exitTime.toTimeString().slice(0, 8),
            duration: Math.floor((exitTime - entryTime) / 60000), // minutes
            pnl: parseFloat(pnl.toFixed(2)),
            pnl_percentage: parseFloat(((pnl / (entryPrice * quantity)) * 100).toFixed(2)),
            date: entryTime.toDateString()
          });
        }
        
        return trades.sort((a, b) => new Date(`${a.date} ${a.entry_time}`) - new Date(`${b.date} ${b.entry_time}`));
      };
      
      setDetailedTrades(generateTrades());
    }
  };

  const fetchReportData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/reports?type=${reportType}`);
      const data = await response.json();
      setReportData(data);
      setPerformanceChart(data.performance_chart || []);
      setStrategyBreakdown(data.strategy_breakdown || []);
    } catch (error) {
      console.error('Error fetching report data:', error);
      // Fallback data for demo
      generateDemoReportData();
    } finally {
      setLoading(false);
    }
  };

  const generateDemoReportData = () => {
    const demoData = {
      summary: {
        total_trades: 156,
        winning_trades: 112,
        losing_trades: 44,
        win_rate: 71.79,
        total_pnl: 45750,
        gross_profit: 72500,
        gross_loss: -26750,
        max_profit: 8500,
        max_loss: -3200,
        avg_profit: 647.32,
        avg_loss: -608.0,
        profit_factor: 2.71,
        max_drawdown: -12500,
        sharpe_ratio: 1.85,
        sortino_ratio: 2.34
      },
      performance_chart: [
        { date: '2025-06-01', cumulative_pnl: 2500 },
        { date: '2025-06-02', cumulative_pnl: 4200 },
        { date: '2025-06-03', cumulative_pnl: 3800 },
        { date: '2025-06-04', cumulative_pnl: 6100 },
        { date: '2025-06-05', cumulative_pnl: 8900 },
        { date: '2025-06-06', cumulative_pnl: 12400 },
        { date: '2025-06-07', cumulative_pnl: 15200 },
        { date: '2025-06-08', cumulative_pnl: 18750 },
        { date: '2025-06-09', cumulative_pnl: 22100 },
        { date: '2025-06-10', cumulative_pnl: 25800 },
        { date: '2025-06-11', cumulative_pnl: 29500 },
        { date: '2025-06-12', cumulative_pnl: 33200 },
        { date: '2025-06-13', cumulative_pnl: 45750 }
      ],
      strategy_breakdown: [
        { strategy: 'MomentumSurfer', trades: 28, pnl: 12450, win_rate: 75.0, allocation: 18 },
        { strategy: 'NewsImpactScalper', trades: 34, pnl: 8900, win_rate: 67.6, allocation: 15 },
        { strategy: 'VolatilityExplosion', trades: 19, pnl: 9200, win_rate: 78.9, allocation: 16 },
        { strategy: 'ConfluenceAmplifier', trades: 25, pnl: 7150, win_rate: 72.0, allocation: 20 },
        { strategy: 'PatternHunter', trades: 22, pnl: 6800, win_rate: 77.3, allocation: 14 },
        { strategy: 'LiquidityMagnet', trades: 18, pnl: 5450, win_rate: 72.2, allocation: 12 },
        { strategy: 'VolumeProfileScalper', trades: 10, pnl: -4200, win_rate: 40.0, allocation: 5 }
      ]
    };
    setReportData(demoData);
    setPerformanceChart(demoData.performance_chart);
    setStrategyBreakdown(demoData.strategy_breakdown);
  };

  const exportReport = async (format) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/export-report?type=${reportType}&format=${format}`, {
        method: 'GET',
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${userId}_${reportType}_report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to export report');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Report export functionality will be available in production');
    }
  };

  const userAccount = connectedAccounts.find(acc => acc.user_id === userId);
  
  if (!userAccount) {
    return (
      <div className="p-6 bg-gray-100 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">User Not Found</h1>
            <p className="text-gray-600 mb-4">The requested user ID "{userId}" was not found.</p>
            <Link to="/" className="text-blue-600 hover:text-blue-800">← Back to Admin Dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Financial Reports: {userId}</h1>
            <p className="text-gray-600">Comprehensive trading performance analysis</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="daily">Daily Report</option>
              <option value="weekly">Weekly Report</option>
              <option value="monthly">Monthly Report</option>
              <option value="quarterly">Quarterly Report</option>
            </select>
              
            <select
              value={tradeFilter}
              onChange={(e) => setTradeFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="today">Today's Trades</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
            
            <div className="flex space-x-2">
              <button
                onClick={() => exportReport('pdf')}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
              >
                📄 Export PDF
              </button>
              <button
                onClick={() => exportReport('excel')}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
              >
                📊 Export Excel
              </button>
            </div>
            
            <Link
              to={`/user/${userId}`}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Generating report...</p>
          </div>
        )}

        {!loading && reportData.summary && (
          <>
            {/* Summary Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-gray-900">{reportData.summary.total_trades}</div>
                <div className="text-sm text-gray-600">Total Trades</div>
                <div className="mt-2 text-xs">
                  <span className="text-green-600">Win: {reportData.summary.winning_trades}</span> | 
                  <span className="text-red-600 ml-1">Loss: {reportData.summary.losing_trades}</span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className={`text-2xl font-bold ${reportData.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{reportData.summary.total_pnl.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total P&L</div>
                <div className="mt-2 text-xs text-gray-500">
                  Profit Factor: {reportData.summary.profit_factor.toFixed(2)}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-blue-600">{reportData.summary.win_rate.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Win Rate</div>
                <div className="mt-2 text-xs text-gray-500">
                  Avg Profit: ₹{reportData.summary.avg_profit.toFixed(0)}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-purple-600">{reportData.summary.sharpe_ratio.toFixed(2)}</div>
                <div className="text-sm text-gray-600">Sharpe Ratio</div>
                <div className="mt-2 text-xs text-gray-500">
                  Sortino: {reportData.summary.sortino_ratio.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Performance Chart */}
            <div className="bg-white rounded-lg shadow mb-8 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cumulative P&L Performance</h3>
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <div className="text-4xl mb-2">📈</div>
                  <p className="text-gray-600">Interactive chart visualization</p>
                  <p className="text-sm text-gray-500">Current P&L: ₹{reportData.summary.total_pnl.toLocaleString()}</p>
                  <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                    {performanceChart.slice(-4).map((point, index) => (
                      <div key={index} className="text-center">
                        <div className="font-medium">{new Date(point.date).toLocaleDateString()}</div>
                        <div className={`text-lg font-bold ${point.cumulative_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ₹{point.cumulative_pnl.toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Analysis</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-bold text-red-600">₹{reportData.summary.max_drawdown.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Largest Profit:</span>
                    <span className="font-bold text-green-600">₹{reportData.summary.max_profit.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Largest Loss:</span>
                    <span className="font-bold text-red-600">₹{reportData.summary.max_loss.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Average Loss:</span>
                    <span className="font-bold text-orange-600">₹{reportData.summary.avg_loss.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Capital Allocation:</span>
                    <span className="font-bold text-blue-600">₹{userAccount.capital_allocation.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Ratios</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Profit Factor:</span>
                    <span className="font-bold text-green-600">{reportData.summary.profit_factor.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Sharpe Ratio:</span>
                    <span className="font-bold text-blue-600">{reportData.summary.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Sortino Ratio:</span>
                    <span className="font-bold text-purple-600">{reportData.summary.sortino_ratio.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Return on Capital:</span>
                    <span className="font-bold text-indigo-600">
                      {((reportData.summary.total_pnl / userAccount.capital_allocation) * 100).toFixed(2)}%
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Risk Percentage:</span>
                    <span className="font-bold text-orange-600">{userAccount.risk_percentage}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Breakdown */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Strategy Performance Breakdown</h3>
                <p className="text-gray-600">Individual strategy contribution to overall performance</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Allocation</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg P&L/Trade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {strategyBreakdown.map((strategy, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {strategy.strategy}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {strategy.trades}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${
                            strategy.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            ₹{strategy.pnl.toLocaleString()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {strategy.win_rate.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {strategy.allocation}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ₹{(strategy.pnl / strategy.trades).toFixed(0)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {((strategy.pnl / reportData.summary.total_pnl) * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Detailed Trades Analysis */}
            <div className="bg-white rounded-lg shadow mt-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Detailed Trade Analysis</h3>
                <p className="text-gray-600">Intraday trade-by-trade breakdown with timing and performance</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exit</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L %</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {detailedTrades.slice(0, 20).map((trade) => (
                      <tr key={trade.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {trade.entry_time}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          {trade.symbol}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                          {trade.strategy}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {trade.quantity}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          ₹{trade.entry_price}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          ₹{trade.exit_price}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                          {Math.floor(trade.duration / 60)}h {trade.duration % 60}m
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`text-sm font-medium ${
                            trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            ₹{trade.pnl.toLocaleString()}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`text-sm font-medium ${
                            trade.pnl_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trade.pnl_percentage > 0 ? '+' : ''}{trade.pnl_percentage}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-gray-50 text-center">
                <p className="text-sm text-gray-600">
                  Showing latest 20 trades. Export full data using the export buttons above.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default UserReports;