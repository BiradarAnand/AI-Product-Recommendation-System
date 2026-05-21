// src/pages/Admin.jsx
// Full admin dashboard — product management, user management, analytics

import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const BASE = "https://ai-product-recommendation-system-by60.onrender.com";
const API  = axios.create({ baseURL: BASE });

// ── Small reusable components ──────────────────────────────────────────────

function StatCard({ icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-3">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: color + "20", color }}>
          Live
        </span>
      </div>
      <p className="text-3xl font-black text-gray-900">{value}</p>
      <p className="text-sm font-semibold text-gray-700 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function SectionHeader({ title, sub }) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-black text-gray-900">{title}</h2>
      {sub && <p className="text-sm text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

// ── TABS ──────────────────────────────────────────────────────────────────

const TABS = [
  { key: "overview",  label: "Overview",  icon: "📊" },
  { key: "products",  label: "Products",  icon: "📦" },
  { key: "users",     label: "Users",     icon: "👥" },
  { key: "analytics", label: "Analytics", icon: "📈" },
];

// ── MAIN ──────────────────────────────────────────────────────────────────

export default function Admin() {
  const navigate  = useNavigate();
  const [tab, setTab]             = useState("overview");
  const [stats, setStats]         = useState(null);
  const [products, setProducts]   = useState([]);
  const [users, setUsers]         = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");
  const [toast, setToast]         = useState("");

  // Product form state
  const [showProductForm, setShowProductForm] = useState(false);
  const [editProduct, setEditProduct]         = useState(null);
  const [form, setForm] = useState({ name: "", brand: "", category: "", price: "", stock: "", rating: "4.0", description: "", image_url: "" });

  const token   = localStorage.getItem("token");
  const user    = JSON.parse(localStorage.getItem("user") || "null");
  const headers = { Authorization: `Bearer ${token}` };

  // ── Auth guard ──
  useEffect(() => {
    if (!token || user?.role !== "admin") {
      navigate("/login");
    }
  }, []);

  // ── Load data ──
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [statsRes, productsRes, usersRes] = await Promise.allSettled([
          API.get("/api/admin/stats", { headers }),
          API.get("/products", { headers }),
          API.get("/api/admin/users", { headers }),
        ]);

        if (statsRes.status === "fulfilled")    setStats(statsRes.value.data);
        if (productsRes.status === "fulfilled") setProducts(productsRes.value.data || []);
        if (usersRes.status === "fulfilled")    setUsers(usersRes.value.data?.users || usersRes.value.data || []);

        // Analytics from stats
        try {
          const aRes = await API.get("/api/admin/analytics", { headers });
          setAnalytics(aRes.data);
        } catch {}

      } catch (e) {
        setError("Failed to load some admin data. Check your connection.");
      } finally {
        setLoading(false);
      }
    };
    if (token && user?.role === "admin") load();
  }, []);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  // ── Product CRUD ──
  const handleProductSave = async () => {
    try {
      if (editProduct) {
        await API.put(`/api/admin/products/${editProduct.id}`, form, { headers });
        showToast("Product updated successfully!");
      } else {
        await API.post("/api/admin/products", form, { headers });
        showToast("Product added successfully!");
      }
      const res = await API.get("/products", { headers });
      setProducts(res.data || []);
      setShowProductForm(false);
      setEditProduct(null);
      setForm({ name: "", brand: "", category: "", price: "", stock: "", rating: "4.0", description: "", image_url: "" });
    } catch {
      showToast("❌ Failed to save product. Check all fields.");
    }
  };

  const handleProductDelete = async (id) => {
    if (!window.confirm("Delete this product permanently?")) return;
    try {
      await API.delete(`/api/admin/products/${id}`, { headers });
      setProducts(prev => prev.filter(p => p.id !== id));
      showToast("Product deleted.");
    } catch {
      showToast("❌ Delete failed.");
    }
  };

  const openEditForm = (product) => {
    setEditProduct(product);
    setForm({
      name: product.name || "", brand: product.brand || "",
      category: product.category || "", price: product.price || "",
      stock: product.stock || "", rating: product.rating || "4.0",
      description: product.description || "", image_url: product.image_url || "",
    });
    setShowProductForm(true);
  };

  // ── User management ──
  const handleBlockUser = async (userId, currentStatus) => {
    try {
      await API.patch(`/api/admin/users/${userId}/block`, { blocked: !currentStatus }, { headers });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, blocked: !currentStatus } : u));
      showToast(currentStatus ? "User unblocked." : "User blocked.");
    } catch {
      showToast("❌ Action failed.");
    }
  };

  // ── Derived stats (fallback to products array if API stats unavailable) ──
  const totalProducts  = stats?.total_products  ?? products.length;
  const totalUsers     = stats?.total_users     ?? users.length;
  const totalSearches  = stats?.total_searches  ?? "—";
  const totalWishlists = stats?.total_wishlists ?? "—";

  // ── RENDER ──
  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-500 text-sm">Loading admin panel…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "'DM Sans', sans-serif" }}>

      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 px-5 py-3 bg-gray-900 text-white text-sm font-semibold rounded-xl shadow-lg transition-all">
          {toast}
        </div>
      )}

      {/* ── TOP NAV ── */}
      <nav className="sticky top-0 z-40 bg-white shadow-sm px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-2xl font-black text-gray-900" style={{ fontFamily: "'Playfair Display', serif" }}>
            RecoVibe<span className="text-yellow-400">.</span>
          </Link>
          <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs font-bold rounded-full">ADMIN</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">Logged in as <strong className="text-gray-900">{user?.name || user?.email}</strong></span>
          <Link to="/" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">← Back to Site</Link>
          <button
            onClick={() => { localStorage.removeItem("token"); localStorage.removeItem("user"); navigate("/login"); }}
            className="text-sm font-semibold text-red-500 hover:text-red-700 transition-colors"
          >
            Logout
          </button>
        </div>
      </nav>

      <div className="flex">
        {/* ── SIDEBAR ── */}
        <aside className="w-56 min-h-screen bg-white border-r border-gray-100 pt-6 px-4 flex-shrink-0">
          <p className="text-xs font-bold uppercase tracking-widest text-gray-400 px-3 mb-3">Navigation</p>
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold mb-1 transition-all ${
                tab === t.key
                  ? "bg-gray-900 text-white"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </aside>

        {/* ── MAIN ── */}
        <main className="flex-1 p-8">

          {error && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-800 text-sm">
              ⚠ {error}
            </div>
          )}

          {/* ── OVERVIEW TAB ── */}
          {tab === "overview" && (
            <div>
              <SectionHeader title="Dashboard Overview" sub="Live stats across your platform" />
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                <StatCard icon="📦" label="Total Products"  value={totalProducts}  color="#2563EB" />
                <StatCard icon="👥" label="Registered Users" value={totalUsers}    color="#16A34A" />
                <StatCard icon="🔍" label="Total Searches"  value={totalSearches}  color="#F59E0B" />
                <StatCard icon="❤️" label="Wishlist Saves"  value={totalWishlists} color="#EF4444" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent products */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Latest Products</h3>
                  <div className="space-y-3">
                    {products.slice(0, 5).map(p => (
                      <div key={p.id} className="flex items-center gap-3 text-sm">
                        <div className="w-10 h-10 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                          <img src={p.image_url?.startsWith("http") ? p.image_url : `${BASE}/${p.image_url}`} alt={p.name}
                            className="w-full h-full object-contain p-1"
                            onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=80"; }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 truncate">{p.name}</p>
                          <p className="text-gray-400 text-xs">{p.brand} · {p.category}</p>
                        </div>
                        <span className="font-bold text-red-500 flex-shrink-0">₹{p.price}</span>
                      </div>
                    ))}
                  </div>
                  <button onClick={() => setTab("products")} className="mt-4 text-sm text-indigo-600 font-semibold hover:underline">
                    View all products →
                  </button>
                </div>

                {/* Recent users */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Recent Users</h3>
                  {users.length === 0 ? (
                    <p className="text-gray-400 text-sm">No user data available from backend yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {users.slice(0, 5).map(u => (
                        <div key={u.id} className="flex items-center gap-3 text-sm">
                          <div className="w-9 h-9 rounded-full bg-yellow-400 flex items-center justify-center font-black text-gray-900 text-sm flex-shrink-0">
                            {(u.name || u.email || "?")[0].toUpperCase()}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-gray-900 truncate">{u.name || "—"}</p>
                            <p className="text-gray-400 text-xs truncate">{u.email}</p>
                          </div>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${u.blocked ? "bg-red-100 text-red-600" : "bg-green-100 text-green-600"}`}>
                            {u.blocked ? "Blocked" : "Active"}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  <button onClick={() => setTab("users")} className="mt-4 text-sm text-indigo-600 font-semibold hover:underline">
                    Manage users →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── PRODUCTS TAB ── */}
          {tab === "products" && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <SectionHeader title="Product Management" sub={`${products.length} products in database`} />
                <button
                  onClick={() => { setEditProduct(null); setForm({ name:"", brand:"", category:"", price:"", stock:"", rating:"4.0", description:"", image_url:"" }); setShowProductForm(true); }}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white text-sm font-bold rounded-xl hover:bg-yellow-400 hover:text-gray-900 transition-colors"
                >
                  + Add Product
                </button>
              </div>

              {/* Product form modal */}
              {showProductForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.5)" }}>
                  <div className="bg-white rounded-3xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
                    <h3 className="text-xl font-black text-gray-900 mb-6">{editProduct ? "Edit Product" : "Add New Product"}</h3>
                    <div className="space-y-4">
                      {[
                        ["name", "Product Name", "text"],
                        ["brand", "Brand", "text"],
                        ["category", "Category (e.g. Shirts, Jeans)", "text"],
                        ["price", "Price (₹)", "number"],
                        ["stock", "Stock Quantity", "number"],
                        ["rating", "Rating (0-5)", "number"],
                        ["image_url", "Image URL", "text"],
                      ].map(([key, label, type]) => (
                        <div key={key}>
                          <label className="block text-sm font-semibold text-gray-700 mb-1">{label}</label>
                          <input
                            type={type}
                            value={form[key]}
                            onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
                            className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                            style={{ border: "2px solid #e5e7eb" }}
                            onFocus={e => e.target.style.borderColor = "#F5C518"}
                            onBlur={e => e.target.style.borderColor = "#e5e7eb"}
                          />
                        </div>
                      ))}
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">Description</label>
                        <textarea
                          rows={3}
                          value={form.description}
                          onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                          className="w-full px-4 py-2.5 rounded-xl text-sm outline-none resize-none"
                          style={{ border: "2px solid #e5e7eb" }}
                          onFocus={e => e.target.style.borderColor = "#F5C518"}
                          onBlur={e => e.target.style.borderColor = "#e5e7eb"}
                        />
                      </div>
                    </div>
                    <div className="flex gap-3 mt-6">
                      <button onClick={handleProductSave}
                        className="flex-1 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-yellow-400 hover:text-gray-900 transition-colors">
                        {editProduct ? "Save Changes" : "Add Product"}
                      </button>
                      <button onClick={() => { setShowProductForm(false); setEditProduct(null); }}
                        className="px-5 py-3 border-2 border-gray-200 text-gray-700 font-bold rounded-xl hover:border-gray-900 transition-colors">
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Products table */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-100">
                        {["#", "Image", "Name", "Brand", "Category", "Price", "Stock", "Rating", "Actions"].map(h => (
                          <th key={h} className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wider text-gray-500">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {products.map((p, i) => (
                        <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 text-gray-400 text-xs">{p.id}</td>
                          <td className="px-4 py-3">
                            <div className="w-10 h-10 rounded-lg bg-gray-100 overflow-hidden">
                              <img src={p.image_url?.startsWith("http") ? p.image_url : `${BASE}/${p.image_url}`} alt={p.name}
                                className="w-full h-full object-contain p-1"
                                onError={e => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=80"; }} />
                            </div>
                          </td>
                          <td className="px-4 py-3 font-semibold text-gray-900 max-w-[180px] truncate">{p.name}</td>
                          <td className="px-4 py-3 text-gray-600">{p.brand}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold">{p.category}</span>
                          </td>
                          <td className="px-4 py-3 font-bold text-red-500">₹{p.price}</td>
                          <td className="px-4 py-3 text-gray-600">{p.stock}</td>
                          <td className="px-4 py-3 text-yellow-500 font-bold">★ {Number(p.rating).toFixed(1)}</td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <button onClick={() => openEditForm(p)}
                                className="px-2 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-lg hover:bg-blue-100 transition-colors">
                                Edit
                              </button>
                              <button onClick={() => handleProductDelete(p.id)}
                                className="px-2 py-1 bg-red-50 text-red-600 text-xs font-bold rounded-lg hover:bg-red-100 transition-colors">
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── USERS TAB ── */}
          {tab === "users" && (
            <div>
              <SectionHeader title="User Management" sub={`${users.length} registered users`} />
              {users.length === 0 ? (
                <div className="bg-white rounded-2xl p-12 text-center shadow-sm">
                  <p className="text-4xl mb-4">👥</p>
                  <p className="text-gray-500 text-sm">No user data returned from backend yet.</p>
                  <p className="text-gray-400 text-xs mt-2">Make sure GET /api/admin/users route exists and returns an array.</p>
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                          {["#", "Name", "Email", "Joined", "Status", "Actions"].map(h => (
                            <th key={h} className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wider text-gray-500">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {users.map(u => (
                          <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                            <td className="px-4 py-3 text-gray-400 text-xs">{u.id}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-full bg-yellow-400 flex items-center justify-center font-black text-gray-900 text-xs flex-shrink-0">
                                  {(u.name || u.email || "?")[0].toUpperCase()}
                                </div>
                                <span className="font-semibold text-gray-900">{u.name || "—"}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600">{u.email}</td>
                            <td className="px-4 py-3 text-gray-400 text-xs">{u.created_at ? new Date(u.created_at).toLocaleDateString("en-IN") : "—"}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${u.blocked ? "bg-red-100 text-red-600" : "bg-green-100 text-green-700"}`}>
                                {u.blocked ? "Blocked" : "Active"}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => handleBlockUser(u.id, u.blocked)}
                                className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                                  u.blocked
                                    ? "bg-green-50 text-green-700 hover:bg-green-100"
                                    : "bg-red-50 text-red-600 hover:bg-red-100"
                                }`}
                              >
                                {u.blocked ? "Unblock" : "Block"}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── ANALYTICS TAB ── */}
          {tab === "analytics" && (
            <div>
              <SectionHeader title="Platform Analytics" sub="Search trends, top products, and engagement" />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Category distribution */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Products by Category</h3>
                  {(() => {
                    const counts = {};
                    products.forEach(p => { counts[p.category] = (counts[p.category] || 0) + 1; });
                    const sorted = Object.entries(counts).sort((a,b) => b[1]-a[1]);
                    const max = sorted[0]?.[1] || 1;
                    return sorted.length === 0
                      ? <p className="text-gray-400 text-sm">No product data.</p>
                      : sorted.map(([cat, count]) => (
                        <div key={cat} className="mb-3">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-gray-700">{cat}</span>
                            <span className="font-bold text-gray-900">{count}</span>
                          </div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-yellow-400 rounded-full transition-all duration-500"
                              style={{ width: `${(count/max)*100}%` }} />
                          </div>
                        </div>
                      ));
                  })()}
                </div>

                {/* Top rated */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Top Rated Products</h3>
                  <div className="space-y-3">
                    {[...products].sort((a,b) => b.rating - a.rating).slice(0,6).map((p, i) => (
                      <div key={p.id} className="flex items-center gap-3 text-sm">
                        <span className="text-xs font-black text-gray-300 w-5">#{i+1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 truncate">{p.name}</p>
                          <p className="text-xs text-gray-400">{p.brand}</p>
                        </div>
                        <span className="text-yellow-400 font-black text-sm flex-shrink-0">★ {Number(p.rating).toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Most expensive */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Price Range</h3>
                  {(() => {
                    const prices = products.map(p => p.price).filter(Boolean);
                    if (prices.length === 0) return <p className="text-gray-400 text-sm">No data.</p>;
                    const min = Math.min(...prices);
                    const max = Math.max(...prices);
                    const avg = Math.round(prices.reduce((s,v) => s+v, 0) / prices.length);
                    return (
                      <div className="space-y-3">
                        {[["Lowest Price", `₹${min.toLocaleString("en-IN")}`, "text-green-600"],
                          ["Average Price", `₹${avg.toLocaleString("en-IN")}`, "text-blue-600"],
                          ["Highest Price", `₹${max.toLocaleString("en-IN")}`, "text-red-500"]].map(([l,v,c]) => (
                          <div key={l} className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">{l}</span>
                            <span className={`font-black text-lg ${c}`}>{v}</span>
                          </div>
                        ))}
                        <p className="text-xs text-gray-400 mt-2">Based on {prices.length} products</p>
                      </div>
                    );
                  })()}
                </div>

                {/* Backend analytics */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">Backend Analytics</h3>
                  {analytics ? (
                    <pre className="text-xs text-gray-600 bg-gray-50 p-3 rounded-xl overflow-auto max-h-40">
                      {JSON.stringify(analytics, null, 2)}
                    </pre>
                  ) : (
                    <div>
                      <p className="text-gray-400 text-sm mb-2">Analytics API not yet connected.</p>
                      <p className="text-xs text-gray-400">Add this route to Flask: GET /api/admin/analytics</p>
                      <p className="text-xs text-gray-400 mt-1">Return: most_searched, top_viewed, chatbot_count, etc.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}