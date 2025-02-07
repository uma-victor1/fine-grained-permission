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
    """Input model with validation constraints"""

    question: str
    context: UserContext
    portfolio_value: Optional[float] = None


class FinancialResponse(BaseModel):
    """Output model with validation and compliance"""

    answer: str
    compliance_notes: List[str] = Field(default_factory=list)
    used_premium_features: bool = False


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
    """Check if user has permission to submit this financial query.

    Args:
        ctx: Context containing Permit client and user ID
        query: The financial query to validate

    Returns:
        Dict containing permission result and warnings
    """
    print(query)
    try:
        portfolio_permitted = None
        # Check basic input length permission
        permitted = await ctx.deps.permit.check(
            # the user object
            {
                # the user key
                "key": ctx.deps.user_id,
            },
            "submit",
            {
                "type": "financial_queries",
                "attributes": {"length": len(query.question)},
            },
        )
        # Check portfolio analysis permission if value provided
        if query.portfolio_value is not None:
            portfolio_permitted = await ctx.deps.permit.check(
                ctx.deps.user_id, "analyze_portfolio", "financial_analysis"
            )
            permitted = permitted and portfolio_permitted

        return {
            "permitted": permitted,
            "warnings": ["Portfolio analysis requires premium"]
            if not portfolio_permitted
            else [],
        }

    except PermitApiError as e:
        raise SecurityError(f"Permission check failed: {str(e)}")


@financial_agent.tool
async def validate_financial_advice(
    ctx: RunContext[PermitDeps], response: FinancialResponse, context: UserContext
) -> Dict[str, bool]:
    """Validate if user is allowed to receive this financial advice.

    Args:
        ctx: Context containing Permit client and user ID
        response: The response to validate
        context: User context with permissions

    Returns:
        Dict containing permission result and warnings
    """
    try:
        premium_permitted = None

        # Check basic output permission
        permitted = await ctx.deps.permit.check(
            ctx.deps.user_id,
            "receive",
            {
                "type": "financial_advice",
                "attributes": {"length": len(response.answer)},
            },
        )

        # Check premium feature usage
        if response.used_premium_features:
            premium_permitted = await ctx.deps.permit.check(
                ctx.deps.user_id, "access_premium", "financial_advice"
            )
            permitted = permitted and premium_permitted

        return {
            "permitted": permitted,
            "warnings": ["Premium features not available"]
            if not premium_permitted
            else [],
        }

    except PermitApiError as e:
        raise SecurityError(f"Permission check failed: {str(e)}")


@financial_agent.tool
async def access_financial_knowledge(
    ctx: RunContext[PermitDeps], query: FinancialQuery
) -> List[str]:
    """Check documentation access permissions and return allowed docs.

    Args:
        ctx: Context containing Permit client and user ID
        query: The financial query containing user context

    Returns:
        List of allowed documentation types
    """
    try:
        # Check basic documentation access
        basic_docs = ["general_advice", "market_basics"]

        # Check premium documentation access
        premium_permitted = await ctx.deps.permit.check(
            ctx.deps.user_id, "access_premium_docs", "documentation"
        )

        if premium_permitted:
            return basic_docs + [
                "advanced_strategies",
                "tax_planning",
                "portfolio_optimization",
            ]

        return basic_docs

    except PermitApiError as e:
        raise SecurityError(f"Documentation access check failed: {str(e)}")


@financial_agent.tool
async def validate_market_data_access(
    ctx: RunContext[PermitDeps], context: UserContext
) -> bool:
    """Check if agent can make external API calls for user.

    Args:
        ctx: Context containing Permit client and user ID
        context: User context with permissions

    Returns:
        Boolean indicating if access is permitted
    """
    try:
        api_permissions = {
            "market_data": await ctx.deps.permit.check(
                ctx.deps.user_id,
                "access",
                {"type": "api", "attributes": {"endpoint": "market_data"}},
            ),
            "portfolio_analysis": await ctx.deps.permit.check(
                ctx.deps.user_id,
                "access",
                {"type": "api", "attributes": {"endpoint": "portfolio_analysis"}},
            ),
        }

        # User needs both permissions for full API access
        return all(api_permissions.values())

    except PermitApiError as e:
        raise SecurityError(f"API permission check failed: {str(e)}")


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

        # Example 3: Access premium documentation
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
