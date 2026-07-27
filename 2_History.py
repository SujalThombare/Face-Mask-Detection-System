import streamlit as st

from shared.data import init_state, try_connect_db, toggle_saved, is_saved
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | History", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("History")

st.markdown('<div class="sst-brand">History<span>Every detection you\'ve run</span></div>', unsafe_allow_html=True)

# Prefer real data from SQLite when the user is signed in and the DB is
# reachable; otherwise fall back to this session's in-memory list.
if db_connected and st.session_state.logged_in:
    history = db.get_history_db(st.session_state.username)
    # Normalize field names so the display code below works either way
    history = [
        {
            "filename": row["filename"],
            "result": row["result"],
            "confidence": row["confidence"],
            "timestamp": row["created_at"].strftime("%d %b %Y, %I:%M %p") if row["created_at"] else "",
        }
        for row in history
    ]
else:
    history = st.session_state.history

# Keep the in-memory "saved" list in sync with the DB so is_saved()
# (used for the star icon below) reflects what's really saved.
if db_connected and st.session_state.logged_in:
    st.session_state.saved = db.get_saved_db(st.session_state.username)

if not history:
    st.info("No detections yet. Run one from the Home page.")
else:
    for i, entry in enumerate(history):
        css_class = "result-mask" if entry["result"] == "Mask" else "result-nomask"
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""<div class="result-card">
                        <b>{entry['filename']}</b><br>
                        <span class="{css_class}">{entry['result']}</span>
                        &nbsp;&middot;&nbsp; {entry['confidence'] * 100:.0f}% confidence
                        &nbsp;&middot;&nbsp; {entry['timestamp']}
                    </div>""",
                unsafe_allow_html=True,
            )
        with col2:
            star = "★ Saved" if is_saved(entry["filename"]) else "☆ Save"
            if st.button(star, key=f"save_{i}"):
                toggle_saved(entry["filename"])
                if db_connected and st.session_state.logged_in:
                    db.toggle_saved_db(st.session_state.username, entry["filename"])
                st.rerun()
