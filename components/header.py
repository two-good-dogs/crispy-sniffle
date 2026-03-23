import io
import streamlit as st
import pandas as pd
from data.mock_data import get_audits, get_issues, get_adjustments


QUARTERS = [
    "Q2 FY25 Final",
    "Q2 FY25 · Apr 30 close",
    "Q2 FY2025",
]

LIVE_QUARTER = "Q2 FY25 · Apr 30 close"


def render_header():
    """Renders the top navigation bar and snapshot banner. Returns snapshot_mode bool."""

    # ── Top bar ──────────────────────────────────────────────────────────────
    col_logo, col_view, col_q1, col_q2, col_q3, col_user = st.columns(
        [2, 2, 2, 2, 2, 1]
    )

    with col_logo:
        st.markdown(
            "<div style='font-size:1.3rem;font-weight:700;color:#1a1f2e;padding-top:6px;'>"
            "Audit<span style='color:#3b82f6;'>IQ</span></div>",
            unsafe_allow_html=True,
        )

    with col_view:
        view_mode = st.segmented_control(
            "View",
            ["Platform", "Regional"],
            key="view_mode",
            label_visibility="collapsed",
        )

    with col_q1:
        if st.button(
            "● Q2 FY25 Final",
            key="btn_q_final",
            type="secondary",
            use_container_width=True,
            help="Locked snapshot — 16 May 2025",
        ):
            st.session_state.selected_quarter = "Q2 FY25 Final"
            st.session_state.snapshot_mode = True

    with col_q2:
        btn_type = "primary" if not st.session_state.get("snapshot_mode", False) else "secondary"
        if st.button(
            "Q2 FY25 · Apr 30 close",
            key="btn_q_live",
            type=btn_type,
            use_container_width=True,
            help="Live quarter",
        ):
            st.session_state.selected_quarter = LIVE_QUARTER
            st.session_state.snapshot_mode = False

    with col_q3:
        if st.button(
            "Q2 FY2025",
            key="btn_q_fy",
            type="secondary",
            use_container_width=True,
            help="Full fiscal year view",
        ):
            st.session_state.selected_quarter = "Q2 FY2025"
            st.session_state.snapshot_mode = True

    with col_user:
        st.markdown(
            "<div style='background:#3b82f6;color:#fff;border-radius:50%;"
            "width:32px;height:32px;display:flex;align-items:center;justify-content:center;"
            "font-weight:700;font-size:0.85rem;margin-top:4px;'>PK</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Snapshot banner ───────────────────────────────────────────────────────
    snapshot_mode = st.session_state.get("snapshot_mode", False)
    selected_quarter = st.session_state.get("selected_quarter", LIVE_QUARTER)

    if snapshot_mode:
        b1, b2 = st.columns([6, 1])
        with b1:
            st.warning(
                f"⚠ Viewing snapshot: **{selected_quarter} — 16 May 2025**. "
                "Post-cutoff changes visible in Data Validations tab.",
                icon=None,
            )
        with b2:
            if st.button("← Back to Live", key="back_to_live", type="secondary"):
                st.session_state.snapshot_mode = False
                st.session_state.selected_quarter = LIVE_QUARTER
                st.rerun()

    return snapshot_mode


def render_export_button(platform: str):
    """Renders an Export button that downloads an Excel workbook."""
    audits_df = get_audits()
    issues_df = get_issues()
    adjustments = st.session_state.get("adjustments", get_adjustments())

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        audits_df.to_excel(writer, sheet_name="Audits", index=False)
        issues_df.to_excel(writer, sheet_name="Issues", index=False)
        pd.DataFrame(adjustments).to_excel(writer, sheet_name="Adjustments", index=False)
    buffer.seek(0)

    st.download_button(
        label="↓ Export",
        data=buffer,
        file_name=f"AuditIQ_{platform.replace(' ', '_')}_Q2FY25.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="export_btn",
    )
