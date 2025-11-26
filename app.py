import streamlit as st
import json
import os
from datetime import datetime

DB_FILE = "database.json"

# -----------------------
# Load / Save JSON DB
# -----------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "transactions": []}

    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# -----------------------
# Apple Color Palette
# -----------------------
APPLE_BLUE = "#0A84FF"
APPLE_GREEN = "#32D74B"
APPLE_RED = "#FF453A"
APPLE_GRAY = "#1C1C1E"
APPLE_BG = "#000000"
APPLE_CARD = "#1C1C1E"

st.set_page_config(
    page_title="InstacashTT MVP",
    layout="wide",
)

# -----------------------
# STYLE OVERRIDES
# -----------------------
st.markdown(
    f"""
    <style>
        body {{
            background-color: {APPLE_BG};
            color: white;
        }}
        .stButton>button {{
            background-color: {APPLE_BLUE};
            color: white;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
            border: none;
        }}
        .stTextInput>div>div>input {{
            color: white;
            background-color: {APPLE_GRAY};
        }}
        .stNumberInput input {{
            color: white;
            background-color: {APPLE_GRAY};
        }}
        .card {{
            background-color: {APPLE_CARD};
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# AUTH HELPERS
# -----------------------
def authenticate(email, password):
    users = db["users"]
    if email in users and users[email]["password"] == password:
        return users[email]
    return None

def record_transaction(sender, receiver, amount):
    txn = {
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    db["transactions"].append(txn)
    save_db(db)

def get_user_transactions(email):
    return [
        t for t in db["transactions"]
        if t["sender"] == email or t["receiver"] == email
    ]

# -----------------------
# SESSION STATE
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = None

# -----------------------
# LOGIN UI
# -----------------------
def login_screen():
    st.title("💳 InstacashTT — Local Mode MVP")
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Incorrect email or password.")

# -----------------------
# DASHBOARD UI
# -----------------------
def dashboard_screen():
    email = st.session_state.user_email
    user = db["users"][email]

    st.title("👤 Customer Dashboard")
    st.markdown(f"<div class='card'>"
                f"<h3>Name: {user['name']}</h3>"
                f"<p><b>Email:</b> {email}</p>"
                f"<p><b>Balance:</b> ${user['balance']}</p>"
                f"</div>", unsafe_allow_html=True)

    st.subheader("Send Money")
    receiver = st.text_input("Receiver Email")
    amount = st.number_input("Amount", min_value=1.0, step=1.0)

    if st.button("Send"):
        if receiver not in db["users"]:
            st.error("Receiver not found.")
        elif receiver == email:
            st.error("You cannot send money to yourself.")
        elif amount > user["balance"]:
            st.error("Insufficient balance.")
        else:
            db["users"][email]["balance"] -= amount
            db["users"][receiver]["balance"] += amount
            save_db(db)
            record_transaction(email, receiver, amount)
            st.success(f"Sent ${amount} to {receiver}!")
            st.rerun()

    # -----------------------
    # TRANSACTION HISTORY
    # -----------------------
    st.subheader("📜 Transaction History")

    history = get_user_transactions(email)
    if not history:
        st.info("No transactions yet.")
    else:
        for tx in reversed(history):
            color = APPLE_GREEN if tx["receiver"] == email else APPLE_RED
            direction = "RECEIVED" if tx["receiver"] == email else "SENT"

            st.markdown(
                f"""
                <div class="card" style="border-left: 4px solid {color};">
                    <p><b>{direction}</b> ${tx["amount"]}</p>
                    <p><b>From:</b> {tx['sender']} | <b>To:</b> {tx['receiver']}</p>
                    <p><small>{tx['timestamp']}</small></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

# -----------------------
# MAIN ROUTER
# -----------------------
if not st.session_state.logged_in:
    login_screen()
else:
    dashboard_screen()
