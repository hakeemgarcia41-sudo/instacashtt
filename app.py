import streamlit as st
import json
import os

# ---------------------------------------------------------
# DATABASE PATH (WORKS LOCALLY + STREAMLIT CLOUD)
# ---------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")

# ---------------------------------------------------------
# LOAD DATABASE
# ---------------------------------------------------------
def load_db():
    if not os.path.exists(DB_PATH):
        st.error("Database file missing.")
        return {"users": {}}

    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return {"users": {}}

# ---------------------------------------------------------
# SAVE DATABASE
# ---------------------------------------------------------
def save_db(db):
    try:
        with open(DB_PATH, "w") as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        st.error(f"Error saving database: {e}")

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
def login_user(email, password):
    db = load_db()
    users = db.get("users", {})

    if email not in users:
        return None, "Account not found."

    if users[email]["password"] != password:
        return None, "Incorrect password."

    return users[email], None

# ---------------------------------------------------------
# SEND MONEY
# ---------------------------------------------------------
def send_money(sender_email, receiver_email, amount):
    db = load_db()
    users = db.get("users", {})

    if receiver_email not in users:
        return False, "Receiver not found."

    if users[sender_email]["balance"] < amount:
        return False, "Insufficient funds."

    # Process transfer
    users[sender_email]["balance"] -= amount
    users[receiver_email]["balance"] += amount

    save_db(db)
    return True, "Transfer successful!"

# ---------------------------------------------------------
# DASHBOARD – CUSTOMER VIEW
# ---------------------------------------------------------
def customer_dashboard(user_email):
    db = load_db()
    user = db["users"][user_email]

    st.subheader("👤 Customer Dashboard")
    st.write(f"**Name:** {user['name']}")
    st.write(f"**Email:** {user_email}")
    st.write(f"**Balance:** ${user['balance']}")

    st.markdown("---")
    st.header("Send Money")

    receiver = st.text_input("Receiver Email")
    amount = st.number_input("Amount", min_value=1.0, step=1.0)

    if st.button("Send"):
        success, msg = send_money(user_email, receiver, amount)
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

# ---------------------------------------------------------
# MAIN APP UI
# ---------------------------------------------------------
def main():
    st.title("💳 InstacashTT — Local Mode MVP")

    menu = ["Login"]
    choice = st.selectbox("Menu", menu)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = None

    if not st.session_state.logged_in:

        if choice == "Login":
            st.header("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                user, error = login_user(email, password)

                if error:
                    st.error(error)
                else:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.success("Login successful!")
                    st.rerun()

    else:
        # Logged in dashboard
        customer_dashboard(st.session_state.email)

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.email = None
            st.rerun()


# ---------------------------------------------------------
# RUN APP
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
