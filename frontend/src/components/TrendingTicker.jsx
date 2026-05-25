// src/components/TrendingTicker.jsx
// A live-feel horizontal marquee ticker showing trending searches + hot products.
// Drop anywhere in Home.jsx: <TrendingTicker />

import { useEffect, useRef, useState } from "react";

const TRENDING_ITEMS = [
  { type: "search", text: "White sneakers" },
  { type: "hot",    text: "Fossil watches — ₹5,999", badge: "🔥 HOT" },
  { type: "search", text: "Linen shirts for summer" },
  { type: "new",    text: "New: Tech Fleece Hoodie", badge: "✨ NEW" },
  { type: "search", text: "Slim fit chinos" },
  { type: "hot",    text: "Levi's jeans — 37% off", badge: "⚡ DEAL" },
  { type: "search", text: "Running shoes under ₹3000" },
  { type: "new",    text: "New: Graphic print tees", badge: "✨ NEW" },
  { type: "hot",    text: "Nike sneakers — trending", badge: "📈 TREND" },
  { type: "search", text: "Office formal shirts" },
  { type: "hot",    text: "Chronograph watches", badge: "🔥 HOT" },
  { type: "search", text: "Hoodies under ₹2000" },
];

const BADGE_COLORS = {
  "🔥 HOT":    { bg: "#fff3cd", color: "#854d0e" },
  "⚡ DEAL":   { bg: "#fef2f2", color: "#991b1b" },
  "✨ NEW":    { bg: "#f0fdf4", color: "#166534" },
  "📈 TREND":  { bg: "#eff6ff", color: "#1e40af" },
};

export default function TrendingTicker() {
  const [paused, setPaused] = useState(false);
  const items = [...TRENDING_ITEMS, ...TRENDING_ITEMS]; // duplicate for seamless loop

  return (
    <div
      style={{ background: "#F5C518", overflow: "hidden", position: "relative", borderTop: "2px solid #e6b800", borderBottom: "2px solid #e6b800" }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <style>{`
        @keyframes ticker-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .ticker-track {
          display: flex;
          width: max-content;
          animation: ticker-scroll 40s linear infinite;
        }
        .ticker-track.paused { animation-play-state: paused; }
      `}</style>

      <div style={{ display: "flex", alignItems: "center" }}>
        {/* Label pill */}
        <div style={{
          flexShrink: 0,
          background: "#111", color: "#F5C518",
          padding: "8px 16px",
          fontSize: 11, fontWeight: 800,
          letterSpacing: "0.15em", textTransform: "uppercase",
          zIndex: 2, whiteSpace: "nowrap",
        }}>
          🔍 Trending
        </div>

        {/* Scrolling track */}
        <div style={{ overflow: "hidden", flex: 1 }}>
          <div className={`ticker-track${paused ? " paused" : ""}`}>
            {items.map((item, i) => (
              <div
                key={i}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "8px 24px",
                  borderRight: "1px solid rgba(0,0,0,0.1)",
                  cursor: "pointer", whiteSpace: "nowrap",
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(0,0,0,0.06)"}
                onMouseLeave={e => e.currentTarget.style.background = "none"}
              >
                {item.badge && (
                  <span style={{
                    ...(BADGE_COLORS[item.badge] || {}),
                    fontSize: 10, fontWeight: 700,
                    padding: "2px 7px", borderRadius: 50,
                  }}>
                    {item.badge}
                  </span>
                )}
                {!item.badge && (
                  <span style={{ color: "rgba(0,0,0,0.4)", fontSize: 13 }}>🔍</span>
                )}
                <span style={{ fontSize: 13, fontWeight: 600, color: "#111" }}>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}