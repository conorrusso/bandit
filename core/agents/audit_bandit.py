"""
Audit Bandit — specialist security audit agent.

Analyses SOC 2 reports, ISO certificates, and other audit evidence
to produce high-confidence signals for D2, D5, D7, and D8.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional, Callable

from core.agents.agent_base import (
    BaseAgent,
    AgentDocument,
    AgentResult,
)

logger = logging.getLogger("bandit")

# Document types that trigger Audit Bandit
AUDIT_DOC_TYPES = {
    "SOC2_TYPE2",
    "SOC2_TYPE1",
    "SOC1_TYPE2",
    "ISO27001",
    "ISO27701",
    "ISO42001",
    "PENTEST_SUMMARY",
    "HITRUST",
    "FEDRAMP_ATO",
    "VULNERABILITY_DISCLOSURE",
    "PCI_AOC",
    "PCI_ROC",
}

SYSTEM_PROMPT = """You are a senior IT auditor and \
GRC analyst evaluating vendor security and compliance \
evidence. You assess SOC 2 reports, ISO certificates, \
and audit documents for enterprise procurement teams.

Focus on: audit currency, exception items, scope \
coverage, and whether the evidence supports or \
contradicts the vendor's DPA and privacy policy claims.

Return ONLY valid JSON. Be precise. Only report \
what is explicitly stated. Flag any exceptions, \
qualifications, or scope limitations found."""


class AuditBandit(BaseAgent):
    """
    Audit Bandit — specialist security audit agent.

    Analyses SOC 2 reports, ISO certificates, and
    other audit evidence to produce high-confidence
    signals for D2, D5, D7, and D8.

    Key questions answered:
    - Is the SOC 2 current? (audit period end date)
    - Were there exceptions?
    - Does it cover Privacy TSC?
    - Is ISO 27001/27701 current? What scope?
    - Does audit evidence contradict DPA claims?
    """

    name = "Audit Bandit"

    def __init__(
        self,
        provider,
        on_progress: Optional[Callable] = None,
        max_tokens: int = 5000,
    ):
        super().__init__(provider, on_progress, max_tokens)

    def _should_trigger(
        self,
        documents: list[AgentDocument],
    ) -> bool:
        """Trigger if any audit document is present."""
        return any(
            doc.doc_type in AUDIT_DOC_TYPES
            for doc in documents
        )

    def _select_documents(
        self,
        documents: list[AgentDocument],
    ) -> list[AgentDocument]:
        """
        Select audit documents.
        Also include DPA for conflict detection.
        """
        audit_docs = [
            d for d in documents
            if d.doc_type in AUDIT_DOC_TYPES
        ]
        dpa_docs = [
            d for d in documents
            if d.doc_type == "DPA"
        ]

        # Up to 3 audit docs + DPA if present
        selected = audit_docs[:3]
        if dpa_docs:
            selected += dpa_docs[:1]

        return selected

    def _build_prompt(
        self,
        vendor_name: str,
        documents: list[AgentDocument],
        intake_context: str | None,
    ) -> str:
        """Build the audit analysis prompt."""

        today = date.today().isoformat()
        doc_sections = []
        doc_type_list = []

        for doc in documents:
            text = self._truncate_text(doc.text, 20000)
            doc_sections.append(
                f"=== {doc.doc_type}: {doc.filename} ===\n"
                f"{text}"
            )
            doc_type_list.append(doc.doc_type)

        docs_text = "\n\n".join(doc_sections)
        has_soc2 = any(
            "SOC2" in t for t in doc_type_list
        )
        has_iso27001 = "ISO27001" in doc_type_list
        has_iso27701 = "ISO27701" in doc_type_list
        has_iso42001 = "ISO42001" in doc_type_list
        has_pentest = "PENTEST_SUMMARY" in doc_type_list
        has_dpa = "DPA" in doc_type_list

        intake_section = (
            f"\nIntake context:\n{intake_context}\n"
            if intake_context else ""
        )

        return f"""Analyse the following audit documents \
for {vendor_name}. Today's date is {today}.
{intake_section}
Return ONLY this JSON object:

{{
  "soc2": {{
    "present": {str(has_soc2).lower()},
    "type": "<Type I|Type II|null>",
    "audit_period_end": "<YYYY-MM-DD or null>",
    "is_current": <true|false|null>,
    "months_since_audit": <integer or null>,
    "opinion": "<unqualified|qualified|adverse|null>",
    "exceptions_found": <true|false|null>,
    "exception_count": <integer or null>,
    "exceptions_summary": ["<exception 1>"],
    "criteria_covered": ["<Security|Availability|Confidentiality|Processing Integrity|Privacy>"],
    "privacy_tsc_included": <true|false|null>,
    "privacy_tsc_exceptions": <true|false|null>,
    "sub_processor_controls_noted": <true|false|null>,
    "breach_notification_controls_noted": <true|false|null>,
    "deletion_controls_noted": <true|false|null>,
    "scope_description": "<brief scope summary or null>"
  }},
  "iso27001": {{
    "present": {str(has_iso27001).lower()},
    "cert_date": "<YYYY-MM-DD or null>",
    "expiry_date": "<YYYY-MM-DD or null>",
    "is_current": <true|false|null>,
    "scope": "<what is covered or null>",
    "certification_body": "<name or null>",
    "surveillance_or_recertification": "<surveillance|recertification|initial|null>"
  }},
  "iso27701": {{
    "present": {str(has_iso27701).lower()},
    "cert_date": "<YYYY-MM-DD or null>",
    "expiry_date": "<YYYY-MM-DD or null>",
    "is_current": <true|false|null>,
    "scope": "<what is covered or null>"
  }},
  "iso42001": {{
    "present": {str(has_iso42001).lower()},
    "cert_date": "<YYYY-MM-DD or null>",
    "expiry_date": "<YYYY-MM-DD or null>",
    "is_current": <true|false|null>,
    "scope": "<what is covered or null>"
  }},
  "pentest": {{
    "present": {str(has_pentest).lower()},
    "test_date": "<YYYY-MM-DD or null>",
    "is_current": <true|false|null>,
    "critical_findings": <true|false|null>,
    "high_findings": <true|false|null>,
    "scope": "<what was tested or null>"
  }},
  "dpa_conflicts": [
    {{
      "claim": "<what DPA claims>",
      "evidence": "<what audit doc shows>",
      "severity": "<high|medium|low>"
    }}
  ],
  "framework_evidence": {{
    "soc2_type2_privacy_tsc": <true|false>,
    "soc2_type2_security_only": <true|false>,
    "iso_27001_only": <true|false>,
    "iso_27701_certified": <true|false>,
    "iso_42001_certified": <true|false>
  }},
  "top_findings": [
    "<finding 1 — specific, cite document>",
    "<finding 2>",
    "<finding 3>"
  ],
  "red_flags": ["<concern from audit evidence>"],
  "positive_signals": ["<strength evidenced by audit>"],
  "questions_for_vendor": [
    "<question 1>",
    "<question 2>"
  ],
  "overall_audit_assessment": "<one paragraph summary>"
}}

DOCUMENTS:
{docs_text}"""

    def analyse(
        self,
        vendor_name: str,
        documents: list[AgentDocument],
        intake_context: str | None = None,
    ) -> AgentResult:
        """
        Run Audit Bandit analysis.
        Returns AgentResult with D2/D5/D7/D8 signals.
        """
        if not self._should_trigger(documents):
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error="No audit documents found",
            )

        selected = self._select_documents(documents)
        if not selected:
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error="No suitable audit documents",
            )

        self._progress(
            f"Audit Bandit — analysing "
            f"{len(selected)} document(s)…"
        )

        prompt = self._build_prompt(
            vendor_name, selected, intake_context
        )

        try:
            result = self._call_llm_json(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            logger.error(
                f"Audit Bandit failed for "
                f"{vendor_name}: {e}"
            )
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error=str(e),
            )

        # Build signals
        signals = self._build_signals(result)

        # Framework evidence from audit
        framework_evidence = result.get(
            "framework_evidence", {}
        )
        # Only keep truthy entries
        framework_evidence = {
            k: v for k, v in framework_evidence.items() if v
        }

        findings = result.get("top_findings", [])
        red_flags = result.get("red_flags", [])

        return AgentResult(
            agent_name=self.name,
            vendor_name=vendor_name,
            success=True,
            signals=signals,
            framework_evidence=framework_evidence,
            findings=findings + red_flags,
            raw_result=result,
            documents_analysed=[
                d.filename for d in selected
            ],
        )

    def _build_signals(self, result: dict) -> dict:
        """
        Translate audit result into signals for
        dimensions D2, D5, D7, D8.
        """
        soc2 = result.get("soc2", {})
        iso27001 = result.get("iso27001", {})
        iso27701 = result.get("iso27701", {})

        signals = {}

        # D2 — Sub-processor management
        if soc2.get("sub_processor_controls_noted"):
            signals["d2_sub_processor_controls_audited"] = True
        if soc2.get("privacy_tsc_included") and \
                not soc2.get("privacy_tsc_exceptions"):
            signals["d2_third_party_audit_clean"] = True

        # D5 — Breach notification
        if soc2.get("breach_notification_controls_noted"):
            signals["d5_breach_procedures_audited"] = True

        # D7 — Retention and deletion
        if soc2.get("deletion_controls_noted"):
            signals["d7_deletion_controls_audited"] = True

        # D8 — DPA completeness / independent verification
        if soc2.get("present") and \
                soc2.get("is_current") and \
                not soc2.get("exceptions_found"):
            signals["d8_independent_audit_clean"] = True
        elif soc2.get("present") and \
                soc2.get("exceptions_found"):
            signals["d8_audit_exceptions_found"] = True

        if iso27001.get("present") and \
                iso27001.get("is_current"):
            signals["d8_iso27001_current"] = True

        if iso27701.get("present") and \
                iso27701.get("is_current"):
            signals["d8_iso27701_current"] = True

        # Negative signals
        if soc2.get("present") and \
                not soc2.get("is_current"):
            signals["d8_audit_stale"] = True

        if result.get("dpa_conflicts"):
            signals["d8_dpa_audit_conflict"] = True

        return signals

