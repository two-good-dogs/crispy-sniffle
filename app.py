import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="AuditIQ",
    page_icon="📋",
    initial_sidebar_state="expanded",
)

import os
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

import data.data_interface as di
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

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "selected_quarter_filter": "Q1 2026",
    "selected_platforms":      [],
    "selected_regions":        [],
    "enterprise_view":         False,
    "view_mode":               "Platform",
    "snapshot_mode":           False,
    "adjustments":             [],
    "commentary":              {},
    "audit_search":            "",
    "audit_region_filter":     [],
    "audit_status_filter":     [],
    "messages":                [],
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Load core data ────────────────────────────────────────────────────────────
all_audits_raw = di.get_audits()
all_issues     = di.get_issues()

# ── Platform and region filter options (derived from data) ────────────────────
platforms = di.get_platforms(all_audits_raw)

# ── Apply quarter filter ──────────────────────────────────────────────────────
_quarter = st.session_state.get("selected_quarter_filter", "")
if _quarter and "quarter" in all_audits_raw.columns:
    all_audits = all_audits_raw[all_audits_raw["quarter"] == _quarter].copy()
else:
    all_audits = all_audits_raw.copy()

# ── Apply region filter ───────────────────────────────────────────────────────
_enterprise      = st.session_state.get("enterprise_view", False)
_sel_platforms   = st.session_state.get("selected_platforms", [])
_sel_regions     = st.session_state.get("selected_regions", [])

if not _enterprise and _sel_regions and "region" in all_audits.columns:
    _sel_region_set = set(_sel_regions)
    _region_match = all_audits["region"].fillna("").apply(
        lambda x: bool({r.strip() for r in x.split("|") if r.strip()} & _sel_region_set)
    )
    all_audits = all_audits[_region_match]

# ── Platform scope + dynamic audit_type ──────────────────────────────────────
if not _enterprise and _sel_platforms and "lead_group" in all_audits.columns:
    _plat_set = set(_sel_platforms)

    _lead_match = all_audits["lead_group"].isin(_plat_set)
    _impacted_match = (
        all_audits["impacted_platform"]
        .fillna("")
        .apply(lambda x: bool({p.strip() for p in x.split(",") if p.strip()} & _plat_set))
    )
    all_audits = all_audits[_lead_match | _impacted_match].copy()
    all_audits["audit_type"] = "Indirect"
    all_audits.loc[_lead_match, "audit_type"] = "Owned Audit"

if "audit_type" not in all_audits.columns:
    all_audits["audit_type"] = ""

# ── Messages (loaded fresh each run) ─────────────────────────────────────────
try:
    _msgs_raw = di.get_messages(di.CURRENT_USER)
    if (
        not _msgs_raw.empty
        and "usr_to" in _msgs_raw.columns
        and "is_read" in _msgs_raw.columns
    ):
        _unread = int(
            ((_msgs_raw["usr_to"] == di.CURRENT_USER) & (_msgs_raw["is_read"] == False)).sum()
        )
    else:
        _unread = 0
    st.session_state["messages"] = di.get_messages_for_user(di.CURRENT_USER)
except Exception:
    _unread = 0
    st.session_state["messages"] = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar(unread_count=_unread, platforms=platforms, audits_df=all_audits)

# ── Platform label ────────────────────────────────────────────────────────────
if _enterprise:
    platform = "Enterprise"
elif len(_sel_platforms) == 1:
    platform = _sel_platforms[0]
elif len(_sel_platforms) > 1:
    platform = f"{_sel_platforms[0]} +{len(_sel_platforms) - 1}"
else:
    platform = "All Platforms"

# ── Header ────────────────────────────────────────────────────────────────────
snapshot_mode = render_header()

# ── Platform title row ────────────────────────────────────────────────────────
title_col, btn_col1, btn_col2 = st.columns([5, 1, 1])
with title_col:
    st.markdown(
        f"<div class='platform-title'>● {platform} "
        f"<span style='background:#dbeafe;color:#1e40af;border-radius:4px;"
        f"padding:2px 8px;font-size:0.72rem;font-weight:600;margin-left:8px;'>Platform View</span></div>"
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
    render_issue_tracker(all_audits, all_issues)

with tabs[3]:
    render_adjustment_workflow(snapshot_mode=snapshot_mode)

with tabs[4]:
    render_commentary(platform, snapshot_mode=snapshot_mode)

with tabs[5]:
    _view_mode = st.session_state.get("view_mode", "Platform")
    if _view_mode == "Platform":
        render_control_environment(
            snapshot_mode=snapshot_mode,
            platforms=_sel_platforms if not _enterprise else None,
        )
    else:
        render_control_environment_regional(
            snapshot_mode=snapshot_mode,
            regions=_sel_regions if not _enterprise else None,
        )

with tabs[6]:
    render_data_validations(all_audits, snapshot_mode=snapshot_mode)

with tabs[7]:
    render_assurance_summary(all_audits, all_issues, snapshot_mode=snapshot_mode)

with tabs[8]:
    render_notifications(snapshot_mode=snapshot_mode)
