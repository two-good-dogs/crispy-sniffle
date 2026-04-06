import re
import streamlit as st
import pandas as pd

# ── Google Fonts (injected once per page render) ───────────────────────────────
_FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700'
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
    '<style>@keyframes kpi-rise{from{opacity:0;transform:translateY(8px)}'
    'to{opacity:1;transform:translateY(0)}}</style>'
)

# ── Chip / pill configs ────────────────────────────────────────────────────────
_TYPE_CFG = {
    "Owned Audit": ("#ede9fe", "#5b21b6"),
    "Indirect":    ("#f0f9ff", "#0369a1"),
    "":            ("#f3f4f6", "#9ca3af"),
}
_STATUS_CFG = {
    "Complete":    ("#d1fae5", "#065f46", "#10b981"),
    "In Progress": ("#dbeafe", "#1e40af", "#3b82f6"),
    "Fieldwork":   ("#fef3c7", "#92400e", "#f59e0b"),
}
_RATING_CFG = {
    "High":   ("#fee2e2", "#991b1b"),
    "Medium": ("#fef3c7", "#92400e"),
    "Low":    ("#d1fae5", "#065f46"),
    "N/A":    ("#f3f4f6", "#9ca3af"),
}
_REGION_CFG = {
    "USA":       ("#dbeafe", "#1e40af"),
    "APAC":      ("#d1fae5", "#065f46"),
    "Canada":    ("#fce7f3", "#9d174d"),
    "Caribbean": ("#fef3c7", "#92400e"),
    "UK":        ("#ede9fe", "#5b21b6"),
}
_CANONICAL_REGIONS = ["APAC", "Canada", "Caribbean", "USA", "UK"]

# ── Column name aliases (raw DB → normalised) ──────────────────────────────────
_RENAMES = {
    "audit_title":          "audit_name",
    "title":                "audit_name",
    "lead_audit_group":     "lead_group",
    "audit_group":          "lead_group",
    "engagement_id":        "audit_id",
    "regional_coverage":    "region",
    "report_rating":        "rating",
    "current_rating":       "rating",
    "impacted_audit_group": "impacted_platform",
}

# ── Table header labels ────────────────────────────────────────────────────────
_HEADER_LABELS = {
    "audit_id":    "ID",
    "audit_name":  "Audit",
    "audit_type":  "Type",
    "lead_group":  "Lead Group",
    "region":      "Region",
    "status":      "Status",
    "rating":      "Rating",
    "issue_count": "Issues",
}

# ── Table style strings ────────────────────────────────────────────────────────
_TH = (
    "font-family:'IBM Plex Mono',monospace;font-size:0.58rem;font-weight:500;"
    "letter-spacing:0.06em;text-transform:uppercase;color:#9ca3af;"
    "padding:8px 12px;text-align:left;background:#f9fafb;"
    "border-bottom:1px solid #e5e7eb;white-space:nowrap;"
)
_TD_BASE = "padding:7px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;white-space:nowrap;"

# ── KPI card style strings ─────────────────────────────────────────────────────
_CARD = (
    "flex:1;background:#ffffff;border-radius:12px;padding:22px 24px 18px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.06),0 4px 20px rgba(0,0,0,0.05);"
    "animation:kpi-rise .45s cubic-bezier(.22,1,.36,1) both;"
)
_CARD_LBL = (
    "font-family:'IBM Plex Mono',monospace;font-size:0.58rem;font-weight:600;"
    "letter-spacing:0.12em;text-transform:uppercase;color:#9ca3af;margin-bottom:10px;"
)
_CARD_NUM = (
    "font-family:'Barlow Condensed',sans-serif;font-size:4rem;font-weight:700;"
    "line-height:0.85;margin-bottom:12px;letter-spacing:-0.01em;"
)
_CARD_SEP  = "border:none;border-top:1px solid #f3f4f6;margin:0 0 10px 0;"
_CARD_META = "font-size:0.72rem;color:#6b7280;line-height:1.7;"


# ── Pill / badge helpers ───────────────────────────────────────────────────────

def _chip(text, bg="#f3f4f6", color="#374151", radius="999px",
          size="0.7rem", fw="600", pad="3px 10px"):
    return (
        f"<span style='display:inline-block;padding:{pad};border-radius:{radius};"
        f"font-size:{size};font-weight:{fw};background:{bg};color:{color};"
        f"white-space:nowrap;line-height:1.5;'>{text}</span>"
    )


def _kbadge(text, bg, color):
    """KPI card badge — mono font + letter-spacing, distinct from generic _chip."""
    return (
        f"<span style='display:inline-block;padding:3px 10px;border-radius:5px;"
        f"font-family:IBM Plex Mono,monospace;font-size:0.6rem;font-weight:700;"
        f"letter-spacing:0.08em;background:{bg};color:{color};"
        f"margin-bottom:14px;'>{text}</span>"
    )


def _type_pill(val):
    bg, color = _TYPE_CFG.get(str(val), ("#f3f4f6", "#9ca3af"))
    return _chip(val or "—", bg, color, radius="5px", size="0.68rem")


def _status_pill(val):
    bg, color, dot = _STATUS_CFG.get(str(val), ("#f3f4f6", "#6b7280", "#9ca3af"))
    return (
        f"<span style='display:inline-flex;align-items:center;gap:5px;padding:3px 10px;"
        f"border-radius:999px;font-size:0.7rem;font-weight:600;"
        f"background:{bg};color:{color};white-space:nowrap;line-height:1.5;'>"
        f"<span style='width:6px;height:6px;border-radius:50%;background:{dot};"
        f"flex-shrink:0;display:inline-block;'></span>{val}</span>"
    )


def _rating_pill(val):
    bg, color = _RATING_CFG.get(str(val), ("#f3f4f6", "#9ca3af"))
    return _chip(val or "—", bg, color)


def _region_pills(val):
    if not val or pd.isna(val) or str(val).strip() == "":
        return "<span style='color:#d1d5db;'>—</span>"
    parts = [p.strip() for p in str(val).split("|") if p.strip()]
    chips = [
        _chip(p, *_REGION_CFG.get(p, ("#f3f4f6", "#374151")),
              radius="4px", size="0.66rem", fw="500", pad="2px 7px")
        for p in parts
    ]
    return (
        "<span style='display:inline-flex;flex-wrap:wrap;gap:3px;'>"
        + "".join(chips) + "</span>"
    )


def _issue_badge(count):
    n = int(count) if not pd.isna(count) else 0
    if n == 0:
        return "<span style='color:#d1d5db;font-weight:600;'>—</span>"
    return _chip(str(n), "#fee2e2", "#dc2626", size="0.72rem", fw="700")


# ── HTML table renderer ────────────────────────────────────────────────────────

def _render_audit_table(df: pd.DataFrame):
    if df.empty:
        st.markdown(
            "<div style='padding:40px 0;text-align:center;color:#9ca3af;"
            "font-size:0.85rem;'>No audits match the current filters.</div>",
            unsafe_allow_html=True,
        )
        return

    df = df.rename(columns={k: v for k, v in _RENAMES.items() if k in df.columns})

    # Hide audit_type column when no platform filter is active (all values empty)
    if "audit_type" in df.columns and (df["audit_type"].fillna("") == "").all():
        df = df.drop(columns=["audit_type"])

    cols = [c for c in _HEADER_LABELS if c in df.columns]
    thead = "<tr>" + "".join(
        f"<th style='{_TH}'>{_HEADER_LABELS[c]}</th>" for c in cols
    ) + "</tr>"

    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        bg  = "#ffffff" if i % 2 == 0 else "#fafafa"
        td  = _TD_BASE + f"background:{bg};"
        cells = []
        for col in cols:
            val = row.get(col, "")
            if col == "audit_id":
                cell = (
                    f"<td style='{td}'><span style='font-family:\"IBM Plex Mono\","
                    f"monospace;font-size:0.66rem;color:#9ca3af;'>{val}</span></td>"
                )
            elif col == "audit_name":
                safe = str(val).replace("'", "&#39;").replace('"', "&quot;")
                cell = (
                    f"<td style='{td}max-width:280px;white-space:normal;'>"
                    f"<span style='font-size:0.78rem;font-weight:500;color:#111827;"
                    f"display:block;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap;' title='{safe}'>{val}</span></td>"
                )
            elif col == "audit_type":
                cell = f"<td style='{td}'>{_type_pill(val)}</td>"
            elif col == "lead_group":
                cell = (
                    f"<td style='{td}'><span style='font-size:0.78rem;"
                    f"font-weight:500;color:#374151;'>{val}</span></td>"
                )
            elif col == "region":
                cell = f"<td style='{td}'>{_region_pills(val)}</td>"
            elif col == "status":
                cell = f"<td style='{td}'>{_status_pill(str(val))}</td>"
            elif col == "rating":
                cell = f"<td style='{td}'>{_rating_pill(str(val))}</td>"
            elif col == "issue_count":
                cell = f"<td style='{td}text-align:center;'>{_issue_badge(val)}</td>"
            else:
                cell = f"<td style='{td}'>{val}</td>"
            cells.append(cell)
        rows.append("<tr>" + "".join(cells) + "</tr>")

    st.markdown(
        '<div style="overflow:auto;max-height:460px;border-radius:10px;'
        'border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead style="position:sticky;top:0;z-index:1;">{thead}</thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>',
        unsafe_allow_html=True,
    )


# ── Local filter helper ────────────────────────────────────────────────────────

def _filter_audits(df, search="", regions=None, statuses=None, audit_types=None):
    if search:
        q = search.lower()
        mask = (
            df["audit_name"].str.lower().str.contains(q, na=False)
            | df["audit_id"].str.lower().str.contains(q, na=False)
            | df["lead_group"].str.lower().str.contains(q, na=False)
        )
        df = df[mask]
    if regions:
        sel = set(regions)
        df = df[
            df["region"].fillna("").apply(
                lambda x: bool({p.strip() for p in x.split("|") if p.strip()} & sel)
            )
        ]
    if statuses:
        df = df[df["status"].isin(statuses)]
    if audit_types and "audit_type" in df.columns:
        df = df[df["audit_type"].isin(audit_types)]
    return df


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_portfolio_overview(audits_df: pd.DataFrame, snapshot_mode: bool = False):

    owned_count        = (audits_df["audit_type"] == "Owned Audit").sum()
    indirect_count     = (audits_df["audit_type"] == "Indirect").sum()
    total_count        = len(audits_df)
    all_issues         = int(audits_df["issue_count"].sum())
    overdue_count      = int(audits_df["is_overdue"].sum())
    out_of_scope_count = int(audits_df["out_of_scope"].sum())

    # ── Framework note ────────────────────────────────────────────────────────
    owned_chip    = _chip("OWNED",    "#ede9fe", "#5b21b6", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    indirect_chip = _chip("INDIRECT", "#f0f9ff", "#0369a1", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    issues_chip   = _chip("ISSUES",   "#fee2e2", "#991b1b", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    st.markdown(
        _FONT_LINK
        + '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px;'
          'background:#f0f7ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;'
          'border-radius:8px;padding:11px 16px;margin-bottom:16px;">'
        + '<span style="font-size:1rem;">ℹ</span>'
        + '<span style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;'
          'font-weight:700;letter-spacing:0.08em;color:#1e3a5f;text-transform:uppercase;">Audit Count Framework</span>'
        + '<span style="color:#bfdbfe;">|</span>'
        + f'<span style="font-size:0.76rem;color:#374151;">{owned_chip}&nbsp;Lead Audit Group matches selected platform</span>'
        + '<span style="color:#bfdbfe;">·</span>'
        + f'<span style="font-size:0.76rem;color:#374151;">{indirect_chip}&nbsp;Platform in Impacted Platform field</span>'
        + '<span style="color:#bfdbfe;">·</span>'
        + f'<span style="font-size:0.76rem;color:#374151;">{issues_chip}&nbsp;Remediation Owner field</span>'
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Four KPI cards ────────────────────────────────────────────────────────
    def _card_html(label, value, badge_text, badge_bg, badge_fg, accent, meta, delay):
        return (
            f'<div style="{_CARD}border-top:4px solid {accent};animation-delay:{delay};">'
            f'<div style="{_CARD_LBL}">{label}</div>'
            f'<div style="{_CARD_NUM}color:{accent};">{value}</div>'
            f'{_kbadge(badge_text, badge_bg, badge_fg)}'
            f'<hr style="{_CARD_SEP}">'
            f'<div style="{_CARD_META}">{meta}</div>'
            f'</div>'
        )

    cards = (
        '<div style="display:flex;gap:14px;margin-bottom:4px;">'
        + _card_html("Owned Coverage", owned_count, "OWNED", "#d1fae5", "#065f46", "#059669",
                     "Lead Audit Group field", "0s")
        + _card_html("Indirect Coverage", indirect_count, "INDIRECT", "#dbeafe", "#1e40af", "#2563eb",
                     "Impacted Platform field", ".07s")
        + _card_html("Total Footprint", total_count, "DE-DUPLICATED", "#fef3c7", "#92400e", "#d97706",
                     f'Owned&nbsp;<strong style="color:#374151;">{owned_count}</strong>'
                     f'&ensp;·&ensp;Indirect&nbsp;<strong style="color:#374151;">{indirect_count}</strong>',
                     ".14s")
        + _card_html("Open Issues", all_issues, "ISSUES", "#fee2e2", "#991b1b", "#dc2626",
                     f'Remediation Owner field<br>'
                     f'Overdue&nbsp;<strong style="color:#dc2626;">{overdue_count}</strong>'
                     f'&ensp;·&ensp;Out-of-scope&nbsp;<strong style="color:#374151;">{out_of_scope_count}</strong>',
                     ".21s")
        + '</div>'
    )
    st.markdown(cards, unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Filter row ────────────────────────────────────────────────────────────
    region_opts = [
        r for r in _CANONICAL_REGIONS
        if any(
            r in re.split(r"\s*[|,;]\s*", str(v))
            for v in audits_df["region"].dropna()
        )
    ]

    fc1, fc2, fc3 = st.columns([3, 2, 2])
    with fc1:
        search = st.text_input(
            "Search audits",
            placeholder="Search by name, ID, or lead group…",
            key="audit_search",
            label_visibility="collapsed",
        )
    with fc2:
        region_filter = st.multiselect(
            "All Regions",
            options=region_opts,
            key="audit_region_filter",
            placeholder="All Regions",
            label_visibility="collapsed",
        )
    with fc3:
        status_filter = st.multiselect(
            "All Statuses",
            options=["Complete", "In Progress", "Fieldwork"],
            key="audit_status_filter",
            placeholder="All Statuses",
            label_visibility="collapsed",
        )

    filtered   = _filter_audits(audits_df, search=search,
                                regions=region_filter or None,
                                statuses=status_filter or None)
    owned_f    = _filter_audits(filtered, audit_types=["Owned Audit"])
    indirect_f = _filter_audits(filtered, audit_types=["Indirect"])

    st.markdown(
        f"<div style='font-size:0.88rem;font-weight:600;color:#1a1f2e;margin:8px 0 4px;'>"
        f"All Audits — <span style='color:#6b7280;font-weight:400;'>{len(filtered)} total</span></div>",
        unsafe_allow_html=True,
    )

    sub_tabs = st.tabs([
        f"All Audits  {len(filtered)}",
        f"Owned Audits  {len(owned_f)}",
        f"Indirect Coverage  {len(indirect_f)}",
    ])

    with sub_tabs[0]:
        _render_audit_table(filtered)
    with sub_tabs[1]:
        _render_audit_table(owned_f)
    with sub_tabs[2]:
        _render_audit_table(indirect_f)
