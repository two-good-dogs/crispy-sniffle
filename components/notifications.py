from datetime import datetime

import pandas as pd
import streamlit as st

from data.mock_data import get_audits, get_issues, get_users, get_seed_messages, CURRENT_USER


# ── Compose form ──────────────────────────────────────────────────────────────

def _next_msg_id(messages: list) -> str:
    if not messages:
        return "MSG-001"
    ids = [int(m["msg_id"].split("-")[1]) for m in messages if m.get("msg_id", "").startswith("MSG-")]
    return f"MSG-{max(ids) + 1:03d}"


def render_compose_panel(snapshot_mode: bool):
    st.markdown("### New Message")

    users = get_users()
    recipients = [u["name"] for u in users if u["name"] != CURRENT_USER]

    audits_df = get_audits()
    issues_df = get_issues()

    audit_options = {
        f"{row['audit_id']} · {row['audit_name']}": ("project", row["audit_id"])
        for _, row in audits_df.iterrows()
    }
    issue_options = {
        f"{row['issue_id']} · {row['title']}": ("issue", row["issue_id"])
        for _, row in issues_df.iterrows()
    }

    with st.form("compose_form", clear_on_submit=True):
        to_user = st.selectbox(
            "To *",
            recipients,
            key="compose_to",
            disabled=snapshot_mode,
        )

        subject_type = st.radio(
            "Regarding",
            ["Project / Audit", "Issue"],
            horizontal=True,
            key="compose_subject_type",
            disabled=snapshot_mode,
        )

        if subject_type == "Project / Audit":
            subject_label_key = st.selectbox(
                "Select Audit *",
                list(audit_options.keys()),
                key="compose_audit_select",
                disabled=snapshot_mode,
            )
            _sub_type, _sub_id = audit_options.get(subject_label_key, ("project", ""))
            _sub_label = subject_label_key
        else:
            subject_label_key = st.selectbox(
                "Select Issue *",
                list(issue_options.keys()),
                key="compose_issue_select",
                disabled=snapshot_mode,
            )
            _sub_type, _sub_id = issue_options.get(subject_label_key, ("issue", ""))
            _sub_label = subject_label_key

        body = st.text_area(
            "Message *",
            placeholder="Type your message here…",
            height=140,
            key="compose_body",
            disabled=snapshot_mode,
        )

        send_btn = st.form_submit_button(
            "Send Message →",
            type="primary",
            use_container_width=True,
            disabled=snapshot_mode,
        )

        if send_btn and not snapshot_mode:
            if not body.strip():
                st.error("Message body is required.")
            else:
                new_msg = {
                    "msg_id": _next_msg_id(st.session_state.messages),
                    "from_user": CURRENT_USER,
                    "to_user": to_user,
                    "subject_type": _sub_type,
                    "subject_id": _sub_id,
                    "subject_label": _sub_label,
                    "message": body,
                    "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "read": True,  # sender has already "read" their own sent message
                }
                st.session_state.messages.append(new_msg)
                st.success(
                    f"Message {new_msg['msg_id']} sent to **{to_user}**. "
                    "They will see it in their Notifications tab."
                )


# ── Message table helpers ─────────────────────────────────────────────────────

def _render_messages_table(msgs: list, mark_read_key: str):
    if not msgs:
        st.info("No messages here yet.")
        return

    df = pd.DataFrame(msgs)
    display_df = df[["msg_id", "from_user", "to_user", "subject_label", "message", "sent_at", "read"]].copy()
    display_df["message"] = display_df["message"].str[:80] + "…"
    display_df["read"] = display_df["read"].map({True: "Read", False: "● Unread"})
    display_df.columns = ["ID", "From", "To", "Regarding", "Preview", "Sent", "Status"]

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
        if st.button(
            f"Mark all {len(unread_ids)} as read",
            key=mark_read_key,
            type="secondary",
        ):
            for msg in st.session_state.messages:
                if msg["msg_id"] in unread_ids:
                    msg["read"] = True
            st.rerun()


# ── Main render ───────────────────────────────────────────────────────────────

def render_notifications(snapshot_mode: bool = False):
    if "messages" not in st.session_state:
        st.session_state.messages = get_seed_messages()

    all_messages = st.session_state.messages

    my_inbox = [m for m in all_messages if m["to_user"] == CURRENT_USER]
    my_sent  = [m for m in all_messages if m["from_user"] == CURRENT_USER]
    unread_count = sum(1 for m in my_inbox if not m["read"])

    # ── Page header ───────────────────────────────────────────────────────────
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Notifications & Messages")
        st.markdown(
            f"<div style='font-size:0.82rem;color:#6b7280;margin-bottom:12px;'>"
            f"Messages are private — you see only messages you sent or received. "
            f"Inbox: <strong>{len(my_inbox)}</strong> · "
            f"Unread: <strong style='color:#dc2626;'>{unread_count}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with h2:
        if unread_count:
            st.markdown(
                f"<div style='background:#dc2626;color:#fff;border-radius:20px;"
                f"padding:4px 16px;font-weight:700;font-size:1rem;text-align:center;margin-top:8px;'>"
                f"🔔 {unread_count} unread</div>",
                unsafe_allow_html=True,
            )

    # ── Two-column layout: compose | message tabs ─────────────────────────────
    left, right = st.columns([1, 1.4])

    with left:
        render_compose_panel(snapshot_mode)

    with right:
        inbox_label = f"Inbox  ({len(my_inbox)})"
        sent_label  = f"Sent  ({len(my_sent)})"
        all_label   = f"All  ({len(my_inbox) + len(my_sent)})"

        msg_tabs = st.tabs([inbox_label, sent_label, all_label])

        with msg_tabs[0]:
            if unread_count:
                st.markdown(
                    f"<div style='background:#fee2e2;border:1px solid #fca5a5;"
                    f"border-radius:6px;padding:8px 14px;font-size:0.82rem;color:#991b1b;"
                    f"margin-bottom:10px;'>"
                    f"🔔 You have <strong>{unread_count}</strong> unread message(s)."
                    f"</div>",
                    unsafe_allow_html=True,
                )
            _render_messages_table(my_inbox, mark_read_key="mark_read_inbox")

        with msg_tabs[1]:
            _render_messages_table(my_sent, mark_read_key="mark_read_sent")

        with msg_tabs[2]:
            combined = sorted(
                my_inbox + [m for m in my_sent if m not in my_inbox],
                key=lambda m: m["sent_at"],
                reverse=True,
            )
            _render_messages_table(combined, mark_read_key="mark_read_all")
