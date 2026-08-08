"""
Shared visual theme (dark background, red accents) + sidebar navigation.
Imported by every page so the whole app looks and behaves consistently,
mirroring shared/styles.py in the movie recommendation project.
"""
import streamlit as st

from shared.data import NAV_ITEMS, logout

PRIMARY_RED = "#ff1e2d"

CSS = f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}

    /* Hide Streamlit's own auto-generated page list (built from filenames
       like "app", "Login", "Profile"...) that renders at the top of the
       sidebar by default. We draw our own nav with st.page_link() below,
       so the built-in one is just visual clutter/duplication. */
    [data-testid="stSidebarNav"] {{display: none;}}

    .stApp {{
        background-color: #0e0e10;
        color: #e5e5e5;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #131316;
        border-right: 1px solid #2a2a2e;
    }}

    /* Brand title used at the top of every page + sidebar */
    .sst-brand {{
        color: {PRIMARY_RED};
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: 1px;
        border-bottom: 1px solid #2a2a2e;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }}
    .sst-brand span {{
        display: block;
        color: #9a9aa2;
        font-size: 0.85rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-weight: 500;
    }}

    /* Full-width red buttons everywhere in the app */
    div.stButton > button {{
        background-color: {PRIMARY_RED};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        width: 100%;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: background-color 0.15s ease-in-out;
    }}
    div.stButton > button:hover {{
        background-color: #d4151f;
        color: white;
    }}

    /* Sidebar page links */
    div[data-testid="stPageLink"] a {{
        color: #d5d5da !important;
        border-radius: 6px;
        padding: 6px 10px !important;
    }}
    div[data-testid="stPageLink"] a:hover {{
        background: rgba(255,30,45,0.15);
        color: {PRIMARY_RED} !important;
    }}

    /* Card used for each detection result / history row */
    .result-card {{
        background-color: #131316;
        border: 1px solid #2a2a2e;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }}
    .result-mask {{ color: #3ddc84; font-weight: 700; }}
    .result-nomask {{ color: {PRIMARY_RED}; font-weight: 700; }}

    /* Card that frames the Sign In / Sign Up form */
    .auth-card {{
        background-color: #131316;
        border: 1px solid #2a2a2e;
        border-radius: 10px;
        padding: 2.5rem;
        max-width: 420px;
        margin: 3rem auto 0 auto;
    }}

    input, textarea {{
        background-color: #1a1a1e !important;
        color: #e5e5e5 !important;
    }}

    /* Big number cards on the Visualization page */
    .metric-card {{
        background-color: #131316;
        border: 1px solid #2a2a2e;
        border-radius: 10px;
        padding: 1.4rem;
        text-align: center;
    }}
    .metric-card .metric-value {{
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.1;
    }}
    .metric-card .metric-label {{
        color: #9a9aa2;
        font-size: 0.85rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }}

    /* Horizontal Mask vs No Mask comparison bar */
    .bar-row {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.6rem;
    }}
    .bar-row .bar-label {{
        width: 110px;
        flex-shrink: 0;
        font-weight: 600;
    }}
    .bar-track {{
        flex-grow: 1;
        background-color: #1a1a1e;
        border-radius: 6px;
        height: 22px;
        overflow: hidden;
        border: 1px solid #2a2a2e;
    }}
    .bar-fill {{
        height: 100%;
        border-radius: 6px 0 0 6px;
        transition: width 0.3s ease-in-out;
    }}
    .bar-fill-mask {{ background-color: #3ddc84; }}
    .bar-fill-nomask {{ background-color: {PRIMARY_RED}; }}
    .bar-pct {{
        width: 48px;
        flex-shrink: 0;
        text-align: right;
        color: #d5d5da;
        font-weight: 600;
    }}
</style>
"""


def inject_css():
    """Injects the global dark/red theme. Call once near the top of every page."""
    st.markdown(CSS, unsafe_allow_html=True)


def render_sidebar(active_label: str):
    """
    Draws the shared sidebar (Home, Profile, History, Saved) on every page,
    so all windows are connected and one click away from each other.

    active_label: the label of the page currently being viewed (e.g. "Home"),
    used only to bold the matching sidebar entry.

    st.page_link(...) is Streamlit's built-in way to navigate between pages —
    no manual st.switch_page() calls needed for these links.
    """
    with st.sidebar:
        st.markdown(
            '<div class="sst-brand" style="font-size:1.6rem;">SST'
            '<span style="font-size:0.65rem;">Face Mask Detection</span></div>',
            unsafe_allow_html=True,
        )

        for item in NAV_ITEMS:
            label = f"**{item['icon']} {item['label']}**" if item["label"] == active_label else f"{item['icon']} {item['label']}"
            st.page_link(item["page"], label=label)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.get("logged_in"):
            st.caption(f"Signed in as **{st.session_state.username}**")
            if st.button("Sign Out", key="nav_signout", use_container_width=True):
                # TODO: clear any real session / auth token here
                logout()
                st.switch_page("pages/0_Login.py")
        else:
            st.page_link("pages/0_Login.py", label="🔑 Sign In")
