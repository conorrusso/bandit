"""
Bandit Vendor Auto-Detector
============================
4-stage pipeline to infer vendor function categories from a name/domain:

  Stage 1 — alias map          (slug → canonical slug before lookup)
  Stage 2 — known vendor match (exact slug match in KNOWN_VENDORS)
  Stage 3 — domain segment     (first segment of domain matches known vendor)
  Stage 4 — keyword inference  (name contains category keywords)
  Stage 5 — unknown fallback   (GENERAL_SAAS, confidence=0.0)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.profiles.vendor_functions import VendorFunction


@dataclass
class AutoDetectResult:
    """Result of vendor function auto-detection."""
    functions: list[VendorFunction]
    confidence: float          # 0.0–1.0
    method: str                # "known_vendor" | "domain_match" | "keyword" | "unknown"
    vendor_slug: str


class VendorAutoDetector:
    """Detect vendor function categories from name + optional domain."""

    # Legal suffixes stripped before slug normalisation
    LEGAL_SUFFIXES = [
        " inc", " inc.", " corp", " corp.", " llc", " ltd", " ltd.",
        " limited", " gmbh", " ag", " sa", " bv", " nv", " plc",
        " group", " holdings", " technologies", " solutions", " software",
        " systems", " services", " platform", " labs",
    ]

    # Keyword sets per function for inference fallback
    KEYWORD_MAP: dict[VendorFunction, list[str]] = {
        VendorFunction.AI_ML: [
            "ai", "ml", "gpt", "llm", "openai", "anthropic", "gemini",
            "intelligence", "neural", "deep learning", "machine learning",
            "copilot", "assistant", "predict",
        ],
        VendorFunction.HEALTHCARE_CLINICAL: [
            "health", "clinical", "medical", "pharma", "ehr", "emr",
            "hospital", "patient", "care", "therapy", "diagnostic",
        ],
        VendorFunction.PAYMENTS: [
            "pay", "stripe", "checkout", "billing", "card", "merchant",
            "transaction", "fintech", "wallet",
        ],
        VendorFunction.FINANCIAL_PROCESSING: [
            "finance", "accounting", "expense", "invoice", "erp", "ap", "ar",
            "procurement", "payroll", "ledger", "audit",
        ],
        VendorFunction.HR_PEOPLE: [
            "hr", "hris", "people", "talent", "recruit", "hire", "workforce",
            "employee", "onboard", "culture", "engagement",
        ],
        VendorFunction.IDENTITY_ACCESS: [
            "identity", "sso", "auth", "okta", "idp", "iam", "saml",
            "oauth", "access", "directory",
        ],
        VendorFunction.SECURITY_TOOLING: [
            "security", "siem", "soc", "endpoint", "vulnerability", "pentest",
            "dlp", "firewall", "threat", "crowdstrike", "sentinel",
        ],
        VendorFunction.INFRASTRUCTURE: [
            "cloud", "aws", "azure", "gcp", "hosting", "cdn", "server",
            "kubernetes", "docker", "infrastructure", "compute",
        ],
        VendorFunction.ANALYTICS_BI: [
            "analytics", "bi", "dashboard", "insights", "metrics", "reporting",
            "datadog", "mixpanel", "amplitude", "tableau", "looker",
        ],
        VendorFunction.COMMUNICATION: [
            "email", "slack", "chat", "messaging", "smtp", "notification",
            "sms", "comms", "mailchimp", "sendgrid", "twilio",
        ],
        VendorFunction.CUSTOMER_DATA: [
            "crm", "salesforce", "hubspot", "customer", "contact", "pipeline",
            "lead", "marketing", "engagement",
        ],
        VendorFunction.LEGAL_COMPLIANCE: [
            "legal", "compliance", "contract", "privacy", "gdpr", "audit trail",
            "ediscovery", "grc", "risk",
        ],
        VendorFunction.SUPPLY_CHAIN: [
            "supply chain", "logistics", "shipping", "fulfillment", "warehouse",
            "vendor management", "procurement", "inventory",
        ],
    }

    # Aliases: normalised slug → canonical slug used in KNOWN_VENDORS
    ALIASES: dict[str, str] = {
        "ms-teams":      "microsoft-teams",
        "teams":         "microsoft-teams",
        "o365":          "microsoft-365",
        "office365":     "microsoft-365",
        "g-suite":       "google-workspace",
        "gsuite":        "google-workspace",
        "gcp":           "google-cloud",
        "aws":           "amazon-web-services",
        "azure":         "microsoft-azure",
        "sfdc":          "salesforce",
        "msft":          "microsoft",
    }

    def detect(
        self,
        vendor_name: str,
        domain: str | None = None,
    ) -> AutoDetectResult:
        """Run 4-stage detection and return AutoDetectResult."""
        from core.profiles.known_vendors import KNOWN_VENDORS

        slug = self._normalise(vendor_name)

        # Stage 1 — alias resolution
        slug = self.ALIASES.get(slug, slug)

        # Stage 2 — exact known vendor match
        if slug in KNOWN_VENDORS:
            return AutoDetectResult(
                functions=list(KNOWN_VENDORS[slug]),
                confidence=1.0,
                method="known_vendor",
                vendor_slug=slug,
            )

        # Stage 3 — domain first-segment match
        if domain:
            domain_slug = domain.split(".")[0].lower().replace("-", "")
            norm_slug = slug.replace("-", "")
            if domain_slug == norm_slug or domain_slug in KNOWN_VENDORS:
                candidate = domain_slug if domain_slug in KNOWN_VENDORS else norm_slug
                if candidate in KNOWN_VENDORS:
                    return AutoDetectResult(
                        functions=list(KNOWN_VENDORS[candidate]),
                        confidence=0.9,
                        method="domain_match",
                        vendor_slug=candidate,
                    )

        # Stage 4 — keyword inference
        name_lower = vendor_name.lower()
        matched_functions: list[VendorFunction] = []
        for fn, keywords in self.KEYWORD_MAP.items():
            if any(kw in name_lower for kw in keywords):
                matched_functions.append(fn)

        if matched_functions:
            return AutoDetectResult(
                functions=matched_functions[:3],  # cap at 3 inferred functions
                confidence=0.6,
                method="keyword",
                vendor_slug=slug,
            )

        # Stage 5 — unknown fallback
        return AutoDetectResult(
            functions=[VendorFunction.GENERAL_SAAS],
            confidence=0.0,
            method="unknown",
            vendor_slug=slug,
        )

    def _normalise(self, name: str) -> str:
        """Normalise a vendor name to a slug for lookup.

        Strips legal suffixes, replaces spaces/underscores with hyphens,
        removes special characters.
        """
        s = name.lower().strip()
        # Remove legal suffixes (longest-first to avoid partial matches)
        for suffix in sorted(self.LEGAL_SUFFIXES, key=len, reverse=True):
            if s.endswith(suffix):
                s = s[: -len(suffix)].strip()
                break
        # Normalise separators
        s = re.sub(r"[\s_]+", "-", s)
        # Remove non-alphanumeric except hyphens
        s = re.sub(r"[^a-z0-9\-]", "", s)
        # Collapse repeated hyphens
        s = re.sub(r"-+", "-", s).strip("-")
        return s


# Module-level singleton
detector = VendorAutoDetector()
