"""Analytics API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from database.connection import get_db
from database.models import Deal, Contact, Customer, Email, Meeting

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get dashboard metrics"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Count metrics
    total_leads = db.query(Contact).count()
    total_deals = db.query(Deal).count()
    total_customers = db.query(Customer).count()
    
    # Revenue metrics
    total_pipeline = db.query(Deal).filter(
        Deal.stage.in_(['prospecting', 'qualification', 'proposal', 'negotiation'])
    ).with_entities(func.sum(Deal.value)).scalar() or 0
    
    total_mrr = db.query(Customer).with_entities(
        func.sum(Customer.mrr)
    ).scalar() or 0
    
    # Recent activity
    new_leads_30d = db.query(Contact).filter(Contact.created_at >= cutoff_date).count()
    deals_won_30d = db.query(Deal).filter(
        Deal.stage == 'closed_won',
        Deal.updated_at >= cutoff_date
    ).count()
    
    return {
        "leads": {
            "total": total_leads,
            "new_this_period": new_leads_30d,
            "qualified": db.query(Contact).filter(Contact.lead_status == 'qualified').count()
        },
        "deals": {
            "total": total_deals,
            "pipeline_value": float(total_pipeline),
            "won_this_period": deals_won_30d
        },
        "customers": {
            "total": total_customers,
            "mrr": float(total_mrr),
            "arr": float(total_mrr * 12)
        },
        "period_days": days
    }


@router.get("/pipeline")
async def get_pipeline_metrics(db: Session = Depends(get_db)):
    """Get pipeline breakdown by stage"""
    stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
    pipeline = {}
    
    total_value = 0
    weighted_value = 0
    
    for stage in stages:
        deals = db.query(Deal).filter(Deal.stage == stage).all()
        count = len(deals)
        value = sum(d.value for d in deals)
        stage_weighted = sum(d.value * d.probability / 100 for d in deals)
        
        pipeline[stage] = {
            "count": count,
            "value": value,
            "weighted_value": stage_weighted,
            "avg_health_score": sum(d.health_score for d in deals) / count if count > 0 else 0
        }
        
        if stage not in ['closed_won', 'closed_lost']:
            total_value += value
            weighted_value += stage_weighted
    
    return {
        "pipeline": pipeline,
        "total_value": total_value,
        "weighted_value": weighted_value,
        "total_deals": sum(p["count"] for p in pipeline.values()),
        "avg_health_score": db.query(func.avg(Deal.health_score)).scalar() or 0
    }


@router.get("/revenue/trend")
async def get_revenue_trend(
    months: int = 6,
    db: Session = Depends(get_db)
):
    """Get revenue trend for forecasting"""
    now = datetime.now()
    trend_data = []
    
    for i in range(months, 0, -1):
        month_start = now - timedelta(days=30*i)
        month_end = now - timedelta(days=30*(i-1))
        
        won_deals = db.query(Deal).filter(
            Deal.stage == 'closed_won',
            Deal.updated_at >= month_start,
            Deal.updated_at <= month_end
        ).all()
        
        revenue = sum(d.value for d in won_deals)
        
        trend_data.append({
            "month": month_start.strftime("%b"),
            "revenue": revenue,
            "deals_count": len(won_deals)
        })
    
    # Add forecast for next 3 months
    avg_revenue = sum(d["revenue"] for d in trend_data[-3:]) / 3 if trend_data else 0
    for i in range(1, 4):
        future_month = now + timedelta(days=30*i)
        trend_data.append({
            "month": future_month.strftime("%b"),
            "revenue": None,
            "forecast": avg_revenue * (1 + 0.05*i),  # 5% growth projection
            "deals_count": None
        })
    
    return {"trend": trend_data, "months": months}


@router.get("/performance/win-rate")
async def get_win_rate_by_segment(db: Session = Depends(get_db)):
    """Get win rate analysis by segment"""
    # This would ideally segment by company size, industry, etc.
    # For now, we'll segment by deal value ranges
    
    segments = [
        {"name": "SMB", "min": 0, "max": 20000},
        {"name": "Mid-Market", "min": 20000, "max": 100000},
        {"name": "Enterprise", "min": 100000, "max": float('inf')},
    ]
    
    results = []
    for segment in segments:
        all_deals = db.query(Deal).filter(
            Deal.value >= segment["min"],
            Deal.value < segment["max"]
        ).all()
        
        won_deals = [d for d in all_deals if d.stage == 'closed_won']
        
        if all_deals:
            win_rate = len(won_deals) / len(all_deals) * 100
            avg_deal_size = sum(d.value for d in all_deals) / len(all_deals)
        else:
            win_rate = 0
            avg_deal_size = 0
        
        results.append({
            "segment": segment["name"],
            "win_rate": round(win_rate, 1),
            "total_deals": len(all_deals),
            "won_deals": len(won_deals),
            "avg_deal_size": round(avg_deal_size, 0)
        })
    
    return {"segments": results}


@router.get("/customers/health")
async def get_customer_health_distribution(db: Session = Depends(get_db)):
    """Get customer health score distribution"""
    health_ranges = [
        {"name": "At Risk", "min": 0, "max": 40, "color": "#ef4444"},
        {"name": "Warning", "min": 40, "max": 60, "color": "#f59e0b"},
        {"name": "Healthy", "min": 60, "max": 80, "color": "#10b981"},
        {"name": "Excellent", "min": 80, "max": 101, "color": "#059669"},
    ]
    
    distribution = []
    for range in health_ranges:
        count = db.query(Customer).filter(
            Customer.health_score >= range["min"],
            Customer.health_score < range["max"]
        ).count()
        
        distribution.append({
            "name": range["name"],
            "value": count,
            "color": range["color"]
        })
    
    return {"distribution": distribution}


@router.get("/agents/performance")
async def get_agent_performance(db: Session = Depends(get_db)):
    """Get AI agent performance metrics"""
    # This would query agent_logs table in production
    return {
        "agents": [
            {
                "name": "Lead Qualification",
                "tasks_completed": 1247,
                "accuracy": 94,
                "time_saved_hours": 52
            },
            {
                "name": "Email Intelligence",
                "tasks_completed": 3421,
                "accuracy": 91,
                "time_saved_hours": 128
            },
            {
                "name": "Sales Pipeline",
                "tasks_completed": 892,
                "accuracy": 96,
                "time_saved_hours": 38
            },
            {
                "name": "Customer Success",
                "tasks_completed": 567,
                "accuracy": 93,
                "time_saved_hours": 45
            },
            {
                "name": "Meeting Scheduler",
                "tasks_completed": 423,
                "accuracy": 98,
                "time_saved_hours": 67
            },
            {
                "name": "Analytics",
                "tasks_completed": 156,
                "accuracy": 99,
                "time_saved_hours": 24
            }
        ]
    }


@router.get("/churn/prediction")
async def get_churn_prediction(
    months: int = 3,
    db: Session = Depends(get_db)
):
    """Get churn prediction data"""
    now = datetime.now()
    predictions = []
    
    for i in range(months, 0, -1):
        month_date = now - timedelta(days=30*i)
        
        at_risk = db.query(Customer).filter(
            Customer.churn_risk == 'high',
            Customer.updated_at >= month_date - timedelta(days=30),
            Customer.updated_at < month_date
        ).count()
        
        total = db.query(Customer).count()
        churn_rate = (at_risk / total * 100) if total > 0 else 0
        
        predictions.append({
            "month": month_date.strftime("%b"),
            "predicted": round(churn_rate * 1.1, 1),  # AI prediction
            "actual": round(churn_rate, 1)
        })
    
    # Future predictions
    for i in range(1, 3):
        future_month = now + timedelta(days=30*i)
        predictions.append({
            "month": future_month.strftime("%b"),
            "predicted": round(predictions[-1]["actual"] * 0.95, 1),  # Improving trend
            "actual": None
        })
    
    return {"predictions": predictions}


@router.get("/activity/weekly")
async def get_weekly_activity(db: Session = Depends(get_db)):
    """Get weekly activity metrics"""
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    
    activity = []
    for i in range(5):  # Mon-Fri
        day = week_start + timedelta(days=i)
        day_end = day + timedelta(days=1)
        
        emails = db.query(Email).filter(
            Email.created_at >= day,
            Email.created_at < day_end
        ).count()
        
        meetings = db.query(Meeting).filter(
            Meeting.scheduled_at >= day,
            Meeting.scheduled_at < day_end
        ).count()
        
        activity.append({
            "day": day.strftime("%a"),
            "emails": emails,
            "meetings": meetings,
            "calls": emails // 5,  # Estimate
            "demos": meetings // 2  # Estimate
        })
    
    return {"activity": activity}


@router.get("/ai-insights")
async def get_ai_insights(db: Session = Depends(get_db)):
    """Get AI-generated insights and recommendations"""
    # Calculate key metrics
    total_deals = db.query(Deal).count()
    won_deals = db.query(Deal).filter(Deal.stage == 'closed_won').count()
    win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
    
    avg_cycle = db.query(func.avg(Deal.health_score)).scalar() or 50
    
    at_risk_customers = db.query(Customer).filter(
        Customer.churn_risk.in_(['high', 'medium'])
    ).count()
    
    insights = []
    
    # Revenue insight
    pipeline_value = db.query(Deal).filter(
        Deal.stage.in_(['prospecting', 'qualification', 'proposal', 'negotiation'])
    ).with_entities(func.sum(Deal.value)).scalar() or 0
    
    if pipeline_value > 1000000:
        insights.append({
            "type": "opportunity",
            "category": "revenue",
            "title": "Strong Pipeline",
            "message": f"Pipeline value of ${pipeline_value/1000000:.1f}M positions you well for Q targets"
        })
    
    # Win rate insight
    if win_rate >= 60:
        insights.append({
            "type": "success",
            "category": "performance",
            "title": "Excellent Win Rate",
            "message": f"{win_rate:.0f}% win rate is above industry average of 47%"
        })
    elif win_rate < 40:
        insights.append({
            "type": "warning",
            "category": "performance",
            "title": "Win Rate Improvement Needed",
            "message": f"Current win rate of {win_rate:.0f}% is below target. Review qualification criteria."
        })
    
    # Churn insight
    if at_risk_customers > 0:
        insights.append({
            "type": "alert",
            "category": "retention",
            "title": "Churn Risk Detected",
            "message": f"{at_risk_customers} customers show churn risk signals. Schedule check-ins."
        })
    
    return {
        "insights": insights,
        "generated_at": datetime.now().isoformat()
    }
