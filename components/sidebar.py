import streamlit as st
import pandas as pd
import data.data_interface as di

# ── Platform group definitions (keyword-matched, order matters) ───────────────
_PLATFORM_GROUPS = [
    ("Lines of Business", [
        "capital markets", "city national", "commercial banking",
        "insurance", "personal banking", "rbc bank", "wealth management",
    ]),
    ("Functions", [
        "anti money", "chief financial", "chief legal",
        "global compliance", "group risk", "human resources",
    ]),
    ("Technology & Operations", [
        "technology and operations", "technology & operations", "technology",
    ]),
]
_GROUP_KEYS = {
    "Lines of Business":       "sel_lob",
    "Functions":               "sel_functions",
    "Technology & Operations": "sel_tao",
    "Other":                   "sel_other",
}


def _group_platforms(platform_list: list) -> dict:
    """Bucket each platform into a named group via keyword matching."""
    groups = {name: [] for name, _ in _PLATFORM_GROUPS}
    groups["Other"] = []
    for plat in sorted(platform_list):
        plat_lower = plat.lower()
        placed = False
        for name, keywords in _PLATFORM_GROUPS:
            if any(kw in plat_lower for kw in keywords):
                groups[name].append(plat)
                placed = True
                break
        if not placed:
            groups["Other"].append(plat)
    return groups


def render_sidebar(unread_count: int = 0, platforms: dict = None, audits_df: pd.DataFrame = None):
    if platforms is None:
        platforms = {"lines_of_business": [], "regions": []}

    with st.sidebar:
        # ── Logo ─────────────────────────────────────────────────────────────
        st.markdown(
            '<div style="padding:16px 4px 12px;display:flex;align-items:center;'
            'justify-content:space-between;border-bottom:1px solid rgba(255,184,28,0.18);">'
            '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.55rem;'
            'font-weight:700;color:#ffffff;letter-spacing:0.02em;line-height:1;">'
            'Audit<span style="color:#FFB81C;">IQ</span>'
            '</div>'
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.52rem;'
            'font-weight:600;letter-spacing:0.1em;color:rgba(255,255,255,0.35);'
            'text-transform:uppercase;text-align:right;line-height:1.4;">'
            'Internal<br>Audit</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Notification row ──────────────────────────────────────────────────
        if unread_count > 0:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f'background:rgba(220,38,38,0.15);border:1px solid rgba(220,38,38,0.3);'
                f'border-radius:7px;padding:7px 12px;margin:10px 0 6px;">'
                f'<span style="font-size:0.9rem;">🔔</span>'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;'
                f'font-weight:600;color:#fca5a5;letter-spacing:0.04em;">'
                f'{unread_count} UNREAD</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:7px;'
                'padding:7px 2px;margin:8px 0 2px;">'
                '<span style="font-size:0.85rem;opacity:0.4;">🔔</span>'
                '<span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;'
                'color:rgba(255,255,255,0.3);letter-spacing:0.06em;">NO UNREAD MESSAGES</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Quarter filter ────────────────────────────────────────────────────
        _quarters = sorted(
            audits_df["quarter"].dropna().unique().tolist()
        ) if audits_df is not None and "quarter" in audits_df.columns else ["Q1 2026", "Q2 2026"]

        st.selectbox(
            "Reporting Quarter",
            _quarters,
            key="selected_quarter_filter",
            label_visibility="visible",
        )

        # ── Enterprise view toggle ────────────────────────────────────────────
        enterprise_view = st.toggle(
            "Enterprise View",
            key="enterprise_view",
            help="Show data for all platforms and regions",
        )
        if enterprise_view:
            st.markdown(
                '<div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;'
                'font-weight:700;letter-spacing:0.06em;color:#FFB81C;'
                'background:rgba(255,184,28,0.1);border:1px solid rgba(255,184,28,0.25);'
                'border-radius:5px;padding:5px 10px;margin-bottom:8px;">'
                '&#9670; ALL PLATFORMS · ALL REGIONS</div>',
                unsafe_allow_html=True,
            )

        # ── Platforms (three grouped sections) ───────────────────────────────
        st.markdown(
            "<div class='sidebar-section-header'>Platforms</div>",
            unsafe_allow_html=True,
        )
        _groups = _group_platforms(platforms["lines_of_business"])
        for group_name, key in _GROUP_KEYS.items():
            plats = _groups.get(group_name, [])
            if not plats:
                continue
            st.markdown(
                f"<div class='sidebar-group-header'>{group_name}</div>",
                unsafe_allow_html=True,
            )
            st.pills(
                group_name,
                plats,
                selection_mode="multi",
                key=key,
                label_visibility="collapsed",
                disabled=enterprise_view,
            )

        # ── Regions ───────────────────────────────────────────────────────────
        st.markdown(
            "<div class='sidebar-section-header'>Regions</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "region",
            platforms["regions"],
            selection_mode="multi",
            key="selected_regions",
            label_visibility="collapsed",
            disabled=enterprise_view,
        )

        st.divider()

        # ── Field completeness (custom HTML bar) ──────────────────────────────
        _df = audits_df if audits_df is not None else pd.DataFrame()
        completeness = di.compute_field_completeness(_df)
        pct = int(completeness * 100)
        bar_color = "#ef4444" if pct < 70 else "#f59e0b" if pct < 90 else "#FFB81C"
        status_label = "Needs attention" if pct < 70 else "Improving" if pct < 90 else "On track"
        st.markdown(
            '<div class="completeness-label">Field Completeness</div>'
            f'<div style="background:rgba(255,255,255,0.08);border-radius:99px;'
            f'height:5px;margin:6px 0 5px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:{bar_color};'
            f'border-radius:99px;transition:width 0.4s;"></div></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;'
            f'font-weight:700;color:{bar_color};">{pct}%</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.58rem;'
            f'color:rgba(255,255,255,0.35);letter-spacing:0.05em;">{status_label.upper()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
