import streamlit as st
import pandas as pd
import numpy as np
import folium
import random
import statistics
import requests
import sqlite3
import hashlib
import hmac
import os
import json
import math
import base64
import time
import re
from datetime import date, datetime
from streamlit_folium import st_folium
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Browser geolocation that prompts automatically on page load
try:
    from streamlit_js_eval import get_geolocation
    HAS_GEO = True
except Exception:
    HAS_GEO = False

# Optional auto-refresh for live tracking
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

# =============================================================================
# 1. CONFIG + CONSTANTS
# =============================================================================
st.set_page_config(page_title="Cord Chemicals Field Sales", layout="wide")

# ---- Modern, professional theme (adapts to Light/Dark; fonts left untouched) ----
st.markdown("""
<style>
:root {
    --cord-navy: #0A2A66;
    --cord-navy2: #143C8C;
}

/* Buttons — neutral text inherits the theme so it stays visible in light & dark */
.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(10,42,102,0.35);
    padding: 0.5rem 1rem;
    font-weight: 600;
    transition: all .15s ease;
}
.stButton > button:hover {
    border-color: var(--cord-navy);
    box-shadow: 0 4px 14px rgba(10,42,102,0.25);
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0A2A66 0%, #143C8C 100%);
    border: none; color: #ffffff;
}

/* Metric cards — translucent so they work on any theme background */
[data-testid="stMetric"] {
    background: rgba(10,42,102,0.06);
    border: 1px solid rgba(10,42,102,0.25);
    border-radius: 16px;
    padding: 16px 18px;
}
[data-testid="stMetricValue"] { color: var(--cord-navy); }

/* Bordered containers as soft cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
}

/* Sidebar — navy divider accent */
[data-testid="stSidebar"] { border-right: 2px solid rgba(10,42,102,0.25); }

h1, h2, h3 { letter-spacing: .2px; }

/* Transparent top header/status bar */
[data-testid="stHeader"] { background: transparent !important; }
header[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
[data-baseweb="input"] input, [data-baseweb="select"] { border-radius: 10px; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 12px; overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


def show_splash():
    """One-time CORD AI intro: glowing background, brand fade, booting status."""
    st.markdown("""
    <style>
    .cordai-splash {
        position: fixed; inset: 0; z-index: 99999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: radial-gradient(1200px 600px at 50% 40%, #0c2f73 0%, #08214f 60%, #05132e 100%);
        animation: cordFade 3.4s ease forwards;
    }
    .cordai-glow {
        position: absolute; width: 520px; height: 520px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255,196,0,0.45) 0%, rgba(255,196,0,0.12) 45%, transparent 70%);
        filter: blur(20px); animation: cordPulse 2.2s ease-in-out infinite;
    }
    .cordai-brand {
        position: relative; color: #fff; font-size: 4.2rem; font-weight: 800;
        letter-spacing: 4px; opacity: 0; animation: cordBrand 3.4s ease forwards;
        text-shadow: 0 0 24px rgba(255,196,0,0.85), 0 0 60px rgba(255,196,0,0.5);
    }
    .cordai-brand span { color: #FFC400; }
    .cordai-status { position: relative; margin-top: 26px; height: 24px; color: #cfe0ff; opacity: .9; }
    .cordai-status div { position: absolute; left: 50%; transform: translateX(-50%);
        white-space: nowrap; opacity: 0; }
    .cordai-status .s1 { animation: cordLine 3.4s ease forwards 0.2s; }
    .cordai-status .s2 { animation: cordLine 3.4s ease forwards 1.0s; }
    .cordai-status .s3 { animation: cordLine 3.4s ease forwards 1.8s; }
    .cordai-status .s4 { animation: cordLine 3.4s ease forwards 2.5s; }
    .cordai-bar { position: relative; margin-top: 40px; width: 240px; height: 4px;
        border-radius: 4px; background: rgba(255,255,255,0.12); overflow: hidden; }
    .cordai-bar::after { content:""; position:absolute; inset:0; width:0;
        background: linear-gradient(90deg,#143C8C,#FFC400); animation: cordBar 3.0s ease forwards; }
    @keyframes cordPulse { 0%,100%{transform:scale(0.9);opacity:.7;} 50%{transform:scale(1.1);opacity:1;} }
    @keyframes cordBrand { 0%{opacity:0;transform:scale(0.92);} 25%{opacity:1;transform:scale(1);}
        85%{opacity:1;} 100%{opacity:0;} }
    @keyframes cordLine { 0%,8%{opacity:0;} 14%{opacity:1;} 24%{opacity:1;} 32%{opacity:0;} 100%{opacity:0;} }
    @keyframes cordBar { 0%{width:0;} 100%{width:100%;} }
    @keyframes cordFade { 0%{opacity:1;} 88%{opacity:1;} 100%{opacity:0;visibility:hidden;} }
    </style>
    <div class="cordai-splash">
        <div class="cordai-glow"></div>
        <div class="cordai-brand">CORD<span> AI</span></div>
        <div class="cordai-status">
            <div class="s1">Executing libraries…</div>
            <div class="s2">Booting engine…</div>
            <div class="s3">Calibrating routes &amp; GPS…</div>
            <div class="s4">Booting CORD AI…</div>
        </div>
        <div class="cordai-bar"></div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3.3)

DEPOT_NAME = "Cord Chemicals"
DEPOT_LAT, DEPOT_LNG = 14.5844537, 121.0475689
DEFAULT_MAPBOX_TOKEN = "pk.eyJ1Ijoia2V2aW5yZWkyIiwiYSI6ImNtcHl4ejY4ejA1ODYydHB2dDN3NXppcm0ifQ.Xpq-jmcdlyoVLCwDGulA4g"
DB_PATH = "delivery_app.db"
SECRET_KEY = "cord-chem-internal-secret-change-this"   # used to sign the stay-logged-in token
GEOFENCE_M = 100                                       # auto check-in radius (meters)

ACCOUNTS = pd.DataFrame({
    "Account Name": [
        "De Luxe Electrical & Hdwe. Supply",
        "Firestone Trading",
        "Fishermen Center",
        "Jr Multi Business Resources, Inc.",
        "Marswin Marketing Inc",
        "Ace Hardware (SM Megamall)",
        "Ace Hardware (Alabang)",
    ],
    "Address": [
        "162 N Carpio St, Grace Park East, Caloocan, 1403 Metro Manila",
        "415 San Nicolas St, San Nicolas, Manila, 1010 Metro Manila",
        "823 Tetuan St, Santa Cruz, Manila, 1003 Metro Manila",
        "111 Don Manuel Agregado Street, Quezon City, 1113 Metro Manila",
        "408 San Nicolas St, San Nicolas, Manila, Metro Manila",
        "202 EDSA cor. Dona Julia Vargas Ave, Mandaluyong City, 1550 Metro Manila",
        "2nd Flr, Festival Mall, Zapote Wing, Corporate Ave, Alabang, Muntinlupa, 1770 Metro Manila",
    ],
    "Territory": ["Caloocan", "Manila", "Manila", "Quezon City", "Manila", "Mandaluyong", "Muntinlupa"],
    "Latitude": [14.646187, 14.5999652, 14.6003507, 14.6315267, 14.6000217, 14.58631, 14.4189642],
    "Longitude": [120.983901, 120.9702905, 120.977661, 121.001982, 120.9702217, 121.057465, 121.040753],
})

SALESPERSONS = ["Alex Colorito", "Ritchel Junio", "Jomer Lumauig"]

# Seed users: (username, display name, role, password). Change passwords after first login.
SEED_USERS = [
    ("admin", "Brand Manager", "admin", "admin123"),
    ("alex", "Alex Colorito", "sales", "sales123"),
    ("ritchel", "Ritchel Junio", "sales", "sales123"),
    ("jomer", "Jomer Lumauig", "sales", "sales123"),
]

# =============================================================================
# 2. DATABASE LAYER  (SQLite now; swap DB_PATH/connection for Postgres later)
# =============================================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pw(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
    return salt, digest


def verify_pw(password, salt, digest):
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
    return hmac.compare_digest(check, digest)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, name TEXT, role TEXT, salt TEXT, pwd TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TEXT, driver TEXT, truck TEXT, status TEXT,
        stops_json TEXT, total_km REAL, time_str TEXT,
        created_by TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS live_locations (
        salesperson TEXT PRIMARY KEY, lat REAL, lng REAL, updated_at TEXT)""")
    # Ensure every seed account exists (creates missing ones like 'admin' on upgrade,
    # without overwriting accounts/passwords that already exist).
    for username, name, role, pw in SEED_USERS:
        exists = cur.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
        if not exists:
            salt, digest = hash_pw(pw)
            cur.execute("INSERT INTO users VALUES (?,?,?,?,?)", (username, name, role, salt, digest))
    # Migrate old role names if upgrading from an earlier version
    cur.execute("UPDATE users SET role='admin' WHERE role='dispatcher'")
    cur.execute("UPDATE users SET role='sales' WHERE role='driver'")
    conn.commit()
    conn.close()


def get_user(username):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_password(username, new_pw):
    salt, digest = hash_pw(new_pw)
    conn = get_conn()
    conn.execute("UPDATE users SET salt=?, pwd=? WHERE username=?", (salt, digest, username))
    conn.commit()
    conn.close()


def create_assignment(salesperson, stops, total_km, time_str, created_by):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO assignments
        (run_date, driver, truck, status, stops_json, total_km, time_str, created_by, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (date.today().isoformat(), salesperson, "", "Assigned",
         json.dumps(stops), total_km, time_str, created_by, datetime.now().isoformat(timespec="minutes")))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_assignments(salesperson=None):
    conn = get_conn()
    if salesperson:
        rows = conn.execute("SELECT * FROM assignments WHERE driver=? ORDER BY run_date DESC, id DESC",
                            (salesperson,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM assignments ORDER BY run_date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_assignment(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM assignments WHERE id=?", (aid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_assignment(aid, stops, status):
    conn = get_conn()
    conn.execute("UPDATE assignments SET stops_json=?, status=? WHERE id=?",
                 (json.dumps(stops), status, aid))
    conn.commit()
    conn.close()


def delete_assignment(aid):
    conn = get_conn()
    conn.execute("DELETE FROM assignments WHERE id=?", (aid,))
    conn.commit()
    conn.close()


def upsert_location(salesperson, lat, lng):
    conn = get_conn()
    conn.execute("""INSERT INTO live_locations (salesperson, lat, lng, updated_at)
        VALUES (?,?,?,?)
        ON CONFLICT(salesperson) DO UPDATE SET lat=excluded.lat, lng=excluded.lng,
        updated_at=excluded.updated_at""",
        (salesperson, lat, lng, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


def get_location(salesperson):
    conn = get_conn()
    row = conn.execute("SELECT * FROM live_locations WHERE salesperson=?", (salesperson,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()

# One-time CORD AI splash per browser session
if "splash_done" not in st.session_state:
    show_splash()
    st.session_state.splash_done = True
    st.rerun()

# =============================================================================
# 3. STAY-LOGGED-IN TOKEN + AUTH GATE
# =============================================================================
def make_token(username):
    sig = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{username}:{sig}".encode()).decode()


def verify_token(token):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, sig = raw.rsplit(":", 1)
        expect = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expect):
            return username
    except Exception:
        pass
    return None


if "auth" not in st.session_state:
    st.session_state.auth = None

# Restore session from the URL token so a page refresh does NOT log out.
if st.session_state.auth is None:
    tok = st.query_params.get("t")
    if tok:
        uname = verify_token(tok)
        if uname:
            rec = get_user(uname)
            if rec:
                st.session_state.auth = {"username": rec["username"], "name": rec["name"], "role": rec["role"]}

if st.session_state.auth is None:
    st.title("🔐 Cord Chemicals Field Sales — Sign in")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary")
    if ok:
        rec = get_user(u.strip().lower())
        if rec and verify_pw(p, rec["salt"], rec["pwd"]):
            st.session_state.auth = {"username": rec["username"], "name": rec["name"], "role": rec["role"]}
            st.query_params["t"] = make_token(rec["username"])
            st.rerun()
        else:
            st.error("Invalid username or password.")
    with st.expander("Demo accounts (change passwords after first login)"):
        st.markdown(
            "- **Admin (Brand Manager):** `admin` / `admin123`\n"
            "- **Sales people:** `alex`, `ritchel`, `jomer` — all `sales123`"
        )
    st.stop()

USER = st.session_state.auth

# =============================================================================
# 4. SHARED HELPER FUNCTIONS
# =============================================================================
def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def haversine_matrix(coords):
    rad = np.radians(np.asarray(coords, dtype=float))
    lat = rad[:, 0][:, None]
    lng = rad[:, 1][:, None]
    dlat = lat - lat.T
    dlng = lng - lng.T
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat) * np.cos(lat.T) * np.sin(dlng / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return 6371000.0 * c


@st.cache_data(show_spinner=False)
def get_mapbox_walk_matrices(coords_tuple, token):
    """Mapbox walking Matrix API: walking duration (s) + distance (m). Up to 25 coordinates."""
    coords = list(coords_tuple)
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/walking/{coord_str}"
    params = {"annotations": "duration,distance", "access_token": token}
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok":
                return data.get("durations"), data.get("distances")
    except Exception:
        pass
    return None, None


@st.cache_data(show_spinner=False)
def get_mapbox_walk_route(p_lat, p_lng, c_lat, c_lng, token):
    """Mapbox walking Directions geometry for drawing the footpath."""
    url = f"https://api.mapbox.com/directions/v5/mapbox/walking/{p_lng},{p_lat};{c_lng},{c_lat}"
    params = {"geometries": "geojson", "overview": "full", "access_token": token}
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("routes"):
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[c[1], c[0]] for c in coords]
    except Exception:
        pass
    return None


def fmt_duration(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    if h:
        return f"{h} h {m} min"
    if m:
        return f"{m} min"
    return "<1 min"


def route_totals(order, durations, distances):
    tot_t = tot_d = 0.0
    for a, b in zip(order[:-1], order[1:]):
        tot_t += durations[a][b]
        tot_d += distances[a][b]
    return tot_t, tot_d


# ---- AI itinerary comment ---------------------------------------------------
def analyze_route(route_df, itinerary, distances, durations, territory_map):
    stops = []
    for pos, node in enumerate(itinerary):
        if node == 0:
            continue
        prev_n, next_n = itinerary[pos - 1], itinerary[pos + 1]
        depot_km = distances[0][node] / 1000.0
        detour_km = max(0.0, (distances[prev_n][node] + distances[node][next_n]
                              - distances[prev_n][next_n]) / 1000.0)
        name = route_df.iloc[node]["Account Name"]
        stops.append({"name": name, "territory": territory_map.get(name, "—"),
                      "depot_km": depot_km, "detour_km": detour_km})
    depot_kms = [s["depot_km"] for s in stops]
    median_km = statistics.median(depot_kms) if depot_kms else 0.0
    far_threshold = max(8.0, 2.2 * median_km)
    detour_threshold = max(9.0, 2.5 * median_km)
    outliers = []
    for s in stops:
        reasons = []
        if s["depot_km"] > far_threshold:
            reasons.append(f"{s['depot_km']:.0f} km from base")
        if s["detour_km"] > detour_threshold:
            reasons.append(f"adds a {s['detour_km']:.0f} km swing to the loop")
        if reasons:
            s["reasons"] = reasons
            outliers.append(s)
    groups = {}
    for s in stops:
        groups.setdefault(s["territory"], []).append(s["name"])
    clusters = {t: names for t, names in groups.items() if len(names) >= 2}
    return {"stops": stops, "outliers": outliers, "clusters": clusters, "median_km": median_km}


def heuristic_comment(findings, num_stops, total_km, total_time_str):
    r = random.Random()
    parts = []
    parts.append(r.choice([
        f"Looking at this {num_stops}-stop itinerary ({total_km:.1f} km, about {total_time_str} on foot):",
        f"Quick read on the {num_stops} calls you've lined up — roughly {total_km:.1f} km and ~{total_time_str} of walking:",
        f"Here's how this {num_stops}-stop route shapes up — {total_km:.1f} km, around {total_time_str} on foot:",
    ]))
    outliers = findings["outliers"]
    if outliers:
        for o in outliers:
            reason = " and ".join(o["reasons"])
            same_area = findings["clusters"].get(o["territory"], [])
            line = r.choice([
                f"**{o['name']}** sits well off the cluster — it's {reason}. Unless it's urgent, consider moving it to a dedicated {o['territory']} day.",
                f"**{o['name']}** is the odd one out ({reason}). I'd reschedule it for a day the rep is already working {o['territory']}.",
                f"**{o['name']}** stretches the loop ({reason}). If the visit can wait, hold it for a {o['territory']}-focused trip.",
            ])
            if len(same_area) >= 2:
                line += f" You'll be covering {o['territory']} anyway with {len(same_area)} accounts there, so the wait shouldn't cost a field day."
            parts.append(line)
    else:
        parts.append(r.choice([
            "Every stop is reasonably clustered — no obvious outlier to drop. Efficient as-is.",
            "Nothing looks off-grid; the calls are close enough that the route is already tight.",
        ]))
    clusters = findings["clusters"]
    if clusters:
        biggest_t = max(clusters, key=lambda t: len(clusters[t]))
        parts.append(r.choice([
            f"You've got {len(clusters[biggest_t])} accounts in **{biggest_t}** — keep those back-to-back so the rep clears the area in one sweep.",
            f"**{biggest_t}** has {len(clusters[biggest_t])} stops bunched together; visiting them consecutively is the easy win.",
        ]))
    parts.append(r.choice([
        "Adjust the picking list and re-run to compare.",
        "Tweak the stops and recalculate to test a leaner version.",
        "Re-optimize after any change to see the new numbers.",
    ]))
    return "\n\n".join(parts)


def call_anthropic(api_key, model, prompt):
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": model, "max_tokens": 450, "temperature": 1.0,
            "messages": [{"role": "user", "content": prompt}]}
    resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def generate_ai_comment(findings, num_stops, total_km, total_time_str, ordered_names, api_key, model):
    if api_key:
        outlier_txt = "; ".join(f"{o['name']} ({', '.join(o['reasons'])})" for o in findings["outliers"]) or "none"
        cluster_txt = "; ".join(f"{t}: {len(n)} stops" for t, n in findings["clusters"].items()) or "none"
        flavor = random.choice(["concise", "practical", "candid", "encouraging", "no-nonsense"])
        prompt = (
            "You are a Metro Manila field-sales coordinator advising on one sales rep's walking itinerary. "
            f"Write a {flavor} advisory of 90-140 words (plain text, no headers, no bullet symbols). "
            "Flag any stop that is too far or off the grid for an efficient on-foot loop and recommend either "
            "removing it today or rescheduling it to a day with other visits in the same area; "
            "also note any area where stops cluster so they can be batched. Vary your wording naturally.\n\n"
            f"Route order (after base): {', '.join(ordered_names)}\n"
            f"Total: {total_km:.1f} km, ~{total_time_str} walking, {num_stops} stops.\n"
            f"Flagged far/off-grid stops: {outlier_txt}\n"
            f"Same-area clusters: {cluster_txt}\nBase: Cord Chemicals, Mandaluyong."
        )
        try:
            text = call_anthropic(api_key, model, prompt)
            if text:
                return text
        except Exception as e:
            return heuristic_comment(findings, num_stops, total_km, total_time_str) + \
                f"\n\n_(Live AI unavailable: {e} — showing the built-in analysis.)_"
    return heuristic_comment(findings, num_stops, total_km, total_time_str)


def optimize_open_route(points, objective, mapbox_token, solver_seconds):
    """Open path: start at points[0] (current location), visit all others, no forced return.
    points: list of (lat, lng). Returns ordered indices into `points` starting with 0."""
    n = len(points)
    if n <= 1:
        return {"order": list(range(n)), "durations": [[0]], "distances": [[0]], "source": "none"}

    durations = distances = None
    source = None
    if mapbox_token and n <= 25:
        durations, distances = get_mapbox_walk_matrices(tuple(points), mapbox_token)
        if durations is not None:
            source = "mapbox"
    if durations is None:
        hav = haversine_matrix(points)
        distances = hav.tolist()
        durations = (hav / 1.39).tolist()
        source = "fallback"

    dur = np.array(durations, dtype=float)
    dist = np.array(distances, dtype=float)
    base = dur if objective == "time" else dist
    base = np.nan_to_num(base, nan=1e9, posinf=1e9)

    # Add a dummy "end" node with zero cost to/from everything → open path (no forced return).
    size = n + 1
    matrix = np.zeros((size, size))
    matrix[:n, :n] = np.round(base).astype(int)
    matrix = matrix.astype(int).tolist()
    dummy = n

    manager = pywrapcp.RoutingIndexManager(size, 1, [0], [dummy])
    routing = pywrapcp.RoutingModel(manager)

    def cb(from_index, to_index):
        return matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    idx = routing.RegisterTransitCallback(cb)
    routing.SetArcCostEvaluatorOfAllVehicles(idx)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(int(solver_seconds))
    solution = routing.SolveWithParameters(params)
    if not solution:
        return None

    order = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != dummy:
            order.append(node)
        index = solution.Value(routing.NextVar(index))
    return {"order": order, "durations": durations, "distances": distances, "source": source}


def optimize_walk_route(df, objective, mapbox_token, solver_seconds):
    coords = [tuple(x) for x in df[["Latitude", "Longitude"]].values.tolist()]
    durations = distances = None
    source = None
    if mapbox_token and len(coords) <= 25:
        durations, distances = get_mapbox_walk_matrices(tuple(coords), mapbox_token)
        if durations is not None:
            source = "mapbox"
    if durations is None:
        hav = haversine_matrix(coords)
        distances = hav.tolist()
        durations = (hav / 1.39).tolist()   # ~5 km/h walking fallback
        source = "fallback"

    dur = np.array(durations, dtype=float)
    dist = np.array(distances, dtype=float)
    cost = dur if objective == "time" else dist
    cost = np.nan_to_num(cost, nan=1e9, posinf=1e9)
    matrix = np.round(cost).astype(int).tolist()

    manager = pywrapcp.RoutingIndexManager(len(matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_index, to_index):
        return matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_idx = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(int(solver_seconds))
    solution = routing.SolveWithParameters(params)
    if not solution:
        return None
    order = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        order.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    order.append(manager.IndexToNode(index))
    return {"order": order, "durations": durations, "distances": distances, "source": source}


# ---- Shared route map + step tracker ----------------------------------------
def build_route_map(full_seq, current_idx, token, map_height, open_route=False, highlight_idx=None):
    """full_seq: list of {name,lat,lng}. For a closed route, index 0 and last are the base.
    For an open route, index 0 is the rep's current location and the last node is a real stop.
    highlight_idx: which stop to emphasize as the immediate next destination (defaults to current_idx)."""
    if highlight_idx is None:
        highlight_idx = current_idx
    center = full_seq[current_idx]
    if token:
        tiles_url = ("https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/256/"
                     f"{{z}}/{{x}}/{{y}}?access_token={token}")
        m = folium.Map(location=[center["lat"], center["lng"]], zoom_start=14,
                       tiles=tiles_url, attr="© Mapbox © OpenStreetMap")
    else:
        m = folium.Map(location=[center["lat"], center["lng"]], zoom_start=14)

    start = full_seq[0]
    all_pts = [[start["lat"], start["lng"]]]
    if open_route:
        folium.Marker([start["lat"], start["lng"]], popup=start["name"],
                      icon=folium.Icon(color="green", icon="user")).add_to(m)
        folium.Circle([start["lat"], start["lng"]], radius=GEOFENCE_M, color="#2E7D32",
                      fill=True, fill_opacity=0.08).add_to(m)
    else:
        folium.Marker([start["lat"], start["lng"]], popup=start["name"],
                      icon=folium.Icon(color="black", icon="home")).add_to(m)

    for i in range(1, current_idx + 1):
        a, b = full_seq[i - 1], full_seq[i]
        active = (i == highlight_idx)
        pts = None
        if token:
            pts = get_mapbox_walk_route(a["lat"], a["lng"], b["lat"], b["lng"], token)
        if not pts:
            pts = [[a["lat"], a["lng"]], [b["lat"], b["lng"]]]
        all_pts.extend(pts)
        folium.PolyLine(pts, color="#0A2A66" if active else "#7C93C9",
                        weight=6 if active else 4, opacity=0.9 if active else 0.55,
                        dash_array="1,8").add_to(m)   # dotted = footpath
        last = (i == len(full_seq) - 1)
        if last and not open_route:
            continue  # closed route: last node is the depot, already pinned
        order_no = i  # stop's position in the sequence
        if active:
            folium.Marker([b["lat"], b["lng"]],
                          popup=f"GO HERE NEXT (stop {order_no}):<br>{b['name']}",
                          tooltip=f"➡️ {order_no}. {b['name']}",
                          icon=folium.Icon(color="red", icon="flag")).add_to(m)
        else:
            folium.Marker([b["lat"], b["lng"]],
                          popup=f"Stop {order_no}:<br>{b['name']}",
                          tooltip=f"{order_no}. {b['name']}",
                          icon=folium.Icon(color="blue", icon="ok")).add_to(m)

    # Auto-zoom so the whole visible path fits the screen (works on any phone size).
    if len(all_pts) >= 2:
        lats = [p[0] for p in all_pts]
        lngs = [p[1] for p in all_pts]
        m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]], padding=(40, 40))
    return m


def render_step_tracker(full_seq, step_key, token, map_height, remarks_map=None, arrived_map=None, open_route=False):
    remarks_map = remarks_map or {}
    arrived_map = arrived_map or {}
    last_pos = len(full_seq) - 1
    num_stops = last_pos if open_route else last_pos - 1

    if step_key not in st.session_state:
        st.session_state[step_key] = 1

    c_prev, c_text, c_next = st.columns([1, 4, 1])
    with c_prev:
        if st.button("⬅️ Previous", disabled=(st.session_state[step_key] <= 1),
                     use_container_width=True, key=f"{step_key}_prev"):
            st.session_state[step_key] -= 1
    with c_next:
        if st.button("Next ➡️", disabled=(st.session_state[step_key] >= last_pos),
                     use_container_width=True, key=f"{step_key}_next"):
            st.session_state[step_key] += 1

    cur = max(1, min(st.session_state[step_key], last_pos))
    st.session_state[step_key] = cur
    dest = full_seq[cur]

    with c_text:
        if (not open_route) and cur == last_pos:
            st.markdown(f"<h3 style='text-align:center;color:#0A2A66;'>🏁 Back to Base: {dest['name']}</h3>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align:center;color:#0A2A66;'>Stop {cur} of {num_stops}: {dest['name']}</h3>",
                        unsafe_allow_html=True)
            rmk = remarks_map.get(dest["name"], "")
            if rmk:
                st.markdown(f"<p style='text-align:center;'><i>Remarks: {rmk}</i></p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 🗺️ Itinerary")
        st.markdown(f"🚩 **Start:** {full_seq[0]['name']}")
        for step in range(1, len(full_seq)):
            name = full_seq[step]["name"]
            stamp = arrived_map.get(name)
            if (not open_route) and step == last_pos:
                st.markdown(f"{'✅' if cur >= last_pos else '🏁'} **Back to Base:** {name}")
            elif stamp:
                st.markdown(f"✅ **Stop {step}:** ~~{name}~~ — *{stamp}*")
            elif step == cur:
                st.markdown(f"🎯 **Stop {step}: {name}**")
            else:
                st.markdown(f"⏳ **Stop {step}:** {name}")
    with col2:
        m = build_route_map(full_seq, cur, token, map_height, open_route=open_route)
        st_folium(m, width=None, height=map_height, use_container_width=True,
                  key=f"{step_key}_map_{cur}", returned_objects=[])
    st.caption("Purple dotted line = walking path. 🟢 Green marker = current GPS position.")


def depot_node():
    return {"name": DEPOT_NAME, "lat": DEPOT_LAT, "lng": DEPOT_LNG}

# =============================================================================
# 5. SIDEBAR (account)
# =============================================================================
with st.sidebar:
    role_label = "Admin (Brand Manager)" if USER["role"] in ("admin", "dispatcher") else "Sales Person"
    st.markdown(f"**Signed in:** {USER['name']}  \n*{role_label}*")
    if st.button("Log out", use_container_width=True):
        st.session_state.auth = None
        if "t" in st.query_params:
            del st.query_params["t"]
        st.rerun()
    with st.expander("Change my password"):
        np1 = st.text_input("New password", type="password", key="np1")
        np2 = st.text_input("Confirm", type="password", key="np2")
        if st.button("Update password"):
            if np1 and np1 == np2:
                set_password(USER["username"], np1)
                st.success("Password updated.")
            else:
                st.error("Passwords are empty or don't match.")
    st.divider()


# =============================================================================
# 6. ADMIN (BRAND MANAGER) DASHBOARD
# =============================================================================
def admin_page():
    if "admin_view" not in st.session_state:
        st.session_state.admin_view = None
    view = st.session_state.admin_view
    if view == "itinerary":
        admin_itinerary()
    elif view == "tracking":
        admin_tracking()
    elif view == "chat":
        admin_chat()
    else:
        admin_welcome()


def admin_welcome():
    st.title(f"👋 Welcome, {USER['name']}")
    st.markdown("#### What would you like to work on?")
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 🧭 Plan & Assign Itineraries")
            st.caption("Pick accounts, optimize the walking route, and assign it to a sales person.")
            if st.button("Open Itinerary Planner", type="primary", use_container_width=True, key="go_itin"):
                st.session_state.admin_view = "itinerary"
                st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("### 📡 Live Tracking")
            st.caption("See where a sales person is right now and their progress through the day.")
            if st.button("Open Live Tracking", type="primary", use_container_width=True, key="go_track"):
                st.session_state.admin_view = "tracking"
                st.rerun()
    with c3:
        with st.container(border=True):
            st.markdown("### 🤖 CORD AI Assistant")
            st.caption("Just tell it what to do, e.g. “Give 2 Manila to Alex.” It plans from the rep's location.")
            if st.button("Open CORD AI", type="primary", use_container_width=True, key="go_chat"):
                st.session_state.admin_view = "chat"
                st.rerun()


def admin_itinerary():
    if st.button("⬅️ Back to menu", key="back_itin"):
        st.session_state.admin_view = None
        st.rerun()
    st.title("🧭 Plan & Assign Field Itineraries")

    with st.sidebar:
        st.header("⚙️ Itinerary Setup")
        salesperson = st.selectbox("Sales Person", options=SALESPERSONS)

        st.subheader("📍 Picking Locations")
        selected_names = st.multiselect("Select accounts to visit",
                                        options=ACCOUNTS["Account Name"].tolist())

        st.divider()
        st.subheader("🚶 Optimization (walking)")
        objective_label = st.radio("Optimize for", ["Fastest time (recommended)", "Shortest distance"])
        objective = "time" if objective_label.startswith("Fastest") else "distance"
        solver_seconds = st.slider("Solver effort (seconds)", 1, 15, 3)

        st.subheader("🗺️ Map")
        map_height = st.slider("Map height (px)", 400, 800, 520, step=20)

        st.subheader("🤖 AI Assistant")
        ai_api_key = st.text_input("Anthropic API key (optional)", type="password")
        with st.expander("Advanced"):
            mapbox_token = st.text_input("Mapbox token", value=DEFAULT_MAPBOX_TOKEN, type="password")
            ai_model = st.text_input("AI model", value="claude-sonnet-4-6")

    if "remarks" not in st.session_state:
        st.session_state.remarks = {}

    st.subheader("📋 Visit Manifest")
    st.caption(f"Sales Person: **{salesperson}**  |  Base: **{DEPOT_NAME}**")
    picked = ACCOUNTS[ACCOUNTS["Account Name"].isin(selected_names)].reset_index(drop=True)

    if picked.empty:
        st.info("👈 Use **Picking Locations** in the sidebar to add accounts.")
    else:
        disp = picked[["Account Name", "Address", "Territory"]].copy()
        disp.insert(0, "No", range(1, len(disp) + 1))
        disp["Remarks"] = [st.session_state.remarks.get(n, "") for n in disp["Account Name"]]
        edited = st.data_editor(disp, hide_index=True, num_rows="fixed", use_container_width=True,
                                disabled=["No", "Account Name", "Address", "Territory"],
                                column_config={"No": st.column_config.NumberColumn("No #", width="small"),
                                               "Remarks": st.column_config.TextColumn("Remarks")},
                                key="manifest_table")
        for _, row in edited.iterrows():
            st.session_state.remarks[row["Account Name"]] = row["Remarks"]

    if st.button("⚡ Calculate Optimal Walking Route", type="primary", disabled=picked.empty):
        base_row = pd.DataFrame([{"Account Name": DEPOT_NAME, "Latitude": DEPOT_LAT, "Longitude": DEPOT_LNG}])
        stops = picked[["Account Name", "Latitude", "Longitude"]]
        route_df = pd.concat([base_row, stops]).reset_index(drop=True)
        with st.spinner("Fetching walking times and optimizing..."):
            result = optimize_walk_route(route_df, objective, mapbox_token, solver_seconds)
        if result:
            order = result["order"]
            ordered = [{"name": route_df.iloc[n]["Account Name"],
                        "lat": float(route_df.iloc[n]["Latitude"]),
                        "lng": float(route_df.iloc[n]["Longitude"])} for n in order[1:-1]]
            t_time, t_dist = route_totals(order, result["durations"], result["distances"])
            terr = dict(zip(ACCOUNTS["Account Name"], ACCOUNTS["Territory"]))
            findings = analyze_route(route_df, order, result["distances"], result["durations"], terr)
            st.session_state.disp_route = {
                "ordered": ordered, "salesperson": salesperson,
                "total_km": t_dist / 1000.0, "time_str": fmt_duration(t_time),
                "source": result["source"],
            }
            st.session_state.disp_step = 1
            st.session_state.disp_ai = generate_ai_comment(
                findings, len(ordered), t_dist / 1000.0, fmt_duration(t_time),
                [s["name"] for s in ordered], ai_api_key, ai_model)
            if result["source"] == "mapbox":
                st.success("✅ Walking route calculated via 🚶 **Mapbox**.")
            else:
                st.warning("⚠️ Couldn't reach Mapbox — used straight-line **offline estimates**.")
        else:
            st.error("No solution found.")

    route = st.session_state.get("disp_route")
    if route:
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Stops", len(route["ordered"]))
        m2.metric("Walking distance", f"{route['total_km']:.1f} km")
        m3.metric("Est. walking time", route["time_str"])
        src = "🚶 Mapbox walking" if route["source"] == "mapbox" else "⚠️ offline estimate"
        st.caption(f"Routing source used: {src}")

        if st.session_state.get("disp_ai"):
            with st.container(border=True):
                st.markdown("#### 🤖 AI Itinerary Comment")
                st.markdown(st.session_state.disp_ai)

        full_seq = [depot_node()] + route["ordered"] + [depot_node()]
        render_step_tracker(full_seq, "disp_step", DEFAULT_MAPBOX_TOKEN, map_height,
                            st.session_state.get("remarks", {}))

        st.divider()
        if st.button(f"📌 Assign this itinerary to {route['salesperson']}", type="primary"):
            stops_payload = [{"name": s["name"], "lat": s["lat"], "lng": s["lng"],
                              "remarks": st.session_state.get("remarks", {}).get(s["name"], ""),
                              "visited": False, "arrived_at": None,
                              "departed_at": None, "travel_secs": None} for s in route["ordered"]]
            aid = create_assignment(route["salesperson"], stops_payload,
                                    route["total_km"], route["time_str"], USER["name"])
            st.success(f"Assigned to {route['salesperson']} (itinerary #{aid}). It now shows on their account.")

    st.divider()
    st.subheader("📑 All Itineraries & GPS Check-ins")
    rows = list_assignments()
    if not rows:
        st.caption("No itineraries yet.")
    for a in rows:
        stops = json.loads(a["stops_json"])
        done = sum(1 for s in stops if s.get("visited"))
        with st.expander(f"#{a['id']} · {a['run_date']} · {a['driver']} · {a['status']} · {done}/{len(stops)} visited"):
            st.caption(f"{a['total_km']:.1f} km · ~{a['time_str']} walking · assigned by {a['created_by']}")
            for i, s in enumerate(stops, 1):
                if s.get("arrived_at"):
                    took = f" · took {fmt_duration(s['travel_secs'])}" if s.get("travel_secs") else ""
                    st.markdown(f"✅ **{i}. {s['name']}** — arrived **{s['arrived_at']}**{took}")
                else:
                    st.markdown(f"⏳ **{i}. {s['name']}** — not yet visited")
            if st.button("Delete", key=f"del_{a['id']}"):
                delete_assignment(a["id"])
                st.rerun()


def admin_tracking():
    if st.button("⬅️ Back to menu", key="back_track"):
        st.session_state.admin_view = None
        st.rerun()

    with st.sidebar:
        st.header("📡 Live Tracking")
        track = st.selectbox("Sales person", options=SALESPERSONS, key="track_sel")
        track_auto = False
        if HAS_AUTOREFRESH:
            track_auto = st.checkbox("Auto-refresh every 15s", value=True, key="track_auto")
        map_height = st.slider("Map height (px)", 400, 800, 560, step=20)

    st.title(f"📡 Live Tracking — {track}")
    if track_auto and HAS_AUTOREFRESH:
        st_autorefresh(interval=15000, key="track_refresh")
    elif not HAS_AUTOREFRESH:
        if st.button("🔄 Refresh now", key="track_refresh_btn"):
            st.rerun()

    locrow = get_location(track)
    if not locrow:
        st.info(f"No location reported yet from {track}. They appear here once they open their itinerary and allow GPS.")
        return

    try:
        updated = datetime.fromisoformat(locrow["updated_at"])
        mins = (datetime.now() - updated).total_seconds() / 60.0
        ago = "just now" if mins < 1 else (f"{mins:.0f} min ago" if mins < 60 else f"{mins / 60:.1f} h ago")
    except Exception:
        ago = locrow["updated_at"]
    st.caption(f"📍 {track} — last seen **{ago}** ({locrow['lat']:.5f}, {locrow['lng']:.5f})")

    active = [x for x in list_assignments(track) if x["status"] != "Completed"]
    seq = [{"name": f"📍 {track}", "lat": locrow["lat"], "lng": locrow["lng"]}]
    if active:
        astops = json.loads(active[0]["stops_json"])
        remaining = [s for s in astops if not s.get("visited")]
        for s in remaining:
            seq.append({"name": s["name"], "lat": s["lat"], "lng": s["lng"]})
        done = sum(1 for s in astops if s.get("visited"))
        st.caption(f"Itinerary #{active[0]['id']}: {done}/{len(astops)} visited")

        # Per-stop arrival times + travel durations, plus a live en-route timer
        st.markdown("##### ⏱️ Progress")
        target = next((s for s in astops if not s.get("visited")), None)
        for i, s in enumerate(astops, 1):
            if s.get("arrived_at"):
                took = f" · took **{fmt_duration(s['travel_secs'])}**" if s.get("travel_secs") else ""
                st.markdown(f"✅ **{i}. {s['name']}** — arrived **{s['arrived_at']}**{took}")
            elif s is target and s.get("departed_at"):
                try:
                    elapsed = (datetime.now() - datetime.fromisoformat(s["departed_at"])).total_seconds()
                    st.markdown(f"🚶 **{i}. {s['name']}** — en route, **{fmt_duration(elapsed)}** so far")
                except Exception:
                    st.markdown(f"🚶 **{i}. {s['name']}** — en route")
            else:
                st.markdown(f"⏳ **{i}. {s['name']}** — pending")
    tmap = build_route_map(seq, len(seq) - 1, DEFAULT_MAPBOX_TOKEN, map_height,
                           open_route=True, highlight_idx=1)
    st_folium(tmap, width=None, height=map_height, use_container_width=True,
              key=f"track_map_{track}_{locrow['updated_at']}", returned_objects=[])


# =============================================================================
# 7. CORD AI CHAT (natural-language itinerary assistant)
# =============================================================================
def _parse_count(text):
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    m = re.search(r"\b(\d+)\b", text)
    if m:
        return int(m.group(1))
    for w, n in words.items():
        if re.search(rf"\b{w}\b", text.lower()):
            return n
    return None


def _find_person(text):
    for name in SALESPERSONS:
        if name.split()[0].lower() in text.lower() or name.lower() in text.lower():
            return name
    return None


def _find_territory(text):
    territories = list(dict.fromkeys(ACCOUNTS["Territory"].tolist()))
    return next((t for t in territories if t.lower() in text.lower()), None)


def _is_assign(t):
    return any(k in t for k in ["give", "assign", "send", "route", "add", "plan", "dispatch"])


def _help_text():
    return ("Here's what I can do:\n"
            "- **Assign work:** “Give 2 Manila to Alex”, “Assign 3 Quezon City to Ritchel”, “Send Jomer 1 Caloocan”\n"
            "- **List territories:** “List all territories”\n"
            "- **List accounts:** “Show all accounts” or “List Manila accounts”\n"
            "- **Locate a rep:** “Where is Alex?”\n"
            "- **Check progress:** “Status of Ritchel” or “Show all itineraries status”")


def _territory_list_text():
    counts = ACCOUNTS["Territory"].value_counts()
    lines = [f"There are **{len(counts)}** territories, with **{len(ACCOUNTS)}** accounts in total:"]
    for terr, c in counts.items():
        lines.append(f"- **{terr}** — {c} account(s)")
    return "\n".join(lines)


def _account_list_text(terr=None):
    df = ACCOUNTS if not terr else ACCOUNTS[ACCOUNTS["Territory"].str.lower() == terr.lower()]
    if df.empty:
        return f"No accounts found in **{terr}**."
    title = (f"All **{len(df)}** accounts" if not terr else f"**{len(df)}** account(s) in **{terr}**") + ":"
    lines = [title]
    for terr_name, grp in df.groupby("Territory"):
        names = ", ".join(grp["Account Name"].tolist())
        lines.append(f"- **{terr_name}:** {names}")
    return "\n".join(lines)


def _rep_status_text(person):
    loc = get_location(person)
    parts = []
    if loc:
        try:
            updated = datetime.fromisoformat(loc["updated_at"])
            mins = (datetime.now() - updated).total_seconds() / 60.0
            ago = "just now" if mins < 1 else (f"{mins:.0f} min ago" if mins < 60 else f"{mins / 60:.1f} h ago")
        except Exception:
            ago = loc["updated_at"]
        parts.append(f"📍 **{person}** was last seen **{ago}** at {loc['lat']:.4f}, {loc['lng']:.4f}.")
    else:
        parts.append(f"I don't have a live location for **{person}** yet — they need to open their app and allow GPS.")
    active = [a for a in list_assignments(person) if a["status"] != "Completed"]
    if active:
        astops = json.loads(active[0]["stops_json"])
        done = sum(1 for s in astops if s.get("visited"))
        nxt = next((s["name"] for s in astops if not s.get("visited")), "—")
        parts.append(f"Itinerary #{active[0]['id']}: {done}/{len(astops)} visited · next stop: **{nxt}**.")
    else:
        parts.append("No active itinerary right now.")
    return "\n".join(parts)


def _status_text(person=None):
    people = [person] if person else SALESPERSONS
    lines = ["Here's the current status:"]
    for p in people:
        active = [a for a in list_assignments(p) if a["status"] != "Completed"]
        if active:
            astops = json.loads(active[0]["stops_json"])
            done = sum(1 for s in astops if s.get("visited"))
            lines.append(f"- **{p}** — itinerary #{active[0]['id']}: {done}/{len(astops)} visited")
        else:
            lines.append(f"- **{p}** — no active itinerary")
    return "\n".join(lines)


def _propose_assignment(text, person, terr, n):
    """Existing behavior: plan the nearest N accounts in a territory from the rep's live location."""
    territories = list(dict.fromkeys(ACCOUNTS["Territory"].tolist()))
    if not person:
        return ("Which sales person? For example: *“Give 2 Manila to Alex”*. "
                f"Options: {', '.join(SALESPERSONS)}.", None)
    if not terr:
        return (f"Which territory should I use for {person.split()[0]}? "
                f"Options: {', '.join(territories)}.", None)
    n = n or 1

    # Step 1 — find the rep's live location first
    loc = get_location(person)
    if loc:
        origin = (loc["lat"], loc["lng"])
        origin_name = f"📍 {person} (current location)"
        origin_desc = f"**{person}** is at {loc['lat']:.4f}, {loc['lng']:.4f}"
    else:
        origin = (DEPOT_LAT, DEPOT_LNG)
        origin_name = f"{DEPOT_NAME} (base)"
        origin_desc = (f"I don't have a live GPS fix for **{person}** yet, so I planned from the base "
                       f"(**{DEPOT_NAME}**). Ask them to open their app and share location for a location-based plan")

    # Step 2 — candidates in that territory, nearest to the origin
    cands = ACCOUNTS[ACCOUNTS["Territory"].str.lower() == terr.lower()].copy()
    if cands.empty:
        return (f"There are no accounts in **{terr}**.", None)
    cands["dist"] = [haversine_m(origin[0], origin[1], r["Latitude"], r["Longitude"])
                     for _, r in cands.iterrows()]
    cands = cands.sort_values("dist")
    if len(cands) < n:
        note = f"Only {len(cands)} account(s) exist in {terr}, so I used all of them. "
        n = len(cands)
    else:
        note = ""
    chosen = cands.head(n)

    # Step 3 — optimize the walking order from the rep's location
    pts = [origin] + [(r["Latitude"], r["Longitude"]) for _, r in chosen.iterrows()]
    res = optimize_open_route(pts, "time", DEFAULT_MAPBOX_TOKEN, 3)
    order = res["order"] if res else list(range(len(pts)))
    ordered = []
    for ip in order:
        if ip == 0:
            continue
        r = chosen.iloc[ip - 1]
        ordered.append({"name": r["Account Name"], "lat": float(r["Latitude"]),
                        "lng": float(r["Longitude"]), "address": r["Address"]})
    durs, dists = res["durations"], res["distances"]
    tot_t = sum(durs[x][y] for x, y in zip(order[:-1], order[1:]))
    tot_d = sum(dists[x][y] for x, y in zip(order[:-1], order[1:]))

    lines = [f"{origin_desc}.", f"\nNearest **{n}** {terr} account(s):"]
    for _, r in chosen.iterrows():
        lines.append(f"- **{r['Account Name']}** — {r['dist'] / 1000:.1f} km away")
    lines.append(f"\nOptimized walking route: **{tot_d / 1000:.1f} km · ~{fmt_duration(tot_t)}**.")
    lines.append(f"{note}Review the map below and assign it to {person.split()[0]} if it looks good.")

    proposal = {"salesperson": person, "origin": origin, "origin_name": origin_name,
                "ordered": ordered, "total_km": tot_d / 1000.0, "time_str": fmt_duration(tot_t)}
    return ("\n".join(lines), proposal)


def process_command(text):
    """Route a chat message to a query answer or an assignment proposal.
    Returns (reply_text, proposal_or_None)."""
    t = text.lower()
    person = _find_person(text)
    terr = _find_territory(text)
    n = _parse_count(text)

    # --- Informational queries (no sales person being assigned) ---
    if "help" in t or "what can you" in t:
        return (_help_text(), None)

    if person and any(k in t for k in ["where", "locate", "location", "find "]):
        return (_rep_status_text(person), None)

    if any(k in t for k in ["status", "progress", "how is", "how's", "how are"]) and not _is_assign(t):
        return (_status_text(person), None)

    # List territories — only when no rep is named (so 'give 2 Manila territory to Alex' still assigns)
    if "territor" in t and person is None and \
            any(k in t for k in ["list", "all", "show", "what", "which", "how many", "available", "give"]):
        return (_territory_list_text(), None)

    # List accounts — only when no rep is named and not an assignment
    if "account" in t and person is None and not _is_assign(t):
        return (_account_list_text(terr), None)

    # --- Assignment intent ---
    if person or (_is_assign(t) and terr):
        return _propose_assignment(text, person, terr, n)

    # Plain rep name → show their status
    if person:
        return (_rep_status_text(person), None)

    return ("I didn't catch that. Type **help** to see what I can do, or try "
            "*“Give 2 Manila to Alex”* or *“List all territories”*.", None)


def admin_chat():
    if st.button("⬅️ Back to menu", key="back_chat"):
        st.session_state.admin_view = None
        st.rerun()
    st.title("🤖 CORD AI Assistant")
    st.caption('Try: “Give 2 Manila to Alex”, “Assign 3 Quezon City to Ritchel”, '
               '“Send Jomer 1 Caloocan”.')

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    prompt = st.chat_input("Type a command…")
    if prompt:
        st.session_state.chat_history.append(("user", prompt))
        reply, proposal = process_command(prompt)
        st.session_state.chat_history.append(("assistant", reply))
        st.session_state.chat_proposal = proposal
        st.rerun()

    proposal = st.session_state.get("chat_proposal")
    if proposal:
        st.divider()
        st.subheader(f"📝 Proposed itinerary for {proposal['salesperson']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Stops", len(proposal["ordered"]))
        m2.metric("Walking distance", f"{proposal['total_km']:.1f} km")
        m3.metric("Est. walking time", proposal["time_str"])

        full_seq = [{"name": proposal["origin_name"], "lat": proposal["origin"][0],
                     "lng": proposal["origin"][1]}]
        for s in proposal["ordered"]:
            full_seq.append({"name": s["name"], "lat": s["lat"], "lng": s["lng"]})
        cmap = build_route_map(full_seq, len(full_seq) - 1, DEFAULT_MAPBOX_TOKEN, 460,
                               open_route=True, highlight_idx=1)
        st_folium(cmap, width=None, height=460, use_container_width=True,
                  key="chat_map", returned_objects=[])

        c1, c2 = st.columns(2)
        if c1.button(f"✅ Assign to {proposal['salesperson']}", type="primary", use_container_width=True):
            stops_payload = [{"name": s["name"], "lat": s["lat"], "lng": s["lng"],
                              "remarks": "", "visited": False, "arrived_at": None,
                              "departed_at": None, "travel_secs": None} for s in proposal["ordered"]]
            aid = create_assignment(proposal["salesperson"], stops_payload,
                                    proposal["total_km"], proposal["time_str"], USER["name"])
            st.session_state.chat_history.append(
                ("assistant", f"✅ Assigned to **{proposal['salesperson']}** (itinerary #{aid})."))
            st.session_state.chat_proposal = None
            st.rerun()
        if c2.button("❌ Discard", use_container_width=True):
            st.session_state.chat_proposal = None
            st.rerun()


# =============================================================================
# 8. SALES PERSON DASHBOARD
# =============================================================================
def sales_page():
    st.title(f"🚶 {USER['name']} — My Itinerary")
    mine = list_assignments(salesperson=USER["name"])
    if not mine:
        st.info("No itinerary assigned to you yet. Your brand manager will assign one.")
        return

    labels = {f"#{a['id']} · {a['run_date']} · {a['status']}": a["id"] for a in mine}
    choice = st.selectbox("Choose an itinerary", options=list(labels.keys()))
    aid = labels[choice]

    if st.session_state.get("drv_current_aid") != aid:
        st.session_state.drv_current_aid = aid
        st.session_state.drv_step = 1

    a = get_assignment(aid)
    stops = json.loads(a["stops_json"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Stops", len(stops))
    m2.metric("Walking distance", f"{a['total_km']:.1f} km")
    m3.metric("Est. walking time", a["time_str"])
    st.caption(f"Status: **{a['status']}**  ·  Base: **{DEPOT_NAME}**")

    # ---- GPS check-in (auto-prompts on page load) ---------------------------
    st.subheader("📍 GPS Check-in")
    my_loc = None
    if HAS_GEO:
        st.caption("Your browser will ask to share your location when this page opens — tap **Allow**. "
                   f"Arrivals within {GEOFENCE_M} m of a stop are then recorded automatically.")
        loc = get_geolocation()  # fires the permission prompt automatically, no button
        if loc and isinstance(loc, dict) and loc.get("coords"):
            my_lat = float(loc["coords"]["latitude"])
            my_lng = float(loc["coords"]["longitude"])
            acc = loc["coords"].get("accuracy")
            my_loc = (my_lat, my_lng)
            prev = get_location(USER["name"])
            moved = haversine_m(prev["lat"], prev["lng"], my_lat, my_lng) if prev else 0.0
            upsert_location(USER["name"], my_lat, my_lng)   # let admin track this rep
            st.info(f"📡 Location received: {my_lat:.5f}, {my_lng:.5f}"
                    + (f" (±{acc:.0f} m accuracy)" if acc else ""))
            now = datetime.now()
            changed = False

            # Start the clock for the current target once the rep has actually moved ≥50 m
            target = next((s for s in stops if not s.get("visited")), None)
            if target and moved >= 50 and not target.get("departed_at"):
                target["departed_at"] = now.isoformat(timespec="seconds")
                changed = True

            for s in stops:
                if not s.get("visited"):
                    d = haversine_m(my_lat, my_lng, s["lat"], s["lng"])
                    if d <= GEOFENCE_M:
                        s["visited"] = True
                        s["arrived_at"] = now.strftime("%Y-%m-%d %H:%M")
                        dep = s.get("departed_at")
                        if dep:
                            try:
                                s["travel_secs"] = (now - datetime.fromisoformat(dep)).total_seconds()
                            except Exception:
                                s["travel_secs"] = None
                        changed = True
                        took = f" · travel {fmt_duration(s['travel_secs'])}" if s.get("travel_secs") else ""
                        st.success(f"📍 Checked in at {s['name']} ({d:.0f} m away){took}.")
            if changed:
                status = "Completed" if all(s.get("visited") for s in stops) else "In progress"
                update_assignment(aid, stops, status)
                st.rerun()
            else:
                pending = [s for s in stops if not s.get("visited")]
                if pending:
                    nearest = min(pending, key=lambda s: haversine_m(my_lat, my_lng, s["lat"], s["lng"]))
                    nd = haversine_m(my_lat, my_lng, nearest["lat"], nearest["lng"])
                    st.caption(f"Nearest pending stop: **{nearest['name']}** — {nd:.0f} m away "
                               f"(auto check-in within {GEOFENCE_M} m).")
        elif loc and isinstance(loc, dict) and loc.get("error"):
            code = loc["error"].get("code")
            if code == 1:
                st.error("Location permission was denied. Enable location for this site in your "
                         "browser settings (lock/aA icon → Location → Allow), then reload.")
            else:
                st.warning(f"Couldn't get location: {loc['error'].get('message', 'unknown error')}.")
        else:
            st.caption("⌛ Waiting for your location — please allow the permission prompt if it appears.")
    else:
        st.warning("Location component not installed. Add `streamlit-js-eval` to requirements.txt "
                   "to enable automatic check-ins. You can still check in manually below.")

    # Manual fallback: one-tap check-in for the stop currently shown in the tracker,
    # so the workflow works even if a phone/browser blocks the GPS component.
    with st.expander("📌 Manual check-in (if GPS won't prompt)"):
        pending_names = [s["name"] for s in stops if not s.get("visited")]
        if pending_names:
            pick = st.selectbox("I'm currently at:", options=pending_names, key=f"manual_{aid}")
            if st.button("✅ Check in here now", key=f"manual_btn_{aid}"):
                for s in stops:
                    if s["name"] == pick:
                        s["visited"] = True
                        s["arrived_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                status = "Completed" if all(s.get("visited") for s in stops) else "In progress"
                update_assignment(aid, stops, status)
                st.success(f"Checked in at {pick}.")
                st.rerun()
        else:
            st.caption("All stops already checked in. 🎉")

    unvisited = [s for s in stops if not s.get("visited")]
    remarks_map = {s["name"]: s.get("remarks", "") for s in stops}
    arrived_map = {s["name"]: s.get("arrived_at") for s in stops if s.get("arrived_at")}

    st.divider()
    if not unvisited:
        st.success("🎉 All stops visited — itinerary complete!")
    elif my_loc:
        # Re-optimize the remaining stops starting from the rep's CURRENT location (open route).
        pts = [(my_loc[0], my_loc[1])] + [(s["lat"], s["lng"]) for s in unvisited]
        res = optimize_open_route(pts, "time", DEFAULT_MAPBOX_TOKEN, 3)
        if res and res["order"]:
            order = res["order"]
            seq = []
            for ip in order:
                if ip == 0:
                    seq.append({"name": "📍 You (current location)", "lat": my_loc[0], "lng": my_loc[1]})
                else:
                    s = unvisited[ip - 1]
                    seq.append({"name": s["name"], "lat": s["lat"], "lng": s["lng"]})
            durs, dists = res["durations"], res["distances"]
            tot_t = sum(durs[x][y] for x, y in zip(order[:-1], order[1:]))
            tot_d = sum(dists[x][y] for x, y in zip(order[:-1], order[1:]))
            st.subheader("🧭 Live Route (from your location)")
            st.caption(f"Re-routed from where you are now · {len(unvisited)} stops left · "
                       f"{tot_d / 1000:.1f} km · ~{fmt_duration(tot_t)} remaining")
            render_step_tracker(seq, "drv_step", DEFAULT_MAPBOX_TOKEN, 520,
                                remarks_map, arrived_map, open_route=True)
        else:
            st.warning("Couldn't compute a live route right now — showing the planned order.")
            full_seq = [depot_node()] + [{"name": s["name"], "lat": s["lat"], "lng": s["lng"]} for s in unvisited] + [depot_node()]
            render_step_tracker(full_seq, "drv_step", DEFAULT_MAPBOX_TOKEN, 520, remarks_map, arrived_map)
    else:
        st.caption("Allow location above to get a live route from your position. "
                   "Showing the planned order from base for now.")
        full_seq = [depot_node()] + [{"name": s["name"], "lat": s["lat"], "lng": s["lng"]} for s in unvisited] + [depot_node()]
        render_step_tracker(full_seq, "drv_step", DEFAULT_MAPBOX_TOKEN, 520, remarks_map, arrived_map)

    st.divider()
    st.subheader("✅ Visit Checklist")
    st.caption("GPS records arrivals automatically; you can also tick a stop here if needed.")
    new_flags = []
    for i, s in enumerate(stops):
        stamp = f"  —  arrived {s['arrived_at']}" if s.get("arrived_at") else ""
        rmk = f"  ·  _{s['remarks']}_" if s.get("remarks") else ""
        new_flags.append(st.checkbox(f"{i + 1}. {s['name']}{stamp}{rmk}",
                                     value=s.get("visited", False), key=f"chk_{aid}_{i}"))
    if st.button("💾 Save progress", type="primary"):
        for s, flag in zip(stops, new_flags):
            if flag and not s.get("visited"):
                s["arrived_at"] = s.get("arrived_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
            s["visited"] = flag
            if not flag:
                s["arrived_at"] = None
        status = "Completed" if all(s["visited"] for s in stops) else \
                 ("In progress" if any(s["visited"] for s in stops) else "Assigned")
        update_assignment(aid, stops, status)
        st.success(f"Saved. Status: {status}.")
        st.rerun()


# Route to the correct dashboard by role
if USER["role"] in ("admin", "dispatcher"):
    admin_page()
else:
    sales_page()
