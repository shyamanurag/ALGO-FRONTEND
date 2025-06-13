import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Strategies = () => {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newStrategy, setNewStrategy] = useState({
    name: '',
    description: '',
    parameters: {}
  });
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies`);
      const data = await response.json();
      setStrategies(data.strategies || []); // Extract the strategies array
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setStrategies([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const toggleStrategy = async (strategyId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies/${strategyId}/toggle`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        // Update local state
        setStrategies(strategies.map(strategy => 
          strategy.id === strategyId 
            ? { ...strategy, is_active: !strategy.is_active }
            : strategy
        ));
      } else {
        alert('Failed to toggle strategy');
      }
    } catch (error) {
      console.error('Error toggling strategy:', error);
      alert('Error toggling strategy');
    }
  };

  const createStrategy = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/strategies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newStrategy)
      });

      if (response.ok) {
        setShowCreateForm(false);
        setNewStrategy({ name: '', description: '', parameters: {} });
        fetchStrategies(); // Refresh the list
        alert('Strategy created successfully');
      } else {
        const error = await response.json();
        alert(`Failed to create strategy: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating strategy:', error);
      alert('Error creating strategy');
    }
  };

  const strategyDescriptions = {
    'Moving Average Crossover': {
      description: 'Generates buy signals when short-term moving average crosses above long-term moving average, and sell signals when it crosses below.',
      parameters: ['Short Period (5)', 'Long Period (20)'],
      riskLevel: 'Medium',
      suitability: 'Trending markets'
    },
    'RSI Momentum': {
      description: 'Uses Relative Strength Index to identify overbought (>70) and oversold (<30) conditions for contrarian trades.',
      parameters: ['RSI Period (14)', 'Oversold Level (30)', 'Overbought Level (70)'],
      riskLevel: 'Low',
      suitability: 'Range-bound markets'
    },
    'Price Breakout': {
      description: 'Identifies significant price breakouts above recent highs or below recent lows with strong momentum.',
      parameters: ['Lookback Period (20)', 'Breakout Threshold (2%)'],
      riskLevel: 'High',
      suitability: 'Volatile markets'
    },
    'Mean Reversion': {
      description: 'Trades against extreme price movements, expecting prices to revert to their statistical mean.',
      parameters: ['Lookback Period (15)', 'Z-Score Threshold (2.0)'],
      riskLevel: 'Medium',
      suitability: 'Stable markets'
    },
    'Volume Breakout': {
      description: 'Combines price direction with unusual volume spikes to identify high-probability trade setups.',
      parameters: ['Volume Threshold (1.5x)', 'Price Change Min (1%)'],
      riskLevel: 'Medium',
      suitability: 'All market conditions'
    },
    'Bollinger Bands': {
      description: 'Uses statistical bands around moving average to identify when prices are relatively high or low.',
      parameters: ['Period (20)', 'Standard Deviations (2.0)'],
      riskLevel: 'Low',
      suitability: 'Range-bound markets'
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="strategies-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Trading Strategies</h1>
        <p className="dashboard-subtitle">
          Manage and monitor your algorithmic trading strategies
        </p>
      </div>

      {/* Strategy Overview */}
      <div className="metrics-grid mb-5">
        <div className="metric-card">
          <div className="metric-value neutral">
            {strategies.length}
          </div>
          <div className="metric-label">Total Strategies</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value positive">
            {strategies.filter(s => s.is_active).length}
          </div>
          <div className="metric-label">Active Strategies</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            {strategies.filter(s => !s.is_active).length}
          </div>
          <div className="metric-label">Inactive Strategies</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value neutral">
            6
          </div>
          <div className="metric-label">Core Algorithms</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-4">
        <button 
          onClick={() => setShowCreateForm(true)}
          className="btn btn-primary"
        >
          Create Custom Strategy
        </button>
        
        <button 
          onClick={() => {
            const activeCount = strategies.filter(s => s.is_active).length;
            if (activeCount === 0) {
              alert('No active strategies to disable');
              return;
            }
            strategies.filter(s => s.is_active).forEach(s => toggleStrategy(s.id));
          }}
          className="btn btn-secondary"
        >
          Disable All Active
        </button>
      </div>

      {/* Create Strategy Form */}
      {showCreateForm && (
        <div className="card mb-5">
          <div className="card-header">
            <h2 className="card-title">Create New Strategy</h2>
            <button 
              onClick={() => setShowCreateForm(false)}
              className="btn btn-secondary btn-sm"
            >
              Cancel
            </button>
          </div>
          
          <form onSubmit={createStrategy}>
            <div className="form-group">
              <label className="form-label">Strategy Name</label>
              <input
                type="text"
                value={newStrategy.name}
                onChange={(e) => setNewStrategy({...newStrategy, name: e.target.value})}
                className="form-input"
                required
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                value={newStrategy.description}
                onChange={(e) => setNewStrategy({...newStrategy, description: e.target.value})}
                className="form-input"
                rows="3"
                required
              />
            </div>
            
            <button type="submit" className="btn btn-primary">
              Create Strategy
            </button>
          </form>
        </div>
      )}

      {/* Strategies List */}
      <div className="strategy-list">
        {strategies.map((strategy) => {
          const strategyInfo = strategyDescriptions[strategy.name] || {};
          
          return (
            <div key={strategy.id} className="strategy-item">
              <div className="strategy-info">
                <div className="strategy-name">{strategy.name}</div>
                <div className="strategy-description">{strategy.description}</div>
                
                {strategyInfo.description && (
                  <div className="mt-3 p-3 bg-gray-800 rounded">
                    <div className="text-sm mb-2">
                      <strong>How it works:</strong> {strategyInfo.description}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                      <div>
                        <strong>Parameters:</strong>
                        <ul className="text-muted mt-1">
                          {strategyInfo.parameters?.map((param, index) => (
                            <li key={index}>• {param}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <strong>Risk Level:</strong>
                        <span className={`ml-2 ${
                          strategyInfo.riskLevel === 'High' ? 'text-danger' :
                          strategyInfo.riskLevel === 'Medium' ? 'text-warning' : 'text-success'
                        }`}>
                          {strategyInfo.riskLevel}
                        </span>
                      </div>
                      
                      <div>
                        <strong>Best For:</strong>
                        <span className="text-muted ml-2">{strategyInfo.suitability}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="strategy-controls">
                <span className={`strategy-status ${strategy.is_active ? 'active' : 'inactive'}`}>
                  {strategy.is_active ? 'Active' : 'Inactive'}
                </span>
                
                <button
                  onClick={() => toggleStrategy(strategy.id)}
                  className={`btn btn-sm ${strategy.is_active ? 'btn-danger' : 'btn-success'}`}
                >
                  {strategy.is_active ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {strategies.length === 0 && (
        <div className="card">
          <div className="text-center text-muted p-5">
            <div className="mb-3">🤖</div>
            <h3>No Strategies Found</h3>
            <p>Create your first trading strategy to get started</p>
            <button 
              onClick={() => setShowCreateForm(true)}
              className="btn btn-primary mt-3"
            >
              Create Strategy
            </button>
          </div>
        </div>
      )}

      {/* Strategy Performance Info */}
      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">Strategy Performance Guidelines</h3>
          <span className="card-subtitle">Understanding algorithmic trading strategies</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-success">Trend Following Strategies</h4>
            <ul className="space-y-2 text-sm">
              <li>• <strong>Moving Average Crossover:</strong> Best in trending markets</li>
              <li>• <strong>Price Breakout:</strong> Captures momentum moves</li>
              <li>• <strong>Volume Breakout:</strong> Confirms breakout validity</li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-3 text-info">Mean Reversion Strategies</h4>
            <ul className="space-y-2 text-sm">
              <li>• <strong>RSI Momentum:</strong> Trades overbought/oversold levels</li>
              <li>• <strong>Mean Reversion:</strong> Statistical price normalization</li>
              <li>• <strong>Bollinger Bands:</strong> Range-bound trading</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-900 bg-opacity-20 border border-blue-800 rounded">
          <div className="text-sm text-info">
            <strong>Risk Management:</strong><br/>
            • All strategies incorporate 2% daily stop loss<br/>
            • Position sizing based on volatility and confidence<br/>
            • Automatic square-off at 3:15 PM for intraday trades<br/>
            • Real-time monitoring and risk controls
          </div>
        </div>
      </div>
    </div>
  );
};

export default Strategies;
