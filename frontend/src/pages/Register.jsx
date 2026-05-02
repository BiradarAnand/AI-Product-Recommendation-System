import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API = axios.create({ baseURL: "http://localhost:5000/api" });

const STEPS = [
  { num: 1, key: "form",        title: "Create Account",   desc: "Your basic details" },
  { num: 2, key: "otp",         title: "Verify Email",     desc: "Enter the OTP sent" },
  { num: 3, key: "preferences", title: "Style Profile",    desc: "Personalise your feed" },
];

export default function Register() {
  const [step, setStep] = useState("form");

  const [formData, setFormData] = useState({
    name: "", email: "", password: "",
    otp_channel: "email", // always email — hidden field
  });

  const [otpData, setOtpData] = useState({ user_id: null, otp: "" });

  const [prefs, setPrefs] = useState({
    gender: "unisex", age_group: "young_adult",
    style: "mixed", budget_range: "mid",
    preferred_categories: "", preferred_brands: "",
  });

  const [message, setMessage]   = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [showPass, setShowPass] = useState(false);

  // inject fonts
  if (!document.getElementById("rv-reg-fonts")) {
    const l = document.createElement("link");
    l.id = "rv-reg-fonts"; l.rel = "stylesheet";
    l.href = "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap";
    document.head.appendChild(l);
  }

  const notify = (msg, isErr = false) => {
    if (isErr) { setError(msg); setMessage(""); }
    else       { setMessage(msg); setError(""); }
  };

  // ── Step 1 ──
  const handleFormSubmit = async (e) => {
    e.preventDefault(); setLoading(true); notify("");
    try {
      const res = await API.post("/auth/register", { ...formData, otp_channel: "email" });
      setOtpData({ user_id: res.data.user_id, otp: "" });
      notify("OTP sent to your email. Check your inbox!");
      setStep("otp");
    } catch (err) { notify(err.response?.data?.error || "Registration failed", true); }
    finally { setLoading(false); }
  };

  // ── Step 2 ──
  const handleOtpSubmit = async (e) => {
    e.preventDefault(); setLoading(true); notify("");
    try {
      const res = await API.post("/auth/verify-otp", otpData);
      localStorage.setItem("token", res.data.token);
      if (res.data.user) localStorage.setItem("user", JSON.stringify(res.data.user));
      notify("Email verified! Setting up your style profile…");
      setStep("preferences");
    } catch (err) { notify(err.response?.data?.error || "Invalid OTP", true); }
    finally { setLoading(false); }
  };

  // ── Step 3 ──
  const handlePrefsSubmit = async (e) => {
    e.preventDefault(); setLoading(true); notify("");
    try {
      const token = localStorage.getItem("token");
      await API.post("/user-preferences", prefs, { headers: { Authorization: `Bearer ${token}` } });
      notify("All set! Taking you home…");
      setTimeout(() => { window.location.href = "/"; }, 1200);
    } catch (err) { notify(err.response?.data?.error || "Failed to save preferences", true); }
    finally { setLoading(false); }
  };

  const resendOtp = async () => {
    try {
      await API.post("/auth/resend-otp", { user_id: otpData.user_id });
      notify("OTP resent to your email!");
    } catch { notify("Resend failed", true); }
  };

  const currentStepIdx = STEPS.findIndex((s) => s.key === step);

  const inputCls = "w-full px-4 py-3 rounded-xl text-sm outline-none transition-all";
  const inputStyle = { border: "2px solid #e5e7eb", fontFamily: "'DM Sans', sans-serif" };
  const onFocus = (e) => (e.target.style.borderColor = "#F5C518");
  const onBlur  = (e) => (e.target.style.borderColor = "#e5e7eb");

  const selectCls = "w-full px-4 py-3 rounded-xl text-sm outline-none transition-all cursor-pointer";

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="min-h-screen bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden">

      {/* decorative blobs */}
      <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-10"
        style={{ background: "radial-gradient(circle, #F5C518, transparent)", transform: "translate(30%,-30%)" }} />
      <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full opacity-10"
        style={{ background: "radial-gradient(circle, #F5C518, transparent)", transform: "translate(-30%,30%)" }} />

      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-3 gap-0 rounded-3xl overflow-hidden shadow-2xl relative z-10">

        {/* ── LEFT SIDEBAR ── */}
        <div className="hidden lg:flex flex-col justify-between p-10 relative overflow-hidden"
          style={{ background: "#0f0f0f" }}>
          <div className="absolute inset-0" style={{ background: "linear-gradient(160deg,#111,#0a0a0a)" }} />

          {/* logo */}
          <a href="/" style={{ fontFamily: "'Playfair Display', serif" }}
            className="relative z-10 text-2xl font-black text-white">
            RecoVibe<span style={{ color: "#F5C518" }}>.</span>
          </a>

          {/* steps progress */}
          <div className="relative z-10 space-y-5">
            <p className="text-xs uppercase tracking-widest font-semibold" style={{ color: "#F5C518" }}>
              Registration
            </p>
            {STEPS.map((s, i) => {
              const done   = i < currentStepIdx;
              const active = i === currentStepIdx;
              return (
                <div key={s.key} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-all"
                      style={{
                        background: done ? "#F5C518" : active ? "#F5C518" : "rgba(255,255,255,0.1)",
                        color: done || active ? "#111" : "#777",
                      }}>
                      {done ? "✓" : s.num}
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className="w-0.5 h-8 mt-1"
                        style={{ background: done ? "#F5C518" : "rgba(255,255,255,0.1)" }} />
                    )}
                  </div>
                  <div className="pb-4">
                    <p className={`text-sm font-semibold ${active ? "text-white" : done ? "text-gray-400" : "text-gray-600"}`}>
                      {s.title}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5">{s.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="relative z-10 p-4 rounded-xl text-xs"
            style={{ background: "rgba(245,197,24,0.08)", border: "1px solid rgba(245,197,24,0.2)" }}>
            <p className="font-semibold mb-1" style={{ color: "#F5C518" }}>🔒 Secure Sign-up</p>
            <p className="text-gray-500 leading-relaxed">Your password is hashed. OTP expires in 10 minutes.</p>
          </div>
        </div>

        {/* ── MAIN FORM PANEL ── */}
        <div className="lg:col-span-2 bg-white flex flex-col justify-center p-10 lg:p-12">

          {/* mobile logo */}
          <div className="lg:hidden mb-6 flex items-center justify-between">
            <a href="/" style={{ fontFamily: "'Playfair Display', serif" }}
              className="text-xl font-black text-gray-900">
              RecoVibe<span style={{ color: "#F5C518" }}>.</span>
            </a>
            {/* mobile step pill */}
            <span className="text-xs font-semibold px-3 py-1 rounded-full"
              style={{ background: "#F5C518", color: "#111" }}>
              Step {currentStepIdx + 1}/3
            </span>
          </div>

          {/* heading */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              {step === "form" && "Create Your Account"}
              {step === "otp"  && "Verify Your Email"}
              {step === "preferences" && "Your Style Profile"}
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              {step === "form" && "Join RecoVibe to unlock personalised fashion."}
              {step === "otp"  && `We sent a 6-digit code to ${formData.email}`}
              {step === "preferences" && "Help us curate your perfect wardrobe."}
            </p>
          </div>

          {message && (
            <div className="mb-5 p-3 rounded-xl text-sm font-medium"
              style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#15803d" }}>
              ✓ {message}
            </div>
          )}
          {error && (
            <div className="mb-5 p-3 rounded-xl text-sm font-medium"
              style={{ background: "#fff1f2", border: "1px solid #fecdd3", color: "#be123c" }}>
              ⚠ {error}
            </div>
          )}

          {/* ── STEP 1: FORM ── */}
          {step === "form" && (
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
                <input className={inputCls} style={inputStyle} onFocus={onFocus} onBlur={onBlur}
                  type="text" placeholder="John Doe" value={formData.name}
                  onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))} required />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">✉</span>
                  <input className={inputCls} style={{ ...inputStyle, paddingLeft: "2.5rem" }}
                    onFocus={onFocus} onBlur={onBlur}
                    type="email" placeholder="you@example.com" value={formData.email}
                    onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))} required />
                </div>
                <p className="text-xs text-gray-400 mt-1">OTP will be sent to this email for verification.</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                <div className="relative">
                  <input
                    className={inputCls}
                    style={{ ...inputStyle, paddingRight: "4rem" }}
                    onFocus={onFocus} onBlur={onBlur}
                    type={showPass ? "text" : "password"}
                    placeholder="At least 6 characters"
                    value={formData.password}
                    onChange={(e) => setFormData((p) => ({ ...p, password: e.target.value }))}
                    required minLength={6}
                  />
                  <button type="button" onClick={() => setShowPass(!showPass)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-600 font-medium">
                    {showPass ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={loading}
                className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50"
                style={{ background: "#111", color: "#fff" }}>
                {loading ? "Creating…" : "Continue →"}
              </button>

              <p className="text-center text-sm text-gray-500">
                Already registered?{" "}
                <Link to="/login" className="font-bold text-gray-900 hover:underline">Sign in</Link>
              </p>
            </form>
          )}

          {/* ── STEP 2: OTP ── */}
          {step === "otp" && (
            <form onSubmit={handleOtpSubmit} className="space-y-5">
              <div className="p-4 rounded-xl text-sm" style={{ background: "#fffbeb", border: "1px solid #fde68a" }}>
                <p className="font-semibold text-yellow-800 mb-1">📧 Check your inbox</p>
                <p className="text-yellow-700 text-xs">A 6-digit OTP has been sent to <strong>{formData.email}</strong>. It expires in 10 minutes.</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">Enter OTP</label>
                <input
                  type="text" inputMode="numeric" maxLength="6"
                  placeholder="0 0 0 0 0 0"
                  value={otpData.otp}
                  onChange={(e) => setOtpData((p) => ({ ...p, otp: e.target.value.replace(/\D/, "") }))}
                  required
                  className="w-full text-center text-3xl font-mono tracking-widest py-4 rounded-xl outline-none transition-all"
                  style={{ border: "2px solid #e5e7eb", letterSpacing: "0.5em" }}
                  onFocus={onFocus} onBlur={onBlur}
                />
              </div>

              <button type="submit" disabled={loading}
                className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50"
                style={{ background: "#111", color: "#fff" }}>
                {loading ? "Verifying…" : "Verify Email →"}
              </button>

              <p className="text-center text-sm text-gray-500">
                Didn't receive it?{" "}
                <button type="button" onClick={resendOtp}
                  className="font-bold text-gray-900 hover:underline">Resend OTP</button>
              </p>
            </form>
          )}

          {/* ── STEP 3: PREFERENCES ── */}
          {step === "preferences" && (
            <form onSubmit={handlePrefsSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Gender", name: "gender", opts: [["unisex","Unisex"],["male","Male"],["female","Female"]] },
                  { label: "Age Group", name: "age_group", opts: [["teen","Teen (13-19)"],["young_adult","Young Adult (20-35)"],["adult","Adult (36-55)"],["senior","Senior (55+)"]] },
                  { label: "Style", name: "style", opts: [["casual","Casual"],["formal","Formal"],["sporty","Sporty"],["traditional","Traditional"],["mixed","Mixed"]] },
                  { label: "Budget", name: "budget_range", opts: [["budget","Budget"],["mid","Mid-range"],["premium","Premium"],["luxury","Luxury"]] },
                ].map(({ label, name, opts }) => (
                  <div key={name}>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">{label}</label>
                    <select className={selectCls} style={inputStyle} onFocus={onFocus} onBlur={onBlur}
                      name={name} value={prefs[name]}
                      onChange={(e) => setPrefs((p) => ({ ...p, [name]: e.target.value }))}>
                      {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Favourite Categories</label>
                <input className={inputCls} style={inputStyle} onFocus={onFocus} onBlur={onBlur}
                  type="text" placeholder="e.g. Shirts, Jeans, Watches"
                  value={prefs.preferred_categories}
                  onChange={(e) => setPrefs((p) => ({ ...p, preferred_categories: e.target.value }))} />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Favourite Brands</label>
                <input className={inputCls} style={inputStyle} onFocus={onFocus} onBlur={onBlur}
                  type="text" placeholder="e.g. Nike, Zara, Levi's"
                  value={prefs.preferred_brands}
                  onChange={(e) => setPrefs((p) => ({ ...p, preferred_brands: e.target.value }))} />
              </div>

              <button type="submit" disabled={loading}
                className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50"
                style={{ background: "#111", color: "#fff" }}>
                {loading ? "Saving…" : "Complete Setup ✓"}
              </button>
            </form>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}