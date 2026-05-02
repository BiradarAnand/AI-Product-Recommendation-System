import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API = axios.create({ baseURL: "http://localhost:5000/api" });

export default function Login() {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage]   = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [showPass, setShowPass] = useState(false);

  // inject brand fonts once
  if (!document.getElementById("rv-login-fonts")) {
    const link = document.createElement("link");
    link.id   = "rv-login-fonts";
    link.rel  = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap";
    document.head.appendChild(link);
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setMessage(""); setLoading(true);
    try {
      const res = await API.post("/auth/login", { email, password });
      localStorage.setItem("token", res.data.token);
      if (res.data.user) localStorage.setItem("user", JSON.stringify(res.data.user));
      setMessage("Login successful! Redirecting...");
      setTimeout(() => { window.location.href = "/"; }, 1200);
    } catch (err) {
      if (err.response?.status === 403) setError("Account not verified. Check your email.");
      else setError(err.response?.data?.error || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="min-h-screen bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden">

      {/* decorative blobs */}
      <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-10"
        style={{ background: "radial-gradient(circle, #F5C518, transparent)", transform: "translate(30%,-30%)" }} />
      <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full opacity-10"
        style={{ background: "radial-gradient(circle, #F5C518, transparent)", transform: "translate(-30%,30%)" }} />

      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-0 rounded-3xl overflow-hidden shadow-2xl relative z-10">

        {/* ── LEFT PANEL — brand ── */}
        <div className="hidden lg:flex flex-col justify-between p-12 bg-gray-900 relative overflow-hidden">
          <div className="absolute inset-0"
            style={{ background: "linear-gradient(135deg, #111 0%, #1a1a1a 50%, #0a0a0a 100%)" }} />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full opacity-5"
            style={{ background: "#F5C518", transform: "translate(-50%,-50%)", filter: "blur(40px)" }} />

          <div className="relative z-10">
            <a href="/" style={{ fontFamily: "'Playfair Display', serif" }}
              className="text-3xl font-black text-white tracking-tight">
              RecoVibe<span style={{ color: "#F5C518" }}>.</span>
            </a>
          </div>

          <div className="relative z-10">
            <p style={{ color: "#F5C518", fontSize: "12px", letterSpacing: "0.2em" }}
              className="uppercase font-semibold mb-4">Your Style, Personalised</p>
            <h2 style={{ fontFamily: "'Playfair Display', serif" }}
              className="text-4xl font-black text-white leading-tight mb-6">
              Welcome<br />Back to<br />Your Wardrobe.
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Sign in to access personalized outfit recommendations, your wishlist, and exclusive collections curated just for you.
            </p>
          </div>

          <div className="relative z-10 space-y-3">
            {["AI-powered style recommendations", "Curated occasion-based outfits", "Save & track your favourites"].map((f) => (
              <div key={f} className="flex items-center gap-3">
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: "#F5C518", color: "#111" }}>✓</span>
                <span className="text-gray-300 text-sm">{f}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── RIGHT PANEL — form ── */}
        <div className="bg-white flex flex-col justify-center p-10 lg:p-12">

          {/* mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <a href="/" style={{ fontFamily: "'Playfair Display', serif" }}
              className="text-2xl font-black text-gray-900">
              RecoVibe<span style={{ color: "#F5C518" }}>.</span>
            </a>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-1">Sign In</h1>
          <p className="text-gray-400 text-sm mb-8">Enter your credentials to continue</p>

          {message && (
            <div className="mb-5 p-3 rounded-xl text-sm font-medium flex items-center gap-2"
              style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#15803d" }}>
              ✓ {message}
            </div>
          )}
          {error && (
            <div className="mb-5 p-3 rounded-xl text-sm font-medium flex items-center gap-2"
              style={{ background: "#fff1f2", border: "1px solid #fecdd3", color: "#be123c" }}>
              ⚠ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">✉</span>
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm outline-none transition-all"
                  style={{ border: "2px solid #e5e7eb" }}
                  onFocus={(e) => (e.target.style.borderColor = "#F5C518")}
                  onBlur={(e) => (e.target.style.borderColor = "#e5e7eb")}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-semibold text-gray-700">Password</label>
                <a href="#!" className="text-xs font-semibold hover:underline" style={{ color: "#F5C518" }}>
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔒</span>
                <input
                  type={showPass ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-12 py-3 rounded-xl text-sm outline-none transition-all"
                  style={{ border: "2px solid #e5e7eb" }}
                  onFocus={(e) => (e.target.style.borderColor = "#F5C518")}
                  onBlur={(e) => (e.target.style.borderColor = "#e5e7eb")}
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs hover:text-gray-600">
                  {showPass ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: loading ? "#ccc" : "#111", color: "#fff" }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full inline-block"
                    style={{ animation: "spin 0.8s linear infinite" }} />
                  Signing in…
                </span>
              ) : "Sign In →"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-500">
              Don't have an account?{" "}
              <Link to="/register" className="font-bold hover:underline" style={{ color: "#111" }}>
                Create one
              </Link>
            </p>
          </div>

          {/* demo credentials */}
          <div className="mt-4 p-4 rounded-xl text-xs" style={{ background: "#fafafa", border: "1px solid #f0f0f0" }}>
            <p className="font-semibold text-gray-600 mb-1">🧪 Demo Account</p>
            <p className="text-gray-400">demo@example.com / demo123</p>
          </div>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}