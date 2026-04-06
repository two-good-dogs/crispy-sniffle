import uuid
import streamlit as st
import pandas as pd
from datetime import datetime
import data.data_interface as di


def render_control_environment_regional(snapshot_mode: bool = False, regions: list = None):
    st.markdown("### Control Environment Summary — Regional View")

    if not regions:
        st.info("No regions selected. Please select regions in the sidebar.")
        return

    # CE data lives in session state keyed by region set
    _ce_key = f"ce_regional_{'_'.join(sorted(regions))}"
    if _ce_key not in st.session_state:
        # Initialise with one row per region
        st.session_state[_ce_key] = [
            {"rec_id": f"{r}_01", "region": r, "platform": r,
             "ce_rating": "N/A", "trend": "N/A"}
            for r in regions
        ]
    all_ce_data = st.session_state[_ce_key]
    ce_df = pd.DataFrame(all_ce_data)

    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown("#### Regional Platforms")

        for region_idx, region in enumerate(regions):
            if region_idx > 0:
                st.divider()
            st.markdown(f"##### {region}")

            region_df = ce_df[ce_df["region"] == region]

            col1, col2, col3 = st.columns([2.2, 1, 1], gap="small")
            with col1:
                st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Platform</small>", unsafe_allow_html=True)
            with col2:
                st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Rating</small>", unsafe_allow_html=True)
            with col3:
                st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Trend</small>", unsafe_allow_html=True)

            st.markdown("<div style='height:1px;background:#e5e7eb;margin:8px 0;'></div>", unsafe_allow_html=True)

            for _, row in region_df.iterrows():
                rec_id        = row["rec_id"]
                platform_name = row["platform"]
                current_rating = row["ce_rating"]
                current_trend  = row["trend"]

                c1, c2, c3 = st.columns([2.2, 1, 1], gap="small")
                with c1:
                    st.markdown(f"<div style='padding:10px 0;font-weight:500;'>{platform_name}</div>", unsafe_allow_html=True)
                with c2:
                    rating_options = ["N/A", "SAT", "RI", "UNSAT"]
                    sel_rating = st.selectbox(
                        "Rating", rating_options,
                        index=rating_options.index(current_rating) if current_rating in rating_options else 0,
                        key=f"reg_rating_{rec_id}", label_visibility="collapsed",
                    )
                    if not snapshot_mode and sel_rating != current_rating:
                        for r in st.session_state[_ce_key]:
                            if r["rec_id"] == rec_id:
                                r["ce_rating"] = sel_rating
                        st.rerun()
                with c3:
                    trend_options = ["N/A", "Trending Up", "No Change", "Downgraded", "Upgraded"]
                    sel_trend = st.selectbox(
                        "Trend", trend_options,
                        index=trend_options.index(current_trend) if current_trend in trend_options else 0,
                        key=f"reg_trend_{rec_id}", label_visibility="collapsed",
                    )
                    if not snapshot_mode and sel_trend != current_trend:
                        for r in st.session_state[_ce_key]:
                            if r["rec_id"] == rec_id:
                                r["trend"] = sel_trend
                        st.rerun()

                st.markdown("<div style='height:1px;background:#e5e7eb;margin:8px 0;'></div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("#### Commentary")
        primary_region = regions[0]
        region_label = ", ".join(regions[:2]) if len(regions) <= 2 else f"{regions[0]} +{len(regions)-1}"
        st.caption(f"📍 {region_label}")
        st.divider()

        _comm_key = f"ce_regional_comments_{primary_region}"
        if _comm_key not in st.session_state:
            st.session_state[_comm_key] = []
        comments = st.session_state[_comm_key]

        for comment in comments:
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
            if st.button("💾 Save Comment", key="ce_regional_save", use_container_width=True, type="primary"):
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
