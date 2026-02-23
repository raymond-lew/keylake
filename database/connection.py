"""Local Storage Database for AI CRM with Mock Data and Full CRUD Operations"""

import json
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid
import random


class MockDataGenerator:
    """Generate realistic mock data for the CRM"""
    
    FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", 
                   "Michael", "Linda", "William", "Elizabeth", "David", "Barbara",
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
                   "Charles", "Betty", "Christopher", "Lisa", "Daniel", "Nancy",
                   "Matthew", "Margaret", "Anthony", "Sandra", "Mark", "Ashley"]
    
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
                  "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
                  "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
                  "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    COMPANIES = [
        ("TechCorp Solutions", "Technology", "51-200", "$10M-$50M"),
        ("Global Innovations Inc", "Software", "201-500", "$50M-$100M"),
        ("DataFlow Systems", "Data Analytics", "11-50", "$5M-$10M"),
        ("CloudNine Technologies", "Cloud Services", "51-200", "$10M-$50M"),
        ("SmartBiz Platform", "SaaS", "11-50", "$1M-$5M"),
        ("Enterprise Dynamics", "Enterprise Software", "501-1000", "$100M-$500M"),
        ("StartupHub", "Incubator", "1-10", "$0-$1M"),
        ("MegaCorp Industries", "Manufacturing", "1001-5000", "$500M+"),
        ("Digital First Media", "Marketing", "51-200", "$10M-$50M"),
        ("FinanceFlow", "FinTech", "201-500", "$50M-$100M"),
        ("HealthTech Pro", "Healthcare", "51-200", "$10M-$50M"),
        ("EduLearn Platform", "EdTech", "11-50", "$5M-$10M"),
        ("RetailMax", "E-commerce", "201-500", "$50M-$100M"),
        ("LogistiChain", "Logistics", "501-1000", "$100M-$500M"),
        ("GreenEnergy Solutions", "Clean Energy", "51-200", "$10M-$50M"),
    ]
    
    JOB_TITLES = [
        "CEO", "CTO", "CFO", "COO", "VP of Sales", "VP of Marketing",
        "Director of Engineering", "Head of Product", "Sales Manager",
        "Marketing Director", "Business Development Manager", "Account Executive",
        "Product Manager", "Engineering Manager", "Customer Success Manager",
        "Operations Director", "Chief Revenue Officer", "Head of Growth"
    ]
    
    DEAL_STAGES = ["prospecting", "qualification", "proposal", "negotiation", 
                   "closed_won", "closed_lost"]
    
    EMAIL_SUBJECTS = [
        "Following up on our conversation",
        "Quick question about your product",
        "Partnership opportunity",
        "Demo request",
        "Pricing inquiry",
        "Implementation timeline",
        "Contract renewal discussion",
        "Feature request",
        "Support issue - urgent",
        "Meeting follow-up",
        "Proposal review",
        "Next steps",
        "Introduction from referral",
        "Checking in",
        "Quarterly business review"
    ]
    
    MEETING_TYPES = ["demo", "call", "discovery", "negotiation", "check-in", "other"]
    
    @classmethod
    def generate_id(cls) -> str:
        return str(uuid.uuid4())
    
    @classmethod
    def generate_company(cls, index: int = 0) -> Dict:
        name, industry, size, revenue = random.choice(cls.COMPANIES)
        domain = name.lower().replace(" ", "").replace(".", "") + ".com"
        
        return {
            "id": cls.generate_id(),
            "name": name,
            "domain": domain,
            "industry": industry,
            "company_size": size,
            "revenue_range": revenue,
            "location": random.choice(["San Francisco, CA", "New York, NY", "Austin, TX", 
                                       "Seattle, WA", "Boston, MA", "Chicago, IL"]),
            "timezone": "America/Los_Angeles",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "enrichment_data": None,
            "custom_metadata": None
        }
    
    @classmethod
    def generate_contact(cls, company_id: str, company_name: str) -> Dict:
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        
        return {
            "id": cls.generate_id(),
            "company_id": company_id,
            "email": f"{first_name.lower()}.{last_name.lower()}@{company_name.lower().replace(' ', '')}.com",
            "first_name": first_name,
            "last_name": last_name,
            "job_title": random.choice(cls.JOB_TITLES),
            "job_level": random.choice(["C-Level", "VP", "Director", "Manager", "Individual Contributor"]),
            "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "linkedin_url": f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}",
            "lead_score": random.randint(20, 95),
            "lead_status": random.choice(["new", "qualified", "contacted", "qualified", "qualified"]),
            "lead_source": random.choice(["Website", "Referral", "Cold Outreach", "Event", "LinkedIn"]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_contact_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "enrichment_data": None,
            "custom_metadata": None
        }
    
    @classmethod
    def generate_deal(cls, company_id: str, contact_id: str, company_name: str) -> Dict:
        stage = random.choice(cls.DEAL_STAGES)
        value = random.choice([5000, 10000, 25000, 50000, 75000, 100000, 150000, 250000])
        
        probability_map = {
            "prospecting": 20,
            "qualification": 40,
            "proposal": 60,
            "negotiation": 80,
            "closed_won": 100,
            "closed_lost": 0
        }
        
        health_score = random.randint(40, 95) if stage not in ["closed_lost"] else random.randint(20, 50)
        
        return {
            "id": cls.generate_id(),
            "company_id": company_id,
            "contact_id": contact_id,
            "name": f"{company_name} - {random.choice(['Enterprise', 'Professional', 'Starter'])} Deal",
            "value": value,
            "stage": stage,
            "probability": probability_map.get(stage, 50),
            "health_score": health_score,
            "is_stalled": random.choice([True, False, False, False]),
            "risk_factors": random.choice([None, ["Budget concerns", "Timeline pressure"], 
                                          ["Competitor evaluation", "Decision maker not engaged"]]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stage_changed_at": datetime.now().isoformat(),
            "expected_close_date": (date.today() + timedelta(days=random.randint(-30, 90))).isoformat(),
            "actual_close_date": datetime.now().isoformat() if stage in ["closed_won", "closed_lost"] else None,
            "owner_id": cls.generate_id(),
            "notes": "Key stakeholder identified. Technical evaluation in progress." if stage == "negotiation" else None,
            "custom_metadata": None
        }
    
    @classmethod
    def generate_customer(cls, company_id: str, company_name: str) -> Dict:
        plan = random.choice(["Starter", "Professional", "Enterprise", "Enterprise Plus"])
        mrr_map = {"Starter": 499, "Professional": 1499, "Enterprise": 4999, "Enterprise Plus": 9999}
        mrr = mrr_map.get(plan, 999)
        
        health_score = random.randint(50, 95)
        churn_risk = "low" if health_score >= 70 else "medium" if health_score >= 50 else "high"
        
        return {
            "id": cls.generate_id(),
            "company_id": company_id,
            "plan": plan,
            "mrr": mrr,
            "arr": mrr * 12,
            "contract_start_date": (date.today() - timedelta(days=random.randint(30, 365))).isoformat(),
            "contract_end_date": (date.today() + timedelta(days=random.randint(30, 365))).isoformat(),
            "health_score": health_score,
            "churn_risk": churn_risk,
            "churn_probability": random.randint(5, 30) if churn_risk == "low" else random.randint(30, 60) if churn_risk == "medium" else random.randint(60, 90),
            "last_login_at": (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
            "logins_per_week": random.randint(3, 25),
            "features_used": random.randint(3, 10),
            "total_features": 10,
            "license_usage_percent": random.randint(40, 95),
            "daily_active_users": random.randint(5, 50),
            "support_tickets_30d": random.randint(0, 5),
            "critical_tickets_open": random.choice([0, 0, 0, 1, 2]),
            "avg_resolution_hours": random.randint(12, 48),
            "csat_score": round(random.uniform(3.5, 5.0), 1),
            "nps_score": random.randint(6, 10),
            "last_payment_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "payment_delays": random.choice([0, 0, 0, 1]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": None
        }
    
    @classmethod
    def generate_email(cls, contact_id: str, contact_email: str) -> Dict:
        direction = random.choice(["inbound", "outbound"])
        sentiment = random.choice(["positive", "neutral", "negative", "neutral", "positive"])
        
        return {
            "id": cls.generate_id(),
            "contact_id": contact_id,
            "from_email": contact_email if direction == "inbound" else "sales@ourcrm.com",
            "to_email": "sales@ourcrm.com" if direction == "inbound" else contact_email,
            "subject": random.choice(cls.EMAIL_SUBJECTS),
            "body": f"""Hi there,

I hope this email finds you well. I'm reaching out regarding {random.choice(['our product', 'the demo', 'our partnership', 'the proposal'])}.

{random.choice(['Would love to schedule a call to discuss further.', 'Please let me know if you have any questions.', 'Looking forward to hearing from you.'])}

Best regards,
{random.choice(['John', 'Sarah', 'Mike', 'Emily'])}""",
            "direction": direction,
            "sentiment": sentiment,
            "sentiment_score": random.randint(60, 90) if sentiment == "positive" else random.randint(30, 60) if sentiment == "neutral" else random.randint(10, 40),
            "emotion": random.choice(["curious", "interested", "concerned", "excited", "neutral"]),
            "category": random.choice(["inquiry", "support", "sales", "partnership", "general"]),
            "priority": random.choice(["high", "medium", "low", "medium"]),
            "draft_response": f"""Thank you for your email.

I'd be happy to help you with this. Let me look into the details and get back to you shortly.

Best regards,
Sales Team""" if random.choice([True, False, True]) else None,
            "response_sent": random.choice([True, False, False]),
            "received_at": datetime.now().isoformat(),
            "sent_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": None
        }
    
    @classmethod
    def generate_meeting(cls, deal_id: Optional[str] = None) -> Dict:
        meeting_type = random.choice(cls.MEETING_TYPES)
        scheduled = datetime.now() + timedelta(days=random.randint(-5, 14), hours=random.randint(0, 8))
        
        return {
            "id": cls.generate_id(),
            "deal_id": deal_id,
            "title": f"{random.choice(['Product', 'Discovery', 'Follow-up', 'Kickoff', 'QBR'])} {random.choice(['Meeting', 'Call', 'Demo'])}",
            "meeting_type": meeting_type,
            "scheduled_at": scheduled.isoformat(),
            "duration_minutes": random.choice([15, 30, 30, 45, 60]),
            "location": random.choice(["Zoom", "Google Meet", "Microsoft Teams", "In-person"]),
            "attendees": [{"name": "John Doe", "email": "john@example.com", "status": "accepted"}],
            "agenda": {"items": ["Introduction", "Demo", "Q&A", "Next Steps"]} if meeting_type == "demo" else None,
            "prep_materials": {"deck_url": "https://example.com/deck.pdf"} if random.choice([True, False]) else None,
            "context": f"AI-Generated Context:\n- This is a {meeting_type} meeting\n- Key stakeholders will attend\n- Prepare relevant case studies",
            "notes": "Great discussion. Customer is interested in enterprise features." if scheduled < datetime.now() else None,
            "followup_tasks": {"tasks": ["Send proposal", "Schedule technical deep-dive"]} if scheduled < datetime.now() else None,
            "recording_url": "https://example.com/recording" if scheduled < datetime.now() else None,
            "status": random.choice(["scheduled", "completed", "completed", "cancelled"]) if scheduled < datetime.now() else "scheduled",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": None
        }


class LocalStorage:
    """
    Local JSON storage with full CRUD operations for:
    - Companies
    - Contacts
    - Deals
    - Customers
    - Emails
    - Meetings
    """
    
    def __init__(self, db_path: str = "data/crm_db.json", use_mock_data: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
        
        if use_mock_data and self._is_empty():
            self._generate_mock_data()
    
    def _load(self) -> Dict[str, List[Dict]]:
        """Load data from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            'companies': [],
            'contacts': [],
            'deals': [],
            'customers': [],
            'emails': [],
            'meetings': [],
            'activities': [],
            'agent_logs': [],
            'agent_events': [],
            'metrics_daily': []
        }
    
    def _save(self):
        """Save data to JSON file"""
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def _is_empty(self) -> bool:
        """Check if database is empty"""
        return all(len(self.data.get(table, [])) == 0 
                   for table in ['companies', 'contacts', 'deals', 'customers'])
    
    def _generate_mock_data(self):
        """Generate realistic mock data for all tables"""
        print("📦 Generating mock data...")
        
        # Generate companies
        companies = [MockDataGenerator.generate_company(i) for i in range(15)]
        self.data['companies'] = companies
        
        # Generate contacts (2-3 per company)
        contacts = []
        for company in companies:
            num_contacts = random.randint(1, 3)
            for _ in range(num_contacts):
                contacts.append(MockDataGenerator.generate_contact(
                    company['id'], company['name']
                ))
        self.data['contacts'] = contacts
        
        # Generate deals (1-2 per company)
        deals = []
        for company in companies:
            company_contacts = [c for c in contacts if c['company_id'] == company['id']]
            if company_contacts:
                num_deals = random.randint(0, 2)
                for _ in range(num_deals):
                    contact = random.choice(company_contacts)
                    deals.append(MockDataGenerator.generate_deal(
                        company['id'], contact['id'], company['name']
                    ))
        self.data['deals'] = deals
        
        # Generate customers
        customers = []
        won_deal_company_ids = set(d['company_id'] for d in deals if d['stage'] == 'closed_won')
        for company in companies:
            if company['id'] in won_deal_company_ids or random.random() < 0.3:
                customers.append(MockDataGenerator.generate_customer(
                    company['id'], company['name']
                ))
        self.data['customers'] = customers
        
        # Generate emails
        emails = []
        for contact in contacts[:20]:
            num_emails = random.randint(1, 4)
            for _ in range(num_emails):
                emails.append(MockDataGenerator.generate_email(
                    contact['id'], contact['email']
                ))
        self.data['emails'] = emails
        
        # Generate meetings
        meetings = []
        active_deals = [d for d in deals if d['stage'] not in ['closed_won', 'closed_lost']]
        for deal in active_deals[:10]:
            meetings.append(MockDataGenerator.generate_meeting(deal['id']))
        for _ in range(5):
            meetings.append(MockDataGenerator.generate_meeting())
        self.data['meetings'] = meetings
        
        self._save()
        print(f"✅ Mock data generated!")
    
    # ==========================================================================
    # GENERIC CRUD OPERATIONS
    # ==========================================================================
    
    def create(self, table: str, record: Dict) -> Dict:
        """CREATE: Insert a new record"""
        if 'id' not in record or not record['id']:
            record['id'] = str(uuid.uuid4())
        if 'created_at' not in record:
            record['created_at'] = datetime.now().isoformat()
        if 'updated_at' not in record:
            record['updated_at'] = datetime.now().isoformat()
        self.data[table].append(record)
        self._save()
        return record
    
    def read(self, table: str, record_id: str) -> Optional[Dict]:
        """READ: Get a single record by ID"""
        for record in self.data.get(table, []):
            if str(record.get('id')) == record_id:
                return record
        return None
    
    def read_all(self, table: str, filters: Optional[Dict] = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """READ: Get all records with optional filters"""
        records = self.data.get(table, [])
        
        if filters:
            filtered = []
            for record in records:
                match = True
                for key, value in filters.items():
                    if record.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(record)
            records = filtered
        
        return records[offset:offset + limit]
    
    def update(self, table: str, record_id: str, updates: Dict) -> Optional[Dict]:
        """UPDATE: Update a record by ID"""
        for i, record in enumerate(self.data.get(table, [])):
            if str(record.get('id')) == record_id:
                self.data[table][i].update(updates)
                self.data[table][i]['updated_at'] = datetime.now().isoformat()
                self._save()
                return self.data[table][i]
        return None
    
    def delete(self, table: str, record_id: str) -> bool:
        """DELETE: Delete a record by ID"""
        for i, record in enumerate(self.data.get(table, [])):
            if str(record.get('id')) == record_id:
                del self.data[table][i]
                self._save()
                return True
        return False
    
    def count(self, table: str) -> int:
        """Count records in a table"""
        return len(self.data.get(table, []))
    
    # ==========================================================================
    # CONTACTS CRUD
    # ==========================================================================
    
    def create_contact(self, email: str, first_name: str, last_name: str,
                       company_id: Optional[str] = None, job_title: Optional[str] = None,
                       phone: Optional[str] = None, lead_source: str = "Website",
                       **kwargs) -> Dict:
        """Create a new contact"""
        contact = {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "job_title": job_title,
            "phone": phone,
            "lead_score": kwargs.get('lead_score', 50),
            "lead_status": kwargs.get('lead_status', 'new'),
            "lead_source": lead_source,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "enrichment_data": None,
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('contacts', contact)
    
    def get_contact(self, contact_id: str) -> Optional[Dict]:
        """Get contact by ID"""
        return self.read('contacts', contact_id)
    
    def get_all_contacts(self, company_id: Optional[str] = None, 
                         lead_status: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        """Get all contacts with optional filters"""
        filters = {}
        if company_id:
            filters['company_id'] = company_id
        if lead_status:
            filters['lead_status'] = lead_status
        return self.read_all('contacts', filters, limit)
    
    def update_contact(self, contact_id: str, **kwargs) -> Optional[Dict]:
        """Update contact"""
        return self.update('contacts', contact_id, kwargs)
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete contact"""
        return self.delete('contacts', contact_id)
    
    # ==========================================================================
    # DEALS CRUD
    # ==========================================================================
    
    def create_deal(self, name: str, value: float, stage: str = "prospecting",
                    company_id: Optional[str] = None, contact_id: Optional[str] = None,
                    probability: int = 50, expected_close_date: Optional[str] = None,
                    **kwargs) -> Dict:
        """Create a new deal"""
        deal = {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "contact_id": contact_id,
            "name": name,
            "value": value,
            "stage": stage,
            "probability": probability,
            "health_score": kwargs.get('health_score', 50),
            "is_stalled": kwargs.get('is_stalled', False),
            "risk_factors": kwargs.get('risk_factors'),
            "expected_close_date": expected_close_date,
            "owner_id": kwargs.get('owner_id'),
            "notes": kwargs.get('notes'),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stage_changed_at": datetime.now().isoformat(),
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('deals', deal)
    
    def get_deal(self, deal_id: str) -> Optional[Dict]:
        """Get deal by ID"""
        return self.read('deals', deal_id)
    
    def get_all_deals(self, stage: Optional[str] = None,
                      company_id: Optional[str] = None,
                      limit: int = 100) -> List[Dict]:
        """Get all deals with optional filters"""
        filters = {}
        if stage:
            filters['stage'] = stage
        if company_id:
            filters['company_id'] = company_id
        return self.read_all('deals', filters, limit)
    
    def update_deal(self, deal_id: str, **kwargs) -> Optional[Dict]:
        """Update deal"""
        if 'stage' in kwargs:
            kwargs['stage_changed_at'] = datetime.now().isoformat()
        return self.update('deals', deal_id, kwargs)
    
    def delete_deal(self, deal_id: str) -> bool:
        """Delete deal"""
        return self.delete('deals', deal_id)
    
    def update_deal_stage(self, deal_id: str, new_stage: str) -> Optional[Dict]:
        """Update deal stage"""
        return self.update('deals', deal_id, {
            'stage': new_stage,
            'stage_changed_at': datetime.now().isoformat()
        })
    
    # ==========================================================================
    # CUSTOMERS CRUD
    # ==========================================================================
    
    def create_customer(self, company_id: str, plan: str = "Starter",
                        mrr: float = 0, health_score: int = 50,
                        **kwargs) -> Dict:
        """Create a new customer"""
        customer = {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "plan": plan,
            "mrr": mrr,
            "arr": mrr * 12,
            "health_score": health_score,
            "churn_risk": kwargs.get('churn_risk', 'low'),
            "churn_probability": kwargs.get('churn_probability', 0),
            "logins_per_week": kwargs.get('logins_per_week', 0),
            "features_used": kwargs.get('features_used', 0),
            "total_features": kwargs.get('total_features', 10),
            "license_usage_percent": kwargs.get('license_usage_percent', 0),
            "support_tickets_30d": kwargs.get('support_tickets_30d', 0),
            "critical_tickets_open": kwargs.get('critical_tickets_open', 0),
            "csat_score": kwargs.get('csat_score', 0),
            "nps_score": kwargs.get('nps_score', 0),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('customers', customer)
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        return self.read('customers', customer_id)
    
    def get_all_customers(self, churn_risk: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Get all customers with optional filters"""
        filters = {}
        if churn_risk:
            filters['churn_risk'] = churn_risk
        return self.read_all('customers', filters, limit)
    
    def update_customer(self, customer_id: str, **kwargs) -> Optional[Dict]:
        """Update customer"""
        # Auto-update arr when mrr changes
        if 'mrr' in kwargs:
            kwargs['arr'] = kwargs['mrr'] * 12
        return self.update('customers', customer_id, kwargs)
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete customer"""
        return self.delete('customers', customer_id)
    
    def update_customer_health(self, customer_id: str, health_score: int) -> Optional[Dict]:
        """Update customer health score and auto-calculate churn risk"""
        churn_risk = "low" if health_score >= 70 else "medium" if health_score >= 50 else "high"
        churn_probability = random.randint(5, 30) if churn_risk == "low" else \
                           random.randint(30, 60) if churn_risk == "medium" else \
                           random.randint(60, 90)
        return self.update('customers', customer_id, {
            'health_score': health_score,
            'churn_risk': churn_risk,
            'churn_probability': churn_probability
        })
    
    # ==========================================================================
    # EMAILS CRUD
    # ==========================================================================
    
    def create_email(self, from_email: str, to_email: str, subject: str,
                     body: str, direction: str = "inbound",
                     contact_id: Optional[str] = None, **kwargs) -> Dict:
        """Create a new email"""
        email = {
            "id": str(uuid.uuid4()),
            "contact_id": contact_id,
            "from_email": from_email,
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "direction": direction,
            "sentiment": kwargs.get('sentiment'),
            "sentiment_score": kwargs.get('sentiment_score'),
            "emotion": kwargs.get('emotion'),
            "category": kwargs.get('category'),
            "priority": kwargs.get('priority', 'medium'),
            "draft_response": kwargs.get('draft_response'),
            "response_sent": kwargs.get('response_sent', False),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('emails', email)
    
    def get_email(self, email_id: str) -> Optional[Dict]:
        """Get email by ID"""
        return self.read('emails', email_id)
    
    def get_all_emails(self, contact_id: Optional[str] = None,
                       priority: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """Get all emails with optional filters"""
        filters = {}
        if contact_id:
            filters['contact_id'] = contact_id
        if priority:
            filters['priority'] = priority
        return self.read_all('emails', filters, limit)
    
    def update_email(self, email_id: str, **kwargs) -> Optional[Dict]:
        """Update email"""
        return self.update('emails', email_id, kwargs)
    
    def delete_email(self, email_id: str) -> bool:
        """Delete email"""
        return self.delete('emails', email_id)
    
    def mark_email_sent(self, email_id: str) -> Optional[Dict]:
        """Mark email response as sent"""
        return self.update('emails', email_id, {'response_sent': True})
    
    # ==========================================================================
    # MEETINGS CRUD
    # ==========================================================================
    
    def create_meeting(self, title: str, scheduled_at: str,
                       meeting_type: str = "call", duration_minutes: int = 30,
                       deal_id: Optional[str] = None, location: Optional[str] = None,
                       **kwargs) -> Dict:
        """Create a new meeting"""
        meeting = {
            "id": str(uuid.uuid4()),
            "deal_id": deal_id,
            "title": title,
            "meeting_type": meeting_type,
            "scheduled_at": scheduled_at,
            "duration_minutes": duration_minutes,
            "location": location,
            "attendees": kwargs.get('attendees', []),
            "agenda": kwargs.get('agenda'),
            "prep_materials": kwargs.get('prep_materials'),
            "context": kwargs.get('context'),
            "status": kwargs.get('status', 'scheduled'),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('meetings', meeting)
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting by ID"""
        return self.read('meetings', meeting_id)
    
    def get_all_meetings(self, status: Optional[str] = None,
                         meeting_type: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        """Get all meetings with optional filters"""
        filters = {}
        if status:
            filters['status'] = status
        if meeting_type:
            filters['meeting_type'] = meeting_type
        return self.read_all('meetings', filters, limit)
    
    def update_meeting(self, meeting_id: str, **kwargs) -> Optional[Dict]:
        """Update meeting"""
        return self.update('meetings', meeting_id, kwargs)
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting"""
        return self.delete('meetings', meeting_id)
    
    def update_meeting_status(self, meeting_id: str, status: str) -> Optional[Dict]:
        """Update meeting status"""
        return self.update('meetings', meeting_id, {'status': status})

    def get_meetings_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get meetings within a date range"""
        meetings = self.read_all('meetings', limit=1000)
        filtered = []
        for meeting in meetings:
            scheduled_at = meeting.get('scheduled_at', '')
            if scheduled_at:
                meeting_date = datetime.fromisoformat(scheduled_at).date()
                if start_date <= meeting_date <= end_date:
                    filtered.append(meeting)
        return sorted(filtered, key=lambda x: x.get('scheduled_at', ''))

    def get_meetings_by_month(self, year: int, month: int) -> List[Dict]:
        """Get all meetings for a specific month"""
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        return self.get_meetings_by_date_range(start_date, end_date)

    def get_meetings_by_week(self, year: int, week: int) -> List[Dict]:
        """Get all meetings for a specific week"""
        # Get the first day of the week (Monday)
        first_day = date.fromisocalendar(year, week, 1)
        last_day = first_day + timedelta(days=6)
        return self.get_meetings_by_date_range(first_day, last_day)

    # ==========================================================================
    # COMPANIES CRUD
    # ==========================================================================
    
    def create_company(self, name: str, domain: Optional[str] = None,
                       industry: Optional[str] = None, **kwargs) -> Dict:
        """Create a new company"""
        company = {
            "id": str(uuid.uuid4()),
            "name": name,
            "domain": domain,
            "industry": industry,
            "company_size": kwargs.get('company_size'),
            "revenue_range": kwargs.get('revenue_range'),
            "location": kwargs.get('location'),
            "timezone": kwargs.get('timezone', 'UTC'),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "custom_metadata": kwargs.get('custom_metadata')
        }
        return self.create('companies', company)
    
    def get_company(self, company_id: str) -> Optional[Dict]:
        """Get company by ID"""
        return self.read('companies', company_id)
    
    def get_all_companies(self, industry: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Get all companies with optional filters"""
        filters = {}
        if industry:
            filters['industry'] = industry
        return self.read_all('companies', filters, limit)
    
    def update_company(self, company_id: str, **kwargs) -> Optional[Dict]:
        """Update company"""
        return self.update('companies', company_id, kwargs)
    
    def delete_company(self, company_id: str) -> bool:
        """Delete company"""
        return self.delete('companies', company_id)
    
    # ==========================================================================
    # UTILITIES
    # ==========================================================================
    
    def clear_all_data(self):
        """Clear all data and regenerate mock data"""
        self.data = {
            'companies': [],
            'contacts': [],
            'deals': [],
            'customers': [],
            'emails': [],
            'meetings': [],
            'activities': [],
            'agent_logs': [],
            'agent_events': [],
            'metrics_daily': []
        }
        self._generate_mock_data()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            "companies": self.count('companies'),
            "contacts": self.count('contacts'),
            "deals": self.count('deals'),
            "customers": self.count('customers'),
            "emails": self.count('emails'),
            "meetings": self.count('meetings'),
            "activities": self.count('activities')
        }


# Global storage instance with mock data enabled by default
storage = LocalStorage(use_mock_data=True)


def get_db() -> LocalStorage:
    """Get database storage instance"""
    return storage


def regenerate_mock_data():
    """Clear all data and regenerate fresh mock data"""
    storage.clear_all_data()
    return storage
