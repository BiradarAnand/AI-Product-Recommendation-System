import React, { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import RecommendedProducts from "../components/RecommendedProducts";
import { useQuickView } from "../components/ProductQuickView";
import { recordView } from "../components/RecentlyViewed";
import FlashDeals from "../components/FlashDeals";
import TrendingTicker from "../components/TrendingTicker";
import StyleQuiz from "../components/StyleQuiz";
import RecentlyViewed from "../components/RecentlyViewed";
import BrandShowcase from "../components/BrandShowcase";

// ── Constants ──────────────────────────────────────────────────────────────

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

// ── Nav section modes ──────────────────────────────────────────────────────
// "home" | "best-seller" | "new-releases" | "most-reviewed" | "sale"
const NAV_SECTIONS = [
  { key: "home",         label: "Home" },
  { key: "best-seller",  label: "Best Seller" },
  { key: "new-releases", label: "New Releases" },
  { key: "most-reviewed",label: "Most Reviewed" },
  { key: "sale",         label: "🔥 Sale" },
];

// ── Helpers ───────────────────────────────────────────────────────────────

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

// ── Section Page Component ─────────────────────────────────────────────────
// Renders a dedicated full-section grid for Best Seller / New Releases / Most Reviewed / Sale

function SectionPage({
  sectionKey, products, openQuickView,
  wishlistIds, addedCart,
  handleAddToCart, handleWishlist,
}) {
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 16;

  // Sort / label logic per section
  const { title, subtitle, badge, sorted } = React.useMemo(() => {
    const copy = [...products];
    switch (sectionKey) {
      case "best-seller":
        return {
          title:    "Best Sellers",
          subtitle: "Our highest-rated, most-loved products",
          badge:    (p) => ({ text: "⭐ Best Seller", bg: "#fef9c3", color: "#92400e" }),
          sorted:   copy.sort((a, b) => (b.rating || 0) - (a.rating || 0)),
        };
      case "new-releases":
        return {
          title:    "New Releases",
          subtitle: "Fresh drops — just landed in our catalogue",
          badge:    (p) => ({ text: "✨ New", bg: "#eff6ff", color: "#1e40af" }),
          sorted:   copy.sort((a, b) => b.id - a.id), // highest id = newest
        };
      case "most-reviewed":
        return {
          title:    "Most Reviewed",
          subtitle: "Products with the most customer reviews & feedback",
          badge:    (p) => ({ text: `★ ${Number(p.rating || 0).toFixed(1)}`, bg: "#f0fdf4", color: "#166534" }),
          sorted:   copy.sort((a, b) => (b.reviews || b.rating || 0) - (a.reviews || a.rating || 0)),
        };
      case "sale":
        return {
          title:    "🔥 Sale",
          subtitle: "Biggest discounts right now — limited time only",
          badge:    (p) => {
            const d = getDiscount(p.id);
            return { text: `${d}% OFF`, bg: "#fef2f2", color: "#b91c1c" };
          },
          sorted:   copy.sort((a, b) => getDiscount(b.id) - getDiscount(a.id)),
        };
      default:
        return { title: "", subtitle: "", badge: () => null, sorted: copy };
    }
  }, [sectionKey, products]);

  const visible = sorted.slice(0, page * PAGE_SIZE);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Section hero banner */}
      <div
        className="px-4 md:px-10 py-10 md:py-14 text-center"
        style={{
          background: sectionKey === "sale"
            ? "linear-gradient(135deg,#111 0%,#1f1f1f 100%)"
            : "linear-gradient(135deg,#fff 0%,#f9f7f2 100%)",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <h1
          className="font-display text-3xl md:text-5xl font-black mb-3"
          style={{ color: sectionKey === "sale" ? "#F5C518" : "#111" }}
        >
          {title}
        </h1>
        <p style={{ color: sectionKey === "sale" ? "#ccc" : "#888", fontSize: 16 }}>{subtitle}</p>
        <p style={{ color: sectionKey === "sale" ? "#888" : "#bbb", fontSize: 13, marginTop: 8 }}>
          {sorted.length} products
        </p>
      </div>

      {/* Grid */}
      <section className="px-4 md:px-10 py-8 md:py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-[1400px] mx-auto">
          {visible.map((product, idx) => {
            const badgeInfo = badge(product);
            const discount  = getDiscount(product.id);
            const origPrice = Math.round(product.price * 100 / (100 - discount));

            return (
              <div
                key={product.id}
                className="product-card bg-white rounded-2xl shadow-sm overflow-hidden hover:-translate-y-2 hover:shadow-xl transition-all duration-300 cursor-pointer"
                onClick={() => { openQuickView(product); recordView(product); }}
              >
                <div className="relative overflow-hidden bg-gray-50 flex items-center justify-center" style={{ height: 260 }}>
                  <img
                    src={imgSrc(product)}
                    alt={product.name}
                    loading="lazy"
                    style={{ width: "100%", height: "100%", objectFit: "contain", padding: 10 }}
                    onError={(e) => { e.target.onerror = null; e.target.src = getFallbackImage(product.category); }}
                  />

                  {/* Rank badge for best seller / most reviewed */}
                  {(sectionKey === "best-seller" || sectionKey === "most-reviewed") && idx < 3 && (
                    <div className="absolute top-2 left-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-black shadow-md"
                      style={{ background: ["#F5C518","#C0C0C0","#CD7F32"][idx], color: "#111" }}>
                      #{idx + 1}
                    </div>
                  )}

                  {/* Section-specific badge */}
                  {badgeInfo && (
                    <span
                      className="absolute top-2 right-2 text-xs font-bold px-2.5 py-1 rounded-full"
                      style={{ background: badgeInfo.bg, color: badgeInfo.color }}
                    >
                      {badgeInfo.text}
                    </span>
                  )}

                  {/* Sale: show discount % on left too */}
                  {sectionKey === "sale" && (
                    <span className="absolute top-2 left-2 bg-red-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                      {discount}% off
                    </span>
                  )}

                  {/* Wishlist */}
                  <button
                    onClick={(e) => handleWishlist(e, product.id)}
                    className="absolute bottom-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md text-sm hover:scale-110 transition-transform"
                  >
                    {wishlistIds.has(product.id) ? "❤️" : "🤍"}
                  </button>
                </div>

                <div className="p-4">
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">{product.brand}</p>
                  <h3 className="font-bold text-gray-900 mt-1 text-sm leading-snug line-clamp-2">{product.name}</h3>

                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-yellow-400 text-xs">★</span>
                    <span className="text-xs text-gray-500">{Number(product.rating || 0).toFixed(1)}</span>
                    {product.reviews > 0 && (
                      <span className="text-xs text-gray-400">({product.reviews?.toLocaleString()} reviews)</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-red-500 font-extrabold text-base">₹{product.price}</span>
                    {sectionKey === "sale" && (
                      <span className="text-gray-400 text-xs line-through">₹{origPrice}</span>
                    )}
                  </div>

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
            );
          })}
        </div>

        {/* Load more */}
        {sorted.length > page * PAGE_SIZE && (
          <div className="mt-10 text-center max-w-[1400px] mx-auto">
            <p className="text-sm text-gray-400 mb-4">
              Showing {visible.length} of {sorted.length} products
            </p>
            <button
              onClick={() => setPage(p => p + 1)}
              className="px-10 py-3.5 bg-gray-900 text-white font-semibold rounded-full hover:bg-yellow-400 hover:text-gray-900 transition-all hover:-translate-y-0.5"
            >
              Load More ↓
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

// ── Main Home Component ────────────────────────────────────────────────────

export default function Home() {
  const [products, setProducts]             = useState([]);
  const [search, setSearch]                 = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [slideIndex, setSlideIndex]         = useState(0);
  const [slideOpacity, setSlideOpacity]     = useState(1);
  const [activeSection, setActiveSection]   = useState("home");
  const intervalRef                         = useRef(null);
  const navigate                            = useNavigate();
  const { openQuickView }                   = useQuickView();

  const token                               = localStorage.getItem("token");
  const isLoggedIn                          = !!token;
  const user                                = JSON.parse(localStorage.getItem("user") || "null");
  const [cartCount, setCartCount]           = useState(0);
  const [wishlistCount, setWishlistCount]   = useState(0);
  const [wishlistIds, setWishlistIds]       = useState(new Set());
  const [addedCart, setAddedCart]           = useState({});
  const [activeBrand, setActiveBrand]       = useState(null);
  const [page, setPage]                     = useState(1);
  const PAGE_SIZE = 16;
  const [showHistory, setShowHistory]       = useState(false);
  const [searchHistory, setSearchHistory]   = useState([]);
  const searchRef                           = useRef(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // ── Inject fonts ──
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

  // ── Load cart + wishlist ──
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

  // ── Close history dropdown on outside click ──
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

  // ── Filtering (home page collection) ──
  const filtered = products.filter((p) => {
    const matchSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.brand?.toLowerCase().includes(search.toLowerCase());
    const dbCat = (p.category || "").trim().toLowerCase();
    const matchBrand = !activeBrand || (p.brand || "").toLowerCase() === activeBrand.toLowerCase();
    const matchCat =
      activeCategory === "All" ||
      (CATEGORY_MAP[activeCategory] || []).includes(dbCat);
    return matchSearch && matchCat && matchBrand;
  });

  const countFor = (cat) => {
    if (cat === "All") return products.length;
    return products.filter((p) =>
      (CATEGORY_MAP[cat] || []).includes((p.category || "").trim().toLowerCase())
    ).length;
  };

  // ── ML search ──
  const handleMLSearch = async () => {
    if (!search.trim()) return;
    setShowHistory(false);
    setActiveSection("home"); // go to home section to show results
    try {
      const res = await API.get("/api/recommend/search", {
        params: { q: search, top_n: 50 },
        headers: isLoggedIn ? { Authorization: `Bearer ${token}` } : {},
      });
      setProducts(res.data.results || []);
      if (isLoggedIn) {
        const h = await API.get("/api/search-history?limit=10", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSearchHistory(h.data.queries || []);
      }
    } catch {}
  };

  // ── Add to cart ──
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

  // ── Wishlist ──
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

  // ── Logout ──
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.reload();
  };

  // ── Render ──
  return (
    <div className="bg-gray-50 min-h-screen">

      {/* ── NAVBAR ── */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm shadow-sm">
        <div className="flex items-center justify-between px-4 md:px-10 py-4">
          <a href="/" className="font-display text-xl md:text-2xl font-black tracking-tight text-gray-900"
            onClick={(e) => { e.preventDefault(); setActiveSection("home"); setMobileMenuOpen(false); }}>
            RecoVibe<span className="text-yellow-400">.</span>
          </a>

          {/* Desktop nav links */}
          <ul className="hidden lg:flex items-center gap-7 text-sm font-medium text-gray-800 list-none">
            <li>
              <button onClick={() => setActiveSection("home")}
                className={`transition-colors font-semibold pb-0.5 ${
                  activeSection === "home" ? "border-b-2 border-yellow-400 text-gray-900" : "text-gray-600 hover:text-yellow-500"
                }`}>Home</button>
            </li>
            <li>
              <button onClick={() => setActiveSection("best-seller")}
                className={`transition-colors font-semibold pb-0.5 flex items-center gap-1 ${
                  activeSection === "best-seller" ? "border-b-2 border-yellow-400 text-gray-900" : "text-gray-600 hover:text-yellow-500"
                }`}>
                Best Seller
                {activeSection !== "best-seller" && (
                  <span className="text-[10px] bg-yellow-400 text-gray-900 font-black px-1.5 py-0.5 rounded-full">HOT</span>
                )}
              </button>
            </li>
            <li>
              <button onClick={() => { setActiveSection("home"); setTimeout(() => { const chatBtn = document.querySelector('[aria-label="Toggle chat"]'); if (chatBtn) chatBtn.click(); }, 100); }}
                className="text-gray-600 hover:text-yellow-500 transition-colors font-semibold">
                Shop by Occasion
              </button>
            </li>
            <li>
              <button onClick={() => setActiveSection("new-releases")}
                className={`transition-colors font-semibold pb-0.5 flex items-center gap-1 ${
                  activeSection === "new-releases" ? "border-b-2 border-yellow-400 text-gray-900" : "text-gray-600 hover:text-yellow-500"
                }`}>
                New Releases
                {activeSection !== "new-releases" && (
                  <span className="text-[10px] bg-blue-100 text-blue-700 font-black px-1.5 py-0.5 rounded-full">NEW</span>
                )}
              </button>
            </li>
            <li>
              <button onClick={() => setActiveSection("most-reviewed")}
                className={`transition-colors font-semibold pb-0.5 ${
                  activeSection === "most-reviewed" ? "border-b-2 border-yellow-400 text-gray-900" : "text-gray-600 hover:text-yellow-500"
                }`}>Most Reviewed</button>
            </li>
            <li>
              <button onClick={() => setActiveSection("sale")}
                className={`transition-colors font-bold pb-0.5 ${
                  activeSection === "sale" ? "border-b-2 border-red-500 text-red-500" : "text-red-500 hover:text-red-600"
                }`}>🔥 Sale</button>
            </li>
            {user?.role === "admin" && (
              <li><Link to="/admin" className="text-red-500 font-bold hover:text-red-600">Admin</Link></li>
            )}
          </ul>

          {/* NAVBAR RIGHT */}
          <div className="flex items-center gap-2 md:gap-4">
            {/* Search — hidden on small, shown on md+ */}
            <div ref={searchRef} className="relative hidden md:block">
              <div className="flex items-center border-2 border-gray-200 rounded-full overflow-hidden focus-within:border-yellow-400 transition-colors bg-white">
                <input
                  type="text"
                  placeholder="Search products..."
                  className="px-4 py-2 text-sm outline-none w-36 lg:w-52 bg-transparent"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onFocus={() => isLoggedIn && searchHistory.length > 0 && setShowHistory(true)}
                  onKeyDown={(e) => e.key === "Enter" && handleMLSearch()}
                />
                <button onClick={handleMLSearch} className="px-3 py-2 bg-gray-900 text-white text-sm hover:bg-yellow-400 hover:text-gray-900 transition-colors">🔍</button>
              </div>
              {showHistory && searchHistory.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                  <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent Searches</span>
                  </div>
                  {searchHistory.map((q, i) => (
                    <button key={i} onClick={() => { setSearch(q); setShowHistory(false); handleMLSearch(); }}
                      className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 border-b border-gray-50 last:border-b-0">
                      <span className="text-gray-400 text-xs">🕐</span>{q}
                    </button>
                  ))}
                  <button onClick={async () => { await API.delete("/api/search-history", { headers: { Authorization: `Bearer ${token}` } }); setSearchHistory([]); setShowHistory(false); }}
                    className="w-full text-left px-4 py-2 text-xs text-gray-400 hover:text-gray-600 bg-gray-50 border-t border-gray-100">
                    Clear history
                  </button>
                </div>
              )}
            </div>

            {/* Cart */}
            <Link to="/cart" className="relative flex items-center gap-1 text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline">
              🛒
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {cartCount > 9 ? "9+" : cartCount}
                </span>
              )}
              <span className="ml-1 hidden sm:inline">Cart</span>
            </Link>

            {/* Wishlist */}
            <Link to="/wishlist" className="relative flex items-center gap-1 text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline">
              ❤️
              {wishlistCount > 0 && (
                <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {wishlistCount > 9 ? "9+" : wishlistCount}
                </span>
              )}
              <span className="ml-1 hidden sm:inline">Wishlist</span>
            </Link>

            {/* Login / Avatar */}
            {isLoggedIn ? (
              <Link to="/profile" title={user?.name || user?.email || "My Profile"} style={{ textDecoration: "none" }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "50%",
                  background: "linear-gradient(135deg, #F5C518 0%, #e6b800 100%)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontWeight: 900, fontSize: 15, color: "#111",
                  boxShadow: "0 2px 10px rgba(245,197,24,0.4)",
                  cursor: "pointer", flexShrink: 0,
                  transition: "transform 0.15s, box-shadow 0.15s",
                  fontFamily: "'Playfair Display', serif",
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.1)"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(245,197,24,0.5)"; }}
                onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 2px 10px rgba(245,197,24,0.4)"; }}
                >
                  {(user?.name || user?.email || "?")[0].toUpperCase()}
                </div>
              </Link>
            ) : (
              <Link to="/login" className="text-sm font-semibold text-gray-900 hover:text-yellow-500 transition-colors no-underline hidden sm:block">
                Login
              </Link>
            )}

            {/* Hamburger — mobile only */}
            <button
              className="lg:hidden flex flex-col justify-center items-center w-9 h-9 rounded-lg hover:bg-gray-100 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <span className={`block w-5 h-0.5 bg-gray-900 transition-all duration-200 ${mobileMenuOpen ? "rotate-45 translate-y-1.5" : ""}`} />
              <span className={`block w-5 h-0.5 bg-gray-900 my-1 transition-all duration-200 ${mobileMenuOpen ? "opacity-0" : ""}`} />
              <span className={`block w-5 h-0.5 bg-gray-900 transition-all duration-200 ${mobileMenuOpen ? "-rotate-45 -translate-y-1.5" : ""}`} />
            </button>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-white border-t border-gray-100 px-4 pb-4 space-y-1">
            {/* Mobile search */}
            <div className="flex items-center border-2 border-gray-200 rounded-full overflow-hidden focus-within:border-yellow-400 mb-3 mt-2">
              <input
                type="text"
                placeholder="Search products..."
                className="px-4 py-2 text-sm outline-none flex-1 bg-transparent"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { handleMLSearch(); setMobileMenuOpen(false); } }}
              />
              <button onClick={() => { handleMLSearch(); setMobileMenuOpen(false); }} className="px-4 py-2 bg-gray-900 text-white text-sm">🔍</button>
            </div>
            {[
              { key: "home", label: "Home" },
              { key: "best-seller", label: "🏆 Best Seller" },
              { key: "new-releases", label: "✨ New Releases" },
              { key: "most-reviewed", label: "💬 Most Reviewed" },
              { key: "sale", label: "🔥 Sale" },
            ].map(({ key, label }) => (
              <button key={key}
                onClick={() => { setActiveSection(key); setMobileMenuOpen(false); }}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                  activeSection === key ? "bg-yellow-400 text-gray-900" : "text-gray-700 hover:bg-gray-50"
                }`}>{label}</button>
            ))}
            <button
              onClick={() => { setActiveSection("home"); setMobileMenuOpen(false); setTimeout(() => { const chatBtn = document.querySelector('[aria-label="Toggle chat"]'); if (chatBtn) chatBtn.click(); }, 100); }}
              className="w-full text-left px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50">
              🛍️ Shop by Occasion
            </button>
            {!isLoggedIn && (
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 no-underline">
                👤 Login / Register
              </Link>
            )}
            {user?.role === "admin" && (
              <Link to="/admin" onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2.5 rounded-xl text-sm font-bold text-red-500 hover:bg-red-50 no-underline">
                ⚙️ Admin
              </Link>
            )}
          </div>
        )}
      </nav>

      {/* ── SECTION PAGES (Best Seller / New Releases / Most Reviewed / Sale) ── */}
      {activeSection !== "home" && products.length > 0 && (
        <>
          {/* Back to home breadcrumb */}
          <div className="px-4 md:px-10 py-3 bg-white border-b border-gray-100 flex items-center gap-2 text-sm">
            <button
              onClick={() => setActiveSection("home")}
              className="text-gray-400 hover:text-gray-900 transition-colors flex items-center gap-1"
            >
              ← Back to Home
            </button>
            <span className="text-gray-200">/</span>
            <span className="font-semibold text-gray-900 capitalize">
              {NAV_SECTIONS.find(s => s.key === activeSection)?.label}
            </span>
          </div>

          <SectionPage
            sectionKey={activeSection}
            products={products}
            openQuickView={openQuickView}
            wishlistIds={wishlistIds}
            addedCart={addedCart}
            handleAddToCart={handleAddToCart}
            handleWishlist={handleWishlist}
          />
        </>
      )}

      {/* ── HOME PAGE CONTENT ── */}
      {activeSection === "home" && (
        <>

          {/* ── HERO ── */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-16 items-center px-4 md:px-10 lg:px-20 py-10 md:py-16 max-w-[1400px] mx-auto [&>*]:min-w-0">

            {/* LEFT */}
            <div className="relative z-10 order-2 md:order-1">
              <span className="inline-block bg-yellow-400 text-gray-900 text-xs font-bold uppercase tracking-widest px-4 py-1.5 rounded-full mb-4 md:mb-6">
                ✨ New Season 2026
              </span>
              <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-black leading-tight text-gray-900">
                Daily Fabulous <br />
                <span className="underline-yellow">Style for You.</span>
              </h1>
              <p className="text-gray-500 mt-4 md:mt-5 text-base md:text-lg leading-relaxed max-w-md">
                Ready to dress to impress with our fabulous style collection.
                Curated looks for every mood and occasion.
              </p>
              <div className="flex flex-wrap gap-3 md:gap-4 mt-6 md:mt-8">
                <button
                  onClick={() => setActiveSection("best-seller")}
                  className="flex items-center gap-2 bg-gray-900 text-white px-6 md:px-7 py-3 md:py-3.5 rounded-full font-semibold hover:bg-gray-700 transition-all hover:-translate-y-0.5">
                  Shop Now →
                </button>
                <button
                  onClick={() => setActiveSection("sale")}
                  className="px-6 md:px-7 py-3 md:py-3.5 rounded-full border-2 border-gray-300 font-semibold hover:border-red-400 hover:text-red-500 transition-all hover:-translate-y-0.5">
                  🔥 View Sale
                </button>
              </div>
              <div className="flex gap-6 md:gap-10 mt-7 md:mt-10">
                {[
                  { num: "5k+", label: "Happy Customers" },
                  { num: "10K+", label: "Products" },
                  { num: "4.9★", label: "Avg. Rating" },
                ].map((s) => (
                  <div key={s.label}>
                    <div className="font-display text-xl md:text-2xl font-black text-gray-900">{s.num}</div>
                    <div className="text-xs text-gray-500 mt-1">{s.label}</div>
                  </div>
                ))}
              </div>
              <div className="flex gap-3 md:gap-4 mt-7 md:mt-10">
                {MINI_PRODUCTS.map((mp) => (
                  <div key={mp.label} className="bg-white rounded-2xl shadow-md overflow-hidden w-24 md:w-28 cursor-pointer hover:-translate-y-1 transition-transform">
                    <div className="relative">
                      <img src={mp.img} alt={mp.label} className="w-full h-16 md:h-20 object-cover" />
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
            <div className="relative z-10 flex justify-center items-center order-1 md:order-2">
              <div className="relative w-full max-w-lg">

                {/* Shoppers pill */}
                <div className="absolute -top-4 right-2 md:right-6 flex items-center bg-white rounded-full px-3 py-1.5 shadow-lg z-20">
                  {[1, 2, 3, 4].map((i) => (
                    <img key={i} src={`https://i.pravatar.cc/40?img=${i}`} alt={`user${i}`}
                      className="w-6 h-6 md:w-7 md:h-7 rounded-full border-2 border-white object-cover -ml-1.5 first:ml-0" />
                  ))}
                  <span className="text-xs font-semibold ml-2 text-gray-800">10k+ Shoppers</span>
                </div>

                {/* Hero image slider */}
                <div className="relative overflow-hidden rounded-2xl md:rounded-3xl shadow-2xl" style={{ height: "clamp(280px, 50vw, 580px)" }}>
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
                  <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between z-20">
                    <span className="text-white font-bold text-sm md:text-base tracking-wide drop-shadow">
                      {HERO_SLIDES[slideIndex].label}
                    </span>
                    <div className="flex gap-1.5 md:gap-2">
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

                {/* Floating sneaker card — hidden on small screens to prevent overflow */}
                <div className="hidden md:block absolute top-1/4 -left-14 bg-white rounded-2xl shadow-xl p-3 z-20">
                  <img
                    src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=120&q=80"
                    alt="sneaker"
                    className="w-16 h-16 object-contain"
                  />
                  <p className="text-xs font-bold text-gray-900 mt-1">Sneaker</p>
                  <span className="text-xs font-bold text-red-500">₹2,999</span>
                </div>

                {/* Floating review card — hidden on small screens to prevent overflow */}
                <div className="hidden md:block absolute bottom-8 -right-12 bg-white rounded-2xl shadow-xl px-4 py-3 z-20">
                  <p className="text-sm font-bold text-gray-900">10k+ Reviews</p>
                  <p className="text-yellow-400 text-sm mt-0.5">★★★★★</p>
                  <p className="text-xs text-gray-400">(5.0)</p>
                </div>
              </div>
            </div>
          </section>

          {/* ── QUICK NAVIGATION CARDS (replaces dead nav clicks with visual CTAs) ── */}
          <section className="px-4 md:px-10 py-8 md:py-10 bg-white">
            <div className="max-w-[1400px] mx-auto grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
              {[
                { key: "best-seller",   icon: "🏆", label: "Best Sellers",   sub: "Highest rated picks",    bg: "#fffbeb", border: "#F5C518"  },
                { key: "new-releases",  icon: "✨", label: "New Releases",   sub: "Just arrived",           bg: "#eff6ff", border: "#93c5fd"  },
                { key: "most-reviewed", icon: "💬", label: "Most Reviewed",  sub: "Customer favourites",    bg: "#f0fdf4", border: "#86efac"  },
                { key: "sale",          icon: "🔥", label: "Sale",           sub: "Up to 36% off",          bg: "#fff1f2", border: "#fca5a5"  },
              ].map((card) => (
                <button
                  key={card.key}
                  onClick={() => setActiveSection(card.key)}
                  className="flex items-center gap-4 p-4 rounded-2xl border-2 text-left hover:-translate-y-1 hover:shadow-md transition-all"
                  style={{ background: card.bg, borderColor: card.border }}
                >
                  <span className="text-3xl">{card.icon}</span>
                  <div>
                    <p className="font-bold text-gray-900 text-sm">{card.label}</p>
                    <p className="text-xs text-gray-500">{card.sub}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* ── TRENDING TICKER ── */}
          <TrendingTicker />

          {/* ── RECOMMENDED PRODUCTS ── */}
          <RecommendedProducts />

          {/* ── FLASH DEALS ── */}
          <FlashDeals onProductClick={(p) => { openQuickView(p); recordView(p); }} />

          {/* ── RECENTLY VIEWED ── */}
          <RecentlyViewed onProductClick={(p) => { openQuickView(p); recordView(p); }} />

          {/* ── BRAND SHOWCASE ── */}
          <BrandShowcase onBrandSelect={(b) => { setActiveBrand(b); setPage(1); }} />

          {/* ── COLLECTION ── */}
          <section className="px-4 md:px-10 py-10 md:py-20 bg-gray-50" id="collection">
            <div className="text-center mb-8 md:mb-10">
              <h2 className="font-display text-3xl md:text-4xl font-black text-gray-900">Our Collection</h2>
              <p className="text-gray-500 mt-3 text-base">Discover the latest trends in fashion</p>
            </div>

            {/* Category pills */}
            <div className="flex flex-wrap justify-center gap-3 mb-10">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => { setActiveCategory(cat); setPage(1); }}
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

            {/* Product grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {filtered.length === 0 ? (
                <div className="col-span-4 text-center py-16 text-gray-400 text-base">
                  😕 No products found in <strong>{activeCategory}</strong>.
                </div>
              ) : (
                filtered.slice(0, page * PAGE_SIZE).map((product) => (
                  <div
                    key={product.id}
                    className="product-card bg-white rounded-2xl shadow-sm overflow-hidden hover:-translate-y-2 hover:shadow-xl transition-all duration-300 cursor-pointer"
                    onClick={() => { openQuickView(product); recordView(product); }}
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
                      />
                      <span className="absolute top-2 left-2 bg-red-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                        {getDiscount(product.id)}% off
                      </span>
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

            {/* Load More */}
            {filtered.length > page * PAGE_SIZE && (
              <div className="mt-10 text-center">
                <p className="text-sm text-gray-400 mb-4">
                  Showing {Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} products
                </p>
                <button
                  onClick={() => setPage(p => p + 1)}
                  className="px-10 py-3.5 bg-gray-900 text-white font-semibold rounded-full hover:bg-yellow-400 hover:text-gray-900 transition-all hover:-translate-y-0.5"
                >
                  Load More Products ↓
                </button>
              </div>
            )}
            {filtered.length > 0 && filtered.length <= page * PAGE_SIZE && page > 1 && (
              <p className="mt-8 text-center text-sm text-gray-400">
                ✓ All {filtered.length} products loaded
              </p>
            )}
          </section>

          {/* ── STYLE QUIZ ── */}
          <StyleQuiz onProductClick={(p) => { openQuickView(p); recordView(p); }} />

        </>
      )}
    </div>
  );
}