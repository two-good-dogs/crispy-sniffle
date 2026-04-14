import re

import pandas as pd
import streamlit as st

import data.data_interface as di

# ── Category display config ───────────────────────────────────────────────────
_CATEGORIES = [
    {"id": "financial_market",    "label": "Financial Market",        "color": "#60a5fa", "dim": "rgba(96,165,250,0.08)"},
    {"id": "credit_balance",      "label": "Credit & Balance Sheet",  "color": "#a78bfa", "dim": "rgba(167,139,250,0.08)"},
    {"id": "operational_conduct", "label": "Operational & Conduct",   "color": "#f59e0b", "dim": "rgba(245,158,11,0.08)"},
    {"id": "tech_cyber",          "label": "Technology & Cyber",      "color": "#34d399", "dim": "rgba(52,211,153,0.08)"},
    {"id": "regulatory_legal",    "label": "Regulatory & Legal",      "color": "#f87171", "dim": "rgba(248,113,113,0.08)"},
    {"id": "governance_strategy", "label": "Governance & Strategy",   "color": "#94a3b8", "dim": "rgba(148,163,184,0.08)"},
]
_CAT_MAP = {c["id"]: c for c in _CATEGORIES}

_TIER_CFG = {
    "critical": {"color": "#fca5a5", "bg": "rgba(248,113,113,0.15)", "label": "CRIT"},
    "high":     {"color": "#fde68a", "bg": "rgba(245,158,11,0.15)",  "label": "HIGH"},
    "standard": {"color": "#93c5fd", "bg": "rgba(96,165,250,0.15)",  "label": "STD"},
}

_FONT_LINK = (
    '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
)


# ── Coverage cell ─────────────────────────────────────────────────────────────

def _coverage_cell(count: int) -> str:
    if count == 0:
        return (
            "<div style='background:#131820;border:1px solid rgba(255,255,255,0.05);"
            "border-radius:5px;padding:8px 4px;text-align:center;min-width:64px;'>"
            "<span style='color:rgba(255,255,255,0.12);font-size:0.9rem;'>—</span>"
            "</div>"
        )
    if count == 1:
        col, bg, bdr, lbl, fill = "#fca5a5", "rgba(248,113,113,0.12)", "rgba(248,113,113,0.3)", "LOW", 34
    elif count == 2:
        col, bg, bdr, lbl, fill = "#fde68a", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)", "MOD", 67
    else:
        col, bg, bdr, lbl, fill = "#6ee7b7", "rgba(52,211,153,0.12)", "rgba(52,211,153,0.3)", "STG", 100
    return (
        f"<div style='background:{bg};border:1px solid {bdr};border-radius:5px;"
        f"padding:8px 4px;text-align:center;min-width:64px;'>"
        f"<div style='font-family:\"Barlow Condensed\",sans-serif;font-size:1.4rem;"
        f"font-weight:700;color:{col};line-height:1;'>{count}</div>"
        f"<div style='height:2px;background:rgba(255,255,255,0.05);border-radius:2px;margin:3px 6px 2px;'>"
        f"<div style='width:{fill}%;height:100%;background:{col};border-radius:2px;opacity:0.65;'></div>"
        f"</div>"
        f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.44rem;font-weight:700;"
        f"letter-spacing:0.1em;color:{col};opacity:0.75;'>{lbl}</div>"
        f"</div>"
    )


# ── Control density cell ──────────────────────────────────────────────────────

def _pct(num: int, denom: int) -> int:
    return round(num / denom * 100) if denom else 0


def _control_density_cell(stats: dict | None) -> str:
    """Dark cell: control count + DE/OE/TP mini progress bars."""
    if not stats or stats.get("total", 0) == 0:
        return (
            "<div style='background:#131820;border:1px solid rgba(255,255,255,0.05);"
            "border-radius:5px;padding:8px 4px;text-align:center;min-width:80px;'>"
            "<span style='color:rgba(255,255,255,0.12);font-size:0.9rem;'>—</span>"
            "</div>"
        )

    n       = stats["total"]
    de_pct  = _pct(stats.get("de_ef",    0), n)
    oe_pct  = _pct(stats.get("oe_met",   0), n)
    tp_pct  = _pct(stats.get("test_pass", 0), n)

    if tp_pct >= 85:
        num_col, bg, bdr = "#6ee7b7", "rgba(52,211,153,0.10)",  "rgba(52,211,153,0.25)"
    elif tp_pct >= 70:
        num_col, bg, bdr = "#fde68a", "rgba(245,158,11,0.10)",  "rgba(245,158,11,0.25)"
    else:
        num_col, bg, bdr = "#fca5a5", "rgba(248,113,113,0.10)", "rgba(248,113,113,0.25)"

    def _bar(val: int, col: str) -> str:
        return (
            f"<div style='height:3px;background:rgba(255,255,255,0.05);border-radius:2px;flex:1;'>"
            f"<div style='width:{val}%;height:100%;background:{col};border-radius:2px;opacity:0.75;'></div>"
            f"</div>"
        )

    _rs = "display:flex;align-items:center;gap:4px;margin-bottom:3px;"
    _ls = "font-family:'IBM Plex Mono',monospace;font-size:0.42rem;color:rgba(255,255,255,0.32);width:14px;flex-shrink:0;"

    has_results = any(k in stats for k in ("de_ef", "oe_met", "test_pass"))
    bars = ""
    if has_results:
        bars = (
            f"<div style='margin-top:4px;'>"
            f"<div style='{_rs}'><span style='{_ls}'>DE</span>{_bar(de_pct,'#6ee7b7')}"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.42rem;color:#6ee7b7;width:22px;text-align:right;'>{de_pct}%</span></div>"
            f"<div style='{_rs}'><span style='{_ls}'>OE</span>{_bar(oe_pct,'#93c5fd')}"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.42rem;color:#93c5fd;width:22px;text-align:right;'>{oe_pct}%</span></div>"
            f"<div style='{_rs}margin-bottom:0;'><span style='{_ls}'>TP</span>{_bar(tp_pct,'#fde68a')}"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.42rem;color:#fde68a;width:22px;text-align:right;'>{tp_pct}%</span></div>"
            f"</div>"
        )

    return (
        f"<div style='background:{bg};border:1px solid {bdr};border-radius:5px;padding:8px 6px;min-width:80px;'>"
        f"<div style='font-family:\"Barlow Condensed\",sans-serif;font-size:1.4rem;font-weight:700;"
        f"color:{num_col};line-height:1;text-align:center;'>{n}</div>"
        f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.42rem;font-weight:700;"
        f"letter-spacing:0.1em;color:rgba(255,255,255,0.28);text-align:center;margin-bottom:2px;'>CTRL</div>"
        f"{bars}"
        f"</div>"
    )


# ── Data helpers ──────────────────────────────────────────────────────────────

def _get_context() -> dict:
    return {
        "enterprise": st.session_state.get("enterprise_view", False),
        "platforms": list(set(
            st.session_state.get("sel_lob", []) +
            st.session_state.get("sel_functions", []) +
            st.session_state.get("sel_tao", []) +
            st.session_state.get("sel_other", [])
        )),
        "regions":  st.session_state.get("selected_regions", []),
        "quarter":  st.session_state.get("selected_quarter_filter", ""),
    }


def _build_coverage_matrix(audits: pd.DataFrame, by_region: bool, dim_values: list) -> dict:
    """
    Returns {(stripe_id, dim_value): unique_audit_count}.
    Handles pipe-separated region/platform fields correctly.
    """
    from collections import defaultdict
    bucket: dict = defaultdict(set)
    dim_set = set(dim_values)

    for rec in audits.to_dict("records"):
        aid = str(rec.get("audit_id", ""))
        stripes = [str(s).strip() for s in (rec.get("risk_stripes") or [])]
        if not stripes:
            continue

        if by_region:
            raw = str(rec.get("region", "") or "")
            parts = [p.strip() for p in re.split(r"[|,;]", raw) if p.strip()]
            if "Global" in parts:
                parts = list(dim_values)
            dims = [d for d in parts if d in dim_set]
        else:
            lead    = str(rec.get("lead_group", "") or "").strip()
            imp_raw = str(rec.get("impacted_platform", "") or "")
            ae_raw  = str(rec.get("ae_platforms", "") or "")
            all_p   = {lead}
            all_p  |= {p.strip() for p in re.split(r"[|,]", imp_raw) if p.strip()}
            all_p  |= {p.strip() for p in ae_raw.split("|") if p.strip()}
            dims = [d for d in dim_values if d in all_p]

        for sid in stripes:
            for d in dims:
                bucket[(sid, d)].add(aid)

    return {k: len(v) for k, v in bucket.items()}


def _stripe_totals(audits: pd.DataFrame, all_stripes: list) -> dict:
    """Unique audit count per stripe_id, ignoring dimension."""
    from collections import defaultdict
    known = {s["id"] for s in all_stripes}
    totals: dict = defaultdict(set)
    for rec in audits.to_dict("records"):
        aid = str(rec.get("audit_id", ""))
        for sid in (rec.get("risk_stripes") or []):
            sid = str(sid).strip()
            if sid in known:
                totals[sid].add(aid)
    return {k: len(v) for k, v in totals.items()}


def _ctrl_stripe_totals(stripe_controls: pd.DataFrame) -> dict:
    """Per-stripe control counts + result tallies, ignoring dimension."""
    if stripe_controls.empty or "control_type" not in stripe_controls.columns:
        return {}
    result = {}
    for sid, grp in stripe_controls.groupby("control_type"):
        sid = str(sid).strip()
        n   = len(grp)
        de  = int((grp["de_result"]    == "EF").sum())   if "de_result"    in grp.columns else 0
        oe  = int((grp["oe_result"]    == "M").sum())    if "oe_result"    in grp.columns else 0
        tp  = int((grp["test_result"]  == "Pass").sum()) if "test_result"  in grp.columns else 0
        result[sid] = {"total": n, "de_ef": de, "oe_met": oe, "test_pass": tp}
    return result


def _build_control_matrix(
    stripe_controls: pd.DataFrame,
    audits: pd.DataFrame,
    by_region: bool,
    dim_values: list,
) -> dict:
    """
    Returns {(stripe_id, dim_value): {"total": N, "de_ef": N, "oe_met": N, "test_pass": N}}.
    Joins stripe_controls → audits on audit_id to inherit region / platform per control row.
    """
    if stripe_controls.empty or audits.empty:
        return {}

    audit_cols = ["audit_id", "region", "lead_group", "impacted_platform", "ae_platforms"]
    audit_slim = audits[[c for c in audit_cols if c in audits.columns]].drop_duplicates("audit_id")
    merged = stripe_controls.merge(audit_slim, on="audit_id", how="inner")
    if merged.empty:
        return {}

    dim_set = set(dim_values)
    from collections import defaultdict
    bucket: dict = defaultdict(lambda: {"total": 0, "de_ef": 0, "oe_met": 0, "test_pass": 0})

    for rec in merged.to_dict("records"):
        sid = str(rec.get("control_type", "") or "").strip()
        if not sid:
            continue

        de = str(rec.get("de_result",   "") or "")
        oe = str(rec.get("oe_result",   "") or "")
        tp = str(rec.get("test_result", "") or "")

        if by_region:
            raw   = str(rec.get("region", "") or "")
            parts = [p.strip() for p in re.split(r"[|,;]", raw) if p.strip()]
            if "Global" in parts:
                parts = list(dim_values)
            dims = [d for d in parts if d in dim_set]
        else:
            lead    = str(rec.get("lead_group", "") or "").strip()
            imp_raw = str(rec.get("impacted_platform", "") or "")
            ae_raw  = str(rec.get("ae_platforms", "") or "")
            all_p   = {lead}
            all_p  |= {p.strip() for p in re.split(r"[|,]", imp_raw) if p.strip()}
            all_p  |= {p.strip() for p in ae_raw.split("|") if p.strip()}
            dims = [d for d in dim_values if d in all_p]

        for d in dims:
            cell = bucket[(sid, d)]
            cell["total"]     += 1
            cell["de_ef"]     += int(de == "EF")
            cell["oe_met"]    += int(oe == "M")
            cell["test_pass"] += int(tp == "Pass")

    return dict(bucket)


# ── Context banner ─────────────────────────────────────────────────────────────

def _render_context_banner(ctx: dict):
    if ctx["enterprise"]:
        label = "Enterprise · All Platforms · All Regions"
        col, bg, bdr = "#6ee7b7", "rgba(52,211,153,0.08)", "rgba(52,211,153,0.3)"
    elif ctx["platforms"]:
        pts   = ctx["platforms"]
        label = " · ".join(pts[:3]) + (f" +{len(pts)-3}" if len(pts) > 3 else "")
        col, bg, bdr = "#93c5fd", "rgba(96,165,250,0.08)", "rgba(96,165,250,0.3)"
    elif ctx["regions"]:
        label = " · ".join(ctx["regions"])
        col, bg, bdr = "#fde68a", "rgba(245,158,11,0.08)", "rgba(245,158,11,0.3)"
    else:
        label = "All Platforms · All Regions"
        col, bg, bdr = "#94a3b8", "rgba(148,163,184,0.06)", "rgba(148,163,184,0.2)"

    q = ctx.get("quarter", "")
    q_html = (
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.58rem;'
        f'color:rgba(255,255,255,0.28);margin-right:14px;">{q}</span>'
    ) if q else ""

    st.markdown(
        f'{_FONT_LINK}'
        f'<div style="background:#0d1117;border:1px solid rgba(255,255,255,0.07);'
        f'border-radius:8px;padding:10px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">'
        f'{q_html}'
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.54rem;font-weight:700;'
        f'letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.25);">SCOPE</span>'
        f'<span style="background:{bg};border:1px solid {bdr};border-radius:4px;padding:3px 10px;'
        f'font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;font-weight:600;'
        f'letter-spacing:0.05em;color:{col};">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── KPI strip ─────────────────────────────────────────────────────────────────

def _render_kpi_strip(audits: pd.DataFrame, all_stripes: list, ctrl_totals: dict):
    """
    5 KPI cards: 3 audit-level + 2 control-level.
    ctrl_totals: {stripe_id: {"total": N, ...}} from _ctrl_stripe_totals().
    """
    totals       = _stripe_totals(audits, all_stripes)
    n_stripes    = len(all_stripes)
    covered      = len(totals)
    cov_pct      = round(covered / n_stripes * 100) if n_stripes else 0
    critical_ids = {s["id"] for s in all_stripes if s.get("tier") == "critical"}
    critical_gaps = len(critical_ids - set(totals))

    # Control-level aggregates across all known stripes
    total_ctrl = sum(v["total"]     for v in ctrl_totals.values())
    total_pass = sum(v["test_pass"] for v in ctrl_totals.values())
    pass_rate  = _pct(total_pass, total_ctrl) if total_ctrl else None

    if pass_rate is None:
        pass_val, pass_badge, pass_meta, pass_ncol = "N/A", "NO DATA", "No control results available", "#94a3b8"
    elif pass_rate >= 85:
        pass_val, pass_badge, pass_ncol = f"{pass_rate}%", "ON TRACK", "#6ee7b7"
        pass_meta = f"{total_pass} of {total_ctrl} controls passed"
    elif pass_rate >= 70:
        pass_val, pass_badge, pass_ncol = f"{pass_rate}%", "MONITOR", "#fde68a"
        pass_meta = f"{total_pass} of {total_ctrl} controls passed"
    else:
        pass_val, pass_badge, pass_ncol = f"{pass_rate}%", "AT RISK", "#fca5a5"
        pass_meta = f"{total_pass} of {total_ctrl} controls passed"

    cards = [
        ("STRIPES MONITORED", str(n_stripes),    f"{covered} ACTIVE",
         f"{n_stripes - covered} without coverage",    "owned",    "#6ee7b7"),
        ("COVERAGE RATE",     f"{cov_pct}%",      "STRIPE BREADTH",
         f"{covered} of {n_stripes} stripes",          "indirect", "#93c5fd"),
        ("CONTROLS TESTED",   str(total_ctrl),    "RCM CONTROLS",
         f"Across {len(audits)} audit(s)",              "footprint","#fde68a"),
        ("CRITICAL GAPS",     str(critical_gaps), f"OF {len(critical_ids)} CRITICAL",
         "Stripes with no audit coverage",             "issues",   "#fca5a5"),
        ("CONTROLS PASS RATE", pass_val,           pass_badge,
         pass_meta,                                     "owned" if pass_rate and pass_rate >= 85
                                                         else "footprint" if pass_rate and pass_rate >= 70
                                                         else "issues" if pass_rate is not None
                                                         else "indirect",
         pass_ncol),
    ]

    cols = st.columns(5)
    for i, (col, (lbl, val, badge, meta, cls, ncol)) in enumerate(zip(cols, cards)):
        with col:
            st.markdown(
                f"<div class='kpi-card {cls}' style='animation-delay:{i*0.07:.2f}s;'>"
                f"<div class='kpi-label'>{lbl}</div>"
                f"<div class='kpi-number' style='color:{ncol};font-size:3rem;'>{val}</div>"
                f"<span class='kpi-badge'>{badge}</span>"
                f"<hr class='kpi-divider'>"
                f"<div class='kpi-meta'>{meta}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Heatmap matrix ─────────────────────────────────────────────────────────────

def _render_heatmap_matrix(matrix: dict, totals: dict, all_stripes: list, dim_values: list):
    n_cols = len(dim_values) + 2  # stripe name + dims + total

    # Header
    th = (
        "padding:10px 8px;font-family:'IBM Plex Mono',monospace;font-size:0.56rem;"
        "font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.4);"
        "white-space:nowrap;text-align:center;border-bottom:1px solid rgba(255,255,255,0.07);"
    )
    headers = f"<th style='{th}text-align:left;min-width:200px;padding-left:14px;'>Risk Stripe</th>"
    for dv in dim_values:
        label = dv if len(dv) <= 16 else dv[:13] + "…"
        headers += f"<th style='{th}min-width:72px;'>{label}</th>"
    headers += f"<th style='{th}min-width:72px;color:rgba(255,255,255,0.25);'>TOTAL</th>"

    body = ""
    for cat in _CATEGORIES:
        cat_stripes = [s for s in all_stripes if s.get("category") == cat["id"]]
        if not cat_stripes:
            continue

        # Category separator
        body += (
            f"<tr><td colspan='{n_cols}' style='"
            f"background:rgba(255,255,255,0.02);padding:8px 14px;"
            f"border-top:1px solid rgba(255,255,255,0.06);'>"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.54rem;"
            f"font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{cat['color']};'>"
            f"◈ {cat['label']}</span>"
            f"</td></tr>"
        )

        for stripe in cat_stripes:
            sid = stripe["id"]
            tier = _TIER_CFG.get(stripe.get("tier", "standard"), _TIER_CFG["standard"])
            row_total = totals.get(sid, 0)

            name_cell = (
                f"<td style='padding:6px 10px 6px 14px;"
                f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                f"<div style='display:flex;align-items:center;gap:8px;'>"
                f"<span style='font-size:0.85rem;flex-shrink:0;'>{stripe.get('icon','')}</span>"
                f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.67rem;font-weight:600;"
                f"color:rgba(255,255,255,0.8);white-space:nowrap;'>{stripe['name']}</span>"
                f"<span style='margin-left:auto;background:{tier['bg']};border-radius:3px;"
                f"padding:1px 6px;font-family:\"IBM Plex Mono\",monospace;font-size:0.43rem;"
                f"font-weight:700;letter-spacing:0.1em;color:{tier['color']};flex-shrink:0;'>"
                f"{tier['label']}</span>"
                f"</div></td>"
            )

            dim_cells = "".join(
                f"<td style='padding:5px 6px;border-bottom:1px solid rgba(255,255,255,0.04);"
                f"text-align:center;'>{_coverage_cell(matrix.get((sid, dv), 0))}</td>"
                for dv in dim_values
            )

            total_cell = (
                f"<td style='padding:5px 6px;border-bottom:1px solid rgba(255,255,255,0.04);"
                f"text-align:center;opacity:0.7;'>{_coverage_cell(row_total)}</td>"
            )

            body += f"<tr style='background:transparent;'>{name_cell}{dim_cells}{total_cell}</tr>"

    st.markdown(
        f"{_FONT_LINK}"
        f"<div style='overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.07);'>"
        f"<table style='width:100%;border-collapse:collapse;background:#0d1117;'>"
        f"<thead><tr style='background:#111827;'>{headers}</tr></thead>"
        f"<tbody>{body}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )


# ── Control heatmap matrix ────────────────────────────────────────────────────

def _render_control_legend():
    st.markdown(
        "<div style='display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap;'>"
        "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.55rem;"
        "color:rgba(255,255,255,0.28);'>Legend:</span>"
        "<span style='background:#131820;border:1px solid rgba(255,255,255,0.05);border-radius:4px;"
        "padding:2px 8px;font-size:0.6rem;color:rgba(255,255,255,0.18);'>— No controls</span>"
        "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.52rem;"
        "color:rgba(255,255,255,0.2);margin-left:8px;'>Pass rate →</span>"
        "<span style='background:rgba(248,113,113,0.12);border:1px solid rgba(248,113,113,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#fca5a5;'>&lt;70% At Risk</span>"
        "<span style='background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#fde68a;'>70–84% Monitor</span>"
        "<span style='background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#6ee7b7;'>≥85% On Track</span>"
        "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.52rem;"
        "color:rgba(255,255,255,0.2);margin-left:8px;'>Bars →</span>"
        "<span style='font-size:0.58rem;color:#6ee7b7;'>DE</span>"
        "<span style='font-size:0.58rem;color:#93c5fd;'>OE</span>"
        "<span style='font-size:0.58rem;color:#fde68a;'>TP</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_control_heatmap_matrix(
    ctrl_matrix: dict,
    ctrl_totals: dict,
    all_stripes: list,
    dim_values: list,
):
    """Same table skeleton as audit heatmap but cells show control density."""
    n_cols = len(dim_values) + 2

    th = (
        "padding:10px 8px;font-family:'IBM Plex Mono',monospace;font-size:0.56rem;"
        "font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.4);"
        "white-space:nowrap;text-align:center;border-bottom:1px solid rgba(255,255,255,0.07);"
    )
    headers = f"<th style='{th}text-align:left;min-width:200px;padding-left:14px;'>Risk Stripe</th>"
    for dv in dim_values:
        label = dv if len(dv) <= 16 else dv[:13] + "…"
        headers += f"<th style='{th}min-width:88px;'>{label}</th>"
    headers += f"<th style='{th}min-width:88px;color:rgba(255,255,255,0.25);'>ALL DIMS</th>"

    body = ""
    for cat in _CATEGORIES:
        cat_stripes = [s for s in all_stripes if s.get("category") == cat["id"]]
        if not cat_stripes:
            continue

        body += (
            f"<tr><td colspan='{n_cols}' style='"
            f"background:rgba(255,255,255,0.02);padding:8px 14px;"
            f"border-top:1px solid rgba(255,255,255,0.06);'>"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.54rem;"
            f"font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:{cat['color']};'>"
            f"◈ {cat['label']}</span>"
            f"</td></tr>"
        )

        for stripe in cat_stripes:
            sid  = stripe["id"]
            tier = _TIER_CFG.get(stripe.get("tier", "standard"), _TIER_CFG["standard"])

            name_cell = (
                f"<td style='padding:6px 10px 6px 14px;"
                f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                f"<div style='display:flex;align-items:center;gap:8px;'>"
                f"<span style='font-size:0.85rem;flex-shrink:0;'>{stripe.get('icon','')}</span>"
                f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.67rem;font-weight:600;"
                f"color:rgba(255,255,255,0.8);white-space:nowrap;'>{stripe['name']}</span>"
                f"<span style='margin-left:auto;background:{tier['bg']};border-radius:3px;"
                f"padding:1px 6px;font-family:\"IBM Plex Mono\",monospace;font-size:0.43rem;"
                f"font-weight:700;letter-spacing:0.1em;color:{tier['color']};flex-shrink:0;'>"
                f"{tier['label']}</span>"
                f"</div></td>"
            )

            dim_cells = "".join(
                f"<td style='padding:5px 6px;border-bottom:1px solid rgba(255,255,255,0.04);"
                f"text-align:center;'>"
                f"{_control_density_cell(ctrl_matrix.get((sid, dv)))}</td>"
                for dv in dim_values
            )

            total_cell = (
                f"<td style='padding:5px 6px;border-bottom:1px solid rgba(255,255,255,0.04);"
                f"text-align:center;opacity:0.75;'>"
                f"{_control_density_cell(ctrl_totals.get(sid))}</td>"
            )

            body += f"<tr style='background:transparent;'>{name_cell}{dim_cells}{total_cell}</tr>"

    st.markdown(
        f"{_FONT_LINK}"
        f"<div style='overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.07);'>"
        f"<table style='width:100%;border-collapse:collapse;background:#0d1117;'>"
        f"<thead><tr style='background:#111827;'>{headers}</tr></thead>"
        f"<tbody>{body}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )


# ── Gap analysis ──────────────────────────────────────────────────────────────

def _render_gap_panel(matrix: dict, all_stripes: list, dim_values: list):
    tier_gaps: dict = {"critical": [], "high": [], "standard": []}

    for stripe in all_stripes:
        sid  = stripe["id"]
        tier = stripe.get("tier", "standard")
        gaps = [dv for dv in dim_values if matrix.get((sid, dv), 0) == 0]
        for dv in gaps:
            tier_gaps[tier].append((stripe, dv))

    total_gaps = sum(len(v) for v in tier_gaps.values())

    if total_gaps == 0:
        st.markdown(
            "<div style='background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);"
            "border-left:3px solid #34d399;border-radius:6px;padding:12px 16px;'>"
            "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.75rem;font-weight:700;"
            "color:#6ee7b7;letter-spacing:0.05em;'>FULL COVERAGE</span>"
            "<p style='font-size:0.8rem;color:rgba(255,255,255,0.45);margin:4px 0 0;'>"
            "All risk stripes have at least one audit across every active dimension.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    tier_meta = [
        ("critical", "#fca5a5", "rgba(248,113,113,0.12)", "rgba(248,113,113,0.25)", "CRITICAL GAPS"),
        ("high",     "#fde68a", "rgba(245,158,11,0.12)",  "rgba(245,158,11,0.25)",  "HIGH PRIORITY"),
        ("standard", "#93c5fd", "rgba(96,165,250,0.12)",  "rgba(96,165,250,0.25)",  "STANDARD"),
    ]

    for tier_id, col, bg, bdr, tier_lbl in tier_meta:
        gaps = tier_gaps[tier_id]
        if not gaps:
            continue

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin:12px 0 8px;'>"
            f"<span style='background:{bg};border:1px solid {bdr};border-radius:3px;padding:2px 8px;"
            f"font-family:\"IBM Plex Mono\",monospace;font-size:0.54rem;font-weight:700;"
            f"letter-spacing:0.1em;color:{col};'>{tier_lbl}</span>"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.6rem;"
            f"color:rgba(255,255,255,0.28);'>{len(gaps)} gap(s)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        chips = "".join(
            f"<div style='background:#131820;border:1px solid rgba(255,255,255,0.07);"
            f"border-left:2px solid {col};border-radius:5px;padding:5px 12px;"
            f"font-family:\"IBM Plex Mono\",monospace;font-size:0.62rem;'>"
            f"<span style='color:rgba(255,255,255,0.72);font-weight:600;'>"
            f"{s.get('icon','')} {s['name']}</span>"
            f"<span style='color:rgba(255,255,255,0.25);margin:0 6px;'>·</span>"
            f"<span style='color:rgba(255,255,255,0.38);'>{dv}</span>"
            f"</div>"
            for s, dv in gaps
        )
        st.markdown(
            f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;'>{chips}</div>",
            unsafe_allow_html=True,
        )


# ── Stripe explorer ───────────────────────────────────────────────────────────

def _render_stripe_explorer(audits: pd.DataFrame, all_stripes: list):
    records   = audits.to_dict("records")
    known_ids = {s["id"] for s in all_stripes}

    # Build stripe → audit records map
    stripe_recs: dict = {s["id"]: [] for s in all_stripes}
    for rec in records:
        for sid in (rec.get("risk_stripes") or []):
            sid = str(sid).strip()
            if sid in stripe_recs:
                stripe_recs[sid].append(rec)

    for cat in _CATEGORIES:
        cat_stripes = [s for s in all_stripes if s.get("category") == cat["id"]]
        if not cat_stripes:
            continue

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin:20px 0 8px;'>"
            f"<span style='width:3px;height:14px;background:{cat['color']};border-radius:2px;"
            f"flex-shrink:0;display:inline-block;'></span>"
            f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.6rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;color:{cat['color']};'>{cat['label']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        for stripe in cat_stripes:
            sid       = stripe["id"]
            s_recs    = stripe_recs.get(sid, [])
            unique_ids = {r.get("audit_id") for r in s_recs}
            count     = len(unique_ids)
            level_lbl = (
                "No Coverage" if count == 0
                else "Low" if count == 1
                else "Moderate" if count == 2
                else "Strong"
            )
            tier      = _TIER_CFG.get(stripe.get("tier", "standard"), _TIER_CFG["standard"])

            with st.expander(
                f"{stripe.get('icon','')} {stripe['name']}  ·  {count} audit(s)  ·  {level_lbl}",
                expanded=False,
            ):
                st.markdown(
                    f"<p style='font-size:0.78rem;color:rgba(255,255,255,0.45);margin-bottom:10px;'>"
                    f"{stripe.get('description', '')}</p>",
                    unsafe_allow_html=True,
                )
                if not s_recs:
                    st.markdown(
                        "<div style='background:rgba(248,113,113,0.07);border:1px solid rgba(248,113,113,0.18);"
                        "border-left:3px solid #f87171;border-radius:6px;padding:10px 14px;'>"
                        "<span style='font-size:0.78rem;color:#fca5a5;'>"
                        "No audits currently cover this risk stripe. Consider adding coverage in the next cycle."
                        "</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    seen, rows = set(), []
                    for r in s_recs:
                        aid = r.get("audit_id", "")
                        if aid in seen:
                            continue
                        seen.add(aid)
                        rows.append({
                            "ID":         aid,
                            "Audit Name": r.get("audit_name", ""),
                            "Type":       r.get("audit_type", ""),
                            "Region":     r.get("region", ""),
                            "Status":     r.get("status", ""),
                            "Rating":     r.get("rating", ""),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Legend row ────────────────────────────────────────────────────────────────

def _render_legend():
    st.markdown(
        "<div style='display:flex;gap:10px;align-items:center;margin-bottom:10px;'>"
        "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.55rem;"
        "color:rgba(255,255,255,0.28);'>Legend:</span>"
        "<span style='background:#131820;border:1px solid rgba(255,255,255,0.05);border-radius:4px;"
        "padding:2px 8px;font-size:0.6rem;color:rgba(255,255,255,0.18);'>— None</span>"
        "<span style='background:rgba(248,113,113,0.12);border:1px solid rgba(248,113,113,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#fca5a5;'>1 Low</span>"
        "<span style='background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#fde68a;'>2 Moderate</span>"
        "<span style='background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.3);"
        "border-radius:4px;padding:2px 8px;font-size:0.6rem;color:#6ee7b7;'>3+ Strong</span>"
        "<span style='margin-left:12px;font-family:\"IBM Plex Mono\",monospace;font-size:0.52rem;"
        "color:rgba(255,255,255,0.2);'>Tier →</span>"
        "<span style='background:rgba(248,113,113,0.15);border-radius:3px;padding:1px 6px;"
        "font-size:0.52rem;color:#fca5a5;font-family:\"IBM Plex Mono\",monospace;'>CRIT</span>"
        "<span style='background:rgba(245,158,11,0.15);border-radius:3px;padding:1px 6px;"
        "font-size:0.52rem;color:#fde68a;font-family:\"IBM Plex Mono\",monospace;'>HIGH</span>"
        "<span style='background:rgba(96,165,250,0.15);border-radius:3px;padding:1px 6px;"
        "font-size:0.52rem;color:#93c5fd;font-family:\"IBM Plex Mono\",monospace;'>STD</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def _section_label(text: str):
    st.markdown(
        f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.62rem;font-weight:700;"
        f"letter-spacing:0.12em;text-transform:uppercase;color:rgba(255,255,255,0.45);"
        f"margin:20px 0 8px;'>{text}</div>",
        unsafe_allow_html=True,
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def render_risk_stripe_coverage(audits: pd.DataFrame, snapshot_mode: bool = False):
    all_stripes = di.RISK_STRIPES
    ctx         = _get_context()
    platforms   = di.get_platforms(audits)

    # ── Context banner ────────────────────────────────────────────────────────
    _render_context_banner(ctx)

    # ── Load controls scoped to the same audit filter ─────────────────────────
    stripe_controls = di.get_stripe_controls(audits["audit_id"].tolist())
    ctrl_totals     = _ctrl_stripe_totals(stripe_controls)

    # ── KPI strip (audit + control metrics) ───────────────────────────────────
    _render_kpi_strip(audits, all_stripes, ctrl_totals)

    st.markdown("<div style='margin:20px 0 4px;'></div>", unsafe_allow_html=True)

    # ── View toggle (shared by both heatmap tabs) ─────────────────────────────
    toggle_col, _ = st.columns([2, 5])
    with toggle_col:
        by_region = st.radio(
            "Coverage dimension",
            ["By Region", "By Platform"],
            horizontal=True,
            key="risk_stripe_view",
        ) == "By Region"

    dim_values = platforms["regions"] if by_region else platforms["lines_of_business"]
    dim_label  = "Region" if by_region else "Platform"

    # ── Pre-compute matrices ──────────────────────────────────────────────────
    matrix      = _build_coverage_matrix(audits, by_region, dim_values)
    totals      = _stripe_totals(audits, all_stripes)
    ctrl_matrix = _build_control_matrix(stripe_controls, audits, by_region, dim_values)

    # ── Matrix section with sub-tabs ──────────────────────────────────────────
    _section_label("Coverage Matrix")

    cov_tab, ctrl_tab = st.tabs(["Audit Coverage", "Control Testing"])

    with cov_tab:
        _render_legend()
        if dim_values:
            _render_heatmap_matrix(matrix, totals, all_stripes, dim_values)
        else:
            st.info(
                f"No {dim_label.lower()} data available. "
                "Ensure audits are loaded with platform / region information."
            )

    with ctrl_tab:
        _render_control_legend()
        if dim_values:
            _render_control_heatmap_matrix(ctrl_matrix, ctrl_totals, all_stripes, dim_values)
        else:
            st.info(
                f"No {dim_label.lower()} data available. "
                "Ensure audits are loaded with platform / region information."
            )

    # ── Gap analysis (audit coverage gaps) ───────────────────────────────────
    _section_label("Coverage Gaps")
    if dim_values:
        _render_gap_panel(matrix, all_stripes, dim_values)
    else:
        st.info("Select a dimension to view gap analysis.")

    # ── Stripe explorer ───────────────────────────────────────────────────────
    _section_label("Stripe Explorer")
    st.markdown(
        "<div style='font-size:0.76rem;color:rgba(255,255,255,0.32);margin:-4px 0 12px;'>"
        "Expand each stripe to view contributing audits, depth, and regional distribution."
        "</div>",
        unsafe_allow_html=True,
    )
    _render_stripe_explorer(audits, all_stripes)
