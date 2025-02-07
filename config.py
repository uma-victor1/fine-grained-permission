"""
Configuration script to set up required resources and policies in Permit.io
for the financial advisor secure agent.
"""

import asyncio
from permit import Permit
import os
from dotenv import load_dotenv

load_dotenv()

# API keys
PERMIT_KEY = os.environ["PERMIT_KEY"]
PDP_URL = "http://localhost:7100"

# Initialize Permit.io SDK
permit = Permit(
    pdp=PDP_URL,
    token=PERMIT_KEY,
)

# Define resources for Financial Advisor security
resources = [
    {
        "key": "financial_query",
        "name": "Financial Query",
        "description": "User financial queries and analysis requests",
        "actions": {
            "submit": {},
            "analyze_portfolio": {},
        },
        "attributes": {
            "length": {
                "type": "number",
                "description": "Length of the query in characters",
            }
        },
    },
    {
        "key": "financial_advice",
        "name": "Financial Advice",
        "description": "AI agent financial recommendations",
        "actions": {
            "receive": {},
            "access_premium": {},
        },
        "attributes": {
            "length": {
                "type": "number",
                "description": "Length of the advice in characters",
            }
        },
    },
    {
        "key": "documentation",
        "name": "Documentation",
        "description": "Financial documentation and resources",
        "actions": {
            "read": {},
            "access_premium_docs": {},
        },
    },
    {
        "key": "api",
        "name": "API",
        "description": "External financial API endpoints",
        "actions": {
            "access": {},
        },
        "attributes": {
            "endpoint": {
                "type": "string",
                "description": "API endpoint identifier",
            }
        },
    },
]

# Define roles and their permissions
roles = [
    {
        "name": "free_tier",
        "permissions": [
            {"resource": "financial_query", "actions": ["submit"]},
            {"resource": "financial_advice", "actions": ["receive"]},
            {"resource": "documentation", "actions": ["read"]},
        ],
    },
    {
        "name": "premium_tier",
        "permissions": [
            {
                "resource": "financial_query",
                "actions": ["submit", "analyze_portfolio"],
            },
            {
                "resource": "financial_advice",
                "actions": ["receive", "access_premium"],
            },
            {
                "resource": "documentation",
                "actions": ["read", "access_premium_docs"],
            },
            {"resource": "api", "actions": ["access"]},
        ],
    },
]


async def create_permit_config():
    # Create resources
    for resource in resources:
        try:
            await permit.api.resources.create(resource)
            print(f"Created resource: {resource['name']}")
        except Exception as e:
            print(f"Error creating resource {resource['name']}: {str(e)}")

    # Create roles
    for role in roles:
        try:
            # Build role permissions list
            role_permissions = []
            for permission in role.get("permissions", []):
                role_permissions.extend(
                    [
                        f"{permission['resource']}:{action}"
                        for action in permission["actions"]
                    ]
                )

            # Create role object
            role_obj = {
                "name": role["name"],
                "key": role["name"].lower().replace(" ", "_"),
                "permissions": role_permissions,
                "description": f"Role for {role['name']} users",
            }

            await permit.api.roles.create(role_obj)
            print(f"Created role: {role['name']}")
        except Exception as e:
            print(f"Error creating role {role['name']}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(create_permit_config())
