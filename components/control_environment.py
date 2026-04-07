import uuid
import streamlit as st
import pandas as pd
from datetime import datetime
import data.data_interface as di


# ── Helpers ───────────────────────────────────────────────────────────────────

def _filter_controls(controls: pd.DataFrame, platforms: list) -> pd.DataFrame:
    """
    Return controls relevant to the selected platforms.
    Owned  : audit_group matches a selected platform.
    In-scope: selected platform appears in ae_platforms (pipe-separated).
    """
    if controls.empty:
        return controls
    plat_set = set(platforms)
    owned = controls["audit_group"].isin(plat_set)
    in_scope = (
        controls["ae_platforms"].fillna("").apply(
            lambda x: bool({p.strip() for p in x.split("|") if p.strip()} & plat_set)
        )
    )
    return controls[owned | in_scope].copy()


def _aggregate_controls(controls: pd.DataFrame) -> pd.DataFrame:
    """Aggregate long-format controls to one summary row per audit_id."""
    if controls.empty:
        return pd.DataFrame()
    return (
        controls.groupby("audit_id", sort=False)
        .agg(
            audit_group=("audit_group", "first"),
            total=("control_id", "count"),
            de_ef=("de_result", lambda x: (x == "EF").sum()),
            oe_met=("oe_result", lambda x: (x == "M").sum()),
            test_pass=("test_result", lambda x: (x == "Pass").sum()),
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

def render_control_environment(snapshot_mode: bool = False, platforms: list = None):
    st.markdown("### Control Environment Summary")

    if not platforms:
        st.info("No platforms selected. Please select platforms in the sidebar.")
        return

    # ── Load and filter controls ──────────────────────────────────────────────
    controls_raw = di.get_controls()

    missing_cols = {"audit_group", "ae_platforms", "control_id"} - set(controls_raw.columns)
    if missing_cols:
        st.warning(f"Controls data missing expected columns: {missing_cols}")
        return

    controls = _filter_controls(controls_raw, platforms)

    if controls.empty:
        st.info("No controls data found for the selected platforms.")
        return

    agg = _aggregate_controls(controls)

    # ── Summary metrics strip ─────────────────────────────────────────────────
    total_ctrl  = int(controls["control_id"].count())
    de_rate     = _pct((controls["de_result"] == "EF").sum(), total_ctrl)
    oe_rate     = _pct((controls["oe_result"] == "M").sum(), total_ctrl)
    test_rate   = _pct((controls["test_result"] == "Pass").sum(), total_ctrl)
    audit_count = agg["audit_id"].nunique()

    st.markdown(
        '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;">'
        + "".join([
            f'<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;'
            f'padding:12px 18px;min-width:110px;">'
            f'<div style="font-size:0.6rem;font-weight:600;letter-spacing:0.08em;'
            f'text-transform:uppercase;color:#9ca3af;">{lbl}</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:{col};'
            f'font-family:\'Barlow Condensed\',sans-serif;line-height:1.1;">{val}</div>'
            f'</div>'
            for lbl, val, col in [
                ("Audits", audit_count, "#1a1f2e"),
                ("Controls", total_ctrl, "#1a1f2e"),
                ("DE Effective", de_rate, "#059669"),
                ("OE Met", oe_rate, "#2563eb"),
                ("Tests Pass", test_rate, "#d97706"),
            ]
        ])
        + '</div>',
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.5, 1], gap="large")

    # ── LEFT: Per-audit control summary + qualitative ratings ─────────────────
    with left_col:
        st.markdown("#### Auditable Units")

        _ce_key = f"ce_data_{'_'.join(sorted(platforms))}"
        # Seed session state from actual audits in data
        existing_ids = {r["au_id"] for r in st.session_state.get(_ce_key, [])}
        new_rows = [
            {"au_id": row["audit_id"], "auditable_unit": row["audit_id"],
             "audit_group": row["audit_group"], "ce_rating": "N/A", "trend": "N/A"}
            for _, row in agg.iterrows()
            if row["audit_id"] not in existing_ids
        ]
        if _ce_key not in st.session_state:
            st.session_state[_ce_key] = new_rows
        else:
            st.session_state[_ce_key].extend(new_rows)

        # Header row
        h1, h2, h3, h4 = st.columns([2.5, 1.8, 1, 1])
        for col_widget, label in zip([h1, h2, h3, h4],
                                     ["Audit ID", "Results", "Rating", "Trend"]):
            col_widget.markdown(
                f"<div style='font-size:0.68rem;font-weight:700;color:#9ca3af;"
                f"text-transform:uppercase;letter-spacing:0.06em;padding-bottom:4px;'>"
                f"{label}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:1px;background:#e5e7eb;margin-bottom:8px;'></div>",
                    unsafe_allow_html=True)

        for _, agg_row in agg.iterrows():
            au_id = agg_row["audit_id"]
            # Find session state row
            ce_row = next(
                (r for r in st.session_state[_ce_key] if r["au_id"] == au_id),
                {"ce_rating": "N/A", "trend": "N/A"},
            )
            current_rating = ce_row["ce_rating"]
            current_trend  = ce_row["trend"]

            # Compute per-audit metrics
            aud_ctrl = controls[controls["audit_id"] == au_id]
            n = len(aud_ctrl)
            de = _pct((aud_ctrl["de_result"] == "EF").sum(), n)
            oe = _pct((aud_ctrl["oe_result"] == "M").sum(), n)
            tp = _pct((aud_ctrl["test_result"] == "Pass").sum(), n)

            c1, c2, c3, c4 = st.columns([2.5, 1.8, 1, 1])

            with c1:
                st.markdown(
                    f"<div style='padding:8px 0;font-size:0.78rem;font-weight:500;"
                    f"color:#111827;line-height:1.3;'>{au_id}</div>"
                    f"<div style='font-size:0.64rem;color:#6b7280;margin-bottom:4px;'>"
                    f"{agg_row['risk_cats']}</div>",
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown(
                    '<div style="display:flex;flex-wrap:wrap;gap:4px;padding:8px 0;">'
                    + _result_chip("DE", de, "#d1fae5", "#065f46")
                    + _result_chip("OE", oe, "#dbeafe", "#1e40af")
                    + _result_chip("Pass", tp, "#fef3c7", "#92400e")
                    + '</div>',
                    unsafe_allow_html=True,
                )

            with c3:
                rating_opts = ["N/A", "SAT", "RI", "UNSAT"]
                sel_rating = st.selectbox(
                    "Rating", rating_opts,
                    index=rating_opts.index(current_rating) if current_rating in rating_opts else 0,
                    key=f"rating_{au_id}", label_visibility="collapsed",
                )
                if not snapshot_mode and sel_rating != current_rating:
                    for r in st.session_state[_ce_key]:
                        if r["au_id"] == au_id:
                            r["ce_rating"] = sel_rating
                    st.rerun()

            with c4:
                trend_opts = ["N/A", "Improving", "Stable", "Deteriorating"]
                sel_trend = st.selectbox(
                    "Trend", trend_opts,
                    index=trend_opts.index(current_trend) if current_trend in trend_opts else 0,
                    key=f"trend_{au_id}", label_visibility="collapsed",
                )
                if not snapshot_mode and sel_trend != current_trend:
                    for r in st.session_state[_ce_key]:
                        if r["au_id"] == au_id:
                            r["trend"] = sel_trend
                    st.rerun()

            st.markdown("<div style='height:1px;background:#f3f4f6;margin:4px 0 8px;'></div>",
                        unsafe_allow_html=True)

    # ── RIGHT: Commentary ─────────────────────────────────────────────────────
    with right_col:
        st.markdown("#### Commentary")
        primary_platform = platforms[0]
        label = ", ".join(platforms[:2]) if len(platforms) <= 2 else f"{platforms[0]} +{len(platforms)-1}"
        st.caption(f"📍 {label}")
        st.divider()

        _comm_key = f"ce_comments_{primary_platform}"
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
                height=100, key="ce_new_comment", label_visibility="collapsed",
            )
            if st.button("💾 Save Comment", key="ce_save_btn",
                         use_container_width=True, type="primary"):
                if new_text.strip():
                    st.session_state[_comm_key].append({
                        "entry_id": f"CEC-{uuid.uuid4().hex[:8].upper()}",
                        "platform": primary_platform,
                        "text": new_text.strip(),
                        "author": di.CURRENT_USER,
                        "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    st.success("✓ Comment saved")
                    st.rerun()
