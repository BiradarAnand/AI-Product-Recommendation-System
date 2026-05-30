// src/components/ProductQuickView.jsx
// Global quick-view drawer/modal — import once in App.jsx, use everywhere.
//
// Usage:
//   import { useQuickView, QuickViewModal } from "../components/ProductQuickView";
//
//   // In any product card:
//   const { openQuickView } = useQuickView();
//   <div onClick={() => openQuickView(product)}>...</div>
//
//   // In App.jsx (once, at root):
//   <QuickViewModal />

import { useState, useEffect, useCallback, createContext, useContext, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { recordView } from "./RecentlyViewed";

const BASE = "https://ai-product-recommendation-system-by60.onrender.com";
const API  = axios.create({ baseURL: BASE });

// ── Context ────────────────────────────────────────────────────────────────
const QuickViewContext = createContext(null);

export function QuickViewProvider({ children }) {
  const [product,   setProduct]   = useState(null);
  const [isOpen,    setIsOpen]    = useState(false);

  const openQuickView  = useCallback((p) => { setProduct(p); setIsOpen(true);  }, []);
  const closeQuickView = useCallback(()  => { setIsOpen(false); setTimeout(() => setProduct(null), 350); }, []);

  return (
    <QuickViewContext.Provider value={{ product, isOpen, openQuickView, closeQuickView }}>
      {children}
      <QuickViewModal />
    </QuickViewContext.Provider>
  );
}

export function useQuickView() {
  const ctx = useContext(QuickViewContext);
  if (!ctx) throw new Error("useQuickView must be used inside <QuickViewProvider>");
  return ctx;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function imgSrc(url) {
  if (!url) return "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=80";
  if (url.startsWith("http")) return url;
  return `${BASE}/${url}`;
}

function getDiscount(id) {
  return 10 + (id * 7 + id * 3) % 26;
}

function StarRow({ rating }) {
  const r = Math.min(5, Math.max(0, Number(rating) || 0));
  return (
    <span style={{ color: "#F5C518", fontSize: "16px", letterSpacing: "2px" }}>
      {[1,2,3,4,5].map(i => (
        <span key={i} style={{ opacity: i <= Math.round(r) ? 1 : 0.25 }}>★</span>
      ))}
    </span>
  );
}

// ── Main Modal ─────────────────────────────────────────────────────────────
function QuickViewModal() {
  const { product, isOpen, closeQuickView } = useContext(QuickViewContext);
  const navigate  = useNavigate();

  const token      = localStorage.getItem("token");
  const isLoggedIn = !!token;
  const headers    = isLoggedIn ? { Authorization: `Bearer ${token}` } : {};

  const [quantity,    setQuantity]    = useState(1);
  const [wishlisted,  setWishlisted]  = useState(false);
  const [cartAdded,   setCartAdded]   = useState(false);
  const [cartLoading, setCartLoading] = useState(false);
  const [wishLoading, setWishLoading] = useState(false);
  const [imageZoom,   setImageZoom]   = useState(false);
  const [toast,       setToast]       = useState("");
  const [imgLoaded,   setImgLoaded]   = useState(false);

  const overlayRef = useRef(null);

  // Reset state whenever a new product opens
  useEffect(() => {
    if (product) {
      recordView(product);
      setQuantity(1);
      setCartAdded(false);
      setImgLoaded(false);
      setImageZoom(false);
      setToast("");
      // Check wishlist state
      if (isLoggedIn) {
        API.get("/api/wishlist", { headers })
          .then(res => {
            const ids = new Set((res.data.items || []).map(i => i.product_id));
            setWishlisted(ids.has(Number(product.id)));
          })
          .catch(() => {});
      } else {
        setWishlisted(false);
      }
    }
  }, [product]);

  // Lock body scroll
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  // Escape key
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") closeQuickView(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closeQuickView]);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(""), 2500);
  };

  const handleAddToCart = async () => {
    if (!isLoggedIn) { closeQuickView(); navigate("/login"); return; }
    if (cartAdded) { navigate("/cart"); return; }
    setCartLoading(true);
    try {
      await API.post("/api/cart", { product_id: Number(product.id), quantity }, { headers });
      setCartAdded(true);
      showToast(`✓ ${quantity} item${quantity > 1 ? "s" : ""} added to cart`);
      setTimeout(() => setCartAdded(false), 4000);
    } catch {
      showToast("⚠ Couldn't add to cart");
    } finally {
      setCartLoading(false);
    }
  };

  const handleWishlist = async () => {
    if (!isLoggedIn) { closeQuickView(); navigate("/login"); return; }
    setWishLoading(true);
    try {
      if (wishlisted) {
        await API.delete(`/api/wishlist/${product.id}`, { headers });
        setWishlisted(false);
        showToast("Removed from wishlist");
      } else {
        await API.post("/api/wishlist", { product_id: Number(product.id) }, { headers });
        setWishlisted(true);
        showToast("❤️ Saved to wishlist");
      }
    } catch {
      showToast("⚠ Wishlist update failed");
    } finally {
      setWishLoading(false);
    }
  };

  if (!product) return null;

  const discount      = getDiscount(product.id);
  const originalPrice = Math.round((product.price * 100) / (100 - discount));
  const savings       = originalPrice - Number(product.price);
  const maxQty        = product.stock > 0 ? Math.min(product.stock, 10) : 10;

  const FONT_DISPLAY = "'Playfair Display', serif";
  const FONT_BODY    = "'DM Sans', sans-serif";

  return (
    <>
      {/* ── Inject fonts if needed ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap');

        .qv-overlay {
          position: fixed; inset: 0; z-index: 9999;
          background: rgba(0,0,0,0.55);
          display: flex; align-items: flex-end; justify-content: center;
          animation: qv-fade-in 0.2s ease;
        }
        @media (min-width: 640px) {
          .qv-overlay { align-items: center; }
        }
        .qv-overlay.closing { animation: qv-fade-out 0.3s ease forwards; }

        .qv-panel {
          background: #fff;
          width: 100%; max-width: 860px;
          border-radius: 24px 24px 0 0;
          max-height: 92vh;
          overflow-y: auto;
          animation: qv-slide-up 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
          position: relative;
        }
        @media (min-width: 640px) {
          .qv-panel {
            border-radius: 24px;
            max-height: 88vh;
          }
        }

        @keyframes qv-fade-in  { from { opacity: 0; } to { opacity: 1; } }
        @keyframes qv-fade-out { from { opacity: 1; } to { opacity: 0; } }
        @keyframes qv-slide-up { from { transform: translateY(40px); opacity: 0; } to { transform: none; opacity: 1; } }

        .qv-img-wrap {
          overflow: hidden; background: #f8f8f6;
          border-radius: 16px;
          cursor: zoom-in;
          position: relative;
        }
        .qv-img-wrap img {
          width: 100%; height: 100%;
          object-fit: contain; padding: 20px;
          transition: transform 0.4s ease;
        }
        .qv-img-wrap:hover img { transform: scale(1.07); }
        .qv-img-wrap.zoomed { cursor: zoom-out; }
        .qv-img-wrap.zoomed img { transform: scale(1.5); }

        .qv-qty-btn {
          width: 36px; height: 36px; border-radius: 50%;
          background: #f3f3f0; border: none; cursor: pointer;
          font-size: 18px; font-weight: 700; color: #111;
          display: flex; align-items: center; justify-content: center;
          transition: background 0.15s;
        }
        .qv-qty-btn:hover:not(:disabled) { background: #e5e5e2; }
        .qv-qty-btn:disabled { opacity: 0.3; cursor: not-allowed; }

        .qv-cart-btn {
          flex: 1; padding: 14px 20px;
          border-radius: 50px; border: none; cursor: pointer;
          font-size: 14px; font-weight: 700; letter-spacing: 0.3px;
          transition: all 0.2s ease;
        }
        .qv-cart-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
        .qv-cart-btn:active { transform: translateY(0); }
        .qv-cart-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .qv-wish-btn {
          width: 52px; height: 52px; border-radius: 50%;
          border: 2px solid #e5e5e2; background: #fff;
          cursor: pointer; font-size: 20px;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.2s;
        }
        .qv-wish-btn:hover { border-color: #F5C518; transform: scale(1.1); }
        .qv-wish-btn.active { border-color: #ef4444; background: #fff1f2; }

        .qv-toast {
          position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%);
          background: #111; color: #fff;
          padding: 10px 20px; border-radius: 50px;
          font-size: 13px; font-weight: 600;
          white-space: nowrap;
          animation: qv-fade-in 0.2s ease;
          z-index: 10;
        }

        .qv-badge {
          display: inline-flex; align-items: center; gap: 4px;
          padding: 4px 10px; border-radius: 50px;
          font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
        }

        .qv-detail-row {
          display: flex; justify-content: space-between;
          padding: 8px 0; border-bottom: 1px solid #f3f3f0;
          font-size: 13px;
        }
        .qv-detail-row:last-child { border-bottom: none; }

        .qv-spin {
          width: 16px; height: 16px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          display: inline-block;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      {/* ── Overlay ── */}
      {isOpen && (
        <div
          ref={overlayRef}
          className="qv-overlay"
          onClick={(e) => { if (e.target === overlayRef.current) closeQuickView(); }}
        >
          <div className="qv-panel" style={{ fontFamily: FONT_BODY }}>

            {/* ── Close button ── */}
            <button
              onClick={closeQuickView}
              style={{
                position: "sticky", top: 12, left: "calc(100% - 52px)",
                float: "right", marginRight: 16, marginTop: 12,
                width: 36, height: 36, borderRadius: "50%",
                background: "#f3f3f0", border: "none", cursor: "pointer",
                fontSize: 18, fontWeight: 700, color: "#555",
                display: "flex", alignItems: "center", justifyContent: "center",
                zIndex: 5, transition: "background 0.15s",
              }}
              aria-label="Close"
            >
              ✕
            </button>

            <div className="p-4 sm:p-7" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 28 }}>
              <style>{`@media(min-width:640px){.qv-grid{grid-template-columns:1fr 1fr !important;}}`}</style>
              <div className="qv-grid" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 28 }}>

                {/* ── LEFT: Image ── */}
                <div>
                  <div
                    className={`qv-img-wrap ${imageZoom ? "zoomed" : ""}`}
                    style={{ height: "clamp(240px, 40vh, 340px)" }}
                    onClick={() => setImageZoom(z => !z)}
                  >
                    {!imgLoaded && (
                      <div style={{
                        position: "absolute", inset: 0,
                        background: "linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%)",
                        animation: "pulse 1.5s ease-in-out infinite",
                      }} />
                    )}
                    <img
                      src={imgSrc(product.image_url)}
                      alt={product.name}
                      onLoad={() => setImgLoaded(true)}
                      onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=80"; setImgLoaded(true); }}
                      style={{ opacity: imgLoaded ? 1 : 0, transition: "opacity 0.3s" }}
                    />

                    {/* Discount badge */}
                    <div style={{
                      position: "absolute", top: 12, left: 12,
                      background: "#ef4444", color: "#fff",
                      padding: "4px 10px", borderRadius: 50,
                      fontSize: 11, fontWeight: 800, letterSpacing: "0.5px",
                    }}>
                      {discount}% OFF
                    </div>

                    {/* Zoom hint */}
                    <div style={{
                      position: "absolute", bottom: 10, right: 10,
                      background: "rgba(0,0,0,0.45)", color: "#fff",
                      padding: "3px 8px", borderRadius: 6,
                      fontSize: 10, fontWeight: 600,
                    }}>
                      {imageZoom ? "Click to zoom out" : "Click to zoom"}
                    </div>
                  </div>

                  {/* Thumbnail strip placeholder — can be wired to multiple images */}
                  <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                    {[product.image_url].map((url, i) => (
                      <div key={i} style={{
                        width: 52, height: 52, borderRadius: 10,
                        border: "2px solid #F5C518",
                        overflow: "hidden", background: "#f8f8f6",
                        cursor: "pointer",
                      }}>
                        <img
                          src={imgSrc(url)}
                          alt=""
                          style={{ width: "100%", height: "100%", objectFit: "contain", padding: 4 }}
                          onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=80"; }}
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* ── RIGHT: Details ── */}
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                  {/* Brand + Name */}
                  <div>
                    <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.15em", color: "#888", textTransform: "uppercase", margin: "0 0 6px" }}>
                      {product.brand}
                    </p>
                    <h2 style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 900, color: "#111", lineHeight: 1.25, margin: 0 }}>
                      {product.name}
                    </h2>
                  </div>

                  {/* Rating */}
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <StarRow rating={product.rating} />
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#444" }}>{Number(product.rating || 0).toFixed(1)}</span>
                    <span style={{ fontSize: 13, color: "#999" }}>({product.reviews || 0} reviews)</span>
                  </div>

                  {/* Price */}
                  <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 30, fontWeight: 900, color: "#ef4444", lineHeight: 1 }}>
                      ₹{Number(product.price).toLocaleString("en-IN")}
                    </span>
                    <span style={{ fontSize: 16, color: "#bbb", textDecoration: "line-through" }}>
                      ₹{originalPrice.toLocaleString("en-IN")}
                    </span>
                    <span className="qv-badge" style={{ background: "#f0fdf4", color: "#166534", fontSize: 11 }}>
                      Save ₹{savings.toLocaleString("en-IN")}
                    </span>
                  </div>

                  {/* Status badges */}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <span className="qv-badge" style={{ background: "#f3f3f0", color: "#555" }}>
                      {product.category}
                    </span>
                    {product.stock > 0 ? (
                      <span className="qv-badge" style={{ background: "#f0fdf4", color: "#166534" }}>
                        ✓ In Stock {product.stock && `(${product.stock} left)`}
                      </span>
                    ) : (
                      <span className="qv-badge" style={{ background: "#fff1f2", color: "#be123c" }}>
                        Out of Stock
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  {product.description && (
                    <p style={{
                      fontSize: 13, color: "#666", lineHeight: 1.7, margin: 0,
                      borderLeft: "3px solid #F5C518", paddingLeft: 12,
                    }}>
                      {product.description}
                    </p>
                  )}

                  {/* Details table */}
                  <div style={{ background: "#fafaf8", borderRadius: 12, padding: "12px 16px" }}>
                    {[
                      ["Brand",    product.brand    || "—"],
                      ["Category", product.category || "—"],
                      ["Rating",   `${Number(product.rating || 0).toFixed(1)} / 5`],
                      ["Stock",    product.stock > 0 ? `${product.stock} units` : "Out of stock"],
                    ].map(([k, v]) => (
                      <div key={k} className="qv-detail-row">
                        <span style={{ color: "#999", fontWeight: 500 }}>{k}</span>
                        <span style={{ color: "#333", fontWeight: 600 }}>{v}</span>
                      </div>
                    ))}
                  </div>

                  {/* Quantity picker */}
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#444" }}>Quantity:</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, background: "#f8f8f6", borderRadius: 50, padding: "4px 12px" }}>
                      <button className="qv-qty-btn" onClick={() => setQuantity(q => Math.max(1, q - 1))} disabled={quantity <= 1}>−</button>
                      <span style={{ fontWeight: 800, fontSize: 15, minWidth: 24, textAlign: "center" }}>{quantity}</span>
                      <button className="qv-qty-btn" onClick={() => setQuantity(q => Math.min(maxQty, q + 1))} disabled={quantity >= maxQty}>+</button>
                    </div>
                    <span style={{ fontSize: 12, color: "#bbb" }}>max {maxQty}</span>
                  </div>

                  {/* CTA buttons */}
                  <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                    <button
                      className="qv-cart-btn"
                      onClick={handleAddToCart}
                      disabled={cartLoading || product.stock === 0}
                      style={{
                        background: cartAdded ? "#22c55e" : "#111",
                        color: "#fff",
                      }}
                    >
                      {cartLoading
                        ? <span className="qv-spin" />
                        : cartAdded
                          ? "✓ Added — Go to Cart →"
                          : product.stock === 0
                            ? "Out of Stock"
                            : "Add to Cart"}
                    </button>

                    <button
                      className={`qv-wish-btn ${wishlisted ? "active" : ""}`}
                      onClick={handleWishlist}
                      disabled={wishLoading}
                      title={wishlisted ? "Remove from wishlist" : "Save to wishlist"}
                    >
                      {wishLoading ? "…" : wishlisted ? "❤️" : "🤍"}
                    </button>
                  </div>

                  {/* View full page link */}
                  <a
                    href={`/product/${product.id}`}
                    onClick={(e) => { e.preventDefault(); closeQuickView(); navigate(`/product/${product.id}`); }}
                    style={{
                      display: "inline-flex", alignItems: "center", gap: 6,
                      fontSize: 13, fontWeight: 600, color: "#888",
                      textDecoration: "none", borderBottom: "1px solid #e5e5e2",
                      paddingBottom: 2, width: "fit-content",
                      transition: "color 0.15s",
                    }}
                    onMouseEnter={e => e.currentTarget.style.color = "#111"}
                    onMouseLeave={e => e.currentTarget.style.color = "#888"}
                  >
                    View full product page →
                  </a>
                </div>
              </div>
            </div>

            {/* ── Toast ── */}
            {toast && <div className="qv-toast">{toast}</div>}
          </div>
        </div>
      )}
    </>
  );
}