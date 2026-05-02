// UnifiedChatbot.jsx — merged from Chatbot.jsx + OccasionChatbot.jsx
// Calls /api/chat/unified for all messages

import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:5000";

const SLOT_ORDER = ["shirt", "pant", "shoes", "watch"];

const INIT_OCCASIONS = [
  { key: "job_interview", label: "Job Interview",          icon: "💼" },
  { key: "sports",        label: "Sports & Gym",           icon: "🏃" },
  { key: "wedding_guest", label: "Wedding / Function",     icon: "🎊" },
  { key: "casual_outing", label: "Casual Outing",          icon: "☀️" },
  { key: "date_night",    label: "Date Night",             icon: "🌙" },
  { key: "office",        label: "Office & Work",          icon: "🏢" },
  { key: "festival",      label: "Festival & Traditional", icon: "🪔" },
  { key: "beach",         label: "Beach & Vacation",       icon: "🏖️" },
];

const SUGGESTIONS = [
  "Job interview tomorrow",
  "Going to the gym",
  "Jeans under ₹1500",
  "Cousin's wedding",
  "Best rated watches",
  "Date night dinner",
  "Office daily wear",
  "Beach vacation trip",
];

// ─────────────────────────────────────────────
// Avatar
// ─────────────────────────────────────────────
function Avatar() {
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-yellow-400 flex items-center justify-center font-black text-gray-900 text-sm shadow-sm">
      AI
    </div>
  );
}

// ─────────────────────────────────────────────
// Typing indicator
// ─────────────────────────────────────────────
function Typing() {
  return (
    <div className="flex items-end gap-2">
      <Avatar />
      <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          {[0, 150, 300].map(d => (
            <span key={d} className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// General product card (used in general path)
// ─────────────────────────────────────────────
function ProductCard({ product, onClick }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const rating   = product.rating  ? Number(product.rating).toFixed(1)  : null;
  const price    = Number(product.price).toLocaleString("en-IN");
  const matchPct = product.match_pct ?? null;

  const handleClick = onClick || (() => window.location.href = `/product/${product.id}`);

  return (
    <div onClick={handleClick}
      className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer group">
      <div className="aspect-square overflow-hidden bg-gray-100 relative">
        {!imgLoaded && <div className="absolute inset-0 bg-gray-200 animate-pulse" />}
        <img
          src={product.image_url || "/placeholder.png"} alt={product.name} loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          style={{ opacity: imgLoaded ? 1 : 0, transition: "opacity 0.3s" }}
          onLoad={() => setImgLoaded(true)}
          onError={(e) => { e.currentTarget.src = "/placeholder.png"; setImgLoaded(true); }}
        />
        {rating && (
          <span className="absolute top-1.5 right-1.5 bg-yellow-400 text-gray-900 text-xs font-black px-1.5 py-0.5 rounded-md shadow">
            ★ {rating}
          </span>
        )}
        {matchPct !== null && matchPct >= 70 && (
          <span className="absolute top-1.5 left-1.5 bg-green-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-md shadow">
            🎯 {matchPct}%
          </span>
        )}
        {matchPct !== null && matchPct >= 40 && matchPct < 70 && (
          <span className="absolute top-1.5 left-1.5 bg-white/90 text-gray-600 text-xs px-1.5 py-0.5 rounded-md">
            {matchPct}% match
          </span>
        )}
      </div>
      <div className="p-2.5">
        <p className="text-xs font-semibold text-gray-900 truncate">{product.name}</p>
        <p className="text-xs text-gray-400 truncate mt-0.5">{product.brand}</p>
        <div className="flex items-center justify-between mt-1.5">
          <p className="text-sm font-black text-indigo-600">₹{price}</p>
          <span className="text-xs text-gray-400">{product.category}</span>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Outfit slot card (used in occasion path)
// ─────────────────────────────────────────────
function OutfitSlotCard({ item, onClick }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const price    = Number(item.price).toLocaleString("en-IN");
  const rating   = item.rating ? Number(item.rating).toFixed(1) : null;
  const matchPct = item.match_pct ?? null;

  return (
    <div onClick={onClick}
      className="bg-white rounded-xl border-2 border-gray-100 overflow-hidden shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-yellow-300 transition-all duration-200 cursor-pointer group relative">
      <div className="absolute top-1.5 left-1.5 z-10 flex items-center gap-1 bg-gray-900/80 text-white text-xs font-bold px-1.5 py-0.5 rounded-md">
        <span>{item.slot_icon}</span>
        <span>{item.slot_label}</span>
      </div>
      {rating && (
        <span className="absolute top-1.5 right-1.5 z-10 bg-yellow-400 text-gray-900 text-xs font-black px-1.5 py-0.5 rounded-md shadow">
          ★ {rating}
        </span>
      )}
      <div className="aspect-square overflow-hidden bg-gray-100 relative">
        {!imgLoaded && <div className="absolute inset-0 bg-gray-200 animate-pulse" />}
        <img
          src={item.image_url} alt={item.name} loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          style={{ opacity: imgLoaded ? 1 : 0, transition: "opacity 0.3s" }}
          onLoad={() => setImgLoaded(true)}
          onError={(e) => { e.currentTarget.style.display = "none"; setImgLoaded(true); }}
        />
      </div>
      <div className="p-2">
        <p className="text-xs font-semibold text-gray-900 truncate">{item.name}</p>
        <p className="text-xs text-gray-400 truncate mt-0.5">{item.brand || item.category}</p>
        <div className="flex items-center justify-between mt-1">
          <p className="text-sm font-black text-gray-900">₹{price}</p>
          {matchPct !== null && (
            <span className={`text-xs font-bold px-1.5 py-0.5 rounded-md
              ${matchPct >= 70 ? "bg-green-100 text-green-700" :
                matchPct >= 40 ? "bg-yellow-100 text-yellow-700" :
                "bg-gray-100 text-gray-500"}`}>
              {matchPct >= 70 ? "🎯 " : ""}{matchPct}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Outfit total price strip
// ─────────────────────────────────────────────
function OutfitPriceSummary({ outfit }) {
  const items = SLOT_ORDER.map(s => outfit[s]).filter(Boolean);
  if (!items.length) return null;
  const total    = items.reduce((sum, i) => sum + (i.price || 0), 0);
  const validPct = items.filter(i => i.match_pct != null);
  const avgMatch = validPct.length
    ? validPct.reduce((s, i) => s + i.match_pct, 0) / validPct.length
    : 0;

  return (
    <div className="mt-2.5 flex items-center justify-between bg-gray-900 rounded-xl px-4 py-2.5">
      <div className="flex items-center gap-1.5">
        <span className="text-yellow-400 text-sm">✦</span>
        <div>
          <p className="text-white text-xs font-semibold">Complete outfit · {items.length} pieces</p>
          {avgMatch > 0 && (
            <p className="text-gray-400 text-xs">avg match {Math.round(avgMatch)}%</p>
          )}
        </div>
      </div>
      <div className="text-right">
        <p className="text-yellow-400 font-black text-base leading-none">₹{total.toLocaleString("en-IN")}</p>
        <p className="text-gray-400 text-xs mt-0.5">total</p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// NLP confidence badge
// ─────────────────────────────────────────────
function ConfidenceBadge({ msg, onRefine }) {
  return (
    <div className="flex items-start gap-2">
      <Avatar />
      <div className="bg-amber-50 border border-amber-200 rounded-2xl rounded-bl-sm px-4 py-3 max-w-xs">
        <p className="text-xs font-semibold text-amber-700 mb-1">
          {msg.icon} Showing results for <strong>{msg.label}</strong>
        </p>
        <div className="flex items-center gap-2 mb-2">
          <div className="flex-1 bg-amber-100 rounded-full h-1.5">
            <div className="bg-amber-400 h-1.5 rounded-full"
              style={{ width: `${Math.round(msg.confidence * 100)}%` }} />
          </div>
          <span className="text-xs text-amber-600">{Math.round(msg.confidence * 100)}% match</span>
        </div>
        {msg.alternatives?.length > 0 && (
          <p className="text-xs text-amber-600">
            Did you mean:{" "}
            {msg.alternatives.map(a => (
              <button key={a.occasion} onClick={() => onRefine(a.label)}
                className="underline font-semibold mr-1">
                {a.icon} {a.label}
              </button>
            ))}?
          </p>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Single message renderer — handles ALL types
// ─────────────────────────────────────────────
function ChatMessage({ msg, onChip, onProduct, onRefine }) {
  const isUser = msg.role === "user";

  if (msg.type === "typing")     return <Typing />;
  if (msg.type === "confidence") return <ConfidenceBadge msg={msg} onRefine={onRefine} />;

  // Occasion chip buttons
  if (msg.type === "chips") return (
    <div className="flex items-start gap-2">
      <Avatar />
      <div className="flex flex-wrap gap-2 max-w-xs">
        {(msg.occasions || []).map(occ => (
          <button key={occ.key} onClick={() => onChip(occ)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:border-yellow-400 hover:bg-yellow-50 transition-all shadow-sm active:scale-95">
            <span>{occ.icon}</span><span>{occ.label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  // 4-slot outfit grid (occasion path)
  if (msg.type === "outfit") return (
    <div className="flex items-start gap-2 w-full">
      <Avatar />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">{msg.occasion_icon}</span>
          <div>
            <p className="text-sm font-black text-gray-900 leading-none">Best outfit for {msg.occasion_label}</p>
            <p className="text-xs text-gray-400 mt-0.5">AI-curated 4-piece set · ranked by match</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {SLOT_ORDER.map(slot => {
            const item = msg.outfit[slot];
            if (!item) return (
              <div key={slot} className="rounded-xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center aspect-square text-center p-3 bg-gray-50">
                <span className="text-2xl mb-1">{{ shirt:"👕", pant:"👖", shoes:"👟", watch:"⌚" }[slot]}</span>
                <p className="text-xs text-gray-400">No match</p>
              </div>
            );
            return <OutfitSlotCard key={slot} item={item} onClick={() => onProduct(item)} />;
          })}
        </div>
        <OutfitPriceSummary outfit={msg.outfit} />
      </div>
    </div>
  );

  // Product grid (both general and occasion "more picks")
  if (msg.type === "products") return (
    <div className="flex items-start gap-2 w-full">
      <Avatar />
      <div className="flex-1 min-w-0">
        {msg.label && (
          <p className="text-xs text-gray-500 font-semibold mb-2 uppercase tracking-wide">
            {msg.occasion_icon} {msg.label} picks — {msg.total} results
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          {(msg.products || []).slice(0, 6).map(p => (
            <ProductCard key={p.id} product={p} onClick={() => onProduct(p)} />
          ))}
        </div>
        {msg.products?.length > 6 && (
          <p className="text-xs text-gray-400 text-center mt-2">
            +{msg.products.length - 6} more matched
          </p>
        )}
      </div>
    </div>
  );

  // Plain text bubble (user + bot)
  return (
    <div className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      {!isUser && <Avatar />}
      <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm
        ${isUser
          ? "bg-indigo-600 text-white rounded-br-sm"
          : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm"}`}>
        {msg.text}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// MAIN — unified floating chatbot widget
// ─────────────────────────────────────────────
export default function UnifiedChatbot() {
  const navigate = useNavigate();

  // resolve user + token
  const rawUser = localStorage.getItem("user");
  const user    = rawUser ? JSON.parse(rawUser) : null;
  const token   = localStorage.getItem("token");
  const userId  = user?.id || (() => {
    try { return JSON.parse(atob(token.split(".")[1])).user_id; } catch { return null; }
  })();

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  const [open,        setOpen]        = useState(false);
  const [messages,    setMessages]    = useState([]);
  const [occasions,   setOccasions]   = useState(INIT_OCCASIONS);
  const [input,       setInput]       = useState("");
  const [loading,     setLoading]     = useState(false);
  const [greeted,     setGreeted]     = useState(false);
  const [refinements, setRefinements] = useState({});

  // auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // load occasions from backend on mount
  useEffect(() => {
    fetch(`${API}/api/chat/occasions`)
      .then(r => r.json())
      .then(d => { if (Array.isArray(d)) setOccasions(d); })
      .catch(() => {});
  }, []);

  // greeting on first open
  useEffect(() => {
    if (!open || greeted) return;
    setGreeted(true);
    const name = user?.name?.split(" ")[0] || null;
    setTimeout(() => {
      push({ role: "bot", type: "text", text: `Hey${name ? ` ${name}` : ""}! 👋 I'm your AI style assistant. Ask me for products or tell me what occasion you're dressing for!` });
      setTimeout(() => {
        push({ role: "bot", type: "chips", occasions: INIT_OCCASIONS });
      }, 400);
    }, 300);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const push = (msg) =>
    setMessages(p => [...p, { ...msg, _id: Date.now() + Math.random() }]);

  const pushTyping = () => {
    const id = `typing-${Date.now()}`;
    setMessages(p => [...p, { role: "bot", type: "typing", _id: id }]);
    return id;
  };

  const removeTyping = (id) =>
    setMessages(p => p.filter(m => m._id !== id));

  const send = async (text, extraRefinements = {}) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    push({ role: "user", type: "text", text: msg });
    setLoading(true);
    const tid = pushTyping();

    // build history for context (text turns only)
    const history = messages
      .filter(m => m.type === "text" && m.role !== undefined)
      .slice(-6)
      .map(m => ({ role: m.role === "bot" ? "assistant" : "user", content: m.text }));

    try {
      const res = await fetch(`${API}/api/chat/unified`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message:     msg,
          history,
          refinements: { ...refinements, ...extraRefinements },
          user_id:     userId,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      removeTyping(tid);

      // ── always show reply text first ──
      push({ role: "bot", type: "text", text: data.reply });

      // ── confidence badge (show if occasion but low confidence) ──
      if (data.type === "occasion" && data.nlp?.confidence < 0.5) {
        push({
          role: "bot", type: "confidence",
          label:        data.occasion_label,
          icon:         data.occasion_icon,
          confidence:   data.nlp.confidence,
          alternatives: data.nlp.alternatives || [],
        });
      }

      // ── outfit grid (occasion path only) ──
      if (data.type === "occasion" && data.outfit && Object.keys(data.outfit).length > 0) {
        push({
          role: "bot", type: "outfit",
          outfit:         data.outfit,
          occasion_label: data.occasion_label,
          occasion_icon:  data.occasion_icon,
        });
      }

      // ── product grid (both paths) ──
      if (data.products?.length > 0) {
        push({
          role: "bot", type: "products",
          products:       data.products,
          total:          data.total || data.products.length,
          label:          data.type === "occasion" ? `More ${data.occasion_label}` : null,
          occasion_icon:  data.occasion_icon || null,
        });
      }

      // ── clarify chips ──
      if (data.type === "clarify") {
        push({ role: "bot", type: "chips", occasions: data.occasions || occasions });
      }

    } catch (e) {
      removeTyping(tid);
      push({ role: "bot", type: "text", text: `Something went wrong (${e.message}). Please try again 🙏` });
    }

    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <>
      {/* ── Floating toggle button ── */}
      <button
        onClick={() => setOpen(o => !o)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-xl flex items-center justify-center text-2xl transition-all hover:scale-105 active:scale-95"
        aria-label="Toggle chat">
        {open ? "✕" : "🛍️"}
      </button>

      {/* ── Chat window ── */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[390px] max-w-[calc(100vw-24px)] h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">

          {/* Header */}
          <div className="bg-indigo-600 px-4 py-3 flex items-center gap-3 flex-shrink-0">
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-lg">🛍️</div>
            <div>
              <p className="text-white font-semibold text-sm">Style Assistant</p>
              <p className="text-indigo-200 text-xs">Products + Occasions · AI powered</p>
            </div>
            <div className="ml-auto flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-indigo-200 text-xs">Online</span>
            </div>
          </div>

          {/* Budget filter pills */}
          <div className="px-3 pt-2 pb-1 flex gap-2 overflow-x-auto flex-shrink-0 border-b border-gray-100">
            {[
              { key: "",        label: "All" },
              { key: "budget",  label: "≤₹800" },
              { key: "mid",     label: "≤₹3000" },
              { key: "premium", label: "≤₹8000" },
              { key: "luxury",  label: "Luxury" },
            ].map(b => (
              <button key={b.key}
                onClick={() => setRefinements(r => ({ ...r, budget: b.key || undefined }))}
                className={`flex-shrink-0 text-xs px-2.5 py-1 rounded-full border transition-all
                  ${(refinements.budget || "") === b.key
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "border-gray-200 text-gray-500 hover:border-indigo-400 hover:text-indigo-600"}`}>
                {b.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 bg-gray-50/40">
            {messages.map(msg => (
              <ChatMessage
                key={msg._id}
                msg={msg}
                onChip={occ => send(occ.label)}
                onProduct={p => { setOpen(false); navigate(`/product/${p.id}`); }}
                onRefine={label => send(label)}
              />
            ))}
            {loading && <Typing />}
            <div ref={bottomRef} />
          </div>

          {/* Suggestion chips */}
          <div className="px-3 pt-2 pb-1 flex gap-2 overflow-x-auto flex-shrink-0 border-t border-gray-100">
            {SUGGESTIONS.map(s => (
              <button key={s} onClick={() => send(s)} disabled={loading}
                className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full border border-gray-300 text-gray-600 hover:border-indigo-400 hover:bg-indigo-50 hover:text-indigo-700 transition-all disabled:opacity-40 whitespace-nowrap">
                {s}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="px-3 py-3 border-t border-gray-100 bg-white flex-shrink-0">
            <div className="flex gap-2 items-end">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder='Try "job interview" or "jeans under ₹2000"'
                rows={1}
                disabled={loading}
                className="flex-1 resize-none text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent bg-gray-50 placeholder-gray-400 disabled:opacity-50"
                style={{ maxHeight: "100px" }}
              />
              <button
                onClick={() => send()}
                disabled={loading || !input.trim()}
                className="w-10 h-10 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 text-white rounded-xl flex items-center justify-center transition-colors flex-shrink-0">
                {loading
                  ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  : <svg className="w-4 h-4 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                }
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-1.5">Enter to send</p>
          </div>
        </div>
      )}
    </>
  );
}