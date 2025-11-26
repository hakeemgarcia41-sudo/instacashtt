import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import qrcode
from io import BytesIO

# -------------------------------------------------------------------
# INITIALIZE FIREBASE
# -------------------------------------------------------------------
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccount.json")  # ✅ Correct filename
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")

db = firestore.client()

# -------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------
def clean_email(email: str):
    """Convert email into a Firestore-safe document ID."""
    return email.strip().replace(".", "_dot_").replace("@", "_at_")

def hash_password(password: str):
    """Securely hash a password."""
    return hashlib.sha256(password.strip().encode()).hexdigest()

def get_user(email):
    doc_id = clean_email(email)
    return db.collection("users").document(doc_id).get()

def get_merchant(email):
    doc_id = clean_email(email)
    return db.collection("merchants").document(doc_id).get()

# -------------------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------------------
def register_user():
    st.header("Create Customer Account")

    name = st.text_input("Full Name", key="reg_name")
    email = st.text_input("Email", key="reg_email")
    phone = st.text_input("Phone Number", key="reg_phone")
    password = st.text_input("Password", type="password", key="reg_pass")

    if st.button("Register Customer"):
        if not (name and email and phone and password):
            st.error("All fields are required.")
            return

        user_ref = get_user(email)

        if user_ref.exists:
            st.error("This email is already registered.")
            return

        doc_id = clean_email(email)

        db.collection("users").document(doc_id).set({
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "password_hash": hash_password(password),
            "balance": 0,
            "role": "customer"
        })

        st.success("Account created successfully! You may now login.")

def register_merchant():
    st.header("Create Merchant Account")

    business = st.text_input("Business Name", key="biz_name")
    owner = st.text_input("Merchant Owner Name", key="biz_owner")
    email = st.text_input("Merchant Email", key="biz_email")
    phone = st.text_input("Merchant Phone", key="biz_phone")
    password = st.text_input("Password", type="password", key="biz_pass")

    if st.button("Register Merchant"):
        if not (business and owner and email and phone and password):
            st.error("All fields are required.")
            return

        merchant_ref = get_merchant(email)

        if merchant_ref.exists:
            st.error("This merchant email already exists.")
            return

        doc_id = clean_email(email)

        db.collection("merchants").document(doc_id).set({
            "business_name": business.strip(),
            "name": owner.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "password_hash": hash_password(password),
            "balance": 0,
            "role": "merchant"
        })

        st.success("Merchant account created successfully! You may now login.")

# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
def login():
    st.header("Sign In")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        hashed = hash_password(password)

        # Check customer
        user = get_user(email)
        if user.exists:
            data = user.to_dict()
            if data.get("password_hash") == hashed:
                st.session_state.logged_in = True
                st.session_state.user = data
                st.session_state.role = "customer"
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
            return

        # Check merchant
        merchant = get_merchant(email)
        if merchant.exists:
            data = merchant.to_dict()
            if data.get("password_hash") == hashed:
                st.session_state.logged_in = True
                st.session_state.user = data
                st.session_state.role = "merchant"
                st.success("Merchant login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
            return

        st.error("Account not found.")

# -------------------------------------------------------------------
# DASHBOARDS
# -------------------------------------------------------------------
def customer_dashboard():
    user = st.session_state.user
    st.subheader("👤 Customer Wallet Dashboard")

    st.write(f"**Name:** {user['name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Phone:** {user['phone']}")
    st.write(f"**Balance:** ${user['balance']}")

    amount = st.number_input("Enter Amount to Generate QR", min_value=0.01, step=0.01)

    if st.button("Generate Payment QR"):
        qr_data = f"PAYMENT_REQUEST|{user['email']}|{amount}"

        qr = qrcode.make(qr_data)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue())

def merchant_dashboard():
    user = st.session_state.user
    st.subheader("🏪 Merchant Dashboard")

    st.write(f"**Business Name:** {user['business_name']}")
    st.write(f"**Merchant Owner:** {user['name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Phone:** {user['phone']}")
    st.write(f"**Balance:** ${user['balance']}")

    amount = st.number_input("Enter Amount to Receive", min_value=0.01, step=0.01)

    if st.button("Generate Payment QR"):
        qr_data = f"MERCHANT_PAYMENT|{user['email']}|{amount}"

        qr = qrcode.make(qr_data)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue())

# -------------------------------------------------------------------
# MAIN APP ROUTER
# -------------------------------------------------------------------
def main():
    st.title("InstacashTT — Digital Wallet MVP")

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
        role = st.session_state.role
        st.success(f"Welcome, {st.session_state.user['email']}!")

        menu = ["Dashboard", "Logout"]
        choice = st.selectbox("Menu", menu)

        if choice == "Dashboard":
            if role == "customer":
                customer_dashboard()
            else:
                merchant_dashboard()

        if choice == "Logout":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

# -------------------------------------------------------------------
# RUN APP
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
