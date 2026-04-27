"""
Audit Bandit — specialist security audit agent.

Analyses SOC 2 reports, ISO certificates, and other audit evidence
to produce high-confidence signals for D2, D5, D7, and D8.

Signal names match RUBRIC_SOC2.md and RUBRIC_ISO.md exactly.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from pathlib import Path
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


def _load_rubrics() -> dict:
    """Load all audit-related rubric content."""
    base = Path(__file__).parent.parent / "scoring"
    rubrics = {}
    for filename in [
        "RUBRIC_SOC2.md",
        "RUBRIC_ISO.md",
        "SOC2_FIRMS.md",
        "ISO_CERT_BODIES.md",
    ]:
        path = base / filename
        if path.exists():
            rubrics[filename] = path.read_text()
    return rubrics


def _extract_firm_list(content: str) -> str:
    """Extract firm names from SOC2_FIRMS.md for prompt context."""
    lines = []
    in_list = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and (
            "(" in stripped or "LLP" in stripped
            or "LLC" in stripped or "Inc" in stripped
            or stripped.startswith("- Deloitte")
            or stripped.startswith("- PwC")
            or stripped.startswith("- EY")
            or stripped.startswith("- KPMG")
        ):
            # Extract firm name
            name = stripped[2:].strip()
            lines.append(name)
    return "\n".join(lines) if lines else content[:3000]


def _extract_body_list(content: str) -> str:
    """Extract certification body names from ISO_CERT_BODIES.md."""
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **") and "**" in stripped[4:]:
            name = stripped[4:stripped.index("**", 4)]
            lines.append(name)
    return "\n".join(lines) if lines else content[:3000]


SYSTEM_PROMPT = """\
You are a senior IT auditor and GRC analyst evaluating vendor \
security and compliance evidence. You assess SOC 2 reports, \
ISO certificates, and audit documents for enterprise \
procurement teams.

Critical architectural rules:
- You extract signals only. You NEVER recommend scores.
- Absence is not denial: "Privacy TSC not listed" differs \
from "Privacy TSC explicitly excluded."
- Scope narrowing is a finding, not a score deduction.
- Exceptions require management responses — track both.
- For each TRUE signal, cite the document section.
- Return NULL for signals not addressed in the document.

Return ONLY valid JSON. Be precise. Only report what is \
explicitly stated. Flag any exceptions, qualifications, \
or scope limitations found."""


class AuditBandit(BaseAgent):
    """
    Audit Bandit — specialist security audit agent.

    Analyses SOC 2 reports, ISO certificates, and
    other audit evidence to produce high-confidence
    signals for D2, D5, D7, and D8.
    """

    name = "Audit Bandit"

    def __init__(
        self,
        provider,
        on_progress: Optional[Callable] = None,
        max_tokens: int = 8000,
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
        """Build the audit analysis prompt from RUBRIC_SOC2.md
        and RUBRIC_ISO.md."""

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

        intake_section = (
            f"\nIntake context:\n{intake_context}\n"
            if intake_context else ""
        )

        # Load firm/body lists for recognition
        rubrics = _load_rubrics()
        firms_content = rubrics.get("SOC2_FIRMS.md", "")
        bodies_content = rubrics.get("ISO_CERT_BODIES.md", "")

        firms_list = _extract_firm_list(firms_content)
        bodies_list = _extract_body_list(bodies_content)

        return f"""\
Analyse the following audit documents for {vendor_name}. \
Today's date is {today}.
{intake_section}
For each document, determine the type:
- SOC 2 Type I or Type II report
- ISO 27001 certificate or audit report
- ISO 27701 certificate or audit report
- ISO 42001 certificate or audit report
- Penetration test summary
- Other / unknown

For each signal:
- Mark TRUE only if explicitly stated in the document.
- Mark FALSE only if explicitly contradicted.
- Mark NULL if not addressed.
- For TRUE signals, provide the document section reference.

Return ONLY this JSON object — no markdown, no explanation:

{{
  "soc2_signals": {{
    "soc2_type2_present": <true|false|null>,
    "soc2_type2_present_source": "<section or null>",
    "soc2_type1_present": <true|false|null>,
    "soc3_present": <true|false|null>,
    "audit_period_start": "<YYYY-MM-DD or null>",
    "audit_period_end": "<YYYY-MM-DD or null>",
    "report_issuance_date": "<YYYY-MM-DD or null>",
    "audit_period_months": <integer or null>,
    "bridge_letter_present": <true|false|null>,
    "bridge_letter_period_end": "<YYYY-MM-DD or null>",
    "auditor_firm_name": "<exact name or null>",
    "auditor_firm_recognised": <true|false|null>,
    "auditor_firm_location": "<location or null>",
    "auditor_aicpa_member_stated": <true|false|null>,
    "opinion_type": "<unqualified|qualified|adverse|disclaimer|null>",
    "opinion_qualifier_description": "<description or null>",
    "tsc_security_in_scope": <true|false|null>,
    "tsc_availability_in_scope": <true|false|null>,
    "tsc_confidentiality_in_scope": <true|false|null>,
    "tsc_processing_integrity_in_scope": <true|false|null>,
    "tsc_privacy_in_scope": <true|false|null>,
    "tsc_privacy_exceptions_found": <true|false|null>,
    "scope_description_present": <true|false|null>,
    "scope_products_listed": ["<product>"] or null,
    "scope_explicit_exclusions": ["<exclusion>"] or null,
    "scope_narrowing_concern": <true|false|null>,
    "carve_out_method_used": <true|false|null>,
    "sub_service_organisations_listed": ["<org>"] or null,
    "cuecs_documented": <true|false|null>,
    "cuec_list": ["<cuec>"] or null,
    "csocs_documented": <true|false|null>,
    "exceptions_found": <true|false|null>,
    "exception_count": <integer or null>,
    "exception_details": [
      {{
        "control_id": "<id>",
        "description": "<desc>",
        "severity": "<minor|moderate|severe>",
        "management_response_present": <true|false>,
        "management_response_specific": <true|false>,
        "remediation_timeframe": "<timeframe or null>",
        "remediation_complete_at_issuance": <true|false|null>
      }}
    ] or null,
    "all_exceptions_have_responses": <true|false|null>,
    "management_responses_are_specific": <true|false|null>,
    "exceptions_in_privacy_controls": <true|false|null>,
    "exceptions_in_access_controls": <true|false|null>,
    "exceptions_in_change_management": <true|false|null>,
    "exceptions_in_incident_response": <true|false|null>,
    "testing_includes_inspection": <true|false|null>,
    "testing_includes_observation": <true|false|null>,
    "testing_includes_reperformance": <true|false|null>,
    "testing_primarily_inquiry": <true|false|null>,
    "sub_processor_controls_tested": <true|false|null>,
    "breach_notification_controls_tested": <true|false|null>,
    "data_deletion_controls_tested": <true|false|null>,
    "encryption_controls_tested": <true|false|null>,
    "access_review_controls_tested": <true|false|null>,
    "vendor_risk_controls_tested": <true|false|null>,
    "uses_2022_tsc_framework": <true|false|null>,
    "uses_outdated_framework": <true|false|null>
  }},
  "iso_27001_signals": {{
    "iso_27001_present": <true|false|null>,
    "iso_27001_version": "<2022|2013|older|null>",
    "iso_27001_2013_post_transition": <true|false|null>,
    "iso_27001_issue_date": "<YYYY-MM-DD or null>",
    "iso_27001_expiry_date": "<YYYY-MM-DD or null>",
    "iso_27001_surveillance_audit_referenced": <true|false|null>,
    "iso_27001_surveillance_audit_date": "<YYYY-MM-DD or null>",
    "iso_27001_audit_type": "<initial|surveillance|recertification|null>",
    "iso_27001_certification_body_name": "<exact name or null>",
    "iso_27001_certification_body_accredited": <true|false|null>,
    "iso_27001_accreditation_number_stated": <true|false|null>,
    "iso_27001_iaf_recognition": <true|false|null>,
    "iso_27001_scope_statement": "<verbatim scope or null>",
    "iso_27001_scope_includes_primary_service": <true|false|null>,
    "iso_27001_scope_explicit_exclusions": ["<exclusion>"] or null,
    "iso_27001_scope_geographic_coverage": ["<region>"] or null,
    "iso_27001_scope_business_unit_only": <true|false|null>,
    "iso_27001_scope_narrowing_concern": <true|false|null>,
    "iso_27001_soa_provided": <true|false|null>,
    "iso_27001_controls_excluded": ["<control>"] or null,
    "iso_27001_excluded_controls_count": <integer or null>,
    "iso_27001_excluded_controls_justified": <true|false|null>,
    "iso_27001_audit_findings_stated": <true|false|null>,
    "iso_27001_major_nonconformities": <integer or null>,
    "iso_27001_minor_nonconformities": <integer or null>,
    "iso_27001_observations": <integer or null>,
    "iso_27001_data_protection_controls_implemented": <true|false|null>,
    "iso_27001_supplier_controls_implemented": <true|false|null>,
    "iso_27001_incident_management_controls_implemented": <true|false|null>,
    "iso_27001_compliance_controls_implemented": <true|false|null>
  }},
  "iso_27701_signals": {{
    "iso_27701_present": <true|false|null>,
    "iso_27701_extends_27001": <true|false|null>,
    "iso_27701_issue_date": "<YYYY-MM-DD or null>",
    "iso_27701_expiry_date": "<YYYY-MM-DD or null>",
    "iso_27701_certification_body_name": "<exact name or null>",
    "iso_27701_certification_body_accredited": <true|false|null>,
    "iso_27701_scope_statement": "<verbatim scope or null>",
    "iso_27701_role_pii_controller": <true|false|null>,
    "iso_27701_role_pii_processor": <true|false|null>,
    "iso_27701_gdpr_mapped": <true|false|null>,
    "iso_27701_ccpa_mapped": <true|false|null>
  }},
  "iso_42001_signals": {{
    "iso_42001_present": <true|false|null>,
    "iso_42001_issue_date": "<YYYY-MM-DD or null>",
    "iso_42001_expiry_date": "<YYYY-MM-DD or null>",
    "iso_42001_certification_body_name": "<exact name or null>",
    "iso_42001_certification_body_accredited": <true|false|null>,
    "iso_42001_scope_statement": "<verbatim scope or null>",
    "iso_42001_aims_implemented": <true|false|null>,
    "iso_42001_ai_risk_assessment_documented": <true|false|null>,
    "iso_42001_ai_lifecycle_controls": <true|false|null>,
    "iso_42001_data_governance_for_ai": <true|false|null>,
    "iso_42001_third_party_ai_governance": <true|false|null>
  }},
  "cross_certificate_signals": {{
    "iso_certificates_organisation_consistent": <true|false|null>,
    "iso_certificates_scope_aligned": <true|false|null>,
    "iso_certificate_expired": <true|false|null>,
    "iso_certificate_no_surveillance_audit": <true|false|null>,
    "iso_certification_body_unaccredited": <true|false|null>,
    "iso_27701_without_27001": <true|false|null>,
    "iso_scope_excludes_customer_service": <true|false|null>,
    "iso_certificate_image_only": <true|false|null>
  }},
  "dpa_conflicts": [
    {{
      "claim": "<what DPA claims>",
      "evidence": "<what audit doc shows>",
      "severity": "<high|medium|low>"
    }}
  ],
  "top_findings": [
    "<finding — specific, cite document section>"
  ],
  "red_flags": ["<concern from audit evidence>"],
  "positive_signals": ["<strength evidenced by audit>"],
  "questions_for_vendor": [
    "<targeted question>"
  ]
}}

For SOC 2 auditor firm recognition, compare the \
extracted firm name against this list of recognised \
firms. Mark auditor_firm_recognised = TRUE only if \
the firm name matches (case-insensitive, ignoring \
suffixes like LLP/LLC/Inc):

{firms_list}

For ISO certification body accreditation, compare the \
extracted body name against this list. Mark \
iso_*_certification_body_accredited = TRUE only if \
the body matches:

{bodies_list}

Documents:
{docs_text}"""

    def _calc_soc2_currency(
        self,
        period_end: str | None,
        bridge_letter: bool | None,
    ) -> str:
        """Calculate SOC 2 currency status per RUBRIC_SOC2.md."""
        if not period_end:
            return "unknown"
        try:
            end = datetime.strptime(
                period_end, "%Y-%m-%d"
            ).date()
            today = date.today()
            months_old = (
                (today.year - end.year) * 12
                + today.month - end.month
            )
            if months_old <= 12:
                return "current"
            elif months_old <= 18:
                return (
                    "stale_bridged" if bridge_letter
                    else "stale"
                )
            else:
                return "outdated"
        except ValueError:
            return "unknown"

    def _calc_iso_currency(
        self,
        iso_signals: dict,
        prefix: str,
    ) -> str:
        """Calculate ISO certificate currency per RUBRIC_ISO.md."""
        issue_date = iso_signals.get(f"{prefix}_issue_date")
        expiry_date = iso_signals.get(f"{prefix}_expiry_date")
        surveillance = iso_signals.get(
            f"{prefix}_surveillance_audit_referenced"
        )

        if not issue_date and not expiry_date:
            return "unknown"

        today = date.today()

        # Check expiry first
        if expiry_date:
            try:
                exp = datetime.strptime(
                    expiry_date, "%Y-%m-%d"
                ).date()
                if exp < today:
                    return "expired"
                days_to_expiry = (exp - today).days
                if days_to_expiry <= 180:
                    return "expiring_soon"
            except ValueError:
                pass

        # Check issue date age
        if issue_date:
            try:
                issued = datetime.strptime(
                    issue_date, "%Y-%m-%d"
                ).date()
                months_old = (
                    (today.year - issued.year) * 12
                    + today.month - issued.month
                )
                if months_old <= 18:
                    return "current_recent"
                elif surveillance is True:
                    return "current_with_surveillance"
                else:
                    return "current_no_surveillance"
            except ValueError:
                pass

        return "unknown"

    def _calculate_derived(self, raw: dict) -> dict:
        """
        Calculate derived signals per rubric documents.
        The LLM extracts raw fields; these are computed
        deterministically.
        """
        derived = {}

        # SOC 2 currency_status
        soc2 = raw.get("soc2_signals", {})
        derived["currency_status"] = self._calc_soc2_currency(
            soc2.get("audit_period_end"),
            soc2.get("bridge_letter_present"),
        )

        # ISO currency for each cert type
        for prefix in [
            "iso_27001", "iso_27701", "iso_42001"
        ]:
            iso_sigs = raw.get(f"{prefix}_signals", {})
            derived[f"{prefix}_currency_status"] = (
                self._calc_iso_currency(iso_sigs, prefix)
            )

        return derived

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

        # Calculate derived values
        derived = self._calculate_derived(result)

        # Build signals — flatten all sections + derived
        signals = self._build_signals(result, derived)

        # Framework evidence from audit
        framework_evidence = self._build_framework_evidence(
            result
        )

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

    def _build_signals(
        self,
        result: dict,
        derived: dict,
    ) -> dict:
        """
        Flatten all extracted signals into a single dict
        using exact names from RUBRIC_SOC2.md and
        RUBRIC_ISO.md.

        Also generates legacy d2_/d5_/d7_/d8_ prefixed
        signals for backward compatibility with the
        level-walk scoring.
        """
        signals = {}

        # Flatten SOC 2 signals
        soc2 = result.get("soc2_signals", {})
        for k, v in soc2.items():
            if not k.endswith("_source"):
                signals[k] = v

        # Flatten ISO signals (all three types)
        for section in [
            "iso_27001_signals",
            "iso_27701_signals",
            "iso_42001_signals",
        ]:
            iso = result.get(section, {})
            for k, v in iso.items():
                if not k.endswith("_source"):
                    signals[k] = v

        # Flatten cross-certificate signals
        cross = result.get("cross_certificate_signals", {})
        for k, v in cross.items():
            signals[k] = v

        # Add derived values
        signals.update(derived)

        # DPA conflicts flag
        if result.get("dpa_conflicts"):
            signals["d8_dpa_audit_conflict"] = True

        # Legacy d2_/d5_/d7_/d8_ signals for level-walk
        # D2 — Sub-processor management
        if soc2.get("sub_processor_controls_tested") is True:
            signals["d2_sub_processor_controls_audited"] = True
        if (soc2.get("tsc_privacy_in_scope") is True
                and soc2.get("tsc_privacy_exceptions_found") is not True):
            signals["d2_third_party_audit_clean"] = True

        # D5 — Breach notification
        if soc2.get("breach_notification_controls_tested") is True:
            signals["d5_breach_procedures_audited"] = True

        # D7 — Retention and deletion
        if soc2.get("data_deletion_controls_tested") is True:
            signals["d7_deletion_controls_audited"] = True

        # D8 — DPA completeness / independent verification
        soc2_present = (
            soc2.get("soc2_type2_present") is True
            or soc2.get("soc2_type1_present") is True
        )
        currency = derived.get("currency_status", "unknown")

        if soc2_present and currency.startswith("current"):
            if soc2.get("exceptions_found") is not True:
                signals["d8_independent_audit_clean"] = True
            else:
                signals["d8_audit_exceptions_found"] = True
        elif soc2_present and currency in ("stale", "outdated"):
            signals["d8_audit_stale"] = True

        iso_27001 = result.get("iso_27001_signals", {})
        iso_27001_currency = derived.get(
            "iso_27001_currency_status", "unknown"
        )
        if (iso_27001.get("iso_27001_present") is True
                and iso_27001_currency.startswith("current")):
            signals["d8_iso27001_current"] = True

        iso_27701 = result.get("iso_27701_signals", {})
        iso_27701_currency = derived.get(
            "iso_27701_currency_status", "unknown"
        )
        if (iso_27701.get("iso_27701_present") is True
                and iso_27701_currency.startswith("current")):
            signals["d8_iso27701_current"] = True

        return signals

    def _build_framework_evidence(
        self,
        result: dict,
    ) -> dict:
        """
        Build framework evidence dict from audit results.
        """
        evidence = {}
        soc2 = result.get("soc2_signals", {})
        iso_27001 = result.get("iso_27001_signals", {})
        iso_27701 = result.get("iso_27701_signals", {})
        iso_42001 = result.get("iso_42001_signals", {})

        if soc2.get("soc2_type2_present") is True:
            if soc2.get("tsc_privacy_in_scope") is True:
                evidence["soc2_type2_privacy_tsc"] = True
            else:
                evidence["soc2_type2_security_only"] = True

        if (iso_27001.get("iso_27001_present") is True
                and iso_27701.get("iso_27701_present") is not True):
            evidence["iso_27001_only"] = True

        if iso_27701.get("iso_27701_present") is True:
            evidence["iso_27701_certified"] = True

        if iso_42001.get("iso_42001_present") is True:
            evidence["iso_42001_certified"] = True

        return evidence
