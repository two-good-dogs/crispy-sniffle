import streamlit as st
import pandas as pd
from data.mock_data import get_issues


SEV_COLORS = {
    "High":   "background-color:#fee2e2;color:#991b1b;border-radius:10px;padding:2px 8px;font-weight:600;",
    "Medium": "background-color:#fef3c7;color:#92400e;border-radius:10px;padding:2px 8px;font-weight:600;",
    "Low":    "background-color:#d1fae5;color:#065f46;border-radius:10px;padding:2px 8px;font-weight:600;",
}

STATUS_COLORS = {
    "Open":    "background-color:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 8px;",
    "Overdue": "background-color:#fee2e2;color:#991b1b;border-radius:10px;padding:2px 8px;font-weight:600;",
    "Closed":  "background-color:#f3f4f6;color:#6b7280;border-radius:10px;padding:2px 8px;",
}


def render_issue_tracker(audits_df: pd.DataFrame):
    issues_df = get_issues()

    # Join audit name
    audit_map = audits_df.set_index("audit_id")["audit_name"].to_dict()
    issues_df["audit_name"] = issues_df["audit_id"].map(audit_map).fillna("Unknown")

    # ── Metric summary ────────────────────────────────────────────────────────
    open_issues = issues_df[issues_df["status"].isin(["Open", "Overdue"])]
    overdue_issues = issues_df[issues_df["status"] == "Overdue"]
    high_issues = issues_df[issues_df["severity"] == "High"]

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.75rem;font-weight:600;color:#6b7280;text-transform:uppercase;'>Open Issues</div>"
                f"<div style='font-size:2rem;font-weight:700;color:#1a1f2e;'>{len(open_issues)}</div>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.75rem;font-weight:600;color:#6b7280;text-transform:uppercase;'>Overdue</div>"
                f"<div style='font-size:2rem;font-weight:700;color:#dc2626;'>{len(overdue_issues)}</div>",
                unsafe_allow_html=True,
            )
    with c3:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.75rem;font-weight:600;color:#6b7280;text-transform:uppercase;'>High Severity</div>"
                f"<div style='font-size:2rem;font-weight:700;color:#92400e;'>{len(high_issues)}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        search = st.text_input(
            "Search issues",
            placeholder="Search by issue title or audit name…",
            key="issue_search",
            label_visibility="collapsed",
        )
    with f2:
        sev_filter = st.multiselect(
            "Severity",
            ["High", "Medium", "Low"],
            placeholder="All Severities",
            key="issue_sev_filter",
            label_visibility="collapsed",
        )
    with f3:
        status_filter = st.multiselect(
            "Status",
            ["Open", "Overdue", "Closed"],
            placeholder="All Statuses",
            key="issue_status_filter",
            label_visibility="collapsed",
        )

    # Apply filters
    filtered = issues_df.copy()
    if search:
        filtered = filtered[
            filtered["title"].str.contains(search, case=False, na=False) |
            filtered["audit_name"].str.contains(search, case=False, na=False)
        ]
    if sev_filter:
        filtered = filtered[filtered["severity"].isin(sev_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    # ── Table ─────────────────────────────────────────────────────────────────
    display_cols = ["issue_id", "audit_name", "title", "severity", "status", "due_date", "remediation_owner", "days_overdue"]
    display_df = filtered[display_cols].copy()
    display_df["due_date"] = display_df["due_date"].dt.strftime("%d %b %Y")
    display_df.columns = ["Issue ID", "Audit", "Title", "Severity", "Status", "Due Date", "Owner", "Days Overdue"]

    def _style_sev(val):
        return SEV_COLORS.get(val, "")

    def _style_status(val):
        return STATUS_COLORS.get(val, "")

    def _style_overdue(val):
        if isinstance(val, (int, float)) and val > 0:
            return "color:#dc2626;font-weight:700;"
        return ""

    styled = (
        display_df.style
        .applymap(_style_sev, subset=["Severity"])
        .applymap(_style_status, subset=["Status"])
        .applymap(_style_overdue, subset=["Days Overdue"])
        .set_properties(**{"font-size": "0.82rem"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("font-size", "0.78rem"), ("color", "#6b7280"),
                ("font-weight", "600"), ("text-transform", "uppercase"),
                ("letter-spacing", "0.04em"),
            ]},
        ])
    )

    st.markdown(
        f"<div style='font-size:0.9rem;font-weight:600;color:#1a1f2e;margin-bottom:6px;'>"
        f"Issues — <span style='color:#6b7280;'>{len(filtered)} shown</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)
