import React, { useEffect, useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import RecommendedProducts from "../components/RecommendedProducts";

// ── Constants (safe outside component — no hooks) ──────────────────────────

const API = axios.create({ baseURL: "https://ai-product-recommendation-system-by60.onrender.com" });

const HERO_SLIDES = [
  { image: "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=700&q=80", label: "Summer Edit 2026" },
  { image: "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=700&q=80", label: "New Arrivals" },
  { image: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=700&q=80", label: "Street Style" },
  { image: "https://images.unsplash.com/photo-1529391409740-59f2cea08bc6?w=700&q=80", label: "Premium Collection" },
  { image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=700&q=80", label: "Modern Essentials" },
];

const DEMO_PRODUCTS = [
  { id: 1,  name: "Running Sneakers",       brand: "Nike",   price: 2999, rating: 4.5, category: "Sports Shoes", image_url: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80" },
  { id: 2,  name: "Classic White Sneakers", brand: "Adidas", price: 3299, rating: 4.5, category: "Casual Shoes", image_url: "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=600&q=80" },
  { id: 3,  name: "Leather Boots",          brand: "Aldo",   price: 4999, rating: 4.6, category: "Casual Shoes", image_url: "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=600&q=80" },
  { id: 4,  name: "Slip-On Loafers",        brand: "Clarks", price: 3799, rating: 4.4, category: "Casual Shoes", image_url: "https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=600&q=80" },
  { id: 5,  name: "Oxford Button-Down",     brand: "Zara",   price: 1899, rating: 4.3, category: "Shirts",       image_url: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&q=80" },
  { id: 6,  name: "Linen Casual Shirt",     brand: "H&M",    price: 1599, rating: 4.2, category: "Shirts",       image_url: "https://images.unsplash.com/photo-1588359348347-9bc6cbbb689e?w=600&q=80" },
  { id: 7,  name: "Striped Polo Shirt",     brand: "Mango",  price: 1399, rating: 4.1, category: "Shirts",       image_url: "https://images.unsplash.com/photo-1625910513602-b2735be9e0f8?w=600&q=80" },
  { id: 8,  name: "Graphic Print Tee",      brand: "H&M",    price:  899, rating: 4.4, category: "Tshirts",      image_url: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80" },
  { id: 9,  name: "Essential Crew Neck",    brand: "Gap",    price:  699, rating: 4.3, category: "Tshirts",      image_url: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&q=80" },
  { id: 10, name: "V-Neck Basic Tee",       brand: "Puma",   price:  749, rating: 4.2, category: "Tshirts",      image_url: "https://images.unsplash.com/photo-1516826957135-700dedea698c?w=600&q=80" },
  { id: 11, name: "Slim Fit Chinos",        brand: "Zara",   price: 2299, rating: 4.4, category: "Trousers",     image_url: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&q=80" },
  { id: 12, name: "Relaxed Fit Jeans",      brand: "Levi's", price: 2599, rating: 4.5, category: "Jeans",        image_url: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&q=80" },
  { id: 13, name: "Track Pants",            brand: "H&M",    price: 2199, rating: 4.1, category: "Track Pants",  image_url: "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80" },
  { id: 14, name: "Minimalist Steel Watch", brand: "Fossil", price: 5999, rating: 4.7, category: "Watches",      image_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80" },
  { id: 15, name: "Chronograph Sport",      brand: "Titan",  price: 8499, rating: 4.6, category: "Watches",      image_url: "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=600&q=80" },
  { id: 16, name: "Classic Hoodie",         brand: "H&M",    price: 1799, rating: 4.7, category: "Hoodies",      image_url: "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=600&q=80" },
  { id: 17, name: "Zip-Up Hoodie",          brand: "Puma",   price: 1999, rating: 4.3, category: "Hoodies",      image_url: "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=600&q=80" },
  { id: 18, name: "Tech Fleece Hoodie",     brand: "Nike",   price: 3199, rating: 4.5, category: "Hoodies",      image_url: "https://images.unsplash.com/photo-1578681994506-b8f463449011?w=600&q=80" },
];

const CATEGORIES = ["All", "Shoes", "Shirts", "T-Shirts", "Pants", "Watches", "Hoodies"];

const CATEGORY_MAP = {
  "Shoes":    ["shoes", "casual shoes", "sports shoes"],
  "Shirts":   ["shirts"],
  "T-Shirts": ["tshirts", "t-shirts", "t shirts"],
  "Pants":    ["pants", "jeans", "track pants", "trousers"],
  "Watches":  ["watches"],
  "Hoodies":  ["hoodies"],
};

const MINI_PRODUCTS = [
  { label: "Shirts",  price: "₹1399", img: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=200&q=80" },
  { label: "Watches", price: "₹5999", img: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200&q=80" },
  { label: "Hoodie",  price: "₹1799", img: "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=200&q=80" },
];

const imgSrc = (p) => {
  if (!p.image_url) return "";
  if (p.image_url.includes("unsplash.com")) {
    return p.image_url.replace(/w=\d+/, "w=800").replace(/q=\d+/, "q=90");
  }
  if (p.image_url.startsWith("http")) return p.image_url;
  return `https://ai-product-recommendation-system-by60.onrender.com/${p.image_url}`;
};

const getDiscount = (id) => 10 + (id * 7 + id * 3) % 26;

const getFallbackImage = (category = "") => {
  const cat = (category || "").toLowerCase().trim();
  const map = {
    "shirts":       "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&q=80",
    "tshirts":      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80",
    "jeans":        "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&q=80",
    "trousers":     "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&q=80",
    "track pants":  "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
    "casual shoes": "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=600&q=80",
    "sports shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
    "watches":      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
  };
  return map[cat] || "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80";
};

// ── Component ──────────────────────────────────────────────────────────────

export default function Home() {
  const [products, setProducts]             = useState([]);
  const [search, setSearch]                 = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [slideIndex, setSlideIndex]         = useState(0);
  const [slideOpacity, setSlideOpacity]     = useState(1);
  const intervalRef                         = useRef(null);
  const navigate                            = useNavigate();

  // ── NEW: auth + cart/wishlist state ─────────────────────────
  const token                               = localStorage.getItem("token");
  const isLoggedIn                          = !!token;
  const user                                = JSON.parse(localStorage.getItem("user") || "null");
  const [cartCount, setCartCount]           = useState(0);
  const [wishlistCount, setWishlistCount]   = useState(0);
  const [wishlistIds, setWishlistIds]       = useState(new Set());
  const [addedCart, setAddedCart]           = useState({});     // { productId: true }
  const [showHistory, setShowHistory]       = useState(false);
  const [searchHistory, setSearchHistory]   = useState([]);
  const searchRef                           = useRef(null);
  // ────────────────────────────────────────────────────────────

  // ── Inject fonts once ──
  useEffect(() => {
    if (!document.getElementById("rv-fonts")) {
      const link = document.createElement("link");
      link.id = "rv-fonts";
      link.rel = "stylesheet";
      link.href =
        "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap";
      document.head.appendChild(link);

      const style = document.createElement("style");
      style.textContent = `
        body { font-family: 'DM Sans', sans-serif; }
        .font-display { font-family: 'Playfair Display', serif; }
        .underline-yellow { position: relative; display: inline-block; }
        .underline-yellow::after {
          content: ''; position: absolute; left: 0; bottom: -4px;
          width: 100%; height: 5px; background: #F5C518; border-radius: 4px;
        }
        .product-img-zoom { transition: transform 0.4s ease; }
        .product-card:hover .product-img-zoom { transform: scale(1.07); }
      `;
      document.head.appendChild(style);
    }
  }, []);

  // ── Fetch products ──
useEffect(() => {
  axios
    .get("https://ai-product-recommendation-system-by60.onrender.com/products")
    .then((res) => {
      const sorted = [...res.data].sort((a, b) => {
        const aGood = (a.image_url || "").startsWith("http");
        const bGood = (b.image_url || "").startsWith("http");
        if (aGood && !bGood) return -1;
        if (!aGood && bGood) return  1;
        return (b.rating || 0) - (a.rating || 0);
      });
      setProducts(sorted);
    })
    .catch(() => setProducts(DEMO_PRODUCTS));
}, []);

  // ── NEW: Load cart + wishlist counts on mount ──
  useEffect(() => {
    if (!isLoggedIn) return;
    const headers = { Authorization: `Bearer ${token}` };

    API.get("/api/cart", { headers })
      .then((res) => setCartCount(res.data.count || 0))
      .catch(() => {});

    API.get("/api/wishlist", { headers })
      .then((res) => {
        setWishlistCount(res.data.count || 0);
        const ids = new Set((res.data.items || []).map((i) => i.product_id));
        setWishlistIds(ids);
      })
      .catch(() => {});

    API.get("/api/search-history?limit=10", { headers })
      .then((res) => setSearchHistory(res.data.queries || []))
      .catch(() => {});
  }, [isLoggedIn]);

  // ── NEW: Close history dropdown on outside click ──
  useEffect(() => {
    const handleClick = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowHistory(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ── Slider ──
  const startSlider = () => {
    intervalRef.current = setInterval(() => {
      setSlideOpacity(0);
      setTimeout(() => {
        setSlideIndex((prev) => (prev + 1) % HERO_SLIDES.length);
        setSlideOpacity(1);
      }, 400);
    }, 3500);
  };

  useEffect(() => {
    startSlider();
    return () => clearInterval(intervalRef.current);
  }, []);

  const goToSlide = (idx) => {
    clearInterval(intervalRef.current);
    setSlideOpacity(0);
    setTimeout(() => {
      setSlideIndex(idx);
      setSlideOpacity(1);
      startSlider();
    }, 400);
  };

  // ── Filtering ──
  const filtered = products.filter((p) => {
    const matchSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.brand?.toLowerCase().includes(search.toLowerCase());
    const dbCat = (p.category || "").trim().toLowerCase();
    const matchCat =
      activeCategory === "All" ||
      (CATEGORY_MAP[activeCategory] || []).includes(dbCat);
    return matchSearch && matchCat;
  });

  const countFor = (cat) => {
    if (cat === "All") return products.length;
    return products.filter((p) =>
      (CATEGORY_MAP[cat] || []).includes((p.category || "").trim().toLowerCase())
    ).length;
  };

  // ── NEW: ML search (navbar search button click) ──
  const handleMLSearch = async () => {
    if (!search.trim()) return;
    setShowHistory(false);
    try {
      const res = await API.get("/api/recommend/search", {
        params: { q: search, top_n: 50 },
        headers: isLoggedIn ? { Authorization: `Bearer ${token}` } : {},
      });
      setProducts(res.data.results || []);
      // Refresh search history
      if (isLoggedIn) {
        const h = await API.get("/api/search-history?limit=10", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSearchHistory(h.data.queries || []);
      }
    } catch {
      // Fallback: keep local filter working
    }
  };

  // ── NEW: Add to cart ──
  const handleAddToCart = async (e, productId, price) => {
    e.stopPropagation();
    if (!isLoggedIn) { navigate("/login"); return; }
    try {
      await API.post("/api/cart", { product_id: productId, quantity: 1 }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCartCount((c) => c + 1);
      setAddedCart((prev) => ({ ...prev, [productId]: true }));
      setTimeout(() => setAddedCart((prev) => ({ ...prev, [productId]: false })), 2000);
    } catch (err) {
      console.error("Add to cart failed:", err);
    }
  };

  // ── NEW: Add to wishlist ──
  const handleWishlist = async (e, productId) => {
    e.stopPropagation();
    if (!isLoggedIn) { navigate("/login"); return; }
    try {
      if (wishlistIds.has(productId)) {
        await API.delete(`/api/wishlist/${productId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setWishlistIds((prev) => { const s = new Set(prev); s.delete(productId); return s; });
        setWishlistCount((c) => Math.max(0, c - 1));
      } else {
        await API.post("/api/wishlist", { product_id: productId }, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setWishlistIds((prev) => new Set([...prev, productId]));
        setWishlistCount((c) => c + 1);
      }
    } catch (err) {
      console.error("Wishlist failed:", err);
    }
  };

  // ── NEW: Logout ──
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.reload();
  };

  // ── Render ──
  return (
    <div className="bg-gray-50 min-h-screen">

      {/* ── NAVBAR ── */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-10 py-4 bg-white/95 backdrop-blur-sm shadow-sm">
        <a href="/" className="font-display text-2xl font-black tracking-tight text-gray-900">
          RecoVibe<span className="text-yellow-400">.</span>
        </a>
        <ul className="flex items-center gap-7 text-sm font-medium text-gray-800 list-none">
          <li className="border-b-2 border-yellow-400 pb-0.5">
            <Link to="/" className="text-gray-900 no-underline">Home</Link>
          </li>
          <li className="cursor-pointer hover:text-yellow-500 transition-colors">Best Seller</li>
         <li className="cursor-pointer hover:text-yellow-500 transition-colors">
  <Link to="/occasion-chatbot" className="no-underline text-inherit">
    Shop by Occasion
  </Link>
</li>
          <li className="cursor-pointer hover:text-yellow-500 transition-colors">New Releases</li>
          <li className="cursor-pointer hover:text-yellow-500 transition-colors">Most Reviewed</li>
          {user?.role === "admin" && (
            
            <li>
              <Link to="/admin" className="text-red-500 font-bold hover:text-red-600">Admin</Link>
            </li>
          )}
        </ul>

        {/* ── NAVBAR RIGHT — search + cart + wishlist + auth ── */}
        <div className="flex items-center gap-4">

          {/* Search with history dropdown */}
          <div ref={searchRef} className="relative">
            <div className="flex items-center border-2 border-gray-200 rounded-full overflow-hidden focus-within:border-yellow-400 transition-colors bg-white">
              <input
                type="text"
                placeholder="Search products..."
                className="px-4 py-2 text-sm outline-none w-52 bg-transparent"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onFocus={() => isLoggedIn && searchHistory.length > 0 && setShowHistory(true)}
                onKeyDown={(e) => e.key === "Enter" && handleMLSearch()}
              />
              <button
                onClick={handleMLSearch}
                className="px-4 py-2 bg-gray-900 text-white text-sm hover:bg-yellow-400 hover:text-gray-900 transition-colors"
              >
                🔍
              </button>
            </div>

            {/* Search history dropdown — Google style */}
            {showHistory && searchHistory.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent Searches</span>
                </div>
                {searchHistory.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setSearch(q); setShowHistory(false); handleMLSearch(); }}
                    className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 border-b border-gray-50 last:border-b-0"
                  >
                    <span className="text-gray-400 text-xs">🕐</span>
                    {q}
                  </button>
                ))}
                <button
                  onClick={async () => {
                    await API.delete("/api/search-history", { headers: { Authorization: `Bearer ${token}` } });
                    setSearchHistory([]);
                    setShowHistory(false);
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-gray-400 hover:text-gray-600 bg-gray-50 border-t border-gray-100"
                >
                  Clear history
                </button>
              </div>
            )}
          </div>

          {/* Cart link with count badge */}
          <Link to="/cart" className="relative flex items-center gap-1 text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline">
            🛒
            {cartCount > 0 && (
              <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                {cartCount > 9 ? "9+" : cartCount}
              </span>
            )}
            <span className="ml-1">Cart</span>
          </Link>

          {/* Wishlist link with count badge */}
          <Link to="/wishlist" className="relative flex items-center gap-1 text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline">
            ❤️
            {wishlistCount > 0 && (
              <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                {wishlistCount > 9 ? "9+" : wishlistCount}
              </span>
            )}
            <span className="ml-1">Wishlist</span>
          </Link>

          {/* Login / Logout */}
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors"
            >
              Logout
            </button>
          ) : (
            <Link to="/login" className="text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline">
              Login
            </Link>
          )}
        </div>
      </nav>

      {/* ── HERO ── (unchanged) */}
      <section className="grid grid-cols-2 gap-16 items-center px-20 py-16 max-w-[1400px] mx-auto min-h-screen [&>*]:min-w-0">

        {/* LEFT */}
        <div className="relative z-10">
          <span className="inline-block bg-yellow-400 text-gray-900 text-xs font-bold uppercase tracking-widest px-4 py-1.5 rounded-full mb-6">
            ✨ New Season 2026
          </span>
          <h1 className="font-display text-6xl font-black leading-tight text-gray-900">
            Daily Fabulous <br />
            <span className="underline-yellow">Style for You.</span>
          </h1>
          <p className="text-gray-500 mt-5 text-lg leading-relaxed max-w-md">
            Ready to dress to impress with our fabulous style collection.
            Curated looks for every mood and occasion.
          </p>
          <div className="flex gap-4 mt-8">
            <button className="flex items-center gap-2 bg-gray-900 text-white px-7 py-3.5 rounded-full font-semibold hover:bg-gray-700 transition-all hover:-translate-y-0.5">
              Shop Now →
            </button>
            <button className="px-7 py-3.5 rounded-full border-2 border-gray-300 font-semibold hover:border-gray-900 transition-all hover:-translate-y-0.5">
              Learn More
            </button>
          </div>
          <div className="flex gap-10 mt-10">
            {[
              { num: "5k+", label: "Happy Customers" },
              { num: "10K+", label: "Products" },
              { num: "4.9★", label: "Avg. Rating" },
            ].map((s) => (
              <div key={s.label}>
                <div className="font-display text-2xl font-black text-gray-900">{s.num}</div>
                <div className="text-xs text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
          <div className="flex gap-4 mt-10">
            {MINI_PRODUCTS.map((mp) => (
              <div key={mp.label} className="bg-white rounded-2xl shadow-md overflow-hidden w-28 cursor-pointer hover:-translate-y-1 transition-transform">
                <div className="relative">
                  <img src={mp.img} alt={mp.label} className="w-full h-20 object-cover" />
                  <span className="absolute top-1.5 left-1.5 bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                    15% Off
                  </span>
                </div>
                <div className="p-2">
                  <p className="text-xs font-semibold text-gray-900">{mp.label}</p>
                  <span className="text-xs font-bold text-red-500">{mp.price}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT */}
        <div className="relative z-10 flex justify-center items-center">
          <div className="relative w-full max-w-lg">

            {/* Shoppers pill */}
            <div className="absolute -top-4 right-6 flex items-center bg-white rounded-full px-3 py-1.5 shadow-lg z-20">
              {[1, 2, 3, 4].map((i) => (
                <img key={i} src={`https://i.pravatar.cc/40?img=${i}`} alt={`user${i}`}
                  className="w-7 h-7 rounded-full border-2 border-white object-cover -ml-1.5 first:ml-0" />
              ))}
              <span className="text-xs font-semibold ml-2 text-gray-800">10k+ Shoppers</span>
            </div>

            {/* Hero image slider */}
            <div className="relative overflow-hidden rounded-3xl shadow-2xl" style={{ height: "580px" }}>
              {HERO_SLIDES.map((slide, i) => (
                <img
                  key={slide.image}
                  src={slide.image}
                  alt={slide.label}
                  className="absolute inset-0 w-full h-full"
                  style={{
                    objectFit: "cover",
                    objectPosition: "top center",
                    opacity: i === slideIndex ? slideOpacity : 0,
                    transition: "opacity 0.5s ease",
                  }}
                />
              ))}
              <div
                className="absolute bottom-0 left-0 right-0 h-32 z-10"
                style={{ background: "linear-gradient(to top, rgba(0,0,0,0.55), transparent)" }}
              />
              <div className="absolute bottom-5 left-5 right-5 flex items-center justify-between z-20">
                <span className="text-white font-bold text-base tracking-wide drop-shadow">
                  {HERO_SLIDES[slideIndex].label}
                </span>
                <div className="flex gap-2">
                  {HERO_SLIDES.map((_, i) => (
                    <button key={i} onClick={() => goToSlide(i)}
                      style={{
                        height: "8px",
                        background: i === slideIndex ? "#F5C518" : "rgba(255,255,255,0.5)",
                        width: i === slideIndex ? "24px" : "8px",
                        borderRadius: i === slideIndex ? "4px" : "50%",
                        border: "none",
                        cursor: "pointer",
                        transition: "all 0.3s",
                        padding: 0,
                      }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Floating sneaker card */}
            <div className="absolute top-1/4 -left-14 bg-white rounded-2xl shadow-xl p-3 z-20">
              <img
                src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=120&q=80"
                alt="sneaker"
                className="w-16 h-16 object-contain"
              />
              <p className="text-xs font-bold text-gray-900 mt-1">Sneaker</p>
              <span className="text-xs font-bold text-red-500">₹2,999</span>
            </div>

            {/* Floating review card */}
            <div className="absolute bottom-8 -right-12 bg-white rounded-2xl shadow-xl px-4 py-3 z-20">
              <p className="text-sm font-bold text-gray-900">10k+ Reviews</p>
              <p className="text-yellow-400 text-sm mt-0.5">★★★★★</p>
              <p className="text-xs text-gray-400">(5.0)</p>
            </div>
          </div>
        </div>
      </section>

      <RecommendedProducts />

      {/* ── COLLECTION ── (layout unchanged, only buttons wired up) */}
      <section className="px-10 py-20 bg-gray-50" id="collection">
        <div className="text-center mb-10">
          <h2 className="font-display text-4xl font-black text-gray-900">Our Collection</h2>
          <p className="text-gray-500 mt-3 text-base">Discover the latest trends in fashion</p>
        </div>

        {/* Category pills — unchanged */}
        <div className="flex flex-wrap justify-center gap-3 mb-10">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-6 py-2.5 rounded-full border-2 text-sm font-semibold transition-all
                ${activeCategory === cat
                  ? "bg-yellow-400 border-yellow-400 text-gray-900 shadow-md"
                  : "bg-white border-gray-200 text-gray-700 hover:border-gray-900"
                }`}
            >
              {cat}
              <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full
                ${activeCategory === cat ? "bg-yellow-500 text-white" : "bg-gray-100 text-gray-500"}`}>
                {countFor(cat)}
              </span>
            </button>
          ))}
        </div>

        {/* Product grid — only buttons wired, layout unchanged */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {filtered.length === 0 ? (
            <div className="col-span-4 text-center py-16 text-gray-400 text-base">
              😕 No products found in <strong>{activeCategory}</strong>. Try a different category.
            </div>
          ) : (
            filtered.map((product) => (
              <div
                key={product.id}
                className="product-card bg-white rounded-2xl shadow-sm overflow-hidden hover:-translate-y-2 hover:shadow-xl transition-all duration-300 cursor-pointer"
              >
                <div
                  className="relative overflow-hidden bg-gray-50 flex items-center justify-center"
                  style={{ height: "260px", padding: "0" }}
                >
                  <img
                    src={imgSrc(product)}
                    alt={product.name}
                    loading="eager"
                    decoding="sync"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "contain",
                      objectPosition: "center",
                      display: "block",
                      padding: "10px",
                    }}
                    onError={(e) => {
  e.target.onerror = null;
  e.target.src = getFallbackImage(product.category);
}}
//                     onError={(e) => {
//                       e.target.onerror = null;
//                       e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=90";
//                     }}
                  />
                  <span className="absolute top-2 left-2 bg-red-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                    {getDiscount(product.id)}% off
                  </span>

                  {/* ── Wishlist button — now wired to API ── */}
                  <button
                    onClick={(e) => handleWishlist(e, product.id)}
                    className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md text-sm hover:scale-110 transition-transform"
                  >
                    {wishlistIds.has(product.id) ? "❤️" : "🤍"}
                  </button>
                </div>

                <div className="p-4">
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">{product.brand}</p>
                  <h3 className="font-bold text-gray-900 mt-1 text-sm leading-snug">{product.name}</h3>
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-red-500 font-extrabold text-base">₹{product.price}</span>
                    <span className="text-xs text-gray-400">
                      <span className="text-yellow-400">★</span> {product.rating}
                    </span>
                  </div>

                  {/* ── Add to Cart button — now wired to API ── */}
                  <button
                    onClick={(e) => handleAddToCart(e, product.id, product.price)}
                    className={`mt-3 w-full py-2 rounded-full text-xs font-semibold transition-colors ${
                      addedCart[product.id]
                        ? "bg-green-500 text-white"
                        : "bg-gray-900 text-white hover:bg-yellow-400 hover:text-gray-900"
                    }`}
                  >
                    {addedCart[product.id] ? "✓ Added!" : "Add to Cart"}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

    </div>
  );
}