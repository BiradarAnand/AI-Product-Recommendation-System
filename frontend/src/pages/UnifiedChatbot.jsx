// UnifiedChatbot.jsx — Premium AI Stylist Chatbot
// Occasion-aware product recommendations with NLP + Groq-powered replies

import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const API = "https://ai-product-recommendation-system-by60.onrender.com";

// ── Occasions ──────────────────────────────────────────────────────────
const OCCASIONS = [
  { key: "job_interview",  label: "Job Interview",          icon: "💼", color: "#1e3a5f", light: "#dbeafe" },
  { key: "sports",         label: "Sports & Gym",           icon: "🏃", color: "#14532d", light: "#dcfce7" },
  { key: "wedding_guest",  label: "Wedding / Function",     icon: "🎊", color: "#581c87", light: "#f3e8ff" },
  { key: "casual_outing",  label: "Casual Outing",          icon: "☀️", color: "#78350f", light: "#fef3c7" },
  { key: "date_night",     label: "Date Night",             icon: "🌙", color: "#4c1d95", light: "#ede9fe" },
  { key: "office",         label: "Office & Work",          icon: "🏢", color: "#1e3a5f", light: "#e0f2fe" },
  { key: "festival",       label: "Festival & Traditional", icon: "🪔", color: "#7c2d12", light: "#fff7ed" },
  { key: "beach",          label: "Beach & Vacation",       icon: "🏖️", color: "#0c4a6e", light: "#e0f2fe" },
];

const QUICK_PROMPTS = [
  { text: "Job interview tomorrow", icon: "💼" },
  { text: "Going to the gym",       icon: "💪" },
  { text: "Cousin's wedding",       icon: "💒" },
  { text: "Date night dinner",      icon: "🌹" },
  { text: "Beach vacation",         icon: "🌊" },
  { text: "Office daily wear",      icon: "📋" },
  { text: "Diwali celebration",     icon: "🪔" },
  { text: "Jeans under ₹2000",      icon: "👖" },
];

const BUDGET_FILTERS = [
  { key: "",        label: "Any Budget" },
  { key: "budget",  label: "≤ ₹800" },
  { key: "mid",     label: "≤ ₹3,000" },
  { key: "premium", label: "≤ ₹8,000" },
  { key: "luxury",  label: "Luxury" },
];

const SLOT_ORDER = ["shirt", "pant", "shoes", "watch"];
const SLOT_META  = {
  shirt: { label: "Top",      icon: "👕", bg: "#fef9c3" },
  pant:  { label: "Bottom",   icon: "👖", bg: "#dbeafe" },
  shoes: { label: "Footwear", icon: "👟", bg: "#dcfce7" },
  watch: { label: "Watch",    icon: "⌚", bg: "#f3e8ff" },
};

// ── Helpers ───────────────────────────────────────────────────────────────
function imgSrc(url) {
  if (!url) return "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&q=80";
  if (url.startsWith("http")) return url;
  return `${API}/${url}`;
}

// ── Typing dots ───────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "12px 16px" }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: "50%",
          background: "#94a3b8",
          animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          display: "inline-block",
        }} />
      ))}
    </div>
  );
}

// ── AI Avatar ─────────────────────────────────────────────────────────────
function BotAvatar({ size = 32 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)",
      display: "flex", alignItems: "center", justifyContent: "center",
      flexShrink: 0, fontSize: size * 0.4, boxShadow: "0 2px 8px rgba(245,158,11,0.4)",
    }}>
      ✦
    </div>
  );
}

// ── Match badge ───────────────────────────────────────────────────────────
function MatchBadge({ pct }) {
  if (pct == null) return null;
  const color = pct >= 70 ? "#16a34a" : pct >= 40 ? "#d97706" : "#6b7280";
  const bg    = pct >= 70 ? "#dcfce7" : pct >= 40 ? "#fef3c7" : "#f3f4f6";
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 50,
      background: bg, color, border: `1px solid ${color}30`,
    }}>
      {pct >= 70 ? "🎯 " : ""}{pct}% match
    </span>
  );
}

// ── Product card (general) ────────────────────────────────────────────────
function ProductCard({ product, onNavigate }) {
  const [loaded, setLoaded] = useState(false);
  const price    = Number(product.price).toLocaleString("en-IN");
  const rating   = product.rating ? Number(product.rating).toFixed(1) : null;
  const matchPct = product.match_pct ?? null;

  return (
    <div
      onClick={() => onNavigate(product.id)}
      style={{
        background: "#fff", borderRadius: 14,
        border: "1.5px solid #f1f5f9",
        overflow: "hidden", cursor: "pointer",
        transition: "all 0.2s",
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = "translateY(-3px)";
        e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
        e.currentTarget.style.borderColor = "#f59e0b";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.06)";
        e.currentTarget.style.borderColor = "#f1f5f9";
      }}
    >
      <div style={{ position: "relative", aspectRatio: "1/1", background: "#f8fafc", overflow: "hidden" }}>
        {!loaded && (
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.5s infinite" }} />
        )}
        <img
          src={imgSrc(product.image_url)} alt={product.name} loading="lazy"
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: loaded ? 1 : 0, transition: "opacity 0.3s" }}
          onLoad={() => setLoaded(true)}
          onError={e => { e.currentTarget.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&q=80"; setLoaded(true); }}
        />
        {rating && (
          <div style={{
            position: "absolute", top: 6, right: 6,
            background: "#f59e0b", color: "#111",
            fontSize: 10, fontWeight: 800, padding: "2px 7px", borderRadius: 50,
          }}>
            ★ {rating}
          </div>
        )}
        {matchPct != null && matchPct >= 60 && (
          <div style={{
            position: "absolute", top: 6, left: 6,
            background: "#16a34a", color: "#fff",
            fontSize: 9, fontWeight: 700, padding: "2px 6px", borderRadius: 50,
          }}>
            🎯 {matchPct}%
          </div>
        )}
      </div>
      <div style={{ padding: "10px 11px 12px" }}>
        <p style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 3px", fontWeight: 600 }}>
          {product.brand}
        </p>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#1e293b", margin: "0 0 6px", lineHeight: 1.35,
          overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
          {product.name}
        </p>
        <p style={{ fontSize: 14, fontWeight: 900, color: "#ef4444", margin: 0 }}>₹{price}</p>
      </div>
    </div>
  );
}

// ── Outfit slot card ──────────────────────────────────────────────────────
function OutfitCard({ item, slot, onNavigate }) {
  const [loaded, setLoaded] = useState(false);
  const meta  = SLOT_META[slot] || {};
  const price = Number(item.price).toLocaleString("en-IN");
  const pct   = item.match_pct;

  return (
    <div
      onClick={() => onNavigate(item.id)}
      style={{
        background: "#fff", borderRadius: 14,
        border: "2px solid #f1f5f9",
        overflow: "hidden", cursor: "pointer",
        transition: "all 0.2s",
        position: "relative",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = "#f59e0b";
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "0 8px 20px rgba(0,0,0,0.1)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = "#f1f5f9";
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {/* Slot label */}
      <div style={{
        position: "absolute", top: 7, left: 7, zIndex: 2,
        background: meta.bg || "#f1f5f9",
        fontSize: 9, fontWeight: 800, padding: "3px 8px", borderRadius: 50,
        display: "flex", alignItems: "center", gap: 3,
        color: "#374151",
      }}>
        <span>{meta.icon}</span>
        <span style={{ textTransform: "uppercase", letterSpacing: "0.05em" }}>{meta.label}</span>
      </div>

      <div style={{ aspectRatio: "1/1", background: "#f8fafc", position: "relative", overflow: "hidden" }}>
        {!loaded && (
          <div style={{ position: "absolute", inset: 0, background: "#f1f5f9", animation: "pulse 1.5s infinite" }} />
        )}
        <img
          src={imgSrc(item.image_url)} alt={item.name} loading="lazy"
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: loaded ? 1 : 0, transition: "opacity 0.3s" }}
          onLoad={() => setLoaded(true)}
          onError={e => { e.currentTarget.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&q=80"; setLoaded(true); }}
        />
        {item.rating && (
          <div style={{
            position: "absolute", top: 7, right: 7,
            background: "#f59e0b", color: "#111",
            fontSize: 10, fontWeight: 800, padding: "2px 7px", borderRadius: 50,
          }}>
            ★ {Number(item.rating).toFixed(1)}
          </div>
        )}
      </div>
      <div style={{ padding: "9px 10px 11px" }}>
        <p style={{ fontSize: 10, color: "#94a3b8", margin: "0 0 2px", fontWeight: 600 }}>{item.brand || item.category}</p>
        <p style={{ fontSize: 11, fontWeight: 700, color: "#1e293b", margin: "0 0 5px", lineHeight: 1.3,
          overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
          {item.name}
        </p>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ fontSize: 13, fontWeight: 900, color: "#1e293b", margin: 0 }}>₹{price}</p>
          {pct != null && <MatchBadge pct={pct} />}
        </div>
      </div>
    </div>
  );
}

// ── Outfit price strip ─────────────────────────────────────────────────────
function OutfitTotal({ outfit }) {
  const items = SLOT_ORDER.map(s => outfit[s]).filter(Boolean);
  if (!items.length) return null;
  const total = items.reduce((s, i) => s + (Number(i.price) || 0), 0);
  return (
    <div style={{
      marginTop: 10,
      background: "linear-gradient(135deg, #111 0%, #1e293b 100%)",
      borderRadius: 12, padding: "12px 16px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
    }}>
      <div>
        <p style={{ color: "#94a3b8", fontSize: 10, margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.1em" }}>
          Complete outfit · {items.length} pieces
        </p>
        <p style={{ color: "#f59e0b", fontSize: 18, fontWeight: 900, margin: 0 }}>
          ₹{total.toLocaleString("en-IN")}
        </p>
      </div>
      <div style={{
        background: "#f59e0b", color: "#111",
        fontSize: 11, fontWeight: 800, padding: "6px 14px", borderRadius: 50,
      }}>
        Shop All →
      </div>
    </div>
  );
}

// ── NLP Confidence strip ──────────────────────────────────────────────────
function ConfidenceStrip({ nlp, occasionLabel, onAlternative }) {
  if (!nlp || nlp.confidence >= 0.5) return null;
  const pct = Math.round(nlp.confidence * 100);
  return (
    <div style={{
      background: "#fffbeb", border: "1px solid #fde68a",
      borderRadius: 10, padding: "10px 14px", marginBottom: 8,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#92400e" }}>
          Matched: {occasionLabel}
        </span>
        <div style={{ flex: 1, height: 4, background: "#fde68a", borderRadius: 50, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, background: "#f59e0b", borderRadius: 50 }} />
        </div>
        <span style={{ fontSize: 10, color: "#d97706", fontWeight: 700 }}>{pct}%</span>
      </div>
      {nlp.alternatives?.length > 0 && (
        <p style={{ fontSize: 11, color: "#92400e", margin: 0 }}>
          Did you mean:{" "}
          {nlp.alternatives.map(a => (
            <button key={a.occasion} onClick={() => onAlternative(a.label)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#b45309", fontWeight: 700, fontSize: 11, padding: 0, textDecoration: "underline", marginRight: 6 }}>
              {a.icon} {a.label}
            </button>
          ))}?
        </p>
      )}
    </div>
  );
}

// ── Message renderer ──────────────────────────────────────────────────────
function Message({ msg, onChip, onNavigate, onRefine }) {
  const isUser = msg.role === "user";

  if (msg.type === "typing") return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
      <BotAvatar />
      <div style={{ background: "#fff", border: "1.5px solid #f1f5f9", borderRadius: "16px 16px 16px 4px", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <TypingDots />
      </div>
    </div>
  );

  // Occasion chips
  if (msg.type === "chips") return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
      <BotAvatar />
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, color: "#475569", margin: "0 0 10px", fontWeight: 500 }}>
          What's the occasion? Pick one:
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {(msg.occasions || OCCASIONS).map(occ => (
            <button key={occ.key} onClick={() => onChip(occ)}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                background: "#fff", border: "1.5px solid #e2e8f0",
                borderRadius: 10, padding: "9px 12px",
                cursor: "pointer", textAlign: "left",
                transition: "all 0.15s", fontSize: 12, fontWeight: 600, color: "#334155",
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "#f59e0b"; e.currentTarget.style.background = "#fffbeb"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.background = "#fff"; }}
            >
              <span style={{ fontSize: 18 }}>{occ.icon}</span>
              <span>{occ.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  // Outfit grid (occasion path)
  if (msg.type === "outfit") return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start", width: "100%" }}>
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0 }}>
        <ConfidenceStrip nlp={msg.nlp} occasionLabel={msg.occasion_label} onAlternative={onRefine} />
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 22 }}>{msg.occasion_icon}</span>
          <div>
            <p style={{ fontSize: 13, fontWeight: 800, color: "#1e293b", margin: 0 }}>
              Best outfit for {msg.occasion_label}
            </p>
            <p style={{ fontSize: 11, color: "#94a3b8", margin: 0 }}>AI-curated 4-piece set</p>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {SLOT_ORDER.map(slot => {
            const item = msg.outfit[slot];
            if (!item) return (
              <div key={slot} style={{
                borderRadius: 12, border: "2px dashed #e2e8f0",
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                aspectRatio: "1/1", gap: 4, background: "#f8fafc",
              }}>
                <span style={{ fontSize: 24 }}>{SLOT_META[slot]?.icon}</span>
                <p style={{ fontSize: 10, color: "#94a3b8", margin: 0 }}>No match</p>
              </div>
            );
            return <OutfitCard key={slot} item={item} slot={slot} onNavigate={onNavigate} />;
          })}
        </div>
        <OutfitTotal outfit={msg.outfit} />
      </div>
    </div>
  );

  // Product grid
  if (msg.type === "products") return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start", width: "100%" }}>
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0 }}>
        {msg.label && (
          <p style={{ fontSize: 11, fontWeight: 700, color: "#64748b", margin: "0 0 8px",
            textTransform: "uppercase", letterSpacing: "0.08em" }}>
            {msg.occasion_icon} {msg.label}
          </p>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {(msg.products || []).slice(0, 6).map(p => (
            <ProductCard key={p.id} product={p} onNavigate={onNavigate} />
          ))}
        </div>
        {msg.products?.length > 6 && (
          <p style={{ fontSize: 11, color: "#94a3b8", textAlign: "center", marginTop: 6 }}>
            +{msg.products.length - 6} more results
          </p>
        )}
      </div>
    </div>
  );

  // NLP reply text bubble
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexDirection: isUser ? "row-reverse" : "row" }}>
      {!isUser && <BotAvatar />}
      <div style={{
        maxWidth: "78%",
        padding: "11px 15px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser
          ? "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)"
          : "#fff",
        color: isUser ? "#fff" : "#334155",
        fontSize: 13, lineHeight: 1.65,
        boxShadow: isUser
          ? "0 4px 16px rgba(245,158,11,0.35)"
          : "0 2px 10px rgba(0,0,0,0.07)",
        border: isUser ? "none" : "1.5px solid #f1f5f9",
        fontWeight: isUser ? 600 : 400,
      }}>
        {msg.text}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// MAIN CHATBOT COMPONENT
// ══════════════════════════════════════════════════════════════════════
export default function UnifiedChatbot() {
  const navigate = useNavigate();

  const rawUser = localStorage.getItem("user");
  const user    = rawUser ? JSON.parse(rawUser) : null;
  const token   = localStorage.getItem("token");
  const userId  = user?.id || (() => {
    try { return JSON.parse(atob(token.split(".")[1])).user_id; } catch { return null; }
  })();

  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);
  const windowRef  = useRef(null);

  const [open,        setOpen]        = useState(false);
  const [messages,    setMessages]    = useState([]);
  const [input,       setInput]       = useState("");
  const [loading,     setLoading]     = useState(false);
  const [greeted,     setGreeted]     = useState(false);
  const [budget,      setBudget]      = useState("");
  const [unreadCount, setUnreadCount] = useState(0);
  const [showOccasions, setShowOccasions] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Greet on first open
  useEffect(() => {
    if (!open || greeted) return;
    setGreeted(true);
    const name = user?.name?.split(" ")[0] || null;
    setTimeout(() => {
      push({ role: "bot", type: "text", text: `Hey${name ? ` ${name}` : ""}! 👋 I'm your AI style assistant. I can recommend outfits for any occasion or help you find specific products. What are you dressing for today?` });
    }, 350);
  }, [open]);

  const push = useCallback((msg) => {
    setMessages(p => [...p, { ...msg, _id: Date.now() + Math.random() }]);
    if (!open && msg.role === "bot") setUnreadCount(c => c + 1);
  }, [open]);

  const pushTyping = useCallback(() => {
    const id = `typing-${Date.now()}`;
    setMessages(p => [...p, { role: "bot", type: "typing", _id: id }]);
    return id;
  }, []);

  const removeTyping = useCallback((id) => {
    setMessages(p => p.filter(m => m._id !== id));
  }, []);

  const handleOpen = () => {
    setOpen(o => !o);
    setUnreadCount(0);
  };

  const handleNavigate = useCallback((productId) => {
    setOpen(false);
    navigate(`/product/${productId}`);
  }, [navigate]);

  const send = useCallback(async (text, extraRefinements = {}) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setShowOccasions(false);
    push({ role: "user", type: "text", text: msg });
    setLoading(true);
    const tid = pushTyping();

    const history = messages
      .filter(m => m.type === "text" && m.role)
      .slice(-6)
      .map(m => ({ role: m.role === "bot" ? "assistant" : "user", content: m.text }));

    const refinements = { ...(budget ? { budget } : {}), ...extraRefinements };

    try {
      const res = await fetch(`${API}/api/chat/unified`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: msg, history, refinements, user_id: userId }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      removeTyping(tid);

      // 1. Text reply
      push({ role: "bot", type: "text", text: data.reply });

      // 2. NLP confidence badge (if low confidence occasion match)
      if (data.type === "occasion" && data.nlp?.confidence < 0.5 && data.nlp?.confidence >= 0.15) {
        // Show as inline in outfit message
      }

      // 3. Outfit grid
      if (data.type === "occasion" && data.outfit && Object.keys(data.outfit).length > 0) {
        push({
          role: "bot", type: "outfit",
          outfit: data.outfit,
          occasion_label: data.occasion_label,
          occasion_icon:  data.occasion_icon,
          nlp: data.nlp,
        });
      }

      // 4. Products grid
      if (data.products?.length > 0) {
        push({
          role: "bot", type: "products",
          products: data.products,
          total: data.total || data.products.length,
          label: data.type === "occasion" ? `More ${data.occasion_label} picks` : null,
          occasion_icon: data.occasion_icon || null,
        });
      }

      // 5. Clarify → show chips
      if (data.type === "clarify") {
        push({ role: "bot", type: "chips", occasions: data.occasions || OCCASIONS });
      }

    } catch (err) {
      removeTyping(tid);
      push({ role: "bot", type: "text", text: `Something went wrong — please try again! 🙏` });
    }

    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [input, loading, messages, token, userId, budget, push, pushTyping, removeTyping]);

  return (
    <>
      <style>{`
        @keyframes bounce {
          0%,100% { transform: translateY(0); }
          50%      { transform: translateY(-5px); }
        }
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes chatSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes pulse {
          0%,100% { opacity: 1; }
          50%      { opacity: 0.5; }
        }
        @keyframes btnPop {
          0%   { transform: scale(1); }
          50%  { transform: scale(1.15); }
          100% { transform: scale(1); }
        }
        .chat-scroll::-webkit-scrollbar { width: 4px; }
        .chat-scroll::-webkit-scrollbar-track { background: transparent; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 4px; }
        .quick-chip:hover { background: #fffbeb !important; border-color: #f59e0b !important; color: #92400e !important; }
        .budget-pill:hover { background: #1e293b !important; color: #fff !important; }
        .send-btn:not(:disabled):hover { background: #d97706 !important; }
      `}</style>

      {/* ── Floating toggle button ── */}
      <button
        onClick={handleOpen}
        style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 9999,
          width: 58, height: 58, borderRadius: "50%",
          background: open
            ? "#1e293b"
            : "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)",
          border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: open ? 22 : 26,
          boxShadow: "0 8px 24px rgba(245,158,11,0.4)",
          transition: "all 0.25s cubic-bezier(0.34,1.56,0.64,1)",
          color: "#fff",
        }}
        onMouseEnter={e => e.currentTarget.style.transform = "scale(1.08)"}
        onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
        aria-label="Toggle chat"
      >
        {open ? "✕" : "🛍️"}
        {!open && unreadCount > 0 && (
          <span style={{
            position: "absolute", top: 2, right: 2,
            width: 18, height: 18, borderRadius: "50%",
            background: "#ef4444", color: "#fff",
            fontSize: 10, fontWeight: 800,
            display: "flex", alignItems: "center", justifyContent: "center",
            border: "2px solid #fff",
          }}>
            {unreadCount}
          </span>
        )}
      </button>

      {/* ── Chat window ── */}
      {open && (
        <div
          ref={windowRef}
          style={{
            position: "fixed", bottom: 96, right: 24, zIndex: 9998,
            width: 400, maxWidth: "calc(100vw - 32px)",
            height: 640, maxHeight: "calc(100vh - 120px)",
            background: "#f8fafc",
            borderRadius: 22,
            boxShadow: "0 24px 80px rgba(0,0,0,0.2), 0 8px 24px rgba(0,0,0,0.12)",
            display: "flex", flexDirection: "column",
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.8)",
            animation: "chatSlideUp 0.35s cubic-bezier(0.34,1.56,0.64,1)",
          }}
        >
          {/* ── Header ── */}
          <div style={{
            background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
            padding: "14px 18px",
            flexShrink: 0,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{
                width: 40, height: 40, borderRadius: "50%",
                background: "linear-gradient(135deg, #f59e0b, #ef4444)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, boxShadow: "0 4px 12px rgba(245,158,11,0.5)",
              }}>
                ✦
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ color: "#fff", fontWeight: 800, fontSize: 14, margin: 0, letterSpacing: "-0.01em" }}>
                  AI Style Assistant
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 2 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#4ade80", animation: "pulse 2s infinite" }} />
                  <span style={{ color: "#94a3b8", fontSize: 11 }}>Online · Occasion-aware AI</span>
                </div>
              </div>
              {/* Shop by Occasion pill */}
              <button
                onClick={() => setShowOccasions(s => !s)}
                style={{
                  background: showOccasions ? "#f59e0b" : "rgba(255,255,255,0.1)",
                  border: "1px solid rgba(255,255,255,0.15)",
                  borderRadius: 50, padding: "5px 12px",
                  color: showOccasions ? "#111" : "#fff",
                  fontSize: 11, fontWeight: 700, cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                🗂 Occasions
              </button>
            </div>

            {/* Occasion picker (expandable) */}
            {showOccasions && (
              <div style={{ marginTop: 12, animation: "fadeIn 0.2s ease" }}>
                <p style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em", margin: "0 0 8px", fontWeight: 700 }}>
                  Shop by occasion
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                  {OCCASIONS.map(occ => (
                    <button key={occ.key}
                      onClick={() => { send(occ.label); setShowOccasions(false); }}
                      style={{
                        display: "flex", alignItems: "center", gap: 7,
                        background: "rgba(255,255,255,0.08)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: 9, padding: "8px 10px",
                        color: "#e2e8f0", fontSize: 11, fontWeight: 600,
                        cursor: "pointer", textAlign: "left",
                        transition: "all 0.15s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = "rgba(245,158,11,0.2)"; e.currentTarget.style.borderColor = "#f59e0b"; }}
                      onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"; }}
                    >
                      <span style={{ fontSize: 16 }}>{occ.icon}</span>
                      <span>{occ.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ── Budget filter row ── */}
          <div style={{
            background: "#fff",
            padding: "8px 14px",
            display: "flex", gap: 6, overflowX: "auto",
            flexShrink: 0,
            borderBottom: "1px solid #f1f5f9",
          }}>
            <span style={{ fontSize: 10, color: "#94a3b8", fontWeight: 700, flexShrink: 0, display: "flex", alignItems: "center", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Budget:
            </span>
            {BUDGET_FILTERS.map(b => (
              <button key={b.key}
                className="budget-pill"
                onClick={() => setBudget(b.key)}
                style={{
                  flexShrink: 0, fontSize: 11, padding: "4px 11px",
                  borderRadius: 50, border: "1.5px solid",
                  borderColor: budget === b.key ? "#1e293b" : "#e2e8f0",
                  background: budget === b.key ? "#1e293b" : "#fff",
                  color: budget === b.key ? "#fff" : "#475569",
                  cursor: "pointer", fontWeight: 600,
                  transition: "all 0.15s",
                }}
              >
                {b.label}
              </button>
            ))}
          </div>

          {/* ── Messages ── */}
          <div className="chat-scroll" style={{
            flex: 1, overflowY: "auto",
            padding: "16px 14px",
            display: "flex", flexDirection: "column", gap: 14,
          }}>
            {messages.length === 0 && (
              <div style={{ textAlign: "center", padding: "32px 16px", animation: "fadeIn 0.5s ease" }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>✦</div>
                <p style={{ fontWeight: 800, color: "#1e293b", margin: "0 0 6px", fontSize: 16 }}>
                  Your AI Style Assistant
                </p>
                <p style={{ color: "#64748b", fontSize: 12, margin: "0 0 20px", lineHeight: 1.6 }}>
                  Tell me what occasion you're dressing for and I'll curate a complete outfit with AI recommendations.
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 7, justifyContent: "center" }}>
                  {OCCASIONS.slice(0, 4).map(occ => (
                    <button key={occ.key} onClick={() => send(occ.label)}
                      style={{
                        display: "flex", alignItems: "center", gap: 6,
                        background: "#fff", border: "1.5px solid #e2e8f0",
                        borderRadius: 50, padding: "7px 14px",
                        fontSize: 12, fontWeight: 600, color: "#334155",
                        cursor: "pointer", transition: "all 0.15s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = "#f59e0b"; e.currentTarget.style.background = "#fffbeb"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.background = "#fff"; }}
                    >
                      <span>{occ.icon}</span> {occ.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map(msg => (
              <Message
                key={msg._id}
                msg={msg}
                onChip={occ => send(occ.label)}
                onNavigate={handleNavigate}
                onRefine={label => send(label)}
              />
            ))}

            <div ref={bottomRef} />
          </div>

          {/* ── Quick prompts ── */}
          <div style={{
            background: "#fff", padding: "8px 12px 6px",
            display: "flex", gap: 6, overflowX: "auto",
            flexShrink: 0, borderTop: "1px solid #f1f5f9",
          }}>
            {QUICK_PROMPTS.map(p => (
              <button key={p.text}
                className="quick-chip"
                onClick={() => send(p.text)}
                disabled={loading}
                style={{
                  flexShrink: 0, fontSize: 11, padding: "5px 12px",
                  borderRadius: 50, border: "1.5px solid #e2e8f0",
                  background: "#fff", color: "#475569",
                  cursor: "pointer", fontWeight: 600,
                  transition: "all 0.15s", whiteSpace: "nowrap",
                  opacity: loading ? 0.5 : 1,
                }}
              >
                {p.icon} {p.text}
              </button>
            ))}
          </div>

          {/* ── Input ── */}
          <div style={{
            background: "#fff", padding: "12px 14px",
            flexShrink: 0, borderTop: "1px solid #f1f5f9",
          }}>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <div style={{ flex: 1, position: "relative" }}>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                  placeholder='e.g. "interview tomorrow" or "jeans under ₹2000"'
                  rows={1}
                  disabled={loading}
                  style={{
                    width: "100%", resize: "none", border: "1.5px solid #e2e8f0",
                    borderRadius: 14, padding: "11px 14px",
                    fontSize: 13, outline: "none", background: "#f8fafc",
                    color: "#1e293b", fontFamily: "inherit",
                    transition: "border-color 0.15s",
                    maxHeight: 90, boxSizing: "border-box",
                  }}
                  onFocus={e => e.target.style.borderColor = "#f59e0b"}
                  onBlur={e => e.target.style.borderColor = "#e2e8f0"}
                />
              </div>
              <button
                className="send-btn"
                onClick={() => send()}
                disabled={loading || !input.trim()}
                style={{
                  width: 44, height: 44,
                  background: loading || !input.trim()
                    ? "#e2e8f0"
                    : "linear-gradient(135deg, #f59e0b, #ef4444)",
                  border: "none", borderRadius: 12,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                  flexShrink: 0, transition: "all 0.2s",
                  boxShadow: !loading && input.trim() ? "0 4px 12px rgba(245,158,11,0.4)" : "none",
                }}
              >
                {loading
                  ? <span style={{ width: 16, height: 16, border: "2px solid #94a3b8", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "bounce 0.8s linear infinite" }} />
                  : <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                }
              </button>
            </div>
            <p style={{ fontSize: 10, color: "#94a3b8", textAlign: "center", margin: "6px 0 0" }}>
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </div>
      )}
    </>
  );
}