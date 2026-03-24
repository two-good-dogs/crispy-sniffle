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
from data.mock_data import get_audits, get_adjustments
from components.sidebar import render_sidebar
from components.header import render_header, render_export_button
from components.portfolio_overview import render_portfolio_overview
from components.issue_tracker import render_issue_tracker
from components.adjustment_workflow import render_adjustment_workflow
from components.commentary import render_commentary
from components.deck_preview import render_deck_preview
from components.data_validations import render_data_validations
from components.risk_stripe_coverage import render_risk_stripe_coverage

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "selected_platform": "Capital Markets",
    "selected_function": "(none)",
    "selected_technology": "(none)",
    "selected_region_nav": "(all)",
    "view_mode": "Platform",
    "selected_quarter": "Q2 FY25 · Apr 30 close",
    "snapshot_mode": False,
    "adjustments": get_adjustments(),
    "commentary": {},
    "audit_search": "",
    "audit_region_filter": [],
    "audit_status_filter": [],
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar()

# ── Load data ─────────────────────────────────────────────────────────────────
all_audits = get_audits()
platform = st.session_state.get("selected_platform", "Capital Markets")

# ── Header ────────────────────────────────────────────────────────────────────
snapshot_mode = render_header()

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
    render_export_button(platform)

with btn_col2:
    if not snapshot_mode:
        if st.button("+ Adjustment", type="primary", use_container_width=True, key="top_adj_btn"):
            # Switch to adjustment tab by setting a flag
            st.session_state["jump_to_adj"] = True
            st.rerun()

# ── Main tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "Portfolio Overview",
    "Risk Stripe Coverage",
    "Issue Tracker",
    "Adjustment Workflow",
    "Commentary",
    "Deck Preview",
    "Data Validations",
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
    render_deck_preview(platform, all_audits, snapshot_mode=snapshot_mode)

with tabs[6]:
    render_data_validations(all_audits, snapshot_mode=snapshot_mode)
