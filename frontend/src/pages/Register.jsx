import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API = axios.create({ baseURL: "https://ai-product-recommendation-system-by60.onrender.com/api" });

const STEPS = [
  { num: 1, key: "form",        title: "Create Account",   desc: "Your basic details" },
  { num: 2, key: "otp",         title: "Verify Email",     desc: "Enter the OTP sent" },
  { num: 3, key: "preferences", title: "Style Profile",    desc: "Personalise your feed" },
];

export default function Register() {
  const [step, setStep] = useState("form");

  const [formData, setFormData] = useState({
    name: "", email: "", password: "",
    otp_channel: "email",
  });

  const [otpData, setOtpData]     = useState({ user_id: null, otp: "" });
  const [digits, setDigits]        = useState(Array(6).fill(""));
  const [resendCooldown, setResendCooldown] = useState(0); // seconds remaining
  const digitRefs                  = useRef([]);
  const cooldownRef                = useRef(null);

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

  // ── Step 1: Register ──────────────────────────────────────────
  // ✅ FIXED: removed duplicate inner try-catch that caused ReferenceError on 'res'
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    notify("");

    try {
      const res = await API.post("/auth/register", {
        ...formData,
        otp_channel: "email"
      });

      console.log("[REGISTER] Success:", res.data);

      setOtpData({ user_id: res.data.user_id, otp: "" });
      setDigits(Array(6).fill(""));
      notify(
        res.data.email_sent
          ? "OTP sent to your email. Check your inbox!"
          : "Account created! OTP may be delayed — check spam or contact support."
      );
      setStep("otp");
      startCooldown(60);
      setTimeout(() => digitRefs.current[0]?.focus(), 100);

    } catch (err) {
      console.error("[REGISTER] Error:", err.response?.data || err.message);
      notify(err.response?.data?.error || "Registration failed. Please try again.", true);
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2: Verify OTP ────────────────────────────────────────
  // ✅ FIXED: removed duplicate inner try-catch that caused ReferenceError on 'res'
  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    notify("");

    try {
      const res = await API.post("/auth/verify-otp", otpData);

      console.log("[VERIFY-OTP] Success:", res.data);

      localStorage.setItem("token", res.data.token);
      if (res.data.user) {
        localStorage.setItem("user", JSON.stringify(res.data.user));
      }

      notify("Email verified! Setting up your style profile…");
      setStep("preferences");

    } catch (err) {
      console.error("[VERIFY-OTP] Error:", err.response?.data || err.message);
      notify(err.response?.data?.error || "Invalid OTP. Please try again.", true);
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: Save Preferences ──────────────────────────────────
  const handlePrefsSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    notify("");

    try {
      const token = localStorage.getItem("token");
      await API.post("/user-preferences", prefs, {
        headers: { Authorization: `Bearer ${token}` }
      });
      notify("All set! Taking you home…");
      setTimeout(() => { window.location.href = "/"; }, 1200);
    } catch (err) {
      notify(err.response?.data?.error || "Failed to save preferences", true);
    } finally {
      setLoading(false);
    }
  };

  // ── Countdown timer helpers ───────────────────────────────────
  const startCooldown = useCallback((seconds = 60) => {
    setResendCooldown(seconds);
    clearInterval(cooldownRef.current);
    cooldownRef.current = setInterval(() => {
      setResendCooldown((prev) => {
        if (prev <= 1) { clearInterval(cooldownRef.current); return 0; }
        return prev - 1;
      });
    }, 1000);
  }, []);

  useEffect(() => () => clearInterval(cooldownRef.current), []);

  // ── Individual digit handlers ─────────────────────────────────
  const handleDigitChange = (idx, val) => {
    const digit = val.replace(/\D/g, "").slice(-1);
    const next  = [...digits];
    next[idx]   = digit;
    setDigits(next);
    const joined = next.join("");
    setOtpData((p) => ({ ...p, otp: joined }));
    if (digit && idx < 5) digitRefs.current[idx + 1]?.focus();
  };

  const handleDigitKeyDown = (idx, e) => {
    if (e.key === "Backspace" && !digits[idx] && idx > 0) {
      digitRefs.current[idx - 1]?.focus();
    }
    if (e.key === "ArrowLeft"  && idx > 0) digitRefs.current[idx - 1]?.focus();
    if (e.key === "ArrowRight" && idx < 5) digitRefs.current[idx + 1]?.focus();
  };

  const handleDigitPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    const next   = Array(6).fill("");
    [...pasted].forEach((ch, i) => { next[i] = ch; });
    setDigits(next);
    setOtpData((p) => ({ ...p, otp: pasted }));
    const focusIdx = Math.min(pasted.length, 5);
    digitRefs.current[focusIdx]?.focus();
  };

  const resendOtp = async () => {
    if (resendCooldown > 0) return;
    try {
      await API.post("/auth/resend-otp", { user_id: otpData.user_id });
      notify("OTP resent! Check your inbox.");
      setDigits(Array(6).fill(""));
      setOtpData((p) => ({ ...p, otp: "" }));
      digitRefs.current[0]?.focus();
      startCooldown(60);
    } catch {
      notify("Resend failed. Please try again.", true);
    }
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
        <div className="lg:col-span-2 bg-white flex flex-col justify-center p-6 md:p-10 lg:p-12">

          {/* mobile logo */}
          <div className="lg:hidden mb-6 flex items-center justify-between">
            <a href="/" style={{ fontFamily: "'Playfair Display', serif" }}
              className="text-xl font-black text-gray-900">
              RecoVibe<span style={{ color: "#F5C518" }}>.</span>
            </a>
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
              {/* Info banner */}
              <div className="p-4 rounded-xl text-sm" style={{ background: "#fffbeb", border: "1px solid #fde68a" }}>
                <p className="font-semibold text-yellow-800 mb-1">📧 Check your inbox</p>
                <p className="text-yellow-700 text-xs">
                  A 6-digit OTP was sent to <strong>{formData.email}</strong>. It expires in 10 minutes.
                  <br />Not received? Check your spam folder or click Resend below.
                </p>
              </div>

              {/* 6 individual digit boxes */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Enter 6-digit OTP
                </label>
                <div className="flex gap-2 justify-between" onPaste={handleDigitPaste}>
                  {digits.map((d, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (digitRefs.current[idx] = el)}
                      id={`otp-digit-${idx}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={d}
                      onChange={(e) => handleDigitChange(idx, e.target.value)}
                      onKeyDown={(e) => handleDigitKeyDown(idx, e)}
                      required={idx === 0}
                      className="flex-1 text-center text-2xl font-mono font-bold py-4 rounded-xl outline-none transition-all"
                      style={{
                        border: d ? "2px solid #111" : "2px solid #e5e7eb",
                        background: d ? "#f9fafb" : "#fff",
                        minWidth: 0,
                      }}
                      onFocus={(e) => (e.target.style.borderColor = "#F5C518")}
                      onBlur={(e)  => (e.target.style.borderColor = d ? "#111" : "#e5e7eb")}
                    />
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-2 text-center">
                  Tip: you can paste the 6-digit code directly
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || otpData.otp.length < 6}
                className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50"
                style={{ background: "#111", color: "#fff" }}
              >
                {loading ? "Verifying…" : "Verify Email →"}
              </button>

              {/* Resend with cooldown */}
              <p className="text-center text-sm text-gray-500">
                Didn't receive it?{" "}
                {resendCooldown > 0 ? (
                  <span className="font-medium text-gray-400">
                    Resend in <span style={{ color: "#F5C518", fontWeight: 700 }}>{resendCooldown}s</span>
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={resendOtp}
                    className="font-bold text-gray-900 hover:underline"
                  >
                    Resend OTP
                  </button>
                )}
              </p>
            </form>
          )}

          {/* ── STEP 3: PREFERENCES ── */}
          {step === "preferences" && (
            <form onSubmit={handlePrefsSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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