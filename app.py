import streamlit as st
import json
import os
import hashlib
from datetime import datetime

# ============================================================
#  LOCAL DATABASE (JSON FILE)
# ============================================================

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"users": {}, "merchants": {}, "transactions": []}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# ============================================================
#  UTILITY FUNCTIONS
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(email):
    return email in db["users"]

def merchant_exists(email):
    return email in db["merchants"]

def create_transaction(sender, receiver, amount, ttype):
    db["transactions"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "type": ttype,
    })
    save_db(db)

# ============================================================
#  REGISTRATION
# ============================================================

def register_user():
    st.header("Create Customer Account")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register Customer"):
        if user_exists(email):
            st.error("This email is already registered.")
            return

        db["users"][email] = {
            "name": name,
            "email": email,
            "password": hash_password(password),
            "balance": 1000.0,  # Initial demo balance
            "role": "customer",
        }

        save_db(db)
        st.success("Customer registered successfully!")

def register_merchant():
    st.header("Create Merchant Account")

    business = st.text_input("Business Name")
    email = st.text_input("Merchant Email")
    password = st.text_input("Password", type="password")

    if st.button("Register Merchant"):
        if merchant_exists(email):
            st.error("Merchant already exists.")
            return

        db["merchants"][email] = {
            "business_name": business,
            "email": email,
            "password": hash_password(password),
            "balance": 0.0,
            "role": "merchant",
        }

        save_db(db)
        st.success("Merchant registered successfully!")

# ============================================================
#  LOGIN
# ============================================================

def login():
    st.header("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        hashed = hash_password(password)

        # Check Users
        if user_exists(email):
            user = db["users"][email]
            if user["password"] == hashed:
                st.session_state.logged_in = True
                st.session_state.role = "customer"
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect password.")

        # Check Merchants
        elif merchant_exists(email):
            user = db["merchants"][email]
            if user["password"] == hashed:
                st.session_state.logged_in = True
                st.session_state.role = "merchant"
                st.session_state.user = user
                st.success("Merchant login successful!")
                st.rerun()
            else:
                st.error("Incorrect password.")

        else:
            st.error("Account not found.")

# ============================================================
#  CUSTOMER DASHBOARD
# ============================================================

def customer_dashboard():
    user = st.session_state.user
    st.subheader("👤 Customer Dashboard")

    st.write(f"**Name:** {user['name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Balance:** ${user['balance']}")

    st.divider()
    st.subheader("Send Money")

    recipient = st.text_input("Receiver Email")
    amount = st.number_input("Amount", min_value=1.0, step=1.0)

    if st.button("Send"):
        if user["balance"] < amount:
            st.error("Insufficient balance.")
            return

        if not (user_exists(recipient) or merchant_exists(recipient)):
            st.error("Receiver not found.")
            return

        # Update balances
        if user_exists(recipient):
            db["users"][recipient]["balance"] += amount
        else:
            db["merchants"][recipient]["balance"] += amount

        db["users"][user["email"]]["balance"] -= amount
        save_db(db)

        create_transaction(user["email"], recipient, amount, "send")

        st.success(f"Successfully sent ${amount} to {recipient}!")
        st.rerun()

    st.divider()
    st.subheader("Transaction History")

    for tx in db["transactions"]:
        if tx["sender"] == user["email"] or tx["receiver"] == user["email"]:
            st.write(tx)

# ============================================================
#  MERCHANT DASHBOARD
# ============================================================

def merchant_dashboard():
    user = st.session_state.user
    st.subheader("🏪 Merchant Dashboard")

    st.write(f"**Business:** {user['business_name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Balance:** ${user['balance']}")

    st.divider()
    st.subheader("Receive Payment Request")

    sender = st.text_input("Customer Email")
    amount = st.number_input("Amount", min_value=1.0)

    if st.button("Request Payment"):
        if not user_exists(sender):
            st.error("Customer not found.")
            return

        if db["users"][sender]["balance"] < amount:
            st.error("Customer lacks sufficient balance.")
            return

        # Transfer funds
        db["users"][sender]["balance"] -= amount
        db["merchants"][user["email"]]["balance"] += amount

        save_db(db)
        create_transaction(sender, user["email"], amount, "receive")

        st.success("Payment received!")

    st.divider()
    st.subheader("Transactions")

    for tx in db["transactions"]:
        if tx["receiver"] == user["email"] or tx["sender"] == user["email"]:
            st.write(tx)

# ============================================================
#  MAIN APP
# ============================================================

def main():
    st.title("💳 InstacashTT — Local Mode MVP")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        menu = ["Login", "Register Customer", "Register Merchant"]
        choice = st.selectbox("Menu", menu)

        if choice == "Login":
            login()
        elif choice == "Register Customer":
            register_user()
        elif choice == "Register Merchant":
            register_merchant()

    else:
        st.success(f"Welcome, {st.session_state.user['email']}!")

        menu = ["Dashboard", "Logout"]
        choice = st.selectbox("Menu", menu)

        if choice == "Dashboard":
            if st.session_state.role == "customer":
                customer_dashboard()
            else:
                merchant_dashboard()

        if choice == "Logout":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()


if __name__ == "__main__":
    main()
