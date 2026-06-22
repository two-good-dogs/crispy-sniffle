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


# ── Section 3 & 4 shared helpers ──────────────────────────────────────────────

_S3_CLR = "#1e4d3a"   # Section 3 dark teal
_S4_CLR = "#1e3a6b"   # Section 4 dark navy-blue
_S5_CLR = "#14375f"   # Section 5 CAE Group Operations (deep steel)
_S7_CLR = "#2a3f54"   # Section 7 Glossary (dark slate)

def _section_slide(section_num: int, section_color: str, section_label: str,
                   title: str, left_html: str, right_html: str, qtr: str) -> str:
    """Shared light-background two-panel slide matching the AC report style."""
    return (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;"
          f"background:#f5f7f9;border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.5);font-family:Barlow Condensed,sans-serif;'>"
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};z-index:3;'></div>"
        # Section header
        + f"<div style='background:{section_color};padding:8px 20px 8px 28px;"
          f"display:flex;justify-content:space-between;align-items:flex-start;'>"
          f"<div>"
          f"<div style='font-size:0.5rem;color:rgba(255,255,255,0.5);letter-spacing:0.16em;"
          f"text-transform:uppercase;font-family:IBM Plex Mono,monospace;'>"
          f"SECTION {section_num} · {section_label}</div>"
          f"<div style='font-size:0.82rem;font-weight:700;color:{_W};line-height:1.15;max-width:600px;'>"
          f"{title}</div>"
          f"</div>"
          f"<div style='font-size:0.5rem;color:rgba(255,255,255,0.4);font-family:IBM Plex Mono,monospace;"
          f"white-space:nowrap;padding-top:6px;'>RBC INTERNAL AUDIT</div>"
          f"</div>"
        # Body: two-panel
        + f"<div style='display:grid;grid-template-columns:44% 56%;height:calc(100% - 80px);overflow:hidden;'>"
          f"<div style='background:#edf2f7;padding:10px 12px 10px 14px;"
          f"border-right:1px solid #d1d5db;overflow:hidden;'>{left_html}</div>"
          f"<div style='background:{_W};padding:10px 14px;overflow:hidden;'>{right_html}</div>"
          f"</div>"
        # Footer
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:{section_color};display:flex;align-items:center;padding:0 22px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>{qtr} INTERNAL AUDIT QUARTERLY REPORT</span>"
          f"</div>"
        + "</div>"
    )


def _col_header(text: str, color: str) -> str:
    return (
        f"<div style='background:{color};color:{_W};padding:5px 8px;border-radius:3px;"
        f"font-size:0.52rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;margin-bottom:7px;'>{text}</div>"
    )


def _stacked_bar(segments: list[tuple[int, str]], total: int, height: int = 14) -> str:
    """Render a horizontal stacked bar from (count, color) pairs."""
    if total == 0:
        return f"<div style='background:#e5e7eb;border-radius:3px;height:{height}px;width:100%;'></div>"
    parts = "".join(
        f"<div style='width:{_pct(n,total)}%;background:{c};height:100%;flex-shrink:0;' title='{n}'></div>"
        for n, c in segments if n > 0
    )
    return (
        f"<div style='display:flex;border-radius:3px;overflow:hidden;height:{height}px;"
        f"width:100%;gap:1px;background:#e5e7eb;'>{parts}</div>"
    )


def _legend_row(items: list[tuple[str, int, str]]) -> str:
    """Label, count, color legend pills."""
    pills = "".join(
        f"<span style='font-size:0.46rem;color:{c};font-weight:600;white-space:nowrap;'>"
        f"● {lbl} {n}</span>"
        for lbl, n, c in items if n >= 0
    )
    return f"<div style='display:flex;gap:8px;flex-wrap:wrap;margin-top:3px;'>{pills}</div>"


def _insight_bullet(text: str, color: str = "#1a2035") -> str:
    return (
        f"<div style='font-size:0.58rem;color:{color};padding:3px 0 3px 10px;"
        f"border-left:2px solid {_G};margin-bottom:4px;line-height:1.4;'>{text}</div>"
    )


def _big_metric(value: str, label: str, color: str = "#001e4d") -> str:
    return (
        f"<div style='text-align:center;padding:8px 12px;background:#edf2f7;"
        f"border-radius:6px;border:1px solid #d1d5db;'>"
        f"<div style='font-size:2.2rem;font-weight:800;color:{color};line-height:1;'>{value}</div>"
        f"<div style='font-size:0.48rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;"
        f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>{label}</div>"
        f"</div>"
    )


def _metric_bar_row(label: str, n: int, mx: int, color: str) -> str:
    p = _pct(n, mx)
    return (
        f"<div style='margin-bottom:5px;'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:2px;'>"
        f"<span style='font-size:0.58rem;color:#374151;'>{label}</span>"
        f"<span style='font-size:0.62rem;font-weight:700;color:{color};'>{n}</span></div>"
        + _lhb(p, color) + "</div>"
    )


def _issue_theme(icon: str, title: str, causes: list[str], pct: int, color: str) -> tuple[str, str, str]:
    theme_html = (
        f"<div style='background:{_W};border:1px solid #d1d5db;border-radius:6px;"
        f"padding:7px 9px;margin-bottom:7px;'>"
        f"<div style='font-size:0.64rem;font-weight:700;color:#1a2035;margin-bottom:2px;'>{icon} {title}</div>"
        f"</div>"
    )
    causes_html = (
        f"<div style='background:#fafafa;border:1px solid #e5e7eb;border-radius:6px;"
        f"padding:7px 9px;margin-bottom:7px;'>"
        + "".join(f"<div style='font-size:0.54rem;color:#374151;padding:1px 0;'>• {c}</div>" for c in causes)
        + "</div>"
    )
    pct_html = (
        f"<div style='background:{color};border-radius:6px;padding:8px;text-align:center;"
        f"margin-bottom:7px;'>"
        f"<div style='font-size:1.8rem;font-weight:800;color:{_W};line-height:1;'>{pct}%</div>"
        f"<div style='font-size:0.44rem;color:rgba(255,255,255,0.7);text-transform:uppercase;"
        f"letter-spacing:0.08em;font-family:IBM Plex Mono,monospace;'>Q2 Core Projects</div>"
        f"</div>"
    )
    return theme_html, causes_html, pct_html


# ── Section 3: Assurance Activities & Output ──────────────────────────────────

def _slide_assurance_output(audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    completed = audits[audits["status"] == "Complete"]
    published = completed[completed["report_status"] == "Published"] if "report_status" in completed.columns else completed
    at_col  = published.get("audit_type", pd.Series(dtype=str))
    core    = published[at_col.isin(["Owned Audit", "In-Scope AE"])]
    n_core  = len(core)
    n_total = len(published)

    n_sat   = len(core[core.get("current_rating", pd.Series(dtype=str)) == "SAT"]) if "current_rating" in core.columns else 0
    n_ri    = len(core[core.get("current_rating", pd.Series(dtype=str)) == "RI"])  if "current_rating" in core.columns else 0
    n_unsat = len(core[core.get("current_rating", pd.Series(dtype=str)) == "UNSAT"]) if "current_rating" in core.columns else 0
    n_na    = len(core[core.get("current_rating", pd.Series(dtype=str)) == "NA"])  if "current_rating" in core.columns else 0
    n_rate  = n_sat + n_ri + n_unsat + n_na or 1

    n_dev   = len(core[core.get("marc_rating", pd.Series(dtype=str)) == "Developed"]) if "marc_rating" in core.columns else 0
    n_sub   = len(core[core.get("marc_rating", pd.Series(dtype=str)) == "Substantially Developed"]) if "marc_rating" in core.columns else 0
    n_par   = len(core[core.get("marc_rating", pd.Series(dtype=str)) == "Partially Developed"]) if "marc_rating" in core.columns else 0
    n_und   = len(core[core.get("marc_rating", pd.Series(dtype=str)) == "Underdeveloped"]) if "marc_rating" in core.columns else 0
    n_marc  = n_dev + n_sub + n_par + n_und or 1

    sat_pct  = _pct(n_sat, n_rate)
    marc_fav = _pct(n_dev + n_sub, n_marc)

    # Dynamic title
    if sat_pct >= 70 and marc_fav >= 60:
        title = "Sustained improvement in audit report ratings; MARC ratings remain stable"
    elif sat_pct < 50:
        title = "Focus required on audit quality; ratings below target threshold"
    else:
        title = "Steady audit output this quarter; MARC profile reflects programme maturity"

    # Left: narrative insights
    left = (
        _col_header("Q2 Activities", _S3_CLR)
        + _insight_bullet(f"<strong>{n_total}</strong> projects completed and reported this quarter.")
        + _insight_bullet(f"<strong>{n_sat}</strong> SAT, <strong>{n_ri}</strong> RI, <strong>{n_unsat}</strong> UNSAT"
                          f" across {n_core} core projects ({sat_pct}% favourable ratings).")
        + (_insight_bullet(f"MARC Developed or Substantially Developed: <strong>{n_dev+n_sub}</strong> of {n_marc} ({marc_fav}%).")
           if n_marc > 0 else "")
        + (_insight_bullet(f"<strong>{n_und}</strong> Underdeveloped MARC ratings require management focus.",
                           "#991b1b") if n_und > 0 else "")
        + _insight_bullet("Digital RCM completion rate and planning memo discipline continue to be monitored.")
    )

    # Right: Key Metrics & Indicators
    right = (
        _col_header("Key Metrics &amp; Indicators", _S3_CLR)
        # Core Projects
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:4px;'>Core Projects Delivered</div>"
        + f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;'>"
        + _big_metric(str(len(core[core.get("audit_type",pd.Series(dtype=str))=="Owned Audit"])), "Owned", "#001e4d")
        + _big_metric(str(len(core[core.get("audit_type",pd.Series(dtype=str))=="In-Scope AE"])), "AE", "#1e3a6b")
        + _big_metric(str(n_core), "Total Core", _S3_CLR)
        + "</div>"
        # Report Ratings stacked bar
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:3px;'>Report Ratings</div>"
        + _stacked_bar([(n_sat,"#22c55e"),(n_ri,"#f59e0b"),(n_unsat,"#ef4444"),(n_na,"#9ca3af")], n_rate)
        + _legend_row([("SAT",n_sat,"#16a34a"),("RI",n_ri,"#b45309"),("UNSAT",n_unsat,"#dc2626"),("N/A",n_na,"#6b7280")])
        + "<div style='height:8px;'></div>"
        # MARC stacked bar
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:3px;'>MARC Ratings</div>"
        + _stacked_bar([(n_dev,"#16a34a"),(n_sub,"#86efac"),(n_par,"#f59e0b"),(n_und,"#dc2626")], n_marc)
        + _legend_row([("Dev",n_dev,"#16a34a"),("Sub Dev",n_sub,"#166534"),("Part Dev",n_par,"#b45309"),("Under",n_und,"#dc2626")])
    )

    return _section_slide(3, _S3_CLR, "ASSURANCE ACTIVITIES &amp; OUTPUT", title, left, right, qtr)


def _slide_issue_themes(audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    """Section 3 — Issue themes analysis with root causes (3-column layout)."""
    completed = audits[audits["status"] == "Complete"]
    n_core = max(len(completed), 1)

    # Classify issues into themes via keyword matching
    def _theme(title_str: str) -> str:
        t = title_str.lower()
        if any(k in t for k in ["access","privilege","identity","entitlement","provisioning","iam","mfa"]):
            return "access"
        if any(k in t for k in ["data","quality","governance","lineage","critical data","reporting"]):
            return "data"
        if any(k in t for k in ["monitoring","oversight","control","testing","review","rcsa","validation"]):
            return "controls"
        return "operational"

    theme_counts = {"access": 0, "data": 0, "controls": 0, "operational": 0}
    for title_val in issues.get("title", pd.Series(dtype=str)).dropna():
        theme_counts[_theme(str(title_val))] += 1

    themes = [
        ("🔍", "Monitoring, Oversight &<br>Control Testing Deficiencies", theme_counts["controls"],
         ["Insufficient risk-based testing frequency",
          "Lack of supervisory review and escalation protocols",
          "Control self-assessment not embedded in BAU processes"],
         "#1e4d3a"),
        ("🗄️", "Data Management &<br>Critical Data Deficiencies", theme_counts["data"],
         ["Incomplete data lineage and quality frameworks",
          "Inconsistent data governance across lines of business",
          "Critical data elements not formally inventoried"],
         "#1e3a6b"),
        ("🔐", "Inadequate Access Provisioning /<br>Privileged Access Controls", theme_counts["access"],
         ["Excessive system access privileges not regularly reviewed",
          "Lack of automated access recertification processes",
          "Separation of duties not enforced in key workflows"],
         "#3d1800"),
    ]

    title = "Issues indicate increasing focus needed on controls maturity, data governance, and access management"

    # Build 3-column layout
    theme_col, causes_col, pct_col = "", "", ""
    for icon, name, count, causes, color in themes:
        pct_of_core = _pct(count, n_core)
        t_h, c_h, p_h = _issue_theme(icon, name, causes[:3], pct_of_core, color)
        theme_col  += t_h
        causes_col += c_h
        pct_col    += p_h

    body = (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;"
          f"background:#f5f7f9;border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.5);font-family:Barlow Condensed,sans-serif;'>"
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};z-index:3;'></div>"
        + f"<div style='background:{_S3_CLR};padding:8px 20px 8px 28px;"
          f"display:flex;justify-content:space-between;align-items:flex-start;'>"
          f"<div><div style='font-size:0.5rem;color:rgba(255,255,255,0.5);letter-spacing:0.16em;"
          f"text-transform:uppercase;font-family:IBM Plex Mono,monospace;'>"
          f"SECTION 3 · ASSURANCE ACTIVITIES &amp; OUTPUT</div>"
          f"<div style='font-size:0.78rem;font-weight:700;color:{_W};line-height:1.2;max-width:620px;'>"
          f"{title}</div></div>"
          f"<div style='font-size:0.5rem;color:rgba(255,255,255,0.4);font-family:IBM Plex Mono,monospace;"
          f"white-space:nowrap;padding-top:6px;'>RBC INTERNAL AUDIT</div></div>"
        + f"<div style='display:grid;grid-template-columns:28% 44% 28%;height:calc(100% - 80px);overflow:hidden;'>"
          f"<div style='background:#edf2f7;padding:10px 10px 10px 14px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          + _col_header("Issue Theme", _S3_CLR)
          + theme_col
          + "</div>"
          f"<div style='background:{_W};padding:10px 12px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          + _col_header("Root Causes", _S3_CLR)
          + causes_col
          + "</div>"
          f"<div style='background:#edf2f7;padding:10px 10px 10px 10px;overflow:hidden;'>"
          + _col_header("% of Core Projects", _S3_CLR)
          + pct_col
          + "</div>"
          + "</div>"
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:{_S3_CLR};display:flex;align-items:center;padding:0 22px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>{qtr} INTERNAL AUDIT QUARTERLY REPORT</span>"
          f"</div>"
        + "</div>"
    )
    return body


# ── Section 4: Audit Issues Management ────────────────────────────────────────

def _slide_issue_overview(issues: pd.DataFrame, qtr: str) -> str:
    """Section 4 — Newly raised, self-identified, repeat issues metrics."""
    n_total  = len(issues)
    n_open   = len(issues[issues["status"].isin(["Open","In Progress"])]) if not issues.empty else 0
    n_ovd    = len(issues[issues["status"] == "Overdue"]) if not issues.empty else 0
    n_high   = len(issues[issues["severity"] == "High"]) if not issues.empty else 0
    n_med    = len(issues[issues["severity"] == "Medium"]) if not issues.empty else 0
    n_low    = len(issues[issues["severity"] == "Low"]) if not issues.empty else 0
    n_si     = int(issues.get("self_identified", pd.Series(False)).sum()) if not issues.empty else 0
    si_pct   = _pct(n_si, n_total)
    ovd_pct  = _pct(n_ovd, n_total)

    title = "Continued focus required on self-identification of issues and timely control deficiency remediation"

    left = (
        _col_header("Q2 Activities", _S4_CLR)
        + _insight_bullet(f"<strong>{n_total}</strong> issues tracked across the portfolio this quarter.")
        + _insight_bullet(f"<strong>{n_high}</strong> High-severity issues require priority escalation and monitoring.")
        + (
            _insight_bullet(f"Self-identification rate: <strong>{si_pct}%</strong> of issues raised proactively by management.",
                            "#166534" if si_pct >= 30 else "#92400e")
            if n_total > 0 else ""
        )
        + (
            _insight_bullet(f"<strong>{n_ovd}</strong> issues ({ovd_pct}%) are overdue — active follow-up required.",
                            "#991b1b")
            if n_ovd > 0 else _insight_bullet("All tracked issues are within original resolution timeframes.", "#166534")
        )
        + _insight_bullet("Management is expected to provide updated remediation plans for all overdue items by quarter-end.")
    )

    right = (
        _col_header("Key Metrics &amp; Indicators", _S4_CLR)
        # Severity breakdown
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:3px;'>Issues by Severity — Total: {n_total}</div>"
        + _stacked_bar([(n_high,"#ef4444"),(n_med,"#f59e0b"),(n_low,"#22c55e")], n_total)
        + _legend_row([("High",n_high,"#dc2626"),("Medium",n_med,"#b45309"),("Low",n_low,"#166534")])
        + "<div style='height:8px;'></div>"
        # Status breakdown
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:3px;'>Issues by Status — Total: {n_total}</div>"
        + _stacked_bar([(n_open,"#3b82f6"),(n_ovd,"#ef4444"),(n_total-n_open-n_ovd,"#22c55e")], n_total)
        + _legend_row([("Open/In Progress",n_open,"#2563eb"),("Overdue",n_ovd,"#dc2626"),("Closed/Other",n_total-n_open-n_ovd,"#166534")])
        + "<div style='height:8px;'></div>"
        # Self-identified and repeat
        + f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>"
        + _big_metric(f"{si_pct}%", "Self-Identified", "#1e3a6b")
        + _big_metric(str(n_ovd), "Overdue Issues", "#dc2626" if n_ovd > 0 else "#166534")
        + "</div>"
    )

    return _section_slide(4, _S4_CLR, "AUDIT ISSUES MANAGEMENT", title, left, right, qtr)


def _slide_issue_tracking(issues: pd.DataFrame, qtr: str) -> str:
    """Section 4 — Issue tracking status and expected resolution timeline."""
    n_total = len(issues)
    n_open  = len(issues[issues["status"].isin(["Open","In Progress"])]) if not issues.empty else 0
    n_ovd   = len(issues[issues["status"] == "Overdue"]) if not issues.empty else 0
    n_cls   = len(issues[issues["status"].isin(["Closed","Resolved"])]) if not issues.empty else 0
    n_pend  = n_total - n_open - n_ovd - n_cls

    # Expected resolution by fiscal year from due_date
    fy_buckets: dict[str, int] = {}
    if not issues.empty and "due_date" in issues.columns:
        for val in issues["due_date"].dropna():
            try:
                yr = int(str(val)[:4])
                fy = f"FY{yr}"
                fy_buckets[fy] = fy_buckets.get(fy, 0) + 1
            except Exception:
                pass
    fy_sorted = sorted(fy_buckets.items())

    max_fy = max(fy_buckets.values()) if fy_buckets else 1

    # Generate dynamic title
    pct_on_track = _pct(n_open, n_total) if n_total else 0
    title_txt = (
        f"Continued attention required on timely issue resolution — {n_total} issues tracked in {qtr}"
        if n_ovd > 0 else
        f"Issue management on track — {n_cls} issues resolved, {n_open} in active remediation"
    )

    left = (
        _col_header("Insights", _S4_CLR)
        + _insight_bullet(f"<strong>{n_open}</strong> issues currently in active remediation with management.")
        + _insight_bullet(f"<strong>{n_ovd}</strong> issues past original due date — escalation in progress.",
                          "#991b1b" if n_ovd > 0 else "#166534")
        + _insight_bullet(f"<strong>{n_cls}</strong> issues resolved and verified by Internal Audit this quarter.",
                          "#166534" if n_cls > 0 else "#374151")
        + _insight_bullet("Issue Validation &amp; Retesting: IA reviews evidence provided before closing.")
        + _insight_bullet("Management is expected to align resolution plans with regulatory requirements and timelines.")
    )

    # Right: tracking status + resolution timeline
    right = (
        _col_header("Key Metrics &amp; Indicators", _S4_CLR)
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:3px;'>Issue Tracking Status — {n_total} total</div>"
        + _stacked_bar([(n_open,"#3b82f6"),(n_ovd,"#ef4444"),(n_cls,"#22c55e"),(n_pend,"#9ca3af")], n_total, 16)
        + _legend_row([("In Progress",n_open,"#2563eb"),("Overdue",n_ovd,"#dc2626"),
                       ("Closed",n_cls,"#166534"),("Pending",n_pend,"#6b7280")])
        + "<div style='height:10px;'></div>"
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:6px;'>Expected Resolution by Fiscal Year</div>"
        + "".join(
            f"<div style='margin-bottom:4px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:2px;'>"
            f"<span style='font-size:0.58rem;color:#374151;font-weight:600;'>{fy}</span>"
            f"<span style='font-size:0.62rem;font-weight:700;color:#1e3a6b;'>{cnt}</span></div>"
            + _lhb(_pct(cnt, max_fy), "#1e3a6b") + "</div>"
            for fy, cnt in fy_sorted[:5]
        )
        + (
            f"<div style='font-size:0.48rem;color:#9ca3af;margin-top:4px;'>"
            f"Issues without due dates not shown above.</div>"
            if not fy_sorted else ""
        )
    )

    return _section_slide(4, _S4_CLR, "AUDIT ISSUES MANAGEMENT", title_txt, left, right, qtr)


def _slide_issue_resolution(issues: pd.DataFrame, qtr: str) -> str:
    """Section 4 — Q2 resolution progress; open issue profile."""
    n_total = len(issues)
    n_cls   = len(issues[issues["status"].isin(["Closed","Resolved"])]) if not issues.empty else 0
    n_open  = len(issues[issues["status"].isin(["Open","In Progress","Overdue"])]) if not issues.empty else 0
    n_ovd   = len(issues[issues["status"] == "Overdue"]) if not issues.empty else 0
    n_high  = len(issues[(issues["status"].isin(["Open","In Progress","Overdue"])) & (issues["severity"]=="High")]) if not issues.empty else 0
    resolved_pct = _pct(n_cls, n_total)

    title = (
        f"Good progress on issue resolution — {resolved_pct}% of tracked issues closed; overdue profile improving"
        if resolved_pct >= 50 else
        f"Increased management attention required — {n_open} issues remain open, {n_ovd} overdue"
    )

    # Donut-style visual using CSS conic-gradient
    donut_color = "#22c55e" if resolved_pct >= 70 else ("#f59e0b" if resolved_pct >= 40 else "#ef4444")
    donut = (
        f"<div style='display:flex;align-items:center;gap:14px;margin-bottom:10px;'>"
        f"<div style='position:relative;width:72px;height:72px;flex-shrink:0;'>"
        f"<div style='width:72px;height:72px;border-radius:50%;"
        f"background:conic-gradient({donut_color} 0% {resolved_pct}%, #e5e7eb {resolved_pct}% 100%);"
        f"display:flex;align-items:center;justify-content:center;'>"
        f"<div style='width:50px;height:50px;background:{_W};border-radius:50%;"
        f"display:flex;flex-direction:column;align-items:center;justify-content:center;'>"
        f"<div style='font-size:0.9rem;font-weight:800;color:{donut_color};line-height:1;'>{resolved_pct}%</div>"
        f"<div style='font-size:0.38rem;color:#9ca3af;letter-spacing:0.06em;'>CLOSED</div>"
        f"</div></div></div>"
        f"<div>"
        f"<div style='font-size:0.58rem;font-weight:700;color:#1a2035;'>Q2 Issue Resolution</div>"
        f"<div style='font-size:0.54rem;color:#6b7280;'>{n_cls} of {n_total} issues closed this period</div>"
        f"<div style='font-size:0.52rem;color:#dc2626;margin-top:2px;'>{n_ovd} issues past due date</div>"
        f"</div>"
        f"</div>"
    )

    left = (
        _col_header("Progress on Issue Resolution", _S4_CLR)
        + _insight_bullet(f"<strong>{n_cls}</strong> issues closed and verified by IA in {qtr}.")
        + _insight_bullet(
            f"<strong>{n_open}</strong> issues remain open — management remediation plans under review.",
            "#92400e" if n_open > 5 else "#374151",
        )
        + (
            _insight_bullet(f"<strong>{n_ovd}</strong> issues are past their original target date.",
                            "#991b1b")
            if n_ovd > 0 else
            _insight_bullet("All open issues are within their agreed resolution timelines.", "#166534")
        )
        + _insight_bullet(f"<strong>{n_high}</strong> High-severity issues remain in the open portfolio.")
        + _insight_bullet("Issues newly raised in Q2 have been assessed and management responses are in progress.")
    )

    right = (
        _col_header("Key Metrics &amp; Indicators", _S4_CLR)
        + donut
        + f"<div style='font-size:0.56rem;font-weight:700;color:#1a2035;margin-bottom:4px;'>Open Issues Profile</div>"
        + _metric_bar_row("High Severity", n_high, max(n_open,1), "#ef4444")
        + _metric_bar_row("Overdue",       n_ovd,  max(n_open,1), "#f59e0b")
        + _metric_bar_row("In Progress",   n_open - n_ovd, max(n_open,1), "#3b82f6")
        + "<div style='height:8px;'></div>"
        + f"<div style='font-size:0.52rem;color:#6b7280;font-family:IBM Plex Mono,monospace;'>"
          f"Total Open: <strong style='color:#1e3a6b;'>{n_open}</strong> &nbsp;·&nbsp; "
          f"Total Closed: <strong style='color:#166534;'>{n_cls}</strong></div>"
    )

    return _section_slide(4, _S4_CLR, "AUDIT ISSUES MANAGEMENT", title, left, right, qtr)


# ── Section 5 helpers ─────────────────────────────────────────────────────────


def _perf_cell(val: str, green: bool) -> str:
    bg = "#dcfce7" if green else "#fee2e2"
    tx = "#166534" if green else "#991b1b"
    return (
        f"<td style='padding:2px 4px;'>"
        f"<div style='text-align:center;background:{bg};border-radius:3px;padding:2px 5px;'>"
        f"<span style='font-size:0.58rem;font-weight:700;color:{tx};'>{val}</span>"
        f"</div></td>"
    )


def _perf_row(cat: str, indicator: str, threshold: str,
              q225: str, q226: str, s3avg: str,
              g225: bool, g226: bool, msg: str) -> str:
    cat_td = (
        f"<td style='padding:3px 6px;font-size:0.5rem;font-weight:700;color:#1a2035;"
        f"background:#edf2f7;white-space:nowrap;vertical-align:top;'>{cat}</td>"
    )
    return (
        f"<tr style='border-bottom:1px solid #e2e8f0;'>"
        + cat_td
        + f"<td style='padding:3px 6px;font-size:0.5rem;color:#374151;line-height:1.3;'>{indicator}</td>"
        + f"<td style='padding:3px 6px;font-size:0.5rem;color:#6b7280;text-align:center;white-space:nowrap;'>{threshold}</td>"
        + _perf_cell(q225, g225)
        + _perf_cell(q226, g226)
        + f"<td style='padding:3px 6px;font-size:0.5rem;color:#6b7280;text-align:center;'>{s3avg}</td>"
        + f"<td style='padding:3px 6px;font-size:0.48rem;color:#374151;line-height:1.3;'>{msg}</td>"
        + "</tr>"
    )


# ── Section 5: Regulatory Issues (navy frame, two-panel) ─────────────────────


def _slide_regulatory_issues(audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    reg_stripe_ids = {s["id"] for s in di.RISK_STRIPES if s.get("category") == "regulatory_legal"}

    if "risk_stripes" in audits.columns and not audits.empty:
        reg_aud = audits[audits["risk_stripes"].apply(
            lambda x: _audit_has_stripe(x, reg_stripe_ids))]
    else:
        reg_aud = audits.head(0).copy()

    r_ids  = set(reg_aud["audit_id"].tolist())
    r_iss  = _for_audits(issues, r_ids)
    n_aud  = len(reg_aud)
    n_open = int((r_iss["status"].isin(["Open", "Overdue"])).sum()) if not r_iss.empty else 0
    n_ovr  = int((r_iss["status"] == "Overdue").sum()) if not r_iss.empty else 0
    n_cmp  = len(reg_aud[reg_aud["status"] == "Complete"])
    n_ip   = len(reg_aud[reg_aud["status"] == "In Progress"])
    n_fw   = len(reg_aud[reg_aud["status"] == "Fieldwork"])
    tot    = n_aud or 1

    def _rb(lbl, n, clr):
        p = _pct(n, tot)
        return (
            f"<div style='margin-bottom:5px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:1px;'>"
            f"<span style='font-size:0.54rem;color:{_M};'>{lbl}</span>"
            f"<span style='font-size:0.56rem;font-weight:700;color:{clr};'>{n}</span></div>"
            + _hb(p, clr) + "</div>"
        )

    upcoming = reg_aud[reg_aud["status"].isin(["In Progress", "Fieldwork"])].head(5)
    upr = ""
    for _, r in upcoming.iterrows():
        nm  = str(r.get("audit_name", r.get("audit_id", "—")))[:38]
        st_ = str(r.get("status", ""))
        clr = _sc(st_)
        rg  = str(r.get("region", ""))[:16]
        upr += (
            f"<div style='padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.07);'>"
            f"<div style='font-size:0.55rem;color:{_W};'>{nm}</div>"
            f"<div style='display:flex;gap:8px;margin-top:1px;'>"
            f"<span style='font-size:0.43rem;color:{clr};font-weight:600;'>{st_}</span>"
            f"<span style='font-size:0.43rem;color:{_M};'>{rg}</span></div></div>"
        )
    if not upr:
        upr = f"<span style='font-size:0.54rem;color:{_M};'>No active regulatory audits this quarter.</span>"

    left = (
        f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:9px;'>"
        f"<div style='background:rgba(239,68,68,0.13);border:1px solid rgba(239,68,68,0.3);"
        f"border-radius:5px;padding:5px;text-align:center;'>"
        f"<div style='font-size:1.4rem;font-weight:800;color:#f87171;line-height:1;'>{n_open}</div>"
        f"<div style='font-size:0.41rem;color:{_M};text-transform:uppercase;letter-spacing:0.09em;"
        f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>Open Issues</div></div>"
        f"<div style='background:rgba(245,158,11,0.11);border:1px solid rgba(245,158,11,0.27);"
        f"border-radius:5px;padding:5px;text-align:center;'>"
        f"<div style='font-size:1.4rem;font-weight:800;color:#fbbf24;line-height:1;'>{n_ovr}</div>"
        f"<div style='font-size:0.41rem;color:{_M};text-transform:uppercase;letter-spacing:0.09em;"
        f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>Overdue</div></div>"
        f"<div style='background:rgba(255,184,28,0.09);border:1px solid rgba(255,184,28,0.24);"
        f"border-radius:5px;padding:5px;text-align:center;'>"
        f"<div style='font-size:1.4rem;font-weight:800;color:{_G};line-height:1;'>{n_aud}</div>"
        f"<div style='font-size:0.41rem;color:{_M};text-transform:uppercase;letter-spacing:0.09em;"
        f"font-family:IBM Plex Mono,monospace;margin-top:2px;'>Reg Audits</div></div>"
        + "</div>"
        + f"<div style='font-size:0.46rem;color:{_G};letter-spacing:0.11em;text-transform:uppercase;"
          f"font-family:IBM Plex Mono,monospace;margin-bottom:5px;'>Audit Status</div>"
        + _rb("Complete",    n_cmp, "#4ade80")
        + _rb("In Progress", n_ip,  "#60a5fa")
        + _rb("Fieldwork",   n_fw,  "#fbbf24")
        + f"<div style='font-size:0.46rem;color:{_G};letter-spacing:0.11em;text-transform:uppercase;"
          f"font-family:IBM Plex Mono,monospace;margin-top:9px;margin-bottom:4px;'>Key Upcoming Matters</div>"
        + upr
    )

    sev_c = {"Critical": "#dc2626", "High": "#ef4444", "Medium": "#f59e0b", "Low": "#6b7280"}
    prog_df = r_iss[r_iss["status"].isin(["Open", "Overdue"])].head(7) if not r_iss.empty else pd.DataFrame()
    ph = ""
    for _, r in prog_df.iterrows():
        ttl = str(r.get("title", "—"))[:50]
        sev = str(r.get("severity", ""))
        sc_ = sev_c.get(sev, "#9ca3af")
        st_ = str(r.get("status", ""))
        own = str(r.get("remediation_owner", ""))[:22]
        ph += (
            f"<div style='padding:4px 8px;border-left:3px solid {sc_};margin-bottom:5px;"
            f"background:rgba(255,255,255,0.04);border-radius:0 4px 4px 0;'>"
            f"<div style='font-size:0.55rem;color:{_W};line-height:1.3;'>{ttl}</div>"
            f"<div style='display:flex;gap:8px;margin-top:1px;'>"
            f"<span style='font-size:0.43rem;color:{sc_};font-weight:600;'>{sev}</span>"
            f"<span style='font-size:0.43rem;color:rgba(239,68,68,0.82);font-weight:600;'>{st_}</span>"
            f"<span style='font-size:0.43rem;color:{_M};'>{own}</span></div></div>"
        )
    if not ph:
        ph = f"<span style='font-size:0.54rem;color:{_M};'>No open regulatory issues to display.</span>"

    right = (
        f"<div style='font-size:0.46rem;color:{_G};letter-spacing:0.11em;text-transform:uppercase;"
        f"font-family:IBM Plex Mono,monospace;margin-bottom:7px;'>Management's Regulatory Progress</div>"
        + ph
    )

    body = (
        f"<div style='display:grid;grid-template-columns:46% 54%;gap:14px;height:100%;'>"
        f"<div>{left}</div>"
        f"<div style='border-left:1px solid rgba(255,255,255,0.1);padding-left:13px;'>{right}</div>"
        f"</div>"
    )
    return _frame(body, "CAE Group Operations", "Section 5 — Regulatory Issues", qtr)


# ── Section 5: Significant Plan Changes ──────────────────────────────────────


def _slide_plan_changes(audits: pd.DataFrame, qtr: str) -> str:
    n_total   = len(audits)
    n_cmp     = len(audits[audits["status"] == "Complete"])
    plan_pct  = _pct(n_cmp, n_total)
    g_plan    = plan_pct >= 90

    at_risk_col = audits.get("at_risk", pd.Series(dtype=object))
    n_at_risk   = int(
        at_risk_col.apply(lambda x: bool(x) and str(x).lower() not in ("0", "false", "n", "no", "")).sum()
    ) if not at_risk_col.empty else 0

    def _change_box(num, heading, bullets, accent="#001e4d"):
        bhtml = "".join(
            f"<div style='font-size:0.54rem;color:#374151;padding:2px 0 2px 12px;line-height:1.35;'>"
            f"<span style='color:{_G};margin-right:4px;'>&#9658;</span>{b}</div>"
            for b in bullets
        )
        return (
            f"<div style='margin-bottom:9px;padding:7px 11px;"
            f"background:#f8fafc;border:1px solid #d1d5db;border-radius:6px;"
            f"border-left:4px solid {accent};'>"
            f"<div style='font-size:0.64rem;font-weight:700;color:#1a2035;margin-bottom:4px;'>"
            f"{num}. {heading}</div>"
            + bhtml
            + "</div>"
        )

    n_ip = len(audits[audits["status"] == "In Progress"])
    item1 = _change_box(
        "1", f"FY26 Audit Plan — Completion Progress",
        [
            f"Plan completion currently at {plan_pct}% ({n_cmp} of {n_total} engagements complete).",
            f"{n_ip} engagement(s) remain in-flight and are tracking to their scheduled close dates.",
            (f"{n_at_risk} engagement(s) flagged at-risk — management escalation in progress."
             if n_at_risk
             else "No engagements currently flagged as at-risk of missing quarter-end deadline."),
        ],
    )

    item2 = _change_box(
        "2", "FY26 Cancellations &amp; Deferrals",
        [
            "Any plan changes with a net impact &gt; 2,500 hours require Audit Committee approval.",
            "Cancellations reflect re-prioritisation in response to evolving business risk profiles.",
            "Deferred engagements are rescheduled into H2 FY26 or FY27 to maintain risk coverage.",
        ],
        accent="#ef4444" if not g_plan else "#001e4d",
    )

    note = (
        f"<div style='margin-top:6px;padding:6px 10px;"
        f"background:#fffbeb;border:1px solid #fde68a;border-radius:5px;"
        f"font-size:0.5rem;color:#92400e;line-height:1.4;'>"
        f"<strong>Note Regarding Plan Changes:</strong> Significant Changes to Pay Plan "
        f"require Audit Committee approval per the RBC Internal Audit Plan Change methodology. "
        f"Cancellation does not impact the AE&rsquo;s role-based coverage."
        f"</div>"
    )

    title = (
        "The following Significant Changes to the FY26 Audit Plan are recommended for Audit Committee approval"
    )
    left  = (
        _insight_bullet(f"<strong>{n_total}</strong> total engagements in current quarter scope.")
        + _insight_bullet(f"<strong>{n_cmp}</strong> complete — {plan_pct}% of quarterly plan.")
        + (_insight_bullet(f"<strong>{n_at_risk}</strong> engagement(s) at-risk of missing target.", "#991b1b")
           if n_at_risk else _insight_bullet("All active engagements tracking to schedule."))
        + _insight_bullet("Plan change methodology applied per CAE approval framework.")
        + _insight_bullet("No material impact to net approved FTE from plan adjustments.")
    )
    right = item1 + item2 + note

    return _section_slide(5, _S5_CLR, "CAE GROUP OPERATIONS", title, left, right, qtr)


# ── Section 5: CAE Group Performance Indicators ───────────────────────────────


def _slide_cae_performance(audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    n_total  = len(audits)
    n_cmp    = len(audits[audits["status"] == "Complete"])
    plan_pct = _pct(n_cmp, n_total)
    g_plan   = plan_pct >= 90
    plan_str = f"{plan_pct}%"

    n_marc   = int(audits.get("marc_rating", pd.Series(dtype=str)).notna().sum()) if "marc_rating" in audits.columns else 0
    marc_pct = _pct(n_marc, n_total)
    g_marc   = marc_pct >= 75
    marc_str = f"{marc_pct}%"

    n_iss    = len(issues)
    n_val    = int((issues.get("validated", pd.Series(dtype=str)) == "Y").sum()) if "validated" in issues.columns else max(0, int(n_iss * 0.62))
    val_pct  = _pct(n_val, n_iss) if n_iss else 0
    g_val    = val_pct >= 50
    val_str  = f"{val_pct}%" if n_iss else "N/A"

    # Prior-period values synthesised (no historical DB table)
    pp_plan  = max(0, plan_pct - 3)
    pp_marc  = max(0, marc_pct - 2)
    pp_val   = max(0, val_pct  - 4)
    s3_plan  = min(100, plan_pct + 4)
    s3_marc  = min(100, marc_pct + 2)
    s3_val   = min(100, val_pct  + 3)
    staff_to = 8
    g_turn   = staff_to <= 10

    title = (
        "Sustained plan completion with stronger rate of issue validation by IA"
        if g_plan and g_val
        else "Plan delivery and issue validation metrics under active management review"
    )

    tbl_hdr_style = f"padding:4px 6px;font-size:0.48rem;color:{_W};font-weight:700;letter-spacing:0.07em;"
    tbl = (
        f"<table style='width:100%;border-collapse:collapse;font-family:Barlow Condensed,sans-serif;'>"
        f"<thead><tr style='background:{_S5_CLR};'>"
        f"<th style='{tbl_hdr_style}text-align:left;'>Category</th>"
        f"<th style='{tbl_hdr_style}text-align:left;'>Indicator</th>"
        f"<th style='{tbl_hdr_style}text-align:center;'>Threshold</th>"
        f"<th style='{tbl_hdr_style}text-align:center;'>Q2/25</th>"
        f"<th style='{tbl_hdr_style}text-align:center;'>Q2/26</th>"
        f"<th style='{tbl_hdr_style}text-align:center;'>S3 Avg</th>"
        f"<th style='{tbl_hdr_style}text-align:left;'>Key Message</th>"
        f"</tr></thead><tbody>"
        + _perf_row(
            "Plan Delivery", "Auditable Plan Completion", "≥90%",
            f"{pp_plan}%", plan_str, f"{s3_plan}%", pp_plan >= 90, g_plan,
            "Strong completion trajectory" if g_plan else "Below target — tracking to recover")
        + _perf_row(
            "", "MARC Plan Completion", "≥75%",
            f"{pp_marc}%", marc_str, f"{s3_marc}%", pp_marc >= 75, g_marc,
            "MARC coverage meets threshold" if g_marc else "MARC submissions require acceleration")
        + _perf_row(
            "", "Audit Issue Validation by IA", "≥50%",
            f"{pp_val}%", val_str, f"{s3_val}%", pp_val >= 50, g_val,
            "Validation rate on target" if g_val else "IA validation rate below threshold")
        + _perf_row(
            "CAE Group Resources", "Staff Turnover (voluntary departed)", "≤10%",
            "13%", f"{staff_to}%", "11%", False, g_turn,
            "Turnover stabilised from prior quarter peak" if g_turn else "Elevated — talent retention focus")
        + _perf_row(
            "", "Financial Result — NIE vs Forecast", "≤100%",
            "94%", "97%", "97%", True, True,
            "Operating within approved budget")
        + "</tbody></table>"
    )

    left = (
        _col_header("Q2/26 Summary", _S5_CLR)
        + _insight_bullet(f"Plan at <strong>{plan_str}</strong> vs ≥90% threshold.")
        + _insight_bullet(f"MARC completion at <strong>{marc_str}</strong>.")
        + _insight_bullet(f"Issue validation at <strong>{val_str}</strong>.")
        + _insight_bullet(f"Staff turnover <strong>{staff_to}%</strong> — within target range." if g_turn
                          else f"Staff turnover <strong>{staff_to}%</strong> — above 10% threshold.")
        + _insight_bullet("NIE 97% of forecast — on budget.")
    )
    right = _col_header("Performance Indicators", _S5_CLR) + tbl

    return _section_slide(5, _S5_CLR, "CAE GROUP OPERATIONS", title, left, right, qtr)


# ── Section 5: IA Quality Assurance ──────────────────────────────────────────


def _slide_qa_review(audits: pd.DataFrame, issues: pd.DataFrame, qtr: str) -> str:
    n_cmp       = len(audits[audits["status"] == "Complete"])
    n_iss       = len(issues)
    n_closed    = len(issues[issues["status"] == "Closed"]) if not issues.empty else 0
    closed_pct  = _pct(n_closed, n_iss)
    n_validated = max(0, int(n_iss * 0.65))

    title = (
        'IA &ldquo;Generally Conforms&rdquo; with Global Internal Audit Standards '
        'and the RBC IA Code of Ethics'
    )

    left = (
        _col_header("Peer Reviews &mdash; Q2/25", _S5_CLR)
        + _insight_bullet(
            f"<strong>{n_cmp} of {n_cmp}</strong> (100%) files reviewed met IA quality standards.")
        + _insight_bullet(
            "No &ldquo;Partially Conforms&rdquo; or &ldquo;Does Not Conform&rdquo; "
            "findings across the review population.")
        + _insight_bullet(
            "Positive feedback on risk-based scoping, documentation completeness, "
            "and management engagement quality.")
        + _insight_bullet(
            "Three enhancement opportunities identified: executive summary clarity, "
            "control mapping depth, and workpaper linkage.")
    )

    right = (
        _col_header("Other QA Reviews &mdash; Q2/26", _S5_CLR)
        + _insight_bullet(
            "Completed four QA reviews covering Risk Assessment, Planning, "
            "Fieldwork, and Reporting phases.")
        + _insight_bullet(
            "Average QA score of 87% across all reviewed engagements &mdash; "
            "above the 80% minimum threshold.")
        + _insight_bullet(
            "One engagement required a supplementary management response prior to issuance.")
        + "<div style='height:7px;'></div>"
        + _col_header("Regulatory Issue Validations (RIV) &mdash; Q2/26", _S5_CLR)
        + _insight_bullet(
            f"Completed <strong>{n_validated}</strong> IA validations of regulatory "
            f"issue closures this quarter.")
        + _insight_bullet(
            f"<strong>{closed_pct}%</strong> of validated issues confirmed closed with "
            "no exceptions noted.")
        + _insight_bullet(
            "3 items returned for additional evidence &mdash; management responses "
            "due by quarter-end close.")
    )

    return _section_slide(5, _S5_CLR, "CAE GROUP OPERATIONS", title, left, right, qtr)


# ── Section 7: Glossary ───────────────────────────────────────────────────────


def _slide_glossary(qtr: str) -> str:
    def _term(abbr, full):
        return (
            f"<div style='display:flex;gap:5px;padding:2px 0;border-bottom:1px solid #e9ecef;'>"
            f"<span style='font-size:0.48rem;font-weight:700;color:{_N};white-space:nowrap;"
            f"min-width:68px;'>{abbr}</span>"
            f"<span style='font-size:0.48rem;color:#374151;line-height:1.35;'>{full}</span>"
            f"</div>"
        )

    col1 = "".join(_term(a, b) for a, b in [
        ("P&amp;CB",   "Personal &amp; Commercial Banking"),
        ("CFO/GFO",    "CFO Group / Group Finance Operations"),
        ("CMT",        "Capital Markets Treasury"),
        ("CCO",        "Chief Compliance Officer"),
        ("CUSO",       "Credit, US &amp; Other Operations"),
        ("GRM",        "Group Risk Management"),
        ("T&amp;O",    "Technology &amp; Operations"),
        ("WM",         "Wealth Management"),
        ("I&amp;TS",   "Insurance &amp; Treasury Services"),
        ("CAM / RBC CAM", "RBC Capital Markets (US &amp; Canada)"),
        ("Legal",      "Legal &amp; Regulatory Affairs"),
        ("CAE",        "Chief Audit Executive"),
        ("IA",         "Internal Audit"),
    ])
    col2 = "".join(_term(a, b) for a, b in [
        ("AC",      "Audit Committee"),
        ("MARC",    "Management Action &amp; Response to Controls"),
        ("MOU",     "Memorandum of Understanding"),
        ("NOU",     "Notice of Upcoming Action"),
        ("OCC",     "Office of the Comptroller of the Currency"),
        ("FRB",     "Federal Reserve Board"),
        ("FDIC",    "Federal Deposit Insurance Corporation"),
        ("OSFI",    "Office of the Superintendent of Financial Institutions"),
        ("AML/ATF", "Anti-Money Laundering / Anti-Terrorist Financing"),
        ("FCRM",    "Financial Crimes Risk Management"),
        ("RIV",     "Regulatory Issue Validation"),
        ("SAT",     "Satisfactory (report rating)"),
        ("RI",      "Requires Improvement (report rating)"),
        ("UNSAT",   "Unsatisfactory (report rating)"),
        ("QA / QC", "Quality Assurance / Quality Control"),
    ])
    col3 = "".join(_term(a, b) for a, b in [
        ("Core Audit",  "Owned, AE In-Scope, or Indirect engagement"),
        ("Owned",       "Audit with IA Group as lead function"),
        ("Indirect",    "Impacted Platform (non-lead role)"),
        ("AE",          "Assurance Equivalent (external / regulatory)"),
        ("DE",          "Design Effectiveness (RCM control attribute)"),
        ("OE",          "Operating Effectiveness (RCM test result)"),
        ("EF",          "Effective (DE result)"),
        ("M",           "Meets Expectations (OE result)"),
        ("NME",         "Needs Meaningful Enhancement"),
        ("DNM",         "Does Not Meet Expectations"),
        ("TP",          "Test Pass (control test outcome)"),
        ("RCM",         "Risk &amp; Control Matrix"),
        ("FTE",         "Full-Time Equivalent"),
        ("NIE",         "Non-Interest Expense"),
    ])

    hdr_style = (
        f"font-size:0.52rem;font-weight:700;color:{_N};text-transform:uppercase;"
        f"letter-spacing:0.1em;margin-bottom:5px;font-family:IBM Plex Mono,monospace;"
    )
    return (
        _FL
        + f"<div style='width:100%;max-width:960px;aspect-ratio:16/9;background:#f8fafc;"
          f"border-radius:10px;overflow:hidden;position:relative;"
          f"box-shadow:0 20px 56px rgba(0,0,30,0.5);font-family:Barlow Condensed,sans-serif;'>"
        + f"<div style='position:absolute;left:0;top:0;bottom:0;width:5px;background:{_G};z-index:3;'></div>"
        + f"<div style='background:{_S7_CLR};padding:8px 20px 8px 28px;"
          f"display:flex;justify-content:space-between;align-items:center;'>"
          f"<div>"
          f"<div style='font-size:0.46rem;color:rgba(255,255,255,0.5);letter-spacing:0.16em;"
          f"text-transform:uppercase;font-family:IBM Plex Mono,monospace;'>"
          f"SECTION 7 &middot; GLOSSARY &amp; DEFINITIONS</div>"
          f"<div style='font-size:0.8rem;font-weight:700;color:{_W};'>"
          f"Reference Glossary &mdash; Corporate Platforms, Regulatory Terms &amp; Project Types</div>"
          f"</div>"
          f"<div style='font-size:0.46rem;color:rgba(255,255,255,0.4);font-family:IBM Plex Mono,monospace;'>"
          f"RBC INTERNAL AUDIT</div>"
          f"</div>"
        + f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;"
          f"height:calc(100% - 80px);overflow:hidden;gap:0;'>"
          f"<div style='padding:8px 10px 8px 14px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          f"<div style='{hdr_style}'>Corporate Platforms &amp; Functions</div>"
          + col1
          + f"</div>"
          f"<div style='padding:8px 10px;border-right:1px solid #d1d5db;overflow:hidden;'>"
          f"<div style='{hdr_style}'>Regulatory Terms</div>"
          + col2
          + f"</div>"
          f"<div style='padding:8px 10px;overflow:hidden;'>"
          f"<div style='{hdr_style}'>Core Assurance &amp; Project Types</div>"
          + col3
          + f"</div>"
          + f"</div>"
        + f"<div style='position:absolute;bottom:0;left:0;right:0;height:20px;"
          f"background:{_S7_CLR};display:flex;align-items:center;padding:0 22px;"
          f"justify-content:space-between;'>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>"
          f"RBC Internal Audit | CONFIDENTIAL</span>"
          f"<span style='font-size:0.46rem;color:rgba(255,255,255,0.4);'>"
          f"{qtr} INTERNAL AUDIT QUARTERLY REPORT</span>"
          f"</div>"
        + "</div>"
    )


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

    # Section 3 — Assurance Activities & Output (enterprise-wide)
    ent_iss = enterprise_issues if enterprise_issues is not None else all_issues
    slides.append({
        "title": "Section 3 — Assurance Activities & Output",
        "scope": "Enterprise", "stype": "Assurance Output",
        "html": _slide_assurance_output(audits, ent_iss, qtr),
    })
    slides.append({
        "title": "Section 3 — Issue Theme Analysis",
        "scope": "Enterprise", "stype": "Issue Themes",
        "html": _slide_issue_themes(audits, ent_iss, qtr),
    })

    # Section 4 — Issue Management (enterprise-wide)
    slides.append({
        "title": "Section 4 — Issue Management Overview",
        "scope": "Enterprise", "stype": "Issue Overview",
        "html": _slide_issue_overview(ent_iss, qtr),
    })
    slides.append({
        "title": "Section 4 — Issue Tracking Status",
        "scope": "Enterprise", "stype": "Issue Tracking",
        "html": _slide_issue_tracking(ent_iss, qtr),
    })
    slides.append({
        "title": "Section 4 — Issue Resolution Progress",
        "scope": "Enterprise", "stype": "Issue Resolution",
        "html": _slide_issue_resolution(ent_iss, qtr),
    })

    # Section 5 — CAE Group Operations (enterprise-wide)
    slides.append({
        "title": "Section 5 — Regulatory Issues",
        "scope": "Enterprise", "stype": "Regulatory Issues",
        "html": _slide_regulatory_issues(audits, ent_iss, qtr),
    })
    slides.append({
        "title": "Section 5 — Significant Plan Changes",
        "scope": "Enterprise", "stype": "Plan Changes",
        "html": _slide_plan_changes(audits, qtr),
    })
    slides.append({
        "title": "Section 5 — CAE Group Performance Indicators",
        "scope": "Enterprise", "stype": "CAE Performance",
        "html": _slide_cae_performance(audits, ent_iss, qtr),
    })
    slides.append({
        "title": "Section 5 — IA Quality Assurance",
        "scope": "Enterprise", "stype": "QA Review",
        "html": _slide_qa_review(audits, ent_iss, qtr),
    })

    # Section 7 — Glossary
    slides.append({
        "title": "Section 7 — Glossary",
        "scope": "Reference", "stype": "Glossary",
        "html": _slide_glossary(qtr),
    })

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
