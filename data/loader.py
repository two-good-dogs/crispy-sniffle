"""
loader.py — Data adapter layer.

Tries to load live data from the database via data_interface.py.
Falls back to mock_data.py when the DB is unreachable or env vars are absent.
All returned DataFrames conform to the app's internal schema regardless of source.
"""

import os

import pandas as pd

from data.mock_data import (
    get_audits as _mock_audits,
    get_issues as _mock_issues,
    get_adjustments as _mock_adjustments,
    get_seed_messages,
    CURRENT_USER,
)

try:
    from data import data_interface as _di
    _DI_OK = True
except Exception:
    _DI_OK = False

# ── Column-mapping constants ──────────────────────────────────────────────────

_AUDIT_TYPE_MAP = {
    "Audit":                        "Owned Audit",
    "Regulatory Issue Validation":  "In-Scope AE",
}

_STATUS_MAP = {
    "Planning":   "In Progress",
    "Fieldwork":  "Fieldwork",
    "Reporting":  "In Progress",
    "Issued":     "Complete",
    "Completed":  "Complete",
    "Complete":   "Complete",
    "Cancelled":  "Complete",
}

_RATING_MAP = {
    "High":               "High",
    "Medium":             "Medium",
    "Low":                "Low",
    "Not Rated":          "N/A",
    "Satisfactory":       "Low",
    "Needs Improvement":  "Medium",
    "Unsatisfactory":     "High",
}

_SEVERITY_MAP = {
    "Level 1": "High",   "1": "High",
    "Level 2": "Medium", "2": "Medium",
    "Level 3": "Low",    "3": "Low",
}


# ── Normalisers ───────────────────────────────────────────────────────────────

def _normalise_audits(eng: pd.DataFrame) -> pd.DataFrame:
    """Map the DB `eng` DataFrame to the app's audits schema."""
    df = eng.copy()

    df = df.rename(columns={
        "engagement_id":       "audit_id",
        "title":               "audit_name",
        "audit_group":         "lead_group",
        "quarter":             "quarter",
        "region":              "region",
        "impacted_audit_group": "impacted_platform",
        "_issue_count":        "issue_count",
    })

    # audit_type is computed dynamically in app.py based on the platform filter
    df["audit_type"] = ""

    df["status"] = (
        df.get("status", pd.Series(dtype=str))
        .map(_STATUS_MAP)
        .fillna("In Progress")
    )

    df["rating"] = (
        df.get("current_rating", pd.Series(dtype=str))
        .map(_RATING_MAP)
        .fillna("N/A")
    )

    df["is_overdue"]  = df.get("at_risk", pd.Series(dtype=str)).fillna("No").str.upper() == "YES"
    df["out_of_scope"] = False

    df["impacted_platform"] = df.get("impacted_platform", pd.Series(dtype=str)).fillna("")
    df["issue_count"]       = df.get("issue_count", pd.Series(dtype=int)).fillna(0).astype(int)

    # Fields not in DB schema — default to N/A
    df["digital_rcm"]    = "N/A"
    df["planning_memo"]  = "N/A"

    # Keep only the columns the app expects
    keep = [
        "audit_id", "audit_name", "audit_type", "lead_group", "region",
        "status", "rating", "issue_count", "digital_rcm", "planning_memo",
        "impacted_platform", "is_overdue", "out_of_scope", "quarter",
    ]
    return df[[c for c in keep if c in df.columns]]


def _normalise_issues(iss: pd.DataFrame, eng_id_col: str = "audit_id") -> pd.DataFrame:
    """Map the DB `iss` DataFrame to the app's issues schema."""
    df = iss.copy()

    # Issue ID
    if "issue_id" not in df.columns:
        df["issue_id"] = [f"ISS-{i+1:03d}" for i in range(len(df))]

    # audit_id link
    if eng_id_col != "audit_id" and eng_id_col in df.columns:
        df = df.rename(columns={eng_id_col: "audit_id"})

    # Severity
    if "issue_level" in df.columns:
        df["severity"] = df["issue_level"].astype(str).map(_SEVERITY_MAP).fillna("Medium")
    else:
        df["severity"] = "Medium"

    # Status and overdue (vectorised)
    past_due    = df.get("past_due",    pd.Series(0, index=df.index)).fillna(0).astype(int)
    in_progress = df.get("in_progress", pd.Series(0, index=df.index)).fillna(0).astype(int)
    df["status"] = "Closed"
    df.loc[in_progress == 1, "status"] = "Open"
    df.loc[past_due == 1,    "status"] = "Overdue"

    days_past_due = df.get("days_past_due", pd.Series(0, index=df.index)).fillna(0).astype(int)
    df["days_overdue"] = days_past_due.where(past_due == 1, other=0)

    # Title
    for candidate in ("issue_title", "title", "description"):
        if candidate in df.columns:
            df["title"] = df[candidate]
            break
    if "title" not in df.columns:
        df["title"] = "Untitled Issue"

    # Owner
    if "remediation_owner" not in df.columns:
        for candidate in ("owner", "assigned_to", "responsible_party"):
            if candidate in df.columns:
                df["remediation_owner"] = df[candidate]
                break
        else:
            df["remediation_owner"] = "Unknown"

    # Due date
    if "due_date" not in df.columns:
        for candidate in ("target_date", "remediation_date", "actual_end"):
            if candidate in df.columns:
                df["due_date"] = pd.to_datetime(df[candidate], errors="coerce")
                break
        else:
            df["due_date"] = pd.NaT

    df["due_date"] = pd.to_datetime(df.get("due_date"), errors="coerce")

    keep = ["issue_id", "audit_id", "title", "severity", "status",
            "due_date", "remediation_owner", "days_overdue"]
    return df[[c for c in keep if c in df.columns]]


def _normalise_messages(db_df: pd.DataFrame) -> list:
    """Convert DB messages DataFrame to the app's list-of-dicts format."""
    messages = []
    for i, row in db_df.iterrows():
        messages.append({
            "msg_id":        str(row.get("message_id", row.get("msg_id", f"MSG-{i+1:03d}"))),
            "from_user":     str(row.get("usr_from",   row.get("from_user", ""))),
            "to_user":       str(row.get("usr_to",     row.get("to_user", ""))),
            "subject_type":  str(row.get("subject_type", "project")),
            "subject_id":    str(row.get("subject_id", "")),
            "subject_label": str(row.get("subject_lbl", row.get("subject_label", ""))),
            "message":       str(row.get("msg",         row.get("message", ""))),
            "sent_at":       str(row.get("sent_at",     row.get("created_at", ""))),
            "read":          bool(row.get("is_read",    row.get("read", True))),
        })
    return messages


# ── Public interface ──────────────────────────────────────────────────────────

def get_connection_status() -> dict:
    """
    Returns a dict describing the current data source.
    ``{"live": True, "env": "PROD", "db": "DBS00_SOI_PROD"}``
    or
    ``{"live": False, "reason": "..."}``
    """
    if not _DI_OK:
        return {"live": False, "reason": "data_interface module unavailable"}
    try:
        if _di.is_available():
            return {"live": True, "env": _di.env, "db": _di.sql_db}
        return {"live": False, "reason": "DB drivers / env vars not configured"}
    except Exception as exc:
        return {"live": False, "reason": str(exc)}


def get_audits() -> pd.DataFrame:
    """Return audits DataFrame — live DB if available, mock otherwise."""
    try:
        if not _DI_OK or not _di.is_available():
            raise RuntimeError("not available")
        yr = os.getenv("REPORT_YEAR", "2025")
        eng, _rcm, _iss = _di.load_data(yr)
        return _normalise_audits(eng)
    except Exception:
        return _mock_audits()


def get_issues() -> pd.DataFrame:
    """Return issues DataFrame — live DB if available, mock otherwise."""
    try:
        if not _DI_OK or not _di.is_available():
            raise RuntimeError("not available")
        yr = os.getenv("REPORT_YEAR", "2025")
        _eng, _rcm, iss = _di.load_data(yr)
        return _normalise_issues(iss)
    except Exception:
        return _mock_issues()


def get_adjustments() -> list:
    """Return adjustments — live DB if available, mock otherwise."""
    try:
        if not _DI_OK or not _di.is_available():
            raise RuntimeError("not available")
        yr = os.getenv("REPORT_YEAR", "2025")
        with _di._engine().begin() as conn:
            df = pd.read_sql(
                f"[PUB].[usp_ACR_QE_PROJECT_CHANGE_LOG] {yr}", conn
            )
        # Map to app adj schema
        records = []
        for _, row in df.iterrows():
            records.append({
                "adj_id":               str(row.get("change_id", row.get("adj_id", ""))),
                "adj_type":             str(row.get("change_type", "Type 1 – Tag Correction")),
                "field_being_adjusted": str(row.get("field_name", "")),
                "from_value":           str(row.get("old_value", "—")),
                "to_value":             str(row.get("new_value", "—")),
                "reason_code":          str(row.get("reason_code", "")),
                "supporting_note":      str(row.get("notes", "")),
                "evidence_ref":         str(row.get("evidence_ref", "")),
                "submitted_by":         str(row.get("submitted_by", "")),
                "submitted_date":       str(row.get("submitted_date", "")),
                "status":               str(row.get("status", "Pending")),
            })
        return records
    except Exception:
        return _mock_adjustments()


def get_messages_for_user(usr: str) -> list:
    """
    Return messages for the given user.
    Tries the DB first; if unavailable returns the seeded mock messages.
    """
    try:
        if not _DI_OK or not _di.is_available():
            raise RuntimeError("not available")
        return _normalise_messages(_di.get_messages(usr))
    except Exception:
        return get_seed_messages()


def send_message(usr_to: str, usr_from: str, subject_lbl: str, msg: str) -> bool:
    """
    Persist a message to SQL Server.
    Returns True if written, False if DB unavailable or write failed.
    """
    try:
        if not _DI_OK or not _di.is_available():
            return False
        _di.set_message(usr_to, usr_from, subject_lbl, msg)
        return True
    except Exception:
        return False
