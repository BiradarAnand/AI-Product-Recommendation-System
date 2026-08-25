require('dotenv').config({ path: '../.env' }); // Read from backend/.env
const express = require('express');
const nodemailer = require('nodemailer');
const cors = require('cors');

const app = express();
const PORT = process.env.NODE_PORT || 3001;

app.use(cors());
app.use(express.json());

// Set up Nodemailer transporter
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.GMAIL_ADDRESS,
        pass: process.env.GMAIL_APP_PASS
    }
});

app.post('/api/send-otp', async (req, res) => {
    const { name, email, otp } = req.body;

    if (!email || !otp) {
        return res.status(400).json({ success: false, error: 'Email and OTP are required.' });
    }

    const htmlContent = `
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                    padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
            <h2 style="color:#1f2937;">Your OTP Code</h2>
            <p style="color:#6b7280;">Hi ${name || 'User'}, use this code to verify your account:</p>
            <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
                        text-align:center;padding:24px;background:#f9fafb;
                        border-radius:8px;color:#1f2937;">${otp}</div>
            <p style="color:#9ca3af;font-size:13px;margin-top:20px;">
                Expires in 10 minutes. Do not share with anyone.
            </p>
        </div>
    `;

    try {
        await transporter.sendMail({
            from: process.env.GMAIL_ADDRESS,
            to: email,
            subject: 'Your OTP Code',
            text: `Hi ${name || 'User'}, Your OTP is: ${otp}`,
            html: htmlContent
        });

        console.log(`[OTP Email] Sent successfully to ${email}`);
        return res.status(200).json({ success: true, message: 'OTP sent successfully.' });
    } catch (error) {
        console.error(`[OTP Email] Failed:`, error);
        return res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Node Auth Microservice running on port ${PORT}`);
});
