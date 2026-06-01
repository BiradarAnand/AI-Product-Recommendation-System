import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API = "https://ai-product-recommendation-system-by60.onrender.com";

const SUGGESTIONS = [
  "Job interview outfit",
  "Gym & sports",
  "Wedding / function",
  "Casual outing",
  "Date night",
  "Watches under ₹3000",
  "Jeans",
  "Formal shoes",
  "Beach vacation",
  "College wear",
];

const OCCASIONS = [
  { key: "job_interview", label: "Job Interview",      icon: "💼" },
  { key: "sports",        label: "Sports & Gym",       icon: "🏃" },
  { key: "wedding",       label: "Wedding / Function", icon: "🎊" },
  { key: "casual_outing", label: "Casual Outing",      icon: "☀️" },
  { key: "date_night",    label: "Date Night",         icon: "🌙" },
  { key: "office",        label: "Office & Work",      icon: "🏢" },
  { key: "festival",      label: "Festival",           icon: "🪔" },
  { key: "beach",         label: "Beach & Vacation",   icon: "🏖️" },
  { key: "college",       label: "College / Campus",   icon: "🎓" },
];

function Avatar() {
  return (
    <div style={{
      flexShrink: 0, width: 32, height: 32, borderRadius: "50%",
      background: "#F5C518", display: "flex", alignItems: "center",
      justifyContent: "center", fontWeight: 900, fontSize: 12, color: "#111",
    }}>AI</div>
  );
}

function Typing() {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
      <Avatar />
      <div style={{
        background: "#fff", border: "1px solid #e5e7eb",
        borderRadius: "16px 16px 16px 4px", padding: "12px 16px",
      }}>
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          {[0, 150, 300].map(d => (
            <span key={d} style={{
              width: 6, height: 6, borderRadius: "50%", background: "#9ca3af",
              animation: "bounce 1s infinite",
              animationDelay: `${d}ms`,
            }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ProductCard({ product, onClick }) {
  const [loaded, setLoaded] = useState(false);
  return (
    <div
      onClick={() => onClick(product)}
      style={{
        background: "#fff", border: "1.5px solid #f0f0ee",
        borderRadius: 12, overflow: "hidden", cursor: "pointer",
        transition: "transform 0.2s, box-shadow 0.2s",
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
    >
      <div style={{ height: 100, background: "#f8f8f6", position: "relative", overflow: "hidden" }}>
        {!loaded && <div style={{ position: "absolute", inset: 0, background: "#e5e7eb", animation: "pulse 1.5s infinite" }} />}
        <img
          src={product.image_url || "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=200"}
          alt={product.name}
          style={{ width: "100%", height: "100%", objectFit: "contain", padding: 8, opacity: loaded ? 1 : 0, transition: "opacity 0.3s" }}
          onLoad={() => setLoaded(true)}
          onError={e => { e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=200"; setLoaded(true); }}
        />
        {product.rating > 0 && (
          <span style={{
            position: "absolute", top: 4, right: 4,
            background: "#F5C518", color: "#111",
            fontSize: 9, fontWeight: 800, padding: "2px 5px", borderRadius: 6,
          }}>★ {Number(product.rating).toFixed(1)}</span>
        )}
      </div>
      <div style={{ padding: "8px 10px 10px" }}>
        <p style={{ margin: "0 0 2px", fontSize: 10, color: "#9ca3af", fontWeight: 600, textTransform: "uppercase" }}>{product.brand}</p>
        <p style={{ margin: "0 0 4px", fontSize: 11, fontWeight: 700, color: "#111", lineHeight: 1.3,
          overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
          {product.name}
        </p>
        <p style={{ margin: 0, fontSize: 13, fontWeight: 900, color: "#ef4444" }}>
          ₹{Number(product.price).toLocaleString("en-IN")}
        </p>
      </div>
    </div>
  );
}

function Message({ msg, onChip, onProduct }) {
  const isUser = msg.role === "user";

  if (msg.type === "typing") return <Typing />;

  if (msg.type === "chips") return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
      <Avatar />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxWidth: 300 }}>
        {(msg.occasions || OCCASIONS).map(occ => (
          <button key={occ.key} onClick={() => onChip(occ.label)}
            style={{
              display: "flex", alignItems: "center", gap: 5,
              padding: "6px 12px", borderRadius: 50,
              border: "1.5px solid #e5e7eb", background: "#fff",
              fontSize: 12, fontWeight: 600, color: "#374151",
              cursor: "pointer", transition: "all 0.15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "#F5C518"; e.currentTarget.style.background = "#fffbeb"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "#e5e7eb"; e.currentTarget.style.background = "#fff"; }}
          >
            <span>{occ.icon}</span><span>{occ.label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  if (msg.type === "products") return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8, width: "100%" }}>
      <Avatar />
      <div style={{ flex: 1, minWidth: 0 }}>
        {msg.label && (
          <p style={{ margin: "0 0 8px", fontSize: 11, color: "#6b7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {msg.label}
          </p>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {(msg.products || []).slice(0, 6).map(p => (
            <ProductCard key={p.id} product={p} onClick={onProduct} />
          ))}
        </div>
        {msg.products?.length > 6 && (
          <p style={{ fontSize: 11, color: "#9ca3af", textAlign: "center", marginTop: 6 }}>
            +{msg.products.length - 6} more
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8, flexDirection: isUser ? "row-reverse" : "row" }}>
      {!isUser && <Avatar />}
      <div style={{
        maxWidth: "75%", padding: "10px 14px", borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser ? "#4f46e5" : "#fff",
        color: isUser ? "#fff" : "#111827",
        border: isUser ? "none" : "1px solid #e5e7eb",
        fontSize: 13, lineHeight: 1.6,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}>
        {msg.text}
      </div>
    </div>
  );
}

export default function UnifiedChatbot() {
  const navigate  = useNavigate();
  const [open, setOpen]       = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const [greeted, setGreeted] = useState(false);
  const [budget, setBudget]   = useState("");
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!open || greeted) return;
    setGreeted(true);
    const user = JSON.parse(localStorage.getItem("user") || "null");
    const name = user?.name?.split(" ")[0] || null;
    setTimeout(() => {
      push({ role: "bot", type: "text", text: `Hey${name ? ` ${name}` : ""}! 👋 I'm your style assistant. Tell me what occasion or product you're looking for!` });
      setTimeout(() => push({ role: "bot", type: "chips", occasions: OCCASIONS }), 400);
    }, 300);
  }, [open]);

  const push = (msg) =>
    setMessages(p => [...p, { ...msg, _id: Date.now() + Math.random() }]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    push({ role: "user", type: "text", text: msg });
    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/api/chat/unified`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: msg,
          refinements: budget ? { budget } : {},
        }),
      });

      const data = await res.json();

      push({ role: "bot", type: "text", text: data.reply });

      if (data.products?.length > 0) {
        push({
          role: "bot", type: "products",
          products: data.products,
          label: `${data.products.length} products found`,
        });
      }

      if (data.type === "clarify") {
        push({ role: "bot", type: "chips", occasions: OCCASIONS });
      }

    } catch (e) {
      push({ role: "bot", type: "text", text: "Something went wrong. Please try again 🙏" });
    }

    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <>
      <style>{`
        @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideUp { from{transform:translateY(20px);opacity:0} to{transform:none;opacity:1} }
      `}</style>

      {/* Toggle button */}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label="Toggle chat"
        style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 9999,
          width: 56, height: 56, borderRadius: "50%",
          background: "#4f46e5", border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 24, boxShadow: "0 4px 20px rgba(79,70,229,0.4)",
          transition: "transform 0.2s, background 0.2s",
        }}
        onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
        onMouseLeave={e => e.currentTarget.style.transform = "none"}
      >
        {open ? "✕" : "🛍️"}
      </button>

      {/* Chat window */}
      {open && (
        <div style={{
          position: "fixed", bottom: 92, right: 24, zIndex: 9998,
          width: 380, maxWidth: "calc(100vw - 32px)", height: 580,
          background: "#fff", borderRadius: 20,
          boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
          border: "1px solid #e5e7eb",
          display: "flex", flexDirection: "column", overflow: "hidden",
          animation: "slideUp 0.3s ease",
          fontFamily: "'DM Sans', sans-serif",
        }}>

          {/* Header */}
          <div style={{
            background: "#4f46e5", padding: "14px 16px",
            display: "flex", alignItems: "center", gap: 12, flexShrink: 0,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: "50%",
              background: "rgba(255,255,255,0.2)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
            }}>🛍️</div>
            <div>
              <p style={{ margin: 0, color: "#fff", fontWeight: 700, fontSize: 14 }}>Style Assistant</p>
              <p style={{ margin: 0, color: "rgba(255,255,255,0.7)", fontSize: 11 }}>Suggest products by occasion or type</p>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#4ade80", animation: "pulse 2s infinite" }} />
              <span style={{ color: "rgba(255,255,255,0.7)", fontSize: 11 }}>Online</span>
            </div>
          </div>

          {/* Budget filter */}
          <div style={{
            padding: "8px 12px", borderBottom: "1px solid #f3f4f6",
            display: "flex", gap: 6, overflowX: "auto", flexShrink: 0,
          }}>
            {[
              { key: "",        label: "All" },
              { key: "budget",  label: "≤₹1000" },
              { key: "mid",     label: "≤₹3000" },
              { key: "premium", label: "≤₹8000" },
            ].map(b => (
              <button key={b.key}
                onClick={() => setBudget(b.key)}
                style={{
                  flexShrink: 0, padding: "4px 10px", borderRadius: 50, fontSize: 11,
                  fontWeight: 600, cursor: "pointer", border: "1.5px solid",
                  borderColor: budget === b.key ? "#4f46e5" : "#e5e7eb",
                  background: budget === b.key ? "#4f46e5" : "#fff",
                  color: budget === b.key ? "#fff" : "#6b7280",
                  transition: "all 0.15s",
                }}
              >
                {b.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, overflowY: "auto", padding: "16px 12px",
            display: "flex", flexDirection: "column", gap: 12,
            background: "#f9fafb",
          }}>
            {messages.map(msg => (
              <Message
                key={msg._id}
                msg={msg}
                onChip={label => send(label)}
                onProduct={p => { setOpen(false); navigate(`/product/${p.id}`); }}
              />
            ))}
            {loading && <Typing />}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          <div style={{
            padding: "8px 12px", borderTop: "1px solid #f3f4f6",
            display: "flex", gap: 6, overflowX: "auto", flexShrink: 0,
          }}>
            {SUGGESTIONS.map(s => (
              <button key={s} onClick={() => send(s)} disabled={loading}
                style={{
                  flexShrink: 0, padding: "5px 10px", borderRadius: 50,
                  border: "1.5px solid #e5e7eb", background: "#fff",
                  fontSize: 11, fontWeight: 600, color: "#374151",
                  cursor: "pointer", whiteSpace: "nowrap",
                  opacity: loading ? 0.4 : 1, transition: "all 0.15s",
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "#4f46e5"; e.currentTarget.style.color = "#4f46e5"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "#e5e7eb"; e.currentTarget.style.color = "#374151"; }}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input */}
          <div style={{
            padding: "10px 12px 12px", background: "#fff",
            borderTop: "1px solid #f3f4f6", flexShrink: 0,
          }}>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder='Try "job interview" or "jeans under ₹2000"'
                rows={1}
                disabled={loading}
                style={{
                  flex: 1, resize: "none", fontSize: 13,
                  border: "1.5px solid #e5e7eb", borderRadius: 12,
                  padding: "10px 12px", outline: "none",
                  background: "#f9fafb", maxHeight: 80,
                  fontFamily: "inherit", lineHeight: 1.5,
                  opacity: loading ? 0.5 : 1,
                }}
                onFocus={e => e.target.style.borderColor = "#4f46e5"}
                onBlur={e => e.target.style.borderColor = "#e5e7eb"}
              />
              <button
                onClick={() => send()}
                disabled={loading || !input.trim()}
                style={{
                  width: 38, height: 38, borderRadius: 10, border: "none",
                  background: loading || !input.trim() ? "#e5e7eb" : "#4f46e5",
                  color: "#fff", cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0, transition: "background 0.15s",
                }}
              >
                {loading
                  ? <span style={{ width: 14, height: 14, border: "2px solid #fff", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.7s linear infinite", display: "inline-block" }} />
                  : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/></svg>
                }
              </button>
            </div>
            <p style={{ margin: "6px 0 0", fontSize: 10, color: "#9ca3af", textAlign: "center" }}>Enter to send</p>
          </div>
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}