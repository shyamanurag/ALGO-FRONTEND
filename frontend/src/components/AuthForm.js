import React, { useState } from 'react';

const AuthForm = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: 'trader@algotrade.com',
    name: 'Demo Trader'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // For demo purposes, just simulate login
    onLogin({
      id: '1',
      email: formData.email,
      name: formData.name,
      riskTolerance: 1.0,
      maxPositionSize: 100000
    });
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">AlgoTrade Pro</h1>
        <p className="auth-subtitle">
          Autonomous Algorithmic Trading Platform
        </p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          
          <button type="submit" className="btn btn-primary w-full">
            Login to Trading Platform
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <p className="text-muted">
            Demo credentials are pre-filled. This is a trading simulation platform.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthForm;
