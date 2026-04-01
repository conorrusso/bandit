"""
Bandit Document Classifier
============================
Two-pass detection: filename heuristics first,
AI content classification fallback.

Pass 1 — filename patterns (confidence 0.85)
Pass 2 — content keyword matching (confidence 0.4–0.8)
Pass 3 — AI classification (confidence 0.75, only when LLM provided)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DocumentType(str, Enum):
    # Privacy & Data Protection
    PRIVACY_POLICY           = "privacy_policy"
    COOKIE_POLICY            = "cookie_policy"
    CCPA_NOTICE              = "ccpa_notice"
    CHILDRENS_PRIVACY        = "childrens_privacy"

    # Contracts
    DPA                      = "dpa"
    MSA                      = "msa"
    SAAS_AGREEMENT           = "saas_agreement"
    BAA                      = "baa"
    NDA                      = "nda"
    DATA_SHARING_AGREEMENT   = "data_sharing_agreement"
    JOINT_CONTROLLER         = "joint_controller"
    SCCS                     = "sccs"
    ORDER_FORM               = "order_form"

    # Audit & Certification
    SOC2_TYPE2               = "soc2_type2"
    SOC2_TYPE1               = "soc2_type1"
    SOC1_TYPE2               = "soc1_type2"
    ISO27001                 = "iso27001"
    ISO27701                 = "iso27701"
    ISO42001                 = "iso42001"
    HITRUST                  = "hitrust"
    PCI_AOC                  = "pci_aoc"
    PCI_ROC                  = "pci_roc"
    FEDRAMP_ATO              = "fedramp_ato"
    NIST_800_171             = "nist_800_171"
    CMMC                     = "cmmc"
    NYDFS_CERT               = "nydfs_cert"
    DORA_COMPLIANCE          = "dora_compliance"

    # AI-Specific
    AI_POLICY                = "ai_policy"
    MODEL_CARD               = "model_card"
    AI_SYSTEM_CARD           = "ai_system_card"
    EU_AI_ACT_CONFORMITY     = "eu_ai_act_conformity"
    ALGORITHM_IMPACT         = "algorithm_impact"

    # Transfer & International
    TIA                      = "tia"
    ROPA_ENTRY               = "ropa_entry"

    # Security
    PENTEST_SUMMARY          = "pentest_summary"
    VULNERABILITY_DISCLOSURE = "vulnerability_disclosure"
    INCIDENT_RESPONSE        = "incident_response"
    SUB_PROCESSOR_LIST       = "sub_processor_list"
    SECURITY_POLICY          = "security_policy"
    DATA_RETENTION_SCHEDULE  = "data_retention_schedule"

    # Healthcare Specific
    HIPAA_SECURITY_ADDENDUM  = "hipaa_security_addendum"

    # Financial Specific
    GLBA_PRIVACY_NOTICE      = "glba_privacy_notice"
    PCI_SAQ                  = "pci_saq"

    UNKNOWN                  = "unknown"


@dataclass
class ClassificationResult:
    doc_type: DocumentType
    confidence: float    # 0.0–1.0
    method: str          # filename | content_keywords | content_ai | unknown
    reasoning: str


FILENAME_PATTERNS: dict[DocumentType, list[str]] = {
    DocumentType.DPA: [
        "dpa", "data-processing", "data_processing",
        "data-processor", "processor-agreement",
        "processing-agreement", "gdpr-agreement",
        "data-processing-addendum"
    ],
    DocumentType.MSA: [
        "msa", "master-services", "master_services",
        "master-agreement", "service-agreement",
        "master-subscription", "framework-agreement",
        "service-level-agreement", "sla"
    ],
    DocumentType.SAAS_AGREEMENT: [
        "saas-license", "saas_license", "saas-agreement",
        "license-agreement", "subscription-agreement",
        "software-license", "terms-of-service",
        "master-subscription-agreement"
    ],
    DocumentType.BAA: [
        "baa", "business-associate", "hipaa-agreement",
        "hipaa-addendum", "business_associate"
    ],
    DocumentType.SOC2_TYPE2: [
        "soc2", "soc-2", "soc_2", "type-ii", "type2",
        "trust-services", "soc2-type2", "soc-2-type-ii"
    ],
    DocumentType.SOC2_TYPE1: [
        "soc2-type1", "soc-2-type-i", "type-i-report"
    ],
    DocumentType.SOC1_TYPE2: [
        "soc1", "soc-1", "soc_1", "ssae18",
        "financial-controls"
    ],
    DocumentType.ISO27001: [
        "iso27001", "iso-27001", "iso_27001", "27001"
    ],
    DocumentType.ISO27701: [
        "iso27701", "iso-27701", "27701"
    ],
    DocumentType.ISO42001: [
        "iso42001", "iso-42001", "42001",
        "ai-management", "ai-management-system"
    ],
    DocumentType.HITRUST: [
        "hitrust", "hit-trust", "csf-report"
    ],
    DocumentType.PCI_AOC: [
        "pci", "aoc", "attestation-of-compliance",
        "pci-aoc", "pci_aoc"
    ],
    DocumentType.PCI_ROC: [
        "roc", "report-on-compliance", "pci-roc"
    ],
    DocumentType.FEDRAMP_ATO: [
        "fedramp", "ato", "authority-to-operate"
    ],
    DocumentType.NIST_800_171: [
        "nist-800", "800-171", "cui-assessment"
    ],
    DocumentType.AI_POLICY: [
        "ai-policy", "ai_policy", "responsible-ai",
        "ai-principles", "ai-usage", "ai-guidelines",
        "artificial-intelligence-policy", "genai-policy",
        "ai-faq", "ai_faq", "legal-ai", "ai-legal",
        "responsible-ai-faq", "generative-ai-faq"
    ],
    DocumentType.MODEL_CARD: [
        "model-card", "model_card", "modelcard",
        "system-card", "ai-system-card"
    ],
    DocumentType.TIA: [
        "tia", "transfer-impact", "transfer_impact",
        "chapter-v", "schrems", "international-transfer"
    ],
    DocumentType.SUB_PROCESSOR_LIST: [
        "sub-processor", "subprocessor", "sub_processor",
        "third-party-list", "subprocessors",
        "infrastructure-subprocessors"
    ],
    DocumentType.PRIVACY_POLICY: [
        "privacy-policy", "privacy_policy",
        "privacypolicy", "privacy-notice",
        "privacy-statement", "data-privacy"
    ],
    DocumentType.SCCS: [
        "scc", "sccs", "standard-contractual",
        "model-clauses", "eu-model-clauses"
    ],
    DocumentType.HIPAA_SECURITY_ADDENDUM: [
        "hipaa-security", "security-addendum",
        "hipaa-addendum", "phi-addendum"
    ],
    DocumentType.PENTEST_SUMMARY: [
        "pentest", "penetration-test", "pen-test",
        "security-assessment", "vulnerability-assessment"
    ],
    DocumentType.DATA_RETENTION_SCHEDULE: [
        "retention-schedule", "data-retention",
        "retention-policy"
    ],
    DocumentType.INCIDENT_RESPONSE: [
        "incident-response", "ir-policy",
        "security-incident"
    ],
    DocumentType.CMMC: [
        "cmmc", "cybersecurity-maturity"
    ],
    DocumentType.NYDFS_CERT: [
        "nydfs", "part-500", "23-nycrr"
    ],
    DocumentType.DORA_COMPLIANCE: [
        "dora", "digital-operational-resilience"
    ],
}

# Content keywords for keyword-based classification
CONTENT_PATTERNS: dict[DocumentType, list[str]] = {
    DocumentType.DPA: [
        "data processing agreement", "article 28",
        "processor shall", "controller and processor",
        "data processing addendum", "sub-processor",
        "processing activities"
    ],
    DocumentType.BAA: [
        "business associate agreement", "protected health",
        "hipaa", "phi", "covered entity",
        "business associate", "164.504"
    ],
    DocumentType.SOC2_TYPE2: [
        "trust service criteria", "type ii",
        "soc 2", "aicpa", "complementary user entity",
        "carve-out", "inclusive method"
    ],
    DocumentType.SOC1_TYPE2: [
        "soc 1", "ssae 18", "financial reporting",
        "internal controls over financial reporting"
    ],
    DocumentType.ISO27001: [
        "iso/iec 27001", "information security",
        "isms", "annex a", "certification body"
    ],
    DocumentType.ISO42001: [
        "iso/iec 42001", "ai management system",
        "artificial intelligence management"
    ],
    DocumentType.SAAS_AGREEMENT: [
        "subscription term", "license grant",
        "permitted users", "software as a service",
        "acceptable use", "service level",
        "saas", "subscription fee"
    ],
    DocumentType.AI_POLICY: [
        "responsible ai", "ai principles",
        "generative ai", "large language model",
        "ai governance", "ai usage policy",
        "training data", "model training",
        "ai faq", "legal ai"
    ],
    DocumentType.TIA: [
        "transfer impact assessment",
        "schrems", "chapter v", "adequacy decision",
        "standard contractual clauses",
        "supplementary measures"
    ],
    DocumentType.PCI_AOC: [
        "attestation of compliance", "pci dss",
        "qualified security assessor", "qsa",
        "cardholder data environment"
    ],
    DocumentType.HITRUST: [
        "hitrust", "csf", "health information trust",
        "implemented", "managed", "defined"
    ],
}


class DocumentClassifier:

    def classify(
        self,
        file_path: str,
        extracted_text: str = "",
        llm_provider=None,
    ) -> ClassificationResult:

        from pathlib import Path
        filename = Path(file_path).stem.lower()
        filename = filename.replace("_", "-").replace(" ", "-")

        # Pass 1 — filename patterns
        result = self._classify_by_filename(filename)
        if result.confidence >= 0.7:
            return result

        # Pass 2 — content keywords (free, no AI)
        if extracted_text:
            result2 = self._classify_by_content_keywords(extracted_text)
            if result2.confidence >= 0.7:
                return result2

        # Pass 3 — AI content classification
        if llm_provider and extracted_text:
            result3 = self._classify_by_ai(extracted_text[:2000], llm_provider)
            if result3.confidence >= 0.6:
                return result3

        # Return best result so far even if low confidence
        if result.confidence > 0:
            return result

        return ClassificationResult(
            doc_type=DocumentType.UNKNOWN,
            confidence=0.0,
            method="unknown",
            reasoning="Could not classify document type"
        )

    def _classify_by_filename(self, filename: str) -> ClassificationResult:
        for doc_type, patterns in FILENAME_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename:
                    return ClassificationResult(
                        doc_type=doc_type,
                        confidence=0.85,
                        method="filename",
                        reasoning=f"Filename contains '{pattern}'"
                    )
        return ClassificationResult(
            doc_type=DocumentType.UNKNOWN,
            confidence=0.0,
            method="filename",
            reasoning="No filename pattern matched"
        )

    def _classify_by_content_keywords(self, text: str) -> ClassificationResult:
        text_lower = text[:3000].lower()
        best_type = DocumentType.UNKNOWN
        best_score = 0.0
        best_reason = ""

        for doc_type, keywords in CONTENT_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            score = matches / len(keywords)
            if score > best_score:
                best_score = score
                best_type = doc_type
                best_reason = (
                    f"{matches}/{len(keywords)} content keywords matched"
                )

        if best_score >= 0.3:
            return ClassificationResult(
                doc_type=best_type,
                confidence=min(0.8, best_score + 0.4),
                method="content_keywords",
                reasoning=best_reason
            )

        return ClassificationResult(
            doc_type=DocumentType.UNKNOWN,
            confidence=0.0,
            method="content_keywords",
            reasoning="No content patterns matched"
        )

    def _classify_by_ai(self, text_sample: str, llm_provider) -> ClassificationResult:
        valid_types = " | ".join(
            t.value for t in DocumentType if t != DocumentType.UNKNOWN
        )
        prompt = (
            f"What type of compliance document is this? "
            f"Reply with ONLY one of these exact values:\n"
            f"{valid_types}\n\n"
            f"Document sample:\n{text_sample}"
        )
        try:
            response = llm_provider.complete_text(prompt, max_tokens=20)
            type_str = response.strip().lower()
            for doc_type in DocumentType:
                if doc_type.value == type_str:
                    return ClassificationResult(
                        doc_type=doc_type,
                        confidence=0.75,
                        method="content_ai",
                        reasoning=f"AI classified as {type_str}"
                    )
        except Exception:
            pass

        return ClassificationResult(
            doc_type=DocumentType.UNKNOWN,
            confidence=0.0,
            method="content_ai",
            reasoning="AI classification failed"
        )
