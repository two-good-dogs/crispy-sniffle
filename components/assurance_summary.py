import streamlit as st
import pandas as pd


# ── Helpers ───────────────────────────────────────────────────────────────────

RATING_COLORS = {"SAT": "#4a7c59", "RI": "#b8860b", "UNSAT": "#c0392b", "NA": "#6b7280"}
MARC_COLORS = {
    "Developed": "#1a6b3c",
    "Substantially Developed": "#2e8b57",
    "Partially Developed": "#d97706",
    "Underdeveloped": "#dc2626",
}
LEVEL_COLORS = {"High": "#dc2626", "Medium": "#2563eb", "Low": "#6b7280"}


def _bar(value: int, max_val: int, color: str, height: int = 16) -> str:
    pct = min(100, int(value / max_val * 100)) if max_val else 0
    min_w = "4px" if pct > 0 else "0"
    return (
        f"<div style='background:#d1d5db;border-radius:4px;height:{height}px;"
        f"width:100%;margin:4px 0;'>"
        f"<div style='background:{color};width:{pct}%;height:100%;border-radius:4px;"
        f"min-width:{min_w};'></div>"
        f"</div>"
    )


def _metric_row(label: str, value: int, max_val: int, color: str) -> str:
    bar = _bar(value, max_val, color)
    return (
        f"<div style='margin:8px 0;'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
        f"<span style='font-size:0.82rem;color:#374151;font-weight:500;'>{label}</span>"
        f"<span style='font-weight:700;font-size:0.9rem;color:{color};'>{value}</span>"
        f"</div>"
        f"{bar}"
        f"</div>"
    )


def _section_header(left_text: str, right_badge: str, badge_color: str = "#1e40af") -> None:
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"background:#1f2937;color:white;padding:10px 16px;border-radius:6px 6px 0 0;"
        f"margin-bottom:0;'>"
        f"<span style='font-weight:700;font-size:0.95rem;letter-spacing:0.03em;'>{left_text}</span>"
        f"<span style='background:{badge_color};color:white;border-radius:4px;"
        f"padding:3px 12px;font-size:0.85rem;font-weight:700;'>{right_badge}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_assurance_summary(all_audits: pd.DataFrame, all_issues: pd.DataFrame = None, snapshot_mode: bool = False):
    st.markdown("### Assurance Summary")

    if all_audits.empty:
        st.info("No audit data available for the selected filters.")
        return

    # ── Pre-compute all metrics ───────────────────────────────────────────────

    completed = all_audits[all_audits["status"] == "Complete"]
    published = completed[completed["report_status"] == "Published"]

    # Core project counts
    n_audit      = len(published[published["audit_type"] == "Owned Audit"])
    n_inscope_ae = len(published[published["audit_type"] == "In-Scope AE"])
    n_advisory   = len(published[published["audit_type"] == "Indirect"])
    n_total_core = n_audit + n_inscope_ae

    # Report ratings (Owned + AE only — not Indirect)
    core_published = published[published["audit_type"].isin(["Owned Audit", "In-Scope AE"])]
    n_sat      = len(core_published[core_published["current_rating"] == "SAT"])
    n_ri       = len(core_published[core_published["current_rating"] == "RI"])
    n_unsat    = len(core_published[core_published["current_rating"] == "UNSAT"])
    n_na       = len(core_published[core_published["current_rating"] == "NA"])
    max_rating = max(n_sat, n_ri, n_unsat, n_na, 1)

    # MARC ratings (Owned + AE completed, where marc_rating != N/A)
    marc_df = core_published[core_published["marc_rating"] != "N/A"]
    n_developed   = len(marc_df[marc_df["marc_rating"] == "Developed"])
    n_sub_dev     = len(marc_df[marc_df["marc_rating"] == "Substantially Developed"])
    n_part_dev    = len(marc_df[marc_df["marc_rating"] == "Partially Developed"])
    n_underdev    = len(marc_df[marc_df["marc_rating"] == "Underdeveloped"])
    max_marc      = max(n_developed, n_sub_dev, n_part_dev, n_underdev, 1)

    # Footnote: per-platform rating breakdown
    footnote_parts = []
    for grp, grp_df in core_published.groupby("lead_group"):
        ratings = grp_df["current_rating"].value_counts().to_dict()
        parts = [f"{v} {k}" for k, v in ratings.items() if k not in ("NA",)]
        if parts:
            footnote_parts.append(f"{grp} ({', '.join(parts)})")
    footnote = "*" + "; ".join(footnote_parts[:6]) + ("..." if len(footnote_parts) > 6 else "") if footnote_parts else ""

    # Issues — filter by audit IDs in view
    if all_issues is None:
        all_issues = pd.DataFrame()
    audit_ids = set(all_audits["audit_id"].tolist())
    issues = all_issues[all_issues["audit_id"].isin(audit_ids)].copy()

    # Level mapping: High → L1, Medium → L2
    issues["level"] = issues["severity"].map({"High": "L1", "Medium": "L2", "Low": "L2"})

    # Newly raised (from completed audits this period)
    completed_ids = set(completed["audit_id"].tolist())
    new_issues = issues[issues["audit_id"].isin(completed_ids)]
    n_new_l1 = len(new_issues[new_issues["level"] == "L1"])
    n_new_l2 = len(new_issues[new_issues["level"] == "L2"])
    n_new_total = n_new_l1 + n_new_l2

    # Self-identified subset
    si = new_issues[new_issues.get("self_identified", False) == True] if "self_identified" in new_issues.columns else new_issues.iloc[0:0]
    n_si_l1 = len(si[si["level"] == "L1"])
    n_si_l2 = len(si[si["level"] == "L2"])

    # Open issues
    open_issues = issues[issues["status"].isin(["Open", "In Progress"])]
    overdue_issues = issues[issues["status"] == "Overdue"]
    n_open = len(open_issues)
    n_overdue = len(overdue_issues)
    max_open = max(n_open, n_overdue, 1)

    # ── Section 1: Assurance Activities ──────────────────────────────────────

    _section_header(
        "Assurance Activities & Output",
        f"{n_total_core} Core Projects Completed*",
        badge_color="#166534",
    )

    with st.container(border=True):
        col1, col2, col3 = st.columns(3, gap="large")

        # LEFT: Core Projects
        with col1:
            st.markdown("**Core Projects**")
            max_core = max(n_audit, n_inscope_ae, n_advisory, 1)
            st.markdown(
                _metric_row("Audit", n_audit, max_core, "#1e40af")
                + _metric_row("In-Scope AE", n_inscope_ae, max_core, "#7c3aed")
                + _metric_row("Advisory", n_advisory, max_core, "#6b7280"),
                unsafe_allow_html=True,
            )

        # MIDDLE: Report Ratings
        with col2:
            st.markdown("**Report Ratings**")
            st.markdown(
                _metric_row("SAT", n_sat, max_rating, RATING_COLORS["SAT"])
                + _metric_row("RI", n_ri, max_rating, RATING_COLORS["RI"])
                + _metric_row("UNSAT", n_unsat, max_rating, RATING_COLORS["UNSAT"])
                + _metric_row("Not Rated", n_na, max_rating, RATING_COLORS["NA"]),
                unsafe_allow_html=True,
            )

        # RIGHT: MARC Ratings
        with col3:
            st.markdown("**MARC Ratings**")
            st.markdown(
                _metric_row("Developed", n_developed, max_marc, MARC_COLORS["Developed"])
                + _metric_row("Substantially Dev.", n_sub_dev, max_marc, MARC_COLORS["Substantially Developed"])
                + _metric_row("Partially Dev.", n_part_dev, max_marc, MARC_COLORS["Partially Developed"])
                + _metric_row("Underdeveloped", n_underdev, max_marc, MARC_COLORS["Underdeveloped"]),
                unsafe_allow_html=True,
            )

    if footnote:
        st.caption(footnote)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ── Section 2: Issues ─────────────────────────────────────────────────────

    _section_header(
        "Issues",
        f"{n_new_total} Issues Raised",
        badge_color="#991b1b",
    )

    with st.container(border=True):
        col1, col2, col3 = st.columns(3, gap="large")
        max_new = max(n_new_l1, n_new_l2, 1)

        # LEFT: Newly Raised
        with col1:
            st.markdown("**Newly Raised**")
            st.markdown(
                _metric_row("Level 1", n_new_l1, max_new, "#dc2626")
                + _metric_row("Level 2", n_new_l2, max_new, "#2563eb"),
                unsafe_allow_html=True,
            )

        # MIDDLE: Self-Identified
        with col2:
            st.markdown("**Self-Identified** *(of newly raised)*")
            max_si = max(n_si_l1, n_si_l2, 1)
            st.markdown(
                _metric_row("Level 1", n_si_l1, max_si, "#dc2626")
                + _metric_row("Level 2", n_si_l2, max_si, "#2563eb"),
                unsafe_allow_html=True,
            )

        # RIGHT: Open Issues
        with col3:
            st.markdown("**Open Issues**")
            st.markdown(
                _metric_row("In Progress", n_open, max_open, "#d97706")
                + _metric_row("Overdue", n_overdue, max_open, "#dc2626"),
                unsafe_allow_html=True,
            )
            # Level legend
            st.markdown(
                "<div style='margin-top:12px;font-size:0.75rem;color:#6b7280;'>"
                "<span style='background:#dc2626;color:white;border-radius:2px;"
                "padding:1px 6px;margin-right:6px;'>L1</span>High &nbsp;"
                "<span style='background:#2563eb;color:white;border-radius:2px;"
                "padding:1px 6px;margin-right:6px;'>L2</span>Medium"
                "</div>",
                unsafe_allow_html=True,
            )
