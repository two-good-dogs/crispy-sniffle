import streamlit as st
import pandas as pd
import data.data_interface as di


def render_sidebar(unread_count: int = 0, platforms: dict = None, audits_df: pd.DataFrame = None):
    if platforms is None:
        platforms = {"lines_of_business": [], "regions": []}

    with st.sidebar:
        # ── Logo + notification badge ─────────────────────────────────────────
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

        _notif_text = (
            f"<span style='color:#dc2626;font-weight:600;'>{unread_count} unread message(s)</span>"
            if unread_count else "No unread messages"
        )
        st.markdown(
            f"<div style='font-size:0.72rem;color:#9ca3af;margin-bottom:8px;'>{_notif_text}</div>",
            unsafe_allow_html=True,
        )

        # ── Quarter filter ────────────────────────────────────────────────────
        _quarters = sorted(
            audits_df["quarter"].dropna().unique().tolist()
        ) if audits_df is not None and "quarter" in audits_df.columns else ["Q1 2026", "Q2 2026"]

        st.selectbox(
            "Quarter",
            _quarters,
            key="selected_quarter_filter",
            label_visibility="visible",
        )

        # ── Enterprise view toggle ────────────────────────────────────────────
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

        # ── Lines of Business ─────────────────────────────────────────────────
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

        # ── Regions ───────────────────────────────────────────────────────────
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

        # ── Field completeness ────────────────────────────────────────────────
        _df = audits_df if audits_df is not None else pd.DataFrame()
        completeness = di.compute_field_completeness(_df)
        pct = int(completeness * 100)
        st.markdown(
            "<div class='completeness-label'>Field Completeness</div>",
            unsafe_allow_html=True,
        )
        st.progress(completeness)
        color = "#dc2626" if pct < 90 else "#16a34a"
        label = "Below 90%" if pct < 90 else "On track"
        st.markdown(
            f"<div style='font-size:0.75rem;color:{color};font-weight:600;'>"
            f"{pct}% — {label}</div>",
            unsafe_allow_html=True,
        )
