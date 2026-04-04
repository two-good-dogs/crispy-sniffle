import streamlit as st
from data.mock_data import get_platforms, get_audits, compute_field_completeness


def render_sidebar(unread_count: int = 0):
    platforms = get_platforms()
    audits_df = get_audits()

    with st.sidebar:
        # ── Logo + notification badge row ─────────────────────────────────────
        logo_col, notif_col = st.columns([3, 1])
        with logo_col:
            st.markdown(
                "<div style='font-size:1.4rem;font-weight:700;color:#1a1f2e;padding:8px 0 4px 0;'>"
                "Audit<span style='color:#3b82f6;'>IQ</span></div>",
                unsafe_allow_html=True,
            )
        with notif_col:
            if unread_count > 0:
                st.markdown(
                    f"<div style='background:#dc2626;color:#fff;border-radius:50%;"
                    f"width:26px;height:26px;display:flex;align-items:center;"
                    f"justify-content:center;font-weight:700;font-size:0.75rem;"
                    f"margin-top:10px;' title='{unread_count} unread message(s)'>"
                    f"🔔{unread_count}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='color:#9ca3af;font-size:1rem;margin-top:12px;' "
                    "title='No unread messages'>🔔</div>",
                    unsafe_allow_html=True,
                )

        if unread_count:
            _notif_text = (
                f"<span style='color:#dc2626;font-weight:600;'>"
                f"{unread_count} unread message(s)</span>"
            )
        else:
            _notif_text = "No unread messages"
        st.markdown(
            f"<div style='font-size:0.72rem;color:#9ca3af;margin-bottom:8px;'>{_notif_text}</div>",
            unsafe_allow_html=True,
        )

        # ── Quarter filter ────────────────────────────────────────────────────
        st.selectbox(
            "Quarter",
            ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"],
            key="selected_quarter_filter",
            label_visibility="visible",
        )

        # ── Enterprise view toggle ─────────────────────────────────────────────
        enterprise_view = st.toggle(
            "Enterprise View",
            key="enterprise_view",
            help="Show data for all platforms and regions",
        )
        if enterprise_view:
            st.markdown(
                "<div style='font-size:0.72rem;color:#2563eb;font-weight:600;"
                "background:#dbeafe;border-radius:4px;padding:3px 8px;margin-bottom:8px;'>"
                "All platforms · All regions</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div class='sidebar-section-header'>Lines of Business</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "lob",
            platforms["lines_of_business"],
            selection_mode="multi",
            key="selected_platforms",
            label_visibility="collapsed",
            disabled=enterprise_view,
        )

        st.markdown(
            "<div class='sidebar-section-header'>Functions</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "fn",
            platforms["functions"],
            selection_mode="multi",
            key="selected_functions",
            label_visibility="collapsed",
            disabled=enterprise_view,
        )

        st.markdown(
            "<div class='sidebar-section-header'>T&O</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "tech",
            platforms["technology"],
            selection_mode="multi",
            key="selected_technology",
            label_visibility="collapsed",
            disabled=enterprise_view,
        )

        st.markdown(
            "<div class='sidebar-section-header'>Regions</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "region",
            platforms["regions"],
            selection_mode="multi",
            key="selected_regions",
            label_visibility="collapsed",
            disabled=enterprise_view,
        )

        st.divider()

        # Field completeness
        completeness = compute_field_completeness(audits_df)
        pct = int(completeness * 100)
        st.markdown(
            f"<div class='completeness-label'>Field Completeness</div>",
            unsafe_allow_html=True,
        )
        st.progress(completeness)

        below_threshold = pct < 90
        color = "#dc2626" if below_threshold else "#16a34a"
        threshold_label = "Below 90%" if below_threshold else "On track"
        st.markdown(
            f"<div style='font-size:0.75rem;color:{color};font-weight:600;'>"
            f"{pct}% — {threshold_label}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.7rem;color:#9ca3af;margin-top:2px;'>"
            "Impacted Platform 70% · AE Role Type 85%</div>",
            unsafe_allow_html=True,
        )
