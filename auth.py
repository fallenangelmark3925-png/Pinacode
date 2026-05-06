import sqlite3
import streamlit as st
import os
import hashlib
from pathlib import Path

DB_FILE = Path(__file__).parent / "data" / "expenses.db"
BG_IMG_URL = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"


def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def init_auth():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None

    os.makedirs(DB_FILE.parent, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed_pw = hash_password("admin123")
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_pw))

    conn.commit()
    conn.close()


def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hashed_input = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_input))
    user = cursor.fetchone()
    conn.close()

    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False


def create_user(username, password):
    if not username.strip() or not password.strip():
        st.error("Fields cannot be left blank.")
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        st.success(f"✨ Account '{username}' created!")
        return True
    except sqlite3.IntegrityError:
        st.error("⚠️ That username is already taken.")
        return False
    finally:
        conn.close()


def reset_password(username, new_password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        hashed_pw = hash_password(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()


def render_login_page():
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{BG_IMG_URL}");
            background-size: cover; background-attachment: fixed;
        }}
        div[data-testid="stMetric"], .stForm, .stDataFrame {{
            background: rgba(255, 255, 255, 0.08) !important;
            border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px; backdrop-filter: blur(2px);
        }}
        h1, h2, h3, p, span, label {{ color: #ffffff !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
        </style>
        """, unsafe_allow_html=True)

    st.title("🔐 FinTrack Pro Security Portal")

    tab1, tab2, tab3 = st.tabs(["🔑 Sign In", "📝 Create Account", "🔄 Reset Password"])

    with tab1:
        with st.form("login_form"):
            user = st.text_input("Username", key="login_user").strip()
            pw = st.text_input("Password", type="password", key="login_pw")
            submit = st.form_submit_button("Login")
            if submit:
                if check_login(user, pw):
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab2:
        with st.form("signup_form"):
            st.write("### Register a New Profile")
            new_user = st.text_input("Choose Username", key="signup_user").strip()
            new_pw = st.text_input("Choose Password", type="password", key="signup_pw")
            confirm_pw = st.text_input("Confirm Password", type="password", key="signup_confirm_pw")
            signup_submit = st.form_submit_button("Register Account")

            if signup_submit:
                if new_pw != confirm_pw:
                    st.error("Passwords do not match!")
                elif len(new_pw) < 6:
                    st.error("For security, use at least 6 characters.")
                else:
                    create_user(new_user, new_pw)

    with tab3:
        with st.form("forgot_form"):
            st.write("### Reset Your Password")
            f_user = st.text_input("Enter Username", key="forgot_user").strip()
            f_new_pw = st.text_input("New Password", type="password", key="forgot_pw")
            f_confirm_pw = st.text_input("Confirm New Password", type="password", key="forgot_confirm_pw")
            reset_submit = st.form_submit_button("Update Password")

            if reset_submit:
                if f_new_pw != f_confirm_pw:
                    st.error("Passwords do not match!")
                elif len(f_new_pw) < 6:
                    st.error("New password must be at least 6 characters.")
                elif f_user:
                    if reset_password(f_user, f_new_pw):
                        st.success("✅ Password updated! You can now log in.")
                    else:
                        st.error("⚠️ Username not found.")
                else:
                    st.error("Please enter your username.")