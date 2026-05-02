import { useState, useEffect } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "http://localhost:5000/api" });

// Category-specific fallback images
const CATEGORY_IMAGES = {
  "Shirts":       "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&q=80",
  "Tshirts":      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80",
  "Jeans":        "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&q=80",
  "Trousers":     "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&q=80",
  "Track Pants":  "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
  "Casual Shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
  "Sports Shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
  "Watches":      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
  "Hoodies":      "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=600&q=80",
  "Blazers":      "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&q=80",
  "Kurtas":       "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600&q=80",
  "Sneakers":     "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=600&q=80",
};

const getFallbackImage = (category = "") => {
  const key = Object.keys(CATEGORY_IMAGES).find(
    (k) => k.toLowerCase() === category.trim().toLowerCase()
  );
  return CATEGORY_IMAGES[key] || "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80";
};

const getProductImage = (product) => {
  const url = product.image_url || "";
  if (url.includes("unsplash.com")) return url;
  if (url.startsWith("http"))       return url;
  if (url)                          return `http://127.0.0.1:5000/${url}`;
  return getFallbackImage(product.category);
};

// Deterministic discount per product id
const getDiscount = (id) => 10 + (id * 7 + id * 3) % 26;

// Render star rating (e.g. 4.3 → ★★★★☆)
const StarRating = ({ rating }) => {
  const full  = Math.floor(rating);
  const half  = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="text-yellow-400 text-xs tracking-tight">
      {"★".repeat(full)}
      {half ? "½" : ""}
      <span className="text-gray-300">{"★".repeat(empty)}</span>
    </span>
  );
};

export default function RecommendedProducts() {
  const [products, setProducts]               = useState([]);
  const [loading, setLoading]                 = useState(true);
  const [title, setTitle]                     = useState("Personalised for You");
  const [subtitle, setSubtitle]               = useState("");
  const [addedToCart, setAddedToCart]         = useState({});
  const [addedToWishlist, setAddedToWishlist] = useState({});

  const token = localStorage.getItem("token");

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      if (token) {
        // ── Tier 1: personalised feed (collab + popularity) ──────────
        try {
          const res = await API.get("/recommend/feed?top_n=12", {
            headers: { Authorization: `Bearer ${token}` },
          });
          const items       = res.data.results  || [];
          const personalised = res.data.personalised ?? true;

          if (items.length > 0) {
            setProducts(items);
            if (personalised) {
              setTitle("Recommended For You");
              setSubtitle("AI-powered picks based on your taste");
            } else {
              setTitle("Trending Right Now");
              setSubtitle("Top-rated products loved by shoppers");
            }
            setLoading(false);
            return;
          }
        } catch (e) {
          console.log("[RecommendedProducts] Feed failed:", e.message);
        }

        // ── Tier 2: trending fallback (logged-in but no collab data) ─
        try {
          const res = await API.get("/recommend/trending?top_n=12", {
            headers: { Authorization: `Bearer ${token}` },
          });
          const items = res.data.results || [];
          if (items.length > 0) {
            setProducts(items);
            setTitle("Trending Right Now");
            setSubtitle("Top-rated products loved by shoppers");
            setLoading(false);
            return;
          }
        } catch (e) {
          console.log("[RecommendedProducts] Trending fallback failed:", e.message);
        }

      } else {
        // ── Guest: trending products (popularity-ranked, no auth needed) ──
        try {
          const res = await API.get("/recommend/trending?top_n=12");
          const items = res.data.results || [];
          if (items.length > 0) {
            setProducts(items);
            setTitle("Trending Now");
            setSubtitle("Top-rated picks you'll love");
            setLoading(false);
            return;
          }
        } catch (e) {
          console.log("[RecommendedProducts] Guest trending failed:", e.message);
        }
      }

      // ── Last resort: engine not trained yet → show nothing gracefully ──
      setProducts([]);
      setTitle("Featured Products");
      setSubtitle("Browse our collection below");

    } catch (e) {
      console.error("[RecommendedProducts] Unexpected error:", e);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (productId, e) => {
    e.preventDefault();
    if (!token) { alert("Please login first"); return; }
    try {
      await API.post("/cart", { product_id: productId, quantity: 1 }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAddedToCart((prev) => ({ ...prev, [productId]: true }));
      setTimeout(() => setAddedToCart((prev) => ({ ...prev, [productId]: false })), 2000);
    } catch (e) { console.error("Add to cart failed:", e); }
  };

  const handleAddToWishlist = async (productId, e) => {
    e.preventDefault();
    if (!token) { alert("Please login first"); return; }
    try {
      await API.post("/wishlist", { product_id: productId }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAddedToWishlist((prev) => ({ ...prev, [productId]: true }));
      setTimeout(() => setAddedToWishlist((prev) => ({ ...prev, [productId]: false })), 2000);
    } catch (e) { console.error("Add to wishlist failed:", e); }
  };

  // ── Skeleton loader ───────────────────────────────────────────────
  if (loading) {
    return (
      <div className="px-10 py-16">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center mb-10">
            <div className="h-10 bg-gray-200 rounded w-64 mx-auto mb-3 animate-pulse"></div>
            <div className="h-4 bg-gray-100 rounded w-48 mx-auto animate-pulse"></div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl overflow-hidden animate-pulse shadow-sm">
                <div className="h-64 bg-gray-200"></div>
                <div className="p-4 space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-8 bg-gray-200 rounded-full mt-3"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <section className="px-10 py-16 bg-white">
      <div className="max-w-[1400px] mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <h2 className="font-display text-4xl font-black text-gray-900">{title}</h2>
          <p className="text-gray-500 mt-3 text-base">{subtitle}</p>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-10 text-gray-400">
            No recommendations available yet — browse our collection below!
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {products.map((product) => (
              <div
                key={product.id}
                className="product-card bg-white rounded-2xl shadow-sm overflow-hidden hover:-translate-y-2 hover:shadow-xl transition-all duration-300"
              >
                {/* Image */}
                <div className="relative overflow-hidden bg-gray-50 flex items-center justify-center" style={{ height: "260px" }}>
                  <img
                    src={getProductImage(product)}
                    alt={product.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = getFallbackImage(product.category);
                    }}
                  />

                  {/* Discount badge */}
                  <span className="absolute top-2 left-2 bg-red-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                    {getDiscount(product.id)}% off
                  </span>

                  {/* Wishlist button */}
                  <button
                    onClick={(e) => handleAddToWishlist(product.id, e)}
                    className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md hover:scale-110 transition-transform"
                    title="Save to Wishlist"
                  >
                    {addedToWishlist[product.id] ? "❤️" : "🤍"}
                  </button>

                  {/* Recommendation score badge (subtle) */}
                  {product.recommendation_score > 0 && (
                    <span className="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
                      {Math.round(product.recommendation_score * 100)}% match
                    </span>
                  )}
                </div>

                {/* Info */}
                <div className="p-4">
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">{product.brand}</p>
                  <h3 className="font-bold text-gray-900 mt-1 text-sm leading-snug line-clamp-2">{product.name}</h3>

                  {/* Stars + review count */}
                  <div className="flex items-center gap-1.5 mt-1.5">
                    <StarRating rating={product.rating || 0} />
                    <span className="text-xs text-gray-400">
                      {product.rating?.toFixed(1)} ({product.reviews?.toLocaleString()} reviews)
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-3">
                    <span className="text-red-500 font-extrabold text-base">₹{product.price?.toLocaleString()}</span>
                    <span className="text-xs text-gray-400 capitalize">{product.category}</span>
                  </div>

                  <button
                    onClick={(e) => handleAddToCart(product.id, e)}
                    className={`mt-3 w-full py-2 rounded-full text-xs font-semibold transition-all ${
                      addedToCart[product.id]
                        ? "bg-green-500 text-white"
                        : "bg-gray-900 text-white hover:bg-yellow-400 hover:text-gray-900"
                    }`}
                  >
                    {addedToCart[product.id] ? "✓ Added" : "Add to Cart"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}