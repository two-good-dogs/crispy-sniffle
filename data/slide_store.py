"""
slide_store.py — Persistence layer for slide commentary, comments, and custom slides.

Storage: JSON file (data/slide_data.json).  On SQL-Server environments this
would be replaced by a DB-backed implementation — the public API is identical.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from typing import Optional

_STORE = os.path.join(os.path.dirname(__file__), "slide_data.json")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load() -> dict:
    if os.path.exists(_STORE):
        try:
            with open(_STORE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            pass
    return {"version": 1, "slides": {}, "custom_slides": []}


def _save(data: dict) -> None:
    with open(_STORE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


def _slide_key(title: str, scope: str) -> str:
    """Stable 12-char hex key derived from title + scope."""
    return hashlib.md5(f"{title}::{scope}".encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _comment_id(user: str, text: str) -> str:
    return hashlib.md5(f"{user}{text}{_now()}".encode()).hexdigest()[:8]


# ── Commentary ────────────────────────────────────────────────────────────────

def get_commentary(title: str, scope: str) -> str:
    """Return the saved commentary string for this slide (empty string if none)."""
    key = _slide_key(title, scope)
    return _load()["slides"].get(key, {}).get("commentary", "")


def save_commentary(title: str, scope: str, text: str, user: str) -> None:
    """Overwrite the commentary for a slide and record who edited it."""
    key = _slide_key(title, scope)
    data = _load()
    data["slides"].setdefault(key, {"commentary": "", "comments": []})
    data["slides"][key]["commentary"] = text
    data["slides"][key]["commentary_by"] = user
    data["slides"][key]["commentary_at"] = _now()
    _save(data)


# ── Comments ──────────────────────────────────────────────────────────────────

def get_comments(title: str, scope: str) -> list[dict]:
    """Return the comment thread for this slide (newest-last)."""
    key = _slide_key(title, scope)
    return _load()["slides"].get(key, {}).get("comments", [])


def add_comment(title: str, scope: str, user: str, text: str,
                tagged_users: Optional[list[str]] = None) -> dict:
    """Append a top-level comment and return the new comment dict."""
    key = _slide_key(title, scope)
    data = _load()
    data["slides"].setdefault(key, {"commentary": "", "comments": []})

    # Also pick up any @Name patterns from the text body
    at_mentions = re.findall(r"@([\w][^\s@,]*(?:\s[\w][^\s@,]*)?)", text)
    all_tagged = list({*(tagged_users or []), *at_mentions})

    comment: dict = {
        "id":           _comment_id(user, text),
        "user":         user,
        "text":         text,
        "tagged_users": all_tagged,
        "timestamp":    _now(),
        "replies":      [],
    }
    data["slides"][key]["comments"].append(comment)
    _save(data)
    return comment


def add_reply(title: str, scope: str, comment_id: str,
              user: str, text: str) -> Optional[dict]:
    """Append a reply to an existing comment. Returns reply dict or None."""
    key = _slide_key(title, scope)
    data = _load()
    slide_data = data["slides"].get(key, {})
    for comment in slide_data.get("comments", []):
        if comment["id"] == comment_id:
            at_mentions = re.findall(r"@([\w][^\s@,]*(?:\s[\w][^\s@,]*)?)", text)
            reply: dict = {
                "id":           _comment_id(user, text + comment_id),
                "user":         user,
                "text":         text,
                "tagged_users": at_mentions,
                "timestamp":    _now(),
            }
            comment["replies"].append(reply)
            _save(data)
            return reply
    return None


def delete_comment(title: str, scope: str, comment_id: str, user: str) -> bool:
    """Soft-delete a comment (marks it deleted, keeps thread). Returns True on success."""
    key = _slide_key(title, scope)
    data = _load()
    for comment in data["slides"].get(key, {}).get("comments", []):
        if comment["id"] == comment_id and comment["user"] == user:
            comment["text"] = "[deleted]"
            comment["deleted"] = True
            _save(data)
            return True
    return False


# ── Custom slides ─────────────────────────────────────────────────────────────

def get_custom_slides() -> list[dict]:
    """Return all user-created custom slides."""
    return _load().get("custom_slides", [])


def save_custom_slide(slide: dict) -> None:
    """Upsert a custom slide by its 'id' field."""
    data = _load()
    existing = data.get("custom_slides", [])
    updated = [s for s in existing if s.get("id") != slide.get("id")]
    updated.append(slide)
    data["custom_slides"] = updated
    _save(data)


def remove_custom_slide(slide_id: str) -> None:
    """Remove a custom slide by ID."""
    data = _load()
    data["custom_slides"] = [s for s in data.get("custom_slides", [])
                              if s.get("id") != slide_id]
    _save(data)


def get_full_slide_data(title: str, scope: str) -> dict:
    """Return the full stored record for a slide."""
    key = _slide_key(title, scope)
    return _load()["slides"].get(key, {"commentary": "", "comments": []})
