import pandas as pd
import streamlit as st

from shared.data import init_state, try_connect_db, get_today_stats_session
from shared.styles import inject_css, render_sidebar
from shared import db

st.set_page_config(page_title="SST | Visualization", page_icon="😷", layout="wide")
init_state()
db_connected = try_connect_db()
inject_css()
render_sidebar("Visualization")

st.markdown(
    '<div class="sst-brand">Visualization<span>Today\'s detections at a glance</span></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------- DATA
# Prefer the database (combined across every signed-in user) whenever it's
# reachable. If the DB is down for any reason, or nothing has been written
# to it yet, fall back to this session's in-memory history so the page
# never breaks and always shows *something* useful — including detections
# run as a guest, which never reach SQLite in the first place.
db_error = None
stats = None

if db_connected:
    try:
        stats = db.get_today_detection_stats()
    except Exception as e:
        # Defensive: a DB hiccup here should never take the whole page
        # down — just fall back to session data instead.
        db_error = str(e)
        stats = None

session_stats = get_today_stats_session()

if stats is None or (stats["total"] == 0 and session_stats["total"] > 0):
    stats = session_stats
    source_note = (
        "Database unavailable — showing detections from this browser session only."
        if not db_connected or db_error
        else "No detections recorded in the database yet today — showing this session's activity instead."
    )
else:
    # Combine DB-backed detections (signed-in users) with any guest
    # detections from this session that never made it to SQLite, so the
    # dashboard reflects everything that happened today, not just one source.
    guest_only = session_stats["total"] > 0 and not st.session_state.logged_in
    if guest_only:
        stats = {
            "total": stats["total"] + session_stats["total"],
            "mask": stats["mask"] + session_stats["mask"],
            "no_mask": stats["no_mask"] + session_stats["no_mask"],
        }
        source_note = "Combining database totals (signed-in users) with this guest session's detections."
    else:
        source_note = "Live totals from the database, combined across all signed-in users."

if not db_connected:
    st.warning(
        "⚠️ Running without a database connection — visualization is limited to this "
        "browser session. Detections still work normally; check that the app folder "
        "is writable so mask_detection.db can be created for persistent, app-wide stats."
    )
elif db_error:
    st.warning(f"⚠️ Could not read stats from the database ({db_error}). Showing session data instead.")

st.caption(source_note)
st.divider()

# ---------------------------------------------------------------------- METRICS
total, mask, no_mask = stats["total"], stats["mask"], stats["no_mask"]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""<div class="metric-card">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Detections Today</div>
            </div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div class="metric-card">
                <div class="metric-value" style="color:#3ddc84;">{mask}</div>
                <div class="metric-label">Mask Detected</div>
            </div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div class="metric-card">
                <div class="metric-value" style="color:#ff1e2d;">{no_mask}</div>
                <div class="metric-label">No Mask Detected</div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------- BREAKDOWN
if total == 0:
    st.info("No detections have been run yet today. Head to Home to run one.")
else:
    mask_pct = round(mask / total * 100)
    nomask_pct = 100 - mask_pct

    st.markdown("#### Breakdown")
    st.markdown(
        f"""
        <div class="bar-row">
            <div class="bar-label" style="color:#3ddc84;">😷 Mask</div>
            <div class="bar-track"><div class="bar-fill bar-fill-mask" style="width:{mask_pct}%;"></div></div>
            <div class="bar-pct">{mask_pct}%</div>
        </div>
        <div class="bar-row">
            <div class="bar-label" style="color:#ff1e2d;">🚫 No Mask</div>
            <div class="bar-track"><div class="bar-fill bar-fill-nomask" style="width:{nomask_pct}%;"></div></div>
            <div class="bar-pct">{nomask_pct}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Detections by Type")
    chart_df = pd.DataFrame({"Detections": [mask, no_mask]}, index=["Mask", "No Mask"])
    st.bar_chart(chart_df, color="#ff1e2d", height=280)
    
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Detections by Type")
    chart_df = pd.DataFrame({"Detections": [mask, no_mask]}, index=["Mask", "No Mask"])
    st.line_chart(chart_df, color="#ff1e2d", height=280)
        
