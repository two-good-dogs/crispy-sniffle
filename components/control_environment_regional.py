import streamlit as st
import pandas as pd
from datetime import datetime
from data.database import (
    db_get_control_environment,
    db_update_ce_rating,
    db_get_ce_commentary,
    db_save_ce_commentary,
)
from data.mock_data import CURRENT_USER, get_platforms


def render_control_environment_regional(snapshot_mode: bool = False, regions: list = None):
    """Renders regional Control Environment Summary organized by region, then by platform type."""

    st.markdown("### Control Environment Summary — Regional View")

    if not regions:
        st.info("No regions selected. Please select regions in the sidebar.")
        return

    # Get all CE data
    all_ce_data = db_get_control_environment(platforms=None)
    if not all_ce_data:
        st.info("No control environment data available.")
        return

    ce_df = pd.DataFrame(all_ce_data)
    platform_config = get_platforms()
    lobs = platform_config["lines_of_business"]
    functions = platform_config["functions"]
    tech = platform_config["technology"]

    # Two-column layout
    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown("#### Regional Platforms")

        # For each region, show organized platform groupings
        for region_idx, region in enumerate(regions):
            if region_idx > 0:
                st.divider()

            # Region header
            st.markdown(f"##### {region}")

            # Group CE data by platform type within this region
            platform_sections = {
                "Platforms": [],
                "Functions": [],
                "Technology": [],
            }

            for _, row in ce_df.iterrows():
                platform = row["platform"]

                if platform in lobs:
                    platform_sections["Platforms"].append(row)
                elif platform in functions:
                    platform_sections["Functions"].append(row)
                elif platform in tech:
                    platform_sections["Technology"].append(row)

            # Render each section
            for section_name, items in platform_sections.items():
                if not items:
                    continue

                st.markdown(f"**{section_name}**")

                # Table header
                col1, col2, col3 = st.columns([2.2, 1, 1], gap="small")
                with col1:
                    st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Platform</small>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Rating</small>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<small style='font-weight:700;color:#6b7280;font-size:0.75rem;'>Trend</small>", unsafe_allow_html=True)

                st.markdown("<div style='height:1px;background:#e5e7eb;margin:8px 0;'></div>", unsafe_allow_html=True)

                # Render rows for this section
                for item in items:
                    au_id = item["au_id"]
                    platform_name = item["platform"]
                    current_rating = item["ce_rating"]
                    current_trend = item["trend"]

                    col1, col2, col3 = st.columns([2.2, 1, 1], gap="small")

                    with col1:
                        st.markdown(f"<div style='padding:10px 0;font-weight:500;'>{platform_name}</div>", unsafe_allow_html=True)

                    with col2:
                        selected_rating = st.selectbox(
                            "Rating",
                            ["SAT", "RI", "UNSAT"],
                            index=["SAT", "RI", "UNSAT"].index(current_rating),
                            key=f"reg_rating_{au_id}_{region}",
                            label_visibility="collapsed",
                        )

                        if not snapshot_mode and selected_rating != current_rating:
                            db_update_ce_rating(au_id, selected_rating, current_trend)
                            st.rerun()

                    with col3:
                        trend_options = ["Trending Up", "No Change", "Downgraded", "Upgraded"]
                        selected_trend = st.selectbox(
                            "Trend",
                            trend_options,
                            index=trend_options.index(current_trend) if current_trend in trend_options else 1,
                            key=f"reg_trend_{au_id}_{region}",
                            label_visibility="collapsed",
                        )

                        if not snapshot_mode and selected_trend != current_trend:
                            db_update_ce_rating(au_id, current_rating, selected_trend)
                            st.rerun()

                    st.markdown("<div style='height:1px;background:#e5e7eb;margin:8px 0;'></div>", unsafe_allow_html=True)

                st.markdown("")  # Spacing between sections

    # ── RIGHT COLUMN: Commentary ──────────────────────────────────────────────
    with right_col:
        st.markdown("#### Commentary")

        primary_region = regions[0]
        region_label = ", ".join(regions[:2]) if len(regions) <= 2 else f"{regions[0]} +{len(regions)-1}"
        st.caption(f"📍 {region_label}")

        st.divider()

        # Load and display comments for first region
        comments = db_get_ce_commentary(primary_region)

        if comments:
            for comment in comments:
                with st.container(border=True):
                    st.markdown(f"**{comment['author']}**")
                    st.write(comment['text'])
                    st.caption(comment['posted_at'])

        # New comment input
        if not snapshot_mode:
            st.markdown("**Add Insight**")
            new_comment_text = st.text_area(
                "Your insight",
                placeholder="Type your observation…",
                height=100,
                key="ce_regional_comment",
                label_visibility="collapsed",
            )

            if st.button("💾 Save Comment", key="ce_regional_save", use_container_width=True, type="primary"):
                if new_comment_text.strip():
                    import uuid
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    db_save_ce_commentary({
                        "entry_id": f"CEC-{uuid.uuid4().hex[:8].upper()}",
                        "platform": primary_region,
                        "text": new_comment_text.strip(),
                        "author": CURRENT_USER,
                        "posted_at": timestamp,
                    })
                    st.success("✓ Comment saved")
                    st.rerun()
