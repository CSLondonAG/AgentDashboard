import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime, timedelta, time as dtime, date as date_type
from typing import List, Optional, Tuple


STATUS_CHAT_ONLY = "Available_Chat"
STATUS_EMAIL_ONLY = "Available_Email_and_Web"
STATUS_SHARED = "Available_All"
AVAILABLE_STATUSES = {STATUS_CHAT_ONLY, STATUS_EMAIL_ONLY, STATUS_SHARED}
CHAT_DEVNAME = "sfdc_liveagent"
EMAIL_DEVNAME = "casesChannel"
CHAT_CONCURRENCY_CAPACITY = 2

# IMPORTANT: st.set_page_config must be called as the very first Streamlit command
st.set_page_config(page_title="Agent Dashboard", layout="wide")

# --- Load the SVG Logo (wrapped in try so it doesn't crash if missing) ---
try:
    with open("goat_logo.svg", "r", encoding="utf-8") as f:
        svg_code = f.read()
except Exception:
    svg_code = ""

# Design system tokens + component styles
st.markdown("""
    <style>
    /* ── TOKENS ─────────────────────────────────────────── */
    :root {
        --color-bg:            #f8f9fa;
        --color-surface:       #ffffff;
        --color-border:        #e5e7eb;
        --color-text-primary:  #111827;
        --color-text-label:    #6b7280;
        --color-accent:        #2563eb;
        --color-success:       #16a34a;
        --color-warning:       #dc2626;
        --color-warning-bg:    #fef2f2;
        --color-warning-border:#fca5a5;
        --shadow-card:         0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --radius-card:         12px;
        --card-padding:        20px 24px;
        --card-gap:            24px;
    }

    /* ── PAGE ────────────────────────────────────────────── */
    .stApp {
        background-color: var(--color-bg);
    }

    /* ── HEADER ──────────────────────────────────────────── */
    .custom-main-header-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        margin-top: 0;
        padding-top: 1rem;
        margin-bottom: 0.25rem;
        padding-bottom: 0;
    }

    .custom-main-header-container h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--color-text-primary) !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        display: inline;
    }

    .header-logo-inline {
        width: 40px;
        height: auto;
        margin-left: 12px;
        vertical-align: middle;
    }

    /* ── TYPOGRAPHY ──────────────────────────────────────── */
    .main h2 {
        font-size: 0.75rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-bottom: 0 !important;
        line-height: 1.2 !important;
    }

    .main h3 {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: var(--color-text-label) !important;
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
    }

    .main h4 {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: var(--color-text-label) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    .subheader-smaller {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--color-text-label);
        margin-bottom: 1rem;
        letter-spacing: 0.01em;
    }

    /* ── DIVIDER ─────────────────────────────────────────── */
    .section-divider {
        border: none;
        border-top: 1px solid var(--color-border);
        margin: 2rem 0;
    }

    /* ── METRIC CARDS ────────────────────────────────────── */
    .metric-container {
        padding: var(--card-padding);
        border-radius: var(--radius-card);
        background-color: var(--color-surface);
        box-shadow: var(--shadow-card);
        border: 1px solid var(--color-border);
        margin-bottom: var(--card-gap);
        text-align: center;
    }

    .metric-title {
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--color-text-label);
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-text-primary);
        line-height: 1.1;
    }

    .metric-value-accent {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-accent);
        line-height: 1.1;
    }

    .metric-value-success {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-success);
        line-height: 1.1;
    }

    /* ── WARNING CARDS ───────────────────────────────────── */
    .metric-container-warning {
        padding: var(--card-padding);
        border-radius: var(--radius-card);
        background-color: var(--color-warning-bg);
        box-shadow: var(--shadow-card);
        border: 1px solid var(--color-warning-border);
        margin-bottom: var(--card-gap);
        text-align: center;
    }

    .metric-container-warning .metric-title {
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--color-text-label);
        margin-bottom: 8px;
    }

    .metric-container-warning .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-warning);
        line-height: 1.1;
    }

    /* ── LATENESS INCIDENT LIST ──────────────────────────── */
    .incident-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .incident-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 16px;
        border-radius: 8px;
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        margin-bottom: 8px;
    }

    .incident-date {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--color-text-primary);
    }

    .incident-badge {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--color-warning);
        background-color: var(--color-warning-bg);
        border: 1px solid var(--color-warning-border);
        padding: 3px 10px;
        border-radius: 999px;
        letter-spacing: 0.02em;
    }

    /* ── EMPTY STATES ────────────────────────────────────── */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 2rem;
        text-align: center;
    }

    .empty-state-label {
        margin-top: 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--color-text-label);
        letter-spacing: 0.02em;
    }

    /* ── SHIFT BOX (retained, cleaned up) ───────────────── */
    .shift-box {
        padding: var(--card-padding);
        border-radius: var(--radius-card);
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        font-size: 1.5em;
        font-weight: 700;
        color: var(--color-accent);
        text-align: center;
        box-shadow: var(--shadow-card);
    }

    </style>
""", unsafe_allow_html=True)


# -----------------------------
# Data loading helpers
# -----------------------------
def safe_read_csv(path, **kwargs):
    """Read a CSV and gracefully handle empty files."""
    try:
        return pd.read_csv(path, **kwargs)
    except EmptyDataError:
        return pd.DataFrame()


def load_data():
    # Items
    df_items = safe_read_csv("report_items.csv", dayfirst=True)
    if not df_items.empty:
        df_items["Start DT"] = pd.to_datetime(df_items["Start DT"], dayfirst=True, errors="coerce")
        df_items["End DT"] = pd.to_datetime(df_items["End DT"], dayfirst=True, errors="coerce")
        df_items["User: Full Name"] = df_items["User: Full Name"].astype(str).str.strip()
        df_items["Service Channel: Developer Name"] = df_items["Service Channel: Developer Name"].astype(str).str.strip()

    # Presence
    df_presence = safe_read_csv("report_presence.csv", dayfirst=True)
    if not df_presence.empty:
        df_presence["Start DT"] = pd.to_datetime(df_presence["Start DT"], dayfirst=True, errors="coerce")
        df_presence["End DT"] = pd.to_datetime(df_presence["End DT"], dayfirst=True, errors="coerce")
        df_presence["Created By: Full Name"] = df_presence["Created By: Full Name"].astype(str).str.strip()
        df_presence["Service Presence Status: Developer Name"] = df_presence["Service Presence Status: Developer Name"].astype(str).str.strip()

    # Shifts
    df_shifts = safe_read_csv("shifts.csv")
    if not df_shifts.empty:
        if "Column1" in df_shifts.columns and "Agent Name" not in df_shifts.columns:
            df_shifts.rename(columns={"Column1": "Agent Name"}, inplace=True)
        if "Agent Name" in df_shifts.columns:
            df_shifts["Agent Name"] = df_shifts["Agent Name"].astype(str).str.strip()

    # Chat transcripts — one row per conversation, with exact start/end times
    df_chat = safe_read_csv("chat_transcripts.csv")
    if df_chat.empty:
        # Try common alternative filenames in case it was uploaded differently
        for alt in ["chat_transcript.csv", "chat.csv", "transcripts.csv", "report1771339850121.csv"]:
            df_chat = safe_read_csv(alt)
            if not df_chat.empty:
                break
    if not df_chat.empty:
        # Brute-force clean every column name: remove BOM, strip whitespace,
        # then build a lookup that matches regardless of BOM or encoding quirks
        clean = {col: col.encode("utf-8").decode("utf-8-sig").strip() for col in df_chat.columns}
        df_chat.rename(columns=clean, inplace=True)

        # Now find the agent column — it may be "Owner: Full Name" or a BOM variant
        agent_col = next((c for c in df_chat.columns if "Full Name" in c), None)
        if agent_col and agent_col != "Agent Name":
            df_chat.rename(columns={agent_col: "Agent Name"}, inplace=True)

        # Normalise Case Number column
        case_col = next((c for c in df_chat.columns if "Case Number" in c), None)
        if case_col and case_col != "Case Number":
            df_chat.rename(columns={case_col: "Case Number"}, inplace=True)

        if "Agent Name" in df_chat.columns:
            df_chat["Agent Name"] = df_chat["Agent Name"].astype(str).str.strip()
        if "Start Time" in df_chat.columns:
            df_chat["Start DT"] = pd.to_datetime(df_chat["Start Time"], format="%d/%m/%Y, %H:%M", errors="coerce")
        if "End Time" in df_chat.columns:
            df_chat["End DT"] = pd.to_datetime(df_chat["End Time"], format="%d/%m/%Y, %H:%M", errors="coerce")
        if "Start DT" in df_chat.columns and "End DT" in df_chat.columns:
            df_chat["Duration (s)"] = (df_chat["End DT"] - df_chat["Start DT"]).dt.total_seconds()
            # Drop abandoned chats (zero/null duration — visitor left before agent responded)
            df_chat = df_chat[
                df_chat["Start DT"].notna() &
                df_chat["End DT"].notna() &
                (df_chat["Duration (s)"] > 0)
            ].copy()

    return df_items, df_presence, df_shifts, df_chat


df_items, df_presence, df_shifts, df_chat = load_data()

if df_presence.empty or df_items.empty or df_shifts.empty:
    st.error("One or more data files are empty or missing. Please check report_items.csv, report_presence.csv, and shifts.csv.")
    st.stop()


# -----------------------------
# Utility functions
# -----------------------------
def normalise_shift_value(value):
    """Return a clean shift/event string from the rota cell."""
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\n", " ").strip().split())


def get_shift_value(agent_shift_row, shift_col):
    if agent_shift_row.empty or shift_col not in df_shifts.columns:
        return ""
    return normalise_shift_value(agent_shift_row[shift_col].values[0])


def is_not_assigned_shift(shift_str):
    text = normalise_shift_value(shift_str).lower()
    return text in {"", "nan", "not assigned", "n/a", "na", "day off", "off"}


def is_sick_shift(shift_str):
    text = normalise_shift_value(shift_str).lower()
    return any(word in text for word in ["sick", "sickness", "illness", "ill"])


def is_manual_late_shift(shift_str):
    text = normalise_shift_value(shift_str).lower()
    return "late" in text


def parse_shift_range(shift_str, base_date):
    """Parse rota shifts like '7:00 AM - 4:00 PM', even if notes/newlines are present."""
    import re

    text = normalise_shift_value(shift_str)
    if not text:
        return None, None

    # Accept both hyphen and en dash separators, and ignore notes such as Sick/Late after the times.
    matches = re.findall(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM)?)\b", text, flags=re.IGNORECASE)
    if len(matches) < 2:
        return None, None

    parsed_times = []
    for part in matches[:2]:
        part = part.strip().upper().replace(" ", "")
        for fmt in ("%I:%M%p", "%H:%M"):
            try:
                parsed_times.append(datetime.strptime(part, fmt).time())
                break
            except ValueError:
                continue

    if len(parsed_times) < 2:
        return None, None

    start_dt = datetime.combine(base_date, parsed_times[0])
    end_dt = datetime.combine(base_date, parsed_times[1])
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def has_shift_time(shift_str, base_date):
    sched_start, sched_end = parse_shift_range(shift_str, base_date)
    return sched_start is not None and sched_end is not None


def classify_rota_day(shift_str, base_date):
    shift_str = normalise_shift_value(shift_str)
    if is_not_assigned_shift(shift_str):
        return "not_assigned"
    if is_sick_shift(shift_str):
        return "sick"
    if has_shift_time(shift_str, base_date):
        return "scheduled"
    if is_manual_late_shift(shift_str):
        return "manual_late"
    return "other_event"


def format_seconds_to_mm_ss(total_seconds):
    if total_seconds is None:
        return "–"
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


Interval = Tuple[pd.Timestamp, pd.Timestamp]


def merge_intervals(intervals) -> List[Interval]:
    """Merge overlapping or adjacent intervals and discard invalid rows."""
    norm = []
    for pair in intervals or []:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        start = pd.to_datetime(pair[0], errors="coerce")
        end = pd.to_datetime(pair[1], errors="coerce")
        if pd.notna(start) and pd.notna(end) and end > start:
            norm.append([start, end])
    if not norm:
        return []
    norm.sort(key=lambda interval: interval[0])
    merged = [norm[0]]
    for start, end in norm[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(interval) for interval in merged]


def clip_to_window(start, end, window_start, window_end) -> Optional[Interval]:
    if pd.isna(start) or pd.isna(end):
        return None
    clipped_start = max(pd.Timestamp(start), pd.Timestamp(window_start))
    clipped_end = min(pd.Timestamp(end), pd.Timestamp(window_end))
    return (clipped_start, clipped_end) if clipped_end > clipped_start else None


def sum_seconds(intervals) -> float:
    return float(sum((end - start).total_seconds() for start, end in intervals))


def intersect_seconds(left_intervals, right_intervals) -> float:
    """Return wall-clock seconds where two interval sets overlap."""
    left = merge_intervals(left_intervals)
    right = merge_intervals(right_intervals)
    left_index = right_index = 0
    total = 0.0
    while left_index < len(left) and right_index < len(right):
        start = max(left[left_index][0], right[right_index][0])
        end = min(left[left_index][1], right[right_index][1])
        if end > start:
            total += (end - start).total_seconds()
        if left[left_index][1] < right[right_index][1]:
            left_index += 1
        else:
            right_index += 1
    return float(total)


def concurrent_slot_seconds(work_intervals, available_intervals,
                            capacity: int = CHAT_CONCURRENCY_CAPACITY) -> float:
    """Return used chat slot-seconds, capped at the configured capacity."""
    if capacity <= 0:
        raise ValueError("capacity must be greater than zero")
    available = merge_intervals(available_intervals)
    events = []
    for pair in work_intervals or []:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        start = pd.to_datetime(pair[0], errors="coerce")
        end = pd.to_datetime(pair[1], errors="coerce")
        if pd.isna(start) or pd.isna(end) or end <= start:
            continue
        for available_start, available_end in available:
            overlap_start = max(start, available_start)
            overlap_end = min(end, available_end)
            if overlap_end > overlap_start:
                events.append((overlap_start, 1))
                events.append((overlap_end, -1))
    events.sort(key=lambda event: (event[0], event[1]))
    active = 0
    previous = None
    total = 0.0
    for timestamp, change in events:
        if previous is not None and timestamp > previous:
            total += (timestamp - previous).total_seconds() * min(active, capacity)
        active += change
        previous = timestamp
    return float(total)


def email_assignable_capacity(chat_intervals, email_intervals, shared_intervals):
    """Return shared email capacity, used capacity, and excess-demand seconds.

    During ``Available_All`` an agent is email-assignable only while no chat is
    active. Any active chat makes shared time unavailable for email.
    """
    shared = merge_intervals(shared_intervals)
    capacity_seconds = used_seconds = raw_email_seconds = 0.0

    for shared_start, shared_end in shared:
        events = {shared_start: [0, 0], shared_end: [0, 0]}
        for intervals, event_index in ((chat_intervals, 0), (email_intervals, 1)):
            for pair in intervals or []:
                if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                    continue
                start = pd.to_datetime(pair[0], errors="coerce")
                end = pd.to_datetime(pair[1], errors="coerce")
                if pd.isna(start) or pd.isna(end) or end <= start:
                    continue
                overlap_start = max(start, shared_start)
                overlap_end = min(end, shared_end)
                if overlap_end <= overlap_start:
                    continue
                events.setdefault(overlap_start, [0, 0])[event_index] += 1
                events.setdefault(overlap_end, [0, 0])[event_index] -= 1

        active_chat = active_email = 0
        previous = shared_start
        for timestamp in sorted(events):
            if timestamp > previous:
                elapsed = (timestamp - previous).total_seconds()
                email_assignable = active_chat == 0
                if email_assignable:
                    capacity_seconds += elapsed
                    if active_email > 0:
                        used_seconds += elapsed
                elif active_email > 0:
                    raw_email_seconds += elapsed
            chat_delta, email_delta = events[timestamp]
            active_chat += chat_delta
            active_email += email_delta
            previous = timestamp

    return float(capacity_seconds), float(used_seconds), float(raw_email_seconds)


# -----------------------------
# Sidebar controls
# -----------------------------
agents = sorted(df_presence["Created By: Full Name"].dropna().unique())

# --- REMOVE AGENTS WHO HAVE LEFT THE COMPANY ---
agents_to_remove = [
    "Atuweni Masangano",
    "Dorah Mwase",
    "Jonathan Mandala",
    "Lindah Sewero",
    "Shiellah Phuka",
]

agents = [a for a in agents if a not in agents_to_remove]

agent = st.sidebar.selectbox("Agent Name", agents)

# Build list of all dates we have presence data for
raw_dates = sorted(df_presence["Start DT"].dt.date.unique())
available_dates = [pd.to_datetime(d).date() for d in raw_dates]

min_date = min(available_dates)
max_date = max(available_dates)

# Date range selector (Option A – unified range)
date_range = st.sidebar.date_input(
    "Date range",
    value=(max_date - timedelta(days=6), max_date),  # default: last 7 days
    min_value=min_date,
    max_value=max_date,
)

# Robust handling whether user selects a single date or a range
if isinstance(date_range, (list, tuple)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date = end_date = max_date
else:
    start_date = end_date = date_range

if start_date > end_date:
    start_date, end_date = end_date, start_date

# -----------------------------
# Header (Agent + Date range)
# -----------------------------
st.markdown(f"""
    <div class="custom-main-header-container">
        <h1>Agent Dashboard for {agent}</h1>
        <div class="header-logo-inline">{svg_code}</div>
    </div>
""", unsafe_allow_html=True)

if start_date == end_date:
    date_label = start_date.strftime("%d %B %Y")
else:
    date_label = f"{start_date.strftime('%d %B %Y')} – {end_date.strftime('%d %B %Y')}"

st.markdown(
    f"""<div class='subheader-smaller'>Date range: {date_label}</div>""",
    unsafe_allow_html=True,
)
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# -----------------------------
# Filter data to agent + range
# -----------------------------
range_start_dt = datetime.combine(start_date, dtime(0, 0))
range_end_dt = datetime.combine(end_date, dtime(23, 59))
range_end_exclusive = datetime.combine(end_date + timedelta(days=1), dtime(0, 0))

df_presence_agent_range = df_presence[
    (df_presence["Created By: Full Name"] == agent)
    & (df_presence["End DT"] > range_start_dt)
    & (df_presence["Start DT"] < range_end_exclusive)
].copy()

# Items: filter by agent first, then by Start DT's DATE between start_date and end_date.
df_items_agent = df_items[
    (df_items["User: Full Name"] == agent)
    & (~df_items["Start DT"].isna())
    & (~df_items["End DT"].isna())
].copy()
df_items_agent["Start Date"] = df_items_agent["Start DT"].dt.date

df_items_agent_range = df_items_agent[
    (df_items_agent["Start Date"] >= start_date)
    & (df_items_agent["Start Date"] <= end_date)
].copy()

# Utilisation is based on interval overlap, not just the item's start date.
df_items_agent_overlap = df_items_agent[
    (df_items_agent["Start DT"] < range_end_exclusive)
    & (df_items_agent["End DT"] > range_start_dt)
].copy()

# List of days in the selected range
day_list = [
    start_date + timedelta(days=i)
    for i in range((end_date - start_date).days + 1)
]

# Check schedule in range
agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()
has_scheduled_shift = False
has_sick_event = False
for d in day_list:
    shift_col = d.strftime("%d/%m/%Y")
    sched_shift = get_shift_value(agent_shift_row, shift_col)
    day_type = classify_rota_day(sched_shift, d)
    if day_type == "scheduled":
        has_scheduled_shift = True
    elif day_type == "sick":
        has_sick_event = True

    if has_scheduled_shift and has_sick_event:
        break

# -----------------------------
# High-level conditional view
# -----------------------------
if has_sick_event and not has_scheduled_shift and df_presence_agent_range.empty:
    st.markdown("""
        <div class="empty-state">
            <img src="app/static/absent.png" width="220" style="opacity:0.85;" />
            <div class="empty-state-label">Sickness recorded in this date range</div>
        </div>
    """, unsafe_allow_html=True)
elif not has_scheduled_shift and df_presence_agent_range.empty:
    st.markdown("""
        <div class="empty-state">
            <img src="app/static/day_off.png" width="220" style="opacity:0.85;" />
            <div class="empty-state-label">No shifts scheduled in this date range</div>
        </div>
    """, unsafe_allow_html=True)
elif has_scheduled_shift and df_presence_agent_range.empty:
    st.markdown("""
        <div class="empty-state">
            <img src="app/static/absent.png" width="220" style="opacity:0.85;" />
            <div class="empty-state-label">Absent for all scheduled shifts in this date range</div>
        </div>
    """, unsafe_allow_html=True)
else:
    # =========================================================
    # AHT & Volume – Selected Range
    # =========================================================
    st.markdown("### Average Handling Time & Volume")

    df_range_items = df_items_agent_range.copy()
    df_range_items["Duration"] = (df_range_items["End DT"] - df_range_items["Start DT"]).dt.total_seconds()

    chat_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "sfdc_liveagent"]
    email_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "casesChannel"]

    aht_chat = chat_items["Duration"].mean() if not chat_items.empty else None    # seconds
    aht_email = email_items["Duration"].mean() if not email_items.empty else None

    num_chat_items = len(chat_items)
    num_email_items = len(email_items)

    # =========================================================
    # Capacity utilisation – Selected Range
    # =========================================================
    chat_only_intervals = []
    email_only_intervals = []
    shared_intervals = []
    for _, presence_row in df_presence_agent_range.iterrows():
        interval = clip_to_window(
            presence_row["Start DT"], presence_row["End DT"],
            range_start_dt, range_end_exclusive,
        )
        if not interval:
            continue
        status = presence_row["Service Presence Status: Developer Name"]
        if status == STATUS_CHAT_ONLY:
            chat_only_intervals.append(interval)
        elif status == STATUS_EMAIL_ONLY:
            email_only_intervals.append(interval)
        elif status == STATUS_SHARED:
            shared_intervals.append(interval)

    chat_only_intervals = merge_intervals(chat_only_intervals)
    email_only_intervals = merge_intervals(email_only_intervals)
    shared_intervals = merge_intervals(shared_intervals)

    def item_intervals(channel):
        channel_items = df_items_agent_overlap[
            df_items_agent_overlap["Service Channel: Developer Name"] == channel
        ]
        intervals = [
            clip_to_window(start, end, range_start_dt, range_end_exclusive)
            for start, end in zip(channel_items["Start DT"], channel_items["End DT"])
        ]
        return [interval for interval in intervals if interval]

    chat_intervals = item_intervals(CHAT_DEVNAME)
    email_intervals = merge_intervals(item_intervals(EMAIL_DEVNAME))

    chat_available_intervals = merge_intervals(chat_only_intervals + shared_intervals)
    chat_available_seconds = sum_seconds(chat_available_intervals)
    chat_slot_seconds = concurrent_slot_seconds(
        chat_intervals, chat_available_intervals, CHAT_CONCURRENCY_CAPACITY
    )
    chat_load_seconds = chat_slot_seconds / CHAT_CONCURRENCY_CAPACITY
    chat_utilization = (
        chat_load_seconds / chat_available_seconds if chat_available_seconds else None
    )

    email_only_capacity_seconds = sum_seconds(email_only_intervals)
    email_only_load_seconds = (
        intersect_seconds(email_intervals, email_only_intervals)
        if email_only_intervals else 0.0
    )
    shared_email_capacity, shared_email_load, email_excess_seconds = (
        email_assignable_capacity(chat_intervals, email_intervals, shared_intervals)
    )
    email_capacity_seconds = email_only_capacity_seconds + shared_email_capacity
    email_load_seconds = email_only_load_seconds + shared_email_load
    email_utilization = (
        email_load_seconds / email_capacity_seconds if email_capacity_seconds else None
    )

    overall_available_seconds = sum_seconds(merge_intervals(
        chat_only_intervals + email_only_intervals + shared_intervals
    ))
    overall_load_seconds = chat_load_seconds + email_load_seconds
    shift_utilization = (
        overall_load_seconds / overall_available_seconds
        if overall_available_seconds else None
    )

    col_aht1, col_aht2 = st.columns(2)
    with col_aht1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Chat (mm:ss)</div>
                <div class="metric-value-accent">{format_seconds_to_mm_ss(aht_chat) if aht_chat is not None else "–"}</div>
                <div class="metric-title" style="margin-top:12px;">Chat Items</div>
                <div class="metric-value">{num_chat_items}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_aht2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Email (mm:ss)</div>
                <div class="metric-value-accent">{format_seconds_to_mm_ss(aht_email) if aht_email is not None else "–"}</div>
                <div class="metric-title" style="margin-top:12px;">Email Items</div>
                <div class="metric-value">{num_email_items}</div>
            </div>
        """, unsafe_allow_html=True)

    chat_util_display = f"{chat_utilization:.1%}" if chat_utilization is not None else "–"
    email_util_display = f"{email_utilization:.1%}" if email_utilization is not None else "–"
    shift_util_display = f"{shift_utilization:.1%}" if shift_utilization is not None else "–"
    util_chat_col, util_email_col, util_shift_col = st.columns(3)
    with util_chat_col:
        st.markdown(f"""
            <div class="metric-container" title="Two chat slots per agent: one active chat uses 50% capacity and two use 100%.">
                <div class="metric-title">Chat Utilisation</div>
                <div class="metric-value-accent">{chat_util_display}</div>
                <div class="metric-title" style="margin-top:8px;">{chat_load_seconds/3600:.1f} load-h of {chat_available_seconds/3600:.1f}h</div>
            </div>
        """, unsafe_allow_html=True)
    with util_email_col:
        st.markdown(f"""
            <div class="metric-container" title="During Available_All, email capacity counts only while no chat is active.">
                <div class="metric-title">Email Utilisation</div>
                <div class="metric-value-accent">{email_util_display}</div>
                <div class="metric-title" style="margin-top:8px;">{email_load_seconds/3600:.1f} load-h of {email_capacity_seconds/3600:.1f} assignable-h</div>
            </div>
        """, unsafe_allow_html=True)
    with util_shift_col:
        st.markdown(f"""
            <div class="metric-container" title="Capacity-adjusted chat and email load divided by total available time.">
                <div class="metric-title">Shift Utilisation</div>
                <div class="metric-value-accent">{shift_util_display}</div>
                <div class="metric-title" style="margin-top:8px;">{overall_load_seconds/3600:.1f} load-h of {overall_available_seconds/3600:.1f}h</div>
            </div>
        """, unsafe_allow_html=True)

    if email_excess_seconds > 0:
        st.caption(
            f"⚠️ {email_excess_seconds/3600:.1f} email-hours were recorded during an "
            "active chat while the agent was in Available_All. They are excluded from "
            "email utilisation and shown as excess demand."
        )

    # =========================================================
    # Long Chat Handles (>= 15 minutes)
    # =========================================================
    # Driven directly from chat_transcripts.csv — one row per
    # conversation with exact Start/End times recorded by Salesforce.
    # No segment grouping or fuzzy matching needed.
    # =========================================================
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Long Chat Handles (≥ 15 min)")

    LONG_CHAT_THRESHOLD_SECONDS = 15 * 60

    required_chat_cols = {"Agent Name", "Start DT", "End DT", "Duration (s)"}
    if df_chat.empty or not required_chat_cols.issubset(df_chat.columns):
        if df_chat.empty:
            st.warning("⚠️ chat_transcripts.csv not found. Make sure it is committed to your repository.")
        else:
            found_cols = list(df_chat.columns)
            missing = required_chat_cols - set(df_chat.columns)
            st.warning(f"⚠️ chat_transcripts.csv loaded but missing expected columns.\n\nFound: `{found_cols}`\n\nMissing: `{missing}`")
    else:
        # Filter to this agent, within the selected date range
        agent_chats = df_chat[
            (df_chat["Agent Name"] == agent) &
            (df_chat["Start DT"].dt.date >= start_date) &
            (df_chat["Start DT"].dt.date <= end_date)
        ].copy()

        long_chats = agent_chats[
            agent_chats["Duration (s)"] >= LONG_CHAT_THRESHOLD_SECONDS
        ].sort_values("Start DT").reset_index(drop=True)

        if long_chats.empty:
            st.info("No chat conversations of 15 minutes or more in the selected range.")
        else:
            long_chats["Handle Time (mm:ss)"] = long_chats["Duration (s)"].apply(
                format_seconds_to_mm_ss
            )

            display_cols = [
                "Handle Time (mm:ss)",
                "Start DT",
                "End DT",
                "Case Number",
                "Visitor Email",
                "Chat Button: Developer Name",
                "Chat Transcript Name",
            ]
            cols_present = [c for c in display_cols if c in long_chats.columns]
            st.dataframe(
                long_chats[cols_present],
                width="stretch",
                hide_index=True,
            )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### Daily Overview")

    total_shift_seconds = 0
    total_available_seconds = 0
    days_worked = 0

    lunch_days_with_data = 0
    lunch_days_out_of_window = 0

    available_statuses = {"Available_Chat", "Available_Email_and_Web", "Available_All"}

    for d in day_list:
        agent_daily = df_presence_agent_range[df_presence_agent_range["Start DT"].dt.date == d].copy()
        if agent_daily.empty:
            continue

        days_worked += 1

        first_segment_start = agent_daily["Start DT"].min()
        last_segment_end = agent_daily["End DT"].max()
        day_shift_duration = (last_segment_end - first_segment_start).total_seconds()
        total_shift_seconds += day_shift_duration

        # Use the scheduled rota start time as the reference point for lunch compliance.
        shift_col = d.strftime("%d/%m/%Y")
        scheduled_shift = get_shift_value(agent_shift_row, shift_col)
        scheduled_shift_start, _ = parse_shift_range(scheduled_shift, d)

        avail_df_day = agent_daily[agent_daily["Service Presence Status: Developer Name"].isin(available_statuses)]
        if not avail_df_day.empty:
            day_available_seconds = (avail_df_day["End DT"] - avail_df_day["Start DT"]).dt.total_seconds().sum()
            total_available_seconds += day_available_seconds

        lunch_entry = agent_daily[
            agent_daily["Service Presence Status: Developer Name"] == "Busy_Lunch"
        ].sort_values(by="Start DT")
        if not lunch_entry.empty and scheduled_shift_start is not None:
            lunch_days_with_data += 1
            lunch_start = lunch_entry.iloc[0]["Start DT"]
            time_to_lunch = (lunch_start - scheduled_shift_start).total_seconds()
            # Allow a 15-minute grace period either side of the 3–5 hour lunch window.
            if time_to_lunch < (2 * 3600 + 45 * 60) or time_to_lunch > (5 * 3600 + 15 * 60):
                lunch_days_out_of_window += 1

    if total_shift_seconds > 0:
        hours = int(total_shift_seconds // 3600)
        minutes_only = int((total_shift_seconds % 3600) // 60)
        total_shift_display = f"{hours:02d}:{minutes_only:02d}"
    else:
        total_shift_display = "00:00"

    if total_available_seconds > 0:
        avail_hours = int(total_available_seconds // 3600)
        avail_minutes_only = int((total_available_seconds % 3600) // 60)
        total_available_display = f"{avail_hours:02d}:{avail_minutes_only:02d}"
    else:
        total_available_display = "00:00"

    expected_seconds = days_worked * (7 * 3600 + 50 * 60)
    availability_warning = days_worked > 0 and total_available_seconds < expected_seconds

    if lunch_days_with_data > 0:
        lunch_ok = lunch_days_with_data - lunch_days_out_of_window
        lunch_text = f"{lunch_ok}/{lunch_days_with_data} days OK"
        lunch_warning = lunch_days_out_of_window > 0
    else:
        lunch_text = "No Lunch Data"
        lunch_warning = False

    col3, col4, col5 = st.columns(3)
    with col3:
        box_class = "metric-container-warning" if lunch_warning else "metric-container"
        val_class = "metric-value" if lunch_warning else "metric-value-success"
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Lunch Compliance</div>
                <div class="{val_class}">{lunch_text}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">Total Shift Time</div>
                <div class="metric-value">{total_shift_display}</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        box_class = "metric-container-warning" if availability_warning else "metric-container"
        val_class = "metric-value" if availability_warning else "metric-value-success"
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Total Available Time</div>
                <div class="{val_class}">{total_available_display}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # =========================================================
    # Per-Day Shift & Adherence – Selected Range
    # =========================================================
    st.markdown("### Per-Day Shift & Adherence")

    per_day_rows = []

    for d in day_list:
        shift_col = d.strftime("%d/%m/%Y")
        sched_shift = get_shift_value(agent_shift_row, shift_col)
        day_type = classify_rota_day(sched_shift, d)

        agent_daily = df_presence_agent_range[df_presence_agent_range["Start DT"].dt.date == d].copy()

        if agent_daily.empty:
            if day_type == "sick":
                status = "Sick"
            elif day_type == "scheduled":
                status = "Absent (Scheduled)"
            elif day_type == "manual_late":
                status = "Late (Recorded)"
            elif day_type == "other_event":
                status = sched_shift
            else:
                status = "Day Off / Not Assigned"
            per_day_rows.append(
                {
                    "Date": d.strftime("%d %b %Y"),
                    "Scheduled Shift": sched_shift or "Not Assigned",
                    "Actual Shift": "—",
                    "Lunch Break": "—",
                    "Late (min)": "",
                    "Status": status,
                }
            )
            continue

        earliest = agent_daily["Start DT"].min()
        latest = agent_daily["End DT"].max()
        actual_shift_str = f"{earliest.strftime('%H:%M')}–{latest.strftime('%H:%M')}"

        # Show the full recorded lunch break window and total duration.
        lunch_segments = agent_daily[
            agent_daily["Service Presence Status: Developer Name"] == "Busy_Lunch"
        ].sort_values("Start DT")

        if not lunch_segments.empty:
            lunch_start = lunch_segments["Start DT"].min()
            lunch_end = lunch_segments["End DT"].max()
            lunch_seconds = (
                lunch_segments["End DT"] - lunch_segments["Start DT"]
            ).dt.total_seconds().clip(lower=0).sum()
            lunch_minutes = int(round(lunch_seconds / 60))
            lunch_break_str = (
                f"{lunch_start.strftime('%H:%M')}–{lunch_end.strftime('%H:%M')} "
                f"({lunch_minutes} min)"
            )
        else:
            lunch_break_str = "—"

        late_minutes = ""
        status = "Worked"

        if day_type == "sick":
            status = "Sick (worked)"
        elif day_type == "manual_late":
            status = "Late (Recorded)"
        elif day_type == "scheduled":
            sched_start, _ = parse_shift_range(sched_shift, d)
            if sched_start:
                delay = (earliest - sched_start).total_seconds() / 60
                if delay >= 5:
                    late_minutes = int(delay)
                    status = "Late"
                else:
                    status = "On Time"

        per_day_rows.append(
            {
                "Date": d.strftime("%d %b %Y"),
                "Scheduled Shift": sched_shift or "Not Assigned",
                "Actual Shift": actual_shift_str,
                "Lunch Break": lunch_break_str,
                "Late (min)": late_minutes,
                "Status": status,
            }
        )

    if per_day_rows:
        per_day_df = pd.DataFrame(per_day_rows)
        # Coerce Late (min) to string to avoid Arrow int/str mix issues
        per_day_df["Late (min)"] = per_day_df["Late (min)"].astype(str)
        st.dataframe(per_day_df, width="stretch", hide_index=True)
    else:
        st.info("No per-day shift data available for this range.")

# =========================================================
# Lateness – Last 30 Days (from end of selected range)
# =========================================================
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("### Lateness – Last 30 Days")

anchor_date = end_date if isinstance(end_date, date_type) else pd.to_datetime(end_date).date()

total_minutes_late = 0
window_days = [anchor_date - timedelta(days=i) for i in range(0, 30)]
lateness_incidents = []

agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()

for d in window_days:
    shift_col = d.strftime("%d/%m/%Y")
    sched_shift_d = get_shift_value(agent_shift_row, shift_col)
    day_type_d = classify_rota_day(sched_shift_d, d)

    df_day_late_check = df_presence[
        (df_presence["Created By: Full Name"] == agent)
        & (df_presence["Start DT"].dt.date == d)
    ]

    if day_type_d == "manual_late":
        lateness_incidents.append(
            f"- **{d.strftime('%d %b %Y')}**: Recorded late"
        )
        continue

    if not df_day_late_check.empty and day_type_d == "scheduled":
        sched_start_d, _ = parse_shift_range(sched_shift_d, d)
        actual_start_time_d = df_day_late_check["Start DT"].min()
        if sched_start_d and actual_start_time_d:
            delay = (actual_start_time_d - sched_start_d).total_seconds() / 60
            if delay >= 5:
                total_minutes_late += delay
                lateness_incidents.append(
                    f"- **{d.strftime('%d %b %Y')}**: {int(delay)} min late"
                )

if not lateness_incidents:
    st.markdown("""
        <div class="empty-state">
            <div class="empty-state-label">No lateness incidents in the last 30 days</div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="metric-container-warning">
            <div class="metric-title">Total Lateness – Last 30 Days</div>
            <div class="metric-value">{int(total_minutes_late)} min</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Lateness Incidents")
    items_html = "\n".join([
        f'<li class="incident-item"><span class="incident-date">{inc.split("**: ")[0].replace("- **", "")}</span>'
        f'<span class="incident-badge">{inc.split("**: ")[1]}</span></li>'
        for inc in lateness_incidents
    ])
    st.markdown(f'<ul class="incident-list">{items_html}</ul>', unsafe_allow_html=True)

# =========================================================
# Absence – Last 90 Days (from end of selected range)
# =========================================================
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("### Absence – Last 90 Days")

abs_window = [anchor_date - timedelta(days=i) for i in range(0, 90)]
absent_days = []
sick_days = []

agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()

for d in abs_window:
    shift_col_d = d.strftime("%d/%m/%Y")
    sched_shift_d = get_shift_value(agent_shift_row, shift_col_d)
    day_type_d = classify_rota_day(sched_shift_d, d)

    if day_type_d == "sick":
        sick_days.append(d.strftime("%d %b %Y"))
        continue

    if day_type_d != "scheduled":
        continue

    df_day_presence = df_presence[
        (df_presence["Created By: Full Name"] == agent)
        & (df_presence["Start DT"].dt.date == d)
    ]

    if df_day_presence.empty:
        absent_days.append(d.strftime("%d %b %Y"))

if not absent_days and not sick_days:
    st.markdown("""
        <div class="empty-state">
            <div class="empty-state-label">No absences or sickness in the last 90 days</div>
        </div>
    """, unsafe_allow_html=True)
else:
    col_abs, col_sick = st.columns(2)
    with col_abs:
        box_class = "metric-container-warning" if absent_days else "metric-container"
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Absence Count – Last 90 Days</div>
                <div class="metric-value">{len(absent_days)}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_sick:
        box_class = "metric-container-warning" if sick_days else "metric-container"
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Sickness Count – Last 90 Days</div>
                <div class="metric-value">{len(sick_days)}</div>
            </div>
        """, unsafe_allow_html=True)

    if absent_days:
        st.markdown("#### Absence Dates")
        items_html = "\n".join([
            f'<li class="incident-item"><span class="incident-date">{ad}</span>'
            f'<span class="incident-badge">Absent</span></li>'
            for ad in absent_days
        ])
        st.markdown(f'<ul class="incident-list">{items_html}</ul>', unsafe_allow_html=True)

    if sick_days:
        st.markdown("#### Sickness Dates")
        items_html = "\n".join([
            f'<li class="incident-item"><span class="incident-date">{sd}</span>'
            f'<span class="incident-badge">Sick</span></li>'
            for sd in sick_days
        ])
        st.markdown(f'<ul class="incident-list">{items_html}</ul>', unsafe_allow_html=True)
