import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API = axios.create({ baseURL: "https://ai-product-recommendation-system-by60.onrender.com/api" });

export default function Wishlist() {
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    loadWishlist();
  }, []);

  const loadWishlist = async () => {
    if (!token) {
      setError("Please login first");
      setLoading(false);
      return;
    }
    try {
      const res = await API.get("/wishlist", { headers: { Authorization: `Bearer ${token}` } });
      setWishlist(res.data);
    } catch (e) {
      setError("Failed to load wishlist");
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (productId) => {
    try {
      await API.delete(`/wishlist/${productId}`, { headers: { Authorization: `Bearer ${token}` } });
      loadWishlist();
    } catch (e) {
      setError("Failed to remove item");
    }
  };

  const handleAddToCart = async (productId) => {
    try {
      await API.post(`/wishlist/${productId}/to-cart`, {}, { headers: { Authorization: `Bearer ${token}` } });
      loadWishlist();
    } catch (e) {
      setError("Failed to move to cart");
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading wishlist...</div>;

  if (!token) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Sign In Required</h1>
        <p className="text-gray-600 mb-6">Please log in to view your wishlist</p>
        <Link to="/login" className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Go to Login</Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Your Wishlist</h1>
          <Link to="/" className="text-indigo-600 hover:underline">← Back to shop</Link>
        </div>

        {error && <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

        {!wishlist || wishlist.count === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center">
            <p className="text-xl text-gray-500 mb-6">Your wishlist is empty</p>
            <Link to="/" className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Start Shopping</Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {wishlist.items.map((item) => (
              <div key={item.product_id} className="bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
                <img src={item.image_url} alt={item.name} className="w-full h-48 object-cover" />
                <div className="p-4">
                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">{item.category}</p>
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{item.name}</h3>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-lg font-bold text-indigo-600">₹{item.price}</span>
                    <span className="text-xs text-gray-500">⭐ {item.rating}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAddToCart(item.product_id)}
                      className="flex-1 py-2 bg-indigo-600 text-white text-sm font-semibold rounded hover:bg-indigo-700 transition-all"
                    >
                      Add to Cart
                    </button>
                    <button
                      onClick={() => handleRemove(item.product_id)}
                      className="px-3 py-2 border border-gray-300 text-gray-700 text-sm font-semibold rounded hover:border-red-300 hover:text-red-600 transition-all"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}