import streamlit as st
from openai import OpenAI
import sqlite3
from datetime import datetime

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine TEXT,
            time TEXT,
            dosage TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_reminder(medicine, time, dosage):
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("INSERT INTO reminders (medicine, time, dosage, created_at) VALUES (?, ?, ?, ?)",
              (medicine, time, dosage, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_reminders():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("SELECT medicine, time, dosage, created_at FROM reminders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_all():
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()

# --- Initialize database ---
init_db()

# --- Page Setup ---
st.set_page_config(page_title="MediRemind", page_icon="💊", layout="centered")

# --- Custom Styling ---
st.markdown("""
    <style>
    .title { font-size: 40px; font-weight: 800; color: #1a73e8; text-align: center; }
    .subtitle { font-size: 16px; color: #555; text-align: center; margin-bottom: 30px; }
    .reminder-box { background: #ffffff; padding: 15px; border-radius: 12px; margin: 8px 0; border-left: 5px solid #1a73e8; }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="title">💊 MediRemind</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your personal AI-powered medicine assistant</div>', unsafe_allow_html=True)
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.caption("Your key is never stored or shared.")
    st.divider()
    st.markdown("### 📋 How to use")
    st.markdown("1. Enter your API key\n2. Type a medicine name\n3. Set reminder time\n4. Click the button!")
    st.divider()
    if st.button("🗑️ Clear All Reminders"):
        delete_all()
        st.success("All reminders cleared!")

# --- Main Form ---
col1, col2 = st.columns(2)
with col1:
    medicine_name = st.text_input("💊 Medicine Name", placeholder="e.g. Paracetamol")
with col2:
    reminder_time = st.time_input("⏰ Reminder Time")

dosage = st.text_input("📏 Dosage (optional)", placeholder="e.g. 500mg, 1 tablet")

# --- Button ---
if st.button("✅ Save Reminder & Get AI Info", use_container_width=True):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    elif not medicine_name:
        st.error("Please enter a medicine name!")
    else:
        save_reminder(medicine_name, str(reminder_time), dosage if dosage else "Not specified")
        st.success(f"✅ Reminder saved for {medicine_name} at {reminder_time}!")

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

# --- Show saved reminders ---
reminders = get_reminders()
if reminders:
    st.divider()
    st.subheader(f"📋 Your Reminders ({len(reminders)} total)")
    for r in reminders:
        st.markdown(f"""
        <div class="reminder-box">
            💊 <strong>{r[0]}</strong> — ⏰ {r[1]} — 📏 {r[2]} — 🕐 Added: {r[3]}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No reminders yet. Add your first medicine above!")
