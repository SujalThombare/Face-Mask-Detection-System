import streamlit as st

from shared.data import init_state, try_connect_db
from shared.styles import inject_css
from shared import db

st.set_page_config(page_title="SST | Sign In", page_icon="😷", layout="centered")
init_state()
inject_css()

# Try to connect to the local SQLite database once per session. This
# should basically always succeed (no server/credentials needed) — if
# db_connected somehow ends up False (e.g. read-only filesystem), we
# fall back to the old demo behaviour (accepts any non-empty
# username/password) so the UI still works.
db_connected = try_connect_db()

# No sidebar on the login page — matches the reference design where
# auth screens are standalone, full-focus windows.

st.markdown(
    '<div class="sst-brand" style="text-align:center;border:none;">SST'
    '<span style="text-align:center;">Face Mask Detection System</span></div>',
    unsafe_allow_html=True,
)

if not db_connected:
    st.warning(
        "Running without a database connection — accounts won't be saved. "
        "Check that the app folder is writable so mask_detection.db can be created."
    )

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"   # "signin" | "signup"

st.markdown('<div class="auth-card">', unsafe_allow_html=True)

if st.session_state.auth_mode == "signin":
    st.subheader("Sign In")

    st.text_input("Username", key="signin_username")
    st.text_input("Password", type="password", key="signin_password")

    if st.button(">-- Sign In", key="btn_signin"):
        username = st.session_state.signin_username
        password = st.session_state.signin_password

        if db_connected:
            # Real check against the users table in SQLite.
            if db.verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.switch_page("app.py")
            else:
                st.error("Incorrect username or password.")
        else:
            # Fallback demo behaviour when there's no DB configured yet.
            st.session_state.logged_in = True
            st.session_state.username = username or "Guest"
            st.switch_page("app.py")

    st.write("Don't have an account?")
    if st.button(">-- Go to Sign Up", key="btn_goto_signup"):
        st.session_state.auth_mode = "signup"
        st.rerun()

else:
    st.subheader("Sign Up")

    st.text_input("Full Name", key="signup_fullname")
    st.text_input("Username", key="signup_username")
    st.text_input("Email", key="signup_email")
    st.text_input("Password", type="password", key="signup_password")
    st.text_input("Confirm Password", type="password", key="signup_confirm_password")

    if st.button(">-- Create Account", key="btn_signup"):
        password = st.session_state.signup_password
        confirm = st.session_state.signup_confirm_password
        username = st.session_state.signup_username

        if not username or not password:
            st.error("Username and password are required.")
        elif password != confirm:
            st.error("Passwords don't match.")
        elif db_connected:
            success, message = db.register_user(
                username=username,
                password=password,
                full_name=st.session_state.signup_fullname,
                email=st.session_state.signup_email,
            )
            if success:
                st.session_state.auth_mode = "signin"
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        else:
            # No DB configured yet — just bounce back to Sign In, same as before.
            st.session_state.auth_mode = "signin"
            st.rerun()

    st.write("Already have an account?")
    if st.button(">-- Go to Sign In", key="btn_goto_signin"):
        st.session_state.auth_mode = "signin"
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
