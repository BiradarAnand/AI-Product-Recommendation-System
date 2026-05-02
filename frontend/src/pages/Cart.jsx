import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API = axios.create({ baseURL: "http://localhost:5000/api" });

export default function Cart() {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    if (!token) {
      setError("Please login first");
      setLoading(false);
      return;
    }
    
    try {
      const res = await API.get("/cart", { headers: { Authorization: `Bearer ${token}` } });
      setCart(res.data);
    } catch (e) {
      setError("Failed to load cart");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (productId, newQty) => {
    if (newQty < 1) return;
    try {
      await API.put(`/cart/${productId}`, { quantity: newQty }, { headers: { Authorization: `Bearer ${token}` } });
      loadCart();
    } catch (e) {
      setError("Failed to update quantity");
    }
  };

  const handleRemove = async (productId) => {
    try {
      await API.delete(`/cart/${productId}`, { headers: { Authorization: `Bearer ${token}` } });
      loadCart();
    } catch (e) {
      setError("Failed to remove item");
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading cart...</div>;

  if (!token) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Sign In Required</h1>
        <p className="text-gray-600 mb-6">Please log in to view your cart</p>
        <Link to="/login" className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Go to Login</Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Your Cart</h1>
          <Link to="/" className="text-indigo-600 hover:underline">← Back to shop</Link>
        </div>

        {error && <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

        {!cart || cart.count === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center">
            <p className="text-xl text-gray-500 mb-6">Your cart is empty</p>
            <Link to="/" className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Continue Shopping</Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Items */}
            <div className="lg:col-span-2 space-y-4">
              {cart.items.map((item) => (
                <div key={item.product_id} className="bg-white rounded-lg p-4 flex gap-4 hover:shadow-md transition-shadow">
                  <img src={item.image_url} alt={item.name} className="w-24 h-24 object-cover rounded" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{item.name}</h3>
                    <p className="text-sm text-gray-500">{item.category}</p>
                    <p className="text-lg font-bold text-indigo-600 mt-2">₹{item.price_at_add}</p>
                  </div>
                  <div className="flex flex-col items-end justify-between">
                    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                      <button onClick={() => handleUpdateQuantity(item.product_id, item.quantity - 1)} className="px-2 py-1 hover:bg-gray-200">−</button>
                      <span className="px-3 font-semibold">{item.quantity}</span>
                      <button onClick={() => handleUpdateQuantity(item.product_id, item.quantity + 1)} className="px-2 py-1 hover:bg-gray-200">+</button>
                    </div>
                    <button onClick={() => handleRemove(item.product_id)} className="text-red-500 text-sm hover:underline font-semibold">Remove</button>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="bg-white rounded-lg p-6 h-fit sticky top-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Order Summary</h2>
              <div className="space-y-3 border-b border-gray-200 pb-4">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal ({cart.count} items)</span>
                  <span>₹{cart.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-green-600 font-semibold">
                  <span>Discount (5%)</span>
                  <span>-₹{cart.discount.toFixed(2)}</span>
                </div>
              </div>
              <div className="flex justify-between text-2xl font-bold text-gray-900 mt-4 mb-6">
                <span>Total</span>
                <span>₹{cart.total.toFixed(2)}</span>
              </div>
              <button className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-all">
                Proceed to Checkout
              </button>
              <Link to="/" className="block text-center text-indigo-600 hover:underline mt-4 text-sm font-semibold">Continue Shopping</Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}