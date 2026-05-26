import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const BASE = "https://ai-product-recommendation-system-by60.onrender.com";
const API = axios.create({ baseURL: BASE });

const FONT_DISPLAY = "'Playfair Display', serif";
const FONT_BODY = "'DM Sans', sans-serif";

function Avatar({ name, email, size = 80 }) {
  const initials = name
    ? name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : (email || "?")[0].toUpperCase();
  return (
    <div
      style={{
        width: size, height: size, borderRadius: "50%",
        background: "linear-gradient(135deg, #F5C518 0%, #e6b800 100%)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: FONT_DISPLAY, fontSize: size * 0.36, fontWeight: 900,
        color: "#111", flexShrink: 0,
        boxShadow: "0 4px 20px rgba(245,197,24,0.35)",
      }}
    >
      {initials}
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: "#fff", border: "1.5px solid #f0f0ee",
      borderRadius: 16, padding: "20px 18px",
      display: "flex", flexDirection: "column", gap: 8,
      flex: "1 1 140px", minWidth: 120,
      transition: "transform 0.2s, box-shadow 0.2s",
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.07)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
    >
      <span style={{ fontSize: 22 }}>{icon}</span>
      <p style={{ fontSize: 26, fontWeight: 900, color: color || "#111", margin: 0, fontFamily: FONT_DISPLAY }}>{value}</p>
      <p style={{ fontSize: 12, color: "#999", margin: 0, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</p>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "10px 14px", borderRadius: 10, border: "none",
        background: active ? "#111" : "transparent",
        color: active ? "#F5C518" : "#666",
        fontFamily: FONT_BODY, fontSize: 14, fontWeight: 600,
        cursor: "pointer", width: "100%", textAlign: "left",
        transition: "all 0.15s",
      }}
      onMouseEnter={e => { if (!active) { e.currentTarget.style.background = "#f8f8f6"; e.currentTarget.style.color = "#111"; } }}
      onMouseLeave={e => { if (!active) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#666"; } }}
    >
      <span style={{ fontSize: 18 }}>{icon}</span>
      {label}
    </button>
  );
}

function OrderRow({ order, idx }) {
  const statusColor = {
    delivered: { bg: "#f0fdf4", color: "#166534" },
    processing: { bg: "#fffbeb", color: "#92400e" },
    cancelled: { bg: "#fff1f2", color: "#be123c" },
  }[order.status] || { bg: "#f3f3f0", color: "#555" };

  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "14px 0", borderBottom: "1px solid #f3f3f0",
      gap: 12, flexWrap: "wrap",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: "#f8f8f6", display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 20, flexShrink: 0,
        }}>
          {["👟","👔","⌚","👖","🧥"][idx % 5]}
        </div>
        <div>
          <p style={{ margin: 0, fontWeight: 700, fontSize: 14, color: "#111" }}>{order.name}</p>
          <p style={{ margin: 0, fontSize: 12, color: "#aaa" }}>{order.date}</p>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ fontWeight: 900, fontSize: 16, color: "#ef4444" }}>₹{order.price}</span>
        <span style={{
          ...statusColor, padding: "3px 10px",
          borderRadius: 50, fontSize: 11, fontWeight: 700,
        }}>
          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
        </span>
      </div>
    </div>
  );
}

const MOCK_ORDERS = [
  { name: "Running Sneakers – Nike",       price: "2,999", date: "22 May 2026", status: "delivered" },
  { name: "Minimalist Steel Watch",        price: "5,999", date: "15 May 2026", status: "delivered" },
  { name: "Classic Hoodie – H&M",          price: "1,799", date: "8 May 2026",  status: "processing" },
  { name: "Oxford Button-Down – Zara",     price: "1,899", date: "1 May 2026",  status: "delivered" },
  { name: "Relaxed Fit Jeans – Levi's",   price: "2,199", date: "20 Apr 2026", status: "cancelled" },
];

const PREF_OPTIONS = {
  gender:     [["unisex","Unisex"],["male","Male"],["female","Female"]],
  age_group:  [["teen","Teen"],["young_adult","Young Adult"],["adult","Adult"],["senior","Senior"]],
  style:      [["casual","Casual"],["formal","Formal"],["sporty","Sporty"],["traditional","Traditional"],["mixed","Mixed"]],
  budget_range:[["budget","Budget"],["mid","Mid-range"],["premium","Premium"],["luxury","Luxury"]],
};

export default function Profile() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({ cart: 0, wishlist: 0, orders: MOCK_ORDERS.length });
  const [prefs, setPrefs] = useState({ gender: "unisex", age_group: "young_adult", style: "mixed", budget_range: "mid", preferred_categories: "", preferred_brands: "" });
  const [prefsSaved, setPrefsSaved] = useState(false);
  const [prefsEditing, setPrefsEditing] = useState(false);
  const [toast, setToast] = useState("");

  const token = localStorage.getItem("token");

  // inject fonts
  useEffect(() => {
    if (!document.getElementById("rv-profile-fonts")) {
      const link = document.createElement("link");
      link.id = "rv-profile-fonts"; link.rel = "stylesheet";
      link.href = "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap";
      document.head.appendChild(link);
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored || !token) { navigate("/login"); return; }
    setUser(JSON.parse(stored));

    const headers = { Authorization: `Bearer ${token}` };
    API.get("/api/cart", { headers }).then(r => setStats(s => ({ ...s, cart: r.data.count || 0 }))).catch(() => {});
    API.get("/api/wishlist", { headers }).then(r => setStats(s => ({ ...s, wishlist: r.data.count || 0 }))).catch(() => {});
    API.get("/api/user-preferences", { headers }).then(r => {
      if (r.data) setPrefs(p => ({ ...p, ...r.data }));
    }).catch(() => {});
  }, []);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 2500); };

  const handleSavePrefs = async () => {
    try {
      await API.post("/api/user-preferences", prefs, { headers: { Authorization: `Bearer ${token}` } });
      setPrefsSaved(true); setPrefsEditing(false);
      showToast("✓ Preferences saved!");
      setTimeout(() => setPrefsSaved(false), 3000);
    } catch {
      showToast("Failed to save preferences");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token"); localStorage.removeItem("user");
    navigate("/login");
  };

  if (!user) return null;

  const joinDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })
    : "2026";

  const TABS = [
    { key: "overview",    label: "Overview",     icon: "🏠" },
    { key: "orders",      label: "Order History", icon: "📦" },
    { key: "preferences", label: "Style Profile", icon: "✨" },
    { key: "settings",    label: "Settings",      icon: "⚙️" },
  ];

  return (
    <div style={{ fontFamily: FONT_BODY, minHeight: "100vh", background: "#fafaf8" }}>

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 9999,
          background: "#111", color: "#fff", padding: "12px 22px",
          borderRadius: 50, fontSize: 13, fontWeight: 700,
          boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
          animation: "fadeIn 0.2s ease",
        }}>
          {toast}
        </div>
      )}
      <style>{`@keyframes fadeIn { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:none} }`}</style>

      {/* ── NAVBAR ── */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(255,255,255,0.97)", backdropFilter: "blur(8px)",
        borderBottom: "1px solid #f0f0ee",
        padding: "14px 40px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <Link to="/" style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 900, color: "#111", textDecoration: "none" }}>
          RecoVibe<span style={{ color: "#F5C518" }}>.</span>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#aaa" }}>
          <Link to="/" style={{ color: "#aaa", textDecoration: "none", fontWeight: 600 }}>Home</Link>
          <span>/</span>
          <span style={{ color: "#111", fontWeight: 700 }}>My Profile</span>
        </div>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link to="/cart" style={{ fontSize: 13, fontWeight: 700, color: "#111", textDecoration: "none" }}>🛒 Cart</Link>
          <Link to="/wishlist" style={{ fontSize: 13, fontWeight: 700, color: "#111", textDecoration: "none" }}>❤️ Wishlist</Link>
          <Link to="/" style={{ fontSize: 13, fontWeight: 600, color: "#999", textDecoration: "none" }}>← Shop</Link>
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px", display: "grid", gridTemplateColumns: "220px 1fr", gap: 28 }}>

        {/* ── SIDEBAR ── */}
        <aside>
          {/* Profile card */}
          <div style={{
            background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20,
            padding: "28px 20px", textAlign: "center", marginBottom: 14,
          }}>
            <Avatar name={user.name} email={user.email} size={72} />
            <h2 style={{ fontFamily: FONT_DISPLAY, fontSize: 17, fontWeight: 900, color: "#111", margin: "14px 0 3px" }}>
              {user.name || "User"}
            </h2>
            <p style={{ fontSize: 12, color: "#aaa", margin: "0 0 4px" }}>{user.email}</p>
            {user.role === "admin" && (
              <span style={{ display: "inline-block", background: "#111", color: "#F5C518", fontSize: 10, fontWeight: 800, padding: "3px 10px", borderRadius: 50, letterSpacing: "0.1em", textTransform: "uppercase", marginTop: 6 }}>
                Admin
              </span>
            )}
            <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid #f3f3f0" }}>
              <p style={{ fontSize: 11, color: "#bbb", margin: 0, fontWeight: 600 }}>Member since {joinDate}</p>
            </div>
          </div>

          {/* Nav */}
          <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 16, padding: "10px 8px" }}>
            {TABS.map(t => (
              <NavItem key={t.key} icon={t.icon} label={t.label} active={activeTab === t.key} onClick={() => setActiveTab(t.key)} />
            ))}
            <div style={{ borderTop: "1px solid #f3f3f0", marginTop: 6, paddingTop: 6 }}>
              {user.role === "admin" && (
                <NavItem icon="🔧" label="Admin Panel" onClick={() => navigate("/admin")} />
              )}
              <NavItem icon="🛍️" label="Continue Shopping" onClick={() => navigate("/")} />
            </div>
            <div style={{ borderTop: "1px solid #f3f3f0", marginTop: 6, paddingTop: 6 }}>
              <button
                onClick={handleLogout}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "10px 14px", borderRadius: 10, border: "none",
                  background: "transparent", color: "#ef4444",
                  fontFamily: FONT_BODY, fontSize: 14, fontWeight: 600,
                  cursor: "pointer", width: "100%", textAlign: "left",
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#fff1f2"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
              >
                <span style={{ fontSize: 18 }}>🚪</span>
                Sign Out
              </button>
            </div>
          </div>
        </aside>

        {/* ── MAIN PANEL ── */}
        <main>

          {/* ── OVERVIEW TAB ── */}
          {activeTab === "overview" && (
            <div>
              {/* Header */}
              <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontFamily: FONT_DISPLAY, fontSize: 28, fontWeight: 900, color: "#111", margin: "0 0 4px" }}>
                  Welcome back, {(user.name || "there").split(" ")[0]}! 👋
                </h1>
                <p style={{ fontSize: 14, color: "#aaa", margin: 0 }}>Here's a snapshot of your account</p>
              </div>

              {/* Stats */}
              <div style={{ display: "flex", gap: 14, marginBottom: 24, flexWrap: "wrap" }}>
                <StatCard icon="🛒" label="Items in cart"     value={stats.cart}     color="#111" />
                <StatCard icon="❤️" label="Wishlist saves"    value={stats.wishlist} color="#ef4444" />
                <StatCard icon="📦" label="Total orders"      value={stats.orders}   color="#111" />
                <StatCard icon="⭐" label="Avg. rating given" value="4.8"            color="#F5C518" />
              </div>

              {/* Recent orders preview */}
              <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20, padding: "24px 26px", marginBottom: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h3 style={{ fontFamily: FONT_DISPLAY, fontSize: 18, fontWeight: 900, color: "#111", margin: 0 }}>Recent Orders</h3>
                  <button onClick={() => setActiveTab("orders")} style={{
                    background: "none", border: "none", color: "#F5C518", fontWeight: 700,
                    fontSize: 13, cursor: "pointer", fontFamily: FONT_BODY,
                  }}>
                    View all →
                  </button>
                </div>
                {MOCK_ORDERS.slice(0, 3).map((o, i) => <OrderRow key={i} order={o} idx={i} />)}
              </div>

              {/* Quick links */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                {[
                  { icon: "❤️", label: "Saved",        sub: `${stats.wishlist} items saved`, href: "/wishlist", bg: "#fff1f2" },
                  { icon: "🛒", label: "Cart",          sub: `${stats.cart} items pending`,  href: "/cart",     bg: "#f0f9ff" },
                  { icon: "✨", label: "Style Profile", sub: "Update your preferences",      tab: "preferences", bg: "#fffbeb" },
                  { icon: "📦", label: "Order History", sub: "Track all your orders",        tab: "orders",      bg: "#f0fdf4" },
                ].map((card) => (
                  <div
                    key={card.label}
                    onClick={() => card.href ? navigate(card.href) : setActiveTab(card.tab)}
                    style={{
                      background: card.bg, borderRadius: 16, padding: "20px 18px",
                      cursor: "pointer", display: "flex", alignItems: "center", gap: 14,
                      border: "1.5px solid transparent", transition: "all 0.2s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.07)"; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
                  >
                    <span style={{ fontSize: 26 }}>{card.icon}</span>
                    <div>
                      <p style={{ fontWeight: 800, fontSize: 14, color: "#111", margin: "0 0 2px" }}>{card.label}</p>
                      <p style={{ fontSize: 12, color: "#888", margin: 0 }}>{card.sub}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── ORDERS TAB ── */}
          {activeTab === "orders" && (
            <div>
              <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontFamily: FONT_DISPLAY, fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 4px" }}>Order History</h1>
                <p style={{ fontSize: 14, color: "#aaa", margin: 0 }}>{MOCK_ORDERS.length} total orders</p>
              </div>
              <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20, padding: "24px 26px" }}>
                {MOCK_ORDERS.map((o, i) => <OrderRow key={i} order={o} idx={i} />)}
              </div>
            </div>
          )}

          {/* ── PREFERENCES TAB ── */}
          {activeTab === "preferences" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
                <div>
                  <h1 style={{ fontFamily: FONT_DISPLAY, fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 4px" }}>Style Profile</h1>
                  <p style={{ fontSize: 14, color: "#aaa", margin: 0 }}>Your preferences shape your AI recommendations</p>
                </div>
                {!prefsEditing && (
                  <button onClick={() => setPrefsEditing(true)} style={{
                    background: "#111", color: "#fff", border: "none",
                    borderRadius: 50, padding: "10px 22px", fontSize: 13, fontWeight: 700,
                    cursor: "pointer", transition: "all 0.2s",
                  }}
                    onMouseEnter={e => { e.currentTarget.style.background = "#F5C518"; e.currentTarget.style.color = "#111"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "#111"; e.currentTarget.style.color = "#fff"; }}
                  >
                    ✏️ Edit
                  </button>
                )}
              </div>

              <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20, padding: "28px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
                  {Object.entries(PREF_OPTIONS).map(([key, options]) => (
                    <div key={key}>
                      <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
                        {key.replace("_", " ")}
                      </label>
                      {prefsEditing ? (
                        <select
                          value={prefs[key]}
                          onChange={e => setPrefs(p => ({ ...p, [key]: e.target.value }))}
                          style={{
                            width: "100%", padding: "10px 14px", borderRadius: 10,
                            border: "2px solid #f0f0ee", fontSize: 14, fontFamily: FONT_BODY,
                            outline: "none", cursor: "pointer", background: "#fff",
                          }}
                          onFocus={e => e.target.style.borderColor = "#F5C518"}
                          onBlur={e => e.target.style.borderColor = "#f0f0ee"}
                        >
                          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                      ) : (
                        <p style={{
                          margin: 0, padding: "10px 14px", borderRadius: 10,
                          background: "#fafaf8", fontSize: 14, fontWeight: 600, color: "#111",
                          border: "1.5px solid #f3f3f0",
                        }}>
                          {options.find(([v]) => v === prefs[key])?.[1] || prefs[key]}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Free text fields */}
                {["preferred_categories", "preferred_brands"].map((key) => (
                  <div key={key} style={{ marginBottom: 16 }}>
                    <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
                      {key === "preferred_categories" ? "Favourite Categories" : "Favourite Brands"}
                    </label>
                    {prefsEditing ? (
                      <input
                        type="text"
                        value={prefs[key]}
                        onChange={e => setPrefs(p => ({ ...p, [key]: e.target.value }))}
                        placeholder={key === "preferred_categories" ? "e.g. Shirts, Jeans, Watches" : "e.g. Nike, Zara, Levi's"}
                        style={{
                          width: "100%", padding: "10px 14px", borderRadius: 10,
                          border: "2px solid #f0f0ee", fontSize: 14, fontFamily: FONT_BODY,
                          outline: "none", boxSizing: "border-box",
                        }}
                        onFocus={e => e.target.style.borderColor = "#F5C518"}
                        onBlur={e => e.target.style.borderColor = "#f0f0ee"}
                      />
                    ) : (
                      <p style={{
                        margin: 0, padding: "10px 14px", borderRadius: 10,
                        background: "#fafaf8", fontSize: 14, fontWeight: 600, color: prefs[key] ? "#111" : "#ccc",
                        border: "1.5px solid #f3f3f0",
                      }}>
                        {prefs[key] || "Not set"}
                      </p>
                    )}
                  </div>
                ))}

                {prefsEditing && (
                  <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
                    <button onClick={handleSavePrefs} style={{
                      flex: 1, padding: "12px", background: "#111", color: "#fff",
                      border: "none", borderRadius: 50, fontSize: 14, fontWeight: 700,
                      cursor: "pointer", transition: "all 0.2s",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.background = "#F5C518"; e.currentTarget.style.color = "#111"; }}
                      onMouseLeave={e => { e.currentTarget.style.background = "#111"; e.currentTarget.style.color = "#fff"; }}
                    >
                      Save Changes
                    </button>
                    <button onClick={() => setPrefsEditing(false)} style={{
                      padding: "12px 24px", background: "none", border: "2px solid #f0f0ee",
                      borderRadius: 50, fontSize: 14, fontWeight: 700, color: "#888",
                      cursor: "pointer",
                    }}>
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── SETTINGS TAB ── */}
          {activeTab === "settings" && (
            <div>
              <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontFamily: FONT_DISPLAY, fontSize: 26, fontWeight: 900, color: "#111", margin: "0 0 4px" }}>Settings</h1>
                <p style={{ fontSize: 14, color: "#aaa", margin: 0 }}>Manage your account details</p>
              </div>

              {/* Account info */}
              <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20, padding: "28px", marginBottom: 16 }}>
                <h3 style={{ fontFamily: FONT_DISPLAY, fontSize: 16, fontWeight: 900, color: "#111", margin: "0 0 20px" }}>Account Information</h3>
                {[
                  { label: "Full Name",  value: user.name  || "—", icon: "👤" },
                  { label: "Email",      value: user.email || "—", icon: "✉️" },
                  { label: "Role",       value: user.role  || "user", icon: "🔑" },
                  { label: "Member Since", value: joinDate, icon: "📅" },
                ].map(row => (
                  <div key={row.label} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "14px 0", borderBottom: "1px solid #f3f3f0",
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 18 }}>{row.icon}</span>
                      <span style={{ fontSize: 13, color: "#888", fontWeight: 600 }}>{row.label}</span>
                    </div>
                    <span style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>{row.value}</span>
                  </div>
                ))}
              </div>

              {/* Quick actions */}
              <div style={{ background: "#fff", border: "1.5px solid #f0f0ee", borderRadius: 20, padding: "28px", marginBottom: 16 }}>
                <h3 style={{ fontFamily: FONT_DISPLAY, fontSize: 16, fontWeight: 900, color: "#111", margin: "0 0 16px" }}>Quick Actions</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  {[
                    { label: "Go to Cart",    icon: "🛒", action: () => navigate("/cart"),    bg: "#f0f9ff" },
                    { label: "My Wishlist",   icon: "❤️", action: () => navigate("/wishlist"), bg: "#fff1f2" },
                    { label: "Style Profile", icon: "✨", action: () => setActiveTab("preferences"), bg: "#fffbeb" },
                    ...(user.role === "admin" ? [{ label: "Admin Panel", icon: "🔧", action: () => navigate("/admin"), bg: "#f3f4f6" }] : []),
                  ].map(btn => (
                    <button key={btn.label} onClick={btn.action} style={{
                      background: btn.bg, border: "none", borderRadius: 12,
                      padding: "14px 16px", cursor: "pointer", display: "flex",
                      alignItems: "center", gap: 10, fontFamily: FONT_BODY,
                      fontSize: 14, fontWeight: 700, color: "#111",
                      transition: "all 0.15s",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.07)"; }}
                      onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
                    >
                      <span style={{ fontSize: 20 }}>{btn.icon}</span>
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Danger zone */}
              <div style={{ background: "#fff", border: "1.5px solid #fee2e2", borderRadius: 20, padding: "24px 28px" }}>
                <h3 style={{ fontFamily: FONT_DISPLAY, fontSize: 16, fontWeight: 900, color: "#be123c", margin: "0 0 12px" }}>Danger Zone</h3>
                <p style={{ fontSize: 13, color: "#aaa", margin: "0 0 16px" }}>These actions are permanent and cannot be undone.</p>
                <button onClick={handleLogout} style={{
                  background: "none", border: "2px solid #fee2e2", borderRadius: 50,
                  padding: "10px 24px", fontSize: 13, fontWeight: 700, color: "#be123c",
                  cursor: "pointer", transition: "all 0.15s", fontFamily: FONT_BODY,
                }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#fff1f2"; e.currentTarget.style.borderColor = "#ef4444"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "none"; e.currentTarget.style.borderColor = "#fee2e2"; }}
                >
                  Sign Out of Account
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}