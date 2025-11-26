import streamlit as st
import json
from datetime import datetime

DB_FILE = "database.json"

# -------------------------
# Load / Save Database
# -------------------------
def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


# -------------------------
# Apple-Style UI Theme
# -------------------------
st.markdown(
    """
    <style>
        body {
            background-color: #1C1C1E;
            color: #E5E5EA;
        }

        .stApp {
            background-color: #1C1C1E !important;
        }

        .stTextInput textarea, .stTextInput input {
            background-color: #2C2C2E !important;
            color: #E5E5EA !important;
            border-radius: 10px !important;
        }

        .stNumberInput input {
            background-color: #2C2C2E !important;
            color: #E5E5EA !important;
            border-radius: 10px !important;
        }

        .stButton>button {
            background-color: #0A84FF !important;
            color: white !important;
            border-radius: 12px !important;
            border: none !important;
            padding: 0.5rem 1.2rem !important;
        }

        .balance-card {
            background-color: #2C2C2E;
            padding: 20px;
            border-radius: 15px;
            margin-top: 10px;
            margin-bottom: 20px;
        }

        .transaction-card {
            background-color: #2C2C2E;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 10px;
        }

        .sent {
            color: #FF453A;   /* Apple Red */
        }
        .received {
            color: #30D158;   /* Apple Green */
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Login Function
# -------------------------
def login_user(email, password):
    db = load_db()
    if email in db["users"]:
        if db["users"][email]["password"] == password:
            return True, db["users"][email]
        return False, "Incorrect password."
    return False, "Account not found."


# -------------------------
# Send Money + Log Transfer
# -------------------------
def send_money(sender_email, receiver_email, amount):
    db = load_db()

    if receiver_email not in db["users"]:
        return False, "Receiver not found."

    if db["users"][sender_email]["balance"] < amount:
        return False, "Insufficient funds."

    # Update balances
    db["users"][sender_email]["balance"] -= amount
    db["users"][receiver_email]["balance"] += amount

    # Log transaction
    transaction = {
        "sender": sender_email,
        "receiver": receiver_email,
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    db["transactions"].append(transaction)
    save_db(db)

    return True, "Transfer completed."


# -------------------------
# Show Transaction History
# -------------------------
def show_history(email):
    st.subheader("📜 Transaction History")

    db = load_db()
    history = db["transactions"]

    user_history = [t for t in history if t["sender"] == email or t["receiver"] == email]

    user_history.reverse()

    for t in user_history:
        is_sender = t["sender"] == email

        amount_display = f"-${t['amount']}" if is_sender else f"+${t['amount']}"
        label = "Sent to" if is_sender else "Received from"
        counterparty = t["receiver"] if is_sender else t["sender"]
        color_class = "sent" if is_sender else "received"

        st.markdown(
            f"""
            <div class="transaction-card">
                <p class="{color_class}" style="font-size: 20px;"><b>{amount_display}</b></p>
                <p>{label}: <b>{counterparty}</b></p>
                <small>{t["timestamp"]}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -------------------------
# Dashboard
# -------------------------
def dashboard(user_email, user_data):
    st.subheader("🧑‍💼 Customer Dashboard")

    st.markdown(
        f"""
        <div class="balance-card">
            <h3>{user_data["name"]}</h3>
            <p><b>Email:</b> {user_email}</p>
            <h2>Balance: ${user_data["balance"]}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("💸 Send Money")

    receiver = st.text_input("Receiver Email")
    amount = st.number_input("Amount", min_value=1.0, step=1.0)

    if st.button("Send"):
        success, msg = send_money(user_email, receiver, amount)
        if success:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("---")
    show_history(user_email)


# -------------------------
# MAIN APP
# -------------------------
st.title("💳 InstacashTT — Local Mode MVP")

menu = st.selectbox("Menu", ["Login"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        ok, data = login_user(email, password)

        if ok:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_data = data
            st.experimental_rerun()
        else:
            st.error(data)

else:
    dashboard(st.session_state.user_email, st.session_state.user_data)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()
