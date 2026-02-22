"""Task Worker for AI CRM Agents (SQLite-based - No Redis Required)

This module defines tasks that can be executed asynchronously using SQLite queue.
When Redis is not available, tasks are queued in SQLite and executed by a background worker.
"""

from dotenv import load_dotenv
import os
from agents.task_queue import task, task_queue, init_task_queue

# Load environment variables
load_dotenv()

# Initialize task queue on module load
init_task_queue()


# ============================================================================
# AGENT TASKS
# ============================================================================

@task
def process_lead(lead_data: dict):
    """Process new lead through Lead Qualification Agent"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run lead qualification
    result = orchestrator.lead_agent.execute({"lead_data": lead_data})

    return {
        "status": "success",
        "result": result
    }


@task
def process_email(email_data: dict):
    """Process email through Email Intelligence Agent"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run email analysis
    result = orchestrator.email_agent.execute({"email_data": email_data})

    return {
        "status": "success",
        "result": result
    }


@task
def analyze_deal(deal_id: str):
    """Analyze deal through Sales Pipeline Agent"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run deal analysis
    result = orchestrator.sales_agent.execute({"deal_id": deal_id, "action": "analyze"})

    return {
        "status": "success",
        "result": result
    }


@task
def monitor_customer(customer_id: str):
    """Monitor customer through Customer Success Agent"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run customer monitoring
    result = orchestrator.success_agent.execute({"customer_id": customer_id, "action": "monitor"})

    return {
        "status": "success",
        "result": result
    }


@task
def schedule_meeting(meeting_request: dict):
    """Schedule meeting through Meeting Scheduler Agent"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run meeting scheduling
    result = orchestrator.meeting_agent.execute(meeting_request)

    return {
        "status": "success",
        "result": result
    }


@task
def generate_analytics(category: str = "all"):
    """Generate analytics dashboard"""
    from workflows.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    # Run analytics
    result = orchestrator.analytics_agent.execute({"action": "dashboard", "category": category})

    return {
        "status": "success",
        "result": result
    }


# ============================================================================
# SCHEDULED TASKS
# ============================================================================

def daily_health_check():
    """Run daily customer health checks"""
    from workflows.orchestrator import AgentOrchestrator
    from database.connection import SessionLocal
    from database.models import Customer

    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator()
        customers = db.query(Customer).all()

        for customer in customers:
            orchestrator.success_agent.execute({
                "customer_id": str(customer.id),
                "action": "monitor"
            })

        return {"status": "success", "customers_checked": len(customers)}
    finally:
        db.close()


def weekly_pipeline_review():
    """Run weekly pipeline analysis"""
    from workflows.orchestrator import AgentOrchestrator
    from database.connection import SessionLocal
    from database.models import Deal

    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator()
        active_deals = db.query(Deal).filter(
            Deal.stage.in_(['prospecting', 'qualification', 'proposal', 'negotiation'])
        ).all()

        for deal in active_deals:
            orchestrator.sales_agent.execute({
                "deal_id": str(deal.id),
                "action": "analyze"
            })

        return {"status": "success", "deals_reviewed": len(active_deals)}
    finally:
        db.close()


# ============================================================================
# CELERY COMPATIBILITY (if Redis becomes available)
# ============================================================================
# If you want to use Celery with Redis in the future:
# 1. Install Redis: sudo dnf install -y redis
# 2. Start Redis: sudo systemctl start redis
# 3. Set REDIS_URL environment variable
# 4. Run: celery -A agents.worker_celery worker --loglevel=info
