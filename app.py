import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import razorpay
import json

# Supabase setup
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    supabase = create_client("https://dvpebrdomjdclxjttjbf.supabase.co", "sb_secret_tJZEzDaoOvN5mnFwlkB2og_F8DWNY2C")

# Razorpay setup
try:
    rzp_client = razorpay.Client(auth=(st.secrets["RAZORPAY_KEY_ID"], st.secrets["RAZORPAY_KEY_SECRET"]))
    RZP_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
except:
    rzp_client = None
    RZP_KEY_ID = ""

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password):
    try:
        supabase.table("users").insert({"name": name, "email": email, "password": hash_password(password), "plan": "free"}).execute()
        return True
    except:
        return False

def login_user(email, password):
    try:
        result = supabase.table("users").select("name, plan").eq("email", email).eq("password", hash_password(password)).execute()
        return result.data[0] if result.data else None
    except:
        return None

def get_user_plan(email):
    try:
        result = supabase.table("users").select("plan").eq("email", email).execute()
        return result.data[0]['plan'] if result.data else "free"
    except:
        return "free"

def upgrade_user(email):
    try:
        supabase.table("users").update({"plan": "pro"}).eq("email", email).execute()
        return True
    except:
        return False

def save_reminder(user_email, medicine, time, dosage):
    supabase.table("reminders").insert({"user_email": user_email, "medicine": medicine, "time": time, "dosage": dosage}).execute()

def get_reminders(user_email):
    result = supabase.table("reminders").select("*").eq("user_email", user_email).execute()
    return result.data

def delete_all(user_email):
    supabase.table("reminders").delete().eq("user_email", user_email).execute()

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

def check_and_send_reminders():
    now = datetime.now().strftime("%H:%M")
    result = supabase.table("reminders").select("*").eq("time", now).execute()
    for row in result.data:
        send_email(row['user_email'], row['medicine'], row['time'], row['dosage'])

check_and_send_reminders()

st.set_page_config(page_title="MediRemind", page_icon="💊", layout="centered")

st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #1a73e8, #0d47a1);
    padding: 60px 20px;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 30px;
}
.hero h1 { font-size: 48px; font-weight: 900; margin-bottom: 10px; }
.hero p { font-size: 20px; opacity: 0.9; }
.feature-box {
    background: #f8f9ff;
    border-radius: 15px;
    padding: 25px;
    text-align: center;
    border: 1px solid #e0e7ff;
    margin-bottom: 15px;
}
.feature-icon { font-size: 40px; }
.feature-title { font-size: 18px; font-weight: 700; color: #1a73e8; }
.stats-box {
    background: linear-gradient(135deg, #1a73e8, #0d47a1);
    color: white;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
}
.stats-number { font-size: 36px; font-weight: 900; }
.pro-box {
    background: linear-gradient(135deg, #f093fb, #f5576c);
    color: white;
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    margin: 20px 0;
}
.free-box {
    background: #f8f9ff;
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    border: 2px solid #e0e7ff;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "show_app" not in st.session_state:
    st.session_state.show_app = False
if "user_plan" not in st.session_state:
    st.session_state.user_plan = "free"

if not st.session_state.logged_in and not st.session_state.show_app:
    st.markdown("""
    <div class="hero">
        <div style="font-size:60px">💊</div>
        <h1>MediRemind</h1>
        <p>Your AI-powered personal medicine assistant</p>
        <p style="font-size:14px;opacity:0.7">Never miss a dose again</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## ✨ Why MediRemind?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="feature-box"><div class="feature-icon">⏰</div><div class="feature-title">Smart Reminders</div><p>Get email reminders exactly when it's time</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="feature-box"><div class="feature-icon">🤖</div><div class="feature-title">AI Medicine Info</div><p>Instant AI-powered medicine information</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="feature-box"><div class="feature-icon">⚠️</div><div class="feature-title">Drug Interaction</div><p>Check if medicines are safe together</p></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Pricing section
    st.markdown("## 💎 Pricing")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="free-box">
            <h2>🆓 Free</h2>
            <h1>₹0</h1>
            <p>Forever free</p>
            <p>✅ 3 reminders</p>
            <p>✅ AI medicine info</p>
            <p>✅ Drug interaction check</p>
            <p>❌ Symptom checker</p>
            <p>❌ Unlimited reminders</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="pro-box">
            <h2>⭐ Pro</h2>
            <h1>₹99/month</h1>
            <p>Best for patients</p>
            <p>✅ Unlimited reminders</p>
            <p>✅ AI medicine info</p>
            <p>✅ Drug interaction check</p>
            <p>✅ Symptom checker</p>
            <p>✅ Priority support</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🚀 Get Started Free")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.show_app = True
            st.rerun()
    with col2:
        if st.button("✨ Register Free", use_container_width=True):
            st.session_state.show_app = True
            st.rerun()

    st.markdown("<p style='text-align:center;color:gray'>Built with ❤️ by a pharmacy student | MediRemind 2026</p>", unsafe_allow_html=True)

elif not st.session_state.logged_in and st.session_state.show_app:
    if st.button("← Back to Home"):
        st.session_state.show_app = False
        st.rerun()
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
                st.session_state.user_name = user['name']
                st.session_state.user_plan = user.get('plan', 'free')
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
        st.markdown("# 💊 MediRemind")
        st.write(f"👋 Hello, **{st.session_state.user_name}**!")
        if st.session_state.user_plan == "pro":
            st.success("⭐ Pro Member")
        else:
            st.warning("🆓 Free Plan")
            if st.button("⭐ Upgrade to Pro - ₹99/month"):
                st.session_state.show_payment = True
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.show_app = False
            st.rerun()

    # Payment section
    if st.session_state.get("show_payment"):
        st.markdown("## ⭐ Upgrade to Pro")
        st.markdown("Get unlimited reminders + symptom checker for just **₹99/month**!")
        order = rzp_client.order.create({"amount": 9900, "currency": "INR", "payment_capture": 1})
        order_id = order['id']
        payment_html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <button onclick="openRazorpay()" style="background:#1a73e8;color:white;padding:15px 40px;border:none;border-radius:10px;font-size:18px;cursor:pointer;">
            💳 Pay ₹99 Now
        </button>
        <script>
        function openRazorpay() {{
            var options = {{
                key: "{RZP_KEY_ID}",
                amount: 9900,
                currency: "INR",
                name: "MediRemind",
                description: "Pro Plan - 1 Month",
                order_id: "{order_id}",
                handler: function(response) {{
                    window.location.href = "?payment=success&email={st.session_state.user_email}";
                }},
                prefill: {{email: "{st.session_state.user_email}"}},
                theme: {{color: "#1a73e8"}}
            }};
            var rzp = new Razorpay(options);
            rzp.open();
        }}
        </script>
        """
        st.components.v1.html(payment_html, height=100)

        # Check payment success
        params = st.query_params
        if params.get("payment") == "success":
            upgrade_user(st.session_state.user_email)
            st.session_state.user_plan = "pro"
            st.session_state.show_payment = False
            st.success("🎉 Welcome to Pro! Enjoy unlimited features!")
            st.rerun()

    plan = st.session_state.user_plan
    reminders = get_reminders(st.session_state.user_email)

    t1, t2, t3 = st.tabs(["💊 Medicine Reminder", "⚠️ Drug Interaction", "🩺 Symptom Checker"])

    with t1:
        st.subheader("💊 Medicine Reminder")
        if plan == "free" and len(reminders) >= 3:
            st.warning("⚠️ Free plan limit reached! Upgrade to Pro for unlimited reminders.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                medicine = st.text_input("💊 Medicine Name")
            with col2:
                time = st.selectbox("⏰ Reminder Time", [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 30)])
            dosage = st.text_input("✏️ Dosage (optional)")
            if st.button("✅ Save Reminder & Get AI Info", use_container_width=True):
                if medicine:
                    save_reminder(st.session_state.user_email, medicine, time, dosage)
                    send_email(st.session_state.user_email, medicine, time, dosage)
                    st.success(f"✅ Reminder saved for {medicine} at {time}!")
                    with st.spinner("Getting AI info..."):
                        result = ask_ai(f"Tell me about {medicine} medicine. 1.What is it? 2.Uses? 3.Side effects? 4.Warnings? Simple language.")
                        st.subheader("🤖 About this medicine:")
                        st.info(result)
        if reminders:
            st.subheader(f"📋 Your Reminders ({len(reminders)} total)")
            for r in reminders:
                st.markdown(f"💊 **{r['medicine']}** — ⏰ {r['time']} — ✏️ {r['dosage']}")
            if st.button("🗑️ Delete All Reminders"):
                delete_all(st.session_state.user_email)
                st.rerun()

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
        if plan == "free":
            st.warning("🔒 Symptom Checker is a Pro feature!")
            st.markdown("Upgrade to Pro for **₹99/month** to unlock this feature.")
        else:
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
                        result = ask_ai(f"{age}yr {gender} with {severity} symptoms: {symptoms}. 1.Possible condition? 2.OTC medicines? 3.Dosage? 4.When to see doctor? Simple language.")
                        st.warning("⚠️ AI suggestion only. Always consult a real doctor!")
                        st.info(result)
