"""
PydanticAI demonstration of the AI Access Control Four Perimeters Framework

This implementation demonstrates the four essential security perimeters for a financial advisor agent:
1. Prompt Validation: Ensures queries comply with financial advice regulations
2. RAG Permissions: Controls access to different levels of financial documentation
3. Action Permissions: Manages access to financial analysis capabilities
4. Response Validation: Enforces compliance requirements in responses
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from permit import Permit
from permit.exceptions import PermitApiError
import os
from dotenv import load_dotenv
from dataclasses import dataclass


load_dotenv()  # load environment variables

# Permit.io API key
PERMIT_KEY = os.environ.get("PERMIT_KEY")
if not PERMIT_KEY:
    raise ValueError("PERMIT_KEY environment variable not set")
PDP_URL = "http://localhost:7100"


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


class UserContext(BaseModel):
    """User context with permissions information"""

    user_id: str
    tier: str = Field(default="free")


class FinancialQuery(BaseModel):
    """Input model for financial queries"""

    question: str
    context: UserContext
    risk_profile: Optional[str] = None
    portfolio_value: Optional[float] = None
    investment_horizon: Optional[str] = None


class FinancialResponse(BaseModel):
    """Output model for financial advice"""

    answer: str
    compliance_notes: List[str] = Field(default_factory=list)
    certification_level: str = "general"  # general, professional, expert
    risk_warnings: List[str] = Field(default_factory=list)


@dataclass
class PermitDeps:
    """Dependencies for security-focused agent"""

    permit: Permit
    user_id: str

    def __post_init__(self):
        if not self.permit:
            self.permit = Permit(
                token=PERMIT_KEY,
                pdp=PDP_URL,
            )


# Initialize the financial advisor agent
financial_agent = Agent(
    "anthropic:claude-3-5-sonnet-latest",
    deps_type=PermitDeps,
    system_prompt="You are a secure financial advisor assistant.",
)


@financial_agent.tool
async def validate_financial_query(
    ctx: RunContext[PermitDeps],
    query: FinancialQuery,
) -> Dict[str, bool]:
    """SECURITY PERIMETER 1: Prompt Validation

    Validates financial queries against regulatory requirements and advisor certification levels.
    Ensures queries are appropriate for the advisor's certification and user's permission level.

    Key checks:
    - Query matches advisor's certification level
    - Query complies with financial advice regulations
    """
    try:
        # Check advisor certification level permission
        certification_check = await ctx.deps.permit.check(
            ctx.deps.user_id,
            "provide_advice",
            {"type": "certification", "level": get_required_certification(query)},
        )

        # Validate against regulatory requirements
        regulatory_check = await ctx.deps.permit.check(
            ctx.deps.user_id,
            "regulatory_compliance",
            {"type": "advice_type", "category": categorize_query(query)},
        )

        return {
            "permitted": certification_check and regulatory_check,
            "certification_level": get_required_certification(query),
            "warnings": get_regulatory_warnings(query),
        }

    except PermitApiError as e:
        raise SecurityError(f"Advice permission check failed: {str(e)}")


@financial_agent.tool
async def access_financial_knowledge(
    ctx: RunContext[PermitDeps], query: FinancialQuery
) -> List[str]:
    """SECURITY PERIMETER 2: RAG Permissions

    Controls access to financial documentation and knowledge bases based on
    certification levels and regulatory requirements.

    Access levels:
    - Basic: General financial education materials
    - Professional: Licensed advisor materials
    - Expert: Advanced analysis and specialized advice
    """
    try:
        # Basic financial knowledge available to all
        allowed_docs = ["general_education", "basic_principles"]

        # Check professional documentation access
        professional_access = await ctx.deps.permit.check(
            ctx.deps.user_id, "access_professional_docs", "documentation"
        )
        if professional_access:
            allowed_docs.extend(
                [
                    "professional_guidelines",
                    "regulatory_frameworks",
                    "investment_strategies",
                ]
            )

        # Check expert documentation access
        expert_access = await ctx.deps.permit.check(
            ctx.deps.user_id, "access_expert_docs", "documentation"
        )
        if expert_access:
            allowed_docs.extend(
                [
                    "advanced_analysis",
                    "specialized_strategies",
                    "institutional_research",
                ]
            )

        return allowed_docs

    except PermitApiError as e:
        raise SecurityError(f"Documentation access check failed: {str(e)}")


@financial_agent.tool
async def check_action_permissions(
    ctx: RunContext[PermitDeps], action: str, context: UserContext
) -> bool:
    """SECURITY PERIMETER 3: Action Permissions

    Controls access to specific financial analysis and advisory actions based on
    certification level and regulatory requirements.

    Protected actions:
    - Portfolio analysis
    - Risk assessment
    - Investment recommendations
    - Tax strategy
    """
    try:
        action_permissions = {
            "basic_advice": await ctx.deps.permit.check(
                ctx.deps.user_id,
                "provide",
                {"type": "financial_action", "action": "basic_advice"},
            ),
            "portfolio_analysis": await ctx.deps.permit.check(
                ctx.deps.user_id,
                "analyze",
                {"type": "financial_action", "action": "portfolio_analysis"},
            ),
            "specific_recommendations": await ctx.deps.permit.check(
                ctx.deps.user_id,
                "recommend",
                {"type": "financial_action", "action": "specific_recommendations"},
            ),
        }

        return action_permissions.get(action, False)

    except PermitApiError as e:
        raise SecurityError(f"Action permission check failed: {str(e)}")


@financial_agent.tool
async def validate_financial_response(
    ctx: RunContext[PermitDeps], response: FinancialResponse, context: UserContext
) -> Dict[str, bool]:
    """SECURITY PERIMETER 4: Response Validation

    Ensures all financial advice responses meet regulatory requirements and
    include necessary disclaimers and risk warnings.

    Validation checks:
    - Required disclaimers present
    - Risk warnings appropriate
    - Certification level disclosed
    - Compliance with regulatory guidelines
    """
    try:
        # Validate compliance requirements
        compliance_check = await ctx.deps.permit.check(
            ctx.deps.user_id,
            "compliance_validation",
            {"type": "response", "certification": response.certification_level},
        )

        # Ensure required disclaimers
        required_disclaimers = get_required_disclaimers(response.certification_level)
        missing_disclaimers = [
            d for d in required_disclaimers if d not in response.compliance_notes
        ]
        if missing_disclaimers:
            response.compliance_notes.extend(missing_disclaimers)

        # Validate risk warnings
        if needs_risk_warnings(response.answer):
            required_warnings = get_required_risk_warnings(response.answer)
            response.risk_warnings.extend(required_warnings)

        return {
            "permitted": compliance_check,
            "certification_verified": response.certification_level,
            "warnings": response.compliance_notes + response.risk_warnings,
        }

    except PermitApiError as e:
        raise SecurityError(f"Response validation failed: {str(e)}")


"""
Helper functions for Financial Advisor security perimeters.
These functions implement the business logic for certification requirements,
risk assessment, and regulatory compliance.
"""


def get_required_certification(query: FinancialQuery) -> str:
    """
    Determine required certification level based on query content.

    Returns:
        str: "general", "professional", or "expert"
    """
    # Keywords indicating complexity level
    expert_keywords = [
        "derivatives",
        "hedge",
        "institutional",
        "merger",
        "acquisition",
        "structured products",
        "foreign exchange",
        "forex",
        "options trading",
    ]
    professional_keywords = [
        "portfolio",
        "tax strategy",
        "estate planning",
        "retirement",
        "investment strategy",
        "risk assessment",
        "asset allocation",
    ]

    question = query.question.lower()

    # Check for expert-level advice needs
    if any(keyword in question for keyword in expert_keywords):
        return "expert"

    # Check for professional-level advice needs
    if any(keyword in question for keyword in professional_keywords):
        return "professional"

    # Check if portfolio value requires higher certification
    if query.portfolio_value:
        if query.portfolio_value >= 1000000:  # $1M+ portfolios need expert
            return "expert"
        elif query.portfolio_value >= 100000:  # $100k+ portfolios need professional
            return "professional"

    return "general"


def needs_risk_profile(query: FinancialQuery) -> bool:
    """
    Determine if query requires risk profile information.
    """
    risk_required_keywords = [
        "invest",
        "portfolio",
        "allocation",
        "strategy",
        "return",
        "growth",
        "income",
        "risk",
    ]

    # Check if query involves investment advice
    question = query.question.lower()
    requires_risk = any(keyword in question for keyword in risk_required_keywords)

    # Always require risk profile for portfolio analysis
    if query.portfolio_value is not None:
        return True

    return requires_risk


def categorize_query(query: FinancialQuery) -> str:
    """
    Categorize the type of financial advice being requested.
    """
    categories = {
        "investment": ["invest", "stock", "bond", "portfolio", "fund"],
        "retirement": ["retire", "pension", "401k", "ira"],
        "tax": ["tax", "deduction", "write-off", "exemption"],
        "estate": ["estate", "will", "trust", "inheritance"],
        "general": ["advice", "recommend", "should i", "how to"],
    }

    question = query.question.lower()

    for category, keywords in categories.items():
        if any(keyword in question for keyword in keywords):
            return category

    return "general"


def get_regulatory_warnings(query: FinancialQuery) -> List[str]:
    """
    Generate list of required regulatory warnings based on query type.
    """
    warnings = []
    category = categorize_query(query)

    # Base warning for all financial advice
    warnings.append(
        "This information is for educational purposes only and not financial advice"
    )

    # Category-specific warnings
    category_warnings = {
        "investment": [
            "Past performance is not indicative of future results",
            "Investment involves risk of loss",
        ],
        "retirement": [
            "Consult a tax professional for specific retirement advice",
            "Early withdrawal penalties may apply",
        ],
        "tax": [
            "Tax laws are subject to change",
            "Consult a tax professional for your specific situation",
        ],
        "estate": [
            "Estate laws vary by jurisdiction",
            "Consult a legal professional for estate planning",
        ],
    }

    warnings.extend(category_warnings.get(category, []))

    # Add risk-specific warnings
    if needs_risk_profile(query):
        warnings.append(
            "A complete risk assessment is required for personalized investment advice"
        )

    return warnings


def get_required_disclaimers(certification_level: str) -> List[str]:
    """
    Get required disclaimers based on certification level.
    """
    # Base disclaimers for all levels
    base_disclaimers = [
        "Past performance is not indicative of future results",
        "Financial advice may not be suitable for everyone",
    ]

    level_specific_disclaimers = {
        "general": [
            "This is general information only",
            "Consult a professional for specific advice",
        ],
        "professional": [
            "Advice is based on provided information",
            "Additional consultation may be required",
            "Services provided under professional certification",
        ],
        "expert": [
            "Complex financial products carry significant risks",
            "Services provided under expert certification",
            "Regular review and updates recommended",
        ],
    }

    return base_disclaimers + level_specific_disclaimers.get(certification_level, [])


def needs_risk_warnings(response_text: str) -> bool:
    """
    Determine if response requires additional risk warnings.
    """
    risk_triggers = [
        "invest",
        "risk",
        "return",
        "growth",
        "portfolio",
        "stock",
        "bond",
        "fund",
        "market",
        "trade",
    ]

    return any(trigger in response_text.lower() for trigger in risk_triggers)


def get_required_risk_warnings(response_text: str) -> List[str]:
    """
    Generate risk warnings based on response content.
    """
    warnings = []
    text = response_text.lower()

    # Check for specific investment types and add relevant warnings
    if "stock" in text or "equity" in text:
        warnings.append("Stock investments can result in significant loss of principal")

    if "bond" in text or "fixed income" in text:
        warnings.append("Bond values fluctuate with interest rates and credit quality")

    if "international" in text or "foreign" in text:
        warnings.append(
            "International investments carry additional risks including currency fluctuations"
        )

    if "small" in text and ("cap" in text or "company" in text):
        warnings.append(
            "Small cap investments may have limited liquidity and higher volatility"
        )

    if "high" in text and "yield" in text:
        warnings.append("High yield investments carry increased default risk")

    # Add general warning if any investment terms are found
    if warnings:
        warnings.append(
            "All investments carry risk of loss. Diversification does not guarantee against loss."
        )

    return warnings


# Example usage
async def main():
    # Initialize Permit client
    permit = Permit(
        token=PERMIT_KEY,
        pdp=PDP_URL,
    )

    # Create deps for a free tier user
    deps = PermitDeps(permit=permit, user_id="umavictor11@gmail.com")

    # Try to use our secured agent
    try:
        # Example 1: Basic financial advice (Free tier)
        result = await financial_agent.run(
            "What are some basic investment strategies for beginners?",
            deps=deps,
        )
        print(f"Basic advice result: {result.data}")

        # Example 2: Try premium feature (Portfolio analysis)
        portfolio_result = await financial_agent.run(
            "Can you analyze my investment portfolio? My current allocation is 60% stocks, 30% bonds, 10% cash.",
            deps=deps,
        )
        print(f"Portfolio analysis result: {portfolio_result.data}")

        # Example 3: Access documentation
        docs_result = await financial_agent.run(
            "Can you provide advanced tax optimization strategies?",
            deps=deps,
        )
        print(f"Documentation access result: {docs_result.data}")

    except SecurityError as e:
        print(f"Security check failed: {str(e)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
