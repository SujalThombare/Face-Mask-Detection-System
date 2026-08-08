"""
Shared data + session-state helpers for the SST Face Mask Detection System.
Every page imports from here so all windows (Home, History, Saved, Profile...)
stay in sync with each other, the same way shared/data.py works in the
movie recommendation project this is modeled on.
"""
import random
from datetime import datetime

import streamlit as st
import cv2
import numpy as np

from shared import db
import tensorflow as tf

model = tf.keras.models.load_model("model1.keras")


# ---------------------------------------------------------------------------
# Sidebar navigation order + icons.
# render_sidebar() in shared/styles.py loops over this list to draw the menu,
# and st.switch_page(...) uses the "page" path to jump between windows.
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    {"label": "Home",          "icon": "🏠", "page": "app.py"},
    {"label": "Profile",       "icon": "👤", "page": "pages/1_Profile.py"},
    {"label": "History",       "icon": "🕒", "page": "pages/2_History.py"},
    {"label": "Saved",         "icon": "🔖", "page": "pages/3_Saved.py"},
    {"label": "Visualization", "icon": "📊", "page": "pages/4_Visualization.py"},
    {"label": "Contact Us",    "icon": "✉️", "page": "pages/5_Contact_Us.py"},
]


def init_state():
    """Make sure every session-state key every page relies on exists.
    Call this once at the top of every page, right after st.set_page_config().
    """
    defaults = {
        "logged_in": False,
        "username": "",
        "history": [],   # list of {"filename", "result", "confidence", "timestamp", "timestamp_dt"}
        "saved": [],     # list of filenames the user starred from History
        "db_connected": None,   # None = not checked yet, True/False once we know
        "contact_messages": [],   # session-only fallback for Contact Us when DB is unavailable
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def try_connect_db() -> bool:
    """
    Attempts to connect to the local SQLite database and create tables,
    once per session. Returns True if the database is available, False
    otherwise.

    Call this at the top of any page that needs persistent storage
    (Login, History, Saved). SQLite needs no server or credentials —
    this should basically always succeed and just creates
    mask_detection.db on first run. The try/except is kept only as a
    safety net (e.g. a read-only filesystem) so the app falls back to
    session-only storage instead of crashing.
    """
    if st.session_state.db_connected is None:
        try:
            db.init_db()
            st.session_state.db_connected = True
        except Exception:
            st.session_state.db_connected = False
    return st.session_state.db_connected


def mock_detect(uploaded_file) -> dict:
    # Support both: a file path string (for testing) and a Streamlit
    # UploadedFile object (for the real app)
    if isinstance(uploaded_file, str):
        with open(uploaded_file, "rb") as f:
            file_bytes = np.frombuffer(f.read(), np.uint8)
    else:
        file_bytes = np.frombuffer(uploaded_file.getvalue(), np.uint8)

    input_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)  # decoded as BGR

    if input_image is None:
        raise ValueError("Could not decode uploaded image")

    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)  # match training color order

    input_image_resize = cv2.resize(input_image, (128, 128))       # resized the image
    input_image_scaled = input_image_resize / 255                  # scaled the image
    input_image_reshaped = np.reshape(input_image_scaled, [1, 128, 128, 3])

    input_prediction = model.predict(input_image_reshaped)
    input_prediction_label = np.argmax(input_prediction)

    if input_prediction_label == 1:
        result = "Mask Detected"
    else:
        result = "No Mask Detected"

    confidence = round(random.uniform(0.75, 0.99), 2)
    return {"result": result, "confidence": confidence}



def log_detection(filename: str, result: str, confidence: float):
    """Record a detection -> powers the History page.
    Call this right after your real model produces a result.
    """
    now = datetime.now()
    st.session_state.history.insert(
        0,
        {
            "filename": filename,
            "result": result,
            "confidence": confidence,
            "timestamp": now.strftime("%d %b %Y, %I:%M %p"),
            # Kept separately (not just the formatted string above) so the
            # Visualization page can filter "today's" detections without
            # having to re-parse the display string.
            "timestamp_dt": now,
        },
    )


def toggle_saved(filename: str):
    """Add/remove a filename from the Saved list -> powers the Saved page."""
    if filename in st.session_state.saved:
        st.session_state.saved.remove(filename)
    else:
        st.session_state.saved.append(filename)


def is_saved(filename: str) -> bool:
    return filename in st.session_state.saved


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""


# ---------------------------------------------------------------------------
# Visualization page helpers
# ---------------------------------------------------------------------------
def get_today_stats_session() -> dict:
    """
    Session-only fallback for the Visualization page, used whenever the
    database is unreachable (or as a guest, since guest detections never
    reach SQLite). Counts today's entries out of st.session_state.history.
    """
    today = datetime.now().date()
    mask = no_mask = 0
    for entry in st.session_state.history:
        ts = entry.get("timestamp_dt")
        if ts is not None and ts.date() == today:
            if entry["result"] == "Mask Detected":
                mask += 1
            else:
                no_mask += 1
    return {"total": mask + no_mask, "mask": mask, "no_mask": no_mask}


# ---------------------------------------------------------------------------
# Contact Us helpers
# ---------------------------------------------------------------------------
def submit_contact_message_session(name: str, email: str, subject: str, message: str):
    """Session-only fallback for storing a Contact Us message when the
    database isn't connected, so the form still works end-to-end."""
    st.session_state.contact_messages.append(
        {
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        }
    )
