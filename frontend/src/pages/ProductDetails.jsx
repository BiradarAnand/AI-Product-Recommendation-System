// src/pages/ProductDetails.jsx
// Opens when user clicks a product anywhere → /product/:id

import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";

const BASE = "https://ai-product-recommendation-system-by60.onrender.com";
const API  = axios.create({ baseURL: BASE });

function imgSrc(url) {
  if (!url) return "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=80";
  if (url.startsWith("http")) return url;
  return `${BASE}/${url}`;
}

function StarRow({ rating }) {
  const r = Math.min(5, Math.max(0, Number(rating)));
  return (
    <span className="text-yellow-400">
      {[1,2,3,4,5].map(i => (
        <span key={i} style={{ opacity: i <= Math.round(r) ? 1 : 0.25 }}>★</span>
      ))}
    </span>
  );
}

export default function ProductDetails() {
  const { id }     = useParams();
  const navigate   = useNavigate();

  const [product, setProduct]     = useState(null);
  const [related, setRelated]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");
  const [added, setAdded]         = useState(false);
  const [wishlisted, setWishlisted] = useState(false);
  const [quantity, setQuantity]   = useState(1);
  const [aiExplanation, setAiExplanation] = useState("");

  const token      = localStorage.getItem("token");
  const isLoggedIn = !!token;
  const headers    = isLoggedIn ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    window.scrollTo(0, 0);
    setLoading(true);
    setError("");
    setAdded(false);
    setWishlisted(false);
    setAiExplanation("");

    const fetchAll = async () => {
      try {
        // Fetch product detail
        const res = await API.get(`/products/${id}`);
        setProduct(res.data);

        // Fetch related products (same category)
        try {
          const relRes = await API.get(`/products?category=${encodeURIComponent(res.data.category)}`);
          const others = (relRes.data || []).filter(p => String(p.id) !== String(id)).slice(0, 4);
          setRelated(others);
        } catch {}

        // Fetch wishlist to check if wishlisted
        if (isLoggedIn) {
          try {
            const wRes = await API.get("/api/wishlist", { headers });
            const ids  = new Set((wRes.data.items || []).map(i => i.product_id));
            setWishlisted(ids.has(Number(id)));
          } catch {}

          // Fetch AI explanation
          try {
            const aiRes = await API.get(`/api/recommend/explain?product_id=${id}`, { headers });
            setAiExplanation(aiRes.data?.explanation || "");
          } catch {}
        }
      } catch {
        setError("Product not found. It may have been removed.");
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [id]);

  const handleAddToCart = async () => {
    if (!isLoggedIn) { navigate("/login"); return; }
    try {
      await API.post("/api/cart", { product_id: Number(id), quantity }, { headers });
      setAdded(true);
      setTimeout(() => setAdded(false), 3000);
    } catch {}
  };

  const handleWishlist = async () => {
    if (!isLoggedIn) { navigate("/login"); return; }
    try {
      if (wishlisted) {
        await API.delete(`/api/wishlist/${id}`, { headers });
        setWishlisted(false);
      } else {
        await API.post("/api/wishlist", { product_id: Number(id) }, { headers });
        setWishlisted(true);
      }
    } catch {}
  };

  // ── LOADING ──
  if (loading) return (
    <div className="min-h-screen bg-gray-50">
      <nav className="sticky top-0 z-50 px-10 py-4 bg-white shadow-sm flex items-center gap-4">
        <Link to="/" className="text-2xl font-black text-gray-900" style={{ fontFamily: "'Playfair Display', serif" }}>
          RecoVibe<span className="text-yellow-400">.</span>
        </Link>
      </nav>
      <div className="max-w-5xl mx-auto px-6 py-16 grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="rounded-3xl bg-gray-200 animate-pulse" style={{ height: "480px" }} />
        <div className="space-y-4 pt-4">
          {[240, 120, 80, 80, 160, 120, 48].map((w, i) => (
            <div key={i} className="h-4 bg-gray-200 animate-pulse rounded" style={{ width: `${w}px` }} />
          ))}
        </div>
      </div>
    </div>
  );

  // ── ERROR ──
  if (error) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-5xl mb-4">😕</p>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Product Not Found</h1>
        <p className="text-gray-500 mb-6">{error}</p>
        <Link to="/" className="px-6 py-3 bg-gray-900 text-white rounded-full font-semibold hover:bg-yellow-400 hover:text-gray-900 transition-colors">
          Back to Shop
        </Link>
      </div>
    </div>
  );

  const discount = 10 + (Number(id) * 7 + Number(id) * 3) % 26;
  const originalPrice = Math.round(product.price * 100 / (100 - discount));

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "'DM Sans', sans-serif" }}>

      {/* ── NAVBAR ── */}
      <nav className="sticky top-0 z-50 px-10 py-4 bg-white shadow-sm flex items-center justify-between">
        <Link to="/" className="text-2xl font-black text-gray-900" style={{ fontFamily: "'Playfair Display', serif" }}>
          RecoVibe<span className="text-yellow-400">.</span>
        </Link>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link to="/" className="hover:text-gray-900 transition-colors">Home</Link>
          <span>/</span>
          <span className="text-gray-400">{product.category}</span>
          <span>/</span>
          <span className="text-gray-900 font-medium truncate max-w-[200px]">{product.name}</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/cart" className="text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors">🛒 Cart</Link>
          <Link to="/wishlist" className="text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors">❤️ Wishlist</Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* ── MAIN PRODUCT SECTION ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 bg-white rounded-3xl p-8 shadow-sm">

          {/* LEFT — Image */}
          <div className="relative">
            <div className="rounded-2xl overflow-hidden bg-gray-50 flex items-center justify-center" style={{ height: "480px" }}>
              <img
                src={imgSrc(product.image_url)}
                alt={product.name}
                className="w-full h-full object-contain p-4"
                onError={e => {
                  e.target.onerror = null;
                  e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=80";
                }}
              />
              <span className="absolute top-4 left-4 bg-red-500 text-white text-sm font-bold px-3 py-1 rounded-full">
                {discount}% OFF
              </span>
            </div>
          </div>

          {/* RIGHT — Details */}
          <div className="flex flex-col justify-center">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-2">{product.brand}</p>
            <h1 className="text-3xl font-black text-gray-900 leading-tight mb-3" style={{ fontFamily: "'Playfair Display', serif" }}>
              {product.name}
            </h1>

            {/* Rating */}
            <div className="flex items-center gap-2 mb-4">
              <StarRow rating={product.rating} />
              <span className="text-sm font-semibold text-gray-700">{Number(product.rating).toFixed(1)}</span>
              <span className="text-sm text-gray-400">({product.reviews || 0} reviews)</span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-3 mb-5">
              <span className="text-4xl font-black text-red-500">₹{Number(product.price).toLocaleString("en-IN")}</span>
              <span className="text-lg text-gray-400 line-through">₹{originalPrice.toLocaleString("en-IN")}</span>
              <span className="text-green-600 font-bold text-sm">You save ₹{(originalPrice - product.price).toLocaleString("en-IN")}</span>
            </div>

            {/* Category & Stock */}
            <div className="flex gap-3 mb-5">
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">{product.category}</span>
              {product.stock > 0
                ? <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">✓ In Stock ({product.stock} left)</span>
                : <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-semibold">Out of Stock</span>
              }
            </div>

            {/* Description */}
            {product.description && (
              <p className="text-gray-600 text-sm leading-relaxed mb-6 border-l-4 border-yellow-400 pl-4">
                {product.description}
              </p>
            )}

            {/* AI Explanation */}
            {aiExplanation && (
              <div className="mb-6 p-4 rounded-xl text-sm" style={{ background: "#fffbeb", border: "1px solid #fde68a" }}>
                <p className="font-bold text-yellow-800 mb-1">🤖 Why this is recommended for you</p>
                <p className="text-yellow-700 leading-relaxed">{aiExplanation}</p>
              </div>
            )}

            {/* Quantity */}
            <div className="flex items-center gap-4 mb-6">
              <span className="text-sm font-semibold text-gray-700">Quantity:</span>
              <div className="flex items-center gap-2 bg-gray-100 rounded-full px-2 py-1">
                <button onClick={() => setQuantity(q => Math.max(1, q - 1))}
                  className="w-8 h-8 rounded-full bg-white shadow text-lg font-bold hover:bg-gray-50 flex items-center justify-center">−</button>
                <span className="w-8 text-center font-bold text-gray-900">{quantity}</span>
                <button onClick={() => setQuantity(q => Math.min(product.stock || 10, q + 1))}
                  className="w-8 h-8 rounded-full bg-white shadow text-lg font-bold hover:bg-gray-50 flex items-center justify-center">+</button>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleAddToCart}
                disabled={product.stock === 0}
                className={`flex-1 py-3.5 rounded-full font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${
                  added ? "bg-green-500 text-white" : "bg-gray-900 text-white hover:bg-yellow-400 hover:text-gray-900"
                }`}
              >
                {added ? "✓ Added to Cart!" : "Add to Cart"}
              </button>
              <button
                onClick={handleWishlist}
                className={`px-5 py-3.5 rounded-full font-bold text-sm border-2 transition-all hover:-translate-y-0.5 ${
                  wishlisted
                    ? "border-red-400 bg-red-50 text-red-500"
                    : "border-gray-200 text-gray-700 hover:border-gray-900"
                }`}
              >
                {wishlisted ? "❤️ Saved" : "🤍 Save"}
              </button>
            </div>
          </div>
        </div>

        {/* ── RELATED PRODUCTS ── */}
        {related.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-black text-gray-900 mb-6" style={{ fontFamily: "'Playfair Display', serif" }}>
              More in {product.category}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
              {related.map(p => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/product/${p.id}`)}
                  className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all cursor-pointer"
                >
                  <div className="bg-gray-50 overflow-hidden" style={{ height: "180px" }}>
                    <img
                      src={imgSrc(p.image_url)}
                      alt={p.name}
                      className="w-full h-full object-contain p-2"
                      onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&q=80"; }}
                    />
                  </div>
                  <div className="p-3">
                    <p className="text-xs text-gray-400 font-medium truncate">{p.brand}</p>
                    <h3 className="text-sm font-bold text-gray-900 mt-0.5 line-clamp-2">{p.name}</h3>
                    <p className="text-red-500 font-extrabold mt-1 text-sm">₹{Number(p.price).toLocaleString("en-IN")}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Back button */}
        <div className="mt-10 text-center">
          <button onClick={() => navigate(-1)}
            className="px-8 py-3 border-2 border-gray-300 text-gray-700 rounded-full font-semibold hover:border-gray-900 transition-colors">
            ← Go Back
          </button>
        </div>
      </div>
    </div>
  );
}