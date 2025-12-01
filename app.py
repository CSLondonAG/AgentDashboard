import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime, timedelta, time as dtime, date as date_type

# IMPORTANT: st.set_page_config must be called as the very first Streamlit command
st.set_page_config(page_title="Agent Dashboard", layout="wide")

# --- Load the SVG Logo (wrapped in try so it doesn't crash if missing) ---
try:
    with open("goat_logo.svg", "r", encoding="utf-8") as f:
        svg_code = f.read()
except Exception:
    svg_code = ""

# Custom CSS for better aesthetics and font sizes
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6; /* Light grey background */
    }

    .custom-main-header-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        margin-top: -35px;
        margin-bottom: 0.1rem;
        padding: 0;
    }

    .custom-main-header-container h1 {
        font-size: 1.5rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        display: inline;
    }

    .header-logo-inline {
        width: 40px;
        height: auto;
        margin-left: 10px;
        vertical-align: middle;
        margin-top: -5px;
    }

    h2 {
        font-size: 0.75rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-bottom: 0 !important;
        line-height: 1.2 !important;
    }

    .subheader-smaller {
        font-size: 0.75rem !important;
        font-weight: 500;
        color: #444;
        margin-bottom: 0.1rem;
    }

    h3 {
        font-size: 1.5rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.8rem !important;
        color: #333333;
    }

    .metric-container {
        padding: 8px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        text-align: center;
    }
    .metric-title {
        font-size: 1.1em;
        color: #333333;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #007bff;
    }
    .late-warning {
        background-color: #ffebeb;
        border: 1px solid #ff4d4d;
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        color: #cc0000;
        margin-top: 10px;
    }
    .info-box {
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
    }

    .shift-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
        font-size: 1.5em;
        font-weight: bold;
        color: #007bff;
        text-align: center;
    }

    .metric-container-warning {
        padding: 8px;
        border-radius: 10px;
        background-color: #ffebeb;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #ff4d4d;
    }
    .metric-container-warning .metric-title {
        font-size: 1.1em;
        color: #333333;
        margin-bottom: 5px;
    }
    .metric-container-warning .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #ff4d4d;
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

    # Chat transcripts (for enrichment)
    df_chat = safe_read_csv("chat.csv", dayfirst=True)
    if not df_chat.empty:
        if "Owner: Full Name" in df_chat.columns:
            df_chat["Owner: Full Name"] = df_chat["Owner: Full Name"].astype(str).str.strip()
        if "Date/Time Opened" in df_chat.columns:
            df_chat["Date/Time Opened DT"] = pd.to_datetime(
                df_chat["Date/Time Opened"],
                format="%d/%m/%Y, %H:%M",
                errors="coerce",
            )

    return df_items, df_presence, df_shifts, df_chat


df_items, df_presence, df_shifts, df_chat = load_data()

if df_presence.empty or df_items.empty or df_shifts.empty:
    st.error("One or more data files are empty or missing. Please check report_items.csv, report_presence.csv, and shifts.csv.")
    st.stop()


# -----------------------------
# Utility functions
# -----------------------------
def parse_shift_range(shift_str, base_date):
    if not shift_str or " - " not in shift_str:
        return None, None
    try:
        start_str, end_str = shift_str.split(" - ")
        start_time = datetime.strptime(start_str.strip().upper(), "%I:%M %p").time()
        end_time = datetime.strptime(end_str.strip().upper(), "%I:%M %p").time()
        return datetime.combine(base_date, start_time), datetime.combine(base_date, end_time)
    except Exception:
        return None, None


def format_seconds_to_mm_ss(total_seconds):
    if total_seconds is None:
        return "–"
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def enrich_long_chat_with_transcripts(long_chat_df, chat_df, agent_name, max_diff_minutes=10):
    """
    For each long chat item, find the closest transcript in chat_df
    for the same agent (Owner: Full Name) within max_diff_minutes of Start DT.

    This version guarantees one enrichment row per long_chat row and
    avoids index-mismatch creating extra blank rows.
    """
    if long_chat_df.empty or chat_df.empty:
        return long_chat_df
    if "Owner: Full Name" not in chat_df.columns or "Date/Time Opened DT" not in chat_df.columns:
        return long_chat_df

    # Only consider this agent’s chats
    chat_agent = chat_df[chat_df["Owner: Full Name"] == agent_name].copy()
    if chat_agent.empty:
        return long_chat_df

    chat_agent = chat_agent.dropna(subset=["Date/Time Opened DT"])

    work_df = long_chat_df.reset_index(drop=True).copy()

    def find_match(row):
        t = row["Start DT"]
        if pd.isna(t):
            return {
                "Case Number": None,
                "Visitor Email": None,
                "Chat Button: Developer Name": None,
                "Abandoned After": None,
                "Wait Time": None,
            }
        window = pd.Timedelta(minutes=max_diff_minutes)
        subset = chat_agent[
            (chat_agent["Date/Time Opened DT"] >= t - window) &
            (chat_agent["Date/Time Opened DT"] <= t + window)
        ]
        if subset.empty:
            return {
                "Case Number": None,
                "Visitor Email": None,
                "Chat Button: Developer Name": None,
                "Abandoned After": None,
                "Wait Time": None,
            }

        # Pick the closest in time
        idx = (subset["Date/Time Opened DT"] - t).abs().idxmin()
        m = subset.loc[idx]
        return {
            "Case Number": m.get("Case Number"),
            "Visitor Email": m.get("Visitor Email"),
            "Chat Button: Developer Name": m.get("Chat Button: Developer Name"),
            "Abandoned After": m.get("Abandoned After"),
            "Wait Time": m.get("Wait Time"),
        }

    extra_cols = work_df.apply(find_match, axis=1, result_type="expand")
    enriched = pd.concat([work_df, extra_cols], axis=1)
    return enriched


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

st.sidebar.header("Select Agent and Date Range")
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
st.markdown("---")

# -----------------------------
# Filter data to agent + range
# -----------------------------
range_start_dt = datetime.combine(start_date, dtime(0, 0))
range_end_dt = datetime.combine(end_date, dtime(23, 59))

df_presence_agent_range = df_presence[
    (df_presence["Created By: Full Name"] == agent)
    & (df_presence["End DT"] >= range_start_dt)
    & (df_presence["Start DT"] <= range_end_dt)
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

# List of days in the selected range
day_list = [
    start_date + timedelta(days=i)
    for i in range((end_date - start_date).days + 1)
]

# Check schedule in range
agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()
has_scheduled_shift = False
for d in day_list:
    shift_col = d.strftime("%d/%m/%Y")
    if not agent_shift_row.empty and shift_col in df_shifts.columns:
        val = agent_shift_row[shift_col].values[0]
        if pd.notna(val) and str(val).strip() != "" and str(val).strip().lower() != "not assigned":
            has_scheduled_shift = True
            break

# -----------------------------
# High-level conditional view
# -----------------------------
if not has_scheduled_shift and df_presence_agent_range.empty:
    st.image("day_off.png", caption="No Shifts Scheduled in this Date Range", width=300)
    st.info("You were not scheduled to work on any of the selected days.")
elif has_scheduled_shift and df_presence_agent_range.empty:
    st.image("absent.png", caption="Absent for all Scheduled Shifts in this Date Range", width=300)
else:
    # =========================================================
    # AHT & Volume – Selected Range
    # =========================================================
    st.markdown("### Average Handling Time (AHT) & Volume – Selected Range")

    df_range_items = df_items_agent_range.copy()
    df_range_items["Duration"] = (df_range_items["End DT"] - df_range_items["Start DT"]).dt.total_seconds()

    chat_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "sfdc_liveagent"]
    email_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "casesChannel"]

    aht_chat = chat_items["Duration"].mean() if not chat_items.empty else None    # seconds
    aht_email = email_items["Duration"].mean() if not email_items.empty else None

    num_chat_items = len(chat_items)
    num_email_items = len(email_items)

    # =========================================================
    # Shift Utilisation – Selected Range
    # =========================================================
    minutes = pd.date_range(start=range_start_dt, end=range_end_dt, freq="min", inclusive="left")

    total_available_minutes = 0
    total_handling_minutes = 0

    for t in minutes:
        pres_at_t = df_presence_agent_range[
            (df_presence_agent_range["Start DT"] <= t)
            & (df_presence_agent_range["End DT"] > t)
        ]
        status = pres_at_t.iloc[0]["Service Presence Status: Developer Name"] if not pres_at_t.empty else None

        if status in ("Available_Chat", "Available_Email_and_Web", "Available_All"):
            total_available_minutes += 1

            is_handling = not df_items_agent_range[
                (df_items_agent_range["Service Channel: Developer Name"].isin(["sfdc_liveagent", "casesChannel"]))
                & (df_items_agent_range["Start DT"] <= t)
                & (df_items_agent_range["End DT"] > t)
            ].empty

            if is_handling:
                total_handling_minutes += 1

    shift_utilization = total_handling_minutes / total_available_minutes if total_available_minutes > 0 else 0.0

    col_aht1, col_aht2 = st.columns(2)
    with col_aht1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Chat (mm:ss)</div>
                <div class="metric-value">{format_seconds_to_mm_ss(aht_chat) if aht_chat is not None else "–"}</div>
                <div class="metric-title"># Chat Items</div>
                <div class="metric-value">{num_chat_items}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_aht2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Email (mm:ss)</div>
                <div class="metric-value">{format_seconds_to_mm_ss(aht_email) if aht_email is not None else "–"}</div>
                <div class="metric-title"># Email Items</div>
                <div class="metric-value">{num_email_items}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Shift Utilization (Selected Range)</div>
            <div class="metric-value">{shift_utilization:.1%}</div>
        </div>
    """, unsafe_allow_html=True)

    # =========================================================
    # Long Chat Handles (>= 15 minutes) – table with chat.csv enrichment
    # =========================================================
    st.markdown("---")
    st.markdown("### Long Chat Handles (≥ 15 minutes) – Selected Range")

    # Start from this agent's chat items
    agent_chat_items = chat_items.copy()

    # Extra defensive filter: ensure only this agent
    if "User: Full Name" in agent_chat_items.columns:
        agent_chat_items = agent_chat_items[agent_chat_items["User: Full Name"] == agent]

    # NEW: Deduplicate identical chat rows (prevents duplicated long chats)
    agent_chat_items = agent_chat_items.drop_duplicates(
        subset=["User: Full Name", "Start DT", "End DT", "Duration"],
        keep="first"
    )

    long_chat = agent_chat_items[agent_chat_items["Duration"] >= 15 * 60].copy()

    if long_chat.empty:
        st.info("No chat items with a handle time of 15 minutes or more in the selected range.")
    else:
        long_chat["Handle Time (mm:ss)"] = long_chat["Duration"].apply(format_seconds_to_mm_ss)

        # Enrich with transcript/case data from chat.csv
        long_chat = enrich_long_chat_with_transcripts(long_chat, df_chat, agent)

        preferred_cols = [
            "Handle Time (mm:ss)",
            "Start DT",
            "End DT",
            "Duration",
            # From chat.csv:
            "Case Number",
            "Visitor Email",
            "Chat Button: Developer Name",
            "Wait Time",
            "Abandoned After",
            # Optional other context fields if present:
            "Queue: Name",
            "Service Channel: Developer Name",
        ]
        cols_present = [c for c in preferred_cols if c in long_chat.columns]
        if "Handle Time (mm:ss)" in cols_present:
            cols_present = ["Handle Time (mm:ss)"] + [c for c in cols_present if c != "Handle Time (mm:ss)"]

        display_df = long_chat[cols_present] if cols_present else long_chat
        st.dataframe(display_df, width="stretch")

    st.markdown("---")

    # =========================================================
    # Daily Overview – Selected Range
    # =========================================================
    st.markdown("### Daily Overview – Selected Range")

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

        avail_df_day = agent_daily[agent_daily["Service Presence Status: Developer Name"].isin(available_statuses)]
        if not avail_df_day.empty:
            day_available_seconds = (avail_df_day["End DT"] - avail_df_day["Start DT"]).dt.total_seconds().sum()
            total_available_seconds += day_available_seconds

        lunch_entry = agent_daily[
            agent_daily["Service Presence Status: Developer Name"] == "Busy_Lunch"
        ].sort_values(by="Start DT")
        if not lunch_entry.empty:
            lunch_days_with_data += 1
            lunch_start = lunch_entry.iloc[0]["Start DT"]
            time_to_lunch = (lunch_start - first_segment_start).total_seconds()
            if time_to_lunch < 3 * 3600 or time_to_lunch > 5 * 3600:
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
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Lunch Compliance</div>
                <div class="metric-value">{lunch_text}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">Total Shift Time (All Worked Days)</div>
                <div class="metric-value">{total_shift_display}</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        box_class = "metric-container-warning" if availability_warning else "metric-container"
        st.markdown(f"""
            <div class="{box_class}">
                <div class="metric-title">Total Available Time</div>
                <div class="metric-value">{total_available_display}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================
    # Per-Day Shift & Adherence – Selected Range
    # =========================================================
    st.markdown("### Per-Day Shift & Adherence (Selected Range)")

    per_day_rows = []

    for d in day_list:
        shift_col = d.strftime("%d/%m/%Y")
        if not agent_shift_row.empty and shift_col in df_shifts.columns:
            sched_val = agent_shift_row[shift_col].values[0]
            sched_shift = str(sched_val).strip() if pd.notna(sched_val) else ""
        else:
            sched_shift = ""

        agent_daily = df_presence_agent_range[df_presence_agent_range["Start DT"].dt.date == d].copy()

        if agent_daily.empty:
            if sched_shift and sched_shift.lower() != "not assigned":
                status = "Absent (Scheduled)"
            else:
                status = "Day Off / Not Assigned"
            per_day_rows.append(
                {
                    "Date": d.strftime("%d %b %Y"),
                    "Scheduled Shift": sched_shift or "Not Assigned",
                    "Actual Shift": "—",
                    "Late (min)": "",
                    "Status": status,
                }
            )
            continue

        earliest = agent_daily["Start DT"].min()
        latest = agent_daily["End DT"].max()
        actual_shift_str = f"{earliest.strftime('%H:%M')}–{latest.strftime('%H:%M')}"

        late_minutes = ""
        status = "Worked"

        if sched_shift and sched_shift.lower() != "not assigned":
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
                "Late (min)": late_minutes,
                "Status": status,
            }
        )

    if per_day_rows:
        per_day_df = pd.DataFrame(per_day_rows)
        # Coerce Late (min) to string to avoid Arrow int/str mix issues
        per_day_df["Late (min)"] = per_day_df["Late (min)"].astype(str)
        st.dataframe(per_day_df, width="stretch")
    else:
        st.info("No per-day shift data available for this range.")

# =========================================================
# Lateness – Last 30 Days (from end of selected range)
# =========================================================
st.markdown("---")
st.markdown("### Lateness – Last 30 Days (from end of selected range)")

anchor_date = end_date if isinstance(end_date, date_type) else pd.to_datetime(end_date).date()

total_minutes_late = 0
window_days = [anchor_date - timedelta(days=i) for i in range(1, 31)]
lateness_incidents = []

agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()

for d in window_days:
    shift_col = d.strftime("%d/%m/%Y")
    if not agent_shift_row.empty and shift_col in df_shifts.columns:
        sched_val_d = agent_shift_row[shift_col].values[0]
        sched_shift_d = str(sched_val_d).strip() if pd.notna(sched_val_d) else None
    else:
        sched_shift_d = None

    df_day_late_check = df_presence[
        (df_presence["Created By: Full Name"] == agent)
        & (df_presence["Start DT"].dt.date == d)
    ]

    if not df_day_late_check.empty and sched_shift_d:
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
    st.image("no_late.png", caption="No Lateness Incidents Recorded (Last 30 Days)", width=300)
else:
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Total Lateness (Last 30 Days)</div>
            <div class="metric-value">
                {int(total_minutes_late)} min late
                {'<span style="color:red; font-size: 0.7em;"> &#x26A0;</span>' if total_minutes_late > 0 else ''}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Incidents of Lateness (Last 30 Days)")
    for incident in lateness_incidents:
        st.markdown(incident)

# =========================================================
# Absence – Last 90 Days (from end of selected range)
# =========================================================
st.markdown("---")
st.markdown("### Absence – Last 90 Days (from end of selected range)")

abs_window = [anchor_date - timedelta(days=i) for i in range(1, 91)]
absent_days = []

agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()

for d in abs_window:
    shift_col_d = d.strftime("%d/%m/%Y")
    if not agent_shift_row.empty and shift_col_d in df_shifts.columns:
        sched_val_d = agent_shift_row[shift_col_d].values[0]
        sched_shift_d = str(sched_val_d).strip() if pd.notna(sched_val_d) else None
    else:
        sched_shift_d = None

    if not sched_shift_d or sched_shift_d.lower() == "not assigned" or sched_shift_d == "":
        continue

    df_day_presence = df_presence[
        (df_presence["Created By: Full Name"] == agent)
        & (df_presence["Start DT"].dt.date == d)
    ]

    if df_day_presence.empty:
        absent_days.append(d.strftime("%d %b %Y"))

if not absent_days:
    st.image("no_late.png", caption="No Absences in the Last 90 Days", width=300)
else:
    st.markdown(f"""
        <div class="metric-container-warning">
            <div class="metric-title">Absence Count (Last 90 Days)</div>
            <div class="metric-value">{len(absent_days)}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Absence Dates (Last 90 Days)")
    for ad in absent_days:
        st.markdown(f"- **{ad}**")
