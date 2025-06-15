import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function AnalyticsReports() {
  const [reportType, setReportType] = useState('daily');
  const [selectedUser, setSelectedUser] = useState('all');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    end: new Date().toISOString().split('T')[0] // today
  });
  const [users, setUsers] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
    generateReport();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/list`);
      const data = await response.json();
      if (data.success) {
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      // Demo users for development
      setUsers([
        { user_id: 'USER001', name: 'Autonomous Trader 1' },
        { user_id: 'USER002', name: 'Autonomous Trader 2' },
        { user_id: 'USER003', name: 'Autonomous Trader 3' }
      ]);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const endpoint = selectedUser === 'all' 
        ? `${BACKEND_URL}/api/reports/system/${reportType}`
        : `${BACKEND_URL}/api/reports/user/${selectedUser}/${reportType}`;
      
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      });

      const response = await fetch(`${endpoint}?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setReportData(data.report);
      } else {
        // Generate demo data for development
        const demoData = generateDemoReportData();
        setReportData(demoData);
      }
    } catch (error) {
      console.error('Error generating report:', error);
      // Generate demo data for development
      const demoData = generateDemoReportData();
      setReportData(demoData);
    } finally {
      setLoading(false);
    }
  };

  const generateDemoReportData = () => {
    // Return empty data structure - NO MOCK DATA
    return {
      summary: {
        total_trades: 0,
        total_pnl: 0,
        avg_win_rate: 0,
        best_day: 0,
        worst_day: 0,
        total_capital_used: 0,
        avg_roi: 0
      },
      daily_data: [],
      strategy_breakdown: []
    };
  };

  const downloadReport = (format = 'csv') => {
    if (!reportData) return;

    let content = '';
    let filename = '';
    let mimeType = '';

    if (format === 'csv') {
      // CSV format
      const headers = ['Date', 'Trades', 'P&L', 'Win Rate %', 'Capital Used', 'ROI %', 'Strategies Used', 'Max Drawdown', 'Avg Trade Duration (min)'];
      const rows = reportData.daily_data.map(day => [
        day.date,
        day.trades,
        day.pnl,
        day.win_rate,
        day.capital_used,
        day.roi_percent,
        day.strategies_used,
        day.max_drawdown,
        day.avg_trade_duration
      ]);
      
      content = [headers, ...rows].map(row => row.join(',')).join('\n');
      filename = `trading_report_${selectedUser}_${dateRange.start}_to_${dateRange.end}.csv`;
      mimeType = 'text/csv';
    } else if (format === 'json') {
      // JSON format
      content = JSON.stringify(reportData, null, 2);
      filename = `trading_report_${selectedUser}_${dateRange.start}_to_${dateRange.end}.json`;
      mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const downloadStrategyReport = () => {
    if (!reportData?.strategy_breakdown) return;

    const headers = ['Strategy', 'Total Trades', 'P&L', 'Win Rate %'];
    const rows = reportData.strategy_breakdown.map(strategy => [
      strategy.strategy,
      strategy.trades,
      strategy.pnl,
      strategy.win_rate
    ]);
    
    const content = [headers, ...rows].map(row => row.join(',')).join('\n');
    const filename = `strategy_performance_${selectedUser}_${new Date().toISOString().split('T')[0]}.csv`;
    
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">📊 Analytics & Reports</h1>
          <p className="text-gray-600">Comprehensive trading performance analysis and downloadable reports</p>
        </div>

        {/* Report Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Report Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="daily">Daily Performance</option>
                <option value="weekly">Weekly Summary</option>
                <option value="monthly">Monthly Analysis</option>
                <option value="strategy">Strategy Breakdown</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">User/Account</label>
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Users (System-wide)</option>
                {users.map(user => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.user_id} - {user.name || 'Autonomous Trader'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({...prev, start: e.target.value}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({...prev, end: e.target.value}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-between items-center mt-6">
            <button
              onClick={generateReport}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition duration-200 disabled:opacity-50"
            >
              {loading ? 'Generating...' : '📊 Generate Report'}
            </button>

            <div className="flex space-x-2">
              <button
                onClick={() => downloadReport('csv')}
                disabled={!reportData || loading}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium transition duration-200 disabled:opacity-50"
              >
                📥 Download CSV
              </button>
              <button
                onClick={() => downloadReport('json')}
                disabled={!reportData || loading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded font-medium transition duration-200 disabled:opacity-50"
              >
                📥 Download JSON
              </button>
              <button
                onClick={downloadStrategyReport}
                disabled={!reportData?.strategy_breakdown || loading}
                className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded font-medium transition duration-200 disabled:opacity-50"
              >
                📥 Strategy Report
              </button>
            </div>
          </div>
        </div>

        {/* Report Summary */}
        {reportData && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">📈 Performance Summary</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-800">{reportData.summary?.total_trades || 0}</div>
                <div className="text-sm text-blue-600">Total Trades</div>
              </div>
              
              <div className={`p-4 rounded-lg ${
                (reportData.summary?.total_pnl || 0) >= 0 
                  ? 'bg-gradient-to-r from-green-50 to-green-100' 
                  : 'bg-gradient-to-r from-red-50 to-red-100'
              }`}>
                <div className={`text-2xl font-bold ${
                  (reportData.summary?.total_pnl || 0) >= 0 ? 'text-green-800' : 'text-red-800'
                }`}>
                  ₹{(reportData.summary?.total_pnl || 0).toLocaleString()}
                </div>
                <div className={`text-sm ${
                  (reportData.summary?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  Total P&L
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-800">
                  {(reportData.summary?.avg_win_rate || 0).toFixed(1)}%
                </div>
                <div className="text-sm text-purple-600">Average Win Rate</div>
              </div>
              
              <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-800">
                  {(reportData.summary?.avg_roi || 0).toFixed(2)}%
                </div>
                <div className="text-sm text-orange-600">Average ROI</div>
              </div>
            </div>
          </div>
        )}

        {/* Strategy Performance Breakdown */}
        {reportData?.strategy_breakdown && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🎯 Strategy Performance Breakdown</h2>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportData.strategy_breakdown.map((strategy, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {strategy.strategy}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {strategy.trades}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        strategy.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{strategy.pnl.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="font-medium text-blue-600">{strategy.win_rate}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Daily Performance Table */}
        {reportData?.daily_data && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">📅 Daily Performance Data</h2>
            </div>
            <div className="overflow-x-auto max-h-96">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capital Used</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ROI %</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportData.daily_data.map((day, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{day.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{day.trades}</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        day.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{day.pnl.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{day.win_rate}%</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{day.capital_used.toLocaleString()}</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        parseFloat(day.roi_percent) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {day.roi_percent}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsReports;