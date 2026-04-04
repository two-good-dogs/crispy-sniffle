import os
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Date, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "auditiq.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Audit(Base):
    __tablename__ = "audits"

    audit_id = Column(String, primary_key=True)
    audit_name = Column(String, nullable=False)
    audit_type = Column(String, nullable=False)
    lead_group = Column(String, nullable=False)
    impacted_group = Column(String, default="")       # comma-separated platforms
    region = Column(String, nullable=False)
    impacted_region = Column(String, default="")       # comma-separated regions
    report_status = Column(String, default="In Progress")  # In Progress or Published
    previous_rating = Column(String, default="NA")     # NA, SAT, RI, UNSAT
    current_rating = Column(String, default="NA")      # NA, SAT, RI, UNSAT
    issue_count = Column(Integer, default=0)
    digital_rcm = Column(String, default="N/A")
    planning_memo = Column(String, default="N/A")
    impacted_platform = Column(String, default="")
    is_overdue = Column(Boolean, default=False)
    out_of_scope = Column(Boolean, default=False)
    quarter = Column(String, default="Q2 FY25")
    risk_stripes = Column(String, default="")          # comma-separated
    # Keep status for internal use (snapshots, validations)
    status = Column(String, default="In Progress")


class Issue(Base):
    __tablename__ = "issues"

    issue_id = Column(String, primary_key=True)
    audit_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    remediation_owner = Column(String, nullable=False)
    days_overdue = Column(Integer, default=0)


class Adjustment(Base):
    __tablename__ = "adjustments"

    adj_id = Column(String, primary_key=True)
    audit_id = Column(String, default="")
    adj_type = Column(String, nullable=False)
    field_being_adjusted = Column(String, nullable=False)
    from_value = Column(String, default="\u2014")
    to_value = Column(String, default="\u2014")
    reason_code = Column(String, nullable=False)
    supporting_note = Column(Text, nullable=False)
    evidence_ref = Column(String, default="")
    submitted_by = Column(String, nullable=False)
    submitted_date = Column(String, nullable=False)
    status = Column(String, default="Pending")


class IssueCommentary(Base):
    __tablename__ = "issue_commentary"

    entry_id  = Column(String, primary_key=True)
    quarter   = Column(String, nullable=False)
    section   = Column(String, nullable=False)   # e.g. "Issue Remediation", "Reissues"
    text      = Column(Text, nullable=False)
    author    = Column(String, nullable=False)
    posted_at = Column(String, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    msg_id        = Column(String, primary_key=True)
    from_user     = Column(String, nullable=False)
    to_user       = Column(String, nullable=False)
    subject_type  = Column(String, nullable=False)   # "project" | "issue"
    subject_id    = Column(String, nullable=False)
    subject_label = Column(String, nullable=False)
    message       = Column(Text, nullable=False)
    sent_at       = Column(String, nullable=False)   # ISO string for easy display
    read          = Column(Boolean, default=False)


class ControlEnvironment(Base):
    """Platform-level CE: one row per Auditable Unit per platform. Used by Platform view."""
    __tablename__ = "control_environment"

    au_id          = Column(String, primary_key=True)  # e.g. "WM_01"
    platform       = Column(String, nullable=False)    # e.g. "WM"
    auditable_unit = Column(String, nullable=False)    # e.g. "Client Advisory"
    entities       = Column(String, nullable=False)
    ce_rating      = Column(String, default="N/A")     # N/A, SAT, RI, UNSAT
    trend          = Column(String, default="N/A")     # N/A, Trending Up, No Change, Downgraded, Upgraded


class ControlEnvironmentRegion(Base):
    """Regional CE: one row per platform per region. Used by Regional view."""
    __tablename__ = "control_environment_region"

    rec_id    = Column(String, primary_key=True)   # e.g. "WM_Canada"
    platform  = Column(String, nullable=False)     # e.g. "WM"
    region    = Column(String, nullable=False)     # e.g. "Canada"
    ce_rating = Column(String, default="N/A")     # N/A, SAT, RI, UNSAT
    trend     = Column(String, default="N/A")     # N/A, Trending Up, No Change, Downgraded, Upgraded


class CECommentary(Base):
    __tablename__ = "ce_commentary"

    entry_id  = Column(String, primary_key=True)
    platform  = Column(String, nullable=False)
    text      = Column(Text, nullable=False)
    author    = Column(String, nullable=False)
    posted_at = Column(String, nullable=False)


def init_db():
    """Create tables and seed with initial data if empty."""
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        if session.query(Audit).count() == 0:
            _seed_audits(session)
        if session.query(Issue).count() == 0:
            _seed_issues(session)
        if session.query(Adjustment).count() == 0:
            _seed_adjustments(session)
        if session.query(Message).count() == 0:
            _seed_messages(session)
        if session.query(ControlEnvironment).count() == 0:
            _seed_control_environment(session)
        if session.query(ControlEnvironmentRegion).count() == 0:
            _seed_control_environment_region(session)
        session.commit()
        # IssueCommentary and CECommentary start empty — no seed needed
    finally:
        session.close()


def get_session():
    return SessionLocal()


# ── Message CRUD ──────────────────────────────────────────────────────────────

def db_get_messages() -> list:
    """Return all messages as plain dicts, newest first."""
    session = SessionLocal()
    try:
        rows = session.query(Message).order_by(Message.sent_at.desc()).all()
        return [
            {
                "msg_id":        r.msg_id,
                "from_user":     r.from_user,
                "to_user":       r.to_user,
                "subject_type":  r.subject_type,
                "subject_id":    r.subject_id,
                "subject_label": r.subject_label,
                "message":       r.message,
                "sent_at":       r.sent_at,
                "read":          r.read,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_save_message(msg: dict) -> None:
    """Insert a new message into the DB."""
    session = SessionLocal()
    try:
        session.add(Message(
            msg_id=msg["msg_id"],
            from_user=msg["from_user"],
            to_user=msg["to_user"],
            subject_type=msg["subject_type"],
            subject_id=msg["subject_id"],
            subject_label=msg["subject_label"],
            message=msg["message"],
            sent_at=msg["sent_at"],
            read=msg.get("read", False),
        ))
        session.commit()
    finally:
        session.close()


def db_mark_read(msg_ids: list) -> None:
    """Mark the given message IDs as read in the DB."""
    if not msg_ids:
        return
    session = SessionLocal()
    try:
        session.query(Message).filter(Message.msg_id.in_(msg_ids)).update(
            {"read": True}, synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


def _seed_messages(session):
    from data.mock_data import get_seed_messages
    for m in get_seed_messages():
        session.add(Message(
            msg_id=m["msg_id"],
            from_user=m["from_user"],
            to_user=m["to_user"],
            subject_type=m["subject_type"],
            subject_id=m["subject_id"],
            subject_label=m["subject_label"],
            message=m["message"],
            sent_at=m["sent_at"],
            read=m.get("read", False),
        ))


def _seed_audits(session):
    audits = [
        # ═══════════════════════════════════════════════════════════════════════
        # CM — Capital Markets  (14 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (5)
        Audit(audit_id="CM-001", audit_name="Trading Book Risk Controls", audit_type="Owned Audit",
              lead_group="CM", impacted_group="CFO,GRM", region="US", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,liquidity,operational"),
        Audit(audit_id="CM-002", audit_name="Derivatives Valuation Process", audit_type="Owned Audit",
              lead_group="CM", impacted_group="CFO", region="UK", impacted_region="US",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,credit"),
        Audit(audit_id="CM-003", audit_name="Prime Brokerage Asset Controls", audit_type="Owned Audit",
              lead_group="CM", impacted_group="GC,T&O", region="APAC", impacted_region="US,UK",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="UNSAT",
              issue_count=5, digital_rcm="Done", planning_memo="Incomplete", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,liquidity,fraud"),
        Audit(audit_id="CM-004", audit_name="Equity Research Compliance", audit_type="Owned Audit",
              lead_group="CM", impacted_group="CLAO", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="CM-005", audit_name="Structured Products Valuation", audit_type="Owned Audit",
              lead_group="CM", impacted_group="CFO,GC", region="UK", impacted_region="APAC",
              status="Fieldwork", report_status="In Progress", previous_rating="RI", current_rating="NA",
              issue_count=2, digital_rcm="N/A", planning_memo="N/A", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,credit,liquidity"),
        # In-Scope AE (3)
        Audit(audit_id="CM-006", audit_name="FX Settlement Controls Review", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="CM,CFO", region="US", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),
        Audit(audit_id="CM-007", audit_name="Collateral Management Oversight", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="CM,GC", region="Canada", impacted_region="US",
              status="In Progress", report_status="In Progress", previous_rating="NA", current_rating="UNSAT",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,liquidity"),
        Audit(audit_id="CM-008", audit_name="Regulatory Reporting Integrity", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="CM,CLAO", region="UK", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        # Indirect (6)
        Audit(audit_id="CM-009", audit_name="AML Transaction Monitoring", audit_type="Indirect",
              lead_group="GRM", impacted_group="CM,CLAO", region="Caribbean", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="UNSAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,fraud"),
        Audit(audit_id="CM-010", audit_name="Counterparty Credit Risk Review", audit_type="Indirect",
              lead_group="GC", impacted_group="CM,CFO", region="US", impacted_region="UK",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit"),
        Audit(audit_id="CM-011", audit_name="Operational Resilience Testing", audit_type="Indirect",
              lead_group="T&O", impacted_group="CM", region="APAC", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),
        Audit(audit_id="CM-012", audit_name="Insider Trading Controls", audit_type="Indirect",
              lead_group="CLAO", impacted_group="CM,GRM", region="UK", impacted_region="US,Canada",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="fraud,compliance"),
        Audit(audit_id="CM-013", audit_name="ORM Framework Assessment", audit_type="Indirect",
              lead_group="GRM", impacted_group="CM,T&O", region="UK", impacted_region="APAC",
              status="Fieldwork", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=1, digital_rcm="N/A", planning_memo="N/A", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="CM-014", audit_name="Market Data Governance", audit_type="Indirect",
              lead_group="CFO", impacted_group="CM,T&O", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,market"),

        # ═══════════════════════════════════════════════════════════════════════
        # WM — Wealth Management  (12 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (5)
        Audit(audit_id="WM-001", audit_name="Client Suitability Assessment", audit_type="Owned Audit",
              lead_group="WM", impacted_group="CLAO", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="WM-002", audit_name="Portfolio Rebalancing Controls", audit_type="Owned Audit",
              lead_group="WM", impacted_group="CFO,GRM", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,operational"),
        Audit(audit_id="WM-003", audit_name="Fee Billing Accuracy Review", audit_type="Owned Audit",
              lead_group="WM", impacted_group="CFO", region="Caribbean", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,fraud"),
        Audit(audit_id="WM-004", audit_name="KYC Refresh Compliance", audit_type="Owned Audit",
              lead_group="WM", impacted_group="CLAO,GRM", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,compliance"),
        Audit(audit_id="WM-005", audit_name="Discretionary Mandate Oversight", audit_type="Owned Audit",
              lead_group="WM", impacted_group="GC", region="UK", impacted_region="",
              status="Fieldwork", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,compliance"),
        # In-Scope AE (3)
        Audit(audit_id="WM-006", audit_name="Digital Onboarding Platform", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="WM,CLAO", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="WM-007", audit_name="Client Reporting Accuracy", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="WM", region="US", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="WM-008", audit_name="Anti-Money Laundering WM Review", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="WM,CLAO", region="Caribbean", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="RI",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,fraud"),
        # Indirect (4)
        Audit(audit_id="WM-009", audit_name="Third-Party Distributor Oversight", audit_type="Indirect",
              lead_group="GC", impacted_group="WM", region="UK", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,compliance"),
        Audit(audit_id="WM-010", audit_name="Data Privacy — Client Records", audit_type="Indirect",
              lead_group="T&O", impacted_group="WM,HR", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),
        Audit(audit_id="WM-011", audit_name="Cross-Border Tax Advisory Compliance", audit_type="Indirect",
              lead_group="CLAO", impacted_group="WM,CFO", region="Caribbean", impacted_region="Canada,US",
              status="In Progress", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="WM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="WM-012", audit_name="Investment Product Governance", audit_type="Indirect",
              lead_group="GRM", impacted_group="WM,GC", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="WM",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="market,compliance"),

        # ═══════════════════════════════════════════════════════════════════════
        # INS — Insurance  (11 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="INS-001", audit_name="Claims Processing Controls", audit_type="Owned Audit",
              lead_group="INS", impacted_group="CFO", region="Canada", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,fraud"),
        Audit(audit_id="INS-002", audit_name="Underwriting Risk Assessment", audit_type="Owned Audit",
              lead_group="INS", impacted_group="GRM,CFO", region="US", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="RI",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,operational"),
        Audit(audit_id="INS-003", audit_name="Reinsurance Treaty Compliance", audit_type="Owned Audit",
              lead_group="INS", impacted_group="GC,CLAO", region="UK", impacted_region="APAC",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,credit"),
        Audit(audit_id="INS-004", audit_name="Actuarial Model Validation", audit_type="Owned Audit",
              lead_group="INS", impacted_group="CFO,GRM", region="APAC", impacted_region="",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="RI",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,operational"),
        # In-Scope AE (3)
        Audit(audit_id="INS-005", audit_name="Policy Administration System Review", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="INS", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="INS-006", audit_name="IFRS 17 Implementation Controls", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="INS,GRM", region="UK", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="INS-007", audit_name="Fraud Detection — Insurance Claims", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="INS,CLAO", region="Caribbean", impacted_region="",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,aml"),
        # Indirect (4)
        Audit(audit_id="INS-008", audit_name="Catastrophe Modelling Governance", audit_type="Indirect",
              lead_group="GRM", impacted_group="INS,CFO", region="US", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,operational"),
        Audit(audit_id="INS-009", audit_name="Broker Commission Payments Review", audit_type="Indirect",
              lead_group="CFO", impacted_group="INS", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="fraud,operational"),
        Audit(audit_id="INS-010", audit_name="Regulatory Capital Adequacy — INS", audit_type="Indirect",
              lead_group="GC", impacted_group="INS,GRM", region="Canada", impacted_region="",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,credit"),
        Audit(audit_id="INS-011", audit_name="Policyholder Data Management", audit_type="Indirect",
              lead_group="T&O", impacted_group="INS,HR", region="UK", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="INS",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber"),

        # ═══════════════════════════════════════════════════════════════════════
        # PB — Personal Banking  (11 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="PB-001", audit_name="Mortgage Origination Controls", audit_type="Owned Audit",
              lead_group="PB", impacted_group="GRM,CFO", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,operational"),
        Audit(audit_id="PB-002", audit_name="Consumer Lending Decisioning", audit_type="Owned Audit",
              lead_group="PB", impacted_group="GRM", region="Canada", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,compliance"),
        Audit(audit_id="PB-003", audit_name="Branch Cash Handling Procedures", audit_type="Owned Audit",
              lead_group="PB", impacted_group="CFO", region="Caribbean", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="UNSAT", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,operational"),
        Audit(audit_id="PB-004", audit_name="Credit Card Fraud Detection", audit_type="Owned Audit",
              lead_group="PB", impacted_group="GRM,T&O", region="US", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="UNSAT",
              issue_count=5, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,it_cyber"),
        # In-Scope AE (3)
        Audit(audit_id="PB-005", audit_name="Mobile Banking Security Assessment", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="PB", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,fraud"),
        Audit(audit_id="PB-006", audit_name="Consumer Complaint Management", audit_type="In-Scope AE",
              lead_group="CLAO", impacted_group="PB,HR", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="PB-007", audit_name="Retail Credit Loss Provisioning", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="PB,GRM", region="Caribbean", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit"),
        # Indirect (4)
        Audit(audit_id="PB-008", audit_name="ATM Network Resilience", audit_type="Indirect",
              lead_group="T&O", impacted_group="PB", region="Canada", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="PB-009", audit_name="Customer Data Privacy — PB", audit_type="Indirect",
              lead_group="GC", impacted_group="PB,T&O", region="UK", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),
        Audit(audit_id="PB-010", audit_name="AML — Retail Transaction Monitoring", audit_type="Indirect",
              lead_group="GRM", impacted_group="PB,CLAO", region="Canada", impacted_region="",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="PB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,fraud"),
        Audit(audit_id="PB-011", audit_name="Branch Regulatory Compliance", audit_type="Indirect",
              lead_group="CLAO", impacted_group="PB", region="APAC", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="PB",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="compliance"),

        # ═══════════════════════════════════════════════════════════════════════
        # CB — Commercial Banking  (11 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="CB-001", audit_name="Commercial Loan Underwriting", audit_type="Owned Audit",
              lead_group="CB", impacted_group="GRM,CFO", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,operational"),
        Audit(audit_id="CB-002", audit_name="Trade Finance Controls", audit_type="Owned Audit",
              lead_group="CB", impacted_group="GC,CLAO", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,aml,fraud"),
        Audit(audit_id="CB-003", audit_name="Syndicated Lending Review", audit_type="Owned Audit",
              lead_group="CB", impacted_group="GRM", region="US", impacted_region="UK",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,liquidity"),
        Audit(audit_id="CB-004", audit_name="Cash Management Products", audit_type="Owned Audit",
              lead_group="CB", impacted_group="T&O,CFO", region="Caribbean", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,liquidity"),
        # In-Scope AE (3)
        Audit(audit_id="CB-005", audit_name="Commercial Credit Model Validation", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="CB,CFO", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit"),
        Audit(audit_id="CB-006", audit_name="Sanctions Screening — CB Clients", audit_type="In-Scope AE",
              lead_group="CLAO", impacted_group="CB,GRM", region="UK", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="RI",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,compliance"),
        Audit(audit_id="CB-007", audit_name="Payment Processing Controls", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="CB,CFO", region="US", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=1, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),
        # Indirect (4)
        Audit(audit_id="CB-008", audit_name="Real Estate Collateral Valuation", audit_type="Indirect",
              lead_group="CFO", impacted_group="CB,GRM", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit,market"),
        Audit(audit_id="CB-009", audit_name="Loan Covenant Monitoring", audit_type="Indirect",
              lead_group="GRM", impacted_group="CB", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit"),
        Audit(audit_id="CB-010", audit_name="Deposit Product Compliance", audit_type="Indirect",
              lead_group="CLAO", impacted_group="CB", region="Caribbean", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="CB",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="CB-011", audit_name="Third-Party Vendor Risk — CB", audit_type="Indirect",
              lead_group="GC", impacted_group="CB,T&O", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CB",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),

        # ═══════════════════════════════════════════════════════════════════════
        # GC — General Counsel  (10 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="GC-001", audit_name="Litigation Management Process", audit_type="Owned Audit",
              lead_group="GC", impacted_group="CLAO,CFO", region="US", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="GC-002", audit_name="Contract Lifecycle Management", audit_type="Owned Audit",
              lead_group="GC", impacted_group="T&O", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="GC-003", audit_name="Intellectual Property Protection", audit_type="Owned Audit",
              lead_group="GC", impacted_group="HR", region="UK", impacted_region="APAC",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,compliance"),
        Audit(audit_id="GC-004", audit_name="Legal Entity Governance", audit_type="Owned Audit",
              lead_group="GC", impacted_group="CFO,CLAO", region="APAC", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        # In-Scope AE (3)
        Audit(audit_id="GC-005", audit_name="Data Retention & eDiscovery", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="GC,CLAO", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),
        Audit(audit_id="GC-006", audit_name="Regulatory Change Management", audit_type="In-Scope AE",
              lead_group="CLAO", impacted_group="GC,GRM", region="UK", impacted_region="US,Canada",
              status="In Progress", report_status="In Progress", previous_rating="RI", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="GC-007", audit_name="Legal Operations Technology", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="GC", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="NA", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        # Indirect (3)
        Audit(audit_id="GC-008", audit_name="Board & Committee Governance", audit_type="Indirect",
              lead_group="HR", impacted_group="GC,CFO", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="GC-009", audit_name="Outside Counsel Fee Management", audit_type="Indirect",
              lead_group="CFO", impacted_group="GC", region="US", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="GC-010", audit_name="Anti-Bribery & Corruption Controls", audit_type="Indirect",
              lead_group="GRM", impacted_group="GC,CLAO", region="Caribbean", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="GC",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,compliance"),

        # ═══════════════════════════════════════════════════════════════════════
        # GRM — Global Risk Management  (10 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="GRM-001", audit_name="Enterprise Risk Appetite Framework", audit_type="Owned Audit",
              lead_group="GRM", impacted_group="CFO,GC", region="Canada", impacted_region="US,UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,market,credit"),
        Audit(audit_id="GRM-002", audit_name="Stress Testing & Scenario Analysis", audit_type="Owned Audit",
              lead_group="GRM", impacted_group="CFO", region="US", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,liquidity,credit"),
        Audit(audit_id="GRM-003", audit_name="Model Risk Management", audit_type="Owned Audit",
              lead_group="GRM", impacted_group="T&O,CFO", region="UK", impacted_region="US",
              status="In Progress", report_status="In Progress", previous_rating="RI", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,market"),
        Audit(audit_id="GRM-004", audit_name="Operational Risk Event Reporting", audit_type="Owned Audit",
              lead_group="GRM", impacted_group="CLAO", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="UNSAT",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        # In-Scope AE (3)
        Audit(audit_id="GRM-005", audit_name="Risk Data Aggregation & Reporting", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="GRM,CFO", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="GRM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="GRM-006", audit_name="Credit Risk Governance — Enterprise", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="GRM,GC", region="US", impacted_region="UK",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="GRM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="credit"),
        Audit(audit_id="GRM-007", audit_name="Market Risk Limit Framework", audit_type="In-Scope AE",
              lead_group="CFO", impacted_group="GRM,CM", region="UK", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="GRM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,liquidity"),
        # Indirect (3)
        Audit(audit_id="GRM-008", audit_name="Climate Risk Integration", audit_type="Indirect",
              lead_group="GC", impacted_group="GRM,CFO", region="UK", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="NA", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="GRM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="market,compliance"),
        Audit(audit_id="GRM-009", audit_name="Third-Party Risk Assessment", audit_type="Indirect",
              lead_group="T&O", impacted_group="GRM", region="Caribbean", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="GRM",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),
        Audit(audit_id="GRM-010", audit_name="Risk Culture & Awareness Programme", audit_type="Indirect",
              lead_group="HR", impacted_group="GRM,CLAO", region="Canada", impacted_region="APAC",
              status="In Progress", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="GRM",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),

        # ═══════════════════════════════════════════════════════════════════════
        # CLAO — Chief Legal & Administrative Officer  (10 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="CLAO-001", audit_name="Regulatory Obligations Register", audit_type="Owned Audit",
              lead_group="CLAO", impacted_group="GC,GRM", region="Canada", impacted_region="US,UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="CLAO-002", audit_name="Conduct Risk Monitoring", audit_type="Owned Audit",
              lead_group="CLAO", impacted_group="HR,GRM", region="UK", impacted_region="",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,fraud"),
        Audit(audit_id="CLAO-003", audit_name="Privacy Programme Governance", audit_type="Owned Audit",
              lead_group="CLAO", impacted_group="T&O,GC", region="US", impacted_region="APAC",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,it_cyber"),
        Audit(audit_id="CLAO-004", audit_name="Whistleblower Programme Review", audit_type="Owned Audit",
              lead_group="CLAO", impacted_group="HR", region="Caribbean", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,compliance"),
        # In-Scope AE (3)
        Audit(audit_id="CLAO-005", audit_name="Compliance Training Effectiveness", audit_type="In-Scope AE",
              lead_group="HR", impacted_group="CLAO", region="Canada", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="CLAO-006", audit_name="Regulatory Exam Management", audit_type="In-Scope AE",
              lead_group="GC", impacted_group="CLAO,CFO", region="US", impacted_region="UK",
              status="In Progress", report_status="In Progress", previous_rating="RI", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="CLAO-007", audit_name="Surveillance Technology Platform", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="CLAO,GRM", region="UK", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),
        # Indirect (3)
        Audit(audit_id="CLAO-008", audit_name="Financial Crime Controls — Enterprise", audit_type="Indirect",
              lead_group="GRM", impacted_group="CLAO,GC", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,fraud"),
        Audit(audit_id="CLAO-009", audit_name="Sanctions Policy Adherence", audit_type="Indirect",
              lead_group="GRM", impacted_group="CLAO", region="Caribbean", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="aml,compliance"),
        Audit(audit_id="CLAO-010", audit_name="Regulatory Reporting Automation", audit_type="Indirect",
              lead_group="T&O", impacted_group="CLAO,CFO", region="Canada", impacted_region="",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="CLAO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),

        # ═══════════════════════════════════════════════════════════════════════
        # HR — Human Resources  (10 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="HR-001", audit_name="Payroll Processing Controls", audit_type="Owned Audit",
              lead_group="HR", impacted_group="CFO", region="Canada", impacted_region="Caribbean",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,fraud"),
        Audit(audit_id="HR-002", audit_name="Employee Onboarding & Vetting", audit_type="Owned Audit",
              lead_group="HR", impacted_group="CLAO,GRM", region="US", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,operational"),
        Audit(audit_id="HR-003", audit_name="Compensation & Benefits Governance", audit_type="Owned Audit",
              lead_group="HR", impacted_group="CFO,GC", region="UK", impacted_region="",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="HR-004", audit_name="Workforce Planning & Analytics", audit_type="Owned Audit",
              lead_group="HR", impacted_group="T&O", region="APAC", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="NA", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        # In-Scope AE (3)
        Audit(audit_id="HR-005", audit_name="HRIS Platform Security", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="HR", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="HR",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber"),
        Audit(audit_id="HR-006", audit_name="Employee Data Privacy", audit_type="In-Scope AE",
              lead_group="CLAO", impacted_group="HR,T&O", region="UK", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="HR",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,it_cyber"),
        Audit(audit_id="HR-007", audit_name="Labour Law Compliance — Multi-Jurisdiction", audit_type="In-Scope AE",
              lead_group="GC", impacted_group="HR,CLAO", region="Caribbean", impacted_region="Canada,US",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="HR",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance"),
        # Indirect (3)
        Audit(audit_id="HR-008", audit_name="Diversity & Inclusion Programme", audit_type="Indirect",
              lead_group="GC", impacted_group="HR", region="US", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="HR",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="HR-009", audit_name="Health & Safety Compliance", audit_type="Indirect",
              lead_group="CLAO", impacted_group="HR", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="HR",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="HR-010", audit_name="Contractor & Contingent Workforce", audit_type="Indirect",
              lead_group="CFO", impacted_group="HR,GC", region="Canada", impacted_region="",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="HR",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,fraud"),

        # ═══════════════════════════════════════════════════════════════════════
        # CFO — Chief Financial Officer  (11 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="CFO-001", audit_name="Financial Close Process", audit_type="Owned Audit",
              lead_group="CFO", impacted_group="GC,CLAO", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="CFO-002", audit_name="Tax Reporting & Compliance", audit_type="Owned Audit",
              lead_group="CFO", impacted_group="CLAO,GC", region="US", impacted_region="UK,Canada",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="CFO-003", audit_name="Treasury Operations & Liquidity", audit_type="Owned Audit",
              lead_group="CFO", impacted_group="GRM", region="UK", impacted_region="APAC",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="liquidity,market"),
        Audit(audit_id="CFO-004", audit_name="Intercompany Transfer Pricing", audit_type="Owned Audit",
              lead_group="CFO", impacted_group="GC", region="Caribbean", impacted_region="Canada,US",
              status="Complete", report_status="Published", previous_rating="UNSAT", current_rating="RI",
              issue_count=4, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,fraud"),
        # In-Scope AE (3)
        Audit(audit_id="CFO-005", audit_name="ERP System Access Controls", audit_type="In-Scope AE",
              lead_group="T&O", impacted_group="CFO", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="CFO-006", audit_name="Regulatory Capital Computation", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="CFO,GC", region="UK", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="RI",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,credit"),
        Audit(audit_id="CFO-007", audit_name="Financial Consolidation Controls", audit_type="In-Scope AE",
              lead_group="GC", impacted_group="CFO,CLAO", region="APAC", impacted_region="Caribbean",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="NA",
              issue_count=0, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        # Indirect (4)
        Audit(audit_id="CFO-008", audit_name="Accounts Payable Fraud Prevention", audit_type="Indirect",
              lead_group="GRM", impacted_group="CFO", region="US", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="fraud,operational"),
        Audit(audit_id="CFO-009", audit_name="Fixed Asset Management", audit_type="Indirect",
              lead_group="T&O", impacted_group="CFO", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        Audit(audit_id="CFO-010", audit_name="External Audit Coordination", audit_type="Indirect",
              lead_group="GC", impacted_group="CFO,CLAO", region="UK", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=True, quarter="Q2 FY25",
              risk_stripes="compliance"),
        Audit(audit_id="CFO-011", audit_name="Revenue Recognition Controls", audit_type="Indirect",
              lead_group="CLAO", impacted_group="CFO,GRM", region="Caribbean", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="RI", current_rating="RI",
              issue_count=2, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="CFO",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),

        # ═══════════════════════════════════════════════════════════════════════
        # T&O — Technology & Operations  (10 audits)
        # ═══════════════════════════════════════════════════════════════════════
        # Owned (4)
        Audit(audit_id="TO-001", audit_name="Cybersecurity Programme Maturity", audit_type="Owned Audit",
              lead_group="T&O", impacted_group="GRM,GC", region="Canada", impacted_region="US,UK",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="SAT",
              issue_count=2, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber"),
        Audit(audit_id="TO-002", audit_name="Cloud Infrastructure Governance", audit_type="Owned Audit",
              lead_group="T&O", impacted_group="GRM", region="US", impacted_region="APAC",
              status="Complete", report_status="Published", previous_rating="NA", current_rating="RI",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="TO-003", audit_name="Change Management & Release Controls", audit_type="Owned Audit",
              lead_group="T&O", impacted_group="CFO", region="UK", impacted_region="Canada",
              status="In Progress", report_status="In Progress", previous_rating="SAT", current_rating="RI",
              issue_count=4, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        Audit(audit_id="TO-004", audit_name="Data Centre Resilience", audit_type="Owned Audit",
              lead_group="T&O", impacted_group="GRM,CFO", region="APAC", impacted_region="UK",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="UNSAT",
              issue_count=5, digital_rcm="Done", planning_memo="Done", impacted_platform="",
              is_overdue=True, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,operational"),
        # In-Scope AE (3)
        Audit(audit_id="TO-005", audit_name="IT Vendor Management", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="T&O,GC", region="Canada", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=1, digital_rcm="Done", planning_memo="Done", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational,it_cyber"),
        Audit(audit_id="TO-006", audit_name="Identity & Access Management", audit_type="In-Scope AE",
              lead_group="GRM", impacted_group="T&O,CLAO", region="US", impacted_region="UK",
              status="In Progress", report_status="In Progress", previous_rating="RI", current_rating="RI",
              issue_count=3, digital_rcm="Incomplete", planning_memo="Done", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,fraud"),
        Audit(audit_id="TO-007", audit_name="Business Continuity Planning", audit_type="In-Scope AE",
              lead_group="GC", impacted_group="T&O,HR", region="Caribbean", impacted_region="Canada",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="operational"),
        # Indirect (3)
        Audit(audit_id="TO-008", audit_name="Software Licensing Compliance", audit_type="Indirect",
              lead_group="CFO", impacted_group="T&O", region="Canada", impacted_region="",
              status="Complete", report_status="Published", previous_rating="SAT", current_rating="SAT",
              issue_count=0, digital_rcm="Done", planning_memo="Done", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="compliance,operational"),
        Audit(audit_id="TO-009", audit_name="Incident Response & Forensics", audit_type="Indirect",
              lead_group="GRM", impacted_group="T&O,GC", region="UK", impacted_region="US",
              status="Complete", report_status="Published", previous_rating="RI", current_rating="UNSAT",
              issue_count=3, digital_rcm="Done", planning_memo="Done", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,fraud"),
        Audit(audit_id="TO-010", audit_name="API Security & Integration Controls", audit_type="Indirect",
              lead_group="CLAO", impacted_group="T&O,GRM", region="APAC", impacted_region="",
              status="Fieldwork", report_status="In Progress", previous_rating="NA", current_rating="NA",
              issue_count=0, digital_rcm="N/A", planning_memo="N/A", impacted_platform="T&O",
              is_overdue=False, out_of_scope=False, quarter="Q2 FY25",
              risk_stripes="it_cyber,compliance"),
    ]
    session.add_all(audits)


def _seed_issues(session):
    base_date = date(2025, 3, 1)
    issues = [
        # ── CM Issues (23) ─────────────────────────────────────────────────────
        Issue(issue_id="ISS-001", audit_id="CM-001", title="Limit breach escalation not documented", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="J. Smith", days_overdue=0),
        Issue(issue_id="ISS-002", audit_id="CM-001", title="Daily P&L reconciliation gaps", severity="Medium", status="Overdue", due_date=base_date - timedelta(days=5), remediation_owner="J. Smith", days_overdue=5),
        Issue(issue_id="ISS-003", audit_id="CM-001", title="Trader mandate review overdue", severity="High", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="A. Chen", days_overdue=0),
        Issue(issue_id="ISS-004", audit_id="CM-001", title="Risk model validation outstanding", severity="Medium", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="A. Chen", days_overdue=0),
        Issue(issue_id="ISS-005", audit_id="CM-002", title="IPV process not consistently applied", severity="High", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="B. Patel", days_overdue=0),
        Issue(issue_id="ISS-006", audit_id="CM-002", title="Level 3 asset classification inconsistency", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="B. Patel", days_overdue=0),
        Issue(issue_id="ISS-007", audit_id="CM-002", title="Valuation committee minutes incomplete", severity="Low", status="Closed", due_date=base_date - timedelta(days=10), remediation_owner="M. Torres", days_overdue=0),
        Issue(issue_id="ISS-008", audit_id="CM-003", title="Client asset segregation breach", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="R. Kim", days_overdue=0),
        Issue(issue_id="ISS-009", audit_id="CM-003", title="Daily reconciliation failures unresolved", severity="High", status="Overdue", due_date=base_date - timedelta(days=8), remediation_owner="R. Kim", days_overdue=8),
        Issue(issue_id="ISS-010", audit_id="CM-003", title="Margin call processing delays", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="L. Nguyen", days_overdue=0),
        Issue(issue_id="ISS-011", audit_id="CM-003", title="Custody reporting gaps identified", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="L. Nguyen", days_overdue=0),
        Issue(issue_id="ISS-012", audit_id="CM-003", title="Stock lending agreement terms not reviewed", severity="Low", status="Open", due_date=base_date + timedelta(days=60), remediation_owner="P. Williams", days_overdue=0),
        Issue(issue_id="ISS-013", audit_id="CM-004", title="Research distribution list not updated", severity="Low", status="Closed", due_date=base_date - timedelta(days=20), remediation_owner="S. Ahmed", days_overdue=0),
        Issue(issue_id="ISS-014", audit_id="CM-005", title="Pricing model sensitivity testing absent", severity="High", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="D. Foster", days_overdue=0),
        Issue(issue_id="ISS-015", audit_id="CM-005", title="Approval threshold for bespoke instruments", severity="Medium", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="D. Foster", days_overdue=0),
        Issue(issue_id="ISS-016", audit_id="CM-006", title="Nostro account breaks unresolved >30 days", severity="Medium", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="C. Zhang", days_overdue=0),
        Issue(issue_id="ISS-017", audit_id="CM-006", title="CLS settlement netting review overdue", severity="Low", status="Closed", due_date=base_date - timedelta(days=5), remediation_owner="C. Zhang", days_overdue=0),
        Issue(issue_id="ISS-018", audit_id="CM-007", title="Haircut methodology not updated for 18 months", severity="High", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="F. Okafor", days_overdue=0),
        Issue(issue_id="ISS-019", audit_id="CM-007", title="Eligibility criteria applied inconsistently", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="F. Okafor", days_overdue=0),
        Issue(issue_id="ISS-020", audit_id="CM-007", title="Dispute resolution log not maintained", severity="Medium", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="G. Pham", days_overdue=0),
        Issue(issue_id="ISS-021", audit_id="CM-008", title="MiFID II transaction report gaps", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="H. Blanc", days_overdue=0),
        Issue(issue_id="ISS-022", audit_id="CM-008", title="EMIR reconciliation failures", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="H. Blanc", days_overdue=0),
        Issue(issue_id="ISS-023", audit_id="CM-008", title="Dodd-Frank swap reporting latency", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="I. Martins", days_overdue=0),

        # ── WM Issues ──────────────────────────────────────────────────────────
        Issue(issue_id="ISS-024", audit_id="WM-001", title="Suitability questionnaire not updated annually", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="K. Lam", days_overdue=0),
        Issue(issue_id="ISS-025", audit_id="WM-001", title="Risk tolerance mismatch for 12 accounts", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="K. Lam", days_overdue=0),
        Issue(issue_id="ISS-026", audit_id="WM-002", title="Rebalancing threshold drift unmonitored", severity="Medium", status="Closed", due_date=base_date - timedelta(days=15), remediation_owner="N. Roy", days_overdue=0),
        Issue(issue_id="ISS-027", audit_id="WM-003", title="Fee schedule discrepancy in 3 portfolios", severity="High", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="N. Roy", days_overdue=0),
        Issue(issue_id="ISS-028", audit_id="WM-003", title="Billing cycle timing errors", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="T. Okeke", days_overdue=0),
        Issue(issue_id="ISS-029", audit_id="WM-003", title="Client fee disclosure not sent", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="T. Okeke", days_overdue=0),
        Issue(issue_id="ISS-030", audit_id="WM-004", title="KYC refresh overdue for 45 clients", severity="High", status="Overdue", due_date=base_date - timedelta(days=12), remediation_owner="V. Singh", days_overdue=12),
        Issue(issue_id="ISS-031", audit_id="WM-004", title="PEP screening gaps in onboarding", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="V. Singh", days_overdue=0),
        Issue(issue_id="ISS-032", audit_id="WM-004", title="Beneficial ownership records incomplete", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="E. Dubois", days_overdue=0),
        Issue(issue_id="ISS-033", audit_id="WM-004", title="Enhanced due diligence not triggered", severity="High", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="E. Dubois", days_overdue=0),
        Issue(issue_id="ISS-034", audit_id="WM-006", title="Digital onboarding ID verification gaps", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="W. Tan", days_overdue=0),
        Issue(issue_id="ISS-035", audit_id="WM-007", title="Client statement data accuracy errors", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="W. Tan", days_overdue=0),
        Issue(issue_id="ISS-036", audit_id="WM-007", title="Reporting delivery SLA breaches", severity="Low", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="R. Moreno", days_overdue=0),
        Issue(issue_id="ISS-037", audit_id="WM-008", title="STR filing delays identified", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="R. Moreno", days_overdue=0),
        Issue(issue_id="ISS-038", audit_id="WM-008", title="Transaction monitoring rules not calibrated", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="Y. Cho", days_overdue=0),
        Issue(issue_id="ISS-039", audit_id="WM-008", title="Alert backlog exceeding SLA", severity="High", status="Overdue", due_date=base_date - timedelta(days=3), remediation_owner="Y. Cho", days_overdue=3),
        Issue(issue_id="ISS-040", audit_id="WM-010", title="Privacy notice not updated for APAC clients", severity="Low", status="Open", due_date=base_date + timedelta(days=55), remediation_owner="L. Chen", days_overdue=0),
        Issue(issue_id="ISS-041", audit_id="WM-012", title="Product suitability matrix outdated", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="L. Chen", days_overdue=0),
        Issue(issue_id="ISS-042", audit_id="WM-012", title="Governance committee meeting frequency", severity="Low", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="A. Park", days_overdue=0),

        # ── INS Issues ─────────────────────────────────────────────────────────
        Issue(issue_id="ISS-043", audit_id="INS-001", title="Claims adjuster authority limits exceeded", severity="Medium", status="Closed", due_date=base_date - timedelta(days=10), remediation_owner="D. Campbell", days_overdue=0),
        Issue(issue_id="ISS-044", audit_id="INS-002", title="Underwriting guidelines not current", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="D. Campbell", days_overdue=0),
        Issue(issue_id="ISS-045", audit_id="INS-002", title="Risk appetite breach in commercial lines", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="M. Fraser", days_overdue=0),
        Issue(issue_id="ISS-046", audit_id="INS-002", title="Pricing model assumptions stale", severity="High", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="M. Fraser", days_overdue=0),
        Issue(issue_id="ISS-047", audit_id="INS-004", title="Actuarial assumption documentation gaps", severity="High", status="Overdue", due_date=base_date - timedelta(days=6), remediation_owner="S. Gupta", days_overdue=6),
        Issue(issue_id="ISS-048", audit_id="INS-004", title="Reserve adequacy testing frequency", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="S. Gupta", days_overdue=0),
        Issue(issue_id="ISS-049", audit_id="INS-004", title="Model change governance process", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="P. Johal", days_overdue=0),
        Issue(issue_id="ISS-050", audit_id="INS-004", title="Back-testing results not reviewed", severity="Medium", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="P. Johal", days_overdue=0),
        Issue(issue_id="ISS-051", audit_id="INS-005", title="System access review not completed", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="C. Reeves", days_overdue=0),
        Issue(issue_id="ISS-052", audit_id="INS-006", title="IFRS 17 transition adjustments unreconciled", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="C. Reeves", days_overdue=0),
        Issue(issue_id="ISS-053", audit_id="INS-006", title="CSM calculation methodology gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="J. Osei", days_overdue=0),
        Issue(issue_id="ISS-054", audit_id="INS-007", title="Fraudulent claims detection model outdated", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="J. Osei", days_overdue=0),
        Issue(issue_id="ISS-055", audit_id="INS-007", title="SIU referral process not followed", severity="High", status="Overdue", due_date=base_date - timedelta(days=4), remediation_owner="T. Alvarez", days_overdue=4),
        Issue(issue_id="ISS-056", audit_id="INS-007", title="Claims leakage analysis incomplete", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="T. Alvarez", days_overdue=0),
        Issue(issue_id="ISS-057", audit_id="INS-009", title="Commission override approvals missing", severity="Low", status="Closed", due_date=base_date - timedelta(days=8), remediation_owner="B. Nakamura", days_overdue=0),
        Issue(issue_id="ISS-058", audit_id="INS-010", title="Capital calculation spreadsheet errors", severity="High", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="B. Nakamura", days_overdue=0),
        Issue(issue_id="ISS-059", audit_id="INS-010", title="Regulatory filing deadline tracking gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="H. Mendez", days_overdue=0),

        # ── PB Issues ──────────────────────────────────────────────────────────
        Issue(issue_id="ISS-060", audit_id="PB-001", title="Mortgage documentation checklist incomplete", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="F. Leblanc", days_overdue=0),
        Issue(issue_id="ISS-061", audit_id="PB-001", title="Income verification process gaps", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="F. Leblanc", days_overdue=0),
        Issue(issue_id="ISS-062", audit_id="PB-002", title="Credit score override documentation weak", severity="Medium", status="Closed", due_date=base_date - timedelta(days=5), remediation_owner="G. Watts", days_overdue=0),
        Issue(issue_id="ISS-063", audit_id="PB-003", title="Cash vault reconciliation delays", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="G. Watts", days_overdue=0),
        Issue(issue_id="ISS-064", audit_id="PB-003", title="Dual custody procedures not followed", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="I. Baptiste", days_overdue=0),
        Issue(issue_id="ISS-065", audit_id="PB-003", title="Teller shortage reporting inconsistent", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="I. Baptiste", days_overdue=0),
        Issue(issue_id="ISS-066", audit_id="PB-004", title="Fraud rule tuning overdue by 9 months", severity="High", status="Overdue", due_date=base_date - timedelta(days=15), remediation_owner="K. Rivera", days_overdue=15),
        Issue(issue_id="ISS-067", audit_id="PB-004", title="Chargeback processing SLA breach", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="K. Rivera", days_overdue=0),
        Issue(issue_id="ISS-068", audit_id="PB-004", title="Card fraud analytics model drift", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="O. Petrov", days_overdue=0),
        Issue(issue_id="ISS-069", audit_id="PB-004", title="Real-time alert suppression misconfigured", severity="High", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="O. Petrov", days_overdue=0),
        Issue(issue_id="ISS-070", audit_id="PB-004", title="Merchant fraud monitoring gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="A. Shah", days_overdue=0),
        Issue(issue_id="ISS-071", audit_id="PB-005", title="Session timeout setting non-compliant", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="A. Shah", days_overdue=0),
        Issue(issue_id="ISS-072", audit_id="PB-007", title="ECL model parameter calibration outdated", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="D. Hussain", days_overdue=0),
        Issue(issue_id="ISS-073", audit_id="PB-007", title="Stage 2 migration criteria inconsistent", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="D. Hussain", days_overdue=0),
        Issue(issue_id="ISS-074", audit_id="PB-009", title="GDPR data subject request backlog", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="S. Murphy", days_overdue=0),
        Issue(issue_id="ISS-075", audit_id="PB-011", title="Branch compliance checklist gaps", severity="Low", status="Closed", due_date=base_date - timedelta(days=12), remediation_owner="S. Murphy", days_overdue=0),

        # ── CB Issues ──────────────────────────────────────────────────────────
        Issue(issue_id="ISS-076", audit_id="CB-001", title="Credit approval authority exceeded", severity="Medium", status="Closed", due_date=base_date - timedelta(days=7), remediation_owner="R. Bergeron", days_overdue=0),
        Issue(issue_id="ISS-077", audit_id="CB-002", title="Trade finance document verification gaps", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="R. Bergeron", days_overdue=0),
        Issue(issue_id="ISS-078", audit_id="CB-002", title="LC issuance without proper collateral", severity="High", status="Overdue", due_date=base_date - timedelta(days=10), remediation_owner="N. Abdi", days_overdue=10),
        Issue(issue_id="ISS-079", audit_id="CB-002", title="Sanctions screening for trade counterparties", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="N. Abdi", days_overdue=0),
        Issue(issue_id="ISS-080", audit_id="CB-002", title="Documentary collection process weaknesses", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="Q. Fernandez", days_overdue=0),
        Issue(issue_id="ISS-081", audit_id="CB-003", title="Syndicate allocation process undocumented", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="Q. Fernandez", days_overdue=0),
        Issue(issue_id="ISS-082", audit_id="CB-003", title="Agent bank reporting delays", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="U. Jiang", days_overdue=0),
        Issue(issue_id="ISS-083", audit_id="CB-005", title="PD model back-testing failures", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="U. Jiang", days_overdue=0),
        Issue(issue_id="ISS-084", audit_id="CB-005", title="LGD estimation methodology gaps", severity="High", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="X. Kovacs", days_overdue=0),
        Issue(issue_id="ISS-085", audit_id="CB-006", title="Sanctions list update frequency insufficient", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="X. Kovacs", days_overdue=0),
        Issue(issue_id="ISS-086", audit_id="CB-006", title="False positive review backlog", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="Z. Al-Rashid", days_overdue=0),
        Issue(issue_id="ISS-087", audit_id="CB-006", title="Adverse media screening gaps", severity="High", status="Overdue", due_date=base_date - timedelta(days=5), remediation_owner="Z. Al-Rashid", days_overdue=5),
        Issue(issue_id="ISS-088", audit_id="CB-007", title="Payment instruction validation weak", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="W. Dubois", days_overdue=0),
        Issue(issue_id="ISS-089", audit_id="CB-009", title="Covenant breach notification delays", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="W. Dubois", days_overdue=0),
        Issue(issue_id="ISS-090", audit_id="CB-011", title="Vendor SLA monitoring not systematic", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="E. Tremblay", days_overdue=0),

        # ── GC Issues ──────────────────────────────────────────────────────────
        Issue(issue_id="ISS-091", audit_id="GC-001", title="Litigation reserve estimation inconsistent", severity="Medium", status="Closed", due_date=base_date - timedelta(days=8), remediation_owner="M. Brooks", days_overdue=0),
        Issue(issue_id="ISS-092", audit_id="GC-002", title="Contract renewal tracking gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="M. Brooks", days_overdue=0),
        Issue(issue_id="ISS-093", audit_id="GC-002", title="Template clause library not updated", severity="Low", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="P. Ingram", days_overdue=0),
        Issue(issue_id="ISS-094", audit_id="GC-004", title="Entity register not reconciled to regulator", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="P. Ingram", days_overdue=0),
        Issue(issue_id="ISS-095", audit_id="GC-004", title="Director appointment filings delayed", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="C. Dupont", days_overdue=0),
        Issue(issue_id="ISS-096", audit_id="GC-005", title="eDiscovery hold notice process gaps", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="C. Dupont", days_overdue=0),
        Issue(issue_id="ISS-097", audit_id="GC-006", title="Regulatory change impact assessment delayed", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="H. Volkov", days_overdue=0),
        Issue(issue_id="ISS-098", audit_id="GC-006", title="Change implementation tracking incomplete", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="H. Volkov", days_overdue=0),
        Issue(issue_id="ISS-099", audit_id="GC-009", title="Invoice approval workflow bypass", severity="Low", status="Closed", due_date=base_date - timedelta(days=15), remediation_owner="J. Sato", days_overdue=0),
        Issue(issue_id="ISS-100", audit_id="GC-010", title="Bribery risk assessment not enterprise-wide", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="J. Sato", days_overdue=0),
        Issue(issue_id="ISS-101", audit_id="GC-010", title="Gift and entertainment policy breaches", severity="High", status="Overdue", due_date=base_date - timedelta(days=7), remediation_owner="A. Nowak", days_overdue=7),
        Issue(issue_id="ISS-102", audit_id="GC-010", title="Third-party due diligence not completed", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="A. Nowak", days_overdue=0),

        # ── GRM Issues ─────────────────────────────────────────────────────────
        Issue(issue_id="ISS-103", audit_id="GRM-001", title="Risk appetite statement not board-approved", severity="Medium", status="Closed", due_date=base_date - timedelta(days=10), remediation_owner="T. Eriksen", days_overdue=0),
        Issue(issue_id="ISS-104", audit_id="GRM-002", title="Stress scenario calibration not updated", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="T. Eriksen", days_overdue=0),
        Issue(issue_id="ISS-105", audit_id="GRM-002", title="Reverse stress test not conducted", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="V. Desai", days_overdue=0),
        Issue(issue_id="ISS-106", audit_id="GRM-003", title="Model inventory incomplete", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="V. Desai", days_overdue=0),
        Issue(issue_id="ISS-107", audit_id="GRM-003", title="Model validation backlog exceeds policy", severity="High", status="Overdue", due_date=base_date - timedelta(days=9), remediation_owner="L. Bergstrom", days_overdue=9),
        Issue(issue_id="ISS-108", audit_id="GRM-003", title="Model risk reporting frequency inadequate", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="L. Bergstrom", days_overdue=0),
        Issue(issue_id="ISS-109", audit_id="GRM-004", title="Loss event reporting threshold too high", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="R. Gagnon", days_overdue=0),
        Issue(issue_id="ISS-110", audit_id="GRM-004", title="Root cause analysis not conducted", severity="High", status="Overdue", due_date=base_date - timedelta(days=14), remediation_owner="R. Gagnon", days_overdue=14),
        Issue(issue_id="ISS-111", audit_id="GRM-004", title="Key risk indicator thresholds not calibrated", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="N. Salazar", days_overdue=0),
        Issue(issue_id="ISS-112", audit_id="GRM-004", title="Scenario analysis methodology documentation", severity="Medium", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="N. Salazar", days_overdue=0),
        Issue(issue_id="ISS-113", audit_id="GRM-005", title="Data lineage mapping incomplete", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="F. Lavoie", days_overdue=0),
        Issue(issue_id="ISS-114", audit_id="GRM-006", title="Credit committee governance gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="F. Lavoie", days_overdue=0),
        Issue(issue_id="ISS-115", audit_id="GRM-006", title="Concentration risk limits not enforced", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="D. Okonkwo", days_overdue=0),
        Issue(issue_id="ISS-116", audit_id="GRM-007", title="VaR limit breach escalation process", severity="Medium", status="Closed", due_date=base_date - timedelta(days=5), remediation_owner="D. Okonkwo", days_overdue=0),
        Issue(issue_id="ISS-117", audit_id="GRM-009", title="Third-party risk register not current", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="B. Haddad", days_overdue=0),
        Issue(issue_id="ISS-118", audit_id="GRM-009", title="Vendor exit strategy not documented", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="B. Haddad", days_overdue=0),

        # ── CLAO Issues ────────────────────────────────────────────────────────
        Issue(issue_id="ISS-119", audit_id="CLAO-001", title="Obligation register update frequency gap", severity="Low", status="Closed", due_date=base_date - timedelta(days=12), remediation_owner="S. Tremblay", days_overdue=0),
        Issue(issue_id="ISS-120", audit_id="CLAO-002", title="Conduct risk MI not shared with board", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="S. Tremblay", days_overdue=0),
        Issue(issue_id="ISS-121", audit_id="CLAO-002", title="Employee attestation completion rate low", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="M. Aziz", days_overdue=0),
        Issue(issue_id="ISS-122", audit_id="CLAO-003", title="Privacy impact assessment not completed", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="M. Aziz", days_overdue=0),
        Issue(issue_id="ISS-123", audit_id="CLAO-003", title="Data breach notification SLA missed", severity="High", status="Overdue", due_date=base_date - timedelta(days=6), remediation_owner="J. Fletcher", days_overdue=6),
        Issue(issue_id="ISS-124", audit_id="CLAO-003", title="Consent management platform gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="J. Fletcher", days_overdue=0),
        Issue(issue_id="ISS-125", audit_id="CLAO-005", title="Training completion tracking inaccurate", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="E. Marchand", days_overdue=0),
        Issue(issue_id="ISS-126", audit_id="CLAO-006", title="Exam finding remediation tracking gaps", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="E. Marchand", days_overdue=0),
        Issue(issue_id="ISS-127", audit_id="CLAO-006", title="MRA response timeliness", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="G. Popov", days_overdue=0),
        Issue(issue_id="ISS-128", audit_id="CLAO-007", title="Surveillance alert tuning not reviewed", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="G. Popov", days_overdue=0),
        Issue(issue_id="ISS-129", audit_id="CLAO-007", title="Communication monitoring coverage gaps", severity="High", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="W. Ibrahim", days_overdue=0),
        Issue(issue_id="ISS-130", audit_id="CLAO-007", title="Surveillance data retention non-compliant", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="W. Ibrahim", days_overdue=0),
        Issue(issue_id="ISS-131", audit_id="CLAO-008", title="Financial crime risk assessment scope narrow", severity="Medium", status="Closed", due_date=base_date - timedelta(days=8), remediation_owner="C. Bouchard", days_overdue=0),
        Issue(issue_id="ISS-132", audit_id="CLAO-009", title="Sanctions screening system update lag", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="C. Bouchard", days_overdue=0),
        Issue(issue_id="ISS-133", audit_id="CLAO-009", title="Escalation protocol not followed", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="O. Ndiaye", days_overdue=0),

        # ── HR Issues ──────────────────────────────────────────────────────────
        Issue(issue_id="ISS-134", audit_id="HR-001", title="Payroll exception report not reviewed", severity="Medium", status="Closed", due_date=base_date - timedelta(days=10), remediation_owner="L. Côté", days_overdue=0),
        Issue(issue_id="ISS-135", audit_id="HR-002", title="Background check completion delays", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="L. Côté", days_overdue=0),
        Issue(issue_id="ISS-136", audit_id="HR-002", title="Reference verification gaps in 8 hires", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="P. Santos", days_overdue=0),
        Issue(issue_id="ISS-137", audit_id="HR-005", title="Privileged access to HRIS not reviewed", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="P. Santos", days_overdue=0),
        Issue(issue_id="ISS-138", audit_id="HR-006", title="Employee data retention exceeds policy", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="T. McBride", days_overdue=0),
        Issue(issue_id="ISS-139", audit_id="HR-007", title="Employment law update tracking gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="T. McBride", days_overdue=0),
        Issue(issue_id="ISS-140", audit_id="HR-007", title="Multi-jurisdiction compliance matrix outdated", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="R. Larsson", days_overdue=0),
        Issue(issue_id="ISS-141", audit_id="HR-009", title="Workplace safety inspection overdue", severity="Low", status="Closed", due_date=base_date - timedelta(days=15), remediation_owner="R. Larsson", days_overdue=0),

        # ── CFO Issues ─────────────────────────────────────────────────────────
        Issue(issue_id="ISS-142", audit_id="CFO-001", title="Month-end close checklist gaps", severity="Low", status="Closed", due_date=base_date - timedelta(days=5), remediation_owner="A. Beaulieu", days_overdue=0),
        Issue(issue_id="ISS-143", audit_id="CFO-002", title="Transfer pricing documentation not current", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="A. Beaulieu", days_overdue=0),
        Issue(issue_id="ISS-144", audit_id="CFO-002", title="Tax provision reconciliation differences", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="K. Fontaine", days_overdue=0),
        Issue(issue_id="ISS-145", audit_id="CFO-003", title="Liquidity buffer calculation methodology", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="K. Fontaine", days_overdue=0),
        Issue(issue_id="ISS-146", audit_id="CFO-003", title="Intraday liquidity monitoring gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="S. Beaumont", days_overdue=0),
        Issue(issue_id="ISS-147", audit_id="CFO-003", title="Contingency funding plan not tested", severity="High", status="Overdue", due_date=base_date - timedelta(days=8), remediation_owner="S. Beaumont", days_overdue=8),
        Issue(issue_id="ISS-148", audit_id="CFO-004", title="Intercompany pricing not at arm's length", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="D. Arsenault", days_overdue=0),
        Issue(issue_id="ISS-149", audit_id="CFO-004", title="Country-by-country reporting gaps", severity="High", status="Overdue", due_date=base_date - timedelta(days=11), remediation_owner="D. Arsenault", days_overdue=11),
        Issue(issue_id="ISS-150", audit_id="CFO-004", title="Permanent establishment risk assessment", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="V. Pelletier", days_overdue=0),
        Issue(issue_id="ISS-151", audit_id="CFO-004", title="Withholding tax compliance monitoring", severity="Medium", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="V. Pelletier", days_overdue=0),
        Issue(issue_id="ISS-152", audit_id="CFO-005", title="SOD conflict in ERP payment module", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="J. Gagné", days_overdue=0),
        Issue(issue_id="ISS-153", audit_id="CFO-006", title="RWA calculation adjustment process", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="J. Gagné", days_overdue=0),
        Issue(issue_id="ISS-154", audit_id="CFO-006", title="Capital adequacy reporting delays", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="M. Hébert", days_overdue=0),
        Issue(issue_id="ISS-155", audit_id="CFO-008", title="Duplicate payment detection gaps", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="M. Hébert", days_overdue=0),
        Issue(issue_id="ISS-156", audit_id="CFO-008", title="Vendor master data integrity issues", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="L. Girard", days_overdue=0),
        Issue(issue_id="ISS-157", audit_id="CFO-008", title="Ghost vendor detection controls absent", severity="High", status="Overdue", due_date=base_date - timedelta(days=6), remediation_owner="L. Girard", days_overdue=6),
        Issue(issue_id="ISS-158", audit_id="CFO-010", title="External audit finding follow-up gaps", severity="Low", status="Closed", due_date=base_date - timedelta(days=20), remediation_owner="B. Cloutier", days_overdue=0),
        Issue(issue_id="ISS-159", audit_id="CFO-011", title="Revenue cut-off testing exceptions", severity="Medium", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="B. Cloutier", days_overdue=0),
        Issue(issue_id="ISS-160", audit_id="CFO-011", title="Contract modification accounting gaps", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="N. Boucher", days_overdue=0),

        # ── T&O Issues ─────────────────────────────────────────────────────────
        Issue(issue_id="ISS-161", audit_id="TO-001", title="Penetration test finding remediation lag", severity="Medium", status="Open", due_date=base_date + timedelta(days=20), remediation_owner="E. Gauthier", days_overdue=0),
        Issue(issue_id="ISS-162", audit_id="TO-001", title="Security awareness training completion gap", severity="Low", status="Closed", due_date=base_date - timedelta(days=8), remediation_owner="E. Gauthier", days_overdue=0),
        Issue(issue_id="ISS-163", audit_id="TO-002", title="Cloud workload misconfigurations detected", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="J. Perron", days_overdue=0),
        Issue(issue_id="ISS-164", audit_id="TO-002", title="Multi-cloud governance framework gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=28), remediation_owner="J. Perron", days_overdue=0),
        Issue(issue_id="ISS-165", audit_id="TO-002", title="Cloud cost management controls absent", severity="Low", status="Open", due_date=base_date + timedelta(days=45), remediation_owner="H. Desjardins", days_overdue=0),
        Issue(issue_id="ISS-166", audit_id="TO-003", title="Emergency change process not followed", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="H. Desjardins", days_overdue=0),
        Issue(issue_id="ISS-167", audit_id="TO-003", title="Release rollback procedures not tested", severity="High", status="Overdue", due_date=base_date - timedelta(days=5), remediation_owner="C. Thibault", days_overdue=5),
        Issue(issue_id="ISS-168", audit_id="TO-003", title="Change advisory board meeting minutes gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="C. Thibault", days_overdue=0),
        Issue(issue_id="ISS-169", audit_id="TO-003", title="Automated testing coverage below threshold", severity="Medium", status="Open", due_date=base_date + timedelta(days=35), remediation_owner="P. Lévesque", days_overdue=0),
        Issue(issue_id="ISS-170", audit_id="TO-004", title="DR failover testing not conducted annually", severity="High", status="Overdue", due_date=base_date - timedelta(days=20), remediation_owner="P. Lévesque", days_overdue=20),
        Issue(issue_id="ISS-171", audit_id="TO-004", title="UPS capacity assessment overdue", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="F. Bélanger", days_overdue=0),
        Issue(issue_id="ISS-172", audit_id="TO-004", title="Physical security access review gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=25), remediation_owner="F. Bélanger", days_overdue=0),
        Issue(issue_id="ISS-173", audit_id="TO-004", title="Environmental monitoring alerts not configured", severity="High", status="Open", due_date=base_date + timedelta(days=15), remediation_owner="S. Nadeau", days_overdue=0),
        Issue(issue_id="ISS-174", audit_id="TO-004", title="Cooling system redundancy insufficient", severity="Medium", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="S. Nadeau", days_overdue=0),
        Issue(issue_id="ISS-175", audit_id="TO-005", title="Vendor risk tier classification not applied", severity="Low", status="Open", due_date=base_date + timedelta(days=50), remediation_owner="L. Rodrigue", days_overdue=0),
        Issue(issue_id="ISS-176", audit_id="TO-006", title="Orphaned accounts detected in AD", severity="High", status="Open", due_date=base_date + timedelta(days=8), remediation_owner="L. Rodrigue", days_overdue=0),
        Issue(issue_id="ISS-177", audit_id="TO-006", title="MFA not enforced for VPN access", severity="High", status="Open", due_date=base_date + timedelta(days=12), remediation_owner="G. Caron", days_overdue=0),
        Issue(issue_id="ISS-178", audit_id="TO-006", title="Privileged access review overdue by 6 months", severity="High", status="Overdue", due_date=base_date - timedelta(days=10), remediation_owner="G. Caron", days_overdue=10),
        Issue(issue_id="ISS-179", audit_id="TO-009", title="Incident response playbook not updated", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="D. Paquette", days_overdue=0),
        Issue(issue_id="ISS-180", audit_id="TO-009", title="Forensic evidence handling gaps", severity="High", status="Open", due_date=base_date + timedelta(days=18), remediation_owner="D. Paquette", days_overdue=0),
        Issue(issue_id="ISS-181", audit_id="TO-009", title="Post-incident review not conducted", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="R. Fournier", days_overdue=0),

        # ── CM additional issues for indirect audits ───────────────────────────
        Issue(issue_id="ISS-182", audit_id="CM-009", title="AML alert investigation backlog", severity="High", status="Closed", due_date=base_date - timedelta(days=3), remediation_owner="T. Miller", days_overdue=0),
        Issue(issue_id="ISS-183", audit_id="CM-012", title="Insider list maintenance gaps", severity="Medium", status="Open", due_date=base_date + timedelta(days=22), remediation_owner="T. Miller", days_overdue=0),
        Issue(issue_id="ISS-184", audit_id="CM-012", title="Pre-clearance policy not enforced", severity="High", status="Open", due_date=base_date + timedelta(days=10), remediation_owner="K. Brown", days_overdue=0),
        Issue(issue_id="ISS-185", audit_id="CM-013", title="ORM self-assessment not completed", severity="Medium", status="Open", due_date=base_date + timedelta(days=30), remediation_owner="K. Brown", days_overdue=0),
        Issue(issue_id="ISS-186", audit_id="CM-014", title="Market data vendor contract review overdue", severity="Low", status="Open", due_date=base_date + timedelta(days=40), remediation_owner="A. Watson", days_overdue=0),
    ]
    session.add_all(issues)


def _seed_adjustments(session):
    adjustments = [
        Adjustment(adj_id="ADJ-011", audit_id="CM-001", adj_type="Type 1 \u2013 Tag Correction",
                   field_being_adjusted="Regions in Scope", from_value="US only",
                   to_value="US + UK", reason_code="SC \u2013 Scope Clarification",
                   supporting_note="Audit covered UK entities per engagement letter section 2.3.",
                   evidence_ref="CM-AUD-2025-Q2 engagement letter, section 2.3",
                   submitted_by="CM Platform", submitted_date="2025-05-01", status="Approved"),
        Adjustment(adj_id="ADJ-012", audit_id="CM-003", adj_type="Type 2 \u2013 Coverage Claim",
                   field_being_adjusted="Impacted Platform", from_value="Not tagged",
                   to_value="CM tagged", reason_code="MA \u2013 Methodology Alignment",
                   supporting_note="CM named as impacted business in T&O audit scope section 4.",
                   evidence_ref="T&O audit report section 4, issue log ISS-018",
                   submitted_by="CM Platform", submitted_date="2025-05-03", status="Pending"),
    ]
    session.add_all(adjustments)


# ── Issue Commentary CRUD ─────────────────────────────────────────────────────

def db_get_commentary(quarter: str) -> list:
    """Return all commentary entries for a quarter, oldest first."""
    session = SessionLocal()
    try:
        rows = (
            session.query(IssueCommentary)
            .filter(IssueCommentary.quarter == quarter)
            .order_by(IssueCommentary.posted_at)
            .all()
        )
        return [
            {
                "entry_id":  r.entry_id,
                "quarter":   r.quarter,
                "section":   r.section,
                "text":      r.text,
                "author":    r.author,
                "posted_at": r.posted_at,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_save_commentary(entry: dict) -> None:
    session = SessionLocal()
    try:
        session.add(IssueCommentary(
            entry_id=entry["entry_id"],
            quarter=entry["quarter"],
            section=entry["section"],
            text=entry["text"],
            author=entry["author"],
            posted_at=entry["posted_at"],
        ))
        session.commit()
    finally:
        session.close()


def db_delete_commentary(entry_id: str) -> None:
    session = SessionLocal()
    try:
        session.query(IssueCommentary).filter(
            IssueCommentary.entry_id == entry_id
        ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


# ── Control Environment CRUD (Platform view — AU level) ───────────────────────

def db_get_control_environment(platforms: list = None) -> list:
    """Return AU-level CE data filtered by platforms. Used by Platform view."""
    session = SessionLocal()
    try:
        query = session.query(ControlEnvironment)
        if platforms:
            query = query.filter(ControlEnvironment.platform.in_(platforms))
        rows = query.order_by(ControlEnvironment.platform, ControlEnvironment.auditable_unit).all()
        return [
            {
                "au_id": r.au_id,
                "platform": r.platform,
                "auditable_unit": r.auditable_unit,
                "entities": r.entities,
                "ce_rating": r.ce_rating,
                "trend": r.trend,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_update_ce_rating(au_id: str, ce_rating: str, trend: str) -> None:
    """Update CE rating and trend for an auditable unit (Platform view)."""
    session = SessionLocal()
    try:
        session.query(ControlEnvironment).filter(
            ControlEnvironment.au_id == au_id
        ).update(
            {"ce_rating": ce_rating, "trend": trend},
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


# ── Control Environment CRUD (Regional view — platform level) ─────────────────

def db_get_ce_regional(regions: list = None) -> list:
    """Return platform-level CE data filtered by regions. Used by Regional view."""
    session = SessionLocal()
    try:
        query = session.query(ControlEnvironmentRegion)
        if regions:
            query = query.filter(ControlEnvironmentRegion.region.in_(regions))
        rows = query.order_by(ControlEnvironmentRegion.region, ControlEnvironmentRegion.platform).all()
        return [
            {
                "rec_id": r.rec_id,
                "platform": r.platform,
                "region": r.region,
                "ce_rating": r.ce_rating,
                "trend": r.trend,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_update_ce_regional(rec_id: str, ce_rating: str, trend: str) -> None:
    """Update CE rating and trend for a platform-region record (Regional view)."""
    session = SessionLocal()
    try:
        session.query(ControlEnvironmentRegion).filter(
            ControlEnvironmentRegion.rec_id == rec_id
        ).update(
            {"ce_rating": ce_rating, "trend": trend},
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


def db_get_ce_commentary(platform: str) -> list:
    """Return all CE commentary for a platform."""
    session = SessionLocal()
    try:
        rows = (
            session.query(CECommentary)
            .filter(CECommentary.platform == platform)
            .order_by(CECommentary.posted_at)
            .all()
        )
        return [
            {
                "entry_id": r.entry_id,
                "platform": r.platform,
                "text": r.text,
                "author": r.author,
                "posted_at": r.posted_at,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_save_ce_commentary(entry: dict) -> None:
    """Save a CE commentary entry."""
    session = SessionLocal()
    try:
        session.add(CECommentary(
            entry_id=entry["entry_id"],
            platform=entry["platform"],
            text=entry["text"],
            author=entry["author"],
            posted_at=entry["posted_at"],
        ))
        session.commit()
    finally:
        session.close()


def db_delete_ce_commentary(entry_id: str) -> None:
    """Delete a CE commentary entry."""
    session = SessionLocal()
    try:
        session.query(CECommentary).filter(
            CECommentary.entry_id == entry_id
        ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def _seed_control_environment(session):
    """Seed AU-level CE data (Platform view)."""
    from data.mock_data import get_control_environment_seed
    for ce in get_control_environment_seed():
        session.add(ControlEnvironment(
            au_id=ce["au_id"],
            platform=ce["platform"],
            auditable_unit=ce["auditable_unit"],
            entities=ce["entities"],
            ce_rating=ce["ce_rating"],
            trend=ce["trend"],
        ))


def _seed_control_environment_region(session):
    """Seed platform-level CE data per region (Regional view)."""
    from data.mock_data import get_ce_region_seed
    for rec in get_ce_region_seed():
        session.add(ControlEnvironmentRegion(
            rec_id=rec["rec_id"],
            platform=rec["platform"],
            region=rec["region"],
            ce_rating=rec["ce_rating"],
            trend=rec["trend"],
        ))
