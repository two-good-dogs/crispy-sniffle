import pandas as pd
import random
from datetime import date, timedelta


def get_risk_stripes():
    return [
        {"id": "liquidity",   "name": "Liquidity",              "icon": "💧", "description": "Cash flow, funding, and liquidity buffer adequacy"},
        {"id": "credit",      "name": "Credit",                 "icon": "📊", "description": "Counterparty, concentration, and portfolio credit risk"},
        {"id": "market",      "name": "Market",                 "icon": "📈", "description": "Interest rate, FX, equity, and commodity price risk"},
        {"id": "operational", "name": "Operational",            "icon": "⚙️", "description": "Process failures, people risk, and business continuity"},
        {"id": "it_cyber",    "name": "IT / Cyber",             "icon": "🔒", "description": "Technology resilience, data security, and cyber threat"},
        {"id": "fraud",       "name": "Fraud",                  "icon": "🚨", "description": "Internal/external fraud, misconduct, and unauthorized activity"},
        {"id": "compliance",  "name": "Compliance / Regulatory","icon": "📋", "description": "Regulatory adherence, conduct, and reporting obligations"},
        {"id": "aml",         "name": "AML / Financial Crime",  "icon": "🔍", "description": "Money laundering, sanctions, and transaction monitoring"},
    ]


def get_platforms():
    return {
        "lines_of_business": ["CM", "INS", "WM", "PB", "BO", "CB", "CNB", "RBCB"],
        "functions": ["HR", "CFO", "AML", "GC", "GRM"],
        "technology": ["T&O"],
        "regions": ["Canada", "Caribbean", "APAC", "US", "UK"],
    }


# ── Audit name pools ──────────────────────────────────────────────────────────
_AUDIT_NAMES = {
    "CM": [
        "Trading Book Risk Controls", "Derivatives Valuation Review",
        "Prime Brokerage Asset Controls", "FX Settlement Process",
        "Equity Research Compliance", "Credit Risk Model Validation",
        "Market Risk Limit Monitoring", "Structured Products Governance",
        "Collateral Management Review", "Regulatory Reporting Integrity",
        "Market Data Governance", "Position Reporting Accuracy",
        "Algo Trading Controls", "Repo and Reverse Repo Oversight",
        "Options Desk Controls", "Commodities Trading Review",
        "Interest Rate Risk Controls", "OTC Derivatives Clearing",
        "Front Office Supervision Controls", "Trade Surveillance Program",
    ],
    "INS": [
        "Claims Processing Controls", "Underwriting Risk Review",
        "Actuarial Assumption Validation", "Premium Settlement Accuracy",
        "Policy Administration Review", "Reinsurance Program Controls",
        "Insurance Reserve Adequacy", "Solvency Capital Assessment",
        "Liability Valuation Review", "Insurance Distribution Compliance",
        "Life Insurance Underwriting Controls", "P&C Loss Reserving Review",
        "Group Benefits Administration", "Annuity Product Controls",
        "Insurance Fraud Detection Program",
    ],
    "WM": [
        "Client Suitability Assessment", "KYC Program Effectiveness",
        "Portfolio Rebalancing Controls", "Fee Billing Accuracy Review",
        "Client Onboarding Controls", "Investment Advisory Compliance",
        "Fiduciary Duty Assessment", "Discretionary Mandate Oversight",
        "ESG Reporting Accuracy", "Model Portfolio Governance",
        "Managed Account Controls", "Referral Arrangement Review",
        "Third-Party Manager Oversight", "Client Reporting Accuracy",
    ],
    "PB": [
        "HNWI KYC Review", "Credit Facility Controls",
        "Trust Administration Oversight", "Estate Planning Controls",
        "Private Equity Oversight", "Lombard Lending Controls",
        "Relationship Manager Conduct", "Family Office Service Review",
        "PB Suitability Program", "PB Onboarding Compliance",
        "Offshore Booking Controls",
    ],
    "BO": [
        "Payment Processing Controls", "SWIFT Messaging Oversight",
        "Wire Transfer Authorization", "Loan Administration Review",
        "Account Opening Controls", "Dormant Account Management",
        "Nostro Reconciliation Review", "CHAPS Settlement Controls",
        "ACH Processing Controls", "Sanctions Screening Effectiveness",
        "Operational Loss Capture",
    ],
    "CB": [
        "Credit Underwriting Standards", "Commercial Lending Controls",
        "Trade Finance Review", "Treasury Management Services",
        "Commercial KYC Program", "Business Banking Compliance",
        "SME Lending Controls", "Commercial Real Estate Review",
        "Working Capital Facility Review", "Corporate Credit Portfolio Review",
        "Covenant Monitoring Controls",
    ],
    "CNB": [
        "Corporate Lending Controls", "Syndicated Loan Management",
        "Bond Issuance Controls", "Cash Management Services Review",
        "Correspondent Banking Controls", "DCM Origination Review",
        "Corporate Loan Covenant Monitoring", "Institutional Client Controls",
        "Global Transaction Services Review", "Agency Services Oversight",
    ],
    "RBCB": [
        "Consumer Lending Controls", "Mortgage Origination Review",
        "Retail KYC Program", "Branch Operations Oversight",
        "ATM and Card Controls", "Credit Card Portfolio Review",
        "Retail Deposit Controls", "Personal Loan Underwriting",
        "Overdraft Controls", "Digital Banking Security",
        "Retail Complaint Handling", "Collections Process Review",
        "Interest Rate Setting Controls", "Product Sales Suitability",
    ],
    "HR": [
        "Employee Screening Controls", "Compensation Governance Review",
        "Whistleblower Program Effectiveness", "Performance Management Controls",
        "HR Data Privacy Review", "Hiring Process Compliance",
        "Training Program Coverage", "Conduct Risk Controls",
    ],
    "CFO": [
        "Financial Reporting Accuracy", "Budget Variance Controls",
        "Treasury Operations Review", "Tax Compliance Assessment",
        "Management Accounts Review", "Expense Controls Review",
        "Intercompany Accounting Controls", "Revenue Recognition Review",
    ],
    "AML": [
        "Transaction Monitoring Effectiveness", "Sanctions Screening Controls",
        "SAR Filing Process", "PEP Identification Controls",
        "AML Training Program", "Cash Intensive Business Controls",
        "Cross-Border Payment Monitoring", "De-Risking Decisions Review",
    ],
    "GC": [
        "Litigation Reserve Adequacy", "Contract Management Controls",
        "Regulatory Filing Accuracy", "Legal Entity Governance Review",
        "Regulatory Correspondence Controls",
    ],
    "GRM": [
        "Risk Appetite Framework Review", "Stress Testing Adequacy",
        "Model Risk Management", "Operational Risk Controls",
        "Concentration Risk Monitoring", "Risk Data Aggregation",
        "Risk Governance Assessment", "Third-Party Risk Management",
    ],
    "T&O": [
        "Cybersecurity Controls Review", "Data Governance Framework",
        "IT Change Management", "Cloud Infrastructure Controls",
        "Disaster Recovery Testing", "Application Security Review",
        "Vendor Risk Management", "Data Loss Prevention Controls",
        "Access Management Review", "IT Resilience Testing",
        "Network Security Controls",
    ],
}

_RISK_MAP = {
    "CM":   [["market", "liquidity"], ["market", "credit"], ["credit", "market", "operational"], ["compliance"], ["operational", "it_cyber"], ["liquidity", "credit"]],
    "INS":  [["operational", "compliance"], ["credit", "liquidity"], ["fraud", "compliance"], ["compliance"], ["it_cyber", "operational"]],
    "WM":   [["compliance", "operational"], ["fraud", "aml"], ["market", "credit"], ["compliance", "fraud"]],
    "PB":   [["credit", "liquidity"], ["aml", "fraud"], ["compliance", "operational"], ["market", "credit"]],
    "BO":   [["operational", "it_cyber"], ["fraud", "operational"], ["compliance"], ["it_cyber", "operational"]],
    "CB":   [["credit", "operational"], ["compliance", "fraud"], ["aml", "credit"], ["market", "credit"]],
    "CNB":  [["credit", "market"], ["compliance", "operational"], ["aml", "fraud"], ["liquidity", "credit"]],
    "RBCB": [["compliance", "operational"], ["fraud", "aml"], ["credit", "operational"], ["it_cyber", "fraud"]],
    "HR":   [["operational", "compliance"], ["fraud", "compliance"]],
    "CFO":  [["operational", "compliance"], ["market", "liquidity"], ["compliance"]],
    "AML":  [["aml", "fraud"], ["compliance", "aml"]],
    "GC":   [["compliance", "operational"], ["compliance"]],
    "GRM":  [["operational", "credit"], ["market", "operational"], ["compliance", "credit"]],
    "T&O":  [["it_cyber", "operational"], ["fraud", "it_cyber"], ["operational", "it_cyber"]],
}

_ISSUE_TITLES = [
    "Approval threshold not consistently applied",
    "Reconciliation gaps identified in review period",
    "Escalation process not followed per policy",
    "Policy exception not approved at appropriate level",
    "Evidence of review not retained in system of record",
    "System access not revoked on staff departure",
    "Testing not completed within required frequency",
    "Reporting deadline missed for regulatory submission",
    "Risk appetite breach not escalated to committee",
    "Data quality issue identified in source system",
    "Segregation of duties conflict identified",
    "Control owner not identified for key process",
    "Third-party review not conducted within annual cycle",
    "Limit breach not documented or remediated",
    "Training requirement not completed by target population",
    "Management information not reported to governance forum",
    "Key person dependency with no documented backup",
    "Procedure not updated following regulatory change",
    "Alert investigation not completed within SLA",
    "KYC refresh overdue for high-risk client segment",
    "Model output not validated against benchmark",
    "Business continuity plan not tested in period",
    "Vendor contract terms not reviewed annually",
    "Control self-assessment not completed on schedule",
    "Issue closure evidence not sufficient to close",
    "Monitoring report not distributed to required recipients",
    "Exception log not reviewed by management",
    "Dual authorisation control bypassed",
    "Sample of transactions contained unresolved breaks",
    "Risk rating not updated following material event",
]

_OWNERS = [
    "J. Smith", "A. Chen", "B. Patel", "R. Kim", "L. Nguyen",
    "D. Foster", "F. Okafor", "G. Pham", "H. Blanc", "I. Martins",
    "C. Zhang", "M. Torres", "S. Ahmed", "P. Williams", "K. Johansson",
    "N. Osei", "T. Bergman", "E. Nakamura", "V. Reyes", "O. Mensah",
]


def _build_data():
    rng = random.Random(42)
    lobs = ["CM", "INS", "WM", "PB", "BO", "CB", "CNB", "RBCB"]
    fn_to = ["HR", "CFO", "AML", "GC", "GRM", "T&O"]
    regions = ["Canada", "Caribbean", "APAC", "US", "UK"]
    region_w = [0.30, 0.10, 0.15, 0.25, 0.20]

    def pick_rating():
        return rng.choices(["High", "Medium", "Low"], weights=[0.25, 0.50, 0.25])[0]

    def pick_status(q):
        if q == "Q1 2026":
            return rng.choices(["Complete", "In Progress", "Fieldwork"], weights=[0.52, 0.32, 0.16])[0]
        return rng.choices(["Complete", "In Progress", "Fieldwork"], weights=[0.60, 0.26, 0.14])[0]

    def pick_rcm(status):
        if status == "Complete":
            return rng.choices(["Done", "Incomplete"], weights=[0.85, 0.15])[0]
        if status == "In Progress":
            return rng.choices(["Done", "Incomplete", "N/A"], weights=[0.50, 0.35, 0.15])[0]
        return "N/A"

    def pick_memo(status):
        if status == "Complete":
            return rng.choices(["Done", "Incomplete"], weights=[0.90, 0.10])[0]
        if status == "In Progress":
            return rng.choices(["Done", "Incomplete", "N/A"], weights=[0.60, 0.30, 0.10])[0]
        return "N/A"

    def pick_issue_count(rating, status):
        if status == "Fieldwork":
            return rng.randint(0, 2)
        if rating == "High":
            return rng.randint(2, 7)
        if rating == "Medium":
            return rng.randint(1, 4)
        return rng.randint(0, 2)

    def pick_marc(status, audit_type):
        if status != "Complete" or audit_type == "Indirect":
            return "N/A"
        return rng.choices(
            ["Developed", "Substantially Developed", "Partially Developed", "Underdeveloped"],
            weights=[0.15, 0.45, 0.30, 0.10],
        )[0]

    def pick_current_rating(status, risk_rating):
        if status != "Complete":
            return "NA"
        return {"Low": "SAT", "Medium": "RI", "High": "UNSAT"}[risk_rating]

    def make_issues(audit_id, count, base_date, status):
        rows = []
        title_pool = list(_ISSUE_TITLES)
        rng.shuffle(title_pool)
        for j in range(count):
            sev = rng.choices(["High", "Medium", "Low"], weights=[0.28, 0.50, 0.22])[0]
            if status == "Complete":
                ist = rng.choices(["Open", "Closed", "Overdue"], weights=[0.38, 0.42, 0.20])[0]
            else:
                ist = rng.choices(["Open", "Closed", "Overdue"], weights=[0.62, 0.22, 0.16])[0]
            offset = rng.randint(-20, 70)
            if ist == "Overdue" and offset >= 0:
                offset = -rng.randint(1, 15)
            due = base_date + timedelta(days=offset)
            days_ov = max(1, -offset) if ist == "Overdue" else 0
            rows.append({
                "audit_id": audit_id,
                "title": title_pool[j % len(title_pool)],
                "severity": sev,
                "status": ist,
                "due_date": due,
                "remediation_owner": rng.choice(_OWNERS),
                "days_overdue": days_ov,
                "self_identified": rng.random() < 0.25,
            })
        return rows

    # ── Quarter specs ──────────────────────────────────────────────────────────
    # Q1 2026: 56 owned + 20 AE + 14 indirect = 90
    # Q2 2026: 88 owned + 30 AE + 22 indirect = 140
    q1_owned = {"CM": 8, "INS": 7, "WM": 7, "PB": 6, "BO": 7, "CB": 7, "CNB": 7, "RBCB": 7}
    q2_owned = {"CM": 13, "INS": 10, "WM": 11, "PB": 8, "BO": 11, "CB": 11, "CNB": 12, "RBCB": 12}

    quarter_specs = [
        ("Q1 2026", q1_owned, 20, 14, date(2026, 2, 1)),
        ("Q2 2026", q2_owned, 30, 22, date(2026, 5, 1)),
    ]

    audits, issues = [], []
    a_seq, i_seq = 1, 1
    name_cursors = {k: 0 for k in list(lobs) + list(fn_to)}

    def next_name(group):
        pool = _AUDIT_NAMES[group]
        idx = name_cursors[group]
        name = pool[idx % len(pool)]
        if idx >= len(pool):
            name = name + f" — Phase {idx // len(pool) + 1}"
        name_cursors[group] += 1
        return name

    for quarter, lob_counts, n_ae, n_indirect, base_date in quarter_specs:
        q_tag = "Q1" if "Q1" in quarter else "Q2"
        # Reset name cursors per quarter so Q1 and Q2 can reuse pools
        for k in name_cursors:
            name_cursors[k] = 0

        # ── Owned audits ───────────────────────────────────────────────────────
        for lob, count in lob_counts.items():
            for _ in range(count):
                rating = pick_rating()
                status = pick_status(quarter)
                n_issues = pick_issue_count(rating, status)
                aid = f"{lob}-{q_tag}26-{a_seq:03d}"
                a_seq += 1
                audits.append({
                    "audit_id": aid,
                    "audit_name": next_name(lob),
                    "audit_type": "Owned Audit",
                    "lead_group": lob,
                    "region": rng.choices(regions, weights=region_w)[0],
                    "status": status,
                    "rating": rating,
                    "current_rating": pick_current_rating(status, rating),
                    "report_status": "Published" if status == "Complete" else "In Progress",
                    "marc_rating": pick_marc(status, "Owned Audit"),
                    "issue_count": n_issues,
                    "digital_rcm": pick_rcm(status),
                    "planning_memo": pick_memo(status),
                    "impacted_platform": "",
                    "is_overdue": status == "Complete" and rating == "High" and rng.random() < 0.12,
                    "out_of_scope": rng.random() < 0.05,
                    "quarter": quarter,
                    "risk_stripes": rng.choice(_RISK_MAP[lob]),
                })
                for row in make_issues(aid, n_issues, base_date, status):
                    row["issue_id"] = f"ISS-{q_tag}26-{i_seq:03d}"
                    i_seq += 1
                    issues.append(row)

        # ── In-Scope AE ────────────────────────────────────────────────────────
        for _ in range(n_ae):
            lead = rng.choice(fn_to)
            impacted = rng.choice(lobs)
            rating = pick_rating()
            status = pick_status(quarter)
            n_issues = pick_issue_count(rating, status)
            aid = f"AE-{q_tag}26-{a_seq:03d}"
            a_seq += 1
            audits.append({
                "audit_id": aid,
                "audit_name": next_name(lead),
                "audit_type": "In-Scope AE",
                "lead_group": lead,
                "region": rng.choices(regions, weights=region_w)[0],
                "status": status,
                "rating": rating,
                "current_rating": pick_current_rating(status, rating),
                "report_status": "Published" if status == "Complete" else "In Progress",
                "marc_rating": pick_marc(status, "In-Scope AE"),
                "issue_count": n_issues,
                "digital_rcm": pick_rcm(status),
                "planning_memo": pick_memo(status),
                "impacted_platform": impacted,
                "is_overdue": False,
                "out_of_scope": rng.random() < 0.05,
                "quarter": quarter,
                "risk_stripes": rng.choice(_RISK_MAP[lead]),
            })
            for row in make_issues(aid, n_issues, base_date, status):
                row["issue_id"] = f"ISS-{q_tag}26-{i_seq:03d}"
                i_seq += 1
                issues.append(row)

        # ── Indirect ───────────────────────────────────────────────────────────
        for _ in range(n_indirect):
            lead = rng.choice(fn_to)
            impacted = rng.choice(lobs)
            rating = pick_rating()
            status = pick_status(quarter)
            n_issues = pick_issue_count(rating, status)
            aid = f"IND-{q_tag}26-{a_seq:03d}"
            a_seq += 1
            audits.append({
                "audit_id": aid,
                "audit_name": next_name(lead),
                "audit_type": "Indirect",
                "current_rating": pick_current_rating(status, rating),
                "report_status": "Published" if status == "Complete" else "In Progress",
                "marc_rating": "N/A",
                "lead_group": lead,
                "region": rng.choices(regions, weights=region_w)[0],
                "status": status,
                "rating": rating,
                "issue_count": n_issues,
                "digital_rcm": pick_rcm(status),
                "planning_memo": pick_memo(status),
                "impacted_platform": impacted,
                "is_overdue": False,
                "out_of_scope": rng.random() < 0.04,
                "quarter": quarter,
                "risk_stripes": rng.choice(_RISK_MAP[lead]),
            })
            for row in make_issues(aid, n_issues, base_date, status):
                row["issue_id"] = f"ISS-{q_tag}26-{i_seq:03d}"
                i_seq += 1
                issues.append(row)

    audit_df = pd.DataFrame(audits)
    issue_df = pd.DataFrame(issues)
    issue_df["due_date"] = pd.to_datetime(issue_df["due_date"])
    return audit_df, issue_df


# Build once at import time
_AUDIT_DF, _ISSUE_DF = _build_data()


def get_audits() -> pd.DataFrame:
    return _AUDIT_DF.copy()


def get_issues() -> pd.DataFrame:
    return _ISSUE_DF.copy()


def filter_audits(
    df: pd.DataFrame,
    search: str = "",
    regions: list = None,
    statuses: list = None,
    audit_types: list = None,
    quarter: str = None,
    lobs: list = None,
) -> pd.DataFrame:
    result = df.copy()
    if quarter:
        result = result[result["quarter"] == quarter]
    if lobs:
        result = result[result["lead_group"].isin(lobs) | result["impacted_platform"].isin(lobs)]
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
    applicable = df[df["digital_rcm"] != "N/A"]
    if applicable.empty:
        return 1.0
    return (applicable["digital_rcm"] == "Done").sum() / len(applicable)


# ── Control Environment Auditable Units ──────────────────────────────────────

_CE_RATINGS = ["SAT", "RI", "UNSAT"]
_CE_TRENDS = ["Trending Up", "No Change", "Downgraded", "Upgraded"]

_AUDITABLE_UNITS = {
    "CM": [
        "BCS Regulatory Services", "Business Client Services", "Capital Markets COO Functions",
        "Cross Global Markets Teams", "Global Equities", "Macro Products",
        "Treasury & Resource Management", "Economics, Strategy, Innovation, Marketing, and Sustainability",
        "Central Funding Group", "Corporate Banking & Global Credit", "Global Investment Banking",
        "Spread Products", "US Cash Management", "Quantitative Technology Services",
    ],
    "INS": [
        "Claims Operations", "Underwriting Risk", "Actuarial Services",
        "Premium Operations", "Policy Administration", "Reinsurance Management",
        "Insurance Finance", "Life Product Management",
    ],
    "WM": [
        "Client Advisory", "Relationship Management", "Portfolio Management",
        "Operations & Administration", "Compliance & Suitability",
    ],
    "PB": [
        "Client Services", "Credit & Lending", "Trust & Fiduciary",
        "Investment Advisory", "Operations",
    ],
    "BO": [
        "Payment Operations", "Settlement Services", "Loan Administration",
        "Account Management", "Sanctions & Compliance Operations",
    ],
    "CB": [
        "Commercial Lending", "Trade Finance", "Treasury Services",
        "Commercial Onboarding", "Credit Administration",
    ],
    "CNB": [
        "Corporate Lending", "Syndication Management", "DCM Origination",
        "Cash Management", "Correspondent Banking", "Agency Services",
    ],
    "RBCB": [
        "Retail Lending", "Mortgage Operations", "Retail Onboarding",
        "Branch Operations", "Card Services", "Deposits Management",
    ],
    "HR": [
        "Talent Acquisition", "Compensation & Benefits", "Employee Relations",
        "Learning & Development", "Data & Analytics",
    ],
    "CFO": [
        "Financial Planning", "Treasury", "Tax",
        "Management Accounting", "Financial Operations",
    ],
    "AML": [
        "Transaction Monitoring", "Sanctions Screening",
        "Customer Due Diligence", "Reporting & Escalation",
    ],
    "GC": [
        "Litigation Management", "Contract Management",
        "Regulatory Compliance", "Entity Management",
    ],
    "GRM": [
        "Risk Strategy", "Risk Data & Analytics", "Stress Testing",
        "Model Risk Management", "Operational Risk",
    ],
    "T&O": [
        "Cybersecurity", "Data Governance", "IT Operations",
        "Cloud Services", "Application Development", "IT Service Management",
    ],
}


def _build_ce_data():
    """AU-level CE data: one row per Auditable Unit per platform. Used by Platform view."""
    rng = random.Random(42)
    ce_data = []
    for platform, units in _AUDITABLE_UNITS.items():
        for unit_idx, unit_name in enumerate(units):
            au_id = f"{platform}_{unit_idx:02d}"
            ce_data.append({
                "au_id": au_id,
                "platform": platform,
                "auditable_unit": unit_name,
                "entities": "",
                "ce_rating": rng.choice(_CE_RATINGS),
                "trend": rng.choice(_CE_TRENDS),
            })
    return ce_data


def _build_ce_region_data():
    """Platform-level CE data per region: one row per (platform, region). Used by Regional view."""
    rng = random.Random(99)
    records = []
    regions = ["Canada", "Caribbean", "APAC", "US", "UK"]
    all_platforms = list(_AUDITABLE_UNITS.keys())
    for platform in all_platforms:
        for region in regions:
            records.append({
                "rec_id": f"{platform}_{region}",
                "platform": platform,
                "region": region,
                "ce_rating": rng.choice(_CE_RATINGS),
                "trend": rng.choice(_CE_TRENDS),
            })
    return records


_CE_DATA = _build_ce_data()
_CE_REGION_DATA = _build_ce_region_data()


def get_control_environment_seed() -> list:
    """Return AU-level CE data for DB seeding (Platform view)."""
    return _CE_DATA


def get_ce_region_seed() -> list:
    """Return platform-level CE data per region for DB seeding (Regional view)."""
    return _CE_REGION_DATA


def get_adjustments() -> list:
    return [
        {
            "adj_id": "ADJ-011",
            "adj_type": "Type 1 – Tag Correction",
            "field_being_adjusted": "Regions in Scope",
            "from_value": "Canada only",
            "to_value": "Canada + US",
            "reason_code": "SC – Scope Clarification",
            "supporting_note": "Audit covered US entities per engagement letter section 2.3. Regional tag was set incorrectly during initial data entry.",
            "evidence_ref": "CM-AUD-2026-Q1 engagement letter, section 2.3",
            "submitted_by": "Capital Markets Platform",
            "submitted_date": "2026-02-14",
            "status": "Approved",
        },
        {
            "adj_id": "ADJ-012",
            "adj_type": "Type 2 – Coverage Claim",
            "field_being_adjusted": "Impacted Platform",
            "from_value": "Not tagged",
            "to_value": "CM tagged",
            "reason_code": "MA – Methodology Alignment",
            "supporting_note": "CM named as impacted business in T&O audit scope. Issue is attributed to CM collateral desk.",
            "evidence_ref": "T&O audit report section 4, issue log",
            "submitted_by": "Capital Markets Platform",
            "submitted_date": "2026-02-18",
            "status": "Pending",
        },
    ]


CURRENT_USER = "P. Kumar"


def get_users() -> list:
    return [
        {"name": "P. Kumar",    "email": "p.kumar@auditiq.internal",    "initials": "PK", "role": "Capital Markets Audit Lead"},
        {"name": "J. Smith",    "email": "j.smith@auditiq.internal",    "initials": "JS", "role": "Remediation Owner"},
        {"name": "A. Chen",     "email": "a.chen@auditiq.internal",     "initials": "AC", "role": "Remediation Owner"},
        {"name": "B. Patel",    "email": "b.patel@auditiq.internal",    "initials": "BP", "role": "Remediation Owner"},
        {"name": "M. Torres",   "email": "m.torres@auditiq.internal",   "initials": "MT", "role": "Remediation Owner"},
        {"name": "R. Kim",      "email": "r.kim@auditiq.internal",      "initials": "RK", "role": "Remediation Owner"},
        {"name": "L. Nguyen",   "email": "l.nguyen@auditiq.internal",   "initials": "LN", "role": "Remediation Owner"},
        {"name": "P. Williams", "email": "p.williams@auditiq.internal", "initials": "PW", "role": "Remediation Owner"},
        {"name": "S. Ahmed",    "email": "s.ahmed@auditiq.internal",    "initials": "SA", "role": "Remediation Owner"},
        {"name": "D. Foster",   "email": "d.foster@auditiq.internal",   "initials": "DF", "role": "Remediation Owner"},
        {"name": "F. Okafor",   "email": "f.okafor@auditiq.internal",   "initials": "FO", "role": "Remediation Owner"},
        {"name": "G. Pham",     "email": "g.pham@auditiq.internal",     "initials": "GP", "role": "Remediation Owner"},
        {"name": "H. Blanc",    "email": "h.blanc@auditiq.internal",    "initials": "HB", "role": "Remediation Owner"},
        {"name": "I. Martins",  "email": "i.martins@auditiq.internal",  "initials": "IM", "role": "Remediation Owner"},
    ]


def get_seed_messages() -> list:
    q1_audit_ids = _AUDIT_DF[_AUDIT_DF["quarter"] == "Q1 2026"]["audit_id"].tolist()
    q1_issues = _ISSUE_DF[_ISSUE_DF["audit_id"].isin(q1_audit_ids)]

    def _pick_issue(idx):
        if len(q1_issues) > idx:
            row = q1_issues.iloc[idx]
            return row["issue_id"], row["title"], row["audit_id"]
        return "ISS-Q126-001", "Approval threshold not consistently applied", q1_audit_ids[0] if q1_audit_ids else "N/A"

    iid1, ititle1, _ = _pick_issue(0)
    iid2, ititle2, aid2 = _pick_issue(4)
    iid3, ititle3, _ = _pick_issue(8)

    return [
        {
            "msg_id": "MSG-001",
            "from_user": "J. Smith",
            "to_user": CURRENT_USER,
            "subject_type": "issue",
            "subject_id": iid1,
            "subject_label": f"{iid1} · {ititle1}",
            "message": "Hi, I've uploaded the supporting evidence to the shared drive. Could you review and confirm whether this satisfies the remediation requirement before the quarter close?",
            "sent_at": "2026-02-10 09:15",
            "read": False,
        },
        {
            "msg_id": "MSG-002",
            "from_user": "F. Okafor",
            "to_user": CURRENT_USER,
            "subject_type": "project",
            "subject_id": aid2,
            "subject_label": f"{aid2} · Collateral Management Review",
            "message": "The updated methodology document has been signed off by the MD. Can you update the status in AuditIQ? We'd like this marked remediated before the hard close.",
            "sent_at": "2026-02-12 14:33",
            "read": False,
        },
        {
            "msg_id": "MSG-003",
            "from_user": "H. Blanc",
            "to_user": CURRENT_USER,
            "subject_type": "issue",
            "subject_id": iid3,
            "subject_label": f"{iid3} · {ititle3}",
            "message": "Flagging that the remediation will miss the quarter deadline. We're requesting a 2-week extension. Please advise on the process.",
            "sent_at": "2026-02-14 11:07",
            "read": True,
        },
        {
            "msg_id": "MSG-004",
            "from_user": CURRENT_USER,
            "to_user": "R. Kim",
            "subject_type": "issue",
            "subject_id": iid1,
            "subject_label": f"{iid1} · {ititle1}",
            "message": "This issue is now overdue. Please provide an update by EOD Friday or this will be escalated to the Reporting Director.",
            "sent_at": "2026-02-13 16:45",
            "read": True,
        },
        {
            "msg_id": "MSG-005",
            "from_user": "B. Patel",
            "to_user": CURRENT_USER,
            "subject_type": "issue",
            "subject_id": iid2,
            "subject_label": f"{iid2} · {ititle2}",
            "message": "Just a heads up — the Digital RCM is still showing Incomplete. Our team completed the upload last week. Could you verify on your end?",
            "sent_at": "2026-02-15 08:20",
            "read": False,
        },
    ]
