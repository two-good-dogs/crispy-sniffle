from datetime import datetime

import pandas as pd
import streamlit as st

import data.data_interface as di


def _next_msg_id(messages: list) -> str:
    ids = [int(m["msg_id"].split("-")[1]) for m in messages
           if m.get("msg_id", "").startswith("MSG-")]
    return f"MSG-{max(ids) + 1:03d}" if ids else "MSG-001"


def _build_subject_options() -> dict:
    """Build audit+issue subject list from live data."""
    options = {}
    try:
        audits_df = di.get_audits()
        for _, row in audits_df.iterrows():
            label = f"[Audit] {row['audit_id']} · {row['audit_name']}"
            options[label] = ("project", row["audit_id"])
    except Exception:
        pass
    try:
        issues_df = di.get_issues()
        for _, row in issues_df.iterrows():
            label = f"[Issue] {row['issue_id']} · {row['title']}"
            options[label] = ("issue", row["issue_id"])
    except Exception:
        pass
    return options


def _sync_messages():
    """Load messages from DB into session state."""
    try:
        st.session_state["messages"] = di.get_messages_for_user(di.CURRENT_USER)
    except Exception:
        pass


def _render_messages_table(msgs: list, mark_read_key: str):
    if not msgs:
        st.info("No messages here yet.")
        return

    rows = [{
        "ID":        m["msg_id"],
        "From":      m["from_user"],
        "To":        m["to_user"],
        "Regarding": m["subject_label"],
        "Preview":   m["message"][:80] + ("…" if len(m["message"]) > 80 else ""),
        "Sent":      m["sent_at"],
        "Status":    "● Unread" if not m["read"] else "Read",
    } for m in msgs]

    def _style(val):
        if val == "● Unread":
            return "background:#dbeafe;color:#1e40af;border-radius:10px;padding:2px 10px;font-weight:700;"
        return "background:#f3f4f6;color:#9ca3af;border-radius:10px;padding:2px 10px;"

    styled = (
        pd.DataFrame(rows).style
        .applymap(_style, subset=["Status"])
        .set_properties(**{"font-size": "0.82rem"})
        .set_table_styles([{"selector": "th", "props": [
            ("font-size", "0.78rem"), ("color", "#6b7280"),
            ("font-weight", "600"), ("text-transform", "uppercase"),
            ("letter-spacing", "0.04em"),
        ]}])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    unread_ids = [m["msg_id"] for m in msgs
                  if not m["read"] and m["to_user"] == di.CURRENT_USER]
    if unread_ids and st.button(f"Mark all {len(unread_ids)} as read", key=mark_read_key):
        for m in st.session_state["messages"]:
            if m["msg_id"] in unread_ids:
                m["read"] = True
        st.rerun()


def render_compose_panel(snapshot_mode: bool):
    st.markdown("### New Message")
    if snapshot_mode:
        st.warning("Snapshot mode — messaging disabled.")
        return

    recipients = [u for u in di.USERS if u != di.CURRENT_USER]

    st.markdown(
        "<div style='font-size:0.8rem;font-weight:600;color:#374151;margin-bottom:4px;'>Regarding</div>",
        unsafe_allow_html=True,
    )
    subject_filter = st.radio(
        "subject_filter", ["All", "Audits only", "Issues only"],
        horizontal=True, key="notif_subject_filter", label_visibility="collapsed",
    )

    subject_options = _build_subject_options()
    if subject_filter == "Audits only":
        subject_options = {k: v for k, v in subject_options.items() if k.startswith("[Audit]")}
    elif subject_filter == "Issues only":
        subject_options = {k: v for k, v in subject_options.items() if k.startswith("[Issue]")}

    if st.session_state.get("notif_sent_confirmation"):
        st.success(st.session_state.pop("notif_sent_confirmation"))

    with st.form("compose_form"):
        to_user       = st.selectbox("To *", recipients, key="compose_to")
        subject_label = st.selectbox("Select Audit or Issue *",
                                     list(subject_options.keys()), key="compose_subject")
        body = st.text_area("Message *", placeholder="Type your message here…",
                            height=130, key="compose_body")
        send_btn = st.form_submit_button("Send Message →", type="primary",
                                         use_container_width=True)

        if send_btn:
            if not body.strip():
                st.error("Message body is required.")
            elif not subject_options:
                st.error("No subjects available.")
            else:
                _sub_type, _sub_id = subject_options.get(subject_label, ("project", ""))
                new_msg = {
                    "msg_id":        _next_msg_id(st.session_state.get("messages", [])),
                    "from_user":     di.CURRENT_USER,
                    "to_user":       to_user,
                    "subject_type":  _sub_type,
                    "subject_id":    _sub_id,
                    "subject_label": subject_label,
                    "message":       body,
                    "sent_at":       datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "read":          True,
                }
                # Append optimistically; also try DB write
                st.session_state["messages"].append(new_msg)
                try:
                    di.send_message_to_user(to_user, di.CURRENT_USER, subject_label, body)
                except Exception:
                    pass

                st.session_state["notif_sent_confirmation"] = (
                    f"Message {new_msg['msg_id']} sent to **{to_user}**. Check your Sent tab."
                )
                for k in ("compose_to", "compose_subject", "compose_body"):
                    st.session_state.pop(k, None)
                st.rerun()


def render_notifications(snapshot_mode: bool = False):
    _sync_messages()

    all_messages = st.session_state["messages"]
    my_inbox     = [m for m in all_messages if m["to_user"] == di.CURRENT_USER]
    my_sent      = [m for m in all_messages if m["from_user"] == di.CURRENT_USER]
    unread_count = sum(1 for m in my_inbox if not m["read"])

    hdr_left, hdr_right = st.columns([4, 1])
    with hdr_left:
        st.markdown("### Notifications & Messages")
        st.markdown(
            f"<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>"
            f"Inbox: <strong>{len(my_inbox)}</strong> &nbsp;·&nbsp; "
            f"Unread: <strong style='color:#dc2626;'>{unread_count}</strong></div>",
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

    compose_col, inbox_col = st.columns([1, 1.4])

    with compose_col:
        render_compose_panel(snapshot_mode)

    with inbox_col:
        msg_tabs = st.tabs([
            f"Inbox  ({len(my_inbox)})",
            f"Sent  ({len(my_sent)})",
            f"All  ({len(my_inbox) + len(my_sent)})",
        ])
        with msg_tabs[0]:
            if unread_count:
                st.markdown(
                    f"<div style='background:#fee2e2;border:1px solid #fca5a5;"
                    f"border-radius:6px;padding:8px 14px;font-size:0.82rem;"
                    f"color:#991b1b;margin-bottom:10px;'>"
                    f"🔔 You have <strong>{unread_count}</strong> unread message(s).</div>",
                    unsafe_allow_html=True,
                )
            _render_messages_table(my_inbox, "mark_read_inbox")
        with msg_tabs[1]:
            _render_messages_table(my_sent, "mark_read_sent")
        with msg_tabs[2]:
            combined = sorted(
                {m["msg_id"]: m for m in my_inbox + my_sent}.values(),
                key=lambda m: m["sent_at"], reverse=True,
            )
            _render_messages_table(list(combined), "mark_read_all")
