// src/components/FlashDeals.jsx
// Countdown flash deals strip — shows limited-time offers with live timer.
// Drop into Home.jsx: <FlashDeals onProductClick={openQuickView} />

import { useState, useEffect, useRef } from "react";

const DEALS = [
  { id: 12, name: "Relaxed Fit Jeans",      brand: "Levi's", originalPrice: 3499, dealPrice: 2199, discount: 37, category: "Jeans",        image: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80", endsIn: 3600 * 2 + 1800 },
  { id: 14, name: "Minimalist Steel Watch", brand: "Fossil", originalPrice: 8999, dealPrice: 5999, discount: 33, category: "Watches",      image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80", endsIn: 3600 * 5 },
  { id: 16, name: "Classic Hoodie",         brand: "H&M",    originalPrice: 2499, dealPrice: 1799, discount: 28, category: "Hoodies",      image: "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400&q=80", endsIn: 3600 * 1 + 900 },
  { id: 1,  name: "Running Sneakers",       brand: "Nike",   originalPrice: 4299, dealPrice: 2999, discount: 30, category: "Sports Shoes", image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80", endsIn: 3600 * 8 },
  { id: 5,  name: "Oxford Button-Down",     brand: "Zara",   originalPrice: 2599, dealPrice: 1899, discount: 27, category: "Shirts",       image: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400&q=80", endsIn: 3600 * 3 + 600 },
];

function useCountdown(seconds) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    const t = setInterval(() => setLeft(s => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, []);
  const h = String(Math.floor(left / 3600)).padStart(2, "0");
  const m = String(Math.floor((left % 3600) / 60)).padStart(2, "0");
  const s = String(left % 60).padStart(2, "0");
  return { h, m, s, done: left === 0 };
}

function TimerBlock({ value, label }) {
  return (
    <div style={{ textAlign: "center", minWidth: 36 }}>
      <div style={{
        background: "#111", color: "#F5C518",
        fontFamily: "'DM Mono', monospace",
        fontSize: 18, fontWeight: 700,
        padding: "4px 8px", borderRadius: 6,
        letterSpacing: 1, lineHeight: 1,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 9, color: "#999", marginTop: 2, letterSpacing: "0.1em", textTransform: "uppercase" }}>{label}</div>
    </div>
  );
}

function DealCard({ deal, onProductClick }) {
  const { h, m, s, done } = useCountdown(deal.endsIn);
  const urgency = deal.endsIn < 3600;

  return (
    <div
      onClick={() => onProductClick && onProductClick({ id: deal.id, name: deal.name, brand: deal.brand, price: deal.dealPrice, category: deal.category, image_url: deal.image, rating: 4.5, stock: 20 })}
      style={{
        minWidth: 220, maxWidth: 220,
        background: "#fff",
        border: `2px solid ${urgency ? "#ef4444" : "#f3f3f0"}`,
        borderRadius: 20, overflow: "hidden",
        cursor: "pointer",
        transition: "transform 0.2s, box-shadow 0.2s",
        flexShrink: 0,
        position: "relative",
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.boxShadow = "0 12px 32px rgba(0,0,0,0.1)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
    >
      {/* Discount pill */}
      <div style={{
        position: "absolute", top: 10, left: 10, zIndex: 2,
        background: "#ef4444", color: "#fff",
        fontSize: 11, fontWeight: 800,
        padding: "3px 9px", borderRadius: 50,
        letterSpacing: "0.3px",
      }}>
        {deal.discount}% OFF
      </div>

      {/* Urgency indicator */}
      {urgency && (
        <div style={{
          position: "absolute", top: 10, right: 10, zIndex: 2,
          background: "#fff3cd", color: "#854d0e",
          fontSize: 10, fontWeight: 700,
          padding: "3px 8px", borderRadius: 50,
          animation: "pulse-badge 1s ease-in-out infinite",
        }}>
          🔥 Ending soon
        </div>
      )}

      {/* Image */}
      <div style={{ height: 160, background: "#f8f8f6", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
        <img
          src={deal.image} alt={deal.name}
          style={{ width: "100%", height: "100%", objectFit: "contain", padding: 12, transition: "transform 0.3s" }}
          onMouseEnter={e => e.currentTarget.style.transform = "scale(1.08)"}
          onMouseLeave={e => e.currentTarget.style.transform = "none"}
          onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&q=80"; }}
        />
      </div>

      <div style={{ padding: "12px 14px 16px" }}>
        <p style={{ fontSize: 10, color: "#999", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", margin: "0 0 3px" }}>{deal.brand}</p>
        <p style={{ fontSize: 13, fontWeight: 700, color: "#111", margin: "0 0 8px", lineHeight: 1.3, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{deal.name}</p>

        {/* Price */}
        <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 10 }}>
          <span style={{ fontSize: 18, fontWeight: 900, color: "#ef4444" }}>₹{deal.dealPrice.toLocaleString("en-IN")}</span>
          <span style={{ fontSize: 12, color: "#ccc", textDecoration: "line-through" }}>₹{deal.originalPrice.toLocaleString("en-IN")}</span>
        </div>

        {/* Countdown */}
        <div style={{ marginBottom: 10 }}>
          <p style={{ fontSize: 10, color: "#999", fontWeight: 600, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.1em" }}>Ends in</p>
          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
            <TimerBlock value={h} label="hr" />
            <span style={{ fontWeight: 900, color: "#ccc", fontSize: 14, marginBottom: 14 }}>:</span>
            <TimerBlock value={m} label="min" />
            <span style={{ fontWeight: 900, color: "#ccc", fontSize: 14, marginBottom: 14 }}>:</span>
            <TimerBlock value={s} label="sec" />
          </div>
        </div>

        {/* Progress bar — simulated stock */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 10, color: "#999" }}>Stock remaining</span>
            <span style={{ fontSize: 10, fontWeight: 700, color: urgency ? "#ef4444" : "#666" }}>{urgency ? "Almost gone!" : "Selling fast"}</span>
          </div>
          <div style={{ height: 4, background: "#f0f0f0", borderRadius: 50, overflow: "hidden" }}>
            <div style={{
              height: "100%",
              width: urgency ? "15%" : `${30 + (deal.id * 11) % 40}%`,
              background: urgency ? "#ef4444" : "#F5C518",
              borderRadius: 50,
              transition: "width 0.5s ease",
            }} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FlashDeals({ onProductClick }) {
  const scrollRef = useRef(null);

  const scroll = (dir) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir * 240, behavior: "smooth" });
    }
  };

  return (
    <section style={{ background: "#111", position: "relative", overflow: "hidden" }} className="px-4 md:px-10 py-10 md:py-12">
      <style>{`
        @keyframes pulse-badge { 0%,100%{opacity:1} 50%{opacity:0.6} }
        .fd-scroll::-webkit-scrollbar { display: none; }
        .fd-scroll { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      {/* Decorative yellow accent */}
      <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, borderRadius: "50%", background: "rgba(245,197,24,0.06)" }} />

      <div style={{ maxWidth: 1400, margin: "0 auto" }}>
        {/* Header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              background: "#F5C518", color: "#111",
              padding: "6px 14px", borderRadius: 50,
              fontSize: 12, fontWeight: 800, letterSpacing: "0.15em", textTransform: "uppercase",
            }}>
              ⚡ Flash Deals
            </div>
            <div>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 900, color: "#fff", margin: 0, lineHeight: 1 }}>
                Today's Best Offers
              </h2>
              <p style={{ fontSize: 12, color: "#888", margin: "4px 0 0" }}>Limited time · Limited stock</p>
            </div>
          </div>

          {/* Scroll controls */}
          <div style={{ display: "flex", gap: 8 }}>
            {["←", "→"].map((arrow, i) => (
              <button key={arrow} onClick={() => scroll(i === 0 ? -1 : 1)} style={{
                width: 38, height: 38, borderRadius: "50%",
                background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.15)",
                color: "#fff", fontSize: 16, cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s",
              }}
                onMouseEnter={e => e.currentTarget.style.background = "#F5C518"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
              >
                {arrow}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable cards */}
        <div
          ref={scrollRef}
          className="fd-scroll"
          style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 4 }}
        >
          {DEALS.map(deal => (
            <DealCard key={deal.id} deal={deal} onProductClick={onProductClick} />
          ))}
        </div>
      </div>
    </section>
  );
}