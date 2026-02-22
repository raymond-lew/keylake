"""
Email Intelligence Agent - Autonomous email analysis and response

This agent automatically:
- Analyzes sentiment of incoming emails
- Categorizes and prioritizes emails
- Drafts personalized responses
- Suggests follow-up actions
- Detects urgency and emotion
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re


class EmailIntelligenceAgent:
    """
    Autonomous agent for email intelligence workflows.
    
    Capabilities:
    - Sentiment analysis (positive/negative/neutral)
    - Emotion detection (anger, frustration, happiness, excitement)
    - Email categorization (support, sales, demo, pricing, complaint)
    - Priority determination (high/medium/low)
    - Response drafting with personalization
    - Follow-up suggestion generation
    """

    def __init__(self, llm=None, tools=None, memory=None):
        self.name = "EmailIntelligenceAgent"
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self.version = "1.0.0"
        
        # Email categories
        self.categories = [
            "support_request",
            "sales_inquiry",
            "demo_request",
            "pricing_question",
            "complaint",
            "feature_request",
            "general_inquiry",
            "partnership",
            "feedback"
        ]
        
        # Priority keywords
        self.urgency_keywords = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "issue", "problem", "broken", "not working", "help"
        ]
        
        # Sentiment indicators
        self.positive_indicators = [
            "great", "excellent", "amazing", "love", "happy",
            "pleased", "satisfied", "wonderful", "fantastic"
        ]
        self.negative_indicators = [
            "disappointed", "frustrated", "angry", "unhappy",
            "issue", "problem", "broken", "wrong", "terrible"
        ]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email intelligence workflow"""
        email_data = task.get("email_data", {})
        action = task.get("action", "analyze")
        
        if action == "analyze":
            return await self.analyze_email(email_data)
        elif action == "draft_response":
            return await self.draft_response_email(email_data)
        elif action == "categorize":
            return {"category": await self.categorize_email(email_data)}
        elif action == "sentiment":
            return {"sentiment": await self.analyze_sentiment(email_data)}
        else:
            return {"error": f"Unknown action: {action}"}

    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete email analysis workflow.
        
        Steps:
        1. Analyze sentiment and emotion
        2. Categorize email
        3. Determine priority
        4. Draft response
        5. Suggest follow-ups
        """
        # Step 1: Sentiment analysis
        sentiment = await self.analyze_sentiment(email_data)
        
        # Step 2: Categorization
        category = await self.categorize_email(email_data)
        
        # Step 3: Priority determination
        priority = await self.determine_priority(email_data, sentiment, category)
        
        # Step 4: Draft response
        draft_response = await self.draft_response_email(email_data, sentiment, category)
        
        # Step 5: Follow-up suggestions
        follow_ups = await self.suggest_follow_ups(email_data, category)
        
        # Step 6: Extract action items
        action_items = await self.extract_action_items(email_data)
        
        result = {
            "email_id": email_data.get("id"),
            "from": email_data.get("from"),
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "sentiment": sentiment,
            "category": category,
            "priority": priority,
            "draft_response": draft_response,
            "follow_up_suggestions": follow_ups,
            "action_items": action_items,
            "requires_human_review": self._needs_human_review(priority, sentiment),
            "analyzed_at": datetime.utcnow().isoformat(),
            "agent_version": self.version
        }
        
        # Publish event
        await self._publish_event("email_analyzed", result)
        
        return result

    async def analyze_sentiment(
        self,
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of email content.
        
        Returns:
            Dictionary with score, label, emotion, and urgency
        """
        content = email_data.get("body", "")
        subject = email_data.get("subject", "")
        full_text = f"{subject} {content}"
        
        # Calculate sentiment score
        score = self._calculate_sentiment_score(full_text)
        
        # Determine label
        if score >= 7:
            label = "positive"
        elif score >= 4:
            label = "neutral"
        else:
            label = "negative"
        
        # Detect emotion
        emotion = self._detect_emotion(full_text)
        
        # Assess urgency
        urgency = self._assess_urgency(full_text)
        
        # Extract key concerns
        concerns = self._extract_concerns(full_text)
        
        return {
            "score": score,
            "label": label,
            "emotion": emotion,
            "urgency": urgency,
            "concerns": concerns,
            "confidence": 0.85
        }

    async def categorize_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize email into predefined categories.
        
        Categories:
        - support_request: Technical help needed
        - sales_inquiry: Interest in purchasing
        - demo_request: Request for product demo
        - pricing_question: Questions about pricing
        - complaint: Negative feedback/complaint
        - feature_request: Request for new features
        - general_inquiry: General questions
        """
        content = email_data.get("body", "").lower()
        subject = email_data.get("subject", "").lower()
        full_text = f"{subject} {content}"
        
        # Category keywords
        category_keywords = {
            "support_request": ["help", "support", "issue", "problem", "bug", "error", "not working"],
            "sales_inquiry": ["interested", "purchase", "buy", "get started", "sign up"],
            "demo_request": ["demo", "demonstration", "show me", "walkthrough", "tour"],
            "pricing_question": ["pricing", "price", "cost", "how much", "quote", "plan"],
            "complaint": ["complaint", "unhappy", "disappointed", "frustrated", "angry", "terrible"],
            "feature_request": ["feature", "add", "wish", "suggest", "improvement", "would be nice"],
            "partnership": ["partnership", "partner", "collaborate", "integration"],
            "feedback": ["feedback", "review", "opinion", "thoughts"]
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in full_text)
            category_scores[category] = score
        
        # Get best match
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category] / max(len(category_keywords[best_category]), 1)
        
        # Use LLM for better categorization if available
        if self.llm and confidence < 0.5:
            best_category = await self._categorize_with_llm(email_data)
        
        return {
            "primary": best_category,
            "confidence": min(1.0, confidence + 0.3),
            "all_scores": category_scores,
            "secondary": self._get_secondary_category(category_scores, best_category)
        }

    async def determine_priority(
        self,
        email_data: Dict[str, Any],
        sentiment: Dict[str, Any],
        category: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine email priority level.
        
        Priority factors:
        - Urgency level from sentiment
        - Negative sentiment (complaints need fast response)
        - Category (demo requests are high priority)
        - Sender VIP status
        """
        priority_score = 50  # Base priority
        
        # Adjust for urgency
        urgency = sentiment.get("urgency", "medium")
        if urgency == "high":
            priority_score += 30
        elif urgency == "low":
            priority_score -= 20
        
        # Adjust for sentiment
        sentiment_score = sentiment.get("score", 5)
        if sentiment_score <= 3:
            priority_score += 25  # Negative sentiment needs attention
        elif sentiment_score >= 8:
            priority_score += 10  # Positive sentiment is good to nurture
        
        # Adjust for category
        primary_category = category.get("primary", "")
        high_priority_categories = ["complaint", "demo_request", "sales_inquiry"]
        if primary_category in high_priority_categories:
            priority_score += 20
        
        # Check for VIP sender
        sender = email_data.get("from", "")
        if await self._is_vip_sender(sender):
            priority_score += 25
        
        # Determine priority level
        if priority_score >= 80:
            level = "high"
            sla_hours = 4
        elif priority_score >= 50:
            level = "medium"
            sla_hours = 24
        else:
            level = "low"
            sla_hours = 72
        
        return {
            "level": level,
            "score": priority_score,
            "sla_hours": sla_hours,
            "factors": self._explain_priority_factors(priority_score, sentiment, category)
        }

    async def draft_response_email(
        self,
        email_data: Dict[str, Any],
        sentiment: Dict[str, Any] = None,
        category: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Draft personalized email response.
        
        Response guidelines:
        - Match tone to sender's sentiment
        - Address specific concerns
        - Include clear call-to-action
        - Keep concise and professional
        """
        if sentiment is None:
            sentiment = await self.analyze_sentiment(email_data)
        if category is None:
            category = await self.categorize_email(email_data)
        
        sender_name = email_data.get("from_name", "there")
        subject = email_data.get("subject", "")
        content = email_data.get("body", "")
        
        # Get customer context
        context = await self._get_customer_context(email_data.get("from"))
        
        # Generate response using LLM or templates
        if self.llm:
            draft = await self._generate_response_with_llm(
                email_data, sentiment, category, context
            )
        else:
            draft = self._generate_response_template(
                email_data, sentiment, category, context
            )
        
        return {
            "draft": draft,
            "tone": self._get_response_tone(sentiment),
            "personalization": context.get("personalization", {}),
            "suggested_subject": self._generate_subject_line(category, subject)
        }

    async def suggest_follow_ups(
        self,
        email_data: Dict[str, Any],
        category: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate smart follow-up suggestions"""
        suggestions = []
        primary_category = category.get("primary", "general_inquiry")
        
        # Category-specific suggestions
        if primary_category == "demo_request":
            suggestions = [
                {
                    "action": "schedule_demo",
                    "description": "Schedule product demo call",
                    "priority": "high",
                    "suggested_timeframe": "within 24 hours"
                },
                {
                    "action": "send_calendar_link",
                    "description": "Send calendar booking link",
                    "priority": "high",
                    "suggested_timeframe": "immediately"
                },
                {
                    "action": "prepare_demo_env",
                    "description": "Prepare demo environment for prospect",
                    "priority": "medium",
                    "suggested_timeframe": "before meeting"
                }
            ]
        
        elif primary_category == "support_request":
            suggestions = [
                {
                    "action": "create_support_ticket",
                    "description": "Create support ticket and assign to engineer",
                    "priority": "high",
                    "suggested_timeframe": "within 2 hours"
                },
                {
                    "action": "request_more_info",
                    "description": "Request additional details about the issue",
                    "priority": "medium",
                    "suggested_timeframe": "within 4 hours"
                },
                {
                    "action": "schedule_troubleshooting",
                    "description": "Schedule troubleshooting call if needed",
                    "priority": "low",
                    "suggested_timeframe": "within 24 hours"
                }
            ]
        
        elif primary_category == "pricing_question":
            suggestions = [
                {
                    "action": "send_pricing_sheet",
                    "description": "Send detailed pricing information",
                    "priority": "high",
                    "suggested_timeframe": "within 4 hours"
                },
                {
                    "action": "schedule_discovery",
                    "description": "Schedule discovery call to understand needs",
                    "priority": "medium",
                    "suggested_timeframe": "within 48 hours"
                },
                {
                    "action": "send_case_studies",
                    "description": "Send relevant case studies",
                    "priority": "low",
                    "suggested_timeframe": "within 24 hours"
                }
            ]
        
        elif primary_category == "complaint":
            suggestions = [
                {
                    "action": "escalate_to_manager",
                    "description": "Escalate to customer success manager",
                    "priority": "high",
                    "suggested_timeframe": "immediately"
                },
                {
                    "action": "schedule_resolution_call",
                    "description": "Schedule call to resolve issue",
                    "priority": "high",
                    "suggested_timeframe": "within 4 hours"
                },
                {
                    "action": "offer_compensation",
                    "description": "Consider offering credit or compensation",
                    "priority": "medium",
                    "suggested_timeframe": "after assessment"
                }
            ]
        
        else:
            suggestions = [
                {
                    "action": "send_acknowledgment",
                    "description": "Send acknowledgment email",
                    "priority": "medium",
                    "suggested_timeframe": "within 24 hours"
                },
                {
                    "action": "add_to_nurture",
                    "description": "Add to email nurture campaign",
                    "priority": "low",
                    "suggested_timeframe": "this week"
                }
            ]
        
        return suggestions

    async def extract_action_items(
        self,
        email_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract action items from email"""
        content = email_data.get("body", "")
        
        action_items = []
        
        # Look for action item patterns
        action_patterns = [
            r"(?:please|can you|could you|need to|should)\s+(.+?)(?:\.|\?|$)",
            r"(?:action item|next step|to do|todo)[:\s]+(.+?)(?:\.|\n|$)",
            r"^\s*[-•*]\s*(.+?(?:must|should|need to).+?)$"
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                action_items.append({
                    "description": match.strip(),
                    "status": "pending",
                    "extracted_from": "email_body"
                })
        
        return action_items

    # ========================================================================
    # SENTIMENT ANALYSIS HELPERS
    # ========================================================================

    def _calculate_sentiment_score(self, text: str) -> int:
        """Calculate sentiment score (1-10)"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_indicators if word in text_lower)
        negative_count = sum(1 for word in self.negative_indicators if word in text_lower)
        
        # Base score is 5 (neutral)
        score = 5
        
        # Adjust based on word counts
        score += positive_count * 0.5
        score -= negative_count * 0.7
        
        # Check for intensifiers
        intensifiers = ["very", "extremely", "really", "absolutely", "totally"]
        for intensifier in intensifiers:
            if intensifier in text_lower:
                if score > 5:
                    score += 0.5
                elif score < 5:
                    score -= 0.5
        
        return max(1, min(10, int(score)))

    def _detect_emotion(self, text: str) -> str:
        """Detect primary emotion in text"""
        text_lower = text.lower()
        
        emotion_keywords = {
            "anger": ["angry", "furious", "outraged", "livid", "infuriated"],
            "frustration": ["frustrated", "annoyed", "irritated", "bothered"],
            "happiness": ["happy", "pleased", "delighted", "thrilled", "excited"],
            "excitement": ["excited", "eager", "enthusiastic", "looking forward"],
            "concern": ["concerned", "worried", "anxious", "nervous"],
            "gratitude": ["thank", "appreciate", "grateful", "thanks"]
        }
        
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            emotion_scores[emotion] = sum(1 for k in keywords if k in text_lower)
        
        if max(emotion_scores.values()) == 0:
            return "neutral"
        
        return max(emotion_scores, key=emotion_scores.get)

    def _assess_urgency(self, text: str) -> str:
        """Assess urgency level"""
        text_lower = text.lower()
        
        urgency_count = sum(1 for word in self.urgency_keywords if word in text_lower)
        
        # Check for time-sensitive phrases
        time_phrases = ["today", "this week", "as soon as", "right away", "immediately"]
        for phrase in time_phrases:
            if phrase in text_lower:
                urgency_count += 1
        
        if urgency_count >= 3:
            return "high"
        elif urgency_count >= 1:
            return "medium"
        return "low"

    def _extract_concerns(self, text: str) -> List[str]:
        """Extract key concerns from email"""
        concerns = []
        
        # Look for concern patterns
        concern_indicators = ["issue with", "problem with", "concern about", "worried about"]
        
        sentences = text.split(".")
        for sentence in sentences:
            for indicator in concern_indicators:
                if indicator in sentence.lower():
                    concerns.append(sentence.strip())
                    break
        
        return concerns[:3]  # Top 3 concerns

    # ========================================================================
    # RESPONSE GENERATION HELPERS
    # ========================================================================

    def _generate_response_template(
        self,
        email_data: Dict[str, Any],
        sentiment: Dict[str, Any],
        category: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Generate response using templates"""
        sender_name = email_data.get("from_name", "there")
        category_name = category.get("primary", "general_inquiry")
        
        templates = {
            "demo_request": f"""Hi {sender_name},

Thank you for your interest in seeing our product in action! I'd be happy to arrange a personalized demo for you.

Could you please share a few time slots that work for you next week? Our demos typically run 30-45 minutes.

In the meantime, feel free to check out our case studies at [link] to see how companies like yours are achieving results.

Best regards,
[Your Name]""",
            
            "pricing_question": f"""Hi {sender_name},

Thanks for reaching out about pricing! I'd be happy to provide you with detailed information.

Our pricing is customized based on your specific needs and team size. Could we schedule a brief 15-minute call to understand your requirements better? This will help me provide you with the most accurate pricing.

Alternatively, you can view our standard plans at [pricing link].

Looking forward to connecting!

Best regards,
[Your Name]""",
            
            "support_request": f"""Hi {sender_name},

Thank you for contacting support. I understand you're experiencing an issue, and I'm here to help.

Could you please provide a bit more detail about:
1. What you were trying to accomplish
2. What error or behavior you're seeing
3. Any steps you've already tried

This will help me get you to a resolution as quickly as possible.

Best regards,
[Your Name]""",
            
            "complaint": f"""Hi {sender_name},

Thank you for bringing this to our attention, and I sincerely apologize for the frustration you've experienced. This is not the level of service we strive to provide.

I want to make this right for you. Could we schedule a call to discuss this in detail? I'm available [suggest times].

Your feedback is invaluable in helping us improve.

Best regards,
[Your Name]""",
            
            "sales_inquiry": f"""Hi {sender_name},

Great to hear you're interested in our solution! I'd love to learn more about your needs and show you how we can help.

Could we schedule a brief discovery call this week? In the meantime, here's a quick overview of how we help companies like yours: [brief value prop]

What's the best way to reach you?

Best regards,
[Your Name]"""
        }
        
        return templates.get(category_name, f"""Hi {sender_name},

Thank you for reaching out! I've received your message and will get back to you shortly.

Is there anything specific I can help you with in the meantime?

Best regards,
[Your Name]""")

    def _get_response_tone(self, sentiment: Dict[str, Any]) -> str:
        """Determine appropriate response tone"""
        emotion = sentiment.get("emotion", "neutral")
        score = sentiment.get("score", 5)
        
        if emotion in ["anger", "frustration"] or score <= 3:
            return "empathetic_professional"
        elif emotion in ["happiness", "excitement"] or score >= 8:
            return "enthusiastic_friendly"
        elif emotion == "concern":
            return "reassuring_professional"
        else:
            return "professional_friendly"

    def _generate_subject_line(
        self,
        category: Dict[str, Any],
        original_subject: str
    ) -> str:
        """Generate suggested subject line"""
        primary = category.get("primary", "")
        
        subject_templates = {
            "demo_request": "Re: Scheduling Your Product Demo",
            "pricing_question": "Re: Pricing Information",
            "support_request": "Re: Support Request - We're Here to Help",
            "complaint": "Re: Making This Right",
            "sales_inquiry": "Re: Getting Started with [Product]"
        }
        
        return subject_templates.get(primary, f"Re: {original_subject}")

    # ========================================================================
    # CONTEXT HELPERS
    # ========================================================================

    async def _get_customer_context(self, email: str) -> Dict[str, Any]:
        """Get customer context from CRM"""
        # Would query CRM database
        return {
            "is_existing_customer": False,
            "previous_interactions": 0,
            "account_value": 0,
            "personalization": {}
        }

    async def _is_vip_sender(self, email: str) -> bool:
        """Check if sender is VIP"""
        # Would check against VIP list
        vip_domains = ["enterprise.com", "fortune500.com"]
        domain = email.split("@")[-1] if "@" in email else ""
        return domain in vip_domains

    def _needs_human_review(self, priority: Dict, sentiment: Dict) -> bool:
        """Determine if email needs human review"""
        if priority.get("level") == "high":
            return True
        if sentiment.get("score", 5) <= 2:
            return True
        if sentiment.get("emotion") in ["anger", "frustration"]:
            return True
        return False

    def _explain_priority_factors(
        self,
        score: int,
        sentiment: Dict,
        category: Dict
    ) -> List[str]:
        """Explain what factors influenced priority"""
        factors = []
        
        if sentiment.get("urgency") == "high":
            factors.append("High urgency detected")
        if sentiment.get("score", 5) <= 3:
            factors.append("Negative sentiment requires attention")
        if category.get("primary") in ["complaint", "demo_request"]:
            factors.append(f"Category: {category.get('primary')}")
        
        return factors if factors else ["Standard priority"]

    def _get_secondary_category(
        self,
        scores: Dict[str, int],
        primary: str
    ) -> Optional[str]:
        """Get secondary category if applicable"""
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_categories) > 1 and sorted_categories[1][1] > 0:
            return sorted_categories[1][0]
        return None

    async def _categorize_with_llm(self, email_data: Dict[str, Any]) -> str:
        """Use LLM for better categorization"""
        if not self.llm:
            return "general_inquiry"
        
        prompt = f"""Categorize this email into one of: {self.categories}
        
        Subject: {email_data.get('subject', '')}
        Body: {email_data.get('body', '')[:500]}
        
        Return only the category name."""
        
        # Would call LLM
        return "general_inquiry"

    async def _generate_response_with_llm(
        self,
        email_data: Dict[str, Any],
        sentiment: Dict,
        category: Dict,
        context: Dict
    ) -> str:
        """Generate response using LLM"""
        if not self.llm:
            return self._generate_response_template(email_data, sentiment, category, context)
        
        prompt = f"""Draft a professional email response:
        
        Original email:
        Subject: {email_data.get('subject', '')}
        Body: {email_data.get('body', '')[:500]}
        
        Sentiment: {sentiment}
        Category: {category}
        Context: {context}
        
        Guidelines:
        - Match tone to sentiment
        - Be professional and helpful
        - Include clear next steps
        - Keep under 150 words"""
        
        # Would call LLM
        return self._generate_response_template(email_data, sentiment, category, context)

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event for other systems"""
        event = {
            "type": event_type,
            "agent": self.name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"[{self.name}] Published event: {event_type}")
