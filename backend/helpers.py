import hashlib
import sqlite3
import smtplib
from email.message import EmailMessage
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DB_PATH = Path(__file__).parent / "ppip.db"
# --- Helper functions ---
def hash_password(password: str) -> str:
    """Return SHA-256 hash of password"""
    return hashlib.sha256(password.encode()).hexdigest()

def send_email(to_email, subject, body):
    # --- Example using SMTP Gmail ---
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "flores.a.bscs@gmail.com"        # replace with your sender email
    SMTP_PASS = "lbyo bsuf cztj cpkg"           # use App password if Gmail

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)
    

def get_user_by_username(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def send_otp_email(to_email, otp):
    EMAIL_ADDRESS = "flores.a.bscs@gmail.com"
    EMAIL_PASSWORD = "lbyo bsuf cztj cpkg"

    msg = EmailMessage()
    msg['Subject'] = "Your OTP Code"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    # --- Plain text fallback ---
    plain_text = f"Your OTP code is: {otp}. It will expire in 5 minutes."
    msg.set_content(plain_text)

    # --- HTML content ---
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
        <p>Hello,</p>
        <p>Your <strong>One-Time Password (OTP)</strong> is:</p>
        <h2 style="background-color: #f2f2f2; padding: 10px; display: inline-block;">{otp}</h2>
        <p>This code will expire in <strong>5 minutes</strong>. Please do not share it with anyone.</p>
        <p>Thank you,<br>Your Company Name</p>
    </body>
    </html>
    """
    msg.add_alternative(html_message, subtype='html')

    # --- Send email ---
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
