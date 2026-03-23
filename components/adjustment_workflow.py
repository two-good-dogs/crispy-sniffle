import streamlit as st
import pandas as pd
from datetime import date
from data.mock_data import get_adjustments


ADJ_TYPES = [
    "Type 1 – Tag Correction",
    "Type 2 – Coverage Claim",
]

FIELDS = [
    "Lead Audit Group",
    "Scope Platform",
    "Impacted Platform",
    "Regions in Scope",
    "AE (named individual)",
    "Other",
]

REASON_CODES = [
    "SC – Scope Clarification",
    "DC – Data Correction",
    "MA – Methodology Alignment",
    "PD – Portfolio Decision",
    "OT – Other (mandatory note)",
]

STATUS_STYLE = {
    "Approved": "background:#d1fae5;color:#065f46;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:600;",
    "Pending":  "background:#fef3c7;color:#92400e;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:600;",
    "Rejected": "background:#fee2e2;color:#991b1b;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:600;",
}

TYPE_STYLE = {
    "Type 1 – Tag Correction": "background:#ede9fe;color:#5b21b6;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:600;",
    "Type 2 – Coverage Claim": "background:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:600;",
}


def _next_adj_id(adjustments: list) -> str:
    if not adjustments:
        return "ADJ-001"
    ids = [int(a["adj_id"].split("-")[1]) for a in adjustments if "-" in a.get("adj_id", "")]
    return f"ADJ-{max(ids) + 1:03d}"


def render_adjustment_workflow(snapshot_mode: bool = False):
    # ── Two-column layout ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        st.markdown("### Adjustment Types")
        st.markdown(
            "<div style='font-size:0.8rem;color:#6b7280;margin-bottom:12px;'>"
            "Click a type to pre-fill the form</div>",
            unsafe_allow_html=True,
        )

        # Type 1
        with st.container(border=True):
            st.markdown(
                "<div style='border-left:4px solid #7c3aed;padding-left:12px;'>"
                "<div style='font-size:1rem;font-weight:700;color:#1a1f2e;'>Type 1 — Tag Correction</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<span style='background:#ede9fe;color:#5b21b6;border-radius:10px;"
                "padding:2px 10px;font-size:0.72rem;font-weight:600;'>Direct</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.82rem;color:#374151;margin-top:8px;'>"
                "A field on the project card is missing or incorrect. The audit happened but the data wasn't captured in the system.</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.78rem;color:#4b5563;margin-top:8px;'>"
                "<strong>Who:</strong> Audit-owning function initiates. If another platform initiates, audit owner must confirm.<br>"
                "<strong>Evidence:</strong> Audit scope document, final report, or engagement letter.<br>"
                "<strong>Corrects:</strong> Lead Audit Group, Scope Platform, Impacted Platform, Regions in Scope, AE field."
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='margin-top:10px;font-size:0.78rem;'>"
                "<span style='background:#f3f4f6;border:1px solid #d1d5db;border-radius:6px;"
                "padding:3px 10px;font-weight:500;'>Audit owner submits</span>"
                " → "
                "<span style='background:#f3f4f6;border:1px solid #d1d5db;border-radius:6px;"
                "padding:3px 10px;font-weight:500;'>Data Analytics validates</span>"
                " → "
                "<span style='background:#d1fae5;border:1px solid #34d399;border-radius:6px;"
                "padding:3px 10px;font-weight:500;color:#065f46;'>Approved / Rejected</span>"
                "</div>"
                "<div style='font-size:0.72rem;color:#9ca3af;margin-top:4px;'>"
                "If another platform initiates: routes to audit owner (5 days) → Data Analytics → Reporting Director if disputed"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Select Type 1", key="prefill_type1", use_container_width=True):
                st.session_state["adj_prefill_type"] = ADJ_TYPES[0]
                st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Type 2
        with st.container(border=True):
            st.markdown(
                "<div style='border-left:4px solid #1d4ed8;padding-left:12px;'>"
                "<div style='font-size:1rem;font-weight:700;color:#1a1f2e;'>Type 2 — Coverage Claim</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<span style='background:#dbeafe;color:#1e40af;border-radius:10px;"
                "padding:2px 10px;font-size:0.72rem;font-weight:600;'>Indirect</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.82rem;color:#374151;margin-top:8px;'>"
                "Your platform believes it was covered by another function's audit but the Impacted Platform field was not populated.</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.78rem;color:#4b5563;margin-top:8px;'>"
                "<strong>Who:</strong> Claiming platform initiates. Audit owner must confirm within 5 days.<br>"
                "<strong>Evidence:</strong> Condition A (named stakeholder in scope) or Condition B (issue attribution to this platform).<br>"
                "<span style='color:#dc2626;font-weight:600;'>Cannot be self-asserted. Audit owner confirmation is mandatory.</span>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='margin-top:10px;font-size:0.78rem;'>"
                "<span style='background:#f3f4f6;border:1px solid #d1d5db;border-radius:6px;"
                "padding:3px 10px;font-weight:500;'>Claiming platform submits</span>"
                " → "
                "<span style='background:#fef3c7;border:1px solid #f59e0b;border-radius:6px;"
                "padding:3px 10px;font-weight:500;color:#92400e;'>Audit owner confirms (5 days)</span>"
                " → "
                "<span style='background:#f3f4f6;border:1px solid #d1d5db;border-radius:6px;"
                "padding:3px 10px;font-weight:500;'>Data Analytics approves</span>"
                " → "
                "<span style='background:#d1fae5;border:1px solid #34d399;border-radius:6px;"
                "padding:3px 10px;font-weight:500;color:#065f46;'>Approved</span>"
                "</div>"
                "<div style='font-size:0.72rem;color:#9ca3af;margin-top:4px;'>"
                "If disputed → Reporting Director rules within 2 days. If no response in 5 days → auto-escalation."
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Select Type 2", key="prefill_type2", use_container_width=True):
                st.session_state["adj_prefill_type"] = ADJ_TYPES[1]
                st.rerun()

    with right_col:
        st.markdown("### New Adjustment Request")

        if snapshot_mode:
            st.warning("Snapshot mode — submissions are disabled. Switch to live view to submit adjustments.")

        prefill_type = st.session_state.get("adj_prefill_type", ADJ_TYPES[0])
        prefill_idx = ADJ_TYPES.index(prefill_type) if prefill_type in ADJ_TYPES else 0

        with st.form("adj_form", clear_on_submit=True):
            adj_type = st.selectbox(
                "Adjustment Type *",
                ADJ_TYPES,
                index=prefill_idx,
                disabled=snapshot_mode,
                key="form_adj_type",
            )
            field = st.selectbox(
                "Field Being Adjusted *",
                FIELDS,
                disabled=snapshot_mode,
                key="form_adj_field",
            )
            reason = st.selectbox(
                "Reason Code *",
                REASON_CODES,
                disabled=snapshot_mode,
                key="form_adj_reason",
            )
            note = st.text_area(
                "Supporting Note *",
                placeholder="Describe the adjustment and business rationale. Reference specific audit documentation, scope sections, or report references where applicable.",
                height=120,
                disabled=snapshot_mode,
                key="form_adj_note",
            )
            evidence = st.text_input(
                "Evidence Reference",
                placeholder="e.g. Audit report section 3.2, scope document ref. CM-AUD-2025-Q2",
                disabled=snapshot_mode,
                key="form_adj_evidence",
            )

            c_clear, c_submit = st.columns(2)
            with c_clear:
                clear = st.form_submit_button(
                    "Clear",
                    use_container_width=True,
                    disabled=snapshot_mode,
                )
            with c_submit:
                submitted = st.form_submit_button(
                    "Submit Adjustment →",
                    type="primary",
                    use_container_width=True,
                    disabled=snapshot_mode,
                )

            if submitted and not snapshot_mode:
                if not note.strip():
                    st.error("Supporting Note is required.")
                else:
                    new_adj = {
                        "adj_id": _next_adj_id(st.session_state.adjustments),
                        "adj_type": adj_type,
                        "field_being_adjusted": field,
                        "from_value": "—",
                        "to_value": "—",
                        "reason_code": reason,
                        "supporting_note": note,
                        "evidence_ref": evidence,
                        "submitted_by": "Current User",
                        "submitted_date": str(date.today()),
                        "status": "Pending",
                    }
                    st.session_state.adjustments.append(new_adj)
                    if "adj_prefill_type" in st.session_state:
                        del st.session_state["adj_prefill_type"]
                    st.success(f"Adjustment {new_adj['adj_id']} submitted — routed to Data Analytics (3 business day turnaround).")

        st.markdown(
            "<div style='font-size:0.72rem;color:#9ca3af;margin-top:4px;'>"
            "Routed to Data Analytics · 3 business day turnaround · All decisions captured in audit trail"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Adjustments This Quarter ──────────────────────────────────────────────
    st.divider()

    adjustments = st.session_state.get("adjustments", get_adjustments())
    approved_count = sum(1 for a in adjustments if a["status"] == "Approved")
    pending_count = sum(1 for a in adjustments if a["status"] == "Pending")

    hdr1, hdr2 = st.columns([3, 2])
    with hdr1:
        st.markdown("### Adjustments This Quarter")
    with hdr2:
        st.markdown(
            f"<div style='text-align:right;padding-top:8px;'>"
            f"<span style='background:#d1fae5;color:#065f46;border-radius:10px;"
            f"padding:3px 12px;font-size:0.78rem;font-weight:600;margin-right:6px;'>"
            f"✓ {approved_count} Approved</span>"
            f"<span style='background:#fef3c7;color:#92400e;border-radius:10px;"
            f"padding:3px 12px;font-size:0.78rem;font-weight:600;'>"
            f"⏳ {pending_count} Pending</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if not adjustments:
        st.info("No adjustments submitted this quarter.")
        return

    adj_df = pd.DataFrame(adjustments)
    display_cols = ["adj_id", "adj_type", "field_being_adjusted", "from_value", "to_value", "reason_code", "submitted_date", "status"]
    display_df = adj_df[display_cols].copy()
    display_df.columns = ["ID", "Type", "Field", "From", "To", "Reason", "Submitted", "Status"]

    def style_status(val):
        return STATUS_STYLE.get(val, "")

    def style_type(val):
        short = {
            "Type 1 – Tag Correction": "background:#ede9fe;color:#5b21b6;border-radius:10px;padding:2px 8px;font-size:0.75rem;font-weight:600;",
            "Type 2 – Coverage Claim": "background:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 8px;font-size:0.75rem;font-weight:600;",
        }
        return short.get(val, "")

    styled = (
        display_df.style
        .applymap(style_status, subset=["Status"])
        .applymap(style_type, subset=["Type"])
        .set_properties(**{"font-size": "0.82rem"})
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Show pending detail note
    for adj in adjustments:
        if adj["status"] == "Pending":
            st.markdown(
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>"
                f"<strong>{adj['adj_id']}</strong> is awaiting confirmation. "
                f"Auto-escalates to Reporting Director if no response in 5 days."
                f"</div>",
                unsafe_allow_html=True,
            )
