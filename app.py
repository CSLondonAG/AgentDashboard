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

    /* NEW: Container for the custom main header (h1 + inline logo) */
    /* This will apply to both the "No Shift" case and the dashboard case */
    .custom-main-header-container {
        display: flex; /* Use flexbox for inline elements */
        align-items: center; /* Vertically align items in the middle */
        justify-content: flex-start; /* Align to the left */
        margin-top: -35px; /* Pull header up slightly to reduce overall top space - Adjusted from -20px */
        margin-bottom: 0.1rem; /* Reduce space below the main header */
        padding: 0; /* Remove any default padding */
    }

    /* NEW: Styling for the h1 within the custom main header */
    /* This will affect st.markdown with h1 tag */
    .custom-main-header-container h1 {
        font-size: 1.5rem !important; /* Main title font size */
        margin: 0 !important; /* Remove all margins from h1 inside custom header */
        padding: 0 !important; /* Remove all paddings from h1 inside custom header */
        line-height: 1.2 !important; /* Adjust line height for compactness */
        display: inline; /* Ensure it behaves like an inline element within flex */
    }

    /* NEW: Styling for the inline logo within the header */
    .header-logo-inline {
        width: 40px; /* Smaller logo for inline display */
        height: auto;
        margin-left: 10px; /* Space between text and logo */
        vertical-align: middle; /* Align logo with text baseline */
        margin-top: -5px; /* Fine-tune vertical alignment of logo if needed */
    }

    /* NEW/MODIFIED: Styling for the h2 (subheader for Date) */
    /* This will affect st.subheader() */
    h2 {
        font-size: 0.75rem !important; /* Significantly smaller font for the subheader (50% of h1's 1.5rem) */
        margin-top: 0 !important; /* Remove top margin */
        margin-bottom: 0.5rem !important; /* Reduced bottom margin */
        padding-bottom: 0 !important; /* Remove bottom padding */
        line-height: 1.2 !important; /* Adjust line height for compactness */
    }

    /* NEW: CSS for the smaller subheader (date line) */
    .subheader-smaller {
        font-size: 0.75rem !important;
        font-weight: 500;
        color: #444;
        margin-bottom: 0.1rem; /* Adjusted from 0.5rem */
    }

    /* NEW: Styling for h3 (Dashboard section titles) */
    h3 {
        font-size: 1.5rem !important; /* Matches main header font size */
        margin-top: 0.5rem !important; /* Adjusted from 1rem */
        margin-bottom: 0.8rem !important; /* Adjust bottom margin as needed */
        color: #333333; /* Darker color for prominence */
    }

    /* Keep existing metric styles */
    .st-emotion-cache-1r6dm7m { /* Target for metric value */
        font-size: 1.5em;
        font-weight: bold;
    }
    .st-emotion-cache-16idsysf p { /* Target for metric label */
        font-size: 0.2em;
        color: #555555;
    }
    .metric-container {
        padding: 8px; /* Reduced from 15px */
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
        font-size: 1.8em; /* Reduced from 2.2em */
        font-weight: bold;
        color: #007bff;
    }
    /* Specific styles for Adherence Shift display */
    .late-warning {
        background-color: #ffebeb; /* Lighter red for warning */
        border: 1px solid #ff4d4d; /* Red border */
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        color: #cc0000;
        margin-top: 10px;
    }
    .info-box {
        background-color: #e6f7ff; /* Light blue for info */
        border: 1px solid #91d5ff;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
    }

    /* Styles specifically to mimic the provided image's light blue boxes for shifts */
    .shift-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #e6f7ff; /* Light blue background */
        border: 1px solid #91d5ff;
        font-size: 1.5em;
        font-weight: bold;
        color: #007bff;
        text-align: center;
    }

    /* NEW: For warning metrics that need centering and specific font sizes */
    .metric-container-warning {
        padding: 8px; /* Matches metric-container padding */
        border-radius: 10px; /* Matches metric-container border-radius */
        background-color: #ffebeb; /* Lighter red background */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Matches metric-container box-shadow */
        margin-bottom: 20px; /* Matches metric-container margin-bottom */
        text-align: center; /* Center the text */
        border: 1px solid #ff4d4d; /* Red border */
    }
    /* Ensure metric-title and metric-value styles apply to the new warning container */
    .metric-container-warning .metric-title {
        font-size: 1.1em; /* Matches metric-container .metric-title font-size */
        color: #333333; /* Keep text color for title consistent */
        margin-bottom: 5px; /* Matches metric-container .metric-title margin-bottom */
    }
    .metric-container-warning .metric-value {
        font-size: 1.8em; /* Matches metric-container .metric-value font-size */
        font-weight: bold;
        color: #ff4d4d; /* Red color for the value */
    }

    </style>
""", unsafe_allow_html=True)

# @st.cache_data  # DISABLED to ensure fresh data is loaded each time
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
st.sidebar.header("Select Agent and Date")
agent = st.sidebar.selectbox("Agent Name", agents)

raw_dates = sorted(
    df_presence["Start DT"].dt.date.unique()
)
dates = sorted([pd.to_datetime(d).date() for d in raw_dates])

dates = sorted(raw_dates)
date = st.sidebar.date_input("Date", min_value=min(dates), max_value=max(dates), value=max(dates))

def parse_time(val):
    if pd.isna(val): return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except:
            continue
    return None

def parse_td(val):
    if pd.isna(val): return None
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

# --- Common header section (Agent Dashboard Title and Date) - Always displayed at the top ---
st.markdown(f"""
    <div class="custom-main-header-container">
        <h1>Agent Dashboard for {agent}</h1>
        <div class="header-logo-inline">{svg_code}</div>
    </div>
""", unsafe_allow_html=True)
st.markdown(
    f"""<div class='subheader-smaller'>Date: {date.strftime('%d %B %Y')}</div>""",
    unsafe_allow_html=True
)
st.markdown("---") # Visual separator

# --- Determine the scheduled shift (sched) and adherence data presence early ---
shift_col = date.strftime("%d/%m/%Y")
sched_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()]
sched_val = sched_row[shift_col].values[0] if shift_col in df_shifts.columns and not sched_row.empty else None
sched = str(sched_val).strip() if pd.notna(sched_val) else "Not Assigned"

start_dt = datetime.combine(date, dtime(0, 0))
end_dt = datetime.combine(date, dtime(23, 59))
df_agent_day = df_presence[
    (df_presence["Created By: Full Name"] == agent) &
    (df_presence["Start DT"] >= start_dt) &
    (df_presence["Start DT"] <= end_dt)
]
adherence_data_available = not df_agent_day.empty

# --- Conditional display logic based on shift schedule and adherence data ---
if sched == "Not Assigned":
    # Case 1: No shift scheduled for the agent
    st.image("day_off.png", caption="No Shift Scheduled for this Day", width=300)
    st.info("You were not scheduled to work on this day")

elif not adherence_data_available:
    # Case 2: Shift scheduled, but no adherence data available (agent absent)
    st.image("absent.png", caption="You were Absent from your scheduled shift on this day", width=300)

else:
    # Case 3: Shift scheduled and adherence data is available - display full dashboard
    earliest = df_agent_day["Start DT"].min()
    latest = df_agent_day["End DT"].max()
    sched_adherence = f"{earliest.strftime('%I:%M %p')} – {latest.strftime('%I:%M %p')}"

    # >>> BEGIN FIXED LOGIC REGION (keep visuals unchanged) <<<
    minutes = pd.date_range(start=start_dt, end=end_dt, freq="min", inclusive="left")
    num_avail_chat = num_handled_chat = 0
    num_avail_email = num_handled_email = 0

    for t in minutes:
        # Filter for presence within the current minute
        pres_at_t = df_presence[
            (df_presence["Created By: Full Name"] == agent) &
            (df_presence["Start DT"] <= t) &
            (df_presence["End DT"] > t)
        ]
        status = pres_at_t.iloc[0]["Service Presence Status: Developer Name"] if not pres_at_t.empty else None

        # CHAT: Only count availability when actually handling a chat item at this minute
        if status in ("Available_Chat", "Available_All"):
            its = df_items[
                (df_items["User: Full Name"] == agent) &
                (df_items["Service Channel: Developer Name"] == "sfdc_liveagent") &
                (df_items["Start DT"] <= t) &
                (df_items["End DT"] > t)
            ]
            if not its.empty:
                num_avail_chat += 1
                num_handled_chat += 1

        # EMAIL: Only count availability when actually handling an email item at this minute
        if status in ("Available_Email_and_Web", "Available_All"):
            its_e = df_items[
                (df_items["User: Full Name"] == agent) &
                (df_items["Service Channel: Developer Name"] == "casesChannel") &
                (df_items["Start DT"] <= t) &
                (df_items["End DT"] > t)
            ]
            if not its_e.empty:
                num_avail_email += 1
                num_handled_email += 1

    chat_util = num_handled_chat / num_avail_chat if num_avail_chat > 0 else 0
    email_util = num_handled_email / num_avail_email if num_avail_email > 0 else None
    # >>> END FIXED LOGIC REGION <<<

    # Average Handling Time (AHT) & Volume section (moved to top)
    st.markdown("### Average Handling Time (AHT) & Volume") # No line break above this as requested

    df_day_items = df_items[
        (df_items["User: Full Name"] == agent) &
        (df_items["Start DT"].dt.date == date)
    ].copy()

    df_day_items["Duration"] = (df_day_items["End DT"] - df_day_items["Start DT"]).dt.total_seconds()

    chat_items = df_day_items[df_day_items["Service Channel: Developer Name"] == "sfdc_liveagent"]
    email_items = df_day_items[df_day_items["Service Channel: Developer Name"] == "casesChannel"]

    aht_chat = chat_items["Duration"].mean() if not chat_items.empty else None # Changed to seconds
    aht_email = email_items["Duration"].mean() if not email_items.empty else None # Changed to seconds

    num_chat_items = len(chat_items)
    num_email_items = len(email_items)

    col_aht1, col_aht2 = st.columns(2)
    with col_aht1:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Chat (mm:ss)</div>
                <div class="metric-value">{format_seconds_to_mm_ss(aht_chat) if aht_chat is not None else "Not Assigned"}</div>
                <div class="metric-title"># Chat Items</div>
                <div class="metric-value">{"Not Assigned" if num_chat_items == 0 else num_chat_items}</div>
                <div class="metric-title">Chat Utilization</div>
                <div class="metric-value">{chat_util:.1%}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_aht2:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">AHT Email (mm:ss)</div>
                <div class="metric-value">{format_seconds_to_mm_ss(aht_email) if aht_email is not None else "Not Assigned"}</div>
                <div class="metric-title"># Email Items</div>
                <div class="metric-value">{"Not Assigned" if num_email_items == 0 else num_email_items}</div>
                <div class="metric-title">Email Utilization</div>
                <div class="metric-value">{(email_util is not None and f"{email_util:.1%}" or "Not Assigned")}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---") # Visual separator (This one remains as it's between sections)

    # Shift and Adherence
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
                # If late, use the warning style
                st.markdown(f"""
                    <div class="late-warning">
                        <strong>{sched_adherence}</strong><br>
                        <span>Starts {int(delay)} min late &#x26A0;</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # If not late, use the shift-box style to match the image
                st.markdown(f"""
                    <div class="shift-box">
                        {sched_adherence}
                    </div>
                """, unsafe_allow_html=True)
        else:
            # This branch should ideally be caught by 'elif not adherence_data_available' above
            # but is kept as a fallback for robustness.
            st.markdown(f"""
                <div class="shift-box">
                    {sched_adherence}
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---") # Visual separator

    # Lunch and Total Shift Time (Daily Overview)
    st.markdown("### Daily Overview")
    col3, col4 = st.columns(2)

    # Calculate Lunch Time
    # We’ll derive this as the start time of the first Break_Lunch status entry for the selected agent on the selected date.
    # Filter presence data for the selected agent and date again for clarity within this block
    agent_daily_presence_filtered = df_presence[
        (df_presence['Created By: Full Name'] == agent) &
        (df_presence['Start DT'].dt.date == date)
    ].copy()

    lunch_time_entry = agent_daily_presence_filtered[
        agent_daily_presence_filtered['Service Presence Status: Developer Name'] == 'Busy_Lunch'
    ].sort_values(by='Start DT').iloc[0] if not agent_daily_presence_filtered[
        agent_daily_presence_filtered['Service Presence Status: Developer Name'] == 'Busy_Lunch'
    ].empty else None

    lunch_start_time = lunch_time_entry['Start DT'].strftime('%H:%M') if lunch_time_entry is not None else "N/A"

    # Calculate Total Shift Time
    # (End of last presence segment) – (Start of first presence segment)
    # For the selected agent and date.
    if not agent_daily_presence_filtered.empty:
        first_segment_start = agent_daily_presence_filtered['Start DT'].min()
        last_segment_end = agent_daily_presence_filtered['End DT'].max()
        total_shift_duration = last_segment_end - first_segment_start

        # Convert total_shift_duration to hh:mm format
        total_seconds = total_shift_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        total_shift_display = f"{hours:02d}:{minutes:02d}"
    else:
        total_shift_display = "N/A"

    with col3:
        # Calculate actual shift start for lunch time adherence
        actual_shift_start = df_agent_day["Start DT"].min() if not df_agent_day.empty else None

        lunch_warning = False
        if lunch_time_entry is not None and actual_shift_start is not None:
            time_to_lunch = lunch_time_entry['Start DT'] - actual_shift_start
            # Check if lunch is less than 3 hours (10800 seconds) or more than 5 hours (18000 seconds) from shift start
            if time_to_lunch.total_seconds() < 3 * 3600 or time_to_lunch.total_seconds() > 5 * 3600:
                lunch_warning = True

        # Use the new class for warnings in metric containers
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

    st.markdown("---") # Visual separator

    # Rolling 30-Day Lateness (Lateness Statistics)
    st.markdown("### Lateness Statistics")
    total_minutes_late = 0
    window_days = [date - timedelta(days=i) for i in range(1, 31)]

    # Collect incidents of lateness
    lateness_incidents = []

    for d in window_days:
        day_str = d.strftime("%d/%m/%Y")
        shift_col = day_str
        sched_row = df_shifts[df_shifts["Agent Name"].str.lower() == agent.lower()]
        sched_val = sched_row[shift_col].values[0] if shift_col in df_shifts.columns and not sched_row.empty else None
        sched_shift = str(sched_val).strip() if pd.notna(sched_val) else None

        df_day_late_check = df_presence[
            (df_presence["Created By: Full Name"] == agent) &
            (df_presence["Start DT"].dt.date == d)
        ]

        if not df_day_late_check.empty and sched_shift:
            sched_start, _ = parse_shift_range(sched_shift, d)
            actual_start_time = df_day_late_check["Start DT"].min()
            if sched_start and actual_start_time:
                delay = (actual_start_time - sched_start).total_seconds() / 60
                if delay >= 5:
                    total_minutes_late += delay
                    lateness_incidents.append(f"- **{d.strftime('%d %b %Y')}**: {int(delay)} min late")

    # Conditional display based on whether any lateness incidents were found
    if not lateness_incidents:
        st.image("no_late.png", caption="No Lateness Incidents Recorded", width=300)
    else:
        # Display the overall total lateness metric
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">Total Lateness (30-Day Rolling)</div>
                <div class="metric-value">
                    {int(total_minutes_late)} min late
                    {'<span style="color:red; font-size: 0.7em;"> &#x26A0;</span>' if total_minutes_late > 0 else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---") # Visual separator

        # Display each lateness instance contributing to the total
        st.markdown("#### Incidents of Lateness (Last 30 Days)")
        for incident in lateness_incidents:
            st.markdown(incident)
