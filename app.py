import streamlit as st
from groq import Groq
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

def init_db():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, medicine TEXT, time TEXT, dosage TEXT, created_at TEXT)""")
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def login_user(email, password):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email=? AND password=?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def save_reminder(user_email, medicine, time, dosage):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("INSERT INTO reminders (user_email, medicine, time, dosage, created_at) VALUES (?, ?, ?, ?, ?)", (user_email, medicine, time, dosage, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_reminders(user_email):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("SELECT medicine, time, dosage, created_at FROM reminders WHERE user_email=? ORDER BY id DESC", (user_email,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_all(user_email):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE user_email=?", (user_email,))
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
    msg['Subject'] = f"Medicine Reminder: {medicine}"
    body = f"Hello!\n\nReminder for {medicine} at {time}.\nDosage: {dosage}\n\nStay healthy!\nMediRemind"
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

def ask_ai(prompt):
    try:
        key = st.secrets["GROQ_API_KEY"]
    except:
        key = "no_key"
    client = Groq(api_key=key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

init_db()
st.set_page_config(page_title="MediRemind", page_icon="💊", layout="centered")
st.markdown("""<style>.title{font-size:40px;font-weight:800;color:#1a73e8;text-align:center}.subtitle{font-size:16px;color:#555;text-align:center;margin-bottom:30px}.reminder-box{background:#ffffff;padding:15px;border-radius:12px;margin:8px 0;border-left:5px solid #1a73e8}</style>""", unsafe_allow_html=True)
st.markdown('<div class="title">💊 MediRemind</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your personal AI-powered medicine assistant</div>', unsafe_allow_html=True)
st.divider()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            user = login_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = user[0]
                st.rerun()
            else:
                st.error("Wrong email or password!")
    with tab2:
        st.subheader("Create Account")
        name = st.text_input("Your Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Create Account", use_container_width=True):
            if register_user(name, reg_email, reg_password):
                st.success("Account created! Please login.")
            else:
                st.error("Email already exists!")
else:
    with st.sidebar:
        st.header("⚙️ Settings")
        st.write(f"👋 Hello, **{st.session_state.user_name}**!")
        st.divider()
        if st.button("🗑️ Clear My Reminders"):
            delete_all(st.session_state.user_email)
            st.success("Reminders cleared!")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_name = ""
            st.rerun()

    t1, t2, t3 = st.tabs(["💊 Medicine Reminder", "⚠️ Drug Interaction", "🩺 Symptom Checker"])

    with t1:
        col1, col2 = st.columns(2)
        with col1:
            medicine_name = st.text_input("💊 Medicine Name", placeholder="e.g. Paracetamol")
        with col2:
            reminder_time = st.time_input("⏰ Reminder Time")
        dosage = st.text_input("📏 Dosage (optional)", placeholder="e.g. 500mg")
        if st.button("✅ Save Reminder & Get AI Info", use_container_width=True):
            if not medicine_name:
                st.error("Please enter a medicine name!")
            else:
                save_reminder(st.session_state.user_email, medicine_name, str(reminder_time), dosage if dosage else "Not specified")
                st.success(f"✅ Reminder saved for {medicine_name} at {reminder_time}!")
                send_email(st.session_state.user_email, medicine_name, str(reminder_time), dosage if dosage else "Not specified")
                with st.spinner("🤖 Getting AI info..."):
                    result = ask_ai(f"About {medicine_name}: 1.What is it? 2.Uses? 3.Side effects? 4.Warnings? 5.Dosage? Simple language for patient.")
                st.subheader("🤖 About this medicine:")
                st.info(result)
        reminders = get_reminders(st.session_state.user_email)
        if reminders:
            st.divider()
            st.subheader(f"📋 Your Reminders ({len(reminders)} total)")
            for r in reminders:
                st.markdown(f'<div class="reminder-box">💊 <strong>{r[0]}</strong> — ⏰ {r[1]} — 📏 {r[2]} — 🕐 {r[3]}</div>', unsafe_allow_html=True)
        else:
            st.info("No reminders yet!")

    with t2:
        st.subheader("⚠️ Drug Interaction Checker")
        col1, col2 = st.columns(2)
        with col1:
            med1 = st.text_input("💊 First Medicine", placeholder="e.g. Aspirin")
        with col2:
            med2 = st.text_input("💊 Second Medicine", placeholder="e.g. Ibuprofen")
        if st.button("🔍 Check Interaction", use_container_width=True):
            if not med1 or not med2:
                st.error("Enter both medicines!")
            else:
                with st.spinner("Checking..."):
                    result = ask_ai(f"Is it safe to take {med1} and {med2} together? 1.Safe or dangerous? 2.What happens? 3.What to do? Simple language.")
                if any(w in result.lower() for w in ["dangerous","avoid","do not","risk","harmful","warning"]):
                    st.error(f"⚠️ {result}")
                else:
                    st.success(f"✅ {result}")

    with t3:
        st.subheader("🩺 Symptom Checker")
        symptoms = st.text_area("Describe symptoms", placeholder="e.g. headache, fever, body pain...")
        age = st.number_input("Age", min_value=1, max_value=100, value=25)
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with col2:
            severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe"])
        if st.button("🔍 Check Symptoms", use_container_width=True):
            if not symptoms:
                st.error("Describe your symptoms!")
            else:
                with st.spinner("Analyzing..."):
                    result = ask_ai(f"{age}yr {gender} with {severity} symptoms: {symptoms}. 1.Possible condition? 2.OTC medicines? 3.Dosage? 4.When to see doctor? Keep simple.")
                st.warning("⚠️ AI suggestion only. Always consult a real doctor!")
                st.info(result)

def check_and_send_reminders():
    now = datetime.now().strftime("%H:%M")
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("SELECT user_email, medicine, time, dosage FROM reminders WHERE time=?", (now,))
    rows = c.fetchall()
    conn.close()
    for row in rows:
        send_email(row[0], row[1], row[2], row[3])

check_and_send_reminders()


