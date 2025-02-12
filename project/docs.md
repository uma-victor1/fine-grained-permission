# Fine-Grained Security for AI Agents

This example demonstrates implementing a secure financial advisor agent using PydanticAI with four distinct security perimeters. It shows how to build a production-ready AI system that enforces certification requirements, regulatory compliance, and proper risk management.

Demonstrates:

- [dynamic system prompt](../agents.md#system-prompts)
- [structured `result_type`](../results.md#structured-result-validation)
- [result validation](../results.md#result-validators-functions)
- [tools](../tools.md)

## Security Perimeters Overview

### Prompt Validation

Validates whether users have explicitly consented to receive AI-generated financial advice.

Key checks:

- User has explicitly opted in to AI financial advice
- Consent is properly recorded and verified
- Compliance with regulatory requirements for automated advice

```python
@financial_agent.tool
async def validate_financial_query(
ctx: RunContext[PermitDeps],
query: FinancialQuery,
) -> Dict[str, bool]:
```

### RAG Permissions

Controls access to financial knowledge base and documentation based on user permissions and document classification levels

- Document classification levels (public, restricted, confidential)
- User clearance level verification
- Regulatory compliance for information access
- Audit trail of document access

```python
@financial_agent.tool
async def access_financial_knowledge(
ctx: RunContext[PermitDeps],
query: FinancialQuery
) -> List[str]:

```

### Action Permissions

Controls permissions for sensitive financial operations, particularly portfolio modifications.

- Portfolio ownership verification
- User authorization level
- Transaction limits compliance
- Account access restrictions

```python
@financial_agent.tool
async def check_action_permissions(
ctx: RunContext[PermitDeps],
action: str,
context: UserContext
) -> bool:

```

### Response Validation

Ensures all financial advice responses meet regulatory requirements and include
necessary disclaimers.

- Automated advice detection using Permit
- Regulatory disclaimer insertion
- Compliance verification

```
@financial_agent.tool
async def validate_financial_response(
ctx: RunContext[PermitDeps],
response: FinancialResponse,
context: UserContext
) -> Dict[str, bool]:

```

## Running the Example

First, configure your Permit.io environment:

```bash
export PERMIT_API_KEY='your-api-key'
```

Update the API key and PDP url in the example code:

```python
Permit(
token="YOUR_API_KEY", # Replace with your actual API key
pdp="http://localhost:7766",
)
```

Here's a visualization of the control flow:

```
User Request
     ↓
PydanticAI Framework
     ↓
validate_financial_query  →  [If fails, stops here]
     ↓
advisor certification check
     ↓
Claude AI Processing     ←  [PydanticAI hands control to Claude]
     ↓
validate_financial_advice →  [If fails, stops here]
     ↓
access_financial_knowledge →  [If fails, stops here]
     ↓
Compliance Check
     ↓
Response to User
```

## Running the Example

With [dependencies installed and environment variables set](./index.md#usage), run:

```bash
python/uv-run -m pydantic_ai_examples.secure-ai-agent
```

## Example Code

```python {title="secure_ai_agent.py"}
#! examples/pydantic_ai_examples/secure-ai-agent.py
```
