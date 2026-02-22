"""Celery Tasks for AI CRM Agents

This module defines async tasks that can be executed by Celery workers.
Tasks are automatically registered when celery worker starts.
"""

from agents.worker import (
    process_lead,
    process_email,
    analyze_deal,
    monitor_customer,
    schedule_meeting,
    generate_analytics,
    daily_health_check,
    weekly_pipeline_review
)

__all__ = [
    'process_lead',
    'process_email',
    'analyze_deal',
    'monitor_customer',
    'schedule_meeting',
    'generate_analytics',
    'daily_health_check',
    'weekly_pipeline_review',
]
