# SST Face Mask Detection System — Streamlit Frontend

A multi-page Streamlit app, structured the same way as the movie recommendation
project: one file per "window", all connected through a shared sidebar and
shared session-state, dark theme with red accents.

## Folder structure

```
mask_detection/
├── app.py                     # Home window (entry point — run this)
├── requirements.txt
├── shared/
│   ├── data.py                 # session-state helpers + mock detection (shared by every page)
│   └── styles.py                # shared CSS theme + sidebar nav component
└── pages/                      # every other window — Streamlit auto-detects these
    ├── 0_Login.py               # Sign In / Sign Up window
    ├── 1_Profile.py              # Profile window
    ├── 2_History.py              # History window
    ├── 3_Saved.py                # Saved window
    ├── 4_Visualization.py        # Today's Mask vs No Mask stats window
    └── 5_Contact_Us.py           # Contact Us window
```

## How the windows are connected

- Streamlit's built-in multi-page mechanism turns every file inside `pages/`
  into its own URL/window automatically — no manual routing needed.
- `shared/styles.py` → `render_sidebar()` draws the **same sidebar**
  (Home, Profile, History, Saved) on every page.
- `shared/data.py` holds `st.session_state` (login status, detection history,
  saved results), so running a detection on Home instantly shows up on the
  History page, and starring a result there shows up on Saved.
- `st.page_link(...)` / `st.switch_page(...)` handle navigation between pages.

## Run it

```bash
cd mask_detection
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Connecting to the database (SQLite)

The app has a real SQLite-backed persistence layer in `shared/db.py`,
with graceful fallback: if the database can't be opened for some reason,
the app keeps working exactly as before (session-only, no persistence).

SQLite needs no server, no credentials, and no separate "create the
database" step — it's just a single file on disk, and Python has the
driver built in.

1. Install dependencies (already includes `sqlalchemy`; SQLite support
   itself ships with Python, no extra driver needed):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app as usual:
   ```bash
   streamlit run app.py
   ```
   On first load, `try_connect_db()` (called at the top of every page)
   connects to a local file called `mask_detection.db` (created
   automatically in the folder you run the app from) and auto-creates
   three tables: `users`, `detections`, and `saved`.

That's it — no `.streamlit/secrets.toml` file is required for the
database to work. `mask_detection.db` is created next to `app.py` the
first time you run the app; delete that file if you ever want to reset
all data.

Once connected:
- Sign Up writes a real row to `users` (password stored as a SHA-256 hash).
- Sign In checks the username/password against that table.
- Running a detection while signed in writes to `detections`.
- Starring/unstarring a result writes to `saved`.
- History, Saved, and Profile read straight from SQLite instead of only
  from `st.session_state`, so your data survives app restarts.
- Contact Us submissions write to a `messages` table.
- Visualization reads today's `detections` rows (grouped by result) straight
  from SQLite, combined across every signed-in user.

## New pages

### Visualization
Shows how many detections have been run **today**: total count, how many
came back "Mask", and how many came back "No Mask" — as big number cards,
a percentage bar, and a bar chart. It reads live totals from the
`detections` table (combined across every signed-in user) whenever the
database is connected, and adds in any guest detections from the current
browser session (which never reach SQLite, since only signed-in users are
persisted). If the database is unreachable, it falls back to showing only
this session's activity so the page never breaks.

### Contact Us
A simple contact form (name, email, subject, message). Submissions are
saved to a `messages` table in SQLite. If the database isn't connected,
the message is kept for the current session only instead of failing, and
a warning explains why.

### Database resilience
Every page (including the two new ones) calls `try_connect_db()` and
checks the returned `db_connected` flag before touching SQLite. If the
database can't be reached for any reason — missing file permissions, a
locked file, etc. — every page falls back to session-only behavior
instead of crashing, and shows a clear warning explaining what's
happening. This was verified by pointing `db.DB_PATH` at a non-existent
path and confirming every page still renders with zero exceptions.

## Where to plug in real logic later

- Replace `mock_detect()` in `shared/data.py` with a call to your real
  trained model (image in, mask/no-mask + confidence out).
- For production, swap the plain SHA-256 password hashing in
  `shared/db.py` for a salted algorithm like bcrypt or argon2 (e.g. via
  the `passlib` package).
- The Profile page already shows full name, email, and member-since date
  via `db.get_user(username)`, whenever those fields were filled in at
  sign up.
