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
    _card_s = "background:#0d1117;border-radius:10px;padding:20px 22px 16px;position:relative;overflow:hidden;flex:1;"
    _label_s = "font-family:'IBM Plex Mono',monospace;font-size:0.6rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#6b7280;margin-bottom:8px;"
    _num_s   = "font-family:'Barlow Condensed',sans-serif;font-size:3.8rem;font-weight:700;line-height:0.88;margin-bottom:10px;letter-spacing:-0.01em;"
    _hr_s    = "border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 10px 0;"
    _meta_s  = "font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#4b5563;line-height:1.8;"

    def _badge(text, bg, color, border):
        return (
            f"<span style='display:inline-block;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.58rem;font-weight:600;letter-spacing:0.1em;padding:2px 9px;"
            f"border-radius:3px;background:{bg};color:{color};border:1px solid {border};"
            f"margin-bottom:12px;'>{text}</span>"
        )

    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
          @keyframes kpi-rise {{
            from {{ opacity:0; transform:translateY(10px); }}
            to   {{ opacity:1; transform:translateY(0); }}
          }}
        </style>

        <div style="display:flex;gap:12px;margin-bottom:16px;">

          <div style="{_card_s}border-top:3px solid #34d399;animation:kpi-rise .45s cubic-bezier(.22,1,.36,1) both;animation-delay:0s;">
            <div style="{_label_s}">Owned Coverage</div>
            <div style="{_num_s}color:#6ee7b7;">{owned_count}</div>
            {_badge("OWNED", "rgba(52,211,153,.13)", "#6ee7b7", "rgba(52,211,153,.28)")}
            <hr style="{_hr_s}">
            <div style="{_meta_s}">↳ Lead Audit Group field</div>
          </div>

          <div style="{_card_s}border-top:3px solid #60a5fa;animation:kpi-rise .45s cubic-bezier(.22,1,.36,1) both;animation-delay:.07s;">
            <div style="{_label_s}">Indirect Coverage</div>
            <div style="{_num_s}color:#93c5fd;">{indirect_count}</div>
            {_badge("INDIRECT", "rgba(96,165,250,.13)", "#93c5fd", "rgba(96,165,250,.28)")}
            <hr style="{_hr_s}">
            <div style="{_meta_s}">↳ Impacted Platform field</div>
          </div>

          <div style="{_card_s}border-top:3px solid #f59e0b;animation:kpi-rise .45s cubic-bezier(.22,1,.36,1) both;animation-delay:.14s;">
            <div style="{_label_s}">Total Footprint</div>
            <div style="{_num_s}color:#fde68a;">{total_count}</div>
            {_badge("DE-DUPLICATED", "rgba(245,158,11,.13)", "#fde68a", "rgba(245,158,11,.28)")}
            <hr style="{_hr_s}">
            <div style="{_meta_s}">
              Owned&nbsp;<strong style="color:#9ca3af;">{owned_count}</strong>
              &nbsp;<span style="color:#1f2937;">·</span>&nbsp;
              Indirect&nbsp;<strong style="color:#9ca3af;">{indirect_count}</strong>
            </div>
          </div>

          <div style="{_card_s}border-top:3px solid #f87171;animation:kpi-rise .45s cubic-bezier(.22,1,.36,1) both;animation-delay:.21s;">
            <div style="{_label_s}">Open Issues</div>
            <div style="{_num_s}color:#fca5a5;">{all_issues}</div>
            {_badge("ISSUES", "rgba(248,113,113,.13)", "#fca5a5", "rgba(248,113,113,.28)")}
            <hr style="{_hr_s}">
            <div style="{_meta_s}">
              ↳ Remediation Owner field<br>
              Overdue&nbsp;<strong style="color:#f87171;">{overdue_count}</strong>
              &nbsp;<span style="color:#1f2937;">·</span>&nbsp;
              Out-of-scope&nbsp;<strong style="color:#9ca3af;">{out_of_scope_count}</strong>
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
