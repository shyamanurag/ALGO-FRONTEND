import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const OrderManagement = () => {
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [orderForm, setOrderForm] = useState({
    symbol: '',
    action: 'BUY',
    quantity: '',
    orderType: 'MARKET',
    price: '',
    stopLoss: '',
    target: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetchOrders();
    fetchPositions();
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchOrders();
      fetchPositions();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/trading/orders`);
      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/positions`);
      if (response.ok) {
        const data = await response.json();
        setPositions(data.positions || []);
      }
    } catch (error) {
      console.error('Error fetching positions:', error);
    }
  };

  const handleSubmitOrder = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const orderData = {
        symbol: orderForm.symbol.toUpperCase(),
        action: orderForm.action,
        quantity: parseInt(orderForm.quantity),
        order_type: orderForm.orderType,
        price: orderForm.orderType !== 'MARKET' ? parseFloat(orderForm.price) : null
      };

      const response = await fetch(`${BACKEND_URL}/api/trading/place-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`Order placed successfully! Order ID: ${data.order_id}`);
        setOrderForm({
          symbol: '',
          action: 'BUY',
          quantity: '',
          orderType: 'MARKET',
          price: '',
          stopLoss: '',
          target: ''
        });
        // Refresh orders and positions
        fetchOrders();
        fetchPositions();
      } else {
        setError(data.error || 'Failed to place order');
      }
    } catch (error) {
      setError('Error placing order: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/trading/cancel-order/${orderId}`, {
        method: 'POST'
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setSuccess('Order cancelled successfully');
        fetchOrders();
      } else {
        setError(data.error || 'Failed to cancel order');
      }
    } catch (error) {
      setError('Error cancelling order: ' + error.message);
    }
  };

  const handleSquareOffPosition = async (symbol) => {
    if (!window.confirm(`Are you sure you want to square off position for ${symbol}?`)) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/trading/square-off/${symbol}`, {
        method: 'POST'
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setSuccess(`Position for ${symbol} squared off successfully`);
        fetchPositions();
        fetchOrders();
      } else {
        setError(data.error || 'Failed to square off position');
      }
    } catch (error) {
      setError('Error squaring off position: ' + error.message);
    }
  };

  const getOrderStatusColor = (status) => {
    switch (status) {
      case 'FILLED': return 'text-green-600';
      case 'PENDING': return 'text-yellow-600';
      case 'CANCELLED': return 'text-red-600';
      case 'REJECTED': return 'text-red-700';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Order Management</h1>

        {/* Alert Messages */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            <strong>Success:</strong> {success}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Order Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Place New Order</h2>
              
              <form onSubmit={handleSubmitOrder} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Symbol</label>
                  <input
                    type="text"
                    value={orderForm.symbol}
                    onChange={(e) => setOrderForm({...orderForm, symbol: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., NIFTY24JUN24000CE"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Action</label>
                  <select
                    value={orderForm.action}
                    onChange={(e) => setOrderForm({...orderForm, action: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Quantity</label>
                  <input
                    type="number"
                    value={orderForm.quantity}
                    onChange={(e) => setOrderForm({...orderForm, quantity: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., 25"
                    min="1"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Order Type</label>
                  <select
                    value={orderForm.orderType}
                    onChange={(e) => setOrderForm({...orderForm, orderType: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="MARKET">MARKET</option>
                    <option value="LIMIT">LIMIT</option>
                  </select>
                </div>

                {orderForm.orderType === 'LIMIT' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Price</label>
                    <input
                      type="number"
                      step="0.01"
                      value={orderForm.price}
                      onChange={(e) => setOrderForm({...orderForm, price: e.target.value})}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., 150.50"
                      required
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Placing Order...' : 'Place Order'}
                </button>
              </form>

              <div className="mt-4 p-3 bg-yellow-50 rounded border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <strong>Risk Warning:</strong> This is live trading. Ensure you understand the risks before placing orders.
                </p>
              </div>
            </div>
          </div>

          {/* Orders and Positions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Recent Orders */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Recent Orders</h2>
                <p className="text-gray-600">Your order history and current status</p>
              </div>
              
              {orders.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {orders.slice(0, 10).map((order, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {order.symbol}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {order.side}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {order.quantity}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {order.order_type}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ₹{order.price?.toFixed(2) || 'Market'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`text-sm font-medium ${getOrderStatusColor(order.status)}`}>
                              {order.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {order.status === 'PENDING' && (
                              <button
                                onClick={() => handleCancelOrder(order.order_id)}
                                className="text-red-600 hover:text-red-800 font-medium"
                              >
                                Cancel
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <p>No orders found</p>
                  <p className="text-sm">Your order history will appear here</p>
                </div>
              )}
            </div>

            {/* Current Positions */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Current Positions</h2>
                <p className="text-gray-600">Your active trading positions</p>
              </div>
              
              {positions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Price</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L %</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {positions.map((position, index) => {
                        const pnlPercent = position.average_entry_price > 0 
                          ? ((position.current_price - position.average_entry_price) / position.average_entry_price) * 100 
                          : 0;
                        
                        return (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {position.symbol}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {position.quantity}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              ₹{position.average_entry_price?.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              ₹{position.current_price?.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-sm font-medium ${
                                position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                ₹{position.unrealized_pnl?.toFixed(2)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-sm font-medium ${
                                pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {pnlPercent.toFixed(2)}%
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {position.status === 'OPEN' && (
                                <button
                                  onClick={() => handleSquareOffPosition(position.symbol)}
                                  className="text-red-600 hover:text-red-800 font-medium"
                                >
                                  Square Off
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  <div className="text-4xl mb-2">📊</div>
                  <p>No active positions</p>
                  <p className="text-sm">Your positions will appear here after trading</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderManagement;