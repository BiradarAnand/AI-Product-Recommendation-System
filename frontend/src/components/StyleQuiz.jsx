// src/components/StyleQuiz.jsx
// 3-step interactive style quiz → shows matched products from the API.
// Drop into Home.jsx: <StyleQuiz onProductClick={openQuickView} />

import { useState } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "https://ai-product-recommendation-system-by60.onrender.com" });

const STEPS = [
  {
    id: "occasion",
    question: "What's your main style need?",
    emoji: "👔",
    options: [
      { value: "office",    label: "Office & Work",      icon: "🏢" },
      { value: "casual",    label: "Casual & Weekend",   icon: "☀️" },
      { value: "sports",    label: "Sports & Fitness",   icon: "🏃" },
      { value: "occasion",  label: "Events & Parties",   icon: "🎊" },
    ],
  },
  {
    id: "budget",
    question: "What's your budget range?",
    emoji: "💰",
    options: [
      { value: "budget",    label: "Under ₹1,000",    icon: "🪙" },
      { value: "mid",       label: "₹1,000–₹3,000",   icon: "💳" },
      { value: "premium",   label: "₹3,000–₹8,000",   icon: "💎" },
      { value: "luxury",    label: "₹8,000+",          icon: "👑" },
    ],
  },
  {
    id: "vibe",
    question: "Pick your style vibe",
    emoji: "✨",
    options: [
      { value: "minimal",   label: "Clean & Minimal",    icon: "◻️" },
      { value: "bold",      label: "Bold & Trendy",      icon: "🔥" },
      { value: "classic",   label: "Timeless Classic",   icon: "🎩" },
      { value: "sporty",    label: "Sporty & Relaxed",   icon: "⚡" },
    ],
  },
];

const PRICE_MAP = { budget: [0, 1000], mid: [1000, 3000], premium: [3000, 8000], luxury: [8000, 99999] };

const CATEGORY_MAP = {
  office:   ["Shirts", "Trousers", "Watches", "Blazers"],
  casual:   ["Tshirts", "Jeans", "Casual Shoes", "Hoodies"],
  sports:   ["Sports Shoes", "Track Pants", "Tshirts"],
  occasion: ["Shirts", "Watches", "Casual Shoes", "Trousers"],
};

function ProgressBar({ step, total }) {
  return (
    <div style={{ display: "flex", gap: 6, marginBottom: 28 }}>
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} style={{
          flex: 1, height: 4, borderRadius: 50,
          background: i <= step ? "#F5C518" : "#f0f0ee",
          transition: "background 0.3s",
        }} />
      ))}
    </div>
  );
}

function ResultCard({ product, onProductClick }) {
  return (
    <div
      onClick={() => onProductClick && onProductClick(product)}
      style={{
        background: "#fff", border: "1.5px solid #f0f0ee",
        borderRadius: 16, overflow: "hidden",
        cursor: "pointer", transition: "transform 0.2s, box-shadow 0.2s",
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.08)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
    >
      <div style={{ height: 140, background: "#f8f8f6", overflow: "hidden" }}>
        <img
          src={product.image_url?.startsWith("http") ? product.image_url : `https://ai-product-recommendation-system-by60.onrender.com/${product.image_url}`}
          alt={product.name}
          style={{ width: "100%", height: "100%", objectFit: "contain", padding: 10 }}
          onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&q=80"; }}
        />
      </div>
      <div style={{ padding: "10px 12px 14px" }}>
        <p style={{ fontSize: 10, color: "#aaa", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", margin: "0 0 2px" }}>{product.brand}</p>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#111", margin: "0 0 6px", lineHeight: 1.3, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{product.name}</p>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 15, fontWeight: 900, color: "#ef4444" }}>₹{Number(product.price).toLocaleString("en-IN")}</span>
          <span style={{ fontSize: 11, color: "#F5C518", fontWeight: 700 }}>★ {Number(product.rating || 4.2).toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}

export default function StyleQuiz({ onProductClick }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers]         = useState({});
  const [results, setResults]         = useState(null);
  const [loading, setLoading]         = useState(false);
  const [started, setStarted]         = useState(false);

  const handleAnswer = async (stepId, value) => {
    const newAnswers = { ...answers, [stepId]: value };
    setAnswers(newAnswers);

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(s => s + 1);
    } else {
      // Final step — fetch results
      setLoading(true);
      try {
        const [minPrice, maxPrice] = PRICE_MAP[newAnswers.budget] || [0, 99999];
        const categories = CATEGORY_MAP[newAnswers.occasion] || [];

        const res = await API.get("/products");
        const all = res.data || [];

        const filtered = all.filter(p => {
          const price = Number(p.price);
          const cat   = (p.category || "").toLowerCase();
          const inBudget = price >= minPrice && price <= maxPrice;
          const inCat    = categories.some(c => c.toLowerCase() === cat);
          return inBudget && inCat;
        });

        // Sort by rating, take top 6
        const sorted = filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, 6);
        setResults(sorted.length > 0 ? sorted : all.sort((a,b) => (b.rating||0)-(a.rating||0)).slice(0,6));
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const reset = () => {
    setCurrentStep(0);
    setAnswers({});
    setResults(null);
    setLoading(false);
  };

  const step = STEPS[currentStep];

  return (
    <section className="px-4 md:px-10 py-12 md:py-16 bg-white">
      <div style={{ maxWidth: 720, margin: "0 auto" }}>

        {/* Entry state */}
        {!started && (
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✨</div>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: "clamp(24px, 5vw, 34px)", fontWeight: 900, color: "#111", margin: "0 0 10px" }}>
              Find Your Perfect Style
            </h2>
            <p style={{ fontSize: 15, color: "#888", margin: "0 0 32px", lineHeight: 1.7 }}>
              Answer 3 quick questions and we'll curate the perfect picks for you.
            </p>
            <button
              onClick={() => setStarted(true)}
              style={{
                background: "#111", color: "#fff",
                border: "none", borderRadius: 50,
                padding: "14px 40px", fontSize: 15, fontWeight: 700,
                cursor: "pointer", transition: "all 0.2s",
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "#F5C518"; e.currentTarget.style.color = "#111"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "#111"; e.currentTarget.style.color = "#fff"; }}
            >
              Start Style Quiz →
            </button>
          </div>
        )}

        {/* Quiz steps */}
        {started && !results && !loading && (
          <div>
            <ProgressBar step={currentStep} total={STEPS.length} />
            <div style={{ textAlign: "center", marginBottom: 32 }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>{step.emoji}</div>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 6px" }}>
                {step.question}
              </h2>
              <p style={{ fontSize: 13, color: "#bbb", margin: 0 }}>Step {currentStep + 1} of {STEPS.length}</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-[14px]">
              {step.options.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => handleAnswer(step.id, opt.value)}
                  style={{
                    background: "#fff", border: "2px solid #f0f0ee",
                    borderRadius: 16, padding: "18px 20px",
                    cursor: "pointer", textAlign: "left",
                    transition: "all 0.2s",
                    display: "flex", alignItems: "center", gap: 12,
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "#F5C518"; e.currentTarget.style.background = "#fffbeb"; e.currentTarget.style.transform = "scale(1.02)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "#f0f0ee"; e.currentTarget.style.background = "#fff"; e.currentTarget.style.transform = "none"; }}
                >
                  <span style={{ fontSize: 24 }}>{opt.icon}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>{opt.label}</span>
                </button>
              ))}
            </div>
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep(s => s - 1)}
                style={{ marginTop: 20, background: "none", border: "none", cursor: "pointer", fontSize: 13, color: "#aaa", fontWeight: 600 }}
              >
                ← Back
              </button>
            )}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", padding: "48px 0" }}>
            <div style={{ fontSize: 40, marginBottom: 16, animation: "spin-slow 2s linear infinite", display: "inline-block" }}>✨</div>
            <p style={{ fontSize: 16, fontWeight: 700, color: "#111" }}>Curating your perfect picks…</p>
            <style>{`@keyframes spin-slow { to { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {/* Results */}
        {results && (
          <div>
            <div style={{ textAlign: "center", marginBottom: 28 }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>🎯</div>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 6px" }}>
                Your Style Matches
              </h2>
              <p style={{ fontSize: 13, color: "#aaa", margin: "0 0 20px" }}>
                Based on your style: <strong style={{ color: "#111" }}>{answers.occasion}</strong> · <strong style={{ color: "#111" }}>{answers.budget}</strong> · <strong style={{ color: "#111" }}>{answers.vibe}</strong>
              </p>
            </div>

            {results.length === 0 ? (
              <p style={{ textAlign: "center", color: "#aaa" }}>No exact matches — try adjusting your budget or style.</p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-[14px] mb-6">
                {results.map(p => (
                  <ResultCard key={p.id} product={p} onProductClick={onProductClick} />
                ))}
              </div>
            )}

            <div style={{ textAlign: "center" }}>
              <button
                onClick={reset}
                style={{
                  background: "none", border: "2px solid #f0f0ee",
                  borderRadius: 50, padding: "10px 28px",
                  fontSize: 13, fontWeight: 700, color: "#555",
                  cursor: "pointer", transition: "border-color 0.15s",
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "#111"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "#f0f0ee"}
              >
                ↺ Retake Quiz
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}