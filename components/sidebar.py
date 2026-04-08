import streamlit as st
import pandas as pd
import data.data_interface as di

# ── Platform group definitions ────────────────────────────────────────────────
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

# RBC palette constants
_NAVY   = "#001e4d"
_BLUE   = "#002654"
_GOLD   = "#FFB81C"
_GOLD2  = "#e6a619"


def _group_platforms(platform_list: list) -> dict:
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


# ── CSS injected from INSIDE the sidebar (wins over Streamlit's own styles) ──
_SIDEBAR_CSS = """
<style>
/* ─── Sidebar shell ─── */
section[data-testid="stSidebar"],
div[data-testid="stSidebar"] {
    background: linear-gradient(160deg,#001430 0%,#001e4d 45%,#002a5e 100%) !important;
    background-color: #001e4d !important;
    border-right: 1px solid rgba(255,184,28,0.3) !important;
    box-shadow: 6px 0 32px rgba(0,0,0,0.35) !important;
}
/* ─── Make every child div transparent so gradient shows ─── */
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] > div > div > div,
div[data-testid="stSidebarContent"],
div[data-testid="stSidebarContent"] > div,
div[data-testid="stSidebarContent"] > div > div {
    background: transparent !important;
    background-color: transparent !important;
}
/* ─── Selectbox ─── */
section[data-testid="stSidebar"] label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.67rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] *:not(svg) {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: rgba(255,255,255,0.4) !important;
}
/* ─── Toggle ─── */
section[data-testid="stSidebar"] [data-testid="stToggle"] *,
section[data-testid="stSidebar"] [data-testid="stToggle"] label,
section[data-testid="stSidebar"] [data-testid="stToggle"] p,
section[data-testid="stSidebar"] [data-testid="stToggle"] span,
section[data-testid="stSidebar"] .stToggle *,
section[data-testid="stSidebar"] .stToggle label,
section[data-testid="stSidebar"] .stToggle p {
    color: rgba(255,255,255,0.82) !important;
}
/* ─── All widget labels (selectbox label, toggle label, etc.) ─── */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label * {
    color: rgba(255,255,255,0.55) !important;
}
/* Selectbox label specifically (overrides widget label above) */
section[data-testid="stSidebar"] .stSelectbox [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] .stSelectbox [data-testid="stWidgetLabel"] * {
    font-size: 0.67rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
/* ─── Pills container ─── */
section[data-testid="stSidebar"] [data-testid="stPills"] {
    gap: 5px !important;
}
/* ─── Pills — unselected: dark navy pill, white text ─── */
section[data-testid="stSidebar"] button[data-testid="stPillsButton"],
section[data-testid="stSidebar"] button[kind="pillsButton"] {
    background-color: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 5px !important;
    font-size: 0.69rem !important;
    font-weight: 500 !important;
    padding: 4px 10px !important;
    transition: all 0.18s ease !important;
}
section[data-testid="stSidebar"] button[data-testid="stPillsButton"],
section[data-testid="stSidebar"] button[data-testid="stPillsButton"] *,
section[data-testid="stSidebar"] button[kind="pillsButton"],
section[data-testid="stSidebar"] button[kind="pillsButton"] * {
    color: rgba(255,255,255,0.88) !important;
}
/* ─── Pills — hover ─── */
section[data-testid="stSidebar"] button[data-testid="stPillsButton"]:hover,
section[data-testid="stSidebar"] button[kind="pillsButton"]:hover {
    background-color: rgba(255,184,28,0.18) !important;
    border-color: rgba(255,184,28,0.55) !important;
}
section[data-testid="stSidebar"] button[data-testid="stPillsButton"]:hover,
section[data-testid="stSidebar"] button[data-testid="stPillsButton"]:hover *,
section[data-testid="stSidebar"] button[kind="pillsButton"]:hover,
section[data-testid="stSidebar"] button[kind="pillsButton"]:hover * {
    color: #FFB81C !important;
}
/* ─── Pills — selected ─── */
section[data-testid="stSidebar"] button[data-testid="stPillsButton"][aria-pressed="true"],
section[data-testid="stSidebar"] button[kind="pillsButton"][aria-pressed="true"] {
    background-color: #FFB81C !important;
    border-color: #FFB81C !important;
}
section[data-testid="stSidebar"] button[data-testid="stPillsButton"][aria-pressed="true"],
section[data-testid="stSidebar"] button[data-testid="stPillsButton"][aria-pressed="true"] *,
section[data-testid="stSidebar"] button[kind="pillsButton"][aria-pressed="true"],
section[data-testid="stSidebar"] button[kind="pillsButton"][aria-pressed="true"] * {
    color: #001430 !important;
    font-weight: 700 !important;
}
/* ─── Divider ─── */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 12px 0 !important;
}
/* ─── Scrollbar ─── */
section[data-testid="stSidebar"]::-webkit-scrollbar { width: 3px; }
section[data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: rgba(255,184,28,0.3); border-radius: 2px;
}
</style>
"""

# ── Reusable inline-style HTML builders (no CSS classes for colour) ───────────
def _section_header(title: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:8px;'
        f'margin:20px 0 10px;padding-bottom:8px;'
        f'border-bottom:1px solid rgba(255,184,28,0.25);">'
        f'<span style="display:inline-block;width:3px;height:14px;'
        f'background:#FFB81C;border-radius:2px;flex-shrink:0;"></span>'
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.6rem;'
        f'font-weight:700;letter-spacing:0.14em;text-transform:uppercase;'
        f'color:#FFB81C;">{title}</span>'
        f'</div>'
    )


def _group_header(title: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:7px;margin:10px 0 5px;">'
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.52rem;'
        f'font-weight:700;letter-spacing:0.11em;text-transform:uppercase;'
        f'color:rgba(255,255,255,0.42);white-space:nowrap;">{title}</span>'
        f'<span style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></span>'
        f'</div>'
    )


def render_sidebar(unread_count: int = 0, platforms: dict = None, audits_df: pd.DataFrame = None):
    if platforms is None:
        platforms = {"lines_of_business": [], "regions": []}

    with st.sidebar:
        # ── Inject CSS (must be first, runs inside sidebar context) ──────────
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(
            '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed'
            ':wght@700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
            '<div style="padding:18px 2px 16px;border-bottom:1px solid rgba(255,184,28,0.18);">'
            '<div style="display:flex;align-items:stretch;gap:12px;">'
            '<div style="width:4px;background:linear-gradient(180deg,#FFB81C,#e6a619);'
            'border-radius:2px;flex-shrink:0;"></div>'
            '<div>'
            '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:2rem;'
            'font-weight:800;color:#ffffff;letter-spacing:-0.01em;line-height:1;">'
            'AUDIT<span style="color:#FFB81C;">IQ</span>'
            '</div>'
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.46rem;'
            'font-weight:500;letter-spacing:0.22em;color:rgba(255,255,255,0.3);'
            'text-transform:uppercase;margin-top:4px;">Internal Audit Platform</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Notification ──────────────────────────────────────────────────────
        if unread_count > 0:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:9px;'
                f'background:rgba(220,38,38,0.12);border:1px solid rgba(220,38,38,0.28);'
                f'border-left:3px solid #ef4444;border-radius:7px;padding:8px 12px;margin:12px 0;">'
                f'<span style="font-size:0.85rem;">🔔</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;'
                f'font-weight:700;letter-spacing:0.06em;color:#fca5a5;">'
                f'{unread_count} UNREAD</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:8px;'
                'padding:8px 2px;margin:8px 0 4px;">'
                '<span style="font-size:0.78rem;opacity:0.3;">🔔</span>'
                '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.58rem;'
                'font-weight:600;letter-spacing:0.08em;color:rgba(255,255,255,0.28);">'
                'NO UNREAD MESSAGES</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Quarter ───────────────────────────────────────────────────────────
        _quarters = (
            sorted(audits_df["quarter"].dropna().unique().tolist())
            if audits_df is not None and "quarter" in audits_df.columns
            else ["Q1 2026", "Q2 2026"]
        )
        st.selectbox("Reporting Quarter", _quarters,
                     key="selected_quarter_filter", label_visibility="visible")

        # ── Enterprise toggle ─────────────────────────────────────────────────
        enterprise_view = st.toggle("Enterprise View", key="enterprise_view",
                                    help="Show data for all platforms and regions")
        if enterprise_view:
            st.markdown(
                '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.6rem;'
                'font-weight:700;letter-spacing:0.07em;color:#FFB81C;'
                'background:rgba(255,184,28,0.08);border:1px solid rgba(255,184,28,0.22);'
                'border-left:3px solid #FFB81C;border-radius:6px;padding:6px 10px;margin:4px 0 8px;">'
                '&#9670;&nbsp; ALL PLATFORMS · ALL REGIONS'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Platform groups ───────────────────────────────────────────────────
        st.markdown(_section_header("Platforms"), unsafe_allow_html=True)
        _groups = _group_platforms(platforms["lines_of_business"])
        for group_name, key in _GROUP_KEYS.items():
            plats = _groups.get(group_name, [])
            if not plats:
                continue
            st.markdown(_group_header(group_name), unsafe_allow_html=True)
            st.pills(group_name, plats, selection_mode="multi",
                     key=key, label_visibility="collapsed", disabled=enterprise_view)

        # ── Regions ───────────────────────────────────────────────────────────
        st.markdown(_section_header("Regions"), unsafe_allow_html=True)
        st.pills("region", platforms["regions"], selection_mode="multi",
                 key="selected_regions", label_visibility="collapsed",
                 disabled=enterprise_view)

        st.divider()

        # ── Field completeness (fully custom HTML, no st.progress) ────────────
        _df = audits_df if audits_df is not None else pd.DataFrame()
        completeness = di.compute_field_completeness(_df)
        pct = int(completeness * 100)
        bar_col  = "#ef4444" if pct < 70 else "#f59e0b" if pct < 90 else _GOLD
        status   = "NEEDS ATTENTION" if pct < 70 else "IMPROVING" if pct < 90 else "ON TRACK"
        st.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.56rem;'
            'font-weight:700;letter-spacing:0.12em;text-transform:uppercase;'
            'color:rgba(255,255,255,0.38);margin-bottom:7px;">Field Completeness</div>'
            f'<div style="background:rgba(255,255,255,0.07);border-radius:99px;height:4px;'
            f'margin-bottom:6px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:{bar_col};border-radius:99px;"></div>'
            f'</div>'
            f'<div style="display:flex;justify-content:space-between;">'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;'
            f'font-weight:700;color:{bar_col};">{pct}%</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.55rem;'
            f'color:rgba(255,255,255,0.28);letter-spacing:0.07em;">{status}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
