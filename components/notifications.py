from datetime import datetime

import pandas as pd
import streamlit as st

from data.mock_data import get_audits, get_issues, get_users, get_seed_messages, CURRENT_USER


# ── Helpers ───────────────────────────────────────────────────────────────────

def _next_msg_id(messages: list) -> str:
    if not messages:
        return "MSG-001"
    ids = [int(m["msg_id"].split("-")[1]) for m in messages if m.get("msg_id", "").startswith("MSG-")]
    return f"MSG-{max(ids) + 1:03d}"


def _build_subject_options() -> dict:
    """Returns a combined dict of all selectable subjects keyed by display label."""
    audits_df = get_audits()
    issues_df = get_issues()
    options = {}
    for _, row in audits_df.iterrows():
        label = f"[Audit] {row['audit_id']} · {row['audit_name']}"
        options[label] = ("project", row["audit_id"])
    for _, row in issues_df.iterrows():
        label = f"[Issue] {row['issue_id']} · {row['title']}"
        options[label] = ("issue", row["issue_id"])
    return options


# ── Compose panel ─────────────────────────────────────────────────────────────

def render_compose_panel(snapshot_mode: bool):
    st.markdown("### New Message")
    if snapshot_mode:
        st.warning("Snapshot mode — messaging disabled.")
        return

    users = get_users()
    recipients = [u["name"] for u in users if u["name"] != CURRENT_USER]

    # ── Subject filter sits OUTSIDE the form so radio triggers a rerun ────────
    st.markdown(
        "<div style='font-size:0.8rem;font-weight:600;color:#374151;margin-bottom:4px;'>Regarding</div>",
        unsafe_allow_html=True,
    )
    subject_filter = st.radio(
        "subject_filter",
        ["All", "Audits only", "Issues only"],
        horizontal=True,
        key="notif_subject_filter",
        label_visibility="collapsed",
    )

    subject_options = _build_subject_options()
    if subject_filter == "Audits only":
        subject_options = {k: v for k, v in subject_options.items() if k.startswith("[Audit]")}
    elif subject_filter == "Issues only":
        subject_options = {k: v for k, v in subject_options.items() if k.startswith("[Issue]")}

    # ── Show post-send confirmation (set in previous run) ────────────────────
    if st.session_state.get("notif_sent_confirmation"):
        st.success(st.session_state.notif_sent_confirmation)
        del st.session_state["notif_sent_confirmation"]

    # ── The form itself has no conditional widgets ────────────────────────────
    with st.form("compose_form"):
        to_user = st.selectbox("To *", recipients, key="compose_to")

        subject_label_key = st.selectbox(
            "Select Audit or Issue *",
            list(subject_options.keys()),
            key="compose_subject",
        )

        body = st.text_area(
            "Message *",
            placeholder="Type your message here…",
            height=130,
            key="compose_body",
        )

        send_btn = st.form_submit_button(
            "Send Message →",
            type="primary",
            use_container_width=True,
        )

        if send_btn:
            if not body.strip():
                st.error("Message body is required.")
            elif not subject_options:
                st.error("No subjects available with current filter.")
            else:
                _sub_type, _sub_id = subject_options.get(subject_label_key, ("project", ""))
                new_msg = {
                    "msg_id": _next_msg_id(st.session_state.messages),
                    "from_user": CURRENT_USER,
                    "to_user": to_user,
                    "subject_type": _sub_type,
                    "subject_id": _sub_id,
                    "subject_label": subject_label_key,
                    "message": body,
                    "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "read": True,
                }
                st.session_state.messages.append(new_msg)
                # Store confirmation text and clear form widget values before rerun
                st.session_state["notif_sent_confirmation"] = (
                    f"Message {new_msg['msg_id']} sent to **{to_user}**. "
                    "Check your Sent tab."
                )
                # Clear the form inputs by deleting their keys from session state
                for k in ("compose_to", "compose_subject", "compose_body"):
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()


# ── Message tables ────────────────────────────────────────────────────────────

def _render_messages_table(msgs: list, mark_read_key: str):
    if not msgs:
        st.info("No messages here yet.")
        return

    rows = []
    for m in msgs:
        rows.append({
            "ID":        m["msg_id"],
            "From":      m["from_user"],
            "To":        m["to_user"],
            "Regarding": m["subject_label"],
            "Preview":   m["message"][:80] + ("…" if len(m["message"]) > 80 else ""),
            "Sent":      m["sent_at"],
            "Status":    "● Unread" if not m["read"] else "Read",
        })

    display_df = pd.DataFrame(rows)

    def style_status(val):
        if val == "● Unread":
            return "background:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 10px;font-weight:700;"
        return "background:#f3f4f6;color:#9ca3af;border-radius:10px;padding:2px 10px;"

    styled = (
        display_df.style
        .applymap(style_status, subset=["Status"])
        .set_properties(**{"font-size": "0.82rem"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("font-size", "0.78rem"), ("color", "#6b7280"),
                ("font-weight", "600"), ("text-transform", "uppercase"),
                ("letter-spacing", "0.04em"),
            ]},
        ])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    unread_ids = [m["msg_id"] for m in msgs if not m["read"] and m["to_user"] == CURRENT_USER]
    if unread_ids:
        if st.button(f"Mark all {len(unread_ids)} as read", key=mark_read_key):
            for msg in st.session_state.messages:
                if msg["msg_id"] in unread_ids:
                    msg["read"] = True
            st.rerun()


# ── Main render ───────────────────────────────────────────────────────────────

def render_notifications(snapshot_mode: bool = False):
    if "messages" not in st.session_state:
        st.session_state.messages = get_seed_messages()

    all_messages = st.session_state.messages
    my_inbox  = [m for m in all_messages if m["to_user"] == CURRENT_USER]
    my_sent   = [m for m in all_messages if m["from_user"] == CURRENT_USER]
    unread_count = sum(1 for m in my_inbox if not m["read"])

    # ── Page header ───────────────────────────────────────────────────────────
    hdr_left, hdr_right = st.columns([4, 1])
    with hdr_left:
        st.markdown("### Notifications & Messages")
        st.markdown(
            f"<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>"
            f"You see only messages you sent or received. &nbsp;"
            f"Inbox: <strong>{len(my_inbox)}</strong> &nbsp;·&nbsp; "
            f"Unread: <strong style='color:#dc2626;'>{unread_count}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with hdr_right:
        if unread_count:
            st.markdown(
                f"<div style='background:#dc2626;color:#fff;border-radius:20px;"
                f"padding:4px 16px;font-weight:700;text-align:center;margin-top:8px;'>"
                f"🔔 {unread_count} unread</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Two-column layout ─────────────────────────────────────────────────────
    compose_col, inbox_col = st.columns([1, 1.4])

    with compose_col:
        render_compose_panel(snapshot_mode)

    with inbox_col:
        inbox_label = f"Inbox  ({len(my_inbox)})"
        sent_label  = f"Sent  ({len(my_sent)})"
        all_label   = f"All  ({len(my_inbox) + len(my_sent)})"

        msg_tabs = st.tabs([inbox_label, sent_label, all_label])

        with msg_tabs[0]:
            if unread_count:
                st.markdown(
                    f"<div style='background:#fee2e2;border:1px solid #fca5a5;"
                    f"border-radius:6px;padding:8px 14px;font-size:0.82rem;"
                    f"color:#991b1b;margin-bottom:10px;'>"
                    f"🔔 You have <strong>{unread_count}</strong> unread message(s).</div>",
                    unsafe_allow_html=True,
                )
            _render_messages_table(my_inbox, mark_read_key="mark_read_inbox")

        with msg_tabs[1]:
            _render_messages_table(my_sent, mark_read_key="mark_read_sent")

        with msg_tabs[2]:
            combined = sorted(
                {m["msg_id"]: m for m in my_inbox + my_sent}.values(),
                key=lambda m: m["sent_at"],
                reverse=True,
            )
            _render_messages_table(list(combined), mark_read_key="mark_read_all")
