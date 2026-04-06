"""
Data validation tests for AuditIQ mock data.

Run with:  python -m pytest tests/test_data.py -v
       or: python tests/test_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from data.mock_data import (
    get_audits, get_issues, get_platforms, filter_audits, compute_field_completeness
)


# ── Run standalone ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    audits_df = get_audits()
    issues_df = get_issues()
    q1_df = audits_df[audits_df["quarter"] == "Q1 2026"]
    q2_df = audits_df[audits_df["quarter"] == "Q2 2026"]
    q1_iss = issues_df[issues_df["audit_id"].isin(q1_df["audit_id"])]
    q2_iss = issues_df[issues_df["audit_id"].isin(q2_df["audit_id"])]

    tests = [
        ("Q1 audit count == 90",        lambda: len(q1_df) == 90),
        ("Q2 audit count == 140",       lambda: len(q2_df) == 140),
        ("Total audit count == 230",    lambda: len(audits_df) == 230),
        ("Q1 Owned == 56",              lambda: len(q1_df[q1_df["audit_type"] == "Owned Audit"]) == 56),
        ("Q1 In-Scope AE == 20",        lambda: len(q1_df[q1_df["audit_type"] == "In-Scope AE"]) == 20),
        ("Q1 Indirect == 14",           lambda: len(q1_df[q1_df["audit_type"] == "Indirect"]) == 14),
        ("Q2 Owned == 88",              lambda: len(q2_df[q2_df["audit_type"] == "Owned Audit"]) == 88),
        ("Q2 In-Scope AE == 30",        lambda: len(q2_df[q2_df["audit_type"] == "In-Scope AE"]) == 30),
        ("Q2 Indirect == 22",           lambda: len(q2_df[q2_df["audit_type"] == "Indirect"]) == 22),
        ("No duplicate audit_ids",      lambda: not audits_df.duplicated("audit_id").any()),
        ("No duplicate issue_ids",      lambda: not issues_df.duplicated("issue_id").any()),
        ("All issue audit_ids exist",   lambda: set(issues_df["audit_id"]).issubset(set(audits_df["audit_id"]))),
        ("issue_count matches rows",    lambda: all(
            issues_df.groupby("audit_id").size().get(r.audit_id, 0) == r.issue_count
            for r in audits_df.itertuples()
        )),
        ("Regions valid",               lambda: set(audits_df["region"].unique()).issubset({"Canada", "Caribbean", "APAC", "US", "UK"})),
        ("Overdue days_overdue > 0",    lambda: (issues_df[issues_df["status"] == "Overdue"]["days_overdue"] > 0).all()),
        ("filter quarter=Q1 → 90",      lambda: len(filter_audits(audits_df, quarter="Q1 2026")) == 90),
        ("filter quarter=Q2 → 140",     lambda: len(filter_audits(audits_df, quarter="Q2 2026")) == 140),
        ("filter region=Canada works",  lambda: filter_audits(audits_df, regions=["Canada"])["region"].eq("Canada").all()),
        ("filter lob=Capital Markets",  lambda: len(filter_audits(audits_df, lobs=["Capital Markets"])) > 0),
        ("Q1 issue count consistent",   lambda: int(q1_df["issue_count"].sum()) == len(q1_iss)),
        ("Q2 issue count consistent",   lambda: int(q2_df["issue_count"].sum()) == len(q2_iss)),
        ("Field completeness in [0,1]", lambda: 0.0 <= compute_field_completeness(q1_df) <= 1.0),
    ]

    passed = failed = 0
    for name, fn in tests:
        try:
            ok = fn()
            if ok:
                print(f"  PASS  {name}")
                passed += 1
            else:
                print(f"  FAIL  {name}")
                failed += 1
        except Exception:
            print(f"  ERROR {name}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed", "✓" if failed == 0 else "✗")
    sys.exit(0 if failed == 0 else 1)
