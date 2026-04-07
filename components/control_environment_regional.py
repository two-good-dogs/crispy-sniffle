import uuid
import re
import streamlit as st
import pandas as pd
from datetime import datetime
import data.data_interface as di


# ── Helpers ───────────────────────────────────────────────────────────────────

def _filter_controls_by_region(controls: pd.DataFrame, regions: list) -> pd.DataFrame:
    """
    Return controls whose regional_coverage contains any selected region.
    regional_coverage is pipe-separated (same pattern as ae_platforms).
    """
    if controls.empty or "regional_coverage" not in controls.columns:
        return controls
    region_set = set(regions)
    match = controls["regional_coverage"].fillna("").apply(
        lambda x: bool({p.strip() for p in re.split(r"\s*[|,;]\s*", x) if p.strip()} & region_set)
    )
    return controls[match].copy()


def _aggregate_by_region(controls: pd.DataFrame) -> pd.DataFrame:
    """Aggregate long-format controls to one summary row per region."""
    if controls.empty:
        return pd.DataFrame()
    # Explode pipe-separated regional_coverage into individual region rows
    exploded = controls.copy()
    exploded["region"] = exploded["regional_coverage"].fillna("").apply(
        lambda x: [p.strip() for p in re.split(r"\s*[|,;]\s*", x) if p.strip()]
    )
    exploded = exploded.explode("region")
    return (
        exploded.groupby("region", sort=False)
        .agg(
            total=("control_id", "count"),
            de_ef=("de_result", lambda x: (x == "EF").sum()),
            oe_met=("oe_result", lambda x: (x == "M").sum()),
            test_pass=("test_result", lambda x: (x == "Pass").sum()),
            audit_count=("audit_id", "nunique"),
            risk_cats=("risk_category", lambda x: " · ".join(sorted(x.dropna().unique()))),
        )
        .reset_index()
    )


def _pct(num, denom):
    return f"{int(round(100 * num / denom))}%" if denom else "—"


def _result_chip(label, value, bg, color):
    return (
        f"<span style='font-size:0.68rem;font-weight:600;color:{color};"
        f"background:{bg};border-radius:4px;padding:2px 7px;'>{label}: {value}</span>"
    )


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_control_environment_regional(snapshot_mode: bool = False, regions: list = None):
    st.markdown("### Control Environment Summary — Regional View")

    if not regions:
        st.info("No regions selected. Please select regions in the sidebar.")
        return

    # ── Load and filter controls ──────────────────────────────────────────────
    controls_raw = di.get_controls()

    missing_cols = {"regional_coverage", "control_id"} - set(controls_raw.columns)
    if missing_cols:
        st.warning(f"Controls data missing expected columns: {missing_cols}")
        return

    controls = _filter_controls_by_region(controls_raw, regions)

    if controls.empty:
        st.info("No controls data found for the selected regions.")
        return

    agg = _aggregate_by_region(controls)
    # Only keep rows for selected regions
    agg = agg[agg["region"].isin(set(regions))]

    left_col, right_col = st.columns([1.5, 1], gap="large")

    # ── LEFT: Per-region control summary + qualitative ratings ────────────────
    with left_col:
        st.markdown("#### Regional Platforms")

        _ce_key = f"ce_regional_{'_'.join(sorted(regions))}"
        existing_ids = {r["rec_id"] for r in st.session_state.get(_ce_key, [])}
        new_rows = [
            {"rec_id": row["region"], "region": row["region"],
             "ce_rating": "N/A", "trend": "N/A"}
            for _, row in agg.iterrows()
            if row["region"] not in existing_ids
        ]
        if _ce_key not in st.session_state:
            st.session_state[_ce_key] = new_rows
        else:
            st.session_state[_ce_key].extend(new_rows)

        for region_idx, (_, agg_row) in enumerate(agg.iterrows()):
            region = agg_row["region"]
            if region_idx > 0:
                st.divider()

            st.markdown(f"##### {region}")

            # Summary chips for this region
            n = int(agg_row["total"])
            de = _pct(int(agg_row["de_ef"]), n)
            oe = _pct(int(agg_row["oe_met"]), n)
            tp = _pct(int(agg_row["test_pass"]), n)

            st.markdown(
                '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">'
                + _result_chip("DE", de, "#d1fae5", "#065f46")
                + _result_chip("OE", oe, "#dbeafe", "#1e40af")
                + _result_chip("Pass", tp, "#fef3c7", "#92400e")
                + f'<span style="font-size:0.68rem;color:#9ca3af;align-self:center;">'
                  f'{int(agg_row["audit_count"])} audits · {n} controls</span>'
                + '</div>',
                unsafe_allow_html=True,
            )

            # Risk categories for this region
            if agg_row["risk_cats"]:
                st.caption(agg_row["risk_cats"])

            # Qualitative rating/trend selectors
            ce_row = next(
                (r for r in st.session_state[_ce_key] if r["rec_id"] == region),
                {"ce_rating": "N/A", "trend": "N/A"},
            )
            current_rating = ce_row["ce_rating"]
            current_trend  = ce_row["trend"]

            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(
                    "<div style='font-size:0.72rem;color:#6b7280;padding:8px 0;'>"
                    "Qualitative assessment</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                rating_opts = ["N/A", "SAT", "RI", "UNSAT"]
                sel_rating = st.selectbox(
                    "Rating", rating_opts,
                    index=rating_opts.index(current_rating) if current_rating in rating_opts else 0,
                    key=f"reg_rating_{region}", label_visibility="collapsed",
                )
                if not snapshot_mode and sel_rating != current_rating:
                    for r in st.session_state[_ce_key]:
                        if r["rec_id"] == region:
                            r["ce_rating"] = sel_rating
                    st.rerun()
            with c3:
                trend_opts = ["N/A", "Improving", "Stable", "Deteriorating"]
                sel_trend = st.selectbox(
                    "Trend", trend_opts,
                    index=trend_opts.index(current_trend) if current_trend in trend_opts else 0,
                    key=f"reg_trend_{region}", label_visibility="collapsed",
                )
                if not snapshot_mode and sel_trend != current_trend:
                    for r in st.session_state[_ce_key]:
                        if r["rec_id"] == region:
                            r["trend"] = sel_trend
                    st.rerun()

    # ── RIGHT: Commentary ─────────────────────────────────────────────────────
    with right_col:
        st.markdown("#### Commentary")
        primary_region = regions[0]
        label = ", ".join(regions[:2]) if len(regions) <= 2 else f"{regions[0]} +{len(regions)-1}"
        st.caption(f"📍 {label}")
        st.divider()

        _comm_key = f"ce_regional_comments_{primary_region}"
        if _comm_key not in st.session_state:
            st.session_state[_comm_key] = []

        for comment in st.session_state[_comm_key]:
            with st.container(border=True):
                st.markdown(f"**{comment['author']}**")
                st.write(comment["text"])
                st.caption(comment["posted_at"])

        if not snapshot_mode:
            st.markdown("**Add Insight**")
            new_text = st.text_area(
                "Your insight", placeholder="Type your observation…",
                height=100, key="ce_regional_comment", label_visibility="collapsed",
            )
            if st.button("💾 Save Comment", key="ce_regional_save",
                         use_container_width=True, type="primary"):
                if new_text.strip():
                    st.session_state[_comm_key].append({
                        "entry_id": f"CEC-{uuid.uuid4().hex[:8].upper()}",
                        "platform": primary_region,
                        "text": new_text.strip(),
                        "author": di.CURRENT_USER,
                        "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    st.success("✓ Comment saved")
                    st.rerun()
