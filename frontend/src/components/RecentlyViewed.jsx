// src/components/RecentlyViewed.jsx
// Persists last 8 viewed products in localStorage. Automatically updated
// whenever ProductQuickView or ProductDetails is opened.
//
// To record a view from anywhere:
//   import { recordView } from "../components/RecentlyViewed";
//   recordView(product); // pass any product object
//
// Drop into Home.jsx: <RecentlyViewed onProductClick={openQuickView} />

import { useState, useEffect } from "react";

const STORAGE_KEY = "rv_recently_viewed";
const MAX_ITEMS   = 8;

// ── Public helper — call this whenever a product is opened ────────────────
export function recordView(product) {
  if (!product?.id) return;
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const filtered = stored.filter(p => p.id !== product.id);
    const slim = {
      id:        product.id,
      name:      product.name,
      brand:     product.brand,
      price:     product.price,
      rating:    product.rating,
      category:  product.category,
      image_url: product.image_url,
      stock:     product.stock,
    };
    const updated = [slim, ...filtered].slice(0, MAX_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {}
}

export function getRecentlyViewed() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

// ── Component ──────────────────────────────────────────────────────────────
export default function RecentlyViewed({ onProductClick }) {
  const [items, setItems] = useState([]);

  // Re-read from localStorage every time the component mounts / user navigates back
  useEffect(() => {
    setItems(getRecentlyViewed());
    // Poll for changes (e.g. when QuickView records a new view)
    const interval = setInterval(() => setItems(getRecentlyViewed()), 2000);
    return () => clearInterval(interval);
  }, []);

  if (items.length === 0) return null;

  const getDiscount = (id) => 10 + (id * 7 + id * 3) % 26;

  return (
    <section style={{ padding: "48px 40px 40px", background: "#fafaf8" }}>
      <style>{`
        .rv-scroll::-webkit-scrollbar { height: 4px; }
        .rv-scroll::-webkit-scrollbar-track { background: #f0f0ee; border-radius: 2px; }
        .rv-scroll::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
      `}</style>

      <div style={{ maxWidth: 1400, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 3px" }}>
              Recently Viewed
            </h2>
            <p style={{ fontSize: 13, color: "#aaa", margin: 0 }}>Pick up where you left off</p>
          </div>
          <button
            onClick={() => { localStorage.removeItem(STORAGE_KEY); setItems([]); }}
            style={{ background: "none", border: "none", fontSize: 12, color: "#ccc", cursor: "pointer", fontWeight: 600 }}
            onMouseEnter={e => e.currentTarget.style.color = "#999"}
            onMouseLeave={e => e.currentTarget.style.color = "#ccc"}
          >
            Clear history
          </button>
        </div>

        <div className="rv-scroll" style={{ display: "flex", gap: 14, overflowX: "auto", paddingBottom: 8 }}>
          {items.map((product) => {
            const discount = getDiscount(product.id);
            const imgSrc   = product.image_url?.startsWith("http")
              ? product.image_url
              : `https://ai-product-recommendation-system-by60.onrender.com/${product.image_url}`;

            return (
              <div
                key={product.id}
                onClick={() => onProductClick && onProductClick(product)}
                style={{
                  minWidth: 160, maxWidth: 160,
                  background: "#fff",
                  border: "1.5px solid #f0f0ee",
                  borderRadius: 16, overflow: "hidden",
                  cursor: "pointer",
                  flexShrink: 0,
                  transition: "transform 0.2s, box-shadow 0.2s, border-color 0.15s",
                  position: "relative",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "translateY(-3px)";
                  e.currentTarget.style.boxShadow = "0 8px 20px rgba(0,0,0,0.07)";
                  e.currentTarget.style.borderColor = "#F5C518";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.boxShadow = "none";
                  e.currentTarget.style.borderColor = "#f0f0ee";
                }}
              >
                {/* Viewed indicator */}
                <div style={{
                  position: "absolute", top: 8, right: 8, zIndex: 1,
                  background: "rgba(0,0,0,0.5)", color: "#fff",
                  fontSize: 9, fontWeight: 700, padding: "2px 6px",
                  borderRadius: 50, letterSpacing: "0.05em",
                }}>
                  👁 Viewed
                </div>

                <div style={{ height: 130, background: "#f8f8f6", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                  <img
                    src={imgSrc}
                    alt={product.name}
                    style={{ width: "100%", height: "100%", objectFit: "contain", padding: 10 }}
                    onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&q=80"; }}
                  />
                </div>

                <div style={{ padding: "10px 12px 12px" }}>
                  <p style={{ fontSize: 10, color: "#bbb", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 2px" }}>{product.brand}</p>
                  <p style={{ fontSize: 12, fontWeight: 700, color: "#111", margin: "0 0 6px", lineHeight: 1.3, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                    {product.name}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 14, fontWeight: 900, color: "#ef4444" }}>
                      ₹{Number(product.price).toLocaleString("en-IN")}
                    </span>
                    <span style={{
                      fontSize: 10, fontWeight: 700,
                      background: "#fff3cd", color: "#854d0e",
                      padding: "1px 6px", borderRadius: 50,
                    }}>
                      -{discount}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}