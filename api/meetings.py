"""Meetings API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from database.connection import get_db
from database.models import Meeting

router = APIRouter()


class MeetingResponse(BaseModel):
    id: str
    title: str
    meeting_type: str
    scheduled_at: datetime
    duration_minutes: int = 30
    status: str
    location: str = None
    
    class Config:
        from_attributes = True


class MeetingDetailResponse(MeetingResponse):
    attendees: List[dict] = []
    agenda: List[str] = []
    context: dict = {}
    ai_prep: List[str] = []
    followup_tasks: List[dict] = []
    meeting_link: str = None


class MeetingCreate(BaseModel):
    title: str
    meeting_type: str
    scheduled_at: datetime
    duration_minutes: int = 30
    location: str = "zoom"
    deal_id: str = None
    attendees: List[dict] = []
    agenda: List[str] = []


@router.get("/", response_model=List[MeetingResponse])
async def list_meetings(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    meeting_type: str = None,
    from_date: date = None,
    to_date: date = None,
    db: Session = Depends(get_db)
):
    """List meetings with filters"""
    query = db.query(Meeting)
    
    if status:
        query = query.filter(Meeting.status == status)
    if meeting_type:
        query = query.filter(Meeting.meeting_type == meeting_type)
    if from_date:
        query = query.filter(Meeting.scheduled_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Meeting.scheduled_at <= datetime.combine(to_date, datetime.max.time()))
    
    meetings = query.offset(skip).limit(limit).all()
    return meetings


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Get meeting by ID with AI prep"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/", response_model=MeetingResponse)
async def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    """Create new meeting"""
    db_meeting = Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


@router.patch("/{meeting_id}/status")
async def update_meeting_status(
    meeting_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Update meeting status"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting.status = status
    db.commit()
    
    return {"status": "updated", "meeting_status": status}


@router.get("/{meeting_id}/ai-prep")
async def get_meeting_ai_prep(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get AI preparation tips for meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    prep_tips = []
    
    # Type-specific prep
    if meeting.meeting_type == 'demo':
        prep_tips.append("Prepare product demo environment")
        prep_tips.append("Review prospect's pain points from CRM")
        prep_tips.append("Have pricing sheet ready")
    elif meeting.meeting_type == 'discovery':
        prep_tips.append("Prepare discovery questions")
        prep_tips.append("Research company background")
        prep_tips.append("Review stakeholder roles")
    elif meeting.meeting_type == 'negotiation':
        prep_tips.append("Review contract terms")
        prep_tips.append("Prepare concession strategy")
        prep_tips.append("Have legal team on standby")
    
    # Time-based prep
    if meeting.scheduled_at:
        hours_until = (meeting.scheduled_at - datetime.now()).total_seconds() / 3600
        if hours_until < 2:
            prep_tips.append(f"Meeting starts in {int(hours_until)} hours - send reminder")
    
    return {
        "meeting_id": meeting_id,
        "prep_tips": prep_tips,
        "context": {
            "meeting_type": meeting.meeting_type,
            "duration": meeting.duration_minutes,
            "status": meeting.status
        }
    }


@router.get("/calendar/upcoming")
async def get_upcoming_meetings(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get upcoming meetings for the next N days"""
    from datetime import timedelta
    now = datetime.now()
    end_date = now + timedelta(days=days)
    
    meetings = db.query(Meeting).filter(
        Meeting.scheduled_at >= now,
        Meeting.scheduled_at <= end_date
    ).order_by(Meeting.scheduled_at).all()
    
    return {
        "meetings": meetings,
        "count": len(meetings),
        "period_days": days
    }
