"""
Shared data + session-state helpers for the SST Face Mask Detection System.
Every page imports from here so all windows (Home, History, Saved, Profile...)
stay in sync with each other, the same way shared/data.py works in the
movie recommendation project this is modeled on.
"""
import random
from datetime import datetime

import streamlit as st
import numpy as np

from shared import db

import cv2

import tensorflow as tf

model = tf.keras.models.load_model("model.keras")

# ---------------------------------------------------------------------------
# Sidebar navigation order + icons.
# render_sidebar() in shared/styles.py loops over this list to draw the menu,
# and st.switch_page(...) uses the "page" path to jump between windows.
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    {"label": "Home",    "icon": "🏠", "page": "app.py"},
    {"label": "Profile", "icon": "👤", "page": "pages/1_Profile.py"},
    {"label": "History", "icon": "🕒", "page": "pages/2_History.py"},
    {"label": "Saved",   "icon": "🔖", "page": "pages/3_Saved.py"},
]


def init_state():
    """Make sure every session-state key every page relies on exists.
    Call this once at the top of every page, right after st.set_page_config().
    """
    defaults = {
        "logged_in": False,
        "username": "",
        "history": [],   # list of {"filename", "result", "confidence", "timestamp"}
        "saved": [],     # list of filenames the user starred from History
        "db_connected": None,   # None = not checked yet, True/False once we know
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

import cv2
import numpy as np
import random

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


def live_detect(frame):

    # Convert BGR (OpenCV) to RGB
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Resize exactly as during training
    img = cv2.resize(img, (128, 128))

    # Normalize
    img = img.astype("float32") / 255.0

    # Add batch dimension
    img = np.expand_dims(img, axis=0)

    # Prediction
    prediction = model.predict(img, verbose=0)

    confidence = float(np.max(prediction) * 100)

    predicted_class = np.argmax(prediction)

    if predicted_class == 1:
        result = "😷 With Mask"
        color = (0, 255, 0)
    else:
        result = "❌ Without Mask"
        color = (0, 0, 255)

    # Draw prediction on live frame
    cv2.putText(
        frame,
        f"{result} ({confidence:.2f}%)",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2
    )

    return {
        "result": result,
        "confidence": confidence,
        "frame": frame
    }
def log_detection(filename: str, result: str, confidence: float):
    """Record a detection -> powers the History page.
    Call this right after your real model produces a result.
    """
    st.session_state.history.insert(
        0,
        {
            "filename": filename,
            "result": result,
            "confidence": confidence,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
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
