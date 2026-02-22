"""Deals API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from database.connection import get_db
from database.models import Deal

router = APIRouter()


class DealCreate(BaseModel):
    name: str
    value: float
    stage: str
    contact_id: str = None
    company_id: str = None
    expected_close_date: date = None


class DealResponse(BaseModel):
    id: str
    name: str
    value: float
    stage: str
    health_score: int
    probability: int
    is_stalled: bool
    expected_close_date: date = None
    contact_name: str = None
    company_name: str = None
    
    class Config:
        from_attributes = True


class DealDetailResponse(DealResponse):
    ai_insights: List[str] = []
    risk_factors: List[str] = []
    next_best_action: str = None
    competitor_mentioned: bool = False
    engagement_level: str = "medium"
    stakeholders: List[dict] = []
    recent_events: List[dict] = []


class DealHealthUpdate(BaseModel):
    health_score: int
    is_stalled: bool
    ai_insights: List[str] = []
    risk_factors: List[str] = []
    next_best_action: str = None


@router.get("/", response_model=List[DealResponse])
async def list_deals(
    skip: int = 0,
    limit: int = 100,
    stage: str = None,
    health_score_min: int = None,
    db: Session = Depends(get_db)
):
    """List all deals with optional filters"""
    query = db.query(Deal)
    if stage:
        query = query.filter(Deal.stage == stage)
    if health_score_min:
        query = query.filter(Deal.health_score >= health_score_min)
    deals = query.offset(skip).limit(limit).all()
    return deals


@router.get("/{deal_id}", response_model=DealDetailResponse)
async def get_deal(deal_id: str, db: Session = Depends(get_db)):
    """Get deal by ID with AI insights"""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/", response_model=DealResponse)
async def create_deal(deal: DealCreate, db: Session = Depends(get_db)):
    """Create new deal"""
    db_deal = Deal(**deal.dict())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


@router.patch("/{deal_id}/stage")
async def update_deal_stage(
    deal_id: str,
    stage: str,
    db: Session = Depends(get_db)
):
    """Update deal stage"""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.stage = stage
    deal.stage_changed_at = func.now()
    db.commit()
    return {"status": "updated", "stage": stage}


@router.patch("/{deal_id}/health")
async def update_deal_health(
    deal_id: str,
    health_update: DealHealthUpdate,
    db: Session = Depends(get_db)
):
    """Update deal health score and AI insights"""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal.health_score = health_update.health_score
    deal.is_stalled = health_update.is_stalled
    if health_update.risk_factors:
        deal.risk_factors = health_update.risk_factors
    
    db.commit()
    return {"status": "updated", "health_score": deal.health_score}


@router.get("/{deal_id}/ai-insights")
async def get_deal_ai_insights(
    deal_id: str,
    db: Session = Depends(get_db)
):
    """Get AI-generated insights for a deal"""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Generate AI insights based on deal data
    insights = []
    risk_factors = []
    
    # Analyze deal stage and probability
    if deal.probability >= 75:
        insights.append("High close probability - prioritize final negotiations")
    elif deal.probability <= 40:
        insights.append("Low close probability - consider additional discovery")
    
    # Check for stalled deals
    if deal.is_stalled:
        risk_factors.append("Deal stalled - no recent activity")
        insights.append("Re-engagement recommended - send case study or offer demo")
    
    # Health score analysis
    if deal.health_score >= 80:
        insights.append("Strong deal health - all stakeholders engaged")
    elif deal.health_score <= 50:
        risk_factors.append("Low deal health score")
        insights.append("Schedule executive alignment meeting")
    
    return {
        "deal_id": deal_id,
        "insights": insights,
        "risk_factors": risk_factors,
        "next_best_action": "Send proposal with enterprise terms" if deal.stage == "negotiation" else "Schedule discovery call",
        "confidence_score": min(deal.health_score, deal.probability)
    }


@router.get("/pipeline/metrics")
async def get_pipeline_metrics(db: Session = Depends(get_db)):
    """Get pipeline metrics and breakdown"""
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
            "weighted_value": stage_weighted
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
