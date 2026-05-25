// src/components/BrandShowcase.jsx
// Animated brand grid — clicking a brand filters the collection.
// Drop into Home.jsx: <BrandShowcase onBrandSelect={(brand) => setActiveBrand(brand)} />

import { useState } from "react";

const BRANDS = [
  { name: "Nike",    emoji: "✔",  color: "#111",    bg: "#f8f8f8", products: 12, categories: ["Sports Shoes", "Tshirts", "Hoodies"] },
  { name: "Adidas",  emoji: "⬡",  color: "#000",    bg: "#f5f5f5", products: 9,  categories: ["Casual Shoes", "Track Pants", "Tshirts"] },
  { name: "Zara",    emoji: "Z",  color: "#222",    bg: "#faf9f6", products: 15, categories: ["Shirts", "Trousers", "Jeans"] },
  { name: "Levi's",  emoji: "L",  color: "#c1001f", bg: "#fff5f5", products: 7,  categories: ["Jeans"] },
  { name: "H&M",     emoji: "H", color: "#e50010", bg: "#fff5f5", products: 18, categories: ["Shirts", "Tshirts", "Hoodies", "Track Pants"] },
  { name: "Fossil",  emoji: "⌚", color: "#8b6914", bg: "#fdf8ee", products: 5,  categories: ["Watches"] },
  { name: "Titan",   emoji: "T",  color: "#1a237e", bg: "#f0f4ff", products: 4,  categories: ["Watches"] },
  { name: "Puma",    emoji: "⬤",  color: "#111",    bg: "#f8f8f8", products: 8,  categories: ["Sports Shoes", "Tshirts", "Track Pants"] },
  { name: "Mango",   emoji: "M",  color: "#b85c00", bg: "#fff8f0", products: 6,  categories: ["Shirts"] },
  { name: "Clarks",  emoji: "C",  color: "#555",    bg: "#f5f5f3", products: 4,  categories: ["Casual Shoes"] },
];

export default function BrandShowcase({ onBrandSelect }) {
  const [selected, setSelected] = useState(null);
  const [hovered,  setHovered]  = useState(null);

  const handleBrand = (brand) => {
    const next = selected?.name === brand.name ? null : brand;
    setSelected(next);
    onBrandSelect && onBrandSelect(next?.name || null);
  };

  return (
    <section style={{ padding: "56px 40px", background: "#fff", borderTop: "1px solid #f0f0ee" }}>
      <div style={{ maxWidth: 1400, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <span style={{
            display: "inline-block", background: "#f8f8f6",
            fontSize: 11, fontWeight: 700, letterSpacing: "0.15em",
            textTransform: "uppercase", color: "#999",
            padding: "5px 14px", borderRadius: 50, marginBottom: 12,
          }}>
            Top Brands
          </span>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 32, fontWeight: 900, color: "#111", margin: "0 0 6px" }}>
            Shop by Brand
          </h2>
          <p style={{ fontSize: 14, color: "#bbb", margin: 0 }}>
            {selected ? `Showing ${selected.products} products from ${selected.name}` : "Click a brand to filter the collection"}
          </p>
        </div>

        {/* Brand grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14, marginBottom: selected ? 28 : 0 }}>
          {BRANDS.map(brand => {
            const isSelected = selected?.name === brand.name;
            const isHovered  = hovered === brand.name;

            return (
              <div
                key={brand.name}
                onClick={() => handleBrand(brand)}
                onMouseEnter={() => setHovered(brand.name)}
                onMouseLeave={() => setHovered(null)}
                style={{
                  padding: "20px 16px",
                  borderRadius: 16,
                  border: `2px solid ${isSelected ? "#F5C518" : isHovered ? "#e0e0dc" : "#f0f0ee"}`,
                  background: isSelected ? "#fffbeb" : brand.bg,
                  cursor: "pointer",
                  textAlign: "center",
                  transition: "all 0.2s",
                  transform: isSelected ? "translateY(-3px)" : isHovered ? "translateY(-2px)" : "none",
                  boxShadow: isSelected ? "0 8px 24px rgba(245,197,24,0.2)" : isHovered ? "0 4px 12px rgba(0,0,0,0.06)" : "none",
                  position: "relative",
                }}
              >
                {isSelected && (
                  <div style={{
                    position: "absolute", top: -8, right: -8,
                    background: "#F5C518", color: "#111",
                    width: 20, height: 20, borderRadius: "50%",
                    fontSize: 11, fontWeight: 900,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    ✓
                  </div>
                )}

                {/* Brand initial / icon */}
                <div style={{
                  width: 48, height: 48, borderRadius: 12,
                  background: isSelected ? "#F5C518" : "#fff",
                  border: "1.5px solid #f0f0ee",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  margin: "0 auto 10px",
                  fontSize: 18, fontWeight: 900, color: isSelected ? "#111" : brand.color,
                  transition: "all 0.2s",
                }}>
                  {brand.emoji}
                </div>

                <p style={{ fontSize: 13, fontWeight: 800, color: "#111", margin: "0 0 3px" }}>{brand.name}</p>
                <p style={{ fontSize: 11, color: "#bbb", margin: 0 }}>{brand.products} items</p>

                {/* Categories on hover */}
                {(isHovered || isSelected) && (
                  <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4, justifyContent: "center" }}>
                    {brand.categories.slice(0, 2).map(c => (
                      <span key={c} style={{
                        fontSize: 9, background: "#f0f0ee", color: "#888",
                        padding: "2px 6px", borderRadius: 50, fontWeight: 600,
                      }}>{c}</span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Active brand info strip */}
        {selected && (
          <div style={{
            background: "#111", borderRadius: 16, padding: "16px 24px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            animation: "slide-in 0.3s ease",
          }}>
            <style>{`@keyframes slide-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }`}</style>
            <div>
              <p style={{ color: "#F5C518", fontSize: 12, fontWeight: 700, margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Filtering by brand
              </p>
              <p style={{ color: "#fff", fontSize: 16, fontWeight: 900, margin: 0 }}>
                {selected.name} · {selected.products} products
              </p>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <div style={{ display: "flex", gap: 6 }}>
                {selected.categories.map(c => (
                  <span key={c} style={{
                    fontSize: 11, background: "rgba(255,255,255,0.1)", color: "#ccc",
                    padding: "3px 10px", borderRadius: 50, fontWeight: 600,
                  }}>{c}</span>
                ))}
              </div>
              <button
                onClick={() => handleBrand(selected)}
                style={{
                  background: "rgba(255,255,255,0.1)", border: "none",
                  color: "#fff", borderRadius: 50, padding: "6px 16px",
                  fontSize: 12, fontWeight: 700, cursor: "pointer",
                  marginLeft: 8,
                }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.2)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
              >
                ✕ Clear
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}