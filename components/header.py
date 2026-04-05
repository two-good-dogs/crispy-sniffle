import streamlit as st
import pandas as pd
from data.mock_data import get_issues, get_adjustments
from utils.excel_export import ALL_SHEETS, build_export_workbook


LIVE_QUARTER = "Q2 FY25 · Apr 30 close"


def render_header():
    """Renders the snapshot banner. Returns snapshot_mode bool."""
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


@st.dialog("Export to Excel", width="large")
def _export_dialog(platform: str, audits_df: pd.DataFrame,
                   issues_df: pd.DataFrame, adjustments: list, quarter: str):
    st.markdown(
        "<p style='color:#6b7280;font-size:0.9rem;margin-top:-8px;'>"
        "Select which worksheets to include in the workbook.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    selected = {}
    for i, sheet in enumerate(ALL_SHEETS):
        col = col1 if i % 2 == 0 else col2
        with col:
            selected[sheet] = st.checkbox(sheet, value=True, key=f"export_sheet_{i}")

    chosen = [s for s, v in selected.items() if v]

    st.divider()

    m1, m2, m3 = st.columns(3)
    m1.metric("Audits included", len(audits_df))
    m2.metric("Issues included", len(issues_df))
    m3.metric("Sheets selected", len(chosen))

    st.divider()

    if not chosen:
        st.warning("Select at least one worksheet.")
        return

    file_name = f"AuditIQ_{platform.replace(' ', '_')}_{quarter.replace(' ', '_')}.xlsx"

    with st.spinner("Building workbook…"):
        wb_bytes = build_export_workbook(
            audits_df=audits_df,
            issues_df=issues_df,
            adjustments=adjustments,
            platform=platform,
            quarter=quarter,
            include_sheets=chosen,
        )

    st.download_button(
        label="⬇ Download Excel Workbook",
        data=wb_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
        key="export_download_btn",
    )

    st.caption(
        f"Workbook includes: {', '.join(chosen)}. "
        "Charts and color-coded ratings are embedded in each sheet."
    )


def render_export_button(platform: str, all_audits: pd.DataFrame):
    _quarter = st.session_state.get("selected_quarter_filter", "Q1 2026")
    issues_df = get_issues()
    issues_df = issues_df[issues_df["audit_id"].isin(all_audits["audit_id"])]
    adjustments = st.session_state.get("adjustments", get_adjustments())

    if st.button("↓ Export", key="export_btn", use_container_width=True):
        _export_dialog(platform, all_audits, issues_df, adjustments, _quarter)
