import streamlit as st

from shared.data import init_state, try_connect_db, submit_contact_message_session
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | Contact Us", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("Contact Us")

st.markdown(
    '<div class="sst-brand">Contact Us<span>Questions, feedback, or bug reports</span></div>',
    unsafe_allow_html=True,
)

if not db_connected:
    st.warning(
        "⚠️ Running without a database connection — your message will only be kept "
        "for this browser session and won't be saved permanently."
    )

col_form, col_info = st.columns([2, 1])

with col_form:
    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    # Prefill name/email for a signed-in user as a convenience; still editable.
    default_name = ""
    default_email = ""
    if st.session_state.logged_in and db_connected:
        user = db.get_user(st.session_state.username)
        if user:
            default_name = user.get("full_name") or st.session_state.username
            default_email = user.get("email") or ""

    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Name", value=default_name)
        email = st.text_input("Email", value=default_email)
        subject = st.text_input("Subject")
        message = st.text_area("Message", height=160)
        submitted = st.form_submit_button("✉️ Send Message")

    if submitted:
        if not name.strip() or not email.strip() or not message.strip():
            st.error("Please fill in your name, email, and a message before sending.")
        else:
            if db_connected:
                success, feedback = db.save_contact_message(
                    name.strip(), email.strip(), subject.strip(), message.strip()
                )
                if success:
                    st.success(feedback)
                else:
                    # DB hiccup mid-request — don't lose the message, fall
                    # back to session storage instead of failing outright.
                    submit_contact_message_session(name.strip(), email.strip(), subject.strip(), message.strip())
                    st.warning(f"Saved to this session only ({feedback}).")
            else:
                submit_contact_message_session(name.strip(), email.strip(), subject.strip(), message.strip())
                st.success("Message saved for this session. Connect the database to store messages permanently.")

    st.markdown('</div>', unsafe_allow_html=True)

with col_info:
   # """st.markdown(
     #   <div class="result-card">
     #           <b>SST Support</b><br><br>
       #         📧 support@sst-maskdetection.example<br>
       #         🕒 Mon–Fri, 9am–6pm<br><br>
       #         Reach out with bugs, feature requests, or questions about
       #         how detections are made — we read every message.
       #     </div>
       # unsafe_allow_html=True,
    #)"""
    st.title(" 📧 SST support ")
    st.write("Developer Name : Sujal Thombare")
    st.write("Email : sujalthombare2468@gmail.com")
    st.write("LinkedIn : www.linkedin.com/in/sujal-thombare-69235541a")
    st.write("GitHub: https://github.com/SujalThombare")
    st.write("LeetCode: https://leetcode.com/u/sujal_2468/")

# ---------------------------------------------------------------------- (Only) sender's own recent messages this session
if st.session_state.contact_messages:
    st.divider()
    st.markdown("#### Sent this session")
    for entry in reversed(st.session_state.contact_messages):
        st.markdown(
            f"""<div class="result-card">
                    <b>{entry['subject'] or '(no subject)'}</b><br>
                    <span style="color:#9a9aa2;">{entry['timestamp']}</span><br>
                    {entry['message']}
                </div>""",
            unsafe_allow_html=True,
        )
