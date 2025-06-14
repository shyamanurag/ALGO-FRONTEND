import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navigation({ user, userRole, systemStatus, connectedAccounts, onLogout }) {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  const activeAccounts = connectedAccounts.filter(acc => acc.status === 'connected').length;
  const totalAccounts = connectedAccounts.length;

  return (
    <nav className="bg-gray-900 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-white">
                Elite Autonomous Trading
              </h1>
            </div>
            
            {userRole === 'admin' && (
              <div className="hidden md:block ml-10">
                <div className="flex items-baseline space-x-4">
                  <Link
                    to="/live-status"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/live-status') || isActive('/')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    🤖 Live Status
                  </Link>
                  
                  <Link
                    to="/trading"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/trading')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    💰 Live Trading
                  </Link>
                  
                  <Link
                    to="/orders"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/orders')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    📋 Orders
                  </Link>
                  
                  <Link
                    to="/strategy-monitoring"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/strategy-monitoring')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    📊 Strategies
                  </Link>
                  
                  <Link
                    to="/admin"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/admin') 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    ⚙️ Admin
                  </Link>
                  
                  <Link
                    to="/accounts"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/accounts')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    Account Management
                  </Link>
                  
                  <Link
                    to="/autonomous-monitoring"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/autonomous-monitoring')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    Autonomous Monitor
                  </Link>
                  
                  <Link
                    to="/elite-recommendations"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      isActive('/elite-recommendations')
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    Elite Advisory
                  </Link>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {/* System Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                systemStatus.status === 'HEALTHY' ? 'bg-green-400' : 
                systemStatus.status === 'WARNING' ? 'bg-yellow-400' : 'bg-red-400'
              }`}></div>
              <span className="text-sm text-gray-300">
                System {systemStatus.status || 'Unknown'}
              </span>
            </div>

            {/* Connected Accounts Count */}
            <div className="flex items-center space-x-2">
              <div className="bg-blue-600 rounded-full px-3 py-1">
                <span className="text-white text-sm font-medium">
                  {activeAccounts}/{totalAccounts}
                </span>
              </div>
              <span className="text-sm text-gray-300">Active Accounts</span>
            </div>

            {/* User Info & Logout */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3 bg-gray-800 rounded-lg px-4 py-2 border border-gray-600">
                <div className="flex flex-col">
                  <div className="text-sm font-medium text-white">{user?.username}</div>
                  <div className="text-xs text-gray-400 capitalize">{userRole} Access</div>
                </div>
                
                <button
                  onClick={onLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-md text-sm font-medium transition duration-200 flex items-center space-x-1"
                  title="Logout"
                >
                  <span>Logout</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {userRole === 'admin' && (
        <div className="md:hidden bg-gray-800">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              to="/"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/') 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Admin Dashboard
            </Link>
            
            <Link
              to="/accounts"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/accounts')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Account Management
            </Link>
            
            <Link
              to="/autonomous-monitoring"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/autonomous-monitoring')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Autonomous Monitor
            </Link>
            
            <Link
              to="/elite-recommendations"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/elite-recommendations')
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Elite Advisory
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navigation;