"""
PydanticAI demonstration of the AI Access Control Four Perimeters Framework

This implementation demonstrates the four access control perimeters framework with a practical example of a financial advisor agent:
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
PDP_URL = "http://localhost:7766"


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


class UserContext(BaseModel):
    """User context with permissions information"""

    user_id: str
    tier: str = Field(default="free")


class FinancialDocument(BaseModel):
    """Model for financial documents"""

    id: str
    type: str = Field(
        ..., description="Document type (e.g., 'investment', 'tax', 'retirement')"
    )
    content: str
    classification: str = Field(..., description="Document classification level")


class FinancialQuery(BaseModel):
    """Input model for financial queries"""

    question: str
    context: UserContext
    documents: Optional[List[FinancialDocument]] = None


class FinancialResponse(BaseModel):
    """Output model for financial advice"""

    answer: str
    includes_advice: bool = False
    disclaimer_added: bool = False


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
) -> bool:
    """SECURITY PERIMETER 1: Prompt Validation
    Validates whether users have explicitly consented to receive AI-generated financial advice.
    Ensures compliance with financial regulations regarding automated advice systems.

    Key checks:
    - User has explicitly opted in to AI financial advice
    - Consent is properly recorded and verified

    Args:
        ctx: Context containing Permit client and user ID
        query: The financial query to validate

    Returns:
        bool: True if user has consented to AI advice, False otherwise
    """
    try:
        permitted = await ctx.deps.permit.check(
            # The user object with their attributes
            {
                "key": ctx.deps.user_id,
                "attributes": {
                    # This attribute would be set when user opts in
                    "ai_advice_opted_in": "false"
                },
            },
            # The action being performed
            "receive",
            # The resource being accessed
            {"type": "financial_advice", "attributes": {"is_ai_generated": "false"}},
        )

        if not permitted:
            raise SecurityError(
                "User has not opted in to receive AI-generated financial advice"
            )

        return True

    except PermitApiError as e:
        raise SecurityError(f"Advice permission check failed: {str(e)}")


@financial_agent.tool
async def access_financial_knowledge(
    ctx: RunContext[PermitDeps], documents: List[FinancialDocument]
) -> List[FinancialDocument]:
    """SECURITY PERIMETER 2: RAG Protection
    Controls access to financial knowledge base and documentation based on user permissions
    and document classification levels. Implements information barriers and content restrictions.

    Key aspects:
    - Document classification levels (public, restricted, confidential)
    - User clearance level verification
    - Regulatory compliance for information access

    Args:
        ctx: Context containing Permit client and user ID
        documents: List of financial documents to filter

    Returns:
        List[FinancialDocument]: Filtered list of documents user is allowed to access
    """
    try:
        # Create resource instances for each document
        resources = [
            {
                "type": "financial_document",
                "attributes": {
                    "doc_type": doc.type,
                    "classification": doc.classification,
                },
            }
            for doc in documents
        ]

        # Use Permit's filter_objects to get allowed documents
        allowed_docs = await ctx.deps.permit.filter_objects(
            ctx.deps.user_id, "read", resources
        )

        # Return only the documents that were allowed
        allowed_ids = {doc["id"] for doc in allowed_docs}
        return [doc for doc in documents if doc.id in allowed_ids]

    except PermitApiError as e:
        raise SecurityError(f"Failed to filter documents: {str(e)}")


@financial_agent.tool
async def check_action_permissions(
    ctx: RunContext[PermitDeps], action: str, context: UserContext, portfolio_id: str
) -> bool:
    """SECURITY PERIMETER 3: Action Authorization
    Controls permissions for sensitive financial operations, particularly portfolio
    modifications. Ensures only authorized users can perform account-level changes.

    Key checks:
    - Portfolio ownership verification

    Args:
        ctx: Context containing Permit client and user ID
        portfolio_id: Identifier of the portfolio to update

    Returns:
        bool: True if user is authorized to update portfolio, False otherwise
    """

    try:
        return await ctx.deps.permit.check(
            ctx.deps.user_id,
            "update",
            {
                "type": "portfolio",
            },
        )
    except PermitApiError as e:
        raise SecurityError(f"Failed to check portfolio update permission: {str(e)}")


@financial_agent.tool
async def validate_financial_response(
    ctx: RunContext[PermitDeps], response: FinancialResponse
) -> FinancialResponse:
    """SECURITY PERIMETER 4: Secure Responses
    Ensures all financial advice responses meet regulatory requirements and include
    necessary disclaimers.

    Key features:
    - Automated advice detection using Permit
    - Regulatory disclaimer insertion


    Args:
        ctx: Context containing Permit client and user ID
        response: The financial response to validate

    Returns:
        FinancialResponse: Validated response with appropriate disclaimers added
    """

    try:
        # Check if response contains financial advice using Permit
        contains_advice = await ctx.deps.permit.check(
            ctx.deps.user_id,
            "requires_disclaimer",
            {"type": "financial_response", "attributes": {"content": response.answer}},
        )

        if contains_advice:
            disclaimer = (
                "\n\nIMPORTANT DISCLAIMER: This is AI-generated financial advice. "
                "This information is for educational purposes only and should not be "
                "considered as professional financial advice. Always consult with a "
                "qualified financial advisor before making investment decisions."
            )
            response.answer += disclaimer
            response.disclaimer_added = True

        return response

    except PermitApiError as e:
        raise SecurityError(f"Failed to check response content: {str(e)}")


# Initialize example documents
SAMPLE_DOCUMENTS = {
    "inv_001": FinancialDocument(
        id="inv_001",
        type="investment",
        content="Tech Growth Fund performance analysis shows a 15% YoY return...",
        classification="confidential",
    ),
    "tax_001": FinancialDocument(
        id="tax_001",
        type="tax",
        content="Tax optimization strategies for high-income investors...",
        classification="restricted",
    ),
    "ret_001": FinancialDocument(
        id="ret_001",
        type="retirement",
        content="401(k) contribution strategies and employer matching...",
        classification="public",
    ),
    "inv_002": FinancialDocument(
        id="inv_002",
        type="investment",
        content="ESG Fund analysis and sustainable investment opportunities...",
        classification="public",
    ),
}


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
