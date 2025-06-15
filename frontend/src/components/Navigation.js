import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navigation({ user, userRole, systemStatus, connectedAccounts, onLogout }) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const isActive = (path) => location.pathname === path;
  
  const activeAccounts = connectedAccounts.filter(acc => acc.status === 'connected').length;
  const totalAccounts = connectedAccounts.length;

  return (
    <nav className="bg-gray-900 border-b border-gray-700">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14">
          {/* Left section - Logo & Navigation */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-lg font-bold text-white hidden sm:block">
                🤖 Elite Autonomous Trading
              </h1>
              <h1 className="text-sm font-bold text-white sm:hidden">
                🤖 Elite Trading
              </h1>
            </div>
            
            {/* Desktop Navigation */}
            {userRole === 'admin' && (
              <div className="hidden lg:block ml-6">
                <div className="flex items-baseline space-x-2">
                  <Link
                    to="/live-status"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/live-status') || isActive('/')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    🤖 Status
                  </Link>
                  
                  <Link
                    to="/strategy-monitoring"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/strategy-monitoring')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    📊 Strategy
                  </Link>
                  
                  <Link
                    to="/elite-recommendations"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/elite-recommendations')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    ⭐ Elite
                  </Link>
                  
                  <Link
                    to="/autonomous-monitoring"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/autonomous-monitoring')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    🔍 Monitor
                  </Link>
                  
                  <Link
                    to="/admin"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/admin') 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    ⚙️ Admin
                  </Link>
                  
                  <Link
                    to="/accounts"
                    className={`px-2 py-1.5 rounded-md text-xs font-medium ${
                      isActive('/accounts')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    🔗 Accounts
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Right section - Status indicators & User */}
          <div className="flex items-center space-x-3">
            {/* Compact Status Indicators */}
            <div className="hidden md:flex items-center space-x-2">
              {/* Autonomous Trading Status */}
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.autonomous_trading ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`}></div>
                <span className="text-xs text-gray-300">
                  {systemStatus.autonomous_trading ? 'AUTO' : 'OFF'}
                </span>
              </div>

              {/* System Health */}
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.system_health === 'HEALTHY' ? 'bg-green-400' : 
                  systemStatus.system_health === 'WARNING' ? 'bg-yellow-400' : 'bg-red-400'
                }`}></div>
                <span className="text-xs text-gray-300">
                  {systemStatus.system_health === 'HEALTHY' ? 'OK' : 'ERR'}
                </span>
              </div>

              {/* Connected Accounts */}
              <div className="bg-blue-600 rounded px-2 py-1">
                <span className="text-white text-xs font-medium">
                  {activeAccounts}/{totalAccounts}
                </span>
              </div>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-1 rounded-md text-gray-400 hover:text-white hover:bg-gray-700"
            >
              <svg className="h-5 w-5" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
                />
              </svg>
            </button>

            {/* Compact User Section */}
            <div className="flex items-center space-x-2">
              <div className="hidden sm:flex flex-col text-right">
                <div className="text-xs font-medium text-white">{user?.username || 'Admin'}</div>
                <div className="text-xs text-gray-400">{userRole}</div>
              </div>
              
              <button
                onClick={onLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-2 py-1.5 rounded text-xs font-medium transition duration-200"
                title="Logout"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {isMobileMenuOpen && userRole === 'admin' && (
        <div className="lg:hidden bg-gray-800 border-t border-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link
              to="/live-status"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/live-status') || isActive('/')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              🤖 Autonomous Status
            </Link>
            
            <Link
              to="/strategy-monitoring"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/strategy-monitoring')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              📊 Strategy Monitor
            </Link>
            
            <Link
              to="/elite-recommendations"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/elite-recommendations')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              ⭐ Elite Recommendations
            </Link>
            
            <Link
              to="/autonomous-monitoring"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/autonomous-monitoring')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              🔍 Autonomous Monitor
            </Link>
            
            <Link
              to="/admin"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/admin')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              ⚙️ System Admin
            </Link>
            
            <Link
              to="/accounts"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/accounts')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              🔗 Account Management
            </Link>

            {/* Mobile Status Indicators */}
            <div className="border-t border-gray-700 pt-2 mt-2">
              <div className="px-3 py-2 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Autonomous Trading:</span>
                  <span className={`text-xs ${systemStatus.autonomous_trading ? 'text-green-400' : 'text-red-400'}`}>
                    {systemStatus.autonomous_trading ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">System Health:</span>
                  <span className="text-xs text-gray-300">{systemStatus.system_health || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Connected Accounts:</span>
                  <span className="text-xs text-gray-300">{activeAccounts}/{totalAccounts}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navigation;