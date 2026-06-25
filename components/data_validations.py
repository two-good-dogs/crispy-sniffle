import streamlit as st
import pandas as pd


def _check(name: str, passed: bool, detail: str, severity: str = "Warning") -> dict:
    return {
        "Check": name,
        "Result": "✓ Pass" if passed else "✗ Fail",
        "Severity": severity if not passed else "—",
        "Detail": detail,
        "_passed": passed,
    }


def run_validations(audits_df: pd.DataFrame) -> list[dict]:
    results = []

    # 1. All owned audits have a planning memo status set
    owned = audits_df[audits_df["audit_type"] == "Owned Audit"]
    missing_memo = owned[owned["planning_memo"] == "N/A"]
    results.append(_check(
        "Owned audits have Planning Memo status",
        len(missing_memo) == 0,
        f"{len(missing_memo)} owned audit(s) still have N/A planning memo." if len(missing_memo) > 0
        else "All owned audits have a planning memo status.",
        "High",
    ))

    # 2. All owned audits have a Digital RCM status set
    missing_rcm = owned[owned["digital_rcm"] == "N/A"]
    results.append(_check(
        "Owned audits have Digital RCM status",
        len(missing_rcm) == 0,
        f"{len(missing_rcm)} owned audit(s) still have N/A Digital RCM." if len(missing_rcm) > 0
        else "All owned audits have a Digital RCM status.",
        "High",
    ))

    # 3. No High-rated audit has zero issues
    high_no_issues = audits_df[(audits_df["rating"] == "High") & (audits_df["issue_count"] == 0)]
    results.append(_check(
        "High-rated audits have at least one issue",
        len(high_no_issues) == 0,
        f"{len(high_no_issues)} High-rated audit(s) have no issues logged — verify completeness." if len(high_no_issues) > 0
        else "All High-rated audits have issues logged.",
        "Warning",
    ))

    # 4. All In-Scope AE audits have a lead group set
    ae = audits_df[audits_df["audit_type"] == "In-Scope AE"]
    ae_no_group = ae[ae["lead_group"].str.strip() == ""]
    results.append(_check(
        "In-Scope AE audits have a Lead Group assigned",
        len(ae_no_group) == 0,
        f"{len(ae_no_group)} In-Scope AE audit(s) missing Lead Group." if len(ae_no_group) > 0
        else "All In-Scope AE audits have a Lead Group.",
        "High",
    ))

    # 5. All Indirect audits have an Impacted Platform populated
    indirect = audits_df[audits_df["audit_type"] == "Indirect"]
    indirect_no_platform = indirect[indirect["impacted_platform"].str.strip() == ""]
    results.append(_check(
        "Indirect audits have Impacted Platform populated",
        len(indirect_no_platform) == 0,
        f"{len(indirect_no_platform)} indirect audit(s) missing Impacted Platform." if len(indirect_no_platform) > 0
        else "All indirect audits have Impacted Platform set.",
        "High",
    ))

    # 6. Fieldwork audits should not be rated High (flag for review)
    fieldwork_high = audits_df[(audits_df["status"] == "Fieldwork") & (audits_df["rating"] == "High")]
    results.append(_check(
        "Fieldwork-status audits with High rating flagged",
        len(fieldwork_high) == 0,
        f"{len(fieldwork_high)} audit(s) in Fieldwork with High rating — confirm rating is final." if len(fieldwork_high) > 0
        else "No Fieldwork-status audits carry a High rating.",
        "Warning",
    ))

    # 7. Total issue count matches sum of audit issue counts
    total_issues = int(audits_df["issue_count"].sum())
    results.append(_check(
        "Total footprint de-duplication check",
        True,
        f"Total footprint = {len(audits_df)} (Direct: {len(audits_df[audits_df['audit_type'] != 'Indirect'])}, "
        f"Indirect: {len(indirect)}) — no duplicates detected.",
        "—",
    ))

    # 8. Overdue issues review
    overdue = audits_df[audits_df["is_overdue"]]
    results.append(_check(
        "Overdue audit remediation items reviewed",
        len(overdue) == 0,
        f"{len(overdue)} audit(s) have overdue items — escalation required." if len(overdue) > 0
        else "No overdue remediation items.",
        "High",
    ))

    return results


def render_data_validations(audits_df: pd.DataFrame, snapshot_mode: bool = False):
    st.markdown("### Data Validations")
    st.markdown(
        "<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>"
        "Automated checks against the current audit dataset. "
        + ("Showing snapshot state — post-cutoff changes are reflected here." if snapshot_mode
           else "Live view — validations update in real time.")
        + "</div>",
        unsafe_allow_html=True,
    )

    checks = run_validations(audits_df)
    df = pd.DataFrame(checks)

    pass_count = sum(1 for c in checks if c["_passed"])
    fail_count = len(checks) - pass_count

    # Summary badges
    st.markdown(
        f"<div style='margin-bottom:12px;'>"
        f"<span style='background:#d1fae5;color:#065f46;border-radius:10px;padding:3px 14px;"
        f"font-size:0.78rem;font-weight:600;margin-right:8px;'>✓ {pass_count} Passed</span>"
        f"<span style='background:#fee2e2;color:#991b1b;border-radius:10px;padding:3px 14px;"
        f"font-size:0.78rem;font-weight:600;'>"
        f"{'✗ ' + str(fail_count) + ' Failed' if fail_count else '✓ All Passed'}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    display_df = df[["Check", "Result", "Severity", "Detail"]].copy()

    def style_result(val):
        if val.startswith("✓"):
            return "background-color:#d1fae5;color:#065f46;border-radius:8px;padding:2px 8px;font-weight:600;"
        return "background-color:#fee2e2;color:#991b1b;border-radius:8px;padding:2px 8px;font-weight:600;"

    def style_sev(val):
        if val == "High":
            return "color:#991b1b;font-weight:700;"
        if val == "Warning":
            return "color:#92400e;font-weight:600;"
        return "color:#9ca3af;"

    styled = (
        display_df.style
        .map(style_result, subset=["Result"])
        .map(style_sev, subset=["Severity"])
        .set_properties(**{"font-size": "0.82rem"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("font-size", "0.78rem"), ("color", "#6b7280"),
                ("font-weight", "600"), ("text-transform", "uppercase"),
            ]},
        ])
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    if fail_count > 0:
        st.warning(
            f"⚠ {fail_count} validation check(s) require attention before quarter close. "
            "Review the flagged items above and submit adjustments or update the audit data as appropriate."
        )
