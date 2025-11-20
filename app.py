import streamlit as st
import pandas as pd

# --- Load All Data Freshly on Each Run ---

# Presence: parse known datetime columns
df_presence = pd.read_csv("report_presence.csv", parse_dates=["Start DT", "End DT"])

# Report Items: parse known datetime columns
df_items = pd.read_csv("report_items.csv", parse_dates=["Start DT", "End DT"])

# Shifts: no date parsing required
df_shifts = pd.read_csv("shifts.csv")

from datetime import datetime, timedelta, time as dtime

# --- Load the SVG Logo ---
with open("goat_logo.svg", "r") as f:
    svg_code = f.read()

# IMPORTANT: st.set_page_config must be called as the very first Streamlit command
st.set_page_config(page_title="Agent Dashboard", layout="wide")

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

    .st-emotion-cache-1r6dm7m {
        font-size: 1.5em;
        font-weight: bold;
    }
    .st-emotion-cache-16idsysf p {
        font-size: 0.2em;
        color: #555555;
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

def load_data():
    df_items = pd.read_csv("report_items.csv", dayfirst=True)
    df_items["Start DT"] = pd.to_datetime(df_items["Start DT"], dayfirst=True, errors="coerce")
    df_items["End DT"] = pd.to_datetime(df_items["End DT"], dayfirst=True, errors="coerce")

    df_presence = pd.read_csv("report_presence.csv", dayfirst=True)
    df_presence["Start DT"] = pd.to_datetime(df_presence["Start DT"], dayfirst=True, errors="coerce")
    df_presence["End DT"] = pd.to_datetime(df_presence["End DT"], dayfirst=True, errors="coerce")

    df_shifts = pd.read_csv("shifts.csv")
    df_shifts.rename(columns={"Column1": "Agent Name"}, inplace=True)
    df_shifts["Agent Name"] = df_shifts["Agent Name"].str.strip()

    df_items["User: Full Name"] = df_items["User: Full Name"].str.strip()
    df_items["Service Channel: Developer Name"] = df_items["Service Channel: Developer Name"].str.strip()
    df_presence["Created By: Full Name"] = df_presence["Created By: Full Name"].str.strip()
    df_presence["Service Presence Status: Developer Name"] = df_presence["Service Presence Status: Developer Name"].str.strip()

    return df_items, df_presence, df_shifts

df_items, df_presence, df_shifts = load_data()

agents = sorted(df_presence["Created By: Full Name"].dropna().unique())
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

if isinstance(date_range, (list, tuple)):
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

if start_date > end_date:
    start_date, end_date = end_date, start_date

from datetime import date as date_type

def parse_time(val):
    if pd.isna(val):
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except Exception:
            continue
    return None

def parse_td(val):
    if pd.isna(val):
        return None
    h, m, s = str(val).split(":")
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))

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

def parse_shift_start(shift_str, base_date):
    if not shift_str or "–" not in shift_str:
        return None
    start_part = shift_str.split("–")[0].strip().upper()
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            shift_time = datetime.strptime(start_part, fmt).time()
            return datetime.combine(base_date, shift_time)
        except ValueError:
            continue
    return None

def format_seconds_to_mm_ss(total_seconds):
    if total_seconds is None:
        return "–"
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# --- Header (Agent + Date Range) ---
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

# --- Range boundaries ---
range_start_dt = datetime.combine(start_date, dtime(0, 0))
range_end_dt = datetime.combine(end_date, dtime(23, 59))

# Filter presence & items to agent + range
df_presence_agent_range = df_presence[
    (df_presence["Created By: Full Name"] == agent)
    & (df_presence["End DT"] >= range_start_dt)
    & (df_presence["Start DT"] <= range_end_dt)
].copy()

df_items_agent_range = df_items[
    (df_items["User: Full Name"] == agent)
    & (df_items["End DT"] >= range_start_dt)
    & (df_items["Start DT"] <= range_end_dt)
].copy()

# Determine if any shifts scheduled in this range
day_list = [
    start_date + timedelta(days=i)
    for i in range((end_date - start_date).days + 1)
]

has_scheduled_shift = False
agent_shift_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()

for d in day_list:
    shift_col = d.strftime("%d/%m/%Y")
    if not agent_shift_row.empty and shift_col in df_shifts.columns:
        val = agent_shift_row[shift_col].values[0]
        if pd.notna(val) and str(val).strip() != "" and str(val).strip().lower() != "not assigned":
            has_scheduled_shift = True
            break

# --- Top-level conditional view ---
if not has_scheduled_shift and df_presence_agent_range.empty:
    # No scheduled shifts and no presence – treat as time off
    st.image("day_off.png", caption="No Shifts Scheduled in this Date Range", width=300)
    st.info("You were not scheduled to work on any of the selected days.")
elif has_scheduled_shift and df_presence_agent_range.empty:
    # Scheduled at least once, but zero presence across entire range
    st.image("absent.png", caption="Absent for all Scheduled Shifts in this Date Range", width=300)
else:
    # =========================================================
    # AHT & Volume (Combined across range)
    # =========================================================
    st.markdown("### Average Handling Time (AHT) & Volume – Selected Range")

    df_range_items = df_items_agent_range.copy()
    df_range_items["Duration"] = (df_range_items["End DT"] - df_range_items["Start DT"]).dt.total_seconds()

    chat_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "sfdc_liveagent"]
    email_items = df_range_items[df_range_items["Service Channel: Developer Name"] == "casesChannel"]

    aht_chat = chat_items["Duration"].mean() if not chat_items.empty else None
    aht_email = email_items["Duration"].mean() if not email_items.empty else None

    num_chat_items = len(chat_items)
    num_email_items = len(email_items)

    # =========================================================
    # Shift Utilization (Combined across range)
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
    # Long Chat Handles (>= 15 minutes) – table
    # =========================================================
    st.markdown("---")
    st.markdown("### Long Chat Handles (≥ 15 minutes) – Selected Range")

    long_chat = chat_items[chat_items["Duration"] >= 15 * 60].copy()

    if long_chat.empty:
        st.info("No chat items with a handle time of 15 minutes or more in the selected range.")
    else:
        long_chat["Handle Time (mm:ss)"] = long_chat["Duration"].apply(format_seconds_to_mm_ss)

        # Choose useful columns if they exist
        preferred_cols = [
            "Handle Time (mm:ss)",
            "Start DT",
            "End DT",
            "Duration",
            "Case Number",
            "Parent Case",
            "Interaction ID",
            "Live Chat Transcript ID",
            "Subject",
            "Record Type",
            "Service Channel: Developer Name",
        ]
        cols_present = [c for c in preferred_cols if c in long_chat.columns]
        # Ensure Handle Time is first
        if "Handle Time (mm:ss)" in cols_present:
            cols_present = (
                ["Handle Time (mm:ss)"] + [c for c in cols_present if c != "Handle Time (mm:ss)"]
            )

        display_df = long_chat[cols_present] if cols_present else long_chat
        st.dataframe(display_df, use_container_width=True)

    st.markdown("---")

    # =========================================================
    # Daily Overview (aggregated across range)
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

        # Shift duration for the day (first start to last end)
        first_segment_start = agent_daily["Start DT"].min()
        last_segment_end = agent_daily["End DT"].max()
        day_shift_duration = (last_segment_end - first_segment_start).total_seconds()
        total_shift_seconds += day_shift_duration

        # Available time for the day
        avail_df_day = agent_daily[agent_daily["Service Presence Status: Developer Name"].isin(available_statuses)]
        if not avail_df_day.empty:
            day_available_seconds = (avail_df_day["End DT"] - avail_df_day["Start DT"]).dt.total_seconds().sum()
            total_available_seconds += day_available_seconds

        # Lunch compliance
        lunch_entry = agent_daily[
            agent_daily["Service Presence Status: Developer Name"] == "Busy_Lunch"
        ].sort_values(by="Start DT")
        if not lunch_entry.empty:
            lunch_days_with_data += 1
            lunch_start = lunch_entry.iloc[0]["Start DT"]
            time_to_lunch = (lunch_start - first_segment_start).total_seconds()
            if time_to_lunch < 3 * 3600 or time_to_lunch > 5 * 3600:
                lunch_days_out_of_window += 1

    # Format totals
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

    # Availability warning: expect 7h50 per worked day
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
                <div class="{box_class}">
                    <div class="metric-title">Total Available Time</div>
                    <div class="metric-value">{total_available_display}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================
    # Per-Day Shift & Adherence Table (Option 2)
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
        st.dataframe(per_day_df, use_container_width=True)
    else:
        st.info("No per-day shift data available for this range.")

# =========================================================
# Lateness (Last 30 Days) – anchored to end of selected range
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
# Absence (Last 90 Days) – anchored to end of selected range
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
