"""
Test script to verify OTP sending works before deploying.
Run locally: python test_otp.py
"""
import os
import sys
from dotenv import load_dotenv  # ← ADD THIS

load_dotenv()  # ← ADD THIS (right after imports, before anything else)

# ── Test 1: Check RESEND_API_KEY is set ──────────────────────────
api_key = os.getenv("RESEND_API_KEY", "")
# api_key="re_zh5ZfER1_3W619r54quVZTegDsPgpg5ve"
print(f"Test 1 - RESEND_API_KEY set: {'✅ YES' if api_key else '❌ NO — set it in .env or Render'}")
if not api_key:
    print("  Fix: Add RESEND_API_KEY to Render environment variables")
    sys.exit(1)

# ── Test 2: Check resend package installed ────────────────────────
try:
    import resend
    print(f"Test 2 - resend package: ✅ installed v{resend.__version__}")
except ImportError:
    print("Test 2 - resend package: ❌ NOT installed")
    print("  Fix: Add 'resend' to requirements.txt and redeploy")
    sys.exit(1)

# ── Test 3: Send actual test email ───────────────────────────────
resend.api_key = api_key
TEST_EMAIL = os.getenv("TEST_EMAIL", "biradaranand025@gmail.com")
print(f"Test 3 - Sending test email to {TEST_EMAIL} ...")

try:
    r = resend.Emails.send({
        "from":    "RecoVibe <onboarding@resend.dev>",
        "to":      [TEST_EMAIL],
        "subject": "OTP Test — RecoVibe",
        "html":    "<h1>Test OTP: 123456</h1><p>If you see this, Resend is working!</p>"
    })
    print(f"Test 3 - Send result: ✅ SUCCESS — id={r.get('id') or r}")
except Exception as e:
    print(f"Test 3 - Send result: ❌ FAILED — {e}")
    sys.exit(1)

print("\n🎉 ALL TESTS PASSED — Resend is working!")