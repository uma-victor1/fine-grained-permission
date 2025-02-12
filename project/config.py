"""
Permit.io configuration for Financial Advisor security perimeters.
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
        "key": "financial_advice",
        "name": "Financial Advice",
        "description": "AI-generated financial advice",
        "actions": {
            "receive": {},
        },
        "attributes": {
            "includes_ai_advice": {
                "type": "bool",
                "description": "Whether the content includes financial advice",
            }
        },
    },
    {
        "key": "financial_document",
        "name": "Financial Document",
        "description": "Financial knowledge documents",
        "actions": {
            "read": {},
        },
        "attributes": {
            "doc_type": {
                "type": "string",
                "description": "Type of financial document",
            },
            "classification": {
                "type": "string",
                "description": "Document classification level",
            },
        },
    },
    {
        "key": "financial_response",
        "name": "Financial Response",
        "description": "AI-generated response content",
        "actions": {
            "requires_disclaimer": {},
        },
        "attributes": {
            "content": {
                "type": "string",
                "description": "Response content to analyze",
            }
        },
    },
    {
        "key": "portfolio",
        "name": "Investment Portfolio",
        "description": "User investment portfolio",
        "actions": {
            "update": {},
        },
        "attributes": {
            "owner_id": {
                "type": "string",
                "description": "Portfolio owner ID",
            }
        },
    },
]

# Define roles with new permissions structure
roles = [
    {
        "name": "basic_user",
        "permissions": [
            {"resource": "financial_advice", "actions": ["receive"]},
            {"resource": "financial_document", "actions": ["read"]},
        ],
    },
    {
        "name": "premium_user",
        "permissions": [
            {"resource": "financial_advice", "actions": ["receive"]},
            {"resource": "financial_document", "actions": ["read"]},
            {"resource": "portfolio", "actions": ["update"]},
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
                "description": f"Role for {role['name']}",
            }

            await permit.api.roles.create(role_obj)
            print(f"Created role: {role['name']}")
        except Exception as e:
            print(f"Error creating role {role['name']}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(create_permit_config())
