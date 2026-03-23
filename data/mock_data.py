import pandas as pd
from datetime import date, timedelta


def get_platforms():
    return {
        "lines_of_business": [
            "Capital Markets",
            "Wealth Management",
            "Banking",
            "Insurance",
        ],
        "functions": [
            "Finance",
            "AML",
            "Banking Compliance",
            "Global Credit",
            "ORM",
        ],
        "technology": [
            "Technology & Operations",
        ],
        "regions": [
            "North America",
            "EMEA",
            "APAC",
        ],
    }


def get_audits() -> pd.DataFrame:
    audits = [
        # Owned Audits (5) — Capital Markets is Lead Audit Group
        {
            "audit_id": "CM-001",
            "audit_name": "Trading Book Risk Controls",
            "audit_type": "Owned Audit",
            "lead_group": "Capital Markets",
            "region": "North America",
            "status": "Complete",
            "rating": "High",
            "issue_count": 4,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-002",
            "audit_name": "Derivatives Valuation Process",
            "audit_type": "Owned Audit",
            "lead_group": "Capital Markets",
            "region": "EMEA",
            "status": "In Progress",
            "rating": "Medium",
            "issue_count": 3,
            "digital_rcm": "Incomplete",
            "planning_memo": "Done",
            "impacted_platform": "",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-003",
            "audit_name": "Prime Brokerage Asset Controls",
            "audit_type": "Owned Audit",
            "lead_group": "Capital Markets",
            "region": "APAC",
            "status": "Complete",
            "rating": "High",
            "issue_count": 5,
            "digital_rcm": "Done",
            "planning_memo": "Incomplete",
            "impacted_platform": "",
            "is_overdue": True,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-004",
            "audit_name": "Equity Research Compliance",
            "audit_type": "Owned Audit",
            "lead_group": "Capital Markets",
            "region": "North America",
            "status": "Complete",
            "rating": "Low",
            "issue_count": 1,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-005",
            "audit_name": "Structured Products Valuation",
            "audit_type": "Owned Audit",
            "lead_group": "Capital Markets",
            "region": "EMEA",
            "status": "Fieldwork",
            "rating": "Medium",
            "issue_count": 2,
            "digital_rcm": "N/A",
            "planning_memo": "N/A",
            "impacted_platform": "",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        # In-Scope AE — Cross-Platform (3)
        {
            "audit_id": "CM-006",
            "audit_name": "FX Settlement Controls Review",
            "audit_type": "In-Scope AE",
            "lead_group": "Technology & Operations",
            "region": "Global",
            "status": "Complete",
            "rating": "Medium",
            "issue_count": 2,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-007",
            "audit_name": "Collateral Management Oversight",
            "audit_type": "In-Scope AE",
            "lead_group": "Finance",
            "region": "North America",
            "status": "In Progress",
            "rating": "High",
            "issue_count": 3,
            "digital_rcm": "Incomplete",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-008",
            "audit_name": "Regulatory Reporting Integrity",
            "audit_type": "In-Scope AE",
            "lead_group": "Finance",
            "region": "EMEA",
            "status": "Complete",
            "rating": "High",
            "issue_count": 3,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": True,
            "quarter": "Q2 FY25",
        },
        # Indirect Coverage (6) — Capital Markets appears in Impacted Platform field
        {
            "audit_id": "CM-009",
            "audit_name": "AML Transaction Monitoring",
            "audit_type": "Indirect",
            "lead_group": "AML",
            "region": "Global",
            "status": "Complete",
            "rating": "High",
            "issue_count": 1,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-010",
            "audit_name": "Counterparty Credit Risk Review",
            "audit_type": "Indirect",
            "lead_group": "Global Credit",
            "region": "North America",
            "status": "In Progress",
            "rating": "Medium",
            "issue_count": 0,
            "digital_rcm": "N/A",
            "planning_memo": "N/A",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-011",
            "audit_name": "Operational Resilience Testing",
            "audit_type": "Indirect",
            "lead_group": "Technology & Operations",
            "region": "APAC",
            "status": "Complete",
            "rating": "Low",
            "issue_count": 0,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-012",
            "audit_name": "Insider Trading Controls",
            "audit_type": "Indirect",
            "lead_group": "Banking Compliance",
            "region": "Global",
            "status": "Complete",
            "rating": "Medium",
            "issue_count": 2,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": True,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-013",
            "audit_name": "ORM Framework Assessment",
            "audit_type": "Indirect",
            "lead_group": "ORM",
            "region": "EMEA",
            "status": "Fieldwork",
            "rating": "Medium",
            "issue_count": 1,
            "digital_rcm": "N/A",
            "planning_memo": "N/A",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
        {
            "audit_id": "CM-014",
            "audit_name": "Market Data Governance",
            "audit_type": "Indirect",
            "lead_group": "Finance",
            "region": "North America",
            "status": "Complete",
            "rating": "Low",
            "issue_count": 1,
            "digital_rcm": "Done",
            "planning_memo": "Done",
            "impacted_platform": "Capital Markets",
            "is_overdue": False,
            "out_of_scope": False,
            "quarter": "Q2 FY25",
        },
    ]
    return pd.DataFrame(audits)


def get_issues() -> pd.DataFrame:
    base_date = date(2025, 3, 1)
    issues = [
        # CM-001: Trading Book Risk Controls — 4 issues
        {"issue_id": "ISS-001", "audit_id": "CM-001", "title": "Limit breach escalation not documented", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=15), "remediation_owner": "J. Smith", "days_overdue": 0},
        {"issue_id": "ISS-002", "audit_id": "CM-001", "title": "Daily P&L reconciliation gaps", "severity": "Medium", "status": "Overdue", "due_date": base_date - timedelta(days=5), "remediation_owner": "J. Smith", "days_overdue": 5},
        {"issue_id": "ISS-003", "audit_id": "CM-001", "title": "Trader mandate review overdue", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=30), "remediation_owner": "A. Chen", "days_overdue": 0},
        {"issue_id": "ISS-004", "audit_id": "CM-001", "title": "Risk model validation outstanding", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=45), "remediation_owner": "A. Chen", "days_overdue": 0},
        # CM-002: Derivatives Valuation Process — 3 issues
        {"issue_id": "ISS-005", "audit_id": "CM-002", "title": "IPV process not consistently applied", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=20), "remediation_owner": "B. Patel", "days_overdue": 0},
        {"issue_id": "ISS-006", "audit_id": "CM-002", "title": "Level 3 asset classification inconsistency", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=25), "remediation_owner": "B. Patel", "days_overdue": 0},
        {"issue_id": "ISS-007", "audit_id": "CM-002", "title": "Valuation committee minutes incomplete", "severity": "Low", "status": "Closed", "due_date": base_date - timedelta(days=10), "remediation_owner": "M. Torres", "days_overdue": 0},
        # CM-003: Prime Brokerage Asset Controls — 5 issues
        {"issue_id": "ISS-008", "audit_id": "CM-003", "title": "Client asset segregation breach", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=10), "remediation_owner": "R. Kim", "days_overdue": 0},
        {"issue_id": "ISS-009", "audit_id": "CM-003", "title": "Daily reconciliation failures unresolved", "severity": "High", "status": "Overdue", "due_date": base_date - timedelta(days=8), "remediation_owner": "R. Kim", "days_overdue": 8},
        {"issue_id": "ISS-010", "audit_id": "CM-003", "title": "Margin call processing delays", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=20), "remediation_owner": "L. Nguyen", "days_overdue": 0},
        {"issue_id": "ISS-011", "audit_id": "CM-003", "title": "Custody reporting gaps identified", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=35), "remediation_owner": "L. Nguyen", "days_overdue": 0},
        {"issue_id": "ISS-012", "audit_id": "CM-003", "title": "Stock lending agreement terms not reviewed", "severity": "Low", "status": "Open", "due_date": base_date + timedelta(days=60), "remediation_owner": "P. Williams", "days_overdue": 0},
        # CM-004: Equity Research Compliance — 1 issue
        {"issue_id": "ISS-013", "audit_id": "CM-004", "title": "Research distribution list not updated", "severity": "Low", "status": "Closed", "due_date": base_date - timedelta(days=20), "remediation_owner": "S. Ahmed", "days_overdue": 0},
        # CM-005: Structured Products Valuation — 2 issues
        {"issue_id": "ISS-014", "audit_id": "CM-005", "title": "Pricing model sensitivity testing absent", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=25), "remediation_owner": "D. Foster", "days_overdue": 0},
        {"issue_id": "ISS-015", "audit_id": "CM-005", "title": "Approval threshold for bespoke instruments", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=40), "remediation_owner": "D. Foster", "days_overdue": 0},
        # CM-006: FX Settlement Controls — 2 issues
        {"issue_id": "ISS-016", "audit_id": "CM-006", "title": "Nostro account breaks unresolved >30 days", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=15), "remediation_owner": "C. Zhang", "days_overdue": 0},
        {"issue_id": "ISS-017", "audit_id": "CM-006", "title": "CLS settlement netting review overdue", "severity": "Low", "status": "Closed", "due_date": base_date - timedelta(days=5), "remediation_owner": "C. Zhang", "days_overdue": 0},
        # CM-007: Collateral Management — 3 issues
        {"issue_id": "ISS-018", "audit_id": "CM-007", "title": "Haircut methodology not updated for 18 months", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=20), "remediation_owner": "F. Okafor", "days_overdue": 0},
        {"issue_id": "ISS-019", "audit_id": "CM-007", "title": "Eligibility criteria applied inconsistently", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=30), "remediation_owner": "F. Okafor", "days_overdue": 0},
        {"issue_id": "ISS-020", "audit_id": "CM-007", "title": "Dispute resolution log not maintained", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=45), "remediation_owner": "G. Pham", "days_overdue": 0},
        # CM-008: Regulatory Reporting — 3 issues
        {"issue_id": "ISS-021", "audit_id": "CM-008", "title": "MiFID II transaction report gaps", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=10), "remediation_owner": "H. Blanc", "days_overdue": 0},
        {"issue_id": "ISS-022", "audit_id": "CM-008", "title": "EMIR reconciliation failures", "severity": "High", "status": "Open", "due_date": base_date + timedelta(days=15), "remediation_owner": "H. Blanc", "days_overdue": 0},
        {"issue_id": "ISS-023", "audit_id": "CM-008", "title": "Dodd-Frank swap reporting latency", "severity": "Medium", "status": "Open", "due_date": base_date + timedelta(days=20), "remediation_owner": "I. Martins", "days_overdue": 0},
    ]
    df = pd.DataFrame(issues)
    df["due_date"] = pd.to_datetime(df["due_date"])
    return df


def get_adjustments() -> list:
    return [
        {
            "adj_id": "ADJ-011",
            "adj_type": "Type 1 – Tag Correction",
            "field_being_adjusted": "Regions in Scope",
            "from_value": "N. America only",
            "to_value": "N. America + EMEA",
            "reason_code": "SC – Scope Clarification",
            "supporting_note": "Audit covered EMEA entities per engagement letter section 2.3. Regional tag was set incorrectly during initial data entry.",
            "evidence_ref": "CM-AUD-2025-Q2 engagement letter, section 2.3",
            "submitted_by": "Capital Markets Platform",
            "submitted_date": "2025-05-01",
            "status": "Approved",
        },
        {
            "adj_id": "ADJ-012",
            "adj_type": "Type 2 – Coverage Claim",
            "field_being_adjusted": "Impacted Platform",
            "from_value": "Not tagged",
            "to_value": "Capital Markets tagged",
            "reason_code": "MA – Methodology Alignment",
            "supporting_note": "Capital Markets named as impacted business in T&O audit scope section 4. Issue CM-ISS-018 is attributed to Capital Markets collateral desk.",
            "evidence_ref": "T&O audit report section 4, issue log ISS-018",
            "submitted_by": "Capital Markets Platform",
            "submitted_date": "2025-05-03",
            "status": "Pending",
        },
    ]


def filter_audits(
    df: pd.DataFrame,
    search: str = "",
    regions: list = None,
    statuses: list = None,
    audit_types: list = None,
) -> pd.DataFrame:
    result = df.copy()
    if search:
        mask = (
            result["audit_name"].str.contains(search, case=False, na=False)
            | result["audit_id"].str.contains(search, case=False, na=False)
            | result["lead_group"].str.contains(search, case=False, na=False)
        )
        result = result[mask]
    if regions:
        result = result[result["region"].isin(regions)]
    if statuses:
        result = result[result["status"].isin(statuses)]
    if audit_types:
        result = result[result["audit_type"].isin(audit_types)]
    return result


def compute_field_completeness(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    done_mask = (df["digital_rcm"] == "Done") & (df["planning_memo"] == "Done")
    applicable = df[df["digital_rcm"] != "N/A"]
    if applicable.empty:
        return 1.0
    return (applicable["digital_rcm"] == "Done").sum() / len(applicable)
