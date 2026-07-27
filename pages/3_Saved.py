import streamlit as st

from shared.data import init_state, try_connect_db, toggle_saved
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | Saved", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("Saved")

st.markdown('<div class="sst-brand">Saved<span>Results you starred from History</span></div>', unsafe_allow_html=True)

if db_connected and st.session_state.logged_in:
    st.session_state.saved = db.get_saved_db(st.session_state.username)
    history_rows = db.get_history_db(st.session_state.username)
    history_by_filename = {row["filename"]: row for row in history_rows}
else:
    history_by_filename = {entry["filename"]: entry for entry in st.session_state.history}

if not st.session_state.saved:
    st.info("Nothing saved yet. Star a result from the History page to see it here.")
else:
    for filename in st.session_state.saved:
        entry = history_by_filename.get(filename)
        col1, col2 = st.columns([5, 1])
        with col1:
            if entry:
                css_class = "result-mask" if entry["result"] == "Mask" else "result-nomask"
                st.markdown(
                    f"""<div class="result-card">
                            <b>{filename}</b><br>
                            <span class="{css_class}">{entry['result']}</span>
                            &nbsp;&middot;&nbsp; {entry['confidence'] * 100:.0f}% confidence
                        </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<div class="result-card"><b>{filename}</b></div>', unsafe_allow_html=True)
        with col2:
            if st.button("Remove", key=f"unsave_{filename}"):
                toggle_saved(filename)
                if db_connected and st.session_state.logged_in:
                    db.toggle_saved_db(st.session_state.username, filename)
                st.rerun()
