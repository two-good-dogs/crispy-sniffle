import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="AuditIQ",
    page_icon="📋",
    initial_sidebar_state="expanded",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────
import os
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from data.database import init_db, db_get_messages
import data.loader as loader
from data.mock_data import CURRENT_USER as _CURRENT_USER, get_seed_messages, get_adjustments
from components.sidebar import render_sidebar
from components.header import render_header, render_export_button
from components.portfolio_overview import render_portfolio_overview
from components.risk_stripe_coverage import render_risk_stripe_coverage
from components.issue_tracker import render_issue_tracker
from components.adjustment_workflow import render_adjustment_workflow
from components.commentary import render_commentary
from components.control_environment import render_control_environment
from components.control_environment_regional import render_control_environment_regional
from components.data_validations import render_data_validations
from components.notifications import render_notifications
from components.assurance_summary import render_assurance_summary

# ── Init DB (creates tables + seeds if empty) ─────────────────────────────────
init_db()

# ── Data source status ────────────────────────────────────────────────────────
_db_status = loader.get_connection_status()

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "selected_quarter_filter": "Q1 2026",
    "selected_platforms": ["CM"],
    "selected_functions": ["HR"],
    "selected_technology": ["T&O"],
    "selected_regions": ["Canada"],
    "enterprise_view": False,
    "view_mode": "Platform",
    "selected_quarter": "Q2 FY25 · Apr 30 close",
    "snapshot_mode": False,
    "adjustments": loader.get_adjustments(),
    "commentary": {},
    "audit_search": "",
    "audit_region_filter": [],
    "audit_status_filter": [],
    "messages": loader.get_messages_for_user(_CURRENT_USER),
    "db_status": _db_status,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Unread count (from DB, before sidebar renders) ───────────────────────────
_all_msgs = db_get_messages()
st.session_state["messages"] = _all_msgs
_unread = sum(1 for m in _all_msgs if m.get("to_user") == _CURRENT_USER and not m.get("read", True))

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar(unread_count=_unread)

# ── Load data ─────────────────────────────────────────────────────────────────
_all_audits_raw = loader.get_audits()
_enterprise = st.session_state.get("enterprise_view", False)
_selected_platforms = st.session_state.get("selected_platforms", ["CM"])
_selected_quarter = st.session_state.get("selected_quarter_filter", "Q1 2026")
_selected_regions = st.session_state.get("selected_regions", [])

# Apply quarter filter (always)
all_audits = _all_audits_raw[_all_audits_raw["quarter"] == _selected_quarter].copy() if "quarter" in _all_audits_raw.columns else _all_audits_raw.copy()

# Apply region filter (if selections made and not enterprise)
if not _enterprise and _selected_regions and "region" in all_audits.columns:
    all_audits = all_audits[all_audits["region"].isin(_selected_regions)]

if _enterprise:
    platform = "Enterprise"
elif len(_selected_platforms) == 1:
    platform = _selected_platforms[0]
elif len(_selected_platforms) > 1:
    platform = f"{_selected_platforms[0]} +{len(_selected_platforms) - 1}"
else:
    platform = "All Platforms"

# ── Header ────────────────────────────────────────────────────────────────────
snapshot_mode = render_header()

# ── Data source banner ────────────────────────────────────────────────────────
if _db_status["live"]:
    st.markdown(
        f"<div style='background:#d1fae5;border:1px solid #6ee7b7;border-radius:6px;"
        f"padding:5px 14px;font-size:0.76rem;color:#065f46;margin-bottom:6px;'>"
        f"🟢 Live data · <strong>{_db_status['db']}</strong> ({_db_status['env']})</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"<div style='background:#fef9c3;border:1px solid #fde047;border-radius:6px;"
        f"padding:5px 14px;font-size:0.76rem;color:#713f12;margin-bottom:6px;'>"
        f"🟡 Using demo data · set <code>ENV_NAME</code>, <code>SCON_HOST</code>, "
        f"<code>SOI_ID</code>, <code>SOI_PW</code> to connect to the database · "
        f"{_db_status.get('reason', '')}</div>",
        unsafe_allow_html=True,
    )

# ── View Mode Toggle ─────────────────────────────────────────────────────────
view_col, spacer = st.columns([1.5, 8.5])
with view_col:
    view_mode = st.segmented_control(
        "View",
        ["Platform", "Regional"],
        key="view_mode",
        selection_mode="single",
    )

# ── Platform title row ────────────────────────────────────────────────────────
title_col, btn_col1, btn_col2 = st.columns([5, 1, 1])

with title_col:
    lob_label = (
        "<span style='background:#dbeafe;color:#1e40af;border-radius:4px;"
        "padding:2px 8px;font-size:0.72rem;font-weight:600;margin-left:8px;'>Platform View</span>"
    )
    st.markdown(
        f"<div class='platform-title'>● {platform} {lob_label}</div>"
        f"<div class='platform-subtitle'>"
        f"Q2 FY2025: Feb 1 – Apr 30 &nbsp;·&nbsp; Primary cutoff Apr 15 &nbsp;·&nbsp; Hard close Apr 30"
        f"</div>",
        unsafe_allow_html=True,
    )

with btn_col1:
    render_export_button(platform, all_audits)

with btn_col2:
    if not snapshot_mode:
        if st.button("+ Adjustment", type="primary", use_container_width=True, key="top_adj_btn"):
            st.session_state["jump_to_adj"] = True
            st.rerun()

# ── Main tabs ─────────────────────────────────────────────────────────────────
notif_label = f"🔔 Notifications  {_unread}" if _unread else "Notifications"

tabs = st.tabs([
    "Portfolio Overview",
    "Risk Stripe Coverage",
    "Issue Tracker",
    "Adjustment Workflow",
    "Commentary",
    "Control Environment",
    "Data Validations",
    "Assurance Summary",
    notif_label,
])

with tabs[0]:
    render_portfolio_overview(all_audits, snapshot_mode=snapshot_mode)

with tabs[1]:
    render_risk_stripe_coverage(all_audits, snapshot_mode=snapshot_mode)

with tabs[2]:
    render_issue_tracker(all_audits)

with tabs[3]:
    render_adjustment_workflow(snapshot_mode=snapshot_mode)

with tabs[4]:
    render_commentary(platform, snapshot_mode=snapshot_mode)

with tabs[5]:
    # Get view mode
    _view_mode = st.session_state.get("view_mode", "Platform")

    if _view_mode == "Platform":
        render_control_environment(
            snapshot_mode=snapshot_mode,
            platforms=_selected_platforms if not _enterprise else None,
        )
    else:  # Regional view
        render_control_environment_regional(
            snapshot_mode=snapshot_mode,
            regions=_selected_regions if not _enterprise else None,
        )

with tabs[6]:
    render_data_validations(all_audits, snapshot_mode=snapshot_mode)

with tabs[7]:
    render_assurance_summary(all_audits, snapshot_mode=snapshot_mode)

with tabs[8]:
    render_notifications(snapshot_mode=snapshot_mode)
