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
    "Owned Audit":  ("#ede9fe", "#5b21b6"),
    "Indirect":     ("#f0f9ff", "#0369a1"),
    "AE In-Scope":  ("#fff7ed", "#c2410c"),
    "":             ("#f3f4f6", "#9ca3af"),
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
    "report_rating":        "current_rating",
    "impacted_audit_group": "impacted_platform",
}

# ── Table header labels ────────────────────────────────────────────────────────
_HEADER_LABELS = {
    "audit_id":        "ID",
    "audit_name":      "Audit",
    "audit_type":      "Type",
    "lead_group":      "Lead Group",
    "region":          "Region",
    "status":          "Status",
    "rating":          "Rating",
    "current_rating":  "Curr. Rating",
    "previous_rating": "Prev. Rating",
    "rating_change":   "Rating Change",
    "issue_count":     "Issues",
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


def _rating_change_pill(val):
    v = str(val).strip()
    if v == "Improved":
        return (
            "<span style='display:inline-flex;align-items:center;gap:4px;padding:3px 10px;"
            "border-radius:999px;font-size:0.7rem;font-weight:600;"
            "background:#d1fae5;color:#065f46;white-space:nowrap;'>"
            "&#9650; Improved</span>"
        )
    if v == "Deteriorated":
        return (
            "<span style='display:inline-flex;align-items:center;gap:4px;padding:3px 10px;"
            "border-radius:999px;font-size:0.7rem;font-weight:600;"
            "background:#fee2e2;color:#991b1b;white-space:nowrap;'>"
            "&#9660; Deteriorated</span>"
        )
    if v == "No Change":
        return (
            "<span style='display:inline-flex;align-items:center;gap:4px;padding:3px 10px;"
            "border-radius:999px;font-size:0.7rem;font-weight:600;"
            "background:#f3f4f6;color:#6b7280;white-space:nowrap;'>"
            "&#9644; No Change</span>"
        )
    return "<span style='color:#d1d5db;font-weight:600;'>—</span>"


def _issue_badge(count, audit_id=""):
    n = int(count) if not pd.isna(count) else 0
    if n == 0:
        return "<span style='color:#d1d5db;font-weight:600;'>—</span>"
    return (
        f"<span data-audit-id='{audit_id}' onclick='openIssuePopup(\"{audit_id}\")' "
        f"style='display:inline-block;padding:3px 10px;border-radius:999px;"
        f"font-size:0.72rem;font-weight:700;background:#fee2e2;color:#dc2626;"
        f"white-space:nowrap;line-height:1.5;cursor:pointer;"
        f"border:1.5px solid transparent;"
        f"transition:all .15s ease;'"
        f"onmouseenter=\"this.style.background='#dc2626';this.style.color='#fff';this.style.borderColor='#b91c1c';\""
        f"onmouseleave=\"this.style.background='#fee2e2';this.style.color='#dc2626';this.style.borderColor='transparent';\""
        f">{n}</span>"
    )


# ── Issue popup modal ──────────────────────────────────────────────────────────

def _build_issue_modal_js(issues_df: pd.DataFrame, audit_name_map: dict) -> str:
    """
    Return a <script>+<div> block embedding all issue data and the modal UI.
    The modal is triggered by openIssuePopup(auditId) called from badge onclick.
    """
    import json as _json

    # Build a dict: audit_id → list of issue dicts
    issues_by_audit: dict = {}
    if issues_df is not None and not issues_df.empty:
        for row in issues_df.to_dict("records"):
            aid = str(row.get("audit_id", ""))
            if not aid:
                continue
            due = row.get("due_date")
            due_str = due.strftime("%d %b %Y") if pd.notna(due) else "—"
            days_ov = int(row.get("days_overdue") or 0)
            issues_by_audit.setdefault(aid, []).append({
                "id":    str(row.get("issue_id", "—")),
                "title": str(row.get("title", "Untitled")),
                "sev":   str(row.get("severity", "—")),
                "stat":  str(row.get("status", "—")),
                "due":   due_str,
                "owner": str(row.get("remediation_owner", "—")),
                "days":  days_ov,
            })

    data_json = _json.dumps(issues_by_audit)
    names_json = _json.dumps(audit_name_map)

    # Derive sev colours from the existing module-level constant
    sev_colors = _json.dumps({
        k: {"bg": v[0], "color": v[1]}
        for k, v in _RATING_CFG.items()
        if k != "N/A"
    })
    stat_colors = _json.dumps({
        "Open":    {"bg": "#dbeafe", "color": "#1e40af"},
        "Overdue": {"bg": "#fee2e2", "color": "#991b1b"},
        "Closed":  {"bg": "#f3f4f6", "color": "#6b7280"},
    })

    return f"""
<!-- Issue popup overlay -->
<!-- pointer-events:none keeps it from capturing scroll/clicks while hidden -->
<div id="iq-issue-overlay" onclick="if(event.target===this)closeIssuePopup()"
  style="display:none;pointer-events:none;position:fixed;inset:0;
  background:rgba(15,23,42,0.55);z-index:99999;
  align-items:center;justify-content:center;padding:20px;box-sizing:border-box;">
  <div id="iq-issue-modal"
    style="background:#ffffff;border-radius:16px;width:100%;max-width:780px;
    max-height:85vh;display:flex;flex-direction:column;
    box-shadow:0 25px 60px rgba(0,0,0,0.22),0 0 0 1px rgba(0,0,0,0.06);
    overflow:hidden;animation:iqModalIn .22s cubic-bezier(.22,1,.36,1);">
    <!-- Header -->
    <div id="iq-modal-header"
      style="padding:20px 24px 16px;border-bottom:1px solid #f3f4f6;flex-shrink:0;
      background:linear-gradient(135deg,#fafafa 0%,#fff 100%);">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.55rem;font-weight:700;
            letter-spacing:0.14em;text-transform:uppercase;color:#9ca3af;margin-bottom:4px;">
            ISSUES &mdash; AUDIT DETAIL
          </div>
          <div id="iq-modal-title"
            style="font-family:'Barlow Condensed',sans-serif;font-size:1.35rem;font-weight:700;
            color:#111827;line-height:1.2;max-width:580px;"></div>
          <div id="iq-modal-audit-id"
            style="font-family:'IBM Plex Mono',monospace;font-size:0.64rem;color:#9ca3af;margin-top:4px;"></div>
        </div>
        <button onclick="closeIssuePopup()"
          style="flex-shrink:0;border:none;background:#f3f4f6;border-radius:8px;
          width:32px;height:32px;cursor:pointer;font-size:1rem;color:#6b7280;
          display:flex;align-items:center;justify-content:center;
          transition:background .15s,color .15s;"
          onmouseenter="this.style.background='#e5e7eb';this.style.color='#374151';"
          onmouseleave="this.style.background='#f3f4f6';this.style.color='#6b7280';">&#10005;</button>
      </div>
      <div id="iq-modal-stats" style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;"></div>
    </div>
    <!-- Body / table -->
    <div style="overflow-y:auto;flex:1;padding:0;">
      <table id="iq-issues-table"
        style="width:100%;border-collapse:collapse;font-size:0.8rem;">
        <thead>
          <tr style="position:sticky;top:0;z-index:1;">
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Issue ID</th>
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;">Title</th>
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Severity</th>
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Status</th>
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Due Date</th>
            <th style="padding:10px 16px;text-align:left;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Owner</th>
            <th style="padding:10px 16px;text-align:right;background:#f9fafb;
              font-family:'IBM Plex Mono',monospace;font-size:0.56rem;font-weight:600;
              letter-spacing:0.08em;text-transform:uppercase;color:#9ca3af;
              border-bottom:1px solid #e5e7eb;white-space:nowrap;">Days Overdue</th>
          </tr>
        </thead>
        <tbody id="iq-issues-tbody"></tbody>
      </table>
      <div id="iq-no-issues"
        style="display:none;padding:48px 24px;text-align:center;
        color:#9ca3af;font-size:0.85rem;">
        No issues found for this audit.
      </div>
    </div>
    <!-- Footer -->
    <div style="padding:14px 24px;border-top:1px solid #f3f4f6;flex-shrink:0;
      background:#fafafa;display:flex;align-items:center;justify-content:flex-end;">
      <button onclick="closeIssuePopup()"
        style="border:1px solid #e5e7eb;background:#fff;border-radius:8px;
        padding:8px 20px;font-size:0.8rem;font-weight:600;color:#374151;
        cursor:pointer;font-family:'IBM Plex Mono',monospace;
        letter-spacing:0.04em;transition:background .15s,border-color .15s;"
        onmouseenter="this.style.background='#f3f4f6';this.style.borderColor='#d1d5db';"
        onmouseleave="this.style.background='#fff';this.style.borderColor='#e5e7eb';">
        Close
      </button>
    </div>
  </div>
</div>

<style>
@keyframes iqModalIn {{
  from {{ opacity:0; transform:scale(0.96) translateY(8px); }}
  to   {{ opacity:1; transform:scale(1)    translateY(0);    }}
}}
</style>

<script>
(function(){{
  var _data  = {data_json};
  var _names = {names_json};
  var _sev   = {sev_colors};
  var _stat  = {stat_colors};

  function pill(text, cfg, extra) {{
    var bg    = (cfg && cfg.bg)    || '#f3f4f6';
    var color = (cfg && cfg.color) || '#374151';
    return '<span style="display:inline-block;padding:2px 9px;border-radius:999px;'
      + 'font-size:0.7rem;font-weight:600;background:' + bg + ';color:' + color + ';'
      + 'white-space:nowrap;line-height:1.5;' + (extra||'') + '">' + text + '</span>';
  }}

  window.openIssuePopup = function(auditId) {{
    var overlay = document.getElementById('iq-issue-overlay');
    var tbody   = document.getElementById('iq-issues-tbody');
    var noIss   = document.getElementById('iq-no-issues');
    var title   = document.getElementById('iq-modal-title');
    var idEl    = document.getElementById('iq-modal-audit-id');
    var stats   = document.getElementById('iq-modal-stats');
    var table   = document.getElementById('iq-issues-table');

    var issues  = _data[auditId] || [];
    var name    = _names[auditId] || auditId;

    title.textContent = name;
    idEl.textContent  = auditId;

    // Stats chips
    var open=0, overdue=0, high=0;
    issues.forEach(function(i){{
      if(i.stat==='Open'||i.stat==='Overdue') open++;
      if(i.stat==='Overdue') overdue++;
      if(i.sev==='High') high++;
    }});

    var statChips = [
      pill(issues.length + ' Total', {{bg:'#f3f4f6',color:'#374151'}}, 'font-family:IBM Plex Mono,monospace;font-size:0.66rem;'),
      open    ? pill(open + ' Open',    {{bg:'#dbeafe',color:'#1e40af'}}, 'font-family:IBM Plex Mono,monospace;font-size:0.66rem;') : '',
      overdue ? pill(overdue + ' Overdue', {{bg:'#fee2e2',color:'#991b1b'}}, 'font-family:IBM Plex Mono,monospace;font-size:0.66rem;font-weight:700;') : '',
      high    ? pill(high + ' High Sev', {{bg:'#fef3c7',color:'#92400e'}}, 'font-family:IBM Plex Mono,monospace;font-size:0.66rem;') : '',
    ].filter(Boolean).join('<span style="color:#e5e7eb;margin:0 2px;">·</span>');
    stats.innerHTML = '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">' + statChips + '</div>';

    // Table rows
    tbody.innerHTML = '';
    if(issues.length === 0) {{
      noIss.style.display  = 'block';
      table.style.display  = 'none';
    }} else {{
      noIss.style.display  = 'none';
      table.style.display  = '';
      issues.forEach(function(iss, idx){{
        var bg = idx % 2 === 0 ? '#ffffff' : '#fafafa';
        var tr = document.createElement('tr');
        tr.style.cssText = 'background:' + bg + ';transition:background .1s;';
        tr.onmouseenter  = function(){{ this.style.background='#eff6ff'; }};
        tr.onmouseleave  = function(){{ this.style.background=bg; }};

        var daysCell = iss.days > 0
          ? '<span style="font-weight:700;color:#dc2626;font-family:IBM Plex Mono,monospace;">' + iss.days + 'd</span>'
          : '<span style="color:#d1d5db;">—</span>';

        tr.innerHTML =
          '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;white-space:nowrap;">'
          + '<span style="font-family:IBM Plex Mono,monospace;font-size:0.66rem;color:#9ca3af;">' + iss.id + '</span></td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;max-width:260px;">'
          + '<span style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
          + 'font-size:0.8rem;font-weight:500;color:#111827;" title="' + iss.title.replace(/"/g,'&quot;') + '">' + iss.title + '</span></td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;white-space:nowrap;">' + pill(iss.sev, _sev[iss.sev]) + '</td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;white-space:nowrap;">' + pill(iss.stat, _stat[iss.stat]) + '</td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;white-space:nowrap;font-size:0.78rem;color:#374151;">' + iss.due + '</td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;font-size:0.78rem;color:#374151;">' + iss.owner + '</td>'
          + '<td style="padding:9px 16px;border-bottom:1px solid #f3f4f6;text-align:right;white-space:nowrap;">' + daysCell + '</td>';
        tbody.appendChild(tr);
      }});
    }}

    overlay.style.display       = 'flex';
    overlay.style.pointerEvents = 'auto';
    overlay.style.backdropFilter = 'blur(3px)';
    document.body.style.overflow = 'hidden';
    // Use a stable global reference so removeEventListener works across reruns
    document.removeEventListener('keydown', window._iqEscHandler);
    window._iqEscHandler = function(e) {{ if(e.key==='Escape') window.closeIssuePopup(); }};
    document.addEventListener('keydown', window._iqEscHandler);
  }};

  window.closeIssuePopup = function() {{
    var overlay = document.getElementById('iq-issue-overlay');
    if(overlay) {{
      overlay.style.display        = 'none';
      overlay.style.pointerEvents  = 'none';
      overlay.style.backdropFilter = '';
    }}
    document.body.style.overflow = '';
    document.removeEventListener('keydown', window._iqEscHandler);
  }};

  // Clean up on Streamlit reruns so stale listeners don't accumulate
  if(window._iqEscHandler) {{
    document.removeEventListener('keydown', window._iqEscHandler);
  }}
}})();
</script>
"""


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
        bg           = "#ffffff" if i % 2 == 0 else "#fafafa"
        td           = _TD_BASE + f"background:{bg};"
        audit_id_val = str(row.get("audit_id", ""))
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
                    f"<td style='{td}max-width:140px;'><span style='font-size:0.78rem;"
                    f"font-weight:500;color:#374151;display:block;overflow:hidden;"
                    f"text-overflow:ellipsis;' title='{val}'>{val}</span></td>"
                )
            elif col == "region":
                cell = f"<td style='{td}'>{_region_pills(val)}</td>"
            elif col == "status":
                cell = f"<td style='{td}'>{_status_pill(str(val))}</td>"
            elif col in ("rating", "current_rating", "previous_rating"):
                cell = f"<td style='{td}'>{_rating_pill(str(val))}</td>"
            elif col == "rating_change":
                cell = f"<td style='{td}'>{_rating_change_pill(val)}</td>"
            elif col == "issue_count":
                cell = f"<td style='{td}text-align:center;'>{_issue_badge(val, audit_id=audit_id_val)}</td>"
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

def _filter_audits(df, search="", regions=None, statuses=None, audit_types=None, ae_in_scope=False):
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
    if ae_in_scope and "ae_in_scope" in df.columns:
        df = df[df["ae_in_scope"] == True]
    return df


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_portfolio_overview(audits_df: pd.DataFrame, issues_df: pd.DataFrame = None, snapshot_mode: bool = False):

    owned_count        = (audits_df["audit_type"] == "Owned Audit").sum()
    indirect_count     = (audits_df["audit_type"] == "Indirect").sum()
    ae_scope_count     = int(audits_df["ae_in_scope"].sum()) if "ae_in_scope" in audits_df.columns else 0
    total_count        = len(audits_df)
    out_of_scope_count = int(audits_df["out_of_scope"].sum())

    # Open issue count comes from the issues DataFrame filtered by owner_platform
    if issues_df is not None and not issues_df.empty and "status" in issues_df.columns:
        _open_iss   = issues_df[issues_df["status"].isin(["Open", "Overdue"])]
        all_issues  = len(_open_iss)
        past_due_count = int((issues_df["status"] == "Overdue").sum())
    else:
        all_issues     = int(audits_df["issue_count"].sum())
        past_due_count = int(audits_df["is_overdue"].sum())

    # ── Framework note ────────────────────────────────────────────────────────
    owned_chip    = _chip("OWNED",       "#ede9fe", "#5b21b6", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    indirect_chip = _chip("INDIRECT",    "#f0f9ff", "#0369a1", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    ae_chip       = _chip("AE IN-SCOPE", "#fff7ed", "#c2410c", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
    issues_chip   = _chip("ISSUES",      "#fee2e2", "#991b1b", radius="4px", size="0.65rem", fw="700", pad="2px 8px")
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
        + f'<span style="font-size:0.76rem;color:#374151;">{ae_chip}&nbsp;Platform in AE Platforms field</span>'
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
        '<div style="display:flex;gap:12px;margin-bottom:4px;">'
        + _card_html("Owned Coverage", owned_count, "OWNED", "#d1fae5", "#065f46", "#059669",
                     "Lead Audit Group field", "0s")
        + _card_html("Indirect Coverage", indirect_count, "INDIRECT", "#dbeafe", "#1e40af", "#2563eb",
                     "Impacted Platform field", ".07s")
        + _card_html("AE In-Scope", ae_scope_count, "AE IN-SCOPE", "#fff7ed", "#c2410c", "#ea580c",
                     "AE Platforms field", ".14s")
        + _card_html("Total Footprint", total_count, "DE-DUPLICATED", "#fef3c7", "#92400e", "#d97706",
                     f'Owned&nbsp;<strong style="color:#374151;">{owned_count}</strong>'
                     f'&ensp;·&ensp;Indirect&nbsp;<strong style="color:#374151;">{indirect_count}</strong>'
                     f'&ensp;·&ensp;AE&nbsp;<strong style="color:#374151;">{ae_scope_count}</strong>',
                     ".21s")
        + _card_html("Open Issues", all_issues, "ISSUES", "#fee2e2", "#991b1b", "#dc2626",
                     f'Issue Owner Platform field<br>'
                     f'Past Due&nbsp;<strong style="color:#dc2626;">{past_due_count}</strong>'
                     f'&ensp;·&ensp;Out-of-scope&nbsp;<strong style="color:#374151;">{out_of_scope_count}</strong>',
                     ".28s")
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

    filtered    = _filter_audits(audits_df, search=search,
                                 regions=region_filter or None,
                                 statuses=status_filter or None)
    owned_f     = _filter_audits(filtered, audit_types=["Owned Audit"])
    indirect_f  = _filter_audits(filtered, audit_types=["Indirect"])
    ae_scope_f  = _filter_audits(filtered, ae_in_scope=True)

    st.markdown(
        f"<div style='font-size:0.88rem;font-weight:600;color:#1a1f2e;margin:8px 0 4px;'>"
        f"All Audits — <span style='color:#6b7280;font-weight:400;'>{len(filtered)} total</span></div>",
        unsafe_allow_html=True,
    )

    # Inject the issue popup modal once — shared by all four sub-tab tables.
    # audit_name_map covers the full (pre-local-filter) set so any badge click resolves.
    _audit_name_map = dict(zip(
        audits_df["audit_id"].astype(str), audits_df["audit_name"].astype(str)
    )) if "audit_id" in audits_df.columns and "audit_name" in audits_df.columns else {}
    st.markdown(_build_issue_modal_js(issues_df, _audit_name_map), unsafe_allow_html=True)

    sub_tabs = st.tabs([
        f"All Audits  {len(filtered)}",
        f"Owned Audits  {len(owned_f)}",
        f"Indirect Coverage  {len(indirect_f)}",
        f"AE In-Scope  {len(ae_scope_f)}",
    ])

    with sub_tabs[0]:
        _render_audit_table(filtered)
    with sub_tabs[1]:
        _render_audit_table(owned_f)
    with sub_tabs[2]:
        _render_audit_table(indirect_f)
    with sub_tabs[3]:
        _render_audit_table(ae_scope_f)
