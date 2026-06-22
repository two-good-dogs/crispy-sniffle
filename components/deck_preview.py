"""deck_preview.py — AC Board report carousel preview + PowerPoint export."""

from __future__ import annotations

import re
from io import BytesIO

import pandas as pd
import streamlit as st

import data.data_interface as di

# ── Brand palette ─────────────────────────────────────────────────────────────
_N  = "#001e4d"    # RBC navy
_G  = "#FFB81C"    # RBC gold
_W  = "#ffffff"
_M  = "rgba(255,255,255,0.58)"
_F  = "rgba(255,255,255,0.20)"

_FL = (
    "<link href='https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800"
    "&family=IBM+Plex+Mono:wght@500;600&display=swap' rel='stylesheet'>"
)

# ── Risk category config (for spotlight slides) ────────────────────────────────
_CAT_CFG: dict[str, dict] = {
    "financial_market":    {"label": "Financial Markets",          "color": "#0d2d5a", "abbr": "FM"},
    "credit_balance":      {"label": "Credit & Balance Sheet",     "color": "#0d3d27", "abbr": "CR"},
    "operational_conduct": {"label": "Operational & Conduct",      "color": "#3d1800", "abbr": "OC"},
    "tech_cyber":          {"label": "Technology & Cyber Security", "color": "#0d2a3d", "abbr": "TC"},
    "regulatory_legal":    {"label": "Regulatory & Legal",         "color": "#2a0d3d", "abbr": "RL"},
    "governance_strategy": {"label": "Governance & Strategy",      "color": "#1a1a1a", "abbr": "GS"},
}

# ── Data helpers ──────────────────────────────────────────────────────────────

def _pct(n: int, d: int) -> int:
    return int(round(100 * n / d)) if d else 0


def _regions(audits: pd.DataFrame) -> list[str]:
    out: set[str] = set()
    for r in audits.get("region", pd.Series(dtype=str)).dropna():
        for p in re.split(r"[|,;]", str(r)):
            s = p.strip()
            if s and s.lower() != "global":
                out.add(s)
    return sorted(out)


def _rgn_filter(audits: pd.DataFrame, region: str) -> pd.DataFrame:
    def _m(r):
        if not isinstance(r, str):
            return False
        parts = {p.strip().lower() for p in re.split(r"[|,;]", r)}
        return region.lower() in parts or "global" in parts
    return audits[audits["region"].apply(_m)].copy()


def _for_audits(df: pd.DataFrame, audit_ids) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["audit_id"].isin(set(audit_ids))].copy()


def _audit_has_stripe(val, stripe_id_set: set) -> bool:
    if isinstance(val, list):
        return bool(set(val) & stripe_id_set)
    if isinstance(val, str):
        return bool({p.strip() for p in re.split(r"[|,;]", val)} & stripe_id_set)
    return False


def _sc(s: str) -> str:
    return {"Complete": "#4ade80", "In Progress": "#60a5fa", "Fieldwork": "#fbbf24"}.get(s, "#9ca3af")


def _rc(r: str) -> str:
    return {
        "SAT": "#4ade80", "RI": "#fbbf24", "UNSAT": "#f87171", "NA": "#9ca3af",
        "High": "#f87171", "Medium": "#fbbf24", "Low": "#86efac",
    }.get(r, "#9ca3af")


def _hb(pct: int, color: str) -> str:
    return (
        f"<div style='background:rgba(255,255,255,0.1);border-radius:2px;height:5px;width:100%;'>"
        f"<div style='background:{color};width:{min(pct,100)}%;height:100%;border-radius:2px;'></div>"
        f"</div>"
    )


def _lhb(pct: int, color: str) -> str:
    """Light-background horizontal bar."""
    return (
        f"<div style='background:#e5e7eb;border-radius:2px;height:6px;width:100%;'>"
        f"<div style='background:{color};width:{min(pct,100)}%;height:100%;border-radius:2px;'></div>"
        f"</div>"
    )


# ── Navy slide frame ───────────────────────────────────────────────────────────

def _frame(body: str, scope: str, stype: str, qtr: str) -> str:
    return (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;background:{_N};"
          f"border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.65);font-family:Barlow Condensed,sans-serif;'>"
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};z-index:2;'></div>"
        + f"<div style='background:rgba(0,0,0,0.38);padding:8px 22px 8px 28px;"
          f"display:flex;justify-content:space-between;align-items:center;"
          f"border-bottom:1px solid rgba(255,184,28,0.22);'>"
          f"<span style='font-size:0.68rem;letter-spacing:0.14em;color:{_G};font-weight:700;"
          f"text-transform:uppercase;'>{scope}</span>"
          f"<span style='font-size:0.58rem;color:{_M};letter-spacing:0.06em;'>{stype}</span></div>"
        + f"<div style='padding:14px 24px 14px 28px;height:calc(100% - 66px);overflow:hidden;'>{body}</div>"
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:rgba(0,0,0,0.42);display:flex;align-items:center;padding:0 20px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.48rem;color:{_F};'>RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.48rem;color:{_F};'>{qtr}</span></div>"
        + "</div>"
    )


# ── Cover slide ────────────────────────────────────────────────────────────────

def _slide_cover(qtr: str) -> str:
    return (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;background:{_N};"
          f"border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.65);font-family:Barlow Condensed,sans-serif;'>"
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};'></div>"
        + f"<div style='position:absolute;right:-20px;top:-20px;width:260px;height:260px;"
          f"background:radial-gradient(circle,rgba(255,184,28,0.09),transparent 70%);'></div>"
        + f"<div style='display:flex;flex-direction:column;justify-content:center;align-items:center;"
          f"height:calc(100% - 20px);text-align:center;padding:0 80px;'>"
          f"<div style='font-size:0.6rem;letter-spacing:0.28em;color:{_G};text-transform:uppercase;"
          f"font-weight:700;margin-bottom:20px;font-family:IBM Plex Mono,monospace;'>RBC INTERNAL AUDIT</div>"
          f"<div style='font-size:3.3rem;font-weight:800;color:{_W};letter-spacing:0.03em;line-height:0.93;'>"
          f"AUDIT COMMITTEE</div>"
          f"<div style='font-size:3.3rem;font-weight:800;color:{_G};letter-spacing:0.03em;line-height:0.93;"
          f"margin-bottom:20px;'>REPORT</div>"
          f"<div style='width:56px;height:3px;background:{_G};margin-bottom:20px;'></div>"
          f"<div style='font-size:1.05rem;font-weight:700;color:{_W};letter-spacing:0.1em;'>"
          f"{qtr} · QUARTER-END SUMMARY</div>"
          f"<div style='font-size:0.62rem;color:{_M};margin-top:10px;letter-spacing:0.05em;"
          f"font-family:IBM Plex Mono,monospace;'>"
          f"February 1 – April 30 &nbsp;·&nbsp; Cutoff Apr 15 &nbsp;·&nbsp; Hard Close Apr 30"
          f"</div></div>"
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:rgba(0,0,0,0.42);display:flex;align-items:center;padding:0 20px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.48rem;color:{_F};'>RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.48rem;color:{_F};'>{qtr}</span></div>"
        + "</div>"
    )


# ── Portfolio (platform) ───────────────────────────────────────────────────────

def _slide_portfolio_plat(plat: str, audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    n_own = len(audits[audits.get("audit_type", pd.Series(dtype=str)) == "Owned Audit"])
    n_ae  = int(audits.get("ae_in_scope", pd.Series(False, index=audits.index)).sum())
    n_ind = len(audits[audits.get("audit_type", pd.Series(dtype=str)) == "Indirect"])
    n_tot = len(audits)
    n_iss = len(issues[issues["status"].isin(["Open", "Overdue"])]) if not issues.empty else 0
    n_cmp = len(audits[audits["status"] == "Complete"])

    def _tile(v, lbl, bg="rgba(255,255,255,0.07)", bc=_F):
        return (
            f"<div style='background:{bg};border:1px solid {bc};border-radius:6px;"
            f"padding:8px 10px;text-align:center;'>"
            f"<div style='font-size:2rem;font-weight:800;color:{_W};line-height:1;'>{v}</div>"
            f"<div style='font-size:0.47rem;color:{_M};letter-spacing:0.12em;text-transform:uppercase;"
            f"font-family:IBM Plex Mono,monospace;margin-top:3px;'>{lbl}</div></div>"
        )

    tiles = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:7px;'>Engagement Summary</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;'>"
        + _tile(n_own, "Owned", "rgba(255,184,28,0.12)", "rgba(255,184,28,0.32)")
        + _tile(n_ae, "AE In-Scope", "rgba(96,165,250,0.1)", "rgba(96,165,250,0.3)")
        + _tile(n_ind, "Indirect", "rgba(255,255,255,0.06)", _F)
        + _tile(n_cmp, "Complete", "rgba(74,222,128,0.09)", "rgba(74,222,128,0.26)")
        + "</div>"
        + f"<div style='background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);"
          f"border-radius:6px;padding:6px 10px;text-align:center;'>"
          f"<div style='font-size:1.5rem;font-weight:800;color:#f87171;line-height:1;'>{n_iss}</div>"
          f"<div style='font-size:0.47rem;color:{_M};letter-spacing:0.12em;text-transform:uppercase;"
          f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>Open Issues</div></div>"
    )

    rows = ""
    for _, row in audits.head(7).iterrows():
        nm  = str(row.get("audit_name", row.get("audit_id", "—")))[:30]
        st_ = str(row.get("status", ""))
        rt  = str(row.get("current_rating", row.get("rating", "—")))
        rows += (
            f"<tr>"
            f"<td style='padding:3px 5px;font-size:0.6rem;color:{_W};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{nm}</td>"
            f"<td style='padding:3px 5px;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
            f"<span style='font-size:0.5rem;color:{_sc(st_)};background:rgba(0,0,0,0.28);"
            f"border-radius:3px;padding:1px 5px;'>{st_ or '—'}</span></td>"
            f"<td style='padding:3px 5px;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
            f"<span style='font-size:0.5rem;color:{_rc(rt)};background:rgba(0,0,0,0.28);"
            f"border-radius:3px;padding:1px 5px;'>{rt}</span></td>"
            f"</tr>"
        )

    tbl = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:5px;'>"
        f"Audit Engagements ({n_tot})</div>"
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
        + "".join(
            f"<th style='padding:3px 5px;text-align:{a};font-size:0.5rem;color:{_M};"
            f"letter-spacing:0.07em;text-transform:uppercase;font-weight:600;"
            f"border-bottom:1px solid rgba(255,184,28,0.26);'>{h}</th>"
            for h, a in [("Audit Name", "left"), ("Status", "center"), ("Rating", "center")]
        )
        + f"</tr></thead><tbody>{rows}</tbody></table>"
    )

    body = (
        f"<div style='display:grid;grid-template-columns:36% 64%;gap:16px;height:100%;'>"
        f"<div>{tiles}</div><div style='overflow:hidden;'>{tbl}</div></div>"
    )
    return _frame(body, plat, "Portfolio Overview", qtr)


# ── Portfolio (region) ─────────────────────────────────────────────────────────

def _slide_portfolio_region(region: str, audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    n_tot  = len(audits)
    n_iss  = len(issues[issues["status"].isin(["Open", "Overdue"])]) if not issues.empty else 0
    n_cmp  = len(audits[audits["status"] == "Complete"])
    n_prog = len(audits[audits["status"] == "In Progress"])
    n_fw   = len(audits[audits["status"] == "Fieldwork"])

    def _tile(v, lbl, bg="rgba(255,255,255,0.07)", bc=_F):
        return (
            f"<div style='background:{bg};border:1px solid {bc};border-radius:6px;"
            f"padding:8px 10px;text-align:center;'>"
            f"<div style='font-size:2rem;font-weight:800;color:{_W};line-height:1;'>{v}</div>"
            f"<div style='font-size:0.47rem;color:{_M};letter-spacing:0.12em;text-transform:uppercase;"
            f"font-family:IBM Plex Mono,monospace;margin-top:3px;'>{lbl}</div></div>"
        )

    tiles = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:7px;'>Engagement Summary</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;'>"
        + _tile(n_tot, "Total", "rgba(255,184,28,0.12)", "rgba(255,184,28,0.32)")
        + _tile(n_cmp, "Complete", "rgba(74,222,128,0.09)", "rgba(74,222,128,0.26)")
        + _tile(n_prog, "In Progress", "rgba(96,165,250,0.1)", "rgba(96,165,250,0.3)")
        + _tile(n_fw, "Fieldwork", "rgba(251,191,36,0.1)", "rgba(251,191,36,0.3)")
        + "</div>"
        + f"<div style='background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);"
          f"border-radius:6px;padding:6px 10px;text-align:center;'>"
          f"<div style='font-size:1.5rem;font-weight:800;color:#f87171;line-height:1;'>{n_iss}</div>"
          f"<div style='font-size:0.47rem;color:{_M};letter-spacing:0.12em;text-transform:uppercase;"
          f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>Open Issues</div></div>"
    )

    rows = ""
    for _, row in audits.head(7).iterrows():
        nm  = str(row.get("audit_name", row.get("audit_id", "—")))[:30]
        st_ = str(row.get("status", ""))
        lg  = str(row.get("lead_group", "—"))[:18]
        rows += (
            f"<tr>"
            f"<td style='padding:3px 5px;font-size:0.6rem;color:{_W};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{nm}</td>"
            f"<td style='padding:3px 5px;font-size:0.56rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{lg}</td>"
            f"<td style='padding:3px 5px;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
            f"<span style='font-size:0.5rem;color:{_sc(st_)};background:rgba(0,0,0,0.28);"
            f"border-radius:3px;padding:1px 5px;'>{st_ or '—'}</span></td>"
            f"</tr>"
        )

    tbl = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:5px;'>"
        f"Audit Engagements ({n_tot})</div>"
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
        + "".join(
            f"<th style='padding:3px 5px;text-align:{a};font-size:0.5rem;color:{_M};"
            f"letter-spacing:0.07em;text-transform:uppercase;font-weight:600;"
            f"border-bottom:1px solid rgba(255,184,28,0.26);'>{h}</th>"
            for h, a in [("Audit Name", "left"), ("Lead Group", "left"), ("Status", "center")]
        )
        + f"</tr></thead><tbody>{rows}</tbody></table>"
    )

    body = (
        f"<div style='display:grid;grid-template-columns:36% 64%;gap:16px;height:100%;'>"
        f"<div>{tiles}</div><div style='overflow:hidden;'>{tbl}</div></div>"
    )
    return _frame(body, region, "Portfolio Overview", qtr)


# ── Assurance summary ──────────────────────────────────────────────────────────

def _slide_assurance(label: str, audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    completed = audits[audits["status"] == "Complete"]
    published = (
        completed[completed["report_status"] == "Published"]
        if "report_status" in completed.columns else completed
    )
    at_col = published.get("audit_type", pd.Series(dtype=str))
    core   = published[at_col.isin(["Owned Audit", "In-Scope AE"])]

    def _cnt(col, val):
        return len(core[core[col] == val]) if col in core.columns else 0

    n_sat, n_ri, n_unsat, n_na = _cnt("current_rating","SAT"), _cnt("current_rating","RI"), _cnt("current_rating","UNSAT"), _cnt("current_rating","NA")
    n_dev, n_sub, n_par, n_und = _cnt("marc_rating","Developed"), _cnt("marc_rating","Substantially Developed"), _cnt("marc_rating","Partially Developed"), _cnt("marc_rating","Underdeveloped")
    max_r = max(n_sat, n_ri, n_unsat, n_na, 1)
    max_m = max(n_dev, n_sub, n_par, n_und, 1)

    audit_ids = set(audits["audit_id"].tolist())
    si = _for_audits(issues, audit_ids) if not issues.empty else pd.DataFrame()
    n_open = len(si[si["status"].isin(["Open","In Progress"])]) if not si.empty else 0
    n_ovd  = len(si[si["status"] == "Overdue"]) if not si.empty else 0
    n_high = len(si[si["severity"] == "High"]) if not si.empty else 0

    def _rbar(lbl, n, mx, color):
        return (
            f"<div style='margin-bottom:6px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
            f"<span style='font-size:0.6rem;color:{_M};'>{lbl}</span>"
            f"<span style='font-size:0.66rem;font-weight:700;color:{color};'>{n}</span></div>"
            + _hb(_pct(n, mx), color) + "</div>"
        )

    def _kpi(v, lbl, color):
        return (
            f"<div style='background:rgba(0,0,0,0.22);border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:6px;padding:7px 12px;text-align:center;flex:1;'>"
            f"<div style='font-size:1.8rem;font-weight:800;color:{color};line-height:1;'>{v}</div>"
            f"<div style='font-size:0.46rem;color:{_M};letter-spacing:0.1em;text-transform:uppercase;"
            f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>{lbl}</div></div>"
        )

    left = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:8px;'>Report Ratings</div>"
        + _rbar("SAT", n_sat, max_r, "#4ade80")
        + _rbar("RI", n_ri, max_r, "#fbbf24")
        + _rbar("UNSAT", n_unsat, max_r, "#f87171")
        + _rbar("N/A", n_na, max_r, "#9ca3af")
    )

    right = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:8px;'>MARC Ratings</div>"
        + _rbar("Developed", n_dev, max_m, "#4ade80")
        + _rbar("Substantially Dev.", n_sub, max_m, "#a3e635")
        + _rbar("Partially Dev.", n_par, max_m, "#fbbf24")
        + _rbar("Underdeveloped", n_und, max_m, "#f87171")
        + f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
          f"font-family:IBM Plex Mono,monospace;font-weight:700;margin:12px 0 6px;'>Issues</div>"
        + f"<div style='display:flex;gap:8px;'>"
        + _kpi(n_open, "Open", "#60a5fa")
        + _kpi(n_ovd, "Overdue", "#f87171")
        + _kpi(n_high, "High Sev.", "#fbbf24")
        + "</div>"
    )

    body = (
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:18px;height:100%;'>"
        f"<div>{left}</div><div>{right}</div></div>"
    )
    return _frame(body, label, "Assurance Summary", qtr)


# ── Control environment ────────────────────────────────────────────────────────

def _slide_control_env(label: str, audits: pd.DataFrame, controls: pd.DataFrame, qtr: str) -> str:
    audit_ids = set(audits["audit_id"].tolist())
    ctl = _for_audits(controls, audit_ids)

    if ctl.empty or "de_result" not in ctl.columns:
        body = (
            f"<div style='display:flex;align-items:center;justify-content:center;height:100%;'>"
            f"<div style='text-align:center;color:{_M};font-size:0.8rem;'>"
            f"No control testing data available for this scope.</div></div>"
        )
        return _frame(body, label, "Control Environment", qtr)

    grp_col = "audit_group" if "audit_group" in ctl.columns else "audit_id"
    agg = (
        ctl.groupby(grp_col, sort=False)
        .agg(
            total=("de_result", "count"),
            de_ef=("de_result", lambda x: (x == "EF").sum()),
            oe_met=("oe_result", lambda x: (x == "M").sum()) if "oe_result" in ctl.columns else ("de_result", lambda _: 0),
            tp=("test_result", lambda x: (x == "Pass").sum()) if "test_result" in ctl.columns else ("de_result", lambda _: 0),
        )
        .reset_index()
        .rename(columns={grp_col: "group"})
        .head(7)
    )

    n_tot = int(ctl.shape[0])
    o_de = _pct(int((ctl["de_result"] == "EF").sum()), n_tot)
    o_oe = _pct(int((ctl.get("oe_result", pd.Series(dtype=str)) == "M").sum()), n_tot) if "oe_result" in ctl.columns else 0
    o_tp = _pct(int((ctl.get("test_result", pd.Series(dtype=str)) == "Pass").sum()), n_tot) if "test_result" in ctl.columns else 0

    def _sbar(lbl, p, color):
        return (
            f"<div style='margin-bottom:4px;display:flex;align-items:center;gap:8px;'>"
            f"<span style='font-size:0.52rem;color:{_M};font-family:IBM Plex Mono,monospace;width:24px;'>{lbl}</span>"
            + _hb(p, color)
            + f"<span style='font-size:0.58rem;font-weight:700;color:{color};width:32px;'>{p}%</span></div>"
        )

    summary = (
        f"<div style='background:rgba(255,184,28,0.08);border:1px solid rgba(255,184,28,0.2);"
        f"border-radius:6px;padding:10px 12px;margin-bottom:12px;'>"
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:8px;'>"
        f"Overall — {n_tot} Controls Tested</div>"
        + _sbar("DE", o_de, "#4ade80")
        + _sbar("OE", o_oe, "#60a5fa")
        + _sbar("TP", o_tp, "#fbbf24")
        + "</div>"
    )

    rows = ""
    for _, row in agg.iterrows():
        grp  = str(row["group"])[:28]
        tot  = int(row["total"])
        de_p = _pct(int(row["de_ef"]), tot)
        oe_p = _pct(int(row["oe_met"]), tot)
        tp_p = _pct(int(row["tp"]), tot)
        tp_c = "#4ade80" if tp_p >= 85 else ("#fbbf24" if tp_p >= 70 else "#f87171")
        rows += (
            f"<tr>"
            f"<td style='padding:3px 5px;font-size:0.58rem;color:{_W};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{grp}</td>"
            f"<td style='padding:3px 8px;font-size:0.56rem;color:#4ade80;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{de_p}%</td>"
            f"<td style='padding:3px 8px;font-size:0.56rem;color:#60a5fa;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{oe_p}%</td>"
            f"<td style='padding:3px 8px;font-size:0.56rem;font-weight:700;color:{tp_c};text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{tp_p}%</td>"
            f"</tr>"
        )

    tbl = (
        f"<div style='font-size:0.54rem;color:{_G};letter-spacing:0.12em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;font-weight:700;margin-bottom:6px;'>By Audit Group</div>"
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
        + "".join(
            f"<th style='padding:3px 5px;text-align:{a};font-size:0.5rem;color:{_M};"
            f"letter-spacing:0.07em;text-transform:uppercase;font-weight:600;"
            f"border-bottom:1px solid rgba(255,184,28,0.26);'>{h}</th>"
            for h, a in [("Group", "left"), ("DE", "center"), ("OE", "center"), ("Pass", "center")]
        )
        + f"</tr></thead><tbody>{rows}</tbody></table>"
    )

    body = (
        f"<div style='display:grid;grid-template-columns:40% 60%;gap:16px;height:100%;'>"
        f"<div>{summary}</div><div style='overflow:hidden;'>{tbl}</div></div>"
    )
    return _frame(body, label, "Control Environment", qtr)


# ── Issues slide ───────────────────────────────────────────────────────────────

def _slide_issues(label: str, issues: pd.DataFrame, qtr: str) -> str:
    if issues.empty:
        body = (
            f"<div style='display:flex;align-items:center;justify-content:center;height:100%;'>"
            f"<div style='text-align:center;color:{_M};font-size:0.8rem;'>No issues for this scope.</div></div>"
        )
        return _frame(body, label, "Issues", qtr)

    open_iss = issues[issues["status"].isin(["Open","In Progress","Overdue"])]
    n_open = len(open_iss)
    n_ovd  = len(issues[issues["status"] == "Overdue"])
    n_high = len(issues[issues["severity"] == "High"])

    def _kpi(v, lbl, color):
        return (
            f"<div style='background:rgba(0,0,0,0.22);border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:6px;padding:8px 14px;text-align:center;flex:1;'>"
            f"<div style='font-size:2rem;font-weight:800;color:{color};line-height:1;'>{v}</div>"
            f"<div style='font-size:0.46rem;color:{_M};letter-spacing:0.1em;text-transform:uppercase;"
            f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>{lbl}</div></div>"
        )

    kpis = (
        f"<div style='display:flex;gap:10px;margin-bottom:12px;'>"
        + _kpi(n_open, "Open", "#60a5fa")
        + _kpi(n_ovd, "Overdue", "#f87171")
        + _kpi(n_high, "High Severity", "#fbbf24")
        + "</div>"
    )

    sev_c = {"High":"#f87171","Medium":"#fbbf24","Low":"#86efac"}
    rows = ""
    for _, row in open_iss.head(7).iterrows():
        title = str(row.get("title","—"))[:42]
        sev   = str(row.get("severity","—"))
        due   = str(row.get("due_date","—"))[:10]
        owner = str(row.get("remediation_owner","—"))[:16]
        sc_   = sev_c.get(sev, "#9ca3af")
        rows += (
            f"<tr>"
            f"<td style='padding:3px 5px;font-size:0.58rem;color:{_W};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{title}</td>"
            f"<td style='padding:3px 5px;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
            f"<span style='font-size:0.5rem;color:{sc_};background:rgba(0,0,0,0.28);"
            f"border-radius:3px;padding:1px 5px;'>{sev}</span></td>"
            f"<td style='padding:3px 5px;font-size:0.56rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{due}</td>"
            f"<td style='padding:3px 5px;font-size:0.56rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.05);'>{owner}</td>"
            f"</tr>"
        )

    tbl = (
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
        + "".join(
            f"<th style='padding:3px 5px;text-align:{a};font-size:0.5rem;color:{_M};"
            f"letter-spacing:0.07em;text-transform:uppercase;font-weight:600;"
            f"border-bottom:1px solid rgba(255,184,28,0.26);'>{h}</th>"
            for h, a in [("Issue Title","left"),("Sev.","center"),("Due","left"),("Owner","left")]
        )
        + f"</tr></thead><tbody>{rows}</tbody></table>"
    )
    return _frame(f"<div style='height:100%;overflow:hidden;'>{kpis}{tbl}</div>", label, "Issues", qtr)


# ── Appendix ───────────────────────────────────────────────────────────────────

def _slide_appendix(all_issues: pd.DataFrame, qtr: str) -> str:
    if all_issues.empty:
        body = (
            f"<div style='display:flex;align-items:center;justify-content:center;height:100%;'>"
            f"<div style='text-align:center;color:{_M};font-size:0.8rem;'>No issues on record.</div></div>"
        )
        return _frame(body, "Enterprise", "Appendix — All Issues", qtr)

    sev_c = {"High":"#f87171","Medium":"#fbbf24","Low":"#86efac"}
    rows = ""
    for _, row in all_issues.head(14).iterrows():
        title  = str(row.get("title","—"))[:38]
        sev    = str(row.get("severity","—"))
        status = str(row.get("status","—"))
        due    = str(row.get("due_date","—"))[:10]
        owner  = str(row.get("remediation_owner","—"))[:14]
        sc_    = sev_c.get(sev, "#9ca3af")
        rows += (
            f"<tr>"
            f"<td style='padding:2px 5px;font-size:0.55rem;color:{_W};"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>{title}</td>"
            f"<td style='padding:2px 5px;text-align:center;"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
            f"<span style='font-size:0.48rem;color:{sc_};background:rgba(0,0,0,0.28);"
            f"border-radius:3px;padding:1px 4px;'>{sev}</span></td>"
            f"<td style='padding:2px 5px;font-size:0.52rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>{status}</td>"
            f"<td style='padding:2px 5px;font-size:0.52rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>{due}</td>"
            f"<td style='padding:2px 5px;font-size:0.52rem;color:{_M};"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>{owner}</td>"
            f"</tr>"
        )

    footer_note = (
        f"<div style='font-size:0.48rem;color:{_M};margin-top:5px;text-align:right;'>"
        f"Showing {min(14, len(all_issues))} of {len(all_issues)} issues</div>"
        if len(all_issues) > 14 else ""
    )

    tbl = (
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
        + "".join(
            f"<th style='padding:3px 5px;text-align:{a};font-size:0.5rem;color:{_G};"
            f"letter-spacing:0.07em;text-transform:uppercase;font-weight:700;"
            f"border-bottom:1px solid rgba(255,184,28,0.3);'>{h}</th>"
            for h, a in [("Issue Title","left"),("Sev.","center"),("Status","left"),("Due","left"),("Owner","left")]
        )
        + f"</tr></thead><tbody>{rows}</tbody></table>{footer_note}"
    )
    return _frame(f"<div style='height:100%;overflow:hidden;'>{tbl}</div>", "Enterprise", "Appendix — All Issues", qtr)


# ── Risk Spotlight slide (light background, 3-column AC report style) ──────────

def _slide_risk_spotlight(
    cat_id: str,
    audits: pd.DataFrame,
    controls: pd.DataFrame,
    qtr: str,
) -> str:
    cfg     = _CAT_CFG.get(cat_id, {"label": cat_id, "color": _N, "abbr": "??"})
    cat_lbl = cfg["label"]
    hdr_clr = cfg["color"]

    stripes     = [s for s in di.RISK_STRIPES if s["category"] == cat_id]
    stripe_ids  = {s["id"] for s in stripes}

    # Audits touching this category
    if "risk_stripes" in audits.columns:
        cat_audits = audits[audits["risk_stripes"].apply(lambda x: _audit_has_stripe(x, stripe_ids))]
    else:
        cat_audits = pd.DataFrame()

    # Controls for this category
    cat_ctl = (
        controls[controls.get("control_type", pd.Series(dtype=str)).isin(stripe_ids)]
        if not controls.empty else pd.DataFrame()
    )
    n_ctl = len(cat_ctl)
    de_p  = _pct(int((cat_ctl.get("de_result", pd.Series(dtype=str)) == "EF").sum()), n_ctl) if n_ctl else 0
    oe_p  = _pct(int((cat_ctl.get("oe_result", pd.Series(dtype=str)) == "M").sum()), n_ctl) if n_ctl else 0
    tp_p  = _pct(int((cat_ctl.get("test_result", pd.Series(dtype=str)) == "Pass").sum()), n_ctl) if n_ctl else 0

    # ── LEFT column: FY26 Key Focus Areas ──────────────────────────────────────
    tier_c = {"critical": "#dc2626", "high": "#d97706", "standard": "#16a34a"}

    focus_items = ""
    for s in stripes[:7]:
        tc = tier_c.get(s["tier"], "#6b7280")
        focus_items += (
            f"<div style='margin-bottom:5px;padding:4px 8px;"
            f"border-left:3px solid {tc};background:#f0f4f8;border-radius:0 4px 4px 0;'>"
            f"<div style='font-size:0.62rem;font-weight:600;color:#1a2035;'>{s['icon']} {s['name']}</div>"
            f"<div style='font-size:0.46rem;color:#6b7280;letter-spacing:0.08em;text-transform:uppercase;'>"
            f"{s['tier'].upper()}</div></div>"
        )

    # ── MIDDLE column: Q2 Activities & Insights ────────────────────────────────
    n_audits = len(cat_audits)
    n_cmp    = len(cat_audits[cat_audits["status"] == "Complete"]) if not cat_audits.empty else 0
    n_prog   = len(cat_audits[cat_audits["status"].isin(["In Progress","Fieldwork"])]) if not cat_audits.empty else 0

    def _ibar(lbl, p, color):
        return (
            f"<div style='margin-bottom:5px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:2px;'>"
            f"<span style='font-size:0.58rem;color:#374151;font-weight:500;'>{lbl}</span>"
            f"<span style='font-size:0.6rem;font-weight:700;color:{color};'>{p}%</span></div>"
            + _lhb(p, color) + "</div>"
        )

    if n_ctl > 0:
        control_insight = (
            f"<div style='background:#f0f4f8;border-radius:6px;padding:8px 10px;margin-bottom:8px;"
            f"border:1px solid #d1d5db;'>"
            f"<div style='font-size:0.58rem;font-weight:700;color:#1a2035;margin-bottom:6px;'>"
            f"{n_ctl} Controls Tested</div>"
            + _ibar("Design Effectiveness", de_p, "#16a34a")
            + _ibar("Operating Effectiveness", oe_p, "#2563eb")
            + _ibar("Test Pass Rate", tp_p, "#d97706")
            + "</div>"
        )
    else:
        control_insight = (
            f"<div style='background:#fef3c7;border-radius:6px;padding:8px 10px;margin-bottom:8px;"
            f"border:1px solid #fde68a;font-size:0.6rem;color:#92400e;'>"
            f"No control testing data for this quarter.</div>"
        )

    audit_summary = (
        f"<div style='font-size:0.58rem;color:#374151;margin-bottom:4px;'>"
        f"<strong style='color:#001e4d;'>{n_audits} engagement{'s' if n_audits!=1 else ''}</strong>"
        f" cover this risk area — {n_cmp} complete, {n_prog} in progress.</div>"
    )

    # Enumerate complete audits briefly
    insights_list = ""
    for _, row in cat_audits[cat_audits["status"] == "Complete"].head(3).iterrows():
        nm = str(row.get("audit_name", row.get("audit_id", "—")))[:38]
        rt = str(row.get("current_rating", ""))
        rc = _rc(rt)
        insights_list += (
            f"<div style='font-size:0.56rem;color:#374151;padding:3px 0;"
            f"border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;'>"
            f"<span>• {nm}</span>"
            f"<span style='color:{rc};font-weight:600;'>{rt or '—'}</span></div>"
        )

    # ── RIGHT column: Upcoming Audit Coverage ──────────────────────────────────
    upcoming = cat_audits[~cat_audits["status"].isin(["Complete"])] if not cat_audits.empty else pd.DataFrame()
    upcoming_items = ""
    for _, row in upcoming.head(8).iterrows():
        nm  = str(row.get("audit_name", row.get("audit_id","—")))[:28]
        st_ = str(row.get("status",""))
        sc  = _sc(st_)
        upcoming_items += (
            f"<div style='font-size:0.58rem;color:#1a2035;padding:3px 0;"
            f"border-bottom:1px solid #e5e7eb;display:flex;align-items:center;gap:6px;'>"
            f"<span style='width:6px;height:6px;border-radius:50%;background:{sc};"
            f"flex-shrink:0;display:inline-block;'></span>"
            f"<span style='flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{nm}</span>"
            f"<span style='font-size:0.5rem;color:{sc};flex-shrink:0;'>{st_}</span>"
            f"</div>"
        )
    if not upcoming_items:
        upcoming_items = f"<div style='font-size:0.58rem;color:#6b7280;padding:4px 0;'>All engagements complete.</div>"

    # ── Column header style ─────────────────────────────────────────────────────
    def _col_hdr(text):
        return (
            f"<div style='background:{hdr_clr};color:{_W};padding:6px 10px;border-radius:4px;"
            f"font-size:0.56rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
            f"font-family:IBM Plex Mono,monospace;margin-bottom:8px;'>{text}</div>"
        )

    # ── Full slide assembly ─────────────────────────────────────────────────────
    return (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;"
          f"background:#f5f7f9;border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.5);font-family:Barlow Condensed,sans-serif;'>"
        # Left RBC gold strip
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};z-index:3;'></div>"
        # Section header bar
        + f"<div style='background:{hdr_clr};padding:9px 22px 9px 28px;"
          f"display:flex;justify-content:space-between;align-items:center;'>"
          f"<div>"
          f"<div style='font-size:0.52rem;color:rgba(255,255,255,0.55);letter-spacing:0.16em;"
          f"text-transform:uppercase;font-family:IBM Plex Mono,monospace;'>"
          f"SECTION 2 · SPOTLIGHT ON KEY &amp; EMERGING RISKS</div>"
          f"<div style='font-size:1.1rem;font-weight:800;color:{_W};letter-spacing:0.04em;'>"
          f"{cat_lbl}</div>"
          f"</div>"
          f"<div style='font-size:0.58rem;color:rgba(255,255,255,0.45);font-family:IBM Plex Mono,monospace;'>"
          f"RBC INTERNAL AUDIT</div>"
          f"</div>"
        # Body: 3 columns
        + f"<div style='display:grid;grid-template-columns:28% 42% 30%;height:calc(100% - 80px);"
          f"overflow:hidden;'>"
        # LEFT column
        + f"<div style='background:#edf2f7;padding:10px 10px 10px 14px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          + _col_hdr("FY26 Key Focus Areas")
          + focus_items
          + "</div>"
        # MIDDLE column
        + f"<div style='background:{_W};padding:10px 12px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          + _col_hdr("Q2 Activities &amp; Insights")
          + control_insight
          + audit_summary
          + insights_list
          + "</div>"
        # RIGHT column
        + f"<div style='background:#edf2f7;padding:10px 10px 10px 10px;overflow:hidden;'>"
          + _col_hdr("Upcoming Audit Coverage")
          + upcoming_items
          + "</div>"
        + "</div>"
        # Footer
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:{hdr_clr};display:flex;align-items:center;padding:0 22px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.48rem;color:rgba(255,255,255,0.4);'>"
          f"RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.48rem;color:rgba(255,255,255,0.4);'>"
          f"{qtr} INTERNAL AUDIT QUARTERLY REPORT</span>"
          f"</div>"
        + "</div>"
    )


# ── Build slide list ───────────────────────────────────────────────────────────

def _build_slides(
    audits: pd.DataFrame,
    all_issues: pd.DataFrame,
    controls: pd.DataFrame,
    view: str,
    qtr: str,
    enterprise_issues: pd.DataFrame | None = None,
) -> list[dict]:
    slides: list[dict] = []

    slides.append({"title": "Cover", "scope": "—", "stype": "Cover", "html": _slide_cover(qtr)})

    if view == "Platform":
        platforms = sorted(audits["lead_group"].dropna().unique().tolist())
        for plat in platforms:
            plat_aud = audits[audits["lead_group"] == plat].copy()
            plat_ids = set(plat_aud["audit_id"].tolist())
            plat_iss = _for_audits(all_issues, plat_ids)
            plat_ctl = _for_audits(controls, plat_ids)
            for stype, fn in [
                ("Portfolio Overview", lambda a=plat_aud, i=plat_iss: _slide_portfolio_plat(plat, a, i, qtr)),
                ("Assurance Summary",  lambda a=plat_aud, i=plat_iss: _slide_assurance(plat, a, i, qtr)),
                ("Control Environment",lambda a=plat_aud, c=plat_ctl: _slide_control_env(plat, a, c, qtr)),
                ("Issues",             lambda i=plat_iss: _slide_issues(plat, i, qtr)),
            ]:
                slides.append({"title": f"{plat} — {stype}", "scope": plat, "stype": stype, "html": fn()})
    else:
        for region in _regions(audits):
            rgn_aud = _rgn_filter(audits, region)
            rgn_ids = set(rgn_aud["audit_id"].tolist())
            rgn_iss = _for_audits(all_issues, rgn_ids)
            rgn_ctl = _for_audits(controls, rgn_ids)
            for stype, fn in [
                ("Portfolio Overview", lambda a=rgn_aud, i=rgn_iss: _slide_portfolio_region(region, a, i, qtr)),
                ("Assurance Summary",  lambda a=rgn_aud, i=rgn_iss: _slide_assurance(region, a, i, qtr)),
                ("Control Environment",lambda a=rgn_aud, c=rgn_ctl: _slide_control_env(region, a, c, qtr)),
                ("Issues",             lambda i=rgn_iss: _slide_issues(region, i, qtr)),
            ]:
                slides.append({"title": f"{region} — {stype}", "scope": region, "stype": stype, "html": fn()})

    # Risk spotlight slides — one per category (enterprise-wide, not view-filtered)
    for cat_id in _CAT_CFG:
        cat_lbl = _CAT_CFG[cat_id]["label"]
        slides.append({
            "title": f"Spotlight — {cat_lbl}",
            "scope": cat_lbl,
            "stype": "Risk Spotlight",
            "html": _slide_risk_spotlight(cat_id, audits, controls, qtr),
        })

    # Appendix
    appx = enterprise_issues if enterprise_issues is not None else all_issues
    slides.append({
        "title": "Appendix — All Issues",
        "scope": "Enterprise", "stype": "Appendix",
        "html": _slide_appendix(appx, qtr),
    })

    return slides


# ── PowerPoint export ──────────────────────────────────────────────────────────

def _build_pptx(slides: list[dict], all_issues: pd.DataFrame, qtr: str) -> BytesIO:
    from pptx import Presentation
    from pptx.util import Emu, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    W, H = 9144000, 5143500   # 10" × 5.63" (16:9)
    prs  = Presentation()
    prs.slide_width  = Emu(W)
    prs.slide_height = Emu(H)
    blank = prs.slide_layouts[6]

    def _rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

    def _rect(sl, l, t, w, h_, fill, line=False):
        sh = sl.shapes.add_shape(1, Emu(l), Emu(t), Emu(w), Emu(h_))
        sh.fill.solid()
        sh.fill.fore_color.rgb = _rgb(fill)
        if not line:
            sh.line.fill.background()
        return sh

    def _txt(sl, text, l, t, w, h_, size, clr, bold=False, align=PP_ALIGN.LEFT, wrap=True):
        box = sl.shapes.add_textbox(Emu(l), Emu(t), Emu(w), Emu(h_))
        tf  = box.text_frame
        tf.word_wrap = wrap
        para = tf.paragraphs[0]
        para.alignment = align
        run = para.add_run()
        run.text = str(text)
        run.font.size = Pt(size)
        run.font.color.rgb = _rgb(clr)
        run.font.bold = bold
        return box

    def _base(sl, scope, stype, cat_color=None):
        bg_c = cat_color if cat_color else _N
        _rect(sl, 0, 0, W, H, bg_c)
        _rect(sl, 0, 0, 30000, H, _G)
        _rect(sl, 0, 0, W, 400000, "#000816")
        _txt(sl, scope, 60000, 110000, W*7//10, 220000, 13, _G, bold=True)
        _txt(sl, stype, W*7//10, 110000, W*3//10-80000, 220000, 9, "888888", align=PP_ALIGN.RIGHT)
        _rect(sl, 0, H-180000, W, 180000, "#000408")
        _txt(sl, "RBC Internal Audit | CONFIDENTIAL", 60000, H-155000, W//2, 140000, 7, "444444")
        _txt(sl, qtr, W-750000, H-155000, 700000, 140000, 7, "444444", align=PP_ALIGN.RIGHT)

    for s in slides:
        sl    = prs.slides.add_slide(blank)
        scope = s["scope"]
        stype = s["stype"]

        if stype == "Cover":
            _rect(sl, 0, 0, W, H, _N)
            _rect(sl, 0, 0, 30000, H, _G)
            _txt(sl, "RBC INTERNAL AUDIT", W//2-900000, H//3-250000, 1800000, 200000, 10, _G, bold=True, align=PP_ALIGN.CENTER)
            _txt(sl, "AUDIT COMMITTEE REPORT", W//2-1300000, H//3, 2600000, 420000, 30, _W, bold=True, align=PP_ALIGN.CENTER)
            _txt(sl, f"{qtr} · QUARTER-END SUMMARY", W//2-1000000, H//3+460000, 2000000, 200000, 14, _G, bold=True, align=PP_ALIGN.CENTER)
            _rect(sl, 0, H-180000, W, 180000, "#000408")
            _txt(sl, "RBC Internal Audit | CONFIDENTIAL", 60000, H-155000, W//2, 140000, 7, "444444")
            _txt(sl, qtr, W-750000, H-155000, 700000, 140000, 7, "444444", align=PP_ALIGN.RIGHT)
            continue

        cat_c = None
        if stype == "Risk Spotlight":
            cat_id = next((k for k, v in _CAT_CFG.items() if v["label"] == scope), None)
            cat_c  = _CAT_CFG[cat_id]["color"] if cat_id else _N

        _base(sl, scope, stype, cat_c)
        top = 450000

        if stype in ("Portfolio Overview", "Assurance Summary", "Control Environment", "Issues"):
            lines = [s["title"]]
            if stype == "Issues" and not all_issues.empty:
                open_n = len(all_issues[all_issues["status"].isin(["Open","In Progress","Overdue"])])
                lines.append(f"Open Issues: {open_n}")
            for i, line in enumerate(lines):
                _txt(sl, line, 60000, top + i*260000, W-120000, 240000, 12 if i==0 else 10, _W, bold=(i==0))

        elif stype == "Risk Spotlight":
            cat_id = next((k for k,v in _CAT_CFG.items() if v["label"] == scope), None)
            if cat_id:
                stripes = [s2 for s2 in di.RISK_STRIPES if s2["category"] == cat_id]
                _txt(sl, "Key Focus Areas:", 60000, top, W//3-120000, 220000, 11, _G, bold=True)
                for i, stripe in enumerate(stripes[:8]):
                    _txt(sl, f"• {stripe['name']} ({stripe['tier']})", 60000, top+240000+i*240000, W//3-120000, 220000, 9, _W)

        elif stype == "Appendix":
            _txt(sl, f"Enterprise Issues — {len(all_issues)} total", 60000, top, W-120000, 240000, 14, _G, bold=True)
            for i, (_, row) in enumerate(all_issues.head(10).iterrows()):
                title = str(row.get("title","—"))[:60]
                sev   = str(row.get("severity",""))
                _txt(sl, f"• {title}  [{sev}]", 60000, top+280000+i*260000, W-120000, 240000, 9, _W)

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ── Main renderer ──────────────────────────────────────────────────────────────

def render_deck_preview(audits: pd.DataFrame, all_issues: pd.DataFrame, snapshot_mode: bool = False):
    for key, val in [("deck_view","Platform"),("deck_slide_idx",0)]:
        if key not in st.session_state:
            st.session_state[key] = val

    qtr = st.session_state.get("selected_quarter_filter","")

    try:
        controls = di.get_controls()
    except Exception:
        controls = pd.DataFrame()

    # Enterprise issues (unfiltered by platform) for the appendix
    enterprise_issues: pd.DataFrame | None = None
    try:
        _raw = di.get_issues()
        if qtr:
            _raw_aud = di.get_audits()
            if "quarter" in _raw_aud.columns:
                _qids = set(_raw_aud[_raw_aud["quarter"] == qtr]["audit_id"].tolist())
                enterprise_issues = _raw[_raw["audit_id"].isin(_qids)].copy()
            else:
                enterprise_issues = _raw
        else:
            enterprise_issues = _raw
    except Exception:
        enterprise_issues = all_issues

    view = st.session_state["deck_view"]

    if audits.empty:
        st.info("No audit data for the current filter selection. Adjust the sidebar filters to see a deck preview.")
        return

    slides = _build_slides(audits, all_issues, controls, view, qtr, enterprise_issues)
    n = len(slides)

    # ── Font preload ──────────────────────────────────────────────────────────
    st.markdown(
        "<link href='https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700"
        "&family=IBM+Plex+Mono:wght@500&display=swap' rel='stylesheet'>",
        unsafe_allow_html=True,
    )

    # ── Navigation row ────────────────────────────────────────────────────────
    c_view, c_scope, c_count, c_prev, c_next = st.columns([1.2, 2.2, 2.8, 0.7, 0.7])

    with c_view:
        new_view = st.selectbox(
            "View", ["Platform","Region"],
            index=0 if view == "Platform" else 1,
            key="deck_view_sel", label_visibility="collapsed",
        )
        if new_view != view:
            st.session_state["deck_view"] = new_view
            st.session_state["deck_slide_idx"] = 0
            st.rerun()

    scopes = list(dict.fromkeys(
        s["scope"] for s in slides if s["stype"] not in ("Cover","Appendix")
    ))

    with c_scope:
        if scopes:
            idx = min(st.session_state["deck_slide_idx"], n - 1)
            cur_scope = slides[idx]["scope"]
            default   = cur_scope if cur_scope in scopes else scopes[0]
            sel = st.selectbox(
                "Jump to", scopes,
                index=scopes.index(default) if default in scopes else 0,
                key="deck_scope_sel", label_visibility="collapsed",
            )
            if sel != default:
                for i, s in enumerate(slides):
                    if s["scope"] == sel:
                        st.session_state["deck_slide_idx"] = i
                        st.rerun()
                        break

    idx = min(st.session_state["deck_slide_idx"], n - 1)
    cur = slides[idx]

    with c_count:
        st.markdown(
            f"<div style='display:flex;align-items:center;height:38px;"
            f"font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:#374151;gap:6px;'>"
            f"<span style='color:#9ca3af;'>Slide</span>"
            f"<span style='font-weight:700;color:{_N};'>{idx+1}</span>"
            f"<span style='color:#d1d5db;'>/</span>"
            f"<span style='color:#6b7280;'>{n}</span>"
            f"<span style='color:{_G};font-size:0.62rem;font-weight:600;overflow:hidden;"
            f"text-overflow:ellipsis;white-space:nowrap;'>&nbsp; {cur['title']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c_prev:
        if st.button("◀ Prev", key="deck_prev", use_container_width=True):
            st.session_state["deck_slide_idx"] = max(0, idx - 1)
            st.rerun()

    with c_next:
        if st.button("Next ▶", key="deck_next", use_container_width=True):
            st.session_state["deck_slide_idx"] = min(n - 1, idx + 1)
            st.rerun()

    # ── Slide display ─────────────────────────────────────────────────────────
    st.markdown("<div style='margin:10px 0 6px;border-top:2px solid #e5e7eb;'></div>", unsafe_allow_html=True)
    st.markdown(cur["html"], unsafe_allow_html=True)
    st.markdown("<div style='margin:6px 0;border-bottom:1px solid #e5e7eb;'></div>", unsafe_allow_html=True)

    # ── Thumbnail strip ───────────────────────────────────────────────────────
    strip_start = max(0, idx - 3)
    strip       = slides[strip_start: idx + 5]
    if strip:
        cols = st.columns(len(strip))
        for ci, (col, s) in enumerate(zip(cols, strip)):
            real = strip_start + ci
            active = real == idx
            with col:
                stype_short = s["stype"][:12]
                scope_short = s["scope"][:10]
                if st.button(
                    f"{scope_short}\n{stype_short}",
                    key=f"ds_{real}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                    help=s["title"],
                ):
                    st.session_state["deck_slide_idx"] = real
                    st.rerun()

    # ── Download row ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    dl_col, _, info_col = st.columns([2, 3, 2])

    with dl_col:
        try:
            buf  = _build_pptx(slides, enterprise_issues or all_issues, qtr)
            name = f"AuditIQ_AC_Report_{qtr.replace(' ','_')}.pptx"
            st.download_button(
                label="⬇ Download Full Deck (.pptx)",
                data=buf,
                file_name=name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                type="primary",
            )
        except Exception as e:
            st.caption(f"pptx unavailable: {e}")

    with info_col:
        st.markdown(
            f"<div style='font-size:0.72rem;color:#6b7280;padding:8px 0;text-align:right;'>"
            f"{n} slides &nbsp;·&nbsp; {view} view &nbsp;·&nbsp; Live data"
            f"</div>",
            unsafe_allow_html=True,
        )
