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
        "key": "certification",
        "name": "Advisor Certification",
        "description": "Certification levels for financial advice",
        "actions": {
            "provide_advice": {},
            "regulatory_compliance": {},
        },
        "attributes": {
            "level": {
                "type": "string",
                "description": "Certification level (general, professional, expert)",
            },
            "category": {
                "type": "string",
                "description": "Type of financial advice",
            },
        },
    },
    {
        "key": "documentation",
        "name": "Financial Documentation",
        "description": "Financial knowledge and resources",
        "actions": {
            "access_professional_docs": {},
            "access_expert_docs": {},
        },
        "attributes": {
            "content_type": {
                "type": "string",
                "description": "Type of financial documentation",
            }
        },
    },
    {
        "key": "financial_action",
        "name": "Financial Actions",
        "description": "Protected financial advisory actions",
        "actions": {
            "provide": {},
            "analyze": {},
            "recommend": {},
        },
        "attributes": {
            "action": {
                "type": "string",
                "description": "Specific financial action type",
            }
        },
    },
    {
        "key": "response",
        "name": "Financial Response",
        "description": "Financial advice response validation",
        "actions": {
            "compliance_validation": {},
        },
        "attributes": {
            "certification": {
                "type": "string",
                "description": "Required certification level",
            }
        },
    },
]

# Define roles with new permissions structure
roles = [
    {
        "name": "general_advisor",
        "permissions": [
            {"resource": "certification", "actions": ["provide_advice"]},
            {"resource": "documentation", "actions": []},  # Basic docs only
            {"resource": "financial_action", "actions": ["provide"]},
            {"resource": "response", "actions": ["compliance_validation"]},
        ],
    },
    {
        "name": "professional_advisor",
        "permissions": [
            {
                "resource": "certification",
                "actions": ["provide_advice", "regulatory_compliance"],
            },
            {
                "resource": "documentation",
                "actions": ["access_professional_docs"],
            },
            {
                "resource": "financial_action",
                "actions": ["provide", "analyze"],
            },
            {"resource": "response", "actions": ["compliance_validation"]},
        ],
    },
    {
        "name": "expert_advisor",
        "permissions": [
            {
                "resource": "certification",
                "actions": ["provide_advice", "regulatory_compliance"],
            },
            {
                "resource": "documentation",
                "actions": ["access_professional_docs", "access_expert_docs"],
            },
            {
                "resource": "financial_action",
                "actions": ["provide", "analyze", "recommend"],
            },
            {"resource": "response", "actions": ["compliance_validation"]},
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
