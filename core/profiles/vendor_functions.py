"""
Bandit Vendor Function Profiles
=================================
Defines vendor function categories and the weight/document modifiers
that each category applies to an assessment.
"""
from __future__ import annotations

from enum import Enum


class VendorFunction(str, Enum):
    FINANCIAL_PROCESSING = "financial_processing"
    HR_PEOPLE            = "hr_people"
    CUSTOMER_DATA        = "customer_data"
    INFRASTRUCTURE       = "infrastructure"
    COMMUNICATION        = "communication"
    ANALYTICS_BI         = "analytics_bi"
    IDENTITY_ACCESS      = "identity_access"
    SECURITY_TOOLING     = "security_tooling"
    AI_ML                = "ai_ml"
    PAYMENTS             = "payments"
    HEALTHCARE_CLINICAL  = "healthcare_clinical"
    LEGAL_COMPLIANCE     = "legal_compliance"
    SUPPLY_CHAIN         = "supply_chain"
    GENERAL_SAAS         = "general_saas"


# Display names for CLI/report output
FUNCTION_LABELS: dict[VendorFunction, str] = {
    VendorFunction.FINANCIAL_PROCESSING: "Financial Processing",
    VendorFunction.HR_PEOPLE:            "HR / People",
    VendorFunction.CUSTOMER_DATA:        "Customer Data",
    VendorFunction.INFRASTRUCTURE:       "Infrastructure / Cloud",
    VendorFunction.COMMUNICATION:        "Communication / Messaging",
    VendorFunction.ANALYTICS_BI:         "Analytics / BI",
    VendorFunction.IDENTITY_ACCESS:      "Identity & Access",
    VendorFunction.SECURITY_TOOLING:     "Security Tooling",
    VendorFunction.AI_ML:                "AI / ML",
    VendorFunction.PAYMENTS:             "Payments",
    VendorFunction.HEALTHCARE_CLINICAL:  "Healthcare / Clinical",
    VendorFunction.LEGAL_COMPLIANCE:     "Legal / Compliance",
    VendorFunction.SUPPLY_CHAIN:         "Supply Chain",
    VendorFunction.GENERAL_SAAS:         "General SaaS",
}


# Per-function weight modifiers and document expectations.
# weight_modifiers: added to dimension weights when this function is detected.
# expected_docs: documents that are typically available and should be requested.
# required_docs: documents that MUST be obtained before approval.
# notes: short rationale for compliance teams.
FUNCTION_MODIFIERS: dict[VendorFunction, dict] = {
    VendorFunction.FINANCIAL_PROCESSING: {
        "weight_modifiers": {"D7": 0.5, "D8": 0.5},
        "expected_docs": ["SOC 1 Type II", "MSA"],
        "required_docs": [],
        "notes": "SOC 1 Type II relevant for financial controls; retention and DPA critical.",
    },
    VendorFunction.HR_PEOPLE: {
        "weight_modifiers": {"D1": 0.5, "D3": 0.5, "D5": 0.5, "D8": 0.5},
        "expected_docs": ["DPA", "SOC 2 Type II"],
        "required_docs": ["DPA"],
        "notes": "Employee data under GDPR Art. 88; Art. 28 DPA required for EU employers.",
    },
    VendorFunction.CUSTOMER_DATA: {
        "weight_modifiers": {"D1": 0.5, "D2": 0.5, "D3": 0.5},
        "expected_docs": ["DPA", "Privacy Policy"],
        "required_docs": [],
        "notes": "Direct customer data exposure — minimization and rights are highest risk.",
    },
    VendorFunction.INFRASTRUCTURE: {
        "weight_modifiers": {"D4": 0.5, "D5": 0.5},
        "expected_docs": ["SOC 2 Type II", "ISO 27001", "DPA"],
        "required_docs": [],
        "notes": "Infrastructure vendors own physical layer — transfer mechanisms and breach response matter.",
    },
    VendorFunction.COMMUNICATION: {
        "weight_modifiers": {"D1": 0.5, "D2": 0.5},
        "expected_docs": ["DPA", "Privacy Policy"],
        "required_docs": [],
        "notes": "Email/messaging vendors often retain content; minimization and sub-processor chain critical.",
    },
    VendorFunction.ANALYTICS_BI: {
        "weight_modifiers": {"D1": 0.5, "D6": 0.5},
        "expected_docs": ["DPA", "Privacy Policy"],
        "required_docs": [],
        "notes": "Analytics vendors frequently use data for model training — D6 AI/ML risk elevated.",
    },
    VendorFunction.IDENTITY_ACCESS: {
        "weight_modifiers": {"D5": 0.5, "D8": 0.5},
        "expected_docs": ["SOC 2 Type II", "DPA"],
        "required_docs": [],
        "notes": "IAM vendors hold credentials; breach notification and DPA obligations are critical.",
    },
    VendorFunction.SECURITY_TOOLING: {
        "weight_modifiers": {"D5": 0.5, "D2": 0.5},
        "expected_docs": ["SOC 2 Type II", "Pen Test Report"],
        "required_docs": [],
        "notes": "Security vendors have elevated access; sub-processor chain and breach response matter.",
    },
    VendorFunction.AI_ML: {
        "weight_modifiers": {"D6": 1.0, "D1": 0.5},
        "expected_docs": ["DPA", "Model Card", "Privacy Policy"],
        "required_docs": [],
        "notes": "AI vendors: EU AI Act + FTC disgorgement risk. D6 weighted highest.",
    },
    VendorFunction.PAYMENTS: {
        "weight_modifiers": {"D7": 0.5, "D8": 0.5, "D5": 0.5},
        "expected_docs": ["PCI DSS AOC", "DPA"],
        "required_docs": ["PCI DSS AOC"],
        "notes": "PCI-DSS cardholder data requirements: retention, breach, and DPA mandatory.",
    },
    VendorFunction.HEALTHCARE_CLINICAL: {
        "weight_modifiers": {"D5": 1.0, "D1": 0.5, "D3": 0.5, "D8": 0.5},
        "expected_docs": ["HIPAA BAA", "DPA", "SOC 2 Type II"],
        "required_docs": ["HIPAA BAA"],
        "notes": "HIPAA BAA required for PHI; 60-day breach notification; D5 highest risk.",
    },
    VendorFunction.LEGAL_COMPLIANCE: {
        "weight_modifiers": {"D8": 0.5, "D2": 0.5},
        "expected_docs": ["DPA", "MSA"],
        "required_docs": ["DPA"],
        "notes": "Legal/compliance vendors often hold privileged data; DPA and sub-processor chain critical.",
    },
    VendorFunction.SUPPLY_CHAIN: {
        "weight_modifiers": {"D2": 0.5, "D4": 0.5},
        "expected_docs": ["DPA", "Privacy Policy"],
        "required_docs": [],
        "notes": "Supply chain vendors introduce cross-border transfer risk; sub-processor visibility needed.",
    },
    VendorFunction.GENERAL_SAAS: {
        "weight_modifiers": {},
        "expected_docs": ["Privacy Policy"],
        "required_docs": [],
        "notes": "No specific function detected — applying baseline weights.",
    },
}


def get_weight_modifiers(functions: list[VendorFunction]) -> dict[str, float]:
    """Combine weight modifiers from multiple vendor functions.

    Returns a dict of dimension → total additive modifier.
    Capped at 2.0 per dimension to prevent runaway stacking.
    """
    combined: dict[str, float] = {}
    for fn in functions:
        mods = FUNCTION_MODIFIERS.get(fn, {}).get("weight_modifiers", {})
        for dim, delta in mods.items():
            combined[dim] = min(2.0, combined.get(dim, 0.0) + delta)
    return combined


def get_expected_docs(functions: list[VendorFunction]) -> list[str]:
    """Return deduplicated list of expected documents across all functions."""
    docs: list[str] = []
    seen: set[str] = set()
    for fn in functions:
        for doc in FUNCTION_MODIFIERS.get(fn, {}).get("expected_docs", []):
            if doc not in seen:
                docs.append(doc)
                seen.add(doc)
    return docs


def get_required_docs(functions: list[VendorFunction]) -> list[str]:
    """Return deduplicated list of required documents across all functions."""
    docs: list[str] = []
    seen: set[str] = set()
    for fn in functions:
        for doc in FUNCTION_MODIFIERS.get(fn, {}).get("required_docs", []):
            if doc not in seen:
                docs.append(doc)
                seen.add(doc)
    return docs
