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
    """Renders the snapshot banner. Returns snapshot_mode bool."""

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
    _quarter = st.session_state.get("selected_quarter_filter", "Q1 2026")
    audits_df = get_audits()
    audits_df = audits_df[audits_df["quarter"] == _quarter]
    issues_df = get_issues()
    issues_df = issues_df[issues_df["audit_id"].isin(audits_df["audit_id"])]
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
