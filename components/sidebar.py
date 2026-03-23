import streamlit as st
from data.mock_data import get_platforms, get_audits, compute_field_completeness


def render_sidebar():
    platforms = get_platforms()
    audits_df = get_audits()

    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.4rem;font-weight:700;color:#1a1f2e;padding:8px 0 16px 0;'>"
            "Audit<span style='color:#3b82f6;'>IQ</span></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='sidebar-section-header'>Lines of Business</div>",
            unsafe_allow_html=True,
        )
        lob_choice = st.radio(
            "lob",
            platforms["lines_of_business"],
            key="selected_platform",
            label_visibility="collapsed",
        )

        st.markdown(
            "<div class='sidebar-section-header'>Functions</div>",
            unsafe_allow_html=True,
        )
        fn_choice = st.radio(
            "fn",
            ["(none)"] + platforms["functions"],
            key="selected_function",
            label_visibility="collapsed",
        )

        st.markdown(
            "<div class='sidebar-section-header'>Technology</div>",
            unsafe_allow_html=True,
        )
        tech_choice = st.radio(
            "tech",
            ["(none)"] + platforms["technology"],
            key="selected_technology",
            label_visibility="collapsed",
        )

        st.markdown(
            "<div class='sidebar-section-header'>Regions</div>",
            unsafe_allow_html=True,
        )
        region_choice = st.radio(
            "region",
            ["(all)"] + platforms["regions"],
            key="selected_region_nav",
            label_visibility="collapsed",
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
