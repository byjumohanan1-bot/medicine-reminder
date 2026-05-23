import streamlit as st
from openai import OpenAI
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def init_db():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine TEXT,
            time TEXT,
            dosage TEXT,
            email TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_reminder(medicine, time, dosage, email):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("INSERT INTO reminders (medicine, time, dosage, email, created_at) VALUES (?, ?, ?, ?, ?)",
              (medicine, time, dosage, email, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_reminders():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("SELECT medicine, time, dosage, email, created_at FROM reminders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_all():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()

def send_email(to_email, medicine, time, dosage):
    try:
        sender_email = st.secrets["GMAIL"]
        sender_password = st.secrets["GMAIL_PASSWORD"]
    except:
        sender_email = "byjumohanan1@gmail.com"
        sender_password = "aejjreaafndystpf"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = f"💊 Medicine Reminder: {medicine}"
    body = f"""
Hello!

This is your medicine reminder from MediRemind!

💊 Medicine: {medicine}
⏰ Time: {time}
📏 Dosage: {dosage}

Please take your medicine on time!

Stay healthy!
MediRemind Team
    """
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

init_db()

st.set_page_config(page_title="MediRemind", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .title { font-size: 40px; font-weight: 800; color: #1a73e8; text-align: center; }
    .subtitle { font-size: 16px; color: #555; text-align: center; margin-bottom: 30px; }
    .reminder-box { background: #ffffff; padding: 15px; border-radius: 12px; margin: 8px 0; border-left: 5px solid #1a73e8; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💊 MediRemind</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your personal AI-powered medicine assistant</div>', unsafe_allow_html=True)
st.divider()

with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.caption("Your key is never stored or shared.")
    st.divider()
    st.markdown("### 📋 How to use")
    st.markdown("1. Enter your API key\n2. Type a medicine name\n3. Set reminder time\n4. Enter your email\n5. Click the button!")
    st.divider()
    if st.button("🗑️ Clear All Reminders"):
        delete_all()
        st.success("All reminders cleared!")

col1, col2 = st.columns(2)
with col1:
    medicine_name = st.text_input("💊 Medicine Name", placeholder="e.g. Paracetamol")
with col2:
    reminder_time = st.time_input("⏰ Reminder Time")

dosage = st.text_input("📏 Dosage (optional)", placeholder="e.g. 500mg, 1 tablet")
user_email = st.text_input("📧 Your Email", placeholder="e.g. yourname@gmail.com")

if st.button("✅ Save Reminder & Get AI Info", use_container_width=True):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    elif not medicine_name:
        st.error("Please enter a medicine name!")
    elif not user_email:
        st.error("Please enter your email!")
    else:
        save_reminder(medicine_name, str(reminder_time), dosage if dosage else "Not specified", user_email)
        st.success(f"✅ Reminder saved for {medicine_name} at {reminder_time}!")
        email_sent = send_email(user_email, medicine_name, str(reminder_time), dosage if dosage else "Not specified")
        if email_sent:
            st.success("📧 Confirmation email sent!")
        else:
            st.warning("⚠️ Email not sent. Please check email settings.")
        with st.spinner("🤖 Getting AI information..."):
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"In 3-4 simple sentences, what is {medicine_name}? What is it used for? Any important warnings? Keep it simple for a patient."
                }]
            )
        st.subheader("🤖 About this medicine:")
        st.info(response.choices[0].message.content)

reminders = get_reminders()
if reminders:
    st.divider()
    st.subheader(f"📋 Your Reminders ({len(reminders)} total)")
    for r in reminders:
        st.markdown(f"""
        <div class="reminder-box">
            💊 <strong>{r[0]}</strong> — ⏰ {r[1]} — 📏 {r[2]} — 📧 {r[3]} — 🕐 {r[4]}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No reminders yet. Add your first medicine above!")
