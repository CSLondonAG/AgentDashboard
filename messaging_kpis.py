"""Agent-attributed Enhanced Messaging KPI calculations."""

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


@dataclass(frozen=True)
class AgentMessagingSnapshot:
    sessions_handled: int = 0
    aht_seconds: Optional[float] = None
    total_handle_seconds: float = 0.0
    transfer_involvement: int = 0
    median_speed_to_answer_seconds: Optional[float] = None
    first_response_within_60_pct: Optional[float] = None
    median_first_response_seconds: Optional[float] = None
    measurable_responses: int = 0
    daily: pd.DataFrame = field(default_factory=pd.DataFrame)
    review_sessions: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass(frozen=True)
class MessagingCard:
    label: str
    value: str
    detail: str


@dataclass(frozen=True)
class MessagingSummaryTile:
    primary_label: str
    primary_value: str
    secondary_label: str
    secondary_value: str


def _format_mmss(seconds: Optional[float]) -> str:
    if seconds is None or pd.isna(seconds):
        return "–"
    total = max(0, int(round(float(seconds))))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def _format_hhmmss(seconds: float) -> str:
    total = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _finite_numeric(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.where(
        numeric.map(lambda value: pd.isna(value) or math.isfinite(float(value)))
    )


def load_messaging_exports(
    agent_work_path: object,
    metrics_path: object,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load optional Messaging exports independently and tolerate bad files."""

    def load_optional(path: object) -> pd.DataFrame:
        try:
            return pd.read_csv(path)
        except (FileNotFoundError, EmptyDataError, ParserError, UnicodeDecodeError):
            return pd.DataFrame()

    return load_optional(agent_work_path), load_optional(metrics_path)


def build_agent_messaging_summary_tile(
    snapshot: AgentMessagingSnapshot,
) -> MessagingSummaryTile:
    """Build the Messaging tile shown in the AHT and volume summary."""
    return MessagingSummaryTile(
        primary_label="Messaging AHT (mm:ss)",
        primary_value=_format_mmss(snapshot.aht_seconds),
        secondary_label="Sessions Handled",
        secondary_value=f"{snapshot.sessions_handled:,}",
    )


def build_agent_messaging_cards(
    snapshot: AgentMessagingSnapshot,
) -> tuple[MessagingCard, ...]:
    """Build the user-visible card values for an agent snapshot."""
    response_pct = (
        "–"
        if snapshot.first_response_within_60_pct is None
        else f"{snapshot.first_response_within_60_pct:.1f}%"
    )
    return (
        MessagingCard("Sessions Handled", f"{snapshot.sessions_handled:,}", "Unique accepted sessions"),
        MessagingCard("Messaging AHT", _format_mmss(snapshot.aht_seconds), "Mean agent handle time per session"),
        MessagingCard("Total Handling Time", _format_hhmmss(snapshot.total_handle_seconds), "Selected agent only"),
        MessagingCard("Transfer Involvement", f"{snapshot.transfer_involvement:,}", "Sessions involving another human agent"),
        MessagingCard("Median Speed to Answer", _format_mmss(snapshot.median_speed_to_answer_seconds), "Routing to acceptance"),
        MessagingCard("First Response <=60s", response_pct, "First-agent sessions only"),
        MessagingCard("Median First Response", _format_mmss(snapshot.median_first_response_seconds), "First-agent sessions only"),
        MessagingCard("Measurable Responses", f"{snapshot.measurable_responses:,}", "Response KPI denominator"),
    )


def format_messaging_review_sessions(review_sessions: pd.DataFrame) -> pd.DataFrame:
    """Return review rows with user-facing dates and durations."""
    source_columns = [
        "Accepted At",
        "Messaging Session",
        "Handle Time (s)",
        "Speed To Answer (s)",
        "First Response (s)",
        "Review Reason",
    ]
    display_columns = [
        "Accepted At",
        "Messaging Session",
        "Handle Time",
        "Speed To Answer",
        "First Response",
        "Review Reason",
    ]
    if review_sessions is None or review_sessions.empty or not set(source_columns).issubset(
        review_sessions.columns
    ):
        return pd.DataFrame(columns=display_columns)

    display = review_sessions[source_columns].copy()
    accepted_at = pd.to_datetime(display["Accepted At"], errors="coerce")
    display["Accepted At"] = accepted_at.apply(
        lambda value: value.strftime("%d %b %Y %H:%M") if pd.notna(value) else "–"
    )
    duration_columns = {
        "Handle Time (s)": "Handle Time",
        "Speed To Answer (s)": "Speed To Answer",
        "First Response (s)": "First Response",
    }
    for source, target in duration_columns.items():
        display[target] = pd.to_numeric(display[source], errors="coerce").apply(_format_mmss)
    return display.drop(columns=duration_columns).loc[:, display_columns]


def _empty_snapshot() -> AgentMessagingSnapshot:
    return AgentMessagingSnapshot()


def calculate_agent_messaging_snapshot(
    agent_work: pd.DataFrame,
    metrics_long: pd.DataFrame,
    agent: str,
    start_date: date,
    end_date: date,
) -> AgentMessagingSnapshot:
    """Return Messaging KPIs that can be attributed to one agent."""
    required_work = {
        "User: Full Name",
        "Accept Date",
        "Handle Time",
        "Speed To Answer",
        "Messaging Session Name",
    }
    if agent_work is None or agent_work.empty or not required_work.issubset(agent_work.columns):
        return _empty_snapshot()

    work = agent_work.copy()
    work["User: Full Name"] = work["User: Full Name"].astype("string").str.strip()
    work["_Agent Key"] = work["User: Full Name"].str.casefold()
    work["Messaging Session Name"] = work["Messaging Session Name"].astype(str).str.strip()
    work["Accept Date"] = pd.to_datetime(
        work["Accept Date"], format="mixed", dayfirst=True, errors="coerce"
    )
    work["Handle Time"] = _finite_numeric(work["Handle Time"])
    work["Speed To Answer"] = _finite_numeric(work["Speed To Answer"])

    human = work[
        work["Accept Date"].notna()
        & work["Messaging Session Name"].ne("")
        & work["_Agent Key"].notna()
        & work["_Agent Key"].ne("")
        & work["_Agent Key"].ne("automated process")
    ].copy()
    if human.empty:
        return _empty_snapshot()

    selected_key = str(agent).strip().casefold()
    selected = human[human["_Agent Key"] == selected_key].copy()
    if selected.empty:
        return _empty_snapshot()

    per_session = (
        selected.groupby("Messaging Session Name", as_index=False)
        .agg(
            Agent_Accept=("Accept Date", "min"),
            Agent_Handle_Secs=("Handle Time", lambda values: values.sum(min_count=1)),
        )
    )
    per_session = per_session[
        per_session["Agent_Accept"].dt.date.between(start_date, end_date)
    ].copy()
    if per_session.empty:
        return _empty_snapshot()

    included_sessions = set(per_session["Messaging Session Name"])
    selected_in_period = selected[selected["Messaging Session Name"].isin(included_sessions)]
    speed_values = selected_in_period["Speed To Answer"].dropna()
    speed_by_session = selected_in_period.groupby("Messaging Session Name")[
        "Speed To Answer"
    ].median()

    human_counts = human.groupby("Messaging Session Name")["_Agent Key"].nunique()
    per_session["Transferred"] = per_session["Messaging Session Name"].map(human_counts).fillna(0) > 1

    first_accept = human.groupby("Messaging Session Name")["Accept Date"].transform("min")
    first_rows = human[human["Accept Date"] == first_accept]
    first_agent_counts = first_rows.groupby("Messaging Session Name")["_Agent Key"].nunique()
    unique_first = first_rows[
        first_rows["Messaging Session Name"].map(first_agent_counts).eq(1)
    ].drop_duplicates("Messaging Session Name")
    owner_by_session = unique_first.set_index("Messaging Session Name")["_Agent Key"]

    response_by_session = pd.Series(dtype="float64")
    required_metrics = {
        "Messaging Session Name",
        "Messaging Session Metric Type",
        "Messaging Session Metric Value",
    }
    if metrics_long is not None and not metrics_long.empty and required_metrics.issubset(metrics_long.columns):
        metrics = metrics_long.copy()
        metrics["Messaging Session Name"] = metrics["Messaging Session Name"].astype(str).str.strip()
        metrics["Messaging Session Metric Value"] = _finite_numeric(
            metrics["Messaging Session Metric Value"]
        )
        first_response = metrics[
            metrics["Messaging Session Metric Type"].astype(str).str.strip()
            == "Service Rep First Response Time"
        ].drop_duplicates("Messaging Session Name")
        eligible_sessions = {
            session
            for session in included_sessions
            if session in owner_by_session.index
            and owner_by_session.loc[session] == selected_key
        }
        eligible_first_response = first_response.loc[
            first_response["Messaging Session Name"].isin(eligible_sessions),
            ["Messaging Session Name", "Messaging Session Metric Value"],
        ]
        eligible_first_response = eligible_first_response[
            eligible_first_response["Messaging Session Metric Value"] > 0
        ]
        response_by_session = eligible_first_response.set_index("Messaging Session Name")[
            "Messaging Session Metric Value"
        ]

    handle_values = per_session["Agent_Handle_Secs"].dropna()
    response_values = response_by_session
    measurable = int(len(response_values))
    review_rows = []
    for row in per_session.itertuples(index=False):
        session_name = row[0]
        accepted_at = row[1]
        handle_seconds = row[2]
        transferred = bool(row[3])
        speed_seconds = speed_by_session.get(session_name)
        first_response_seconds = response_by_session.get(session_name)
        reasons = []
        if pd.notna(first_response_seconds) and first_response_seconds > 60:
            reasons.append("First response >60s")
        if pd.notna(speed_seconds) and speed_seconds > 60:
            reasons.append("Speed to answer >60s")
        if pd.notna(handle_seconds) and handle_seconds >= 15 * 60:
            reasons.append("Handling time ≥15m")
        if transferred:
            reasons.append("Transfer involvement")
        if reasons:
            review_rows.append(
                {
                    "Accepted At": accepted_at,
                    "Messaging Session": session_name,
                    "Handle Time (s)": handle_seconds,
                    "Speed To Answer (s)": speed_seconds,
                    "First Response (s)": first_response_seconds,
                    "Review Reason": "; ".join(reasons),
                }
            )
    review_sessions = pd.DataFrame(
        review_rows,
        columns=[
            "Accepted At",
            "Messaging Session",
            "Handle Time (s)",
            "Speed To Answer (s)",
            "First Response (s)",
            "Review Reason",
        ],
    ).sort_values("Accepted At").reset_index(drop=True)

    daily_rows = []
    for day, day_sessions in per_session.groupby(per_session["Agent_Accept"].dt.date):
        session_names = set(day_sessions["Messaging Session Name"])
        day_handle = day_sessions["Agent_Handle_Secs"].dropna()
        day_speed = selected_in_period.loc[
            selected_in_period["Messaging Session Name"].isin(session_names),
            "Speed To Answer",
        ].dropna()
        day_response = response_by_session[response_by_session.index.isin(session_names)]
        daily_rows.append(
            {
                "Date": day,
                "Sessions Handled": int(len(day_sessions)),
                "Messaging AHT (s)": float(day_handle.mean()) if len(day_handle) else None,
                "Total Handle (s)": float(day_handle.sum()) if len(day_handle) else 0.0,
                "Transfer Involvement": int(day_sessions["Transferred"].sum()),
                "Median Speed to Answer (s)": (
                    float(day_speed.median()) if len(day_speed) else None
                ),
                "First Response <=60s (%)": (
                    float((day_response <= 60).mean() * 100) if len(day_response) else None
                ),
                "Median First Response (s)": (
                    float(day_response.median()) if len(day_response) else None
                ),
                "Measurable Responses": int(len(day_response)),
            }
        )
    daily = pd.DataFrame(daily_rows).sort_values("Date").reset_index(drop=True)

    return AgentMessagingSnapshot(
        sessions_handled=int(len(per_session)),
        aht_seconds=float(handle_values.mean()) if len(handle_values) else None,
        total_handle_seconds=float(handle_values.sum()) if len(handle_values) else 0.0,
        transfer_involvement=int(per_session["Transferred"].sum()),
        median_speed_to_answer_seconds=(
            float(speed_values.median()) if len(speed_values) else None
        ),
        first_response_within_60_pct=(
            float((response_values <= 60).mean() * 100) if measurable else None
        ),
        median_first_response_seconds=(
            float(response_values.median()) if measurable else None
        ),
        measurable_responses=measurable,
        daily=daily,
        review_sessions=review_sessions,
    )
