import React, { useEffect, useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useQuickView } from "../components/ProductQuickView";
import { recordView } from "../components/RecentlyViewed";

const API = axios.create({ baseURL: "http://localhost:5000" });

const primarySrc = (p) => {
  if (!p.image_url) return null;
  if (p.image_url.includes("unsplash.com")) {
    return p.image_url.replace(/w=\d+/, "w=800").replace(/q=\d+/, "q=90");
  }
  if (p.image_url.startsWith("http")) return p.image_url;
  return `http://localhost:5000/${p.image_url}`;
};

const proxySrc = (p) =>
  `http://localhost:5000/proxy-image?url=${encodeURIComponent(p.image_url)}`;

function StrictProductImage({ product, alt, className = "", style = {}, eager = false }) {
  const [step, setStep] = useState(0);       
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  
  const isAmazon = (product.image_url || "").includes("media-amazon.com");

  const src = step === 0 ? primarySrc(product) : (step === 1 && isAmazon ? proxySrc(product) : null);

  const handleError = () => {
    if (step === 0 && isAmazon) {
        setStep(1);
    } else {
        setFailed(true);
    }
  };

  if (!src || failed) {
      return (
          <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-300 text-xs text-center p-4">
              Image Unavailable
          </div>
      );
  }

  return (
    <div className="relative w-full h-full bg-white flex items-center justify-center">
      {!loaded && !failed && (
        <div className="absolute inset-0 animate-pulse bg-gray-100" />
      )}
      <img
        src={src}
        alt={alt}
        loading={eager ? "eager" : "lazy"}
        referrerPolicy="no-referrer"
        onError={handleError}
        onLoad={() => setLoaded(true)}
        className={className}
        style={{ ...style, opacity: loaded ? 1 : 0, transition: "opacity 0.25s ease" }}
      />
    </div>
  );
}

export default function Fashion() {
  const [products, setProducts] = useState([]);
  const [activeCategory, setActiveCategory] = useState("All");
  
  const navigate = useNavigate();
  const { openQuickView } = useQuickView();

  const token = localStorage.getItem("token");
  const isLoggedIn = !!token;
  const user = JSON.parse(localStorage.getItem("user") || "null");
  
  const [cartCount, setCartCount] = useState(0);
  const [addedCart, setAddedCart] = useState({});
  const [wishlistIds, setWishlistIds] = useState(new Set());
  
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 16;

  useEffect(() => {
    API.get("/products")
      .then((res) => {
        // Filter strictly for Fashion or products with tech keywords
        const Fashion = res.data.filter(p => {
           const cat = (p.category || "").toLowerCase();
           return cat === "Fashion" || cat === "smartphones" || cat === "audio";
        });
        setProducts(Fashion.reverse()); // Newest first
      })
      .catch(() => setProducts([]));
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    const headers = { Authorization: `Bearer ${token}` };
    API.get("/api/cart", { headers }).then((res) => setCartCount(res.data.count || 0)).catch(() => {});
    API.get("/api/wishlist", { headers }).then((res) => {
        const ids = new Set((res.data.items || []).map((i) => i.product_id));
        setWishlistIds(ids);
    }).catch(() => {});
  }, [isLoggedIn]);

  // Derived subcategories using keywords since DB categorizes everything as "Fashion"
  const getSubcategory = (p) => {
      const name = (p.name || "").toLowerCase();
      const cat = (p.category || "").toLowerCase();
      if (cat.includes("shirt") || name.includes("shirt")) return "Shirts";
      if (cat.includes("jean") || name.includes("jean") || cat.includes("trouser") || name.includes("trouser") || cat.includes("pant") || name.includes("pant")) return "Bottoms";
      if (cat.includes("shoe") || name.includes("shoe") || name.includes("sneaker")) return "Footwear";
      if (cat.includes("hoodie") || name.includes("hoodie") || cat.includes("jacket") || name.includes("jacket")) return "Outerwear";
      if (cat.includes("watch") || name.includes("watch")) return "Watches";
      return "Other";
  };

  const filtered = useMemo(() => {
      if (activeCategory === "All") return products;
      return products.filter(p => getSubcategory(p) === activeCategory);
  }, [products, activeCategory]);

  const visible = filtered.slice(0, page * PAGE_SIZE);

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

  const handleWishlist = async (e, productId) => {
    e.stopPropagation();
    if (!isLoggedIn) { navigate("/login"); return; }
    try {
      if (wishlistIds.has(productId)) {
        await API.delete(`/api/wishlist/${productId}`, { headers: { Authorization: `Bearer ${token}` } });
        setWishlistIds((prev) => { const s = new Set(prev); s.delete(productId); return s; });
      } else {
        await API.post("/api/wishlist", { product_id: productId }, { headers: { Authorization: `Bearer ${token}` } });
        setWishlistIds((prev) => new Set([...prev, productId]));
      }
    } catch (err) {
      console.error("Wishlist failed:", err);
    }
  };

  const subcats = ["All", "Shirts", "Bottoms", "Footwear", "Outerwear", "Watches", "Other"];

  return (
    <div className="bg-[#0f0f0f] min-h-screen font-sans text-white">
      {/* ── NAVBAR ── */}
      <nav className="sticky top-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 md:px-10 py-4">
          <Link to="/" className="font-display text-xl md:text-2xl font-black tracking-tight text-white">
            RecoVibe<span className="text-[#00d4ff]">.</span>
          </Link>

          <ul className="hidden lg:flex items-center gap-7 text-sm font-medium text-gray-300 list-none">
            <li><Link to="/" className="hover:text-[#00d4ff] transition-colors">Fashion</Link></li>
            <li><span className="text-[#00d4ff] font-bold border-b-2 border-[#00d4ff] pb-1">Fashion</span></li>
          </ul>

          <div className="flex items-center gap-4">
            <Link to="/cart" className="relative text-lg text-white hover:text-[#00d4ff] transition-colors no-underline">
              🛒
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-[#00d4ff] text-black text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full shadow-sm">
                  {cartCount}
                </span>
              )}
            </Link>
            {isLoggedIn ? (
              <Link to="/profile" className="w-9 h-9 rounded-full bg-gray-800 flex items-center justify-center text-sm font-bold text-[#00d4ff] border border-gray-700 hover:border-[#00d4ff] transition-colors">
                {user?.name?.charAt(0).toUpperCase() || "U"}
              </Link>
            ) : (
              <Link to="/login" className="px-5 py-2 bg-[#00d4ff] text-black text-sm font-bold rounded-full hover:bg-white transition-all shadow-md">
                Log In
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* ── HERO HEADER ── */}
      <div className="px-4 md:px-10 py-12 md:py-16 text-center border-b border-gray-800" style={{ background: "linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%)" }}>
        <h1 className="font-display text-4xl md:text-6xl font-black mb-4 text-white">
          RecoVibe <span className="text-[#00d4ff]">Tech</span>
        </h1>
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto">
          The latest gadgets and Fashion, curated for you.
        </p>
        
        {/* Category Navigation */}
        <div className="flex flex-wrap justify-center gap-3 mt-10">
            {subcats.map(cat => (
                <button
                    key={cat}
                    onClick={() => { setActiveCategory(cat); setPage(1); }}
                    className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                        activeCategory === cat 
                        ? "bg-[#00d4ff] text-black shadow-lg" 
                        : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                    }`}
                >
                    {cat}
                </button>
            ))}
        </div>
      </div>

      {/* ── PRODUCTS GRID ── */}
      <div className="px-4 md:px-10 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-[1400px] mx-auto">
            {visible.map((product) => {
                return (
                    <div 
                        key={product.id}
                        className="bg-[#141414] border border-gray-800 rounded-2xl overflow-hidden hover:border-[#00d4ff] hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
                        onClick={() => { openQuickView(product); recordView(product); }}
                    >
                        <div className="relative h-56 bg-white overflow-hidden p-4">
                            <StrictProductImage 
                                product={product} 
                                alt={product.name}
                                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-500"
                            />
                            <button
                                onClick={(e) => handleWishlist(e, product.id)}
                                className="absolute top-3 right-3 w-8 h-8 bg-black/10 backdrop-blur-md rounded-full flex items-center justify-center text-sm hover:scale-110 transition-transform"
                            >
                                {wishlistIds.has(product.id) ? "❤️" : "🤍"}
                            </button>
                        </div>
                        <div className="p-5">
                            <p className="text-xs text-[#00d4ff] uppercase tracking-wider font-bold mb-1">
                                {product.brand || "Tech"}
                            </p>
                            <h3 className="font-semibold text-gray-200 text-sm leading-snug line-clamp-2 min-h-[40px]">
                                {product.name}
                            </h3>
                            <div className="flex items-center gap-2 mt-3">
                                <span className="text-yellow-400 text-xs">★</span>
                                <span className="text-xs text-gray-400">{Number(product.rating || 0).toFixed(1)}</span>
                                {product.reviews > 0 && (
                                    <span className="text-xs text-gray-500">({product.reviews?.toLocaleString()})</span>
                                )}
                            </div>
                            <div className="mt-4 flex items-center justify-between">
                                <span className="text-white font-bold text-lg">₹{product.price?.toLocaleString()}</span>
                                <button
                                    onClick={(e) => handleAddToCart(e, product.id, product.price)}
                                    className={`px-4 py-2 rounded-lg text-xs font-bold transition-colors ${
                                        addedCart[product.id]
                                        ? "bg-green-500 text-white"
                                        : "bg-[#00d4ff]/10 text-[#00d4ff] hover:bg-[#00d4ff] hover:text-black"
                                    }`}
                                >
                                    {addedCart[product.id] ? "Added" : "+ Add"}
                                </button>
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>

        {visible.length === 0 && (
            <div className="text-center py-20">
                <p className="text-gray-500 text-lg">No products found in this category.</p>
            </div>
        )}

        {filtered.length > page * PAGE_SIZE && (
          <div className="mt-12 text-center max-w-[1400px] mx-auto">
            <button
              onClick={() => setPage(p => p + 1)}
              className="px-10 py-3.5 bg-gray-800 text-white font-semibold rounded-full hover:bg-gray-700 transition-all border border-gray-700"
            >
              Load More
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
