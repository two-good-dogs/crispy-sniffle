import streamlit as st
from datetime import datetime


def render_commentary(platform: str, snapshot_mode: bool = False):
    st.markdown("### Platform Commentary")
    st.markdown(
        "<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>"
        f"Add quarter-end commentary for <strong>{platform}</strong>. "
        "Commentary is saved per platform and visible in the Deck Preview tab."
        "</div>",
        unsafe_allow_html=True,
    )

    # Initialize commentary store
    if "commentary" not in st.session_state:
        st.session_state.commentary = {}

    saved_text = st.session_state.commentary.get(platform, "")

    if snapshot_mode:
        st.info("Snapshot mode — commentary is read-only.")
        if saved_text:
            st.markdown(
                f"<div style='background:#f8f9fb;border:1px solid #e5e7eb;border-radius:6px;"
                f"padding:16px;font-size:0.85rem;color:#374151;white-space:pre-wrap;'>{saved_text}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("*No commentary recorded for this quarter.*")
        return

    # Editable mode
    new_text = st.text_area(
        "Commentary",
        value=saved_text,
        height=250,
        placeholder=(
            f"Enter quarter-end commentary for {platform}...\n\n"
            "e.g. Overall audit coverage for Q2 FY25 is strong. "
            "Direct coverage stands at 8 audits with 14 total footprint. "
            "Two open adjustments under review — ADJ-012 pending T&O confirmation."
        ),
        key=f"commentary_input_{platform}",
        label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns([2, 1, 4])
    with c1:
        if st.button("💾 Save Commentary", type="primary", use_container_width=True, key=f"save_commentary_{platform}"):
            st.session_state.commentary[platform] = new_text
            st.session_state[f"commentary_saved_ts_{platform}"] = datetime.now().strftime("%H:%M:%S")
            st.success("Commentary saved.")
    with c2:
        if st.button("Clear", use_container_width=True, key=f"clear_commentary_{platform}"):
            st.session_state.commentary[platform] = ""
            st.rerun()

    ts = st.session_state.get(f"commentary_saved_ts_{platform}")
    if ts and saved_text:
        st.markdown(
            f"<div style='font-size:0.72rem;color:#9ca3af;margin-top:4px;'>"
            f"Last saved at {ts}</div>",
            unsafe_allow_html=True,
        )

    # Word count
    word_count = len(new_text.split()) if new_text.strip() else 0
    st.markdown(
        f"<div style='font-size:0.72rem;color:#d1d5db;text-align:right;margin-top:2px;'>"
        f"{word_count} words</div>",
        unsafe_allow_html=True,
    )
