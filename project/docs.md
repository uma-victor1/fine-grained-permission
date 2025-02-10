# Fine-Grained Security for AI Agents

This example demonstrates implementing a secure financial advisor agent using PydanticAI with four distinct security perimeters. It shows how to build a production-ready AI system that enforces certification requirements, regulatory compliance, and proper risk management.

Demonstrates:

- [dynamic system prompt](../agents.md#system-prompts)
- [structured `result_type`](../results.md#structured-result-validation)
- [result validation](../results.md#result-validators-functions)
- [tools](../tools.md)

## Security Perimeters Overview

### Prompt Validation

Controls what financial questions users can ask based on:

- Advisor certification level required (general, professional, expert)
- Regulatory requirements for different advice types
- Portfolio analysis permissions

```python
@financial_agent.tool
async def validate_financial_query(
ctx: RunContext[PermitDeps],
query: FinancialQuery,
) -> Dict[str, bool]:
```

### RAG Permissions

Manages access to financial documentation and knowledge bases:

- Basic financial education materials
- Professional advisor resources
- Expert-level analysis tools
- Regulatory compliance documentation

```python
@financial_agent.tool
async def access_financial_knowledge(
ctx: RunContext[PermitDeps],
query: FinancialQuery
) -> List[str]:

```

### Action Permissions

Controls access to specific financial advisory actions:

- Basic financial advice
- Portfolio analysis capabilities
- Investment recommendations
- Risk assessment tools

```python
@financial_agent.tool
async def check_action_permissions(
ctx: RunContext[PermitDeps],
action: str,
context: UserContext
) -> bool:

```

### Response Validation

Ensures compliance in financial advice delivery:

- Required disclaimers
- Risk warnings
- Certification level disclosure
- Regulatory compliance checks

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
