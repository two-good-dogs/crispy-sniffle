"""
data_interface.py — Single data layer for AuditIQ.

Connects to SQL Server and exposes normalised DataFrames for audits,
issues and controls.  Set ENV_NAME / SCON_HOST / SOI_ID / SOI_PW to
point at the real database; the app will raise clearly if the connection
cannot be established.
"""

import json
import os
import re
from functools import lru_cache
from urllib.parse import quote_plus

import pandas as pd

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL
    _SQLALCHEMY_OK = True
except ImportError:
    _SQLALCHEMY_OK = False

# ── Connection config ─────────────────────────────────────────────────────────
env      = os.getenv("ENV_NAME", "LOCAL")
sql_host = os.environ.get("SCON_HOST", r"iadb1.fg.rbc.com\in01")
sql_db   = "DBS00_SOI_" + ("LAB" if env == "LOCAL" else "PROD")
sql_id   = os.environ.get("SOI_ID", "")
sql_pw   = os.environ.get("SOI_PW", "")

_conn_url     = None
_cached_engine = None

if _SQLALCHEMY_OK:
    if env == "LOCAL":
        _conn_str = (
            fr"DRIVER={{ODBC Driver 17 for SQL Server}};"
            fr"SERVER={sql_host};DATABASE={sql_db};Trusted_Connection=yes"
        )
        try:
            _conn_url = URL.create("mssql+pyodbc", query={"odbc_connect": _conn_str})
        except Exception:
            _conn_url = None
    elif sql_id and sql_pw:
        _conn_url = f"mssql+pymssql://{sql_id}:{quote_plus(sql_pw)}@{sql_host}/{sql_db}"


def _engine():
    global _cached_engine
    if not _SQLALCHEMY_OK or _conn_url is None:
        raise RuntimeError(
            "Database not available. Set ENV_NAME, SCON_HOST, SOI_ID, SOI_PW."
        )
    if _cached_engine is None:
        _cached_engine = create_engine(_conn_url)
    return _cached_engine


# ── App-level constants ───────────────────────────────────────────────────────
CURRENT_USER = os.getenv("APP_USER", "P. Kumar")

USERS = [
    "P. Kumar",   "J. Smith",   "A. Chen",    "B. Patel",
    "R. Kim",     "L. Nguyen",  "D. Foster",  "F. Okafor",
    "G. Pham",    "H. Blanc",   "I. Martins", "C. Zhang",
    "M. Torres",  "S. Ahmed",   "P. Williams",
]

RISK_STRIPES = [
    # ── Financial Market (4) ──────────────────────────────────────────────────
    {"id": "market_risk",    "name": "Market Risk",         "icon": "📈", "category": "financial_market",    "tier": "critical", "description": "Exposure to adverse movements in market prices including equities, rates, and commodities."},
    {"id": "liquidity_risk", "name": "Liquidity Risk",      "icon": "💧", "category": "financial_market",    "tier": "critical", "description": "Risk of being unable to meet financial obligations as they fall due without incurring unacceptable losses."},
    {"id": "interest_rate",  "name": "Interest Rate Risk",  "icon": "📊", "category": "financial_market",    "tier": "high",     "description": "Exposure to adverse changes in interest rates affecting net interest income and portfolio values."},
    {"id": "fx_risk",        "name": "FX / Currency Risk",  "icon": "💱", "category": "financial_market",    "tier": "high",     "description": "Exposure to foreign exchange rate movements affecting earnings and economic capital."},
    # ── Credit & Balance Sheet (3) ────────────────────────────────────────────
    {"id": "credit_risk",    "name": "Credit Risk",         "icon": "💳", "category": "credit_balance",      "tier": "critical", "description": "Risk of loss from a borrower or counterparty failing to meet its contractual obligations."},
    {"id": "counterparty",   "name": "Counterparty Credit", "icon": "🤝", "category": "credit_balance",      "tier": "high",     "description": "Risk of counterparty default in trading, derivatives, securities financing, or settlement activities."},
    {"id": "concentration",  "name": "Concentration Risk",  "icon": "⚖️", "category": "credit_balance",      "tier": "high",     "description": "Risk from undue exposure to single obligors, sectors, geographies, or correlated asset classes."},
    # ── Operational & Conduct (7) ─────────────────────────────────────────────
    {"id": "operational",    "name": "Operational Risk",    "icon": "⚙️", "category": "operational_conduct", "tier": "critical", "description": "Risk of loss from inadequate or failed internal processes, people, systems, or external events."},
    {"id": "fraud",          "name": "Fraud & Fin. Crime",  "icon": "🚨", "category": "operational_conduct", "tier": "critical", "description": "Internal and external fraud including payment fraud, identity theft, and financial crime schemes."},
    {"id": "aml",            "name": "Anti-Money Laundering","icon": "🏦","category": "operational_conduct", "tier": "critical", "description": "Risk of facilitating money laundering or terrorist financing through inadequate detection and reporting controls."},
    {"id": "conduct_risk",   "name": "Conduct Risk",        "icon": "🎯", "category": "operational_conduct", "tier": "high",     "description": "Risk that employee behaviour leads to poor client outcomes, market integrity issues, or reputational harm."},
    {"id": "third_party",    "name": "Third Party & Vendor","icon": "🔗", "category": "operational_conduct", "tier": "high",     "description": "Risks arising from reliance on third-party service providers, vendors, and outsourced activities."},
    {"id": "bcp",            "name": "Business Continuity", "icon": "🔄", "category": "operational_conduct", "tier": "standard", "description": "Capability to maintain or rapidly recover critical operations following significant disruptions."},
    {"id": "physical_sec",   "name": "Physical Security",   "icon": "🔐", "category": "operational_conduct", "tier": "standard", "description": "Protection of physical assets, premises, and personnel from security threats and unauthorised access."},
    # ── Technology & Cyber (4) ───────────────────────────────────────────────
    {"id": "it_cyber",       "name": "Cyber Security",      "icon": "🛡️", "category": "tech_cyber",          "tier": "critical", "description": "Protection of systems, networks, and data from cyber attacks, intrusions, and unauthorised access."},
    {"id": "data_gov",       "name": "Data Governance",     "icon": "🗄️", "category": "tech_cyber",          "tier": "high",     "description": "Accuracy, completeness, lineage, and security of enterprise data and management information."},
    {"id": "it_resilience",  "name": "IT Resilience",       "icon": "🖥️", "category": "tech_cyber",          "tier": "high",     "description": "Availability, recoverability, and reliability of IT systems and critical infrastructure."},
    {"id": "cloud_risk",     "name": "Cloud & Infrastructure","icon": "☁️","category": "tech_cyber",          "tier": "standard", "description": "Risks from cloud adoption, infrastructure transformation, and managed service dependencies."},
    # ── Regulatory & Legal (4) ───────────────────────────────────────────────
    {"id": "compliance",     "name": "Regulatory Compliance","icon": "📋","category": "regulatory_legal",    "tier": "critical", "description": "Adherence to applicable laws, rules, regulations, and supervisory expectations across jurisdictions."},
    {"id": "sanctions",      "name": "Sanctions & FCRM",    "icon": "⚠️", "category": "regulatory_legal",    "tier": "critical", "description": "Compliance with economic sanctions programmes and financial crimes risk management requirements."},
    {"id": "legal_risk",     "name": "Legal Risk",          "icon": "⚖️", "category": "regulatory_legal",    "tier": "high",     "description": "Exposure to litigation, contractual disputes, regulatory investigations, or unenforceable agreements."},
    {"id": "privacy",        "name": "Privacy & Data Prot.", "icon": "🔏","category": "regulatory_legal",    "tier": "high",     "description": "Compliance with privacy legislation and data subject rights obligations across jurisdictions."},
    # ── Governance & Strategy (3) ────────────────────────────────────────────
    {"id": "model_risk",     "name": "Model Risk",          "icon": "🧮", "category": "governance_strategy", "tier": "high",     "description": "Risk from errors in model design, data inputs, implementation, or inappropriate use of quantitative models."},
    {"id": "esg",            "name": "ESG & Climate Risk",  "icon": "🌱", "category": "governance_strategy", "tier": "standard", "description": "Environmental, social, and governance risks including physical and transition climate-related exposures."},
    {"id": "strategic_risk", "name": "Strategic Risk",      "icon": "🎯", "category": "governance_strategy", "tier": "standard", "description": "Risk from adverse business decisions, poor strategy execution, or failure to adapt to industry changes."},
]

# ── Column-mapping constants ──────────────────────────────────────────────────
_STATUS_MAP = {
    "Planning":  "In Progress",
    "Fieldwork": "Fieldwork",
    "Reporting": "In Progress",
    "Issued":    "Complete",
    "Completed": "Complete",
    "Complete":  "Complete",
    "Cancelled": "Complete",
}

_RATING_MAP = {
    "High":              "High",
    "Medium":            "Medium",
    "Low":               "Low",
    "Not Rated":         "N/A",
    "Satisfactory":      "Low",
    "Needs Improvement": "Medium",
    "Unsatisfactory":    "High",
}

_SEVERITY_MAP = {
    "Level 1": "High",   "1": "High",
    "Level 2": "Medium", "2": "Medium",
    "Level 3": "Low",    "3": "Low",
}

# SAT > RI > UNSAT — used for rating change direction
_RATING_ORDER = {
    "SAT": 2, "SATISFACTORY": 2,
    "RI": 1,  "NEEDS IMPROVEMENT": 1,
    "UNSAT": 0, "UNSATISFACTORY": 0,
}
_RATING_NULL = {"", "NR", "NOT RATED", "N/A", "NAN", "NONE", "NOT APPLICABLE", "NOT_RATED"}


def _rating_change(prev, curr) -> str:
    p = str(prev).strip().upper()
    c = str(curr).strip().upper()
    if p in _RATING_NULL or c in _RATING_NULL:
        return "N/A"
    po = _RATING_ORDER.get(p)
    co = _RATING_ORDER.get(c)
    if po is None or co is None:
        return "N/A"
    if co > po:
        return "Improved"
    if co < po:
        return "Deteriorated"
    return "No Change"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clean(x):
    if pd.isna(x):
        return x
    return str(x).replace("[", "").replace("]", "").replace('"', "").replace("'", "")


# ── Raw DB load (results cached per year string) ──────────────────────────────

@lru_cache(maxsize=8)
def _load_raw(yr: str) -> tuple:
    """
    Execute the three stored procedures and return raw DataFrames.
    Results are cached in-process per yr value.
    """
    engine = _engine()
    with engine.begin() as conn:
        apm = pd.read_sql(f"PUB.usp_ACR_QE_APM {yr}", conn)
        rcm = pd.read_sql(f"PUB.usp_ACR_QE_RCM {yr}", conn)
        iss = pd.read_sql(f"PUB.usp_ACR_QE_ISS {yr}", conn)
    return apm, rcm, iss


def _year() -> str:
    return os.getenv("REPORT_YEAR", "2025")


# ── Normalisers ───────────────────────────────────────────────────────────────

def _build_eng(apm: pd.DataFrame, rcm: pd.DataFrame, iss: pd.DataFrame) -> pd.DataFrame:
    """Collapse APM to one row per engagement and join ratings + counts."""
    SCALAR = [
        "audit_id", "audit_title", "lead_audit_group", "regional_coverage",
        "Core_Type", "status", "reporting_quarter", "impacted_audit_group",
        "at_risk", "ae_platforms",
    ]
    scalar_cols = [c for c in SCALAR if c in apm.columns]
    eng = apm.drop_duplicates("audit_id", keep="first")[scalar_cols].copy()

    eng = eng.rename(columns={
        "audit_id":           "engagement_id",
        "audit_title":        "title",
        "lead_audit_group":   "audit_group",
        "Core_Type":          "engagement_type",
        "reporting_quarter":  "quarter",
        "regional_coverage":  "region",
        "impacted_audit_group": "impacted_platform_raw",
    })

    # Ratings — pull all rating columns present in apm, normalise to common names.
    # DB may use: report_rating, current_rating, marc_rating (for current), previous_rating.
    rating_cols = [c for c in ["audit_id", "report_rating", "current_rating", "marc_rating", "previous_rating"]
                   if c in apm.columns]
    if len(rating_cols) > 1:
        ratings = (
            apm[rating_cols]
            .rename(columns={
                "audit_id":     "engagement_id",
                "report_rating": "current_rating",  # common DB alias
                "marc_rating":   "current_rating",  # fallback alias
            })
            .drop_duplicates("engagement_id")
        )
        eng = eng.merge(ratings, on="engagement_id", how="left")

    if "current_rating" not in eng.columns:
        eng["current_rating"] = "Not Rated"
    else:
        eng["current_rating"] = eng["current_rating"].fillna("Not Rated")

    if "previous_rating" not in eng.columns:
        eng["previous_rating"] = "Not Rated"
    else:
        eng["previous_rating"] = eng["previous_rating"].fillna("Not Rated")

    # Issue count
    if not iss.empty and "audit_id" in iss.columns:
        counts = (
            iss.groupby("audit_id").size()
            .reset_index(name="issue_count")
            .rename(columns={"audit_id": "engagement_id"})
        )
        eng = eng.merge(counts, on="engagement_id", how="left")
    eng["issue_count"] = eng.get("issue_count", pd.Series(dtype=int)).fillna(0).astype(int)

    # Risk stripes from RCM control_type
    if not rcm.empty and "audit_id" in rcm.columns and "control_type" in rcm.columns:
        stripe_agg = (
            rcm.groupby("audit_id")["control_type"]
            .apply(lambda s: list(s.dropna().unique()))
            .reset_index()
            .rename(columns={"audit_id": "engagement_id", "control_type": "risk_stripes"})
        )
        eng = eng.merge(stripe_agg, on="engagement_id", how="left")
    eng["risk_stripes"] = eng.get("risk_stripes", pd.Series(dtype=object)).apply(
        lambda x: x if isinstance(x, list) else []
    )

    # Clean display fields
    for col in ["region", "impacted_platform_raw"]:
        if col in eng.columns:
            eng[col] = eng[col].apply(_clean)

    return eng


def _normalise_audits(eng: pd.DataFrame) -> pd.DataFrame:
    df = eng.rename(columns={
        "engagement_id":       "audit_id",
        "title":               "audit_name",
        "audit_group":         "lead_group",
        "impacted_platform_raw": "impacted_platform",
    })

    df["status"] = (
        df.get("status", pd.Series(dtype=str)).map(_STATUS_MAP).fillna("In Progress")
    )
    df["rating"] = (
        df.get("current_rating", pd.Series(dtype=str)).map(_RATING_MAP).fillna("N/A")
    )
    df["is_overdue"] = (
        df.get("at_risk", pd.Series(dtype=str)).fillna("No").str.upper() == "YES"
    )
    df["out_of_scope"]   = False
    df["audit_type"]     = ""   # computed in app.py after platform filter
    df["digital_rcm"]    = "N/A"
    df["planning_memo"]  = "N/A"
    df["impacted_platform"] = df.get("impacted_platform", pd.Series(dtype=str)).fillna("")

    if "current_rating" in df.columns and "previous_rating" in df.columns:
        df["rating_change"] = df.apply(
            lambda r: _rating_change(r["previous_rating"], r["current_rating"]), axis=1
        )
    else:
        df["rating_change"] = "N/A"

    keep = [
        "audit_id", "audit_name", "audit_type", "lead_group", "region",
        "status", "rating", "current_rating", "previous_rating", "rating_change",
        "issue_count", "digital_rcm", "planning_memo",
        "impacted_platform", "ae_platforms", "is_overdue", "out_of_scope",
        "quarter", "risk_stripes",
    ]
    return df[[c for c in keep if c in df.columns]]


def _normalise_issues(iss: pd.DataFrame) -> pd.DataFrame:
    df = iss.copy()

    if "issue_id" not in df.columns:
        df["issue_id"] = [f"ISS-{i+1:03d}" for i in range(len(df))]

    # Severity
    if "issue_level" in df.columns:
        df["severity"] = df["issue_level"].astype(str).map(_SEVERITY_MAP).fillna("Medium")
    else:
        df["severity"] = "Medium"

    # Status (vectorised)
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
        for candidate in ("owner", "assigned_to"):
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

    # Issue owner platform — try common DB column name variants
    _owner_plat_candidates = ["issue_owner_platform", "owner_platform", "platform", "audit_group"]
    for _c in _owner_plat_candidates:
        if _c in df.columns:
            df["owner_platform"] = df[_c].fillna("")
            break
    if "owner_platform" not in df.columns:
        df["owner_platform"] = ""

    # audit_id link
    if "audit_id" not in df.columns and "engagement_id" in df.columns:
        df = df.rename(columns={"engagement_id": "audit_id"})

    keep = ["issue_id", "audit_id", "title", "severity", "status",
            "due_date", "remediation_owner", "days_overdue", "owner_platform"]
    return df[[c for c in keep if c in df.columns]]


def _normalise_messages(db_df: pd.DataFrame) -> list:
    msgs = []
    for i, row in db_df.iterrows():
        msgs.append({
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
    return msgs


# ── Public API ────────────────────────────────────────────────────────────────

def get_apm_columns() -> dict:
    """Return APM column names and sample non-null values — for debugging only."""
    apm, _, _ = _load_raw(_year())
    result = {}
    for col in apm.columns:
        sample = apm[col].dropna().unique()[:3].tolist()
        result[col] = sample
    return result


def get_audits() -> pd.DataFrame:
    apm, rcm, iss = _load_raw(_year())
    eng = _build_eng(apm, rcm, iss)
    return _normalise_audits(eng)


def get_issues() -> pd.DataFrame:
    _, _, iss = _load_raw(_year())
    return _normalise_issues(iss)


def get_controls() -> pd.DataFrame:
    """Return raw RCM (controls) DataFrame."""
    _, rcm, _ = _load_raw(_year())
    return rcm.copy()


_CANONICAL_REGIONS = ["APAC", "Canada", "Caribbean", "USA", "UK"]
# Lowercase lookup for case-insensitive matching
_CANONICAL_LOWER = {r.lower(): r for r in _CANONICAL_REGIONS}


def _extract_regions(audits_df: pd.DataFrame) -> list:
    """
    Split region strings on any common delimiter (|, comma, semicolon),
    normalise case, and return only the 5 canonical region names.
    """
    found: set = set()
    for val in audits_df["region"].dropna():
        # Split on pipe, comma, or semicolon (with optional surrounding whitespace)
        parts = re.split(r"\s*[|,;]\s*", str(val).strip())
        for part in parts:
            part = part.strip()
            canonical = _CANONICAL_LOWER.get(part.lower())
            if canonical:
                found.add(canonical)
    # Return in canonical order
    return [r for r in _CANONICAL_REGIONS if r in found]


def get_platforms(audits_df: pd.DataFrame = None) -> dict:
    """
    Return sidebar filter options.
    Lines of business and regions are derived from the audits data when provided,
    so the filters always reflect what is actually in the dataset.
    Regions are split on '|' and restricted to the 5 canonical values.
    """
    if audits_df is not None and not audits_df.empty:
        lobs    = sorted(audits_df["lead_group"].dropna().unique().tolist())
        regions = _extract_regions(audits_df)
    else:
        df = get_audits()
        lobs    = sorted(df["lead_group"].dropna().unique().tolist())
        regions = _extract_regions(df)
    return {"lines_of_business": lobs, "regions": regions}


def get_messages_for_user(usr: str) -> list:
    """Return messages for the given user as a list of dicts."""
    try:
        db_df = get_messages(usr)
        return _normalise_messages(db_df)
    except Exception:
        return []


def send_message_to_user(usr_to: str, usr_from: str, subject_lbl: str, msg: str):
    """Write a message to the database."""
    set_message(usr_to, usr_from, subject_lbl, msg)


def compute_field_completeness(df: pd.DataFrame) -> float:
    """Fraction of key fields that are populated (not N/A or empty)."""
    if df.empty:
        return 0.0
    check_cols = [c for c in ("digital_rcm", "planning_memo", "impacted_platform") if c in df.columns]
    if not check_cols:
        return 1.0
    filled = df[check_cols].apply(
        lambda col: col.notna() & (col != "N/A") & (col != "")
    )
    return float(filled.values.mean())


# ── Raw message helpers (kept for direct use) ─────────────────────────────────

def get_messages(usr: str) -> pd.DataFrame:
    """Fetch all messages for a user from the database."""
    with _engine().begin() as conn:
        return pd.read_sql(f"[streamlit].[usp_ACR_QE_MEASSAGES] '{usr}'", conn)


def set_message(usr_to: str, usr_from: str, subject_lbl: str, msg: str):
    """Insert a new message into the database."""
    cmd = "EXEC streamlit.usp_set_ACR_MESSAGE :USR_TO, :USR_FROM, :SUBJECT_LBL, :MSG"
    with _engine().begin() as conn:
        conn.execute(text(cmd), {
            "USR_TO": usr_to, "USR_FROM": usr_from,
            "SUBJECT_LBL": subject_lbl, "MSG": msg,
        })
