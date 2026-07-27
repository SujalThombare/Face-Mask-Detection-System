import streamlit as st


from shared.data import init_state, try_connect_db, mock_detect, log_detection, toggle_saved, is_saved, live_detect
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | Home", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("Home")

# ---------------------------------------------------------------------- HEADER
st.markdown(
    '<div class="sst-brand">SST<span>Face Mask Detection System</span></div>',
    unsafe_allow_html=True,
)

if not st.session_state.logged_in:
    st.info("You're browsing as a guest. Sign in from the sidebar to save your detection history.")

# ---------------------------------------------------------------------- UPLOAD / CAPTURE
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📁 Add Photo")
    uploaded_file = st.file_uploader(
        "Upload an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
    )

with col2:
    st.markdown("#### 📷 Click Photo")
    captured_file = st.camera_input("Take a photo", label_visibility="collapsed") 
# Whichever input was provided (upload takes priority if both are given)
active_file = uploaded_file or captured_file

st.divider()

# ---------------------------------------------------------------------- DETECTION RESULT
st.markdown("### Detection Result")

if active_file is None:
    st.markdown(
        '<div class="result-card">Upload or capture a photo above to run detection.</div>',
        unsafe_allow_html=True,
    )
else:
    st.image(active_file, width=320)

    if st.button("Run Detection", key="btn_run_detection"):
       
        outcome = mock_detect(active_file)
        st.session_state["last_result"] = outcome
        log_detection(active_file.name, outcome["result"], outcome["confidence"])

        # Persist to SQLite too, so it shows up in History/Profile after a
        # restart — only possible once the user is signed in with a
        # real username, and only if the DB is actually connected.
        if db_connected and st.session_state.logged_in:
            db.log_detection_db(
                st.session_state.username, active_file.name,
                outcome["result"], outcome["confidence"],
            )

        st.toast(f"Detection saved to History: {outcome['result']}")

    last_result = st.session_state.get("last_result")
    if last_result:
        css_class = "result-mask" if last_result["result"] == "Mask" else "result-nomask"
        st.markdown(
            f"""<div class="result-card">
                    <span class="{css_class}">{last_result['result']}</span>
                    &nbsp;&middot;&nbsp; Confidence: {last_result['confidence'] * 100:.0f}%
                </div>""",
            unsafe_allow_html=True,
        )
        if st.button("🔖 Save this result", key="btn_save_result"):
            toggle_saved(active_file.name)
            if db_connected and st.session_state.logged_in:
                db.toggle_saved_db(st.session_state.username, active_file.name)
            st.toast(
                "Added to Saved" if is_saved(active_file.name) else "Removed from Saved"
            )

