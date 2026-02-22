"""
Lead Qualification Agent - Autonomous lead scoring and routing

This agent automatically:
- Scores incoming leads (0-100) based on multiple factors
- Routes high-value prospects to appropriate sales teams
- Enriches contact data from public sources (LinkedIn, company data)
- Identifies buying signals and intent
- Publishes events for downstream workflows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import asyncio


class LeadQualificationAgent:
    """
    Autonomous agent for lead qualification workflows.
    
    Scoring factors:
    - Company size (25%): Enterprise > Large > Medium > Small
    - Job title seniority (25%): Executive > Director > Manager > IC
    - Industry fit (20%): Target industries get higher scores
    - Engagement level (15%): Website visits, content downloads
    - Budget signals (15%): Pricing page visits, demo requests
    """

    def __init__(self, llm=None, tools=None, memory=None):
        self.name = "LeadQualificationAgent"
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self.version = "1.0.0"
        
        # Scoring weights
        self.scoring_weights = {
            "company_size": 0.25,
            "job_title": 0.25,
            "industry": 0.20,
            "engagement": 0.15,
            "budget_signals": 0.15
        }
        
        # Target industries
        self.target_industries = [
            "Software", "Technology", "SaaS", "Financial Services",
            "Healthcare", "E-commerce", "Manufacturing"
        ]
        
        # Executive title patterns
        self.executive_patterns = [
            r'\b(ceo|cfo|cto|cio|coo|president|founder|owner)\b',
            r'\b(vp|vice president|evp|svp)\b',
            r'\b(director|head of|chief)\b'
        ]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute lead qualification workflow.
        
        Args:
            task: Dictionary containing lead_data and optional action
            
        Returns:
            Qualification result with score, routing, and enriched data
        """
        lead_data = task.get("lead_data", {})
        action = task.get("action", "qualify")
        
        if action == "qualify":
            return await self.qualify_lead(lead_data)
        elif action == "enrich":
            return await self.enrich_lead_data(lead_data)
        elif action == "score":
            return {"score": await self.score_lead(lead_data)}
        elif action == "route":
            score = task.get("score", 50)
            return await self.route_lead(score, lead_data)
        else:
            return {"error": f"Unknown action: {action}"}

    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete lead qualification workflow.
        
        Steps:
        1. Enrich lead data
        2. Calculate lead score
        3. Identify buying signals
        4. Determine routing
        5. Generate insights
        """
        # Step 1: Enrich data
        enriched_data = await self.enrich_lead_data(lead_data)
        
        # Step 2: Score the lead
        score = await self.score_lead(enriched_data)
        
        # Step 3: Identify buying signals
        signals = await self.identify_buying_signals(enriched_data)
        
        # Step 4: Route to appropriate team
        routing = await self.route_lead(score, signals, enriched_data)
        
        # Step 5: Generate qualification summary
        summary = await self.generate_qualification_summary(
            lead_data, enriched_data, score, signals, routing
        )
        
        result = {
            "lead_id": lead_data.get("id") or enriched_data.get("id"),
            "original_data": lead_data,
            "enriched_data": enriched_data,
            "score": score,
            "score_breakdown": await self.get_score_breakdown(enriched_data),
            "signals": signals,
            "routing": routing,
            "summary": summary,
            "qualified_at": datetime.utcnow().isoformat(),
            "agent_version": self.version
        }
        
        # Publish event for other agents
        await self._publish_event("lead_qualified", result)
        
        return result

    async def enrich_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich lead data from public sources.
        
        Enrichment sources:
        - Company domain analysis
        - LinkedIn profile data (if available)
        - Company size estimation
        - Industry classification
        """
        enriched = {**lead_data}
        
        # Extract and analyze domain
        email = lead_data.get("email", "")
        domain = self._extract_domain(email)
        enriched["domain"] = domain
        
        # Enrich company data
        company_info = await self._lookup_company(domain)
        enriched["company_info"] = company_info
        
        # Enrich job title
        job_title = lead_data.get("job_title", "")
        enriched["title_seniority"] = self._analyze_title_seniority(job_title)
        enriched["is_decision_maker"] = self._is_decision_maker(job_title)
        
        # Add enrichment metadata
        enriched["enrichment_completed"] = True
        enriched["enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched

    async def score_lead(self, lead_data: Dict[str, Any]) -> int:
        """
        Calculate lead score (0-100).
        
        Scoring methodology:
        - Company size score * 0.25
        - Job title score * 0.25
        - Industry fit score * 0.20
        - Engagement score * 0.15
        - Budget signals score * 0.15
        """
        # Company size score
        company_size = lead_data.get("company_info", {}).get("size", "unknown")
        company_score = self._score_company_size(company_size)
        
        # Job title score
        title_seniority = lead_data.get("title_seniority", "unknown")
        title_score = self._score_title_seniority(title_seniority)
        
        # Industry score
        industry = lead_data.get("company_info", {}).get("industry", "")
        industry_score = self._score_industry_fit(industry)
        
        # Engagement score
        engagement_data = lead_data.get("engagement", {})
        engagement_score = self._score_engagement(engagement_data)
        
        # Budget signals score
        budget_signals = lead_data.get("budget_signals", [])
        budget_score = self._score_budget_signals(budget_signals)
        
        # Calculate weighted score
        total_score = (
            company_score * self.scoring_weights["company_size"] +
            title_score * self.scoring_weights["job_title"] +
            industry_score * self.scoring_weights["industry"] +
            engagement_score * self.scoring_weights["engagement"] +
            budget_score * self.scoring_weights["budget_signals"]
        )
        
        return min(100, max(0, int(total_score)))

    async def identify_buying_signals(
        self,
        lead_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify buying signals from lead behavior and data.
        
        Signal types:
        - Timeline mentions
        - Budget discussions
        - Demo/trial requests
        - Competitor comparisons
        - Decision-maker involvement
        - Pain point expressions
        """
        signals = []
        
        # Check for timeline urgency
        timeline = lead_data.get("timeline", "")
        if self._contains_urgency(timeline):
            signals.append({
                "type": "timeline_urgency",
                "description": f"Urgent timeline mentioned: {timeline}",
                "strength": "high",
                "score_impact": 15
            })
        
        # Check for budget signals
        budget_mentions = lead_data.get("budget_mentions", [])
        if budget_mentions:
            signals.append({
                "type": "budget_discussion",
                "description": "Budget has been discussed",
                "strength": "high",
                "score_impact": 20
            })
        
        # Check for demo request
        if lead_data.get("requested_demo"):
            signals.append({
                "type": "demo_request",
                "description": "Requested product demo",
                "strength": "high",
                "score_impact": 25
            })
        
        # Check for pricing page visits
        pricing_visits = lead_data.get("pricing_page_visits", 0)
        if pricing_visits > 2:
            signals.append({
                "type": "pricing_interest",
                "description": f"Visited pricing page {pricing_visits} times",
                "strength": "medium",
                "score_impact": 10
            })
        
        # Check for competitor mentions
        competitors = lead_data.get("competitors_mentioned", [])
        if competitors:
            signals.append({
                "type": "competitor_evaluation",
                "description": f"Evaluating competitors: {', '.join(competitors)}",
                "strength": "medium",
                "score_impact": 10
            })
        
        # Use LLM for additional signal detection
        if self.llm:
            llm_signals = await self._detect_signals_with_llm(lead_data)
            signals.extend(llm_signals)
        
        return signals

    async def route_lead(
        self,
        score: int,
        signals: List[Dict[str, Any]] = None,
        lead_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Determine routing for the lead.
        
        Routing logic:
        - Score >= 80: Enterprise Sales Team
        - Score 60-79: Mid-Market Sales Team
        - Score 40-59: SMB Sales Team
        - Score < 40: Marketing Nurture
        """
        signals = signals or []
        
        # Determine team based on score
        if score >= 80:
            team = "Enterprise Sales"
            priority = "high"
            sla_hours = 4
        elif score >= 60:
            team = "Mid-Market Sales"
            priority = "medium"
            sla_hours = 24
        elif score >= 40:
            team = "SMB Sales"
            priority = "low"
            sla_hours = 48
        else:
            team = "Marketing Nurture"
            priority = "low"
            sla_hours = 72
        
        # Adjust for urgent signals
        urgent_signals = [s for s in signals if s.get("strength") == "high"]
        if len(urgent_signals) >= 2:
            priority = "high"
            sla_hours = min(sla_hours, 12)
        
        # Determine recommended action
        action = self._get_recommended_action(score, team, signals)
        
        return {
            "team": team,
            "priority": priority,
            "sla_hours": sla_hours,
            "recommended_action": action,
            "auto_assign": score >= 60,
            "requires_review": score < 40
        }

    async def get_score_breakdown(
        self,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed score breakdown by category"""
        company_size = lead_data.get("company_info", {}).get("size", "unknown")
        title_seniority = lead_data.get("title_seniority", "unknown")
        industry = lead_data.get("company_info", {}).get("industry", "")
        engagement_data = lead_data.get("engagement", {})
        budget_signals = lead_data.get("budget_signals", [])
        
        return {
            "company_size": {
                "score": self._score_company_size(company_size),
                "weight": self.scoring_weights["company_size"],
                "value": company_size
            },
            "job_title": {
                "score": self._score_title_seniority(title_seniority),
                "weight": self.scoring_weights["job_title"],
                "value": title_seniority
            },
            "industry": {
                "score": self._score_industry_fit(industry),
                "weight": self.scoring_weights["industry"],
                "value": industry
            },
            "engagement": {
                "score": self._score_engagement(engagement_data),
                "weight": self.scoring_weights["engagement"],
                "value": engagement_data
            },
            "budget_signals": {
                "score": self._score_budget_signals(budget_signals),
                "weight": self.scoring_weights["budget_signals"],
                "value": len(budget_signals)
            }
        }

    async def generate_qualification_summary(
        self,
        original: Dict[str, Any],
        enriched: Dict[str, Any],
        score: int,
        signals: List[Dict[str, Any]],
        routing: Dict[str, Any]
    ) -> str:
        """Generate human-readable qualification summary"""
        summary_parts = []
        
        # Score summary
        if score >= 80:
            summary_parts.append(f"High-quality lead (score: {score}/100)")
        elif score >= 60:
            summary_parts.append(f"Qualified lead (score: {score}/100)")
        elif score >= 40:
            summary_parts.append(f"Moderate lead (score: {score}/100)")
        else:
            summary_parts.append(f"Low-priority lead (score: {score}/100)")
        
        # Key signals
        if signals:
            top_signals = [s["description"] for s in signals[:2]]
            summary_parts.append(f"Key signals: {', '.join(top_signals)}")
        
        # Routing
        summary_parts.append(
            f"Routing to {routing['team']} with {routing['priority']} priority"
        )
        
        return ". ".join(summary_parts) + "."

    # ========================================================================
    # SCORING HELPERS
    # ========================================================================

    def _score_company_size(self, size: str) -> int:
        """Score based on company size"""
        scores = {
            "enterprise": 100,
            "large": 85,
            "medium": 70,
            "small": 50,
            "startup": 40,
            "unknown": 50
        }
        return scores.get(size.lower() if size else "unknown", 50)

    def _score_title_seniority(self, seniority: str) -> int:
        """Score based on job title seniority"""
        scores = {
            "executive": 100,
            "director": 85,
            "manager": 65,
            "senior_ic": 55,
            "individual_contributor": 40,
            "unknown": 50
        }
        return scores.get(seniority.lower() if seniority else "unknown", 50)

    def _score_industry_fit(self, industry: str) -> int:
        """Score based on industry fit"""
        if not industry:
            return 50
        
        industry_lower = industry.lower()
        for target in self.target_industries:
            if target.lower() in industry_lower:
                return 100
        
        # Adjacent industries
        adjacent = ["Services", "Consulting", "Finance", "Retail"]
        for adj in adjacent:
            if adj.lower() in industry_lower:
                return 75
        
        return 50

    def _score_engagement(self, engagement_data: Dict[str, Any]) -> int:
        """Score based on engagement level"""
        score = 50  # Base score
        
        # Website visits
        visits = engagement_data.get("website_visits", 0)
        if visits > 10:
            score += 25
        elif visits > 5:
            score += 15
        elif visits > 2:
            score += 5
        
        # Content downloads
        downloads = engagement_data.get("content_downloads", 0)
        if downloads > 5:
            score += 25
        elif downloads > 2:
            score += 15
        elif downloads > 0:
            score += 5
        
        # Email engagement
        if engagement_data.get("email_open_rate", 0) > 50:
            score += 15
        if engagement_data.get("email_click_rate", 0) > 20:
            score += 10
        
        return min(100, score)

    def _score_budget_signals(self, signals: List[str]) -> int:
        """Score based on budget-related signals"""
        if not signals:
            return 50
        
        score = 50 + (len(signals) * 15)
        return min(100, score)

    # ========================================================================
    # DATA ANALYSIS HELPERS
    # ========================================================================

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        if "@" in email:
            return email.split("@")[-1]
        return ""

    def _analyze_title_seniority(self, title: str) -> str:
        """Analyze job title to determine seniority level"""
        if not title:
            return "unknown"
        
        title_lower = title.lower()
        
        # Executive level
        for pattern in self.executive_patterns[:2]:
            if re.search(pattern, title_lower):
                return "executive"
        
        # Director level
        if re.search(self.executive_patterns[2], title_lower):
            return "director"
        
        # Manager level
        if "manager" in title_lower or "head of" in title_lower:
            return "manager"
        
        # Senior IC
        if "senior" in title_lower or "principal" in title_lower or "lead" in title_lower:
            return "senior_ic"
        
        return "individual_contributor"

    def _is_decision_maker(self, title: str) -> bool:
        """Check if title indicates decision-making authority"""
        if not title:
            return False
        
        title_lower = title.lower()
        decision_keywords = [
            "chief", "head", "director", "vp", "vice president",
            "founder", "owner", "ceo", "cto", "cfo", "coo"
        ]
        
        return any(keyword in title_lower for keyword in decision_keywords)

    def _contains_urgency(self, text: str) -> bool:
        """Check if text contains urgency indicators"""
        if not text:
            return False
        
        urgency_keywords = [
            "urgent", "asap", "immediately", "this week", "this month",
            "quickly", "soon", "right away", "pressing", "critical"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in urgency_keywords)

    async def _lookup_company(self, domain: str) -> Dict[str, Any]:
        """Lookup company information by domain"""
        # Placeholder - would integrate with LinkedIn/Clearbit/etc.
        return {
            "domain": domain,
            "name": domain.replace(".com", "").title() if domain else "Unknown",
            "size": "medium",
            "industry": "Technology",
            "location": "Unknown",
            "founded": None,
            "description": ""
        }

    async def _detect_signals_with_llm(
        self,
        lead_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use LLM to detect additional buying signals"""
        if not self.llm:
            return []
        
        try:
            prompt = f"""
            Analyze this lead data and identify buying signals:
            {lead_data}
            
            Return list of signals with type, description, strength (high/medium/low).
            """
            # Would call LLM here
            return []
        except Exception:
            return []

    def _get_recommended_action(
        self,
        score: int,
        team: str,
        signals: List[Dict[str, Any]]
    ) -> str:
        """Get recommended next action for the lead"""
        if score >= 80:
            return "Schedule executive demo within 4 hours"
        elif score >= 60:
            return "Send personalized outreach email within 24 hours"
        elif score >= 40:
            return "Add to nurture campaign and follow up in 1 week"
        else:
            return "Add to monthly newsletter list"

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event for other agents/systems"""
        # Would publish to message bus (Redis, RabbitMQ, etc.)
        event = {
            "type": event_type,
            "agent": self.name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"[{self.name}] Published event: {event_type}")
