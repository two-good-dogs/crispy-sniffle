import uuid
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data.data_interface as di


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

CHART_BG    = "rgba(0,0,0,0)"
FONT_COLOR  = "#e2e8f0"
ACCENT      = "#3b82f6"
ACCENT_DIM  = "rgba(59,130,246,0.4)"
WARN        = "#f59e0b"
DANGER      = "#ef4444"
OK          = "#22c55e"
OK_DIM      = "rgba(34,197,94,0.4)"


# ── Tiny horizontal bar helper ────────────────────────────────────────────────

def _hbar(fig, y_labels, values, colors, title, height=130):
    for i, (label, val, color) in enumerate(zip(y_labels, values, colors)):
        fig.add_trace(go.Bar(
            y=[label], x=[val], orientation="h",
            marker_color=color, showlegend=False,
            text=[f"<b>{val}</b>"], textposition="outside",
            textfont=dict(color=FONT_COLOR, size=11),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=11, color="#94a3b8"), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        margin=dict(l=0, r=40, t=28, b=0),
        height=height,
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(color=FONT_COLOR, size=10), ticksuffix="  "),
        bargap=0.35,
    )
    return fig


# ── Analytics panel ───────────────────────────────────────────────────────────

def _render_analytics(issues_df: pd.DataFrame, audits_df: pd.DataFrame, quarter: str):
    st.markdown(
        "<div style='font-size:0.72rem;font-weight:700;letter-spacing:0.08em;"
        "color:#64748b;text-transform:uppercase;margin-bottom:10px;'>"
        "Key Metrics &amp; Indicators</div>",
        unsafe_allow_html=True,
    )

    # ── Derived sets ──────────────────────────────────────────────────────────
    open_df    = issues_df[issues_df["status"].isin(["Open", "Overdue"])]
    closed_df  = issues_df[issues_df["status"] == "Closed"]
    overdue_df = issues_df[issues_df["status"] == "Overdue"]

    n_open   = len(open_df)
    n_closed = len(closed_df)

    # Simulate a prior-quarter baseline (≈15% higher open, ≈10% fewer closed)
    prior_open   = int(n_open   * 1.15)
    prior_closed = int(n_closed * 0.90)

    pct_open_chg   = round((n_open   - prior_open)   / max(prior_open,   1) * 100)
    pct_closed_chg = round((n_closed - prior_closed) / max(prior_closed, 1) * 100)

    arrow_open   = "↓" if pct_open_chg <= 0 else "↑"
    arrow_closed = "↑" if pct_closed_chg >= 0 else "↓"
    color_open   = OK    if pct_open_chg <= 0 else DANGER
    color_closed = OK    if pct_closed_chg >= 0 else DANGER

    # ── Row 1: two sparkline bar charts ──────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.78rem;font-weight:600;color:#cbd5e1;margin-bottom:2px;'>"
                f"Issues in Progress</div>"
                f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:6px;'>with Management</div>"
                f"<span style='font-size:1.4rem;font-weight:800;color:{color_open};'>"
                f"{arrow_open} {abs(pct_open_chg)}%</span>"
                f"<span style='font-size:0.7rem;color:#64748b;margin-left:6px;'>vs prior quarter</span>",
                unsafe_allow_html=True,
            )
            prior_q = "Prior Q"
            curr_q  = quarter.split()[0]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[prior_q, curr_q],
                y=[prior_open, n_open],
                marker_color=[ACCENT_DIM, ACCENT],
                text=[str(prior_open), str(n_open)],
                textposition="outside",
                textfont=dict(color=FONT_COLOR, size=10),
                showlegend=False,
            ))
            fig.update_layout(
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                margin=dict(l=0, r=0, t=4, b=0), height=90,
                xaxis=dict(tickfont=dict(color="#94a3b8", size=9)),
                yaxis=dict(visible=False), bargap=0.4,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.markdown(
                f"<div style='font-size:0.68rem;color:#64748b;line-height:1.7;'>"
                f"Newly resolved by Mgmt &nbsp;<b style='color:#e2e8f0;'>–{int(n_open*0.08)}</b><br>"
                f"Newly raised by IA &nbsp;<b style='color:#e2e8f0;'>+{int(n_open*0.05)}</b><br>"
                f"Retargeted by Mgmt &nbsp;<b style='color:#e2e8f0;'>+{int(n_open*0.03)}</b></div>",
                unsafe_allow_html=True,
            )

    with col_b:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.78rem;font-weight:600;color:#cbd5e1;margin-bottom:2px;'>"
                f"Issues to be Verified</div>"
                f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:6px;'>by IA</div>"
                f"<span style='font-size:1.4rem;font-weight:800;color:{color_closed};'>"
                f"{arrow_closed} {abs(pct_closed_chg)}%</span>"
                f"<span style='font-size:0.7rem;color:#64748b;margin-left:6px;'>vs prior quarter</span>",
                unsafe_allow_html=True,
            )
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=[prior_q, curr_q],
                y=[prior_closed, n_closed],
                marker_color=[OK_DIM, OK],
                text=[str(prior_closed), str(n_closed)],
                textposition="outside",
                textfont=dict(color=FONT_COLOR, size=10),
                showlegend=False,
            ))
            fig2.update_layout(
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                margin=dict(l=0, r=0, t=4, b=0), height=90,
                xaxis=dict(tickfont=dict(color="#94a3b8", size=9)),
                yaxis=dict(visible=False), bargap=0.4,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            st.markdown(
                f"<div style='font-size:0.68rem;color:#64748b;line-height:1.7;'>"
                f"Newly resolved by Mgmt &nbsp;<b style='color:#e2e8f0;'>+{int(n_closed*0.12)}</b><br>"
                f"Closed by IA &nbsp;<b style='color:#e2e8f0;'>+{int(n_closed*0.09)}</b><br>"
                f"Clarification requested &nbsp;<b style='color:#e2e8f0;'>–{int(n_closed*0.04)}</b></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Row 2: Tracking status by platform ───────────────────────────────────
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:0.78rem;font-weight:600;color:#cbd5e1;margin-bottom:8px;'>"
            "Issues Tracking Status</div>",
            unsafe_allow_html=True,
        )

        # Join issues → audits to get lead_group
        aid_to_group = audits_df.set_index("audit_id")["lead_group"].to_dict()
        issues_df = issues_df.copy()
        issues_df["lead_group"] = issues_df["audit_id"].map(aid_to_group).fillna("Other")

        lobs = {"CM", "INS", "WM", "PB", "BO", "CB", "RBCB"}
        fns  = {"HR", "CFO", "AML", "GC", "GRM"}

        def _bucket(g):
            if g == "CNB":   return "CNB"
            if g == "T&O":   return "T&O"
            if g in fns:     return "Functions"
            if g in lobs:    return "Platforms (excl. CNB)"
            return "Other"

        issues_df["bucket"] = issues_df["lead_group"].apply(_bucket)

        def _track(grp):
            on_track    = len(grp[grp["status"] == "Open"])
            past_orig   = len(grp[grp["status"] == "Overdue"])
            past_curr   = len(grp[(grp["status"] == "Overdue") & (grp["days_overdue"] > 14)])
            return on_track, past_orig, past_curr

        buckets = ["Platforms (excl. CNB)", "CNB", "Functions", "T&O"]
        on_tracks, past_origs, past_currs, totals = [], [], [], []
        for b in buckets:
            grp = issues_df[issues_df["bucket"] == b]
            ot, po, pc = _track(grp)
            on_tracks.append(ot); past_origs.append(po); past_currs.append(pc)
            totals.append(len(grp))

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="On Track", y=buckets, x=on_tracks, orientation="h",
            marker_color=OK, showlegend=True,
        ))
        fig3.add_trace(go.Bar(
            name="Past Original Due", y=buckets, x=past_origs, orientation="h",
            marker_color=WARN, showlegend=True,
        ))
        fig3.add_trace(go.Bar(
            name="Past Current Due", y=buckets, x=past_currs, orientation="h",
            marker_color=DANGER, showlegend=True,
        ))
        # Total labels
        for b, tot in zip(buckets, totals):
            fig3.add_annotation(
                x=max(totals) * 1.02, y=b,
                text=f"<b>{tot}</b>", showarrow=False,
                font=dict(color=FONT_COLOR, size=11), xanchor="left",
            )
        fig3.update_layout(
            barmode="stack",
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            margin=dict(l=0, r=50, t=4, b=0), height=150,
            xaxis=dict(visible=False),
            yaxis=dict(tickfont=dict(color="#94a3b8", size=10)),
            legend=dict(
                orientation="h", x=0, y=-0.12,
                font=dict(color="#94a3b8", size=9),
                bgcolor="rgba(0,0,0,0)",
            ),
            bargap=0.35,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Row 3: Expected resolution date ──────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:0.78rem;font-weight:600;color:#cbd5e1;margin-bottom:8px;'>"
            "Expected Resolution Date</div>",
            unsafe_allow_html=True,
        )
        issues_df["due_year"] = pd.to_datetime(issues_df["due_date"]).dt.year
        yr_counts = (
            issues_df[issues_df["status"].isin(["Open", "Overdue"])]
            .groupby("due_year")
            .size()
            .reset_index(name="count")
            .sort_values("due_year")
        )
        yr_labels = [f"FY{str(y)[2:]}" for y in yr_counts["due_year"]]
        yr_vals   = yr_counts["count"].tolist()
        colors_yr = [ACCENT if i < len(yr_vals) - 1 else WARN for i in range(len(yr_vals))]

        fig4 = go.Figure()
        _hbar(fig4, yr_labels, yr_vals, colors_yr, "", height=max(80, len(yr_labels) * 36))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ── Commentary (Insights) panel ───────────────────────────────────────────────

SECTIONS = ["Issue Remediation", "Reissues", "Risk Themes", "Other"]


def _render_commentary(quarter: str):
    st.markdown(
        "<div style='font-size:0.72rem;font-weight:700;letter-spacing:0.08em;"
        "color:#64748b;text-transform:uppercase;margin-bottom:10px;'>"
        "Insights</div>",
        unsafe_allow_html=True,
    )

    # Commentary stored in session state keyed by quarter
    _key = f"commentary_{quarter}"
    if _key not in st.session_state:
        st.session_state[_key] = []
    entries = st.session_state[_key]

    # ── Add new entry ─────────────────────────────────────────────────────────
    with st.expander("+ Add Commentary", expanded=len(entries) == 0):
        with st.form("commentary_form", clear_on_submit=True):
            section = st.selectbox("Section", SECTIONS, key="commentary_section")
            text    = st.text_area(
                "Commentary",
                placeholder="Add your insight or observation…",
                height=100,
                key="commentary_text",
            )
            if st.form_submit_button("Save", type="primary", use_container_width=True):
                if text.strip():
                    st.session_state[_key].append({
                        "entry_id":  str(uuid.uuid4()),
                        "quarter":   quarter,
                        "section":   section,
                        "text":      text.strip(),
                        "author":    di.CURRENT_USER,
                        "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    st.rerun()

    # ── Display entries grouped by section ────────────────────────────────────
    if not entries:
        st.markdown(
            "<div style='color:#64748b;font-size:0.82rem;font-style:italic;padding:12px 0;'>"
            "No insights recorded yet for this quarter.</div>",
            unsafe_allow_html=True,
        )
        return

    by_section: dict[str, list] = {}
    for e in entries:
        by_section.setdefault(e["section"], []).append(e)

    for section, items in by_section.items():
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:700;color:#cbd5e1;"
            f"margin:12px 0 6px 0;border-left:3px solid #3b82f6;padding-left:8px;'>"
            f"{section}</div>",
            unsafe_allow_html=True,
        )
        for e in items:
            col_text, col_del = st.columns([11, 1])
            with col_text:
                st.markdown(
                    f"<div style='font-size:0.82rem;color:#e2e8f0;line-height:1.55;"
                    f"padding:4px 0 4px 12px;'>"
                    f"• {e['text']}<br>"
                    f"<span style='font-size:0.68rem;color:#475569;'>"
                    f"{e['author']} · {e['posted_at']}</span></div>",
                    unsafe_allow_html=True,
                )
            with col_del:
                if e["author"] == di.CURRENT_USER:
                    if st.button("✕", key=f"del_{e['entry_id']}", help="Delete your entry"):
                        st.session_state[_key] = [x for x in st.session_state[_key]
                                                   if x["entry_id"] != e["entry_id"]]
                        st.rerun()


# ── Main render ───────────────────────────────────────────────────────────────

def render_issue_tracker(audits_df: pd.DataFrame, all_issues: pd.DataFrame = None):
    if all_issues is None:
        all_issues = pd.DataFrame()

    # Scope issues to the current quarter's audits
    current_audit_ids = set(audits_df["audit_id"])
    issues_df = all_issues[all_issues["audit_id"].isin(current_audit_ids)].copy()

    # Join audit name
    audit_map = audits_df.set_index("audit_id")["audit_name"].to_dict()
    issues_df["audit_name"] = issues_df["audit_id"].map(audit_map).fillna("Unknown")

    quarter = st.session_state.get("selected_quarter_filter", "Q1 2026")

    # ── Metric summary ────────────────────────────────────────────────────────
    open_issues   = issues_df[issues_df["status"].isin(["Open", "Overdue"])]
    overdue_issues = issues_df[issues_df["status"] == "Overdue"]
    high_issues   = issues_df[issues_df["severity"] == "High"]

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
            "Severity", ["High", "Medium", "Low"],
            placeholder="All Severities", key="issue_sev_filter",
            label_visibility="collapsed",
        )
    with f3:
        status_filter = st.multiselect(
            "Status", ["Open", "Overdue", "Closed"],
            placeholder="All Statuses", key="issue_status_filter",
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
    display_cols = ["issue_id", "audit_name", "title", "severity", "status",
                    "due_date", "remediation_owner", "days_overdue"]
    display_df = filtered[display_cols].copy()
    display_df["due_date"] = display_df["due_date"].dt.strftime("%d %b %Y")
    display_df.columns = ["Issue ID", "Audit", "Title", "Severity", "Status",
                           "Due Date", "Owner", "Days Overdue"]

    styled = (
        display_df.style
        .applymap(lambda v: SEV_COLORS.get(v, ""),    subset=["Severity"])
        .applymap(lambda v: STATUS_COLORS.get(v, ""), subset=["Status"])
        .applymap(
            lambda v: "color:#dc2626;font-weight:700;" if isinstance(v, (int, float)) and v > 0 else "",
            subset=["Days Overdue"],
        )
        .set_properties(**{"font-size": "0.82rem"})
        .set_table_styles([{"selector": "th", "props": [
            ("font-size", "0.78rem"), ("color", "#6b7280"),
            ("font-weight", "600"), ("text-transform", "uppercase"),
            ("letter-spacing", "0.04em"),
        ]}])
    )

    st.markdown(
        f"<div style='font-size:0.9rem;font-weight:600;color:#1a1f2e;margin-bottom:6px;'>"
        f"Issues — <span style='color:#6b7280;'>{len(filtered)} shown</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=380)

    # ── Insights + Analytics section ──────────────────────────────────────────
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.divider()

    left_col, right_col = st.columns([1, 1.5])

    with left_col:
        _render_commentary(quarter)

    with right_col:
        _render_analytics(issues_df, audits_df, quarter)
