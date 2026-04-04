import streamlit as st
import pandas as pd
from datetime import datetime
from data.database import (
    db_get_control_environment,
    db_update_ce_rating,
    db_get_ce_commentary,
    db_save_ce_commentary,
)
from data.mock_data import CURRENT_USER


def render_control_environment(snapshot_mode: bool = False, platforms: list = None):
    """Renders the Control Environment Summary with AU table and commentary."""

    st.markdown("### Control Environment Summary")

    if not platforms:
        st.info("No platforms selected. Please select platforms in the sidebar.")
        return

    # Get CE data filtered by selected platforms
    ce_data = db_get_control_environment(platforms=platforms)
    if not ce_data:
        st.info("No control environment data available for selected platforms.")
        return

    # Convert to DataFrame
    ce_df = pd.DataFrame(ce_data)

    # Two-column layout
    left_col, right_col = st.columns([1.5, 1], gap="large")

    # ── LEFT COLUMN: CE Table ─────────────────────────────────────────────────
    with left_col:
        st.markdown("#### Auditable Units")

        # Create table data structure
        table_data = []
        for _, row in ce_df.iterrows():
            table_data.append({
                "AU": row["auditable_unit"],
                "Rating": row["ce_rating"],
                "Trend": row["trend"],
                "au_id": row["au_id"],
            })

        # Render table with styled header
        st.markdown(
            "<div style='display:grid;grid-template-columns:2.2fr 1fr 1fr;gap:12px;margin-bottom:16px;'>"
            "<div style='font-weight:700;color:#6b7280;text-transform:uppercase;font-size:0.75rem;letter-spacing:0.05em;'>AU</div>"
            "<div style='font-weight:700;color:#6b7280;text-transform:uppercase;font-size:0.75rem;letter-spacing:0.05em;'>Rating</div>"
            "<div style='font-weight:700;color:#6b7280;text-transform:uppercase;font-size:0.75rem;letter-spacing:0.05em;'>Trend</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Render each row
        for item in table_data:
            au_id = item["au_id"]
            au_name = item["AU"]
            current_rating = item["Rating"]
            current_trend = item["Trend"]

            # Create a container for the entire row
            col1, col2, col3 = st.columns([2.2, 1, 1], gap="small")

            with col1:
                st.markdown(f"<div style='padding:10px 0;font-weight:500;line-height:1.4;'>{au_name}</div>", unsafe_allow_html=True)

            with col2:
                selected_rating = st.selectbox(
                    "Rating",
                    ["SAT", "RI", "UNSAT"],
                    index=["SAT", "RI", "UNSAT"].index(current_rating),
                    key=f"rating_{au_id}",
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
                    key=f"trend_{au_id}",
                    label_visibility="collapsed",
                )

                if not snapshot_mode and selected_trend != current_trend:
                    db_update_ce_rating(au_id, current_rating, selected_trend)
                    st.rerun()

            # Add separator
            st.markdown("<div style='height:1px;background:#e5e7eb;margin:8px 0;'></div>", unsafe_allow_html=True)

    # ── RIGHT COLUMN: Commentary ──────────────────────────────────────────────
    with right_col:
        st.markdown("#### Commentary")

        primary_platform = platforms[0]
        platform_label = ", ".join(platforms[:2]) if len(platforms) <= 2 else f"{platforms[0]} +{len(platforms)-1}"
        st.caption(f"📍 {platform_label}")

        st.divider()

        # Load and display comments
        comments = db_get_ce_commentary(primary_platform)

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
                key="ce_new_comment",
                label_visibility="collapsed",
            )

            if st.button("💾 Save Comment", key="ce_save_btn", use_container_width=True, type="primary"):
                if new_comment_text.strip():
                    import uuid
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    db_save_ce_commentary({
                        "entry_id": f"CEC-{uuid.uuid4().hex[:8].upper()}",
                        "platform": primary_platform,
                        "text": new_comment_text.strip(),
                        "author": CURRENT_USER,
                        "posted_at": timestamp,
                    })
                    st.success("✓ Comment saved")
                    st.rerun()
