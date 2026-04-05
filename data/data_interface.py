"""
data_interface.py — Live database connection layer.

Mirrors the structure of the reference data_interface.py.
Connects to the SQL Server database via SQLAlchemy.
Set ENV_NAME=PROD and SOI_ID/SOI_PW/SCON_HOST for production.
Leave ENV_NAME=LOCAL (default) to attempt Windows ODBC trusted connection.
"""

import json
import os

import pandas as pd
from urllib.parse import quote_plus

# ── Optional DB imports — app still runs without them ─────────────────────────
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

_conn_url = None

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
        _conn_url = (
            f"mssql+pymssql://{sql_id}:{quote_plus(sql_pw)}@{sql_host}/{sql_db}"
        )


def is_available() -> bool:
    """Quick check — returns True only if SQLAlchemy is installed and a
    connection URL was successfully built."""
    return _SQLALCHEMY_OK and _conn_url is not None


def _engine():
    if not is_available():
        raise RuntimeError("Database not available — check env vars and drivers.")
    return create_engine(_conn_url)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _agg_to_json(series) -> str:
    seen, result = set(), []
    for val in series.dropna():
        for v in str(val).split(","):
            v = v.strip()
            if v and v not in seen:
                seen.add(v)
                result.append(v)
    return json.dumps(result)


def _clean(x):
    """Remove brackets and quotes from aggregated display values."""
    if pd.isna(x):
        return x
    return str(x).replace("[", "").replace("]", "").replace('"', "").replace("'", "")


# ── Public data loaders ───────────────────────────────────────────────────────

def load_data(yr: str) -> tuple:
    """
    Load and process the three core DataFrames from the database.

    Parameters
    ----------
    yr : str
        Reporting year/quarter identifier passed to the stored procedures,
        e.g. ``"2025"`` or ``"2025 Q2"``.

    Returns
    -------
    eng : pd.DataFrame
        One row per engagement/audit with all scalar and joined fields.
    rcm : pd.DataFrame
        Raw controls (Risk and Controls Matrix) rows.
    iss : pd.DataFrame
        Raw issues rows.
    """
    engine = _engine()
    with engine.begin() as conn:
        apm = pd.read_sql(f"PUB.usp_ACR_QE_APM {yr}", conn)
        rcm = pd.read_sql(f"PUB.usp_ACR_QE_RCM {yr}", conn)
        iss = pd.read_sql(f"PUB.usp_ACR_QE_ISS {yr}", conn)

    # ── 1. APM → one row per audit ────────────────────────────────────────────
    SCALAR = [
        "audit_id", "plan_coverage_id", "audit_title", "lead_audit_group",
        "regional_coverage", "Core_Type", "status", "reporting_quarter",
        "actual_end", "impacted_audit_group", "at_risk",
        "emerging_risk_flag", "current_quarter",
    ]
    # Keep only columns that actually exist in the returned data
    scalar_cols = [c for c in SCALAR if c in apm.columns]
    eng = apm.drop_duplicates("audit_id", keep="first")[scalar_cols].copy()

    eng = eng.rename(columns={
        "audit_id":           "engagement_id",
        "audit_title":        "title",
        "lead_audit_group":   "audit_group",
        "Core_Type":          "engagement_type",
        "reporting_quarter":  "quarter",
        "regional_coverage":  "region",
    })

    # ── 2. Ratings — join from APM (report_rating / marc_rating) ─────────────
    rating_cols = [c for c in ["audit_id", "report_rating", "previous_rating", "marc_rating"] if c in apm.columns]
    if len(rating_cols) > 1:
        pub_sub = (
            apm[rating_cols]
            .rename(columns={"audit_id": "engagement_id", "report_rating": "current_rating"})
            .drop_duplicates("engagement_id")
        )
        eng = eng.merge(pub_sub, on="engagement_id", how="left")

    eng["current_rating"]  = eng.get("current_rating",  pd.Series(dtype=str)).fillna("Not Rated")
    eng["previous_rating"] = eng.get("previous_rating", pd.Series(dtype=str)).fillna("Not Rated")
    eng["marc_rating"]     = eng.get("marc_rating",     pd.Series(dtype=str)).fillna("N/A")

    # ── 3. RCM → controls_tested JSON dict {control_type: count} ─────────────
    if not rcm.empty and "audit_id" in rcm.columns and "control_type" in rcm.columns:
        rcm_agg = (
            rcm.groupby("audit_id")["control_type"]
            .agg(lambda x: json.dumps({k: int(v) for k, v in x.value_counts().items()}))
            .reset_index()
        )
        rcm_agg.columns = ["engagement_id", "controls_tested"]
        eng = eng.merge(rcm_agg, on="engagement_id", how="left")
    eng["controls_tested"] = eng.get("controls_tested", pd.Series(dtype=str)).fillna("{}")

    # ── 4. Issue count per audit ──────────────────────────────────────────────
    if not iss.empty and "audit_id" in iss.columns:
        iss_counts = iss.groupby("audit_id").size().reset_index(name="_issue_count")
        iss_counts = iss_counts.rename(columns={"audit_id": "engagement_id"})
        eng = eng.merge(iss_counts, on="engagement_id", how="left")
    eng["_issue_count"] = eng.get("_issue_count", pd.Series(dtype=int)).fillna(0).astype(int)

    # ── 5. Clean display columns ──────────────────────────────────────────────
    for col in ["region", "impacted_audit_group"]:
        if col in eng.columns:
            eng[col] = eng[col].apply(_clean)

    for col in ["regional_coverage", "impacted_audit_group"]:
        if col in rcm.columns:
            rcm[col] = rcm[col].apply(_clean)

    if "region" in iss.columns:
        iss["region"] = iss["region"].apply(_clean)

    return eng, rcm, iss


def get_messages(usr: str) -> pd.DataFrame:
    """Fetch all messages for a user from the database."""
    engine = _engine()
    with engine.begin() as conn:
        return pd.read_sql(f"[streamlit].[usp_ACR_QE_MEASSAGES] '{usr}'", conn)


def set_message(usr_to: str, usr_from: str, subject_lbl: str, msg: str):
    """Insert a new message into the database."""
    engine = _engine()
    cmd = (
        "EXEC streamlit.usp_set_ACR_MESSAGE "
        ":USR_TO, :USR_FROM, :SUBJECT_LBL, :MSG"
    )
    params = {
        "USR_TO": usr_to,
        "USR_FROM": usr_from,
        "SUBJECT_LBL": subject_lbl,
        "MSG": msg,
    }
    with engine.connect() as conn:
        conn.execute(text(cmd), params)
        conn.commit()
