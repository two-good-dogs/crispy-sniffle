import streamlit as st
import pandas as pd
from data.mock_data import get_risk_stripes, get_platforms


def _build_stripe_lookup():
    """Map stripe id -> stripe metadata."""
    return {s["id"]: s for s in get_risk_stripes()}


def _explode_stripes(audits: pd.DataFrame) -> pd.DataFrame:
    """Expand each audit into one row per risk stripe it covers."""
    rows = []
    for _, audit in audits.iterrows():
        stripes = audit.get("risk_stripes", [])
        if not stripes:
            continue
        for stripe_id in stripes:
            row = audit.to_dict()
            row["risk_stripe"] = stripe_id
            rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _coverage_level(count: int) -> tuple:
    """Return (css_class, label) based on audit count covering a cell."""
    if count == 0:
        return "heatmap-none", "No coverage"
    elif count == 1:
        return "heatmap-low", "Low"
    elif count == 2:
        return "heatmap-med", "Moderate"
    else:
        return "heatmap-high", "Strong"


def _render_heatmap(exploded: pd.DataFrame, dimension_col: str, dimension_values: list, stripe_lookup: dict):
    """Render a heatmap grid: risk stripes (rows) x dimension (columns)."""
    stripes = get_risk_stripes()

    # Build header row
    header_cells = "<th style='text-align:left;padding:8px 12px;font-size:0.78rem;color:#6b7280;font-weight:600;'>Risk Stripe</th>"
    for dim in dimension_values:
        header_cells += f"<th style='text-align:center;padding:8px 10px;font-size:0.78rem;color:#6b7280;font-weight:600;min-width:100px;'>{dim}</th>"
    header_cells += "<th style='text-align:center;padding:8px 10px;font-size:0.78rem;color:#6b7280;font-weight:600;min-width:80px;'>Total</th>"

    body_rows = ""
    gap_cells = []
    for stripe in stripes:
        sid = stripe["id"]
        stripe_data = exploded[exploded["risk_stripe"] == sid] if not exploded.empty else pd.DataFrame()
        row_total = len(stripe_data)

        cells = f"<td style='padding:8px 12px;font-weight:600;font-size:0.82rem;color:#1a1f2e;white-space:nowrap;'>{stripe['icon']} {stripe['name']}</td>"

        for dim in dimension_values:
            if dimension_col == "region":
                dim_data = stripe_data[
                    (stripe_data["region"] == dim) | (stripe_data["region"] == "Global")
                ] if not stripe_data.empty else pd.DataFrame()
            else:
                dim_data = stripe_data[stripe_data[dimension_col] == dim] if not stripe_data.empty else pd.DataFrame()
            count = len(dim_data)
            css_cls, label = _coverage_level(count)

            if count == 0:
                gap_cells.append((stripe["name"], dim))
                cell_content = "<span style='color:#d1d5db;font-size:0.75rem;'>--</span>"
            else:
                audit_ids = ", ".join(dim_data["audit_id"].unique()[:3])
                extra = f" +{len(dim_data['audit_id'].unique()) - 3}" if len(dim_data["audit_id"].unique()) > 3 else ""
                cell_content = (
                    f"<div class='{css_cls}'>"
                    f"<span style='font-weight:700;font-size:1rem;'>{count}</span>"
                    f"<span style='font-size:0.65rem;display:block;margin-top:1px;'>{audit_ids}{extra}</span>"
                    f"</div>"
                )
            cells += f"<td style='text-align:center;padding:6px 8px;'>{cell_content}</td>"

        # Total column
        total_cls, _ = _coverage_level(row_total)
        cells += (
            f"<td style='text-align:center;padding:6px 8px;'>"
            f"<div class='{total_cls}'><span style='font-weight:700;font-size:1rem;'>{row_total}</span></div>"
            f"</td>"
        )
        body_rows += f"<tr style='border-bottom:1px solid #f3f4f6;'>{cells}</tr>"

    table_html = f"""
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
        <thead><tr style="background:#f8f9fb;border-bottom:2px solid #e5e7eb;">{header_cells}</tr></thead>
        <tbody>{body_rows}</tbody>
    </table>
    </div>
    """
    return table_html, gap_cells


def _render_gap_analysis(gap_cells: list, dimension_label: str):
    """Render identified coverage gaps."""
    if not gap_cells:
        st.markdown(
            "<div class='metric-card' style='border-left:4px solid #065f46;'>"
            "<span style='color:#065f46;font-weight:600;'>Full Coverage</span>"
            "<p style='font-size:0.82rem;color:#6b7280;margin-top:4px;'>All risk stripes have at least one audit across every " + dimension_label.lower() + ".</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div style='font-size:0.85rem;color:#6b7280;margin-bottom:8px;'>"
        f"<strong style='color:#991b1b;'>{len(gap_cells)}</strong> gap(s) identified where a risk stripe has no audit coverage for a {dimension_label.lower()}."
        f"</div>",
        unsafe_allow_html=True,
    )

    gap_html = ""
    for stripe_name, dim_name in gap_cells:
        gap_html += (
            f"<div class='gap-chip'>"
            f"<span style='font-weight:600;'>{stripe_name}</span>"
            f" <span style='color:#9ca3af;'>in</span> "
            f"<span style='font-weight:600;'>{dim_name}</span>"
            f"</div>"
        )

    st.markdown(
        f"<div style='display:flex;flex-wrap:wrap;gap:6px;'>{gap_html}</div>",
        unsafe_allow_html=True,
    )


def _render_stripe_detail(exploded: pd.DataFrame, stripe_lookup: dict):
    """Expandable detail for each risk stripe showing constituent audits."""
    stripes = get_risk_stripes()
    for stripe in stripes:
        sid = stripe["id"]
        stripe_audits = exploded[exploded["risk_stripe"] == sid] if not exploded.empty else pd.DataFrame()
        count = len(stripe_audits["audit_id"].unique()) if not stripe_audits.empty else 0

        _, level_label = _coverage_level(count)
        level_color = {"No coverage": "#991b1b", "Low": "#92400e", "Moderate": "#1e40af", "Strong": "#065f46"}
        color = level_color.get(level_label, "#6b7280")

        with st.expander(f"{stripe['icon']} {stripe['name']} — {count} audit(s) ({level_label})", expanded=False):
            st.markdown(
                f"<p style='font-size:0.82rem;color:#6b7280;margin-bottom:8px;'>{stripe['description']}</p>",
                unsafe_allow_html=True,
            )
            if stripe_audits.empty:
                st.markdown(
                    "<div style='background:#fee2e2;border:1px solid #fca5a5;border-radius:6px;padding:10px 14px;font-size:0.82rem;color:#991b1b;'>"
                    "No audits currently cover this risk stripe. Consider adding coverage in the next audit cycle."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                unique_audits = stripe_audits.drop_duplicates(subset=["audit_id"])
                display_df = unique_audits[["audit_id", "audit_name", "audit_type", "region", "status", "rating"]].copy()
                display_df.columns = ["ID", "Audit Name", "Type", "Region", "Status", "Rating"]
                st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_risk_stripe_coverage(audits: pd.DataFrame, snapshot_mode: bool = False):
    """Main entry point for the Risk Stripe Coverage tab."""
    stripe_lookup = _build_stripe_lookup()
    platforms = get_platforms()
    all_stripes = get_risk_stripes()

    # Explode audits into stripe-level rows
    exploded = _explode_stripes(audits)

    # ── Summary metrics ──────────────────────────────────────────────────────
    total_stripes = len(all_stripes)
    covered_stripes = len(exploded["risk_stripe"].unique()) if not exploded.empty else 0
    coverage_pct = round(covered_stripes / total_stripes * 100) if total_stripes else 0
    total_mappings = len(exploded) if not exploded.empty else 0

    cols = st.columns(4)
    metrics = [
        ("RISK STRIPES", str(total_stripes), f"{covered_stripes} with coverage"),
        ("STRIPE COVERAGE", f"{coverage_pct}%", f"{covered_stripes} of {total_stripes} stripes"),
        ("AUDIT-STRIPE MAPPINGS", str(total_mappings), "Total audit-to-stripe links"),
        ("AVG STRIPES / AUDIT", f"{total_mappings / len(audits):.1f}" if len(audits) else "0", f"Across {len(audits)} audits"),
    ]
    for col, (label, value, sub) in zip(cols, metrics):
        with col:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-card-label'>{label}</div>"
                f"<div class='metric-card-value'>{value}</div>"
                f"<div class='metric-card-sub'>{sub}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── View toggle ──────────────────────────────────────────────────────────
    view_col, legend_col = st.columns([2, 3])
    with view_col:
        heatmap_view = st.radio(
            "Coverage matrix dimension",
            ["By Platform", "By Region"],
            horizontal=True,
            key="risk_stripe_view",
        )

    with legend_col:
        st.markdown(
            "<div style='display:flex;gap:12px;align-items:center;padding-top:28px;font-size:0.75rem;color:#6b7280;'>"
            "<span>Legend:</span>"
            "<span class='heatmap-none' style='padding:2px 8px;'>-- No coverage</span>"
            "<span class='heatmap-low' style='padding:2px 8px;'>1 Low</span>"
            "<span class='heatmap-med' style='padding:2px 8px;'>2 Moderate</span>"
            "<span class='heatmap-high' style='padding:2px 8px;'>3+ Strong</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Heatmap ──────────────────────────────────────────────────────────────
    if heatmap_view == "By Platform":
        # For platform view, use lead_group for owned, impacted_platform for others
        # Simplify: show LOBs as columns
        lobs = platforms["lines_of_business"]
        # Map audits to platform — owned audits -> lead_group, others -> impacted_platform
        if not exploded.empty:
            exploded_view = exploded.copy()
            exploded_view["_platform"] = exploded_view.apply(
                lambda r: r["lead_group"] if r["audit_type"] == "Owned Audit" else r["impacted_platform"],
                axis=1,
            )
        else:
            exploded_view = exploded
        table_html, gaps = _render_heatmap(exploded_view, "_platform", lobs, stripe_lookup)
        dim_label = "Platform"
    else:
        regions = platforms["regions"]
        table_html, gaps = _render_heatmap(exploded, "region", regions, stripe_lookup)
        dim_label = "Region"

    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Gap Analysis ─────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:700;color:#1a1f2e;margin-bottom:8px;'>Coverage Gaps</div>",
        unsafe_allow_html=True,
    )
    _render_gap_analysis(gaps, dim_label)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Stripe Detail ────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:700;color:#1a1f2e;margin-bottom:8px;'>Risk Stripe Detail</div>"
        "<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>Expand each stripe to see contributing audits, coverage type, and regional distribution.</div>",
        unsafe_allow_html=True,
    )
    _render_stripe_detail(exploded, stripe_lookup)
