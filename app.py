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
    "sel_lob":                 [],
    "sel_functions":           [],
    "sel_tao":                 [],
    "sel_other":               [],
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

# Clear any stale session-state values that no longer exist in the option lists
_valid_regions = set(platforms["regions"])
if any(r not in _valid_regions for r in st.session_state.get("selected_regions", [])):
    st.session_state["selected_regions"] = []

# ── Apply quarter filter ──────────────────────────────────────────────────────
_quarter = st.session_state.get("selected_quarter_filter", "")
if _quarter and "quarter" in all_audits_raw.columns:
    all_audits = all_audits_raw[all_audits_raw["quarter"] == _quarter].copy()
else:
    all_audits = all_audits_raw.copy()

# ── Apply region filter ───────────────────────────────────────────────────────
_enterprise      = st.session_state.get("enterprise_view", False)
_sel_platforms   = list(set(
    st.session_state.get("sel_lob",       []) +
    st.session_state.get("sel_functions", []) +
    st.session_state.get("sel_tao",       []) +
    st.session_state.get("sel_other",     [])
))
_sel_regions     = st.session_state.get("selected_regions", [])

if not _enterprise and _sel_regions and "region" in all_audits.columns:
    _sel_region_set = set(_sel_regions)
    _region_match = all_audits["region"].fillna("").apply(
        lambda x: bool({r.strip() for r in x.split("|") if r.strip()} & _sel_region_set)
    )
    all_audits = all_audits[_region_match]

# ── Platform scope + dynamic audit_type ──────────────────────────────────────
if not _enterprise and _sel_platforms and "lead_group" in all_audits.columns:
    import re as _re
    _plat_set = set(_sel_platforms)

    _lead_match = all_audits["lead_group"].isin(_plat_set)
    _impacted_match = (
        all_audits["impacted_platform"]
        .fillna("")
        .apply(lambda x: bool({p.strip() for p in _re.split(r"[|,]", x) if p.strip()} & _plat_set))
    )
    _ae_match = (
        all_audits["ae_platforms"]
        .fillna("")
        .apply(lambda x: bool({p.strip() for p in x.split("|") if p.strip()} & _plat_set))
    ) if "ae_platforms" in all_audits.columns else all_audits["lead_group"].apply(lambda _: False)

    all_audits = all_audits[_lead_match | _impacted_match | _ae_match].copy()

    # Re-align masks to filtered index
    _lead_f     = _lead_match.loc[all_audits.index]
    _impacted_f = _impacted_match.loc[all_audits.index]
    _ae_f       = _ae_match.loc[all_audits.index]

    # Priority: Owned Audit > Indirect > AE In-Scope
    all_audits["ae_in_scope"] = _ae_f.values
    all_audits["audit_type"]  = "AE In-Scope"
    all_audits.loc[_impacted_f.values & ~_lead_f.values, "audit_type"] = "Indirect"
    all_audits.loc[_lead_f.values, "audit_type"] = "Owned Audit"

if "audit_type" not in all_audits.columns:
    all_audits["audit_type"] = ""
if "ae_in_scope" not in all_audits.columns:
    all_audits["ae_in_scope"] = False

# ── Filter issues by platform (issue_owner_platform column) ──────────────────
if not _enterprise and _sel_platforms and "owner_platform" in all_issues.columns:
    all_issues = all_issues[all_issues["owner_platform"].isin(set(_sel_platforms))]

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
    _qtr_badge = (
        '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
        '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
        f"<div class='platform-title'>&#9679; {platform} "
        "<span style='background:#dbeafe;color:#1e40af;border-radius:4px;"
        "padding:2px 8px;font-size:0.72rem;font-weight:600;margin-left:8px;'>Platform View</span></div>"
        '<div style="display:inline-flex;align-items:stretch;border-radius:10px;overflow:hidden;'
        'box-shadow:0 2px 10px rgba(15,60,120,0.13),0 0 0 1px rgba(15,60,120,0.09);margin-bottom:14px;">'
        '<div style="background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 100%);padding:9px 18px;'
        'display:flex;flex-direction:column;justify-content:center;flex-shrink:0;">'
        '<span style="font-family:IBM Plex Mono,monospace;font-size:0.46rem;font-weight:600;'
        'letter-spacing:0.14em;color:rgba(255,255,255,0.55);text-transform:uppercase;">Fiscal Quarter</span>'
        '<span style="font-family:Barlow Condensed,sans-serif;font-size:1.05rem;font-weight:700;'
        'color:#ffffff;letter-spacing:0.03em;line-height:1.2;">Q2 FY2026</span>'
        '</div>'
        '<div style="background:#f8fafc;padding:9px 16px;display:flex;align-items:center;'
        'border-right:1px solid #e2e8f0;flex-shrink:0;">'
        '<span style="font-family:IBM Plex Mono,monospace;font-size:0.73rem;font-weight:500;'
        'color:#334155;white-space:nowrap;">Feb 1 \u2013 Apr 30</span>'
        '</div>'
        '<div style="background:#fffbeb;padding:9px 14px;display:flex;align-items:center;'
        'gap:8px;border-right:1px solid #fde68a;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:#f59e0b;flex-shrink:0;"></span>'
        '<div>'
        '<div style="font-family:IBM Plex Mono,monospace;font-size:0.46rem;font-weight:700;'
        'letter-spacing:0.1em;color:#92400e;text-transform:uppercase;">Primary Cutoff</div>'
        '<div style="font-family:Barlow Condensed,sans-serif;font-size:0.95rem;font-weight:700;'
        'color:#78350f;letter-spacing:0.02em;">Apr 15</div>'
        '</div>'
        '</div>'
        '<div style="background:#fef2f2;padding:9px 14px;display:flex;align-items:center;gap:8px;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:#ef4444;flex-shrink:0;"></span>'
        '<div>'
        '<div style="font-family:IBM Plex Mono,monospace;font-size:0.46rem;font-weight:700;'
        'letter-spacing:0.1em;color:#991b1b;text-transform:uppercase;">Hard Close</div>'
        '<div style="font-family:Barlow Condensed,sans-serif;font-size:0.95rem;font-weight:700;'
        'color:#7f1d1d;letter-spacing:0.02em;">Apr 30</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(_qtr_badge, unsafe_allow_html=True)
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
    render_portfolio_overview(all_audits, issues_df=all_issues, snapshot_mode=snapshot_mode)

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
