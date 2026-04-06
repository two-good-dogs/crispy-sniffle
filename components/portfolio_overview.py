import streamlit as st
import pandas as pd


# ── Styler helpers ────────────────────────────────────────────────────────────

STATUS_COLORS = {
    "Complete":    "background-color:#d1fae5;color:#065f46;border-radius:10px;padding:2px 8px;",
    "In Progress": "background-color:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 8px;",
    "Fieldwork":   "background-color:#fef3c7;color:#92400e;border-radius:10px;padding:2px 8px;",
}

RATING_COLORS = {
    "High":   "background-color:#fee2e2;color:#991b1b;border-radius:10px;padding:2px 8px;font-weight:600;",
    "Medium": "background-color:#fef3c7;color:#92400e;border-radius:10px;padding:2px 8px;font-weight:600;",
    "Low":    "background-color:#d1fae5;color:#065f46;border-radius:10px;padding:2px 8px;font-weight:600;",
    "N/A":    "background-color:#f3f4f6;color:#6b7280;border-radius:10px;padding:2px 8px;",
}

TYPE_COLORS = {
    "Owned Audit": "background-color:#ede9fe;color:#5b21b6;border-radius:10px;padding:2px 8px;",
    "In-Scope AE": "background-color:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 8px;",
    "Indirect":    "background-color:#f3f4f6;color:#374151;border-radius:10px;padding:2px 8px;",
}

RCM_COLORS = {
    "Done":       "background-color:#d1fae5;color:#065f46;border-radius:10px;padding:2px 8px;",
    "Incomplete": "background-color:#fee2e2;color:#991b1b;border-radius:10px;padding:2px 8px;",
    "N/A":        "background-color:#f3f4f6;color:#6b7280;border-radius:10px;padding:2px 8px;",
}

REGION_COLORS = {
    "North America": "background-color:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 8px;",
    "EMEA":          "background-color:#fce7f3;color:#9d174d;border-radius:10px;padding:2px 8px;",
    "APAC":          "background-color:#d1fae5;color:#065f46;border-radius:10px;padding:2px 8px;",
    "Global":        "background-color:#f3f4f6;color:#374151;border-radius:10px;padding:2px 8px;",
}


def _style_col(col_map):
    def styler(val):
        return col_map.get(val, "")
    return styler


def _render_audit_table(df: pd.DataFrame):
    if df.empty:
        st.info("No audits match the current filters.")
        return

    display_cols = [
        "audit_id", "audit_name", "audit_type", "lead_group",
        "region", "status", "rating", "issue_count", "digital_rcm", "planning_memo"
    ]
    display_df = df[display_cols].copy()
    display_df.columns = [
        "ID", "Audit Name", "Type", "Lead Group",
        "Region", "Status", "Rating", "Issues", "Digital RCM", "Planning Memo"
    ]

    styled = (
        display_df.style
        .applymap(_style_col(TYPE_COLORS), subset=["Type"])
        .applymap(_style_col(REGION_COLORS), subset=["Region"])
        .applymap(_style_col(STATUS_COLORS), subset=["Status"])
        .applymap(_style_col(RATING_COLORS), subset=["Rating"])
        .applymap(_style_col(RCM_COLORS), subset=["Digital RCM"])
        .applymap(_style_col(RCM_COLORS), subset=["Planning Memo"])
        .set_properties(**{"text-align": "left"})
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "left"), ("font-size", "0.78rem"),
                                          ("color", "#6b7280"), ("font-weight", "600"),
                                          ("text-transform", "uppercase"), ("letter-spacing", "0.04em")]},
            {"selector": "td", "props": [("font-size", "0.82rem"), ("padding", "6px 8px")]},
        ])
    )

    st.dataframe(styled, use_container_width=True, hide_index=True, height=380)


def _filter_audits(df, search="", regions=None, statuses=None, audit_types=None):
    if search:
        q = search.lower()
        mask = (
            df["audit_name"].str.lower().str.contains(q, na=False) |
            df["audit_id"].str.lower().str.contains(q, na=False) |
            df["lead_group"].str.lower().str.contains(q, na=False)
        )
        df = df[mask]
    if regions:
        df = df[df["region"].isin(regions)]
    if statuses:
        df = df[df["status"].isin(statuses)]
    if audit_types and "audit_type" in df.columns:
        df = df[df["audit_type"].isin(audit_types)]
    return df


def render_portfolio_overview(audits_df: pd.DataFrame, snapshot_mode: bool = False):
    # ── Metric counts ────────────────────────────────────────────────────────
    owned    = audits_df[audits_df["audit_type"] == "Owned Audit"]
    indirect = audits_df[audits_df["audit_type"] == "Indirect"]

    owned_count    = len(owned)
    indirect_count = len(indirect)
    total_count    = len(audits_df)

    all_issues = int(audits_df["issue_count"].sum())
    overdue_count = int(audits_df["is_overdue"].sum())
    out_of_scope_count = int(audits_df["out_of_scope"].sum())

    # ── Audit count framework note ────────────────────────────────────────────
    st.markdown(
        "<div class='framework-note'>"
        "<strong>Audit count framework:</strong> "
        "Owned = Lead Audit Group matches selected platform. "
        "Indirect = Selected platform appears in Impacted Platform field. "
        "Issues = Remediation Owner field."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Four metric cards ─────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="kpi-grid">

          <div class="kpi-card owned" style="animation-delay:0s">
            <div class="kpi-label">Owned Coverage</div>
            <div class="kpi-number">{owned_count}</div>
            <div class="kpi-badge">OWNED</div>
            <hr class="kpi-divider">
            <div class="kpi-meta">↳ Lead Audit Group field</div>
          </div>

          <div class="kpi-card indirect" style="animation-delay:0.07s">
            <div class="kpi-label">Indirect Coverage</div>
            <div class="kpi-number">{indirect_count}</div>
            <div class="kpi-badge">INDIRECT</div>
            <hr class="kpi-divider">
            <div class="kpi-meta">↳ Impacted Platform field</div>
          </div>

          <div class="kpi-card footprint" style="animation-delay:0.14s">
            <div class="kpi-label">Total Footprint</div>
            <div class="kpi-number">{total_count}</div>
            <div class="kpi-badge">DE-DUPLICATED</div>
            <hr class="kpi-divider">
            <div class="kpi-meta-row">
              <span class="kpi-meta-item">Owned&nbsp;<strong>{owned_count}</strong></span>
              <span class="kpi-meta-item" style="color:#1f2937;">·</span>
              <span class="kpi-meta-item">Indirect&nbsp;<strong>{indirect_count}</strong></span>
            </div>
          </div>

          <div class="kpi-card issues" style="animation-delay:0.21s">
            <div class="kpi-label">Open Issues</div>
            <div class="kpi-number">{all_issues}</div>
            <div class="kpi-badge">ISSUES</div>
            <hr class="kpi-divider">
            <div class="kpi-meta">↳ Remediation Owner field</div>
            <div class="kpi-meta-row" style="margin-top:4px;">
              <span class="kpi-meta-item danger">Overdue&nbsp;<strong>{overdue_count}</strong></span>
              <span class="kpi-meta-item" style="color:#1f2937;">·</span>
              <span class="kpi-meta-item">Out-of-scope&nbsp;<strong>{out_of_scope_count}</strong></span>
            </div>
          </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Filter row ────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([3, 2, 2])
    with fc1:
        search = st.text_input(
            "Search audits",
            placeholder="Search by name, ID, or lead group…",
            key="audit_search",
            label_visibility="collapsed",
        )
    with fc2:
        region_filter = st.multiselect(
            "All Regions",
            options=["North America", "EMEA", "APAC", "Global"],
            key="audit_region_filter",
            placeholder="All Regions",
            label_visibility="collapsed",
        )
    with fc3:
        status_filter = st.multiselect(
            "All Statuses",
            options=["Complete", "In Progress", "Fieldwork"],
            key="audit_status_filter",
            placeholder="All Statuses",
            label_visibility="collapsed",
        )

    # Apply filters
    filtered   = _filter_audits(audits_df, search=search,
                                regions=region_filter or None,
                                statuses=status_filter or None)
    owned_f    = _filter_audits(filtered, audit_types=["Owned Audit"])
    indirect_f = _filter_audits(filtered, audit_types=["Indirect"])

    st.markdown(
        f"<div style='font-size:0.9rem;font-weight:600;color:#1a1f2e;margin-bottom:4px;'>"
        f"All Audits — <span style='color:#6b7280;'>{len(filtered)} total</span></div>",
        unsafe_allow_html=True,
    )

    sub_tabs = st.tabs([
        f"All Audits  {len(filtered)}",
        f"Owned Audits  {len(owned_f)}",
        f"Indirect Coverage  {len(indirect_f)}",
    ])

    with sub_tabs[0]:
        _render_audit_table(filtered)

    with sub_tabs[1]:
        _render_audit_table(owned_f)

    with sub_tabs[2]:
        _render_audit_table(indirect_f)
