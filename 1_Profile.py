import pandas as pd
import streamlit as st

from shared.data import init_state, try_connect_db
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | Profile", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("Profile")

st.markdown('<div class="sst-brand">Profile<span>Your account details</span></div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.warning("Sign in from the sidebar to view your profile.")
else:
    if db_connected:
        history_count = len(db.get_history_db(st.session_state.username))
        saved_count = len(db.get_saved_db(st.session_state.username))
    else:
        history_count = len(st.session_state.history)
        saved_count = len(st.session_state.saved)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.write(f"**Username:** {st.session_state.username}")

    if db_connected:
        user = db.get_user(st.session_state.username)
        if user:
            if user.get("full_name"):
                st.write(f"**Full name:** {user['full_name']}")
            if user.get("email"):
                st.write(f"**Email:** {user['email']}")
            if user.get("created_at"):
                st.write(f"**Member since:** {pd.to_datetime(user['created_at']).strftime('%d %b %Y')}")

    st.write(f"**Total detections logged:** {history_count}")
    st.write(f"**Saved results:** {saved_count}")
    st.markdown('</div>', unsafe_allow_html=True)
