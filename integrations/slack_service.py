"""Slack Notifications Service"""

from typing import Dict, List, Any, Optional
import os
import json
from datetime import datetime


class SlackNotificationService:
    """
    Service for sending notifications to Slack.
    Supports:
    - Channel messages
    - Direct messages
    - Interactive buttons
    - Rich formatting
    - Thread replies
    """

    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.default_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#crm-alerts")

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict] = None,
        attachments: List[Dict] = None,
        thread_ts: str = None
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel"""
        payload = {
            "channel": channel,
            "text": text,
            "blocks": blocks or self._create_basic_blocks(text),
            "attachments": attachments or [],
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        # Would use slack_sdk to send message
        return {
            "ok": True,
            "channel": channel,
            "ts": f"{datetime.utcnow().timestamp()}",
            "message": text
        }

    def _create_basic_blocks(self, text: str) -> List[Dict]:
        """Create basic message blocks"""
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        ]

    async def send_lead_notification(
        self,
        lead_data: Dict[str, Any],
        score: int,
        channel: str = None
    ) -> Dict[str, Any]:
        """Send notification about new qualified lead"""
        channel = channel or self.default_channel

        color = "#36a64f" if score >= 70 else "#ff9800" if score >= 40 else "#f44336"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 New {'High-Value' if score >= 70 else 'Qualified'} Lead"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Name:*\n{lead_data.get('first_name', '')} {lead_data.get('last_name', '')}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{lead_data.get('email', '')}"},
                    {"type": "mrkdwn", "text": f"*Company:*\n{lead_data.get('company', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Score:*\n{score}/100"},
                    {"type": "mrkdwn", "text": f"*Title:*\n{lead_data.get('job_title', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Source:*\n{lead_data.get('source', 'Website')}"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in CRM"},
                        "url": f"https://crm.company.com/leads/{lead_data.get('id', '')}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Contact"},
                        "url": f"mailto:{lead_data.get('email', '')}"
                    }
                ]
            }
        ]

        return await self.send_message(channel, "", blocks=blocks)

    async def send_deal_update(
        self,
        deal_data: Dict[str, Any],
        update_type: str,
        channel: str = None
    ) -> Dict[str, Any]:
        """Send notification about deal update"""
        channel = channel or self.default_channel

        icons = {
            "won": "🎉",
            "lost": "😞",
            "stalled": "⚠️",
            "updated": "📊",
            "stage_change": "🔄"
        }

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icons.get(update_type, '📊')} Deal {update_type.replace('_', ' ').title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Deal:*\n{deal_data.get('name', '')}"},
                    {"type": "mrkdwn", "text": f"*Value:*\n${deal_data.get('value', 0):,}"},
                    {"type": "mrkdwn", "text": f"*Stage:*\n{deal_data.get('stage', '')}"},
                    {"type": "mrkdwn", "text": f"*Contact:*\n{deal_data.get('contact_name', 'N/A')}"}
                ]
            }
        ]

        return await self.send_message(channel, "", blocks=blocks)

    async def send_task_reminder(
        self,
        task_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Send task reminder via DM"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⏰ Task Reminder"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{task_data.get('title', 'Task')}*\n{task_data.get('description', '')}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Due: {task_data.get('due_date', 'Today')} | Priority: {task_data.get('priority', 'Medium')}"
                    }
                ]
            }
        ]

        return await self.send_message(user_id, "", blocks=blocks)

    async def send_daily_digest(
        self,
        stats: Dict[str, Any],
        channel: str = None
    ) -> Dict[str, Any]:
        """Send daily CRM digest"""
        channel = channel or self.default_channel

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📈 Daily CRM Digest"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Today's Summary*\n• New Leads: {stats.get('new_leads', 0)}\n• Deals Won: {stats.get('deals_won', 0)}\n• Revenue: ${stats.get('revenue', 0):,}\n• Meetings: {stats.get('meetings', 0)}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Performer*\n🏆 {stats.get('top_performer', 'N/A')} with ${stats.get('top_revenue', 0):,}"
                }
            }
        ]

        return await self.send_message(channel, "", blocks=blocks)

    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Slack channel"""
        return {
            "ok": True,
            "channel": {
                "id": "C123456",
                "name": name,
                "is_private": is_private
            }
        }

    async def invite_user(self, channel: str, user_id: str) -> Dict[str, Any]:
        """Invite user to channel"""
        return {"ok": True}

    async def send_file(
        self,
        channel: str,
        file_path: str,
        title: str = None,
        initial_comment: str = None
    ) -> Dict[str, Any]:
        """Upload and send a file"""
        return {
            "ok": True,
            "file": {
                "id": "F123456",
                "name": os.path.basename(file_path),
                "permalink": f"https://company.slack.com/files/{file_path}"
            }
        }
