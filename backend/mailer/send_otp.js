#!/usr/bin/env node
/**
 * send_otp.js — RecoVibe Nodemailer OTP Sender
 * ─────────────────────────────────────────────
 * Called as a subprocess from Python (email_service.py).
 * Reads { name, email, otp } from stdin (JSON) and sends via Gmail SMTP.
 *
 * Usage (from Python):
 *   subprocess.run(['node', 'mailer/send_otp.js'], input=json.dumps({...}))
 *
 * Exit codes:
 *   0 — email sent successfully
 *   1 — email failed
 *
 * Required env vars (inherited from Python process or .env):
 *   GMAIL_USER         — Gmail address  (e.g. recovibe3@gmail.com)
 *   GMAIL_APP_PASSWORD — 16-char App Password (NOT your account password)
 *   MAIL_FROM_NAME     — Display name   (default: RecoVibe)
 */

"use strict";

const nodemailer = require("nodemailer");

// ── Read JSON payload from stdin ───────────────────────────────────
let rawInput = "";
process.stdin.setEncoding("utf8");

process.stdin.on("data", (chunk) => {
  rawInput += chunk;
});

process.stdin.on("end", async () => {
  let name, email, otp;

  try {
    const payload = JSON.parse(rawInput.trim());
    name  = payload.name  || "User";
    email = payload.email;
    otp   = payload.otp;
  } catch (parseErr) {
    console.error("[Nodemailer] [FAIL] Failed to parse JSON input:", parseErr.message);
    process.exit(1);
  }

  if (!email || !otp) {
    console.error("[Nodemailer] [FAIL] Missing required fields: email, otp");
    process.exit(1);
  }

  const gmailUser     = process.env.GMAIL_USER         || process.env.GMAIL_ADDRESS || "";
  const gmailPass     = process.env.GMAIL_APP_PASSWORD || process.env.GMAIL_APP_PASS || "";
  const fromName      = process.env.MAIL_FROM_NAME     || "RecoVibe";

  if (!gmailUser || !gmailPass) {
    console.error("[Nodemailer] [FAIL] GMAIL_USER / GMAIL_APP_PASSWORD not set in environment");
    process.exit(1);
  }

  // ── Create transporter ─────────────────────────────────────────
  const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 587,
    secure: false,          // STARTTLS
    auth: {
      user: gmailUser,
      pass: gmailPass,
    },
    connectionTimeout: 10000,
    greetingTimeout:   10000,
    socketTimeout:     10000,
  });

  // ── Beautiful HTML email ───────────────────────────────────────
  const htmlBody = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your RecoVibe account</title>
</head>
<body style="margin:0;padding:0;background-color:#0f0f0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#0f0f0f;padding:48px 16px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" border="0"
               style="background:#1a1a1a;border-radius:20px;border:1px solid #2a2a2a;
                      box-shadow:0 20px 60px rgba(0,0,0,0.5);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#111111 0%,#1c1c1c 100%);
                       padding:32px 40px;border-radius:20px 20px 0 0;
                       border-bottom:2px solid #F5C518;">
              <p style="margin:0;font-size:28px;font-weight:900;color:#ffffff;
                         letter-spacing:-0.5px;font-family:Georgia,'Times New Roman',serif;">
                RecoVibe<span style="color:#F5C518;">.</span>
              </p>
              <p style="margin:6px 0 0;font-size:11px;color:#6b7280;
                         letter-spacing:0.15em;text-transform:uppercase;">
                AI-Powered Fashion Recommendations
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#f9fafb;">
                Verify your email
              </h1>
              <p style="margin:0 0 32px;font-size:15px;color:#9ca3af;line-height:1.7;">
                Hi <strong style="color:#f3f4f6;">${name}</strong>,<br>
                Enter the code below to complete your
                <strong style="color:#F5C518;">RecoVibe</strong> account setup.
                This code expires in <strong style="color:#f3f4f6;">10 minutes</strong>.
              </p>

              <!-- OTP Block -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center"
                      style="background:#111111;border:2px solid #F5C518;
                             border-radius:16px;padding:36px 24px;">
                    <p style="margin:0 0 12px;font-size:11px;font-weight:700;
                               color:#6b7280;letter-spacing:0.2em;text-transform:uppercase;">
                      One-Time Password
                    </p>
                    <p style="margin:0;font-size:52px;font-weight:900;color:#F5C518;
                               letter-spacing:0.4em;
                               font-family:'Courier New',Courier,monospace;">
                      ${otp}
                    </p>
                    <p style="margin:12px 0 0;font-size:12px;color:#4b5563;">
                      Valid for 10 minutes only
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Security notice -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="margin-top:24px;">
                <tr>
                  <td style="background:#1f1f1f;border-radius:12px;
                             padding:16px 20px;border-left:3px solid #F5C518;">
                    <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;">
                      🔒 <strong style="color:#9ca3af;">Security tip:</strong>
                      Never share this code with anyone. RecoVibe will
                      <strong style="color:#9ca3af;">never</strong> ask for your OTP via phone or chat.
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:28px 0 0;font-size:13px;color:#4b5563;line-height:1.6;">
                If you didn't create a RecoVibe account, you can safely ignore this email.
                No action is required.
              </p>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <hr style="border:none;border-top:1px solid #2a2a2a;margin:0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;border-radius:0 0 20px 20px;">
              <p style="margin:0;font-size:12px;color:#374151;
                         text-align:center;line-height:1.6;">
                &copy; 2026 RecoVibe &nbsp;&middot;&nbsp;
                AI-powered fashion recommendations &nbsp;&middot;&nbsp;
                <span style="color:#F5C518;">Sent via Nodemailer</span>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;

  const plainText = [
    `Hi ${name},`,
    ``,
    `Your RecoVibe verification code is:`,
    ``,
    `    ${otp}`,
    ``,
    `This code expires in 10 minutes.`,
    `Do not share it with anyone.`,
    ``,
    `If you didn't create a RecoVibe account, ignore this email.`,
    ``,
    `— The RecoVibe Team`,
  ].join("\n");

  const mailOptions = {
    from:    `"${fromName}" <${gmailUser}>`,
    to:      email,
    subject: `${otp} is your RecoVibe verification code`,
    text:    plainText,
    html:    htmlBody,
  };

  // ── Send ───────────────────────────────────────────────────────
  try {
    const info = await transporter.sendMail(mailOptions);
    console.log(`[Nodemailer] [OK] OTP sent to ${email} - MessageId: ${info.messageId}`);
    process.exit(0);
  } catch (err) {
    console.error(`[Nodemailer] [FAIL] Failed to send to ${email}: ${err.message}`);
    if (err.code === "EAUTH") {
      console.error("[Nodemailer] [WARN] Authentication failed - check GMAIL_USER and GMAIL_APP_PASSWORD");
      console.error("[Nodemailer] [WARN] Generate App Password at: myaccount.google.com -> Security -> App passwords");
    }
    process.exit(1);
  }
});
