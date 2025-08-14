import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dtime
from pathlib import Path

# =========================================================
# Page setup
# =========================================================
st.set_page_config(page_title="Agent Dashboard", layout="wide")

# Try to load SVG logo (won't crash if missing)
svg_code = ""
svg_path = Path("goat_logo.svg")
if svg_path.exists():
    try:
        svg_code = svg_path.read_text(encoding="utf-8")
    except Exception:
        svg_code = ""

# =========================================================
# Styles (kept the same visuals you’ve been using)
# =========================================================
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .custom-main-header-container { display:flex; align-items:center; justify-content:flex-start; margin-top:-35px; margin-bottom:0.1rem; padding:0; }
    .custom-main-header-container h1 { font-size:1.5rem !important; margin:0 !important; padding:0 !important; line-height:1.2 !important; display:inline; }
    .header-logo-inline { width:40px; height:auto; margin-left:10px; vertical-align:middle; margin-top:-5px; }
    h2 { font-size:0.75rem !important; margin-top:0 !important; margin-bottom:0.5rem !important; padding-bottom:0 !important; line-height:1.2 !important; }
    .subheader-smaller { font-size:0.75rem !important; font-weight:500; color:#444; margin-bottom:0.1rem; }
    h3 { font-size:1.5rem !important; margin-top:0.5rem !important; margin-bottom:0.8rem !important; color:#333333; }
    .metric-container { padding:8px; border-radius:10px; background:#ffffff; box-shadow:0 4px 8px rgba(0,0,0,0.1); margin-bottom:20px; text-align:center; }
    .metric-title { font-size:1.1em; color:#333333; margin-bottom:5px; }
    .metric-value { font-size:1.8em; font-weight:bold; color:#007bff; }
    .late-warning { background:#ffebeb; border:1px solid #ff4d4d; padding:10px; border-radius:8px; font-weight:bold; color:#cc0000; margin-top:10px; }
    .info-box { background:#e6f7ff; border:1px solid #91d5ff; padding:10px; border-radius:8px; margin-top:10px; }
    .shift-box { padding:15px; border-radius:8px; background:#e6f7ff; border:1px solid #91d5ff; font-size:1.5em; font-weight:bold; color:#007bff; text-align:center; }
    .metric-container-warning { padding:8px; border-radius:10px; background:#ffebeb; box-shadow:0 4px 8px rgba(0,0,0,0.1); margin-bottom:20px; text-align:center; border:1px solid #ff4d4d; }
    .metric-container-warning .metric-title { font-size:1.1em; color:#333333; margin-bottom:5px; }
    .metric-container-warning .metric-value { font-size:1.8em; font-weight:bold; color:#ff4d4d; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# Utilities
# =========================================================
def format_seconds_to_mm_ss(total_seconds):
    if total_seconds is None:
        return "–"
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def parse_shift_range(shift_str, base_date):
    """
    Parse strings like: "09:00 AM - 05:00 PM"
    Return two datetimes (start, end) or (None, None) if parse fails.
    """
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
    """
    Parse strings like: "09:00 – 17:00" (en dash range already formatted)
    Returns datetime for start, or None.
    """
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

# =========================================================
# Load data (coerce to datetimes and clean)
# =========================================================
@st.cache_data(show_spinner=False)
def load_data():
    # Items
    df_items = pd.read_csv("report_items.csv", dayfirst=True)
    df_items["Start DT"] = pd.to_datetime(df_items["Start DT"], dayfirst=True, errors="coerce")
    df_items["End DT"] = pd.to_datetime(df_items["End DT"], dayfirst=True, errors="coerce")
    df_items = df_items.dropna(subset=["Start DT", "End DT"])
    # normalize text
    if "User: Full Name" in df_items.columns:
        df_items["User: Full Name"] = df_items["User: Full Name"].astype(str).str.strip()
    if "Service Channel: Developer Name" in df_items.columns:
        df_items["Service Channel: Developer Name"] = df_items["Service Channel: Developer Name"].astype(str).str.strip()

    # Presence
    df_presence = pd.read_csv("report_presence.csv", dayfirst=True)
    df_presence["Start DT"] = pd.to_datetime(df_presence["Start DT"], dayfirst=True, errors="coerce")
    df_presence["End DT"] = pd.to_datetime(df_presence["End DT"], dayfirst=True, errors="coerce")
    df_presence = df_presence.dropna(subset=["Start DT", "End DT"])
    # normalize text
    if "Created By: Full Name" in df_presence.columns:
        df_presence["Created By: Full Name"] = df_presence["Created By: Full Name"].astype(str).str.strip()
    if "Service Presence Status: Developer Name" in df_presence.columns:
        df_presence["Service Presence Status: Developer Name"] = df_presence["Service Presence Status: Developer Name"].astype(str).str.strip()

    # Shifts
    df_shifts = pd.read_csv("shifts.csv")
    if "Column1" in df_shifts.columns and "Agent Name" not in df_shifts.columns:
        df_shifts = df_shifts.rename(columns={"Column1": "Agent Name"})
    if "Agent Name" in df_shifts.columns:
        df_shifts["Agent Name"] = df_shifts["Agent Name"].astype(str).str.strip()

    return df_items, df_presence, df_shifts

df_items, df_presence, df_shifts = load_data()

# =========================================================
# Sidebar: agent/date
# =========================================================
agents = sorted(df_presence["Created By: Full Name"].dropna().unique())
st.sidebar.header("Select Agent and Date")
agent = st.sidebar.selectbox("Agent Name", agents)

raw_dates = sorted(df_presence["Start DT"].dt.date.unique())
dates = sorted([pd.to_datetime(d).date() for d in raw_dates])
# default to latest available date
date = st.sidebar.date_input("Date", min_value=min(dates), max_value=max(dates), value=max(dates))

# =========================================================
# Header
# =========================================================
st.markdown(f"""
    <div class="custom-main-header-container">
        <h1>Agent Dashboard for {agent}</h1>
        <div class="header-logo-inline">{svg_code}</div>
    </div>
""", unsafe_allow_html=True)
st.markdown(f"""<div class='subheader-smaller'>Date: {date.strftime('%d %B %Y')}</div>""", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# Determine schedule & presence
# =========================================================
shift_col = date.strftime("%d/%m/%Y")
sched_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()
sched_val = sched_row[shift_col].values[0] if (not sched_row.empty and shift_col in sched_row.columns) else None
sched = str(sched_val).strip() if pd.notna(sched_val) else "Not Assigned"

start_dt = datetime.combine(date, dtime(0, 0))
end_dt = datetime.combine(date, dtime(23, 59))

df_agent_day = df_presence[
    (df_presence["Created By: Full Name"] == agent) &
    (df_presence["Start DT"] >= start_dt) &
    (df_presence["Start DT"] <= end_dt)
]
adherence_data_available = not df_agent_day.empty

# =========================================================
# Conditional UI
# =========================================================
if sched == "Not Assigned":
    st.image("day_off.png", caption="No Shift Scheduled for this Day", width=300)
    st.info("You were not scheduled to work on this day")

elif not adherence_data_available:
    st.image("absent.png", caption="You were Absent from your scheduled shift on this day", width=300)

else:
    # -----------------------------------------------------
    # Shift scheduled & adherence data exists
    # -----------------------------------------------------
    earliest = df_agent_day["Start DT"].min()
    latest = df_agent_day["End DT"].max()
    sched_adherence = f"{earliest.strftime('%I:%M %p')} – {latest.strftime('%I:%M %p')}"

    # -----------------------------------------------------
    # SHIFT UTILIZATION (single %)
    # -----------------------------------------------------
    minutes = pd.date_range(start=start_dt, end=end_dt, freq="min", inclusive="left")

    total_available_minutes = 0
    total_handling_minutes = 0

    for t in minutes:
        pres_at_t = df_presence[
            (df_presence["Created By: Full Name"] == agent) &
            (df_presence["Start DT"] <= t) &
            (df_presence["End DT"] > t)
        ]
        status = pres_at_t.iloc[0]["Service Presence Status: Developer Name"] if not pres_at_t.empty else None

        # Any available state contributes to denominator
        if status in ("Available_Chat", "Available_Email_and_Web", "Available_All"):
            total_available_minutes += 1

            # Handling work (either chat or email) at minute t?
            is_handling = not df_items[
                (df_items["User: Full Name"] == agent) &
                (df_items["Service Channel: Developer Name"].isin(["sfdc_liveagent", "casesChannel"])) &
                (df_items["Start DT"] <= t) &
                (df_items["End DT"] > t)
            ].empty

            if is_handling:
                total_handling_minutes += 1

    shift_utilization = total_handling_minutes / total_available_minutes if total_available_minutes > 0 else 0.0

    # -----------------------------------------------------
    # AHT & Volume
    # -----------------------------------------------------
    st.markdown("### Average Handling Time (AHT) & Volume")

    df_day_items = df_items[
        (df_items["User: Full Name"] == agent) &
        (df_items["Start DT"].dt.date == date)
    ].copy()

    df_day_items["Duration"] = (df_day_items["End DT"] - df_day_items["Start DT"]).dt.total_seconds()

    chat_items = df_day_items[df_day_items["Service Channel: Developer Name"] == "sfdc_liveagent"]
    email_items = df_day_items[df_day_items["Service Channel: Developer Name"] == "casesChannel"]

    aht_chat = chat_items["Duration"].mean() if not chat_items.empty else None
    aht_email = email_items["Duration"].mean() if not email_items.empty else None

    num_chat_items = len(chat_items)
    num_email_items = len(email_items)

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

    # Single Shift Utilization metric
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Shift Utilization</div>
            <div class="metric-value">{shift_utilization:.1%}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------------------------------
    # Shift Adherence (Scheduled vs Actual)
    # -----------------------------------------------------
    st.markdown("### Shift Adherence")
    col_sched, col_adh = st.columns(2)

    with col_sched:
        st.markdown("**Shift Scheduled (Assigned)**")
        st.markdown(f"""
            <div class="shift-box">
                {sched}
            </div>
        """, unsafe_allow_html=True)

    with col_adh:
        st.markdown("**Adherence Shift (Actual)**")
        sched_start, sched_end = parse_shift_range(sched, date)
        adh_start = parse_shift_start(sched_adherence, date)

        if sched_start and adh_start:
            delay = (adh_start - sched_start).total_seconds() / 60
            if delay >= 5:
                st.markdown(f"""
                    <div class="late-warning">
                        <strong>{sched_adherence}</strong><br>
                        <span>Starts {int(delay)} min late &#x26A0;</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="shift-box">
                        {sched_adherence}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="shift-box">
                    {sched_adherence}
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------------------------------
    # Daily Overview: Lunch + Total Shift Duration + Total Available Time (NEW)
    # -----------------------------------------------------
    st.markdown("### Daily Overview")
    col3, col4, col5 = st.columns(3)

    agent_daily_presence_filtered = df_presence[
        (df_presence['Created By: Full Name'] == agent) &
        (df_presence['Start DT'].dt.date == date)
    ].copy()

    # Lunch time detection (first Busy_Lunch start)
    lunch_time_entry = agent_daily_presence_filtered[
        agent_daily_presence_filtered['Service Presence Status: Developer Name'] == 'Busy_Lunch'
    ].sort_values(by='Start DT').iloc[0] if not agent_daily_presence_filtered[
        agent_daily_presence_filtered['Service Presence Status: Developer Name'] == 'Busy_Lunch'
    ].empty else None

    lunch_start_time = lunch_time_entry['Start DT'].strftime('%H:%M') if lunch_time_entry is not None else "N/A"

    # Total shift time (last end - first start)
    if not agent_daily_presence_filtered.empty:
        first_segment_start = agent_daily_presence_filtered['Start DT'].min()
        last_segment_end = agent_daily_presence_filtered['End DT'].max()
        total_shift_duration = last_segment_end - first_segment_start
        total_seconds = total_shift_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes_only = int((total_seconds % 3600) // 60)
        total_shift_display = f"{hours:02d}:{minutes_only:02d}"
    else:
        total_shift_display = "N/A"

    # NEW: Total Available Time (sum of all presence rows in any Available* status)
    available_statuses = {"Available_Chat", "Available_Email_and_Web", "Available_All"}
    avail_df = agent_daily_presence_filtered[
        agent_daily_presence_filtered['Service Presence Status: Developer Name'].isin(available_statuses)
    ].copy()

    if not avail_df.empty:
        available_seconds = (avail_df['End DT'] - avail_df['Start DT']).dt.total_seconds().sum()
        avail_hours = int(available_seconds // 3600)
        avail_minutes_only = int((available_seconds % 3600) // 60)
        total_available_display = f"{avail_hours:02d}:{avail_minutes_only:02d}"
    else:
        available_seconds = 0
        total_available_display = "00:00"

    # Threshold check for warning (7 hours 50 minutes = 28200 seconds)
    availability_warning = available_seconds < (7 * 3600 + 50 * 60)

    with col3:
        # Lunch timing validation: between 3h and 5h from actual shift start
        actual_shift_start = df_agent_day["Start DT"].min() if not df_agent_day.empty else None

        lunch_warning = False
        if lunch_time_entry is not None and actual_shift_start is not None:
            time_to_lunch = lunch_time_entry['Start DT'] - actual_shift_start
            if time_to_lunch.total_seconds() < 3 * 3600 or time_to_lunch.total_seconds() > 5 * 3600:
                lunch_warning = True

        lunch_box_class = "metric-container-warning" if lunch_warning else "metric-container"
        st.markdown(f"""
            <div class="{lunch_box_class}">
                <div class="metric-title">Lunch Time</div>
                <div class="metric-value">{lunch_start_time}</div>
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
        avail_box_class = "metric-container-warning" if availability_warning else "metric-container"
        st.markdown(f"""
            <div class="{avail_box_class}">
                <div class="metric-title">Total Available Time</div>
                <div class="metric-value">{total_available_display}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------------------------------
    # Lateness (30-Day Rolling)
    # -----------------------------------------------------
    st.markdown("### Lateness Statistics")
    total_minutes_late = 0
    window_days = [date - timedelta(days=i) for i in range(1, 31)]
    lateness_incidents = []

    for d in window_days:
        shift_col_d = d.strftime("%d/%m/%Y")
        sched_row_d = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()] if "Agent Name" in df_shifts.columns else pd.DataFrame()
        sched_val_d = sched_row_d[shift_col_d].values[0] if (not sched_row_d.empty and shift_col_d in df_shifts.columns) else None
        sched_shift_d = str(sched_val_d).strip() if pd.notna(sched_val_d) else None

        df_day_late_check = df_presence[
            (df_presence["Created By: Full Name"] == agent) &
            (df_presence["Start DT"].dt.date == d)
        ]

        if not df_day_late_check.empty and sched_shift_d:
            sched_start_d, _ = parse_shift_range(sched_shift_d, d)
            actual_start_time_d = df_day_late_check["Start DT"].min()
            if sched_start_d and actual_start_time_d:
                delay = (actual_start_time_d - sched_start_d).total_seconds() / 60
                if delay >= 5:
                    total_minutes_late += delay
                    lateness_incidents.append(f"- **{d.strftime('%d %b %Y')}**: {int(delay)} min late")

    if not lateness_incidents:
        st.image("no_late.png", caption="No Lateness Incidents Recorded", width=300)
    else:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">Total Lateness (30-Day Rolling)</div>
                <div class="metric-value">
                    {int(total_minutes_late)} min late
                    {'<span style=\"color:red; font-size: 0.7em;\"> &#x26A0;</span>' if total_minutes_late > 0 else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Incidents of Lateness (Last 30 Days)")
        for incident in lateness_incidents:
            st.markdown(incident)
