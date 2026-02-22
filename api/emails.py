"""Emails API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database.connection import get_db
from database.models import Email

router = APIRouter()


class EmailResponse(BaseModel):
    id: str
    subject: str
    from_email: str
    to_email: str
    sentiment: str
    sentiment_score: int
    category: str
    priority: str
    is_read: bool = False
    is_starred: bool = False
    received_at: datetime = None
    
    class Config:
        from_attributes = True


class EmailDetailResponse(EmailResponse):
    body: str = None
    preview: str = None
    emotion: str = None
    draft_response: str = None
    ai_insights: List[str] = []
    tags: List[str] = []
    has_attachment: bool = False
    response_sent: bool = False


class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int
    unread_count: int
    urgent_count: int


@router.get("/", response_model=EmailListResponse)
async def list_emails(
    skip: int = 0,
    limit: int = 100,
    priority: str = None,
    category: str = None,
    sentiment: str = None,
    unread_only: bool = False,
    starred_only: bool = False,
    search: str = None,
    db: Session = Depends(get_db)
):
    """List emails with filters"""
    query = db.query(Email)
    
    if priority:
        query = query.filter(Email.priority == priority)
    if category:
        query = query.filter(Email.category == category)
    if sentiment:
        query = query.filter(Email.sentiment == sentiment)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Email.subject.ilike(search_filter)) |
            (Email.body.ilike(search_filter))
        )
    
    total = query.count()
    emails = query.offset(skip).limit(limit).all()
    
    # Calculate counts
    unread_count = db.query(Email).filter(Email.is_read == False).count()
    urgent_count = db.query(Email).filter(
        (Email.priority == 'urgent') | (Email.priority == 'high')
    ).count()
    
    return {
        "emails": emails,
        "total": total,
        "unread_count": unread_count,
        "urgent_count": urgent_count
    }


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(email_id: str, db: Session = Depends(get_db)):
    """Get email by ID with AI analysis"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Mark as read
    email.is_read = True
    db.commit()
    
    return email


@router.post("/{email_id}/star")
async def toggle_email_star(email_id: str, db: Session = Depends(get_db)):
    """Toggle email star status"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_starred = not email.is_starred
    db.commit()
    
    return {"is_starred": email.is_starred}


@router.post("/{email_id}/read")
async def mark_email_read(email_id: str, db: Session = Depends(get_db)):
    """Mark email as read"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_read = True
    db.commit()
    
    return {"status": "marked_read"}


@router.post("/{email_id}/response")
async def send_email_response(
    email_id: str,
    response_data: dict,
    db: Session = Depends(get_db)
):
    """Send response to email"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.response_sent = True
    db.commit()
    
    return {"status": "response_sent"}


@router.get("/{email_id}/ai-analysis")
async def get_email_ai_analysis(
    email_id: str,
    db: Session = Depends(get_db)
):
    """Get AI analysis for email"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    insights = []
    
    # Sentiment-based insights
    if email.sentiment == 'positive' and email.sentiment_score >= 7:
        insights.append("Strong positive sentiment - good opportunity")
    elif email.sentiment == 'negative' and email.sentiment_score <= 3:
        insights.append("Negative sentiment detected - respond with empathy")
    
    # Priority-based insights
    if email.priority == 'urgent':
        insights.append("Urgent - respond within 15 minutes")
    elif email.priority == 'high':
        insights.append("High priority - respond within 2 hours")
    
    # Category-based insights
    if email.category == 'sales_inquiry':
        insights.append("Sales inquiry - include pricing information")
    elif email.category == 'complaint':
        insights.append("Complaint - escalate to support team")
    elif email.category == 'demo_request':
        insights.append("Demo request - schedule within 48 hours")
    
    return {
        "email_id": email_id,
        "sentiment": email.sentiment,
        "sentiment_score": email.sentiment_score,
        "emotion": email.emotion,
        "category": email.category,
        "priority": email.priority,
        "insights": insights,
        "draft_response": email.draft_response,
        "recommended_action": "Reply immediately" if email.priority == 'urgent' else "Reply within 24 hours"
    }
