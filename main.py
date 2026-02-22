"""FastAPI Main Application - AI-Powered CRM"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uvicorn

from database.models import Base, Contact, Deal, Customer, Email, Meeting
from database.connection import engine, get_db
from api import leads, deals, customers, emails, meetings, analytics
from workflows.orchestrator import AgentOrchestrator
from agents.task_queue import task_queue, init_task_queue
from agents import worker  # Initialize tasks

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered CRM",
    description="Production-ready CRM with multi-agent AI architecture",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup (non-blocking)
@app.on_event("startup")
async def startup_event():
    """Create database tables on application startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Database connection failed (tables will be created on first use): {e}")
    
    # Initialize task queue (SQLite-based, no Redis required)
    init_task_queue()

# Initialize agent orchestrator
orchestrator = AgentOrchestrator()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "AI-Powered CRM",
        "version": "1.0.0",
        "status": "healthy",
        "agents": orchestrator.get_agent_status()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "api": "healthy",
        "database": "connected",
        "agents": orchestrator.get_agent_status(),
        "task_queue": task_queue.get_stats()
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(deals.router, prefix="/api/deals", tags=["Deals"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["Meetings"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


# ============================================================================
# AGENT TRIGGER ENDPOINTS
# ============================================================================

@app.post("/api/agents/qualify-lead")
async def qualify_lead(
    lead_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Trigger Lead Qualification Agent"""
    task_id = worker.process_lead.delay(lead_data)
    return {"status": "queued", "task_id": task_id, "message": "Lead qualification queued"}


@app.post("/api/agents/analyze-email")
async def analyze_email(
    email_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Trigger Email Intelligence Agent"""
    task_id = worker.process_email.delay(email_data)
    return {"status": "queued", "task_id": task_id, "message": "Email analysis queued"}


@app.post("/api/agents/analyze-deal/{deal_id}")
async def analyze_deal(
    deal_id: str,
    db: Session = Depends(get_db)
):
    """Trigger Sales Pipeline Agent"""
    task_id = worker.analyze_deal.delay(deal_id)
    return {"status": "queued", "task_id": task_id, "message": "Deal analysis queued"}


@app.post("/api/agents/monitor-customer/{customer_id}")
async def monitor_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Trigger Customer Success Agent"""
    task_id = worker.monitor_customer.delay(customer_id)
    return {"status": "queued", "task_id": task_id, "message": "Customer monitoring queued"}


@app.post("/api/agents/schedule-meeting")
async def schedule_meeting(
    meeting_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Trigger Meeting Scheduler Agent"""
    task_id = worker.schedule_meeting.delay(meeting_request)
    return {"status": "queued", "task_id": task_id, "message": "Meeting scheduling queued"}


@app.post("/api/agents/generate-dashboard")
async def generate_dashboard(
    category: str = "all",
    db: Session = Depends(get_db)
):
    """Trigger Analytics Agent - synchronous"""
    dashboard = await orchestrator.generate_dashboard(category, db)
    return dashboard


# ============================================================================
# WEBHOOKS
# ============================================================================

@app.post("/webhooks/email-received")
async def email_webhook(
    email_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Webhook for incoming emails"""
    task_id = worker.process_email.delay(email_data)
    return {"status": "received", "task_id": task_id}


@app.post("/webhooks/form-submission")
async def form_webhook(
    form_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Webhook for form submissions (new leads)"""
    task_id = worker.process_lead.delay(form_data)
    return {"status": "received", "task_id": task_id}


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
