# Fine-Grained Security for AI Agents

Complete example of building a secure financial advisor agent with PydanticAI. This example demonstrates how to implement security perimeters around AI agents.

Demonstrates:

- [dynamic system prompt](../agents.md#system-prompts)
- [structured `result_type`](../results.md#structured-result-validation)
- [result validation](../results.md#result-validators-functions)
- [tools](../tools.md)

This example creates a secure financial advisor agent that checks permissions before doing anything - like a security guard for an AI. Here are the key parts:

- Basic setup of the Financial Advisor Agent
- Input validation with query length checks
- Output validation with length and compliance check
- Documentation access for different tiers
- API access control for market data

Error handling for security violations

### Security Checks:

- Checks if users are allowed to ask questions (input validation)
- Checks if users are allowed to see answers (output validation)

### User Levels:

- Free users: Can only send/receive short messages (100 characters)
- Premium users: Can send/receive longer messages (1000 characters) and access special features

## RAG

- Access to Documentation

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

Security Perimeters:

- validate_financial_query: checks user's query permissions
- validate_financial_advice: Checks premium feature access
- access_financial_knowledge: Controls access to financial documentation
- validate_market_data_access: Controls access to market data APIs

Here's a visualization of the control flow:

```
User Request
     ↓
PydanticAI Framework
     ↓
validate_financial_query  →  [If fails, stops here]
     ↓
Claude AI Processing     ←  [PydanticAI hands control to Claude]
     ↓
validate_financial_advice →  [If fails, stops here]
     ↓
access_financial_knowledge →  [If fails, stops here]
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
