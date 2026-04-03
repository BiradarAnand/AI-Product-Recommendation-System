import React, { useState } from "react";

function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");

  const [otpSent, setOtpSent] = useState(false);
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);

  // 🔷 Send OTP
  const sendOtp = async () => {
    if (!email) {
      alert("Enter email first");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/send-otp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email })
      });

      const data = await res.json();
      alert(data.message);

      setOtpSent(true);
    } catch (err) {
      console.error(err);
      alert("Error sending OTP");
    }

    setLoading(false);
  };

  // 🔷 Verify OTP
  const verifyOtp = async () => {
    if (!otp) {
      alert("Enter OTP");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/verify-otp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, otp })
      });

      const data = await res.json();

      if (res.ok) {
        alert("OTP Verified ✅");
        setVerified(true);
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert("Error verifying OTP");
    }

    setLoading(false);
  };

  // 🔷 Register User
  const handleRegister = async () => {
    if (!verified) {
      alert("Please verify OTP first ❗");
      return;
    }

    if (!name || !email || !password) {
      alert("Fill all fields");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, email, password })
      });

      const data = await res.json();
      alert(data.message);

      // reset form
      setName("");
      setEmail("");
      setPassword("");
      setOtp("");
      setOtpSent(false);
      setVerified(false);

    } catch (err) {
      console.error(err);
      alert("Registration failed");
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "30px", maxWidth: "400px", margin: "auto" }}>
      <h2>Register</h2>

      {/* Name */}
      <input
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{ width: "100%", marginBottom: "10px", padding: "8px" }}
      />

      {/* Email */}
      <input
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={{ width: "100%", marginBottom: "10px", padding: "8px" }}
      />

      {/* Password */}
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ width: "100%", marginBottom: "10px", padding: "8px" }}
      />

      {/* Send OTP */}
      <button onClick={sendOtp} disabled={loading}>
        {loading ? "Sending..." : "Send OTP"}
      </button>

      {/* OTP Input */}
      {otpSent && (
        <>
          <input
            placeholder="Enter OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            style={{ width: "100%", marginTop: "10px", padding: "8px" }}
          />

          <button onClick={verifyOtp} disabled={loading}>
            Verify OTP
          </button>
        </>
      )}

      {/* Register */}
      <button
        onClick={handleRegister}
        disabled={!verified}
        style={{
          marginTop: "15px",
          width: "100%",
          padding: "10px",
          background: verified ? "green" : "gray",
          color: "white",
          border: "none"
        }}
      >
        Register
      </button>
    </div>
  );
}

export default Register;