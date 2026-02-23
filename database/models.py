"""Data Models for AI CRM - Local Storage"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import uuid


def generate_id() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())


def now() -> str:
    """Get current ISO timestamp"""
    return datetime.now().isoformat()


@dataclass
class Company:
    id: str = field(default_factory=generate_id)
    name: str = ""
    domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    enrichment_data: Optional[Dict] = None
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Contact:
    id: str = field(default_factory=generate_id)
    company_id: Optional[str] = None
    email: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    job_level: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    lead_score: int = 0
    lead_status: str = "new"
    lead_source: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    last_contact_at: Optional[str] = None
    enrichment_data: Optional[Dict] = None
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Deal:
    id: str = field(default_factory=generate_id)
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    name: str = ""
    value: float = 0
    stage: str = "prospecting"
    probability: int = 50
    health_score: int = 50
    is_stalled: bool = False
    risk_factors: Optional[List[str]] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    stage_changed_at: str = field(default_factory=now)
    expected_close_date: Optional[str] = None
    actual_close_date: Optional[str] = None
    owner_id: Optional[str] = None
    notes: Optional[str] = None
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Customer:
    id: str = field(default_factory=generate_id)
    company_id: Optional[str] = None
    plan: Optional[str] = None
    mrr: float = 0
    arr: float = 0
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    health_score: int = 50
    churn_risk: str = "low"
    churn_probability: int = 0
    last_login_at: Optional[str] = None
    logins_per_week: int = 0
    features_used: int = 0
    total_features: int = 10
    license_usage_percent: int = 0
    daily_active_users: int = 0
    support_tickets_30d: int = 0
    critical_tickets_open: int = 0
    avg_resolution_hours: int = 24
    csat_score: float = 0
    nps_score: int = 0
    last_payment_at: Optional[str] = None
    payment_delays: int = 0
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Email:
    id: str = field(default_factory=generate_id)
    contact_id: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    direction: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[int] = None
    emotion: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    draft_response: Optional[str] = None
    response_sent: bool = False
    received_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str = field(default_factory=now)
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Meeting:
    id: str = field(default_factory=generate_id)
    deal_id: Optional[str] = None
    title: str = ""
    meeting_type: Optional[str] = None
    scheduled_at: str = ""
    duration_minutes: int = 30
    location: Optional[str] = None
    attendees: Optional[List[Dict]] = None
    agenda: Optional[Dict] = None
    prep_materials: Optional[Dict] = None
    context: Optional[Dict] = None
    notes: Optional[str] = None
    followup_tasks: Optional[Dict] = None
    recording_url: Optional[str] = None
    status: str = "scheduled"
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Activity:
    id: str = field(default_factory=generate_id)
    contact_id: Optional[str] = None
    deal_id: Optional[str] = None
    activity_type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    assigned_to: Optional[str] = None
    completed: bool = False
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = field(default_factory=now)
    custom_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentLog:
    id: str = field(default_factory=generate_id)
    agent_name: str = ""
    activity_type: Optional[str] = None
    details: Optional[Dict] = None
    created_at: str = field(default_factory=now)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentEvent:
    id: str = field(default_factory=generate_id)
    event_type: str = ""
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None
    payload: Optional[Dict] = None
    processed: bool = False
    created_at: str = field(default_factory=now)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MetricsDaily:
    id: str = field(default_factory=generate_id)
    metric_date: str = ""
    leads_total: int = 0
    leads_qualified: int = 0
    deals_created: int = 0
    deals_won: int = 0
    deals_lost: int = 0
    revenue_won: float = 0
    customers_total: int = 0
    customers_churned: int = 0
    mrr_total: float = 0
    arr_total: float = 0
    pipeline_value: float = 0
    avg_deal_size: float = 0
    avg_sales_cycle_days: int = 0
    avg_health_score: int = 0
    avg_nps_score: int = 0
    avg_csat_score: float = 0
    created_at: str = field(default_factory=now)
    
    def to_dict(self) -> Dict:
        return asdict(self)
