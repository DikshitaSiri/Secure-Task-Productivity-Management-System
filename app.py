import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ---------- DATABASE ----------
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task TEXT,
    status TEXT,
    created_at TEXT
)
""")
conn.commit()

# ---------- HELPERS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    hashed = hash_password(password)
    user = cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (username, hashed)
    ).fetchone()
    return user

# ---------- SESSION ----------
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------- AUTH UI ----------
st.title("🔐 Task Manager with Login")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create New Account")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (new_user, hash_password(new_pass))
            )
            conn.commit()
            st.success("Account created! Please login.")
        except:
            st.error("Username already exists")

elif choice == "Login":
    st.subheader("Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        auth = authenticate(user, pwd)
        if auth:
            st.session_state.user_id = auth[0]
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

# ---------- MAIN APP ----------
if st.session_state.user_id:
    st.subheader("➕ Add Task")

    task = st.text_input("Task name")

    if st.button("Add Task"):
        cursor.execute(
            "INSERT INTO tasks VALUES (NULL, ?, ?, 'Pending', ?)",
            (st.session_state.user_id, task, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        st.success("Task added")

    st.subheader("📋 Your Tasks")

    tasks = cursor.execute(
        "SELECT id, task, status FROM tasks WHERE user_id=?",
        (st.session_state.user_id,)
    ).fetchall()

    for tid, t, s in tasks:
        col1, col2, col3 = st.columns([4, 2, 2])
        col1.write(t)

        if s == "Pending":
            if col2.button("✅ Done", key=f"done{tid}"):
                cursor.execute(
                    "UPDATE tasks SET status='Completed' WHERE id=?",
                    (tid,)
                )
                conn.commit()
                st.experimental_rerun()
        else:
            col2.success("Completed")

        if col3.button("🗑 Delete", key=f"del{tid}"):
            cursor.execute("DELETE FROM tasks WHERE id=?", (tid,))
            conn.commit()
            st.experimental_rerun()

    if st.button("Logout"):
        st.session_state.user_id = None
        st.experimental_rerun()
