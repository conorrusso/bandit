"""
AI Bandit — specialist D6 agent.

Performs deep analysis of AI/ML usage disclosures, model cards,
AI policies, and DPA AI clauses. Produces high-confidence D6
signals and findings for the GRC and Legal reports.

Signal names match RUBRIC_AI_POLICY.md exactly.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Callable

from core.agents.agent_base import (
    BaseAgent,
    AgentDocument,
    AgentResult,
)

logger = logging.getLogger("bandit")

# Document types that trigger AI Bandit
AI_DOC_TYPES = {
    "AI_POLICY",
    "MODEL_CARD",
    "AI_SYSTEM_CARD",
    "EU_AI_ACT_CONFORMITY",
    "ALGORITHM_IMPACT",
    "TERMS_OF_SERVICE",   # often contains AI clauses
    "DPA",                # DPA AI/ML sections
    "PRIVACY_POLICY",     # often contains AI training
}


def _load_rubric() -> str:
    """Load AI policy rubric content."""
    rubric_path = (
        Path(__file__).parent.parent / "scoring" / "RUBRIC_AI_POLICY.md"
    )
    if rubric_path.exists():
        return rubric_path.read_text()
    return ""


SYSTEM_PROMPT = """\
You are an AI governance analyst specialising in vendor AI risk \
assessment for enterprise GRC teams. You evaluate AI policies, \
model cards, and contract AI clauses against GDPR Art. 22, \
EU AI Act, FTC enforcement precedents, and enterprise data \
protection requirements.

Critical architectural rules:
- You extract signals only. You NEVER recommend scores.
- Training and inference are always distinguished.
- Opt-out accessibility is graded (self_service > form_based > \
support_request > contract_negotiation > none).
- EU AI Act tier is vendor-claimed — you flag implausibility \
but do not classify independently.
- Absence of AI disclosure is itself a signal.

Return ONLY valid JSON — no markdown, no explanation, no code \
fences. Be precise and evidence-based."""

# All signal names from RUBRIC_AI_POLICY.md sections A–J.
# These are the exact names the rubric engine expects.
_ALL_AI_SIGNALS = [
    # Section A — AI presence and scope
    "is_ai_vendor",
    "ai_in_customer_facing_service",
    "ai_in_backend_processing",
    "generative_ai_present",
    "third_party_ai_used",
    "third_party_ai_providers_listed",
    # Section B — Training use of customer data
    "trains_on_customer_data",
    "fine_tunes_on_customer_data",
    "uses_customer_data_for_inference",
    "inference_data_retained",
    "uses_customer_data_for_model_improvement",
    "customer_data_segregated_from_training",
    # Section C — Opt-out mechanics
    "opt_out_available",
    "opt_out_accessibility",
    "opt_out_prominent",
    "opt_out_retroactive",
    "opt_in_required",
    "opt_out_granularity",
    # Section D — Legal basis and EU AI Act
    "legal_basis_stated",
    "legal_basis_description",
    "legitimate_interests_balancing_performed",
    "special_category_data_addressed",
    "eu_ai_act_addressed",
    "eu_ai_act_claimed_tier",
    "eu_ai_act_tier_plausible",
    # Section E — Data governance and retention
    "training_data_retention_stated",
    "training_data_retention_period",
    "inference_logs_retention_stated",
    "data_used_in_training_segregated_from_weights",
    "model_deletion_on_contract_termination",
    "algorithmic_disgorgement_addressed",
    # Section F — Fairness, bias, and oversight
    "bias_mitigation_documented",
    "fairness_evaluation_documented",
    "human_in_the_loop_described",
    "ai_decisions_contestable",
    "automated_decision_making_disclosed",
    # Section G — Transparency documentation
    "model_card_available",
    "training_data_sources_disclosed",
    "training_data_provenance_documented",
    "model_updates_disclosed",
    "ai_transparency_report_available",
    # Section H — Contractual AI commitments (DPA)
    "dpa_has_ai_clause",
    "dpa_prohibits_training_on_customer_data",
    "dpa_requires_consent_for_ai_processing",
    "dpa_addresses_ai_subprocessors",
    "dpa_has_ai_audit_rights",
    # Section I — Compliance certifications
    "iso_42001_certified",
    "nist_ai_rmf_referenced",
    "iso_23894_referenced",
    # Section J — AI contradictions and red flags
    "training_claim_contradicts_inference_retention",
    "opt_out_denied_for_ai_features",
    "ai_use_without_disclosure",
    "customer_data_used_for_foundation_model_training",
    # Inferred signal flag
    "is_ai_vendor_inferred",
]

# Value-type signals (not boolean)
_VALUE_TYPE_SIGNALS = {
    "third_party_ai_providers_listed",   # list of strings
    "opt_out_accessibility",             # enum string
    "opt_out_granularity",               # enum string
    "legal_basis_description",           # string
    "eu_ai_act_claimed_tier",            # enum string
    "training_data_retention_period",    # string
}

# Boolean signals (true/false/null)
_BOOLEAN_SIGNALS = [
    s for s in _ALL_AI_SIGNALS if s not in _VALUE_TYPE_SIGNALS
]


class AIBandit(BaseAgent):
    """
    AI Bandit — specialist D6 agent.

    Performs deep analysis of AI/ML usage disclosures,
    model cards, AI policies, and DPA AI clauses.
    Produces high-confidence D6 signals and findings
    for the GRC and Legal reports.
    """

    name = "AI Bandit"

    def __init__(
        self,
        provider,
        on_progress: Optional[Callable] = None,
        max_tokens: int = 6000,
    ):
        super().__init__(provider, on_progress, max_tokens)

    def _should_trigger(
        self,
        documents: list[AgentDocument],
        intake_context: str | None,
    ) -> bool:
        """
        Trigger if any AI-related document is present
        OR if intake marks vendor as AI vendor.
        """
        for doc in documents:
            if doc.doc_type in AI_DOC_TYPES:
                return True
        if intake_context and (
            "ai_in_service: yes" in intake_context.lower()
            or "ai vendor" in intake_context.lower()
            or "uses ai" in intake_context.lower()
        ):
            return True
        return False

    def _select_documents(
        self,
        documents: list[AgentDocument],
    ) -> list[AgentDocument]:
        """
        Prioritise AI-specific documents.
        Always include DPA and Privacy Policy if present.
        """
        priority = []
        supporting = []

        for doc in documents:
            if doc.doc_type in {
                "AI_POLICY", "MODEL_CARD",
                "AI_SYSTEM_CARD", "EU_AI_ACT_CONFORMITY",
                "ALGORITHM_IMPACT",
            }:
                priority.append(doc)
            elif doc.doc_type in {
                "DPA", "PRIVACY_POLICY",
                "TERMS_OF_SERVICE",
            }:
                supporting.append(doc)

        # Priority docs first, then supporting
        # Cap at 4 documents to control prompt size
        return (priority + supporting)[:4]

    def _build_prompt(
        self,
        vendor_name: str,
        documents: list[AgentDocument],
        intake_context: str | None,
    ) -> str:
        """Build the AI analysis prompt from RUBRIC_AI_POLICY.md."""

        doc_sections = []
        for doc in documents:
            text = self._truncate_text(doc.text, 25000)
            doc_sections.append(
                f"=== {doc.doc_type}: {doc.filename} ===\n"
                f"{text}"
            )

        docs_text = "\n\n".join(doc_sections)
        intake_section = (
            f"\nIntake context:\n{intake_context}\n"
            if intake_context else ""
        )

        # Build JSON schema from signal list
        schema_lines = []
        for sig in _BOOLEAN_SIGNALS:
            schema_lines.append(
                f'  "{sig}": <true | false | null>,'
            )
            schema_lines.append(
                f'  "{sig}_source": "<document section or null>",'
            )

        # Value-type signals
        schema_lines.append(
            '  "third_party_ai_providers_listed": '
            '["<provider name>"] or null,'
        )
        schema_lines.append(
            '  "third_party_ai_providers_listed_source": '
            '"<document section or null>",'
        )
        schema_lines.append(
            '  "opt_out_accessibility": '
            '"<self_service|form_based|support_request|'
            'contract_negotiation|none|null>",'
        )
        schema_lines.append(
            '  "opt_out_accessibility_source": '
            '"<document section or null>",'
        )
        schema_lines.append(
            '  "opt_out_granularity": '
            '"<account_level|data_type_level|'
            'field_level|none|null>",'
        )
        schema_lines.append(
            '  "legal_basis_description": "<string or null>",'
        )
        schema_lines.append(
            '  "eu_ai_act_claimed_tier": '
            '"<minimal|limited|high|unacceptable|'
            'not_stated|null>",'
        )
        schema_lines.append(
            '  "training_data_retention_period": '
            '"<string or null>",'
        )

        # Non-signal output fields
        schema_lines.append(
            '  "red_flags": ["<specific concern from text>"],'
        )
        schema_lines.append(
            '  "top_findings": ['
        )
        schema_lines.append(
            '    "<finding — specific, cite document section>"'
        )
        schema_lines.append(
            '  ],')
        schema_lines.append(
            '  "recommended_dpa_clause": '
            '"<specific clause language or null>",'
        )
        schema_lines.append(
            '  "questions_for_vendor": ['
        )
        schema_lines.append(
            '    "<targeted question>"'
        )
        schema_lines.append(
            '  ]')

        schema = "\n".join(schema_lines)

        return f"""\
Analyse the following documents for {vendor_name} \
to extract AI-related signals.
{intake_section}
For each signal below, answer ONLY true, false, or null \
based on what is explicitly stated in the documents.

Mark as TRUE only if the document explicitly states what \
the criteria require.
Mark as FALSE only if the document explicitly contradicts \
the criteria.
Mark as NULL if the topic is not addressed at all in the \
documents.

For each TRUE signal, provide a source reference \
(document name and section) in the corresponding \
_source field.

IMPORTANT distinctions:
- "Training" means customer data influences model weights.
- "Fine-tuning" means customer data adjusts a base model.
- "Inference" means data is processed to generate output \
but not used to update the model.
- "Model improvement" means aggregated/anonymised data \
informs future development.
These four are distinct — do not conflate them.

Return ONLY this JSON object — no markdown, no \
explanation, no code fences:

{{
{schema}
}}

Signal criteria:

Section A — AI presence and scope:
- is_ai_vendor: TRUE if vendor uses AI/ML/GenAI in \
their product or service.
- ai_in_customer_facing_service: TRUE if AI features \
customers directly interact with.
- ai_in_backend_processing: TRUE if AI used for backend \
processing affecting customer data.
- generative_ai_present: TRUE if generative AI, LLMs, \
text/image generation specifically mentioned.
- third_party_ai_used: TRUE if vendor uses third-party \
AI services (OpenAI, Anthropic, etc.).

Section B — Training use of customer data:
- trains_on_customer_data: TRUE if customer data used \
to train models (influences weights). FALSE if \
explicitly stated not used for training.
- fine_tunes_on_customer_data: TRUE if customer data \
used for fine-tuning.
- uses_customer_data_for_inference: TRUE if customer \
data sent to models for inference.
- inference_data_retained: TRUE if inference data is \
retained for any purpose.
- uses_customer_data_for_model_improvement: TRUE if \
customer data used for model/service improvement.
- customer_data_segregated_from_training: TRUE if \
customer data explicitly kept separate from training \
data pools.

Section C — Opt-out mechanics:
- opt_out_available: TRUE if any method exists to opt \
out of AI data use.
- opt_out_prominent: TRUE if opt-out described \
prominently (not buried in footnotes).
- opt_out_retroactive: TRUE if opt-out applies \
retroactively to data already used. FALSE if \
explicitly forward-only.
- opt_in_required: TRUE if customer must affirmatively \
opt in for AI use of their data.

Section D — Legal basis and EU AI Act:
- legal_basis_stated: TRUE if legal basis for AI \
processing stated (consent, legitimate interest, etc.).
- legitimate_interests_balancing_performed: TRUE if \
LIA or balancing test referenced.
- special_category_data_addressed: TRUE if GDPR Art. 9 \
special category data addressed for AI processing.
- eu_ai_act_addressed: TRUE if EU AI Act explicitly \
referenced.
- eu_ai_act_tier_plausible: TRUE if claimed tier \
consistent with described use. FALSE if implausible. \
NULL if insufficient info. Provide reasoning.

Section E — Data governance and retention:
- training_data_retention_stated: TRUE if retention \
period specified for AI training data.
- inference_logs_retention_stated: TRUE if inference \
log retention specified.
- data_used_in_training_segregated_from_weights: TRUE \
if document addresses removing data from model weights.
- model_deletion_on_contract_termination: TRUE if \
commitment to delete fine-tuned models on termination.
- algorithmic_disgorgement_addressed: TRUE if FTC-style \
model destruction addressed.

Section F — Fairness, bias, and oversight:
- bias_mitigation_documented: TRUE if specific bias \
testing or mitigation procedures described.
- fairness_evaluation_documented: TRUE if fairness \
metrics or evaluation procedures described.
- human_in_the_loop_described: TRUE if human oversight \
for AI decisions described.
- ai_decisions_contestable: TRUE if mechanism to \
contest AI decisions described (GDPR Art. 22).
- automated_decision_making_disclosed: TRUE if specific \
automated decisions identified vs human involvement.

Section G — Transparency:
- model_card_available: TRUE if model card referenced \
or included.
- training_data_sources_disclosed: TRUE if training \
data origins disclosed.
- training_data_provenance_documented: TRUE if \
provenance chain documented including consent basis.
- model_updates_disclosed: TRUE if material model \
updates will be disclosed to customers.
- ai_transparency_report_available: TRUE if AI \
transparency or accountability report referenced.

Section H — DPA AI commitments:
- dpa_has_ai_clause: TRUE if DPA has section \
specifically addressing AI/ML processing.
- dpa_prohibits_training_on_customer_data: TRUE if DPA \
prohibits AI training on customer data without written \
agreement.
- dpa_requires_consent_for_ai_processing: TRUE if DPA \
requires customer consent before AI processing.
- dpa_addresses_ai_subprocessors: TRUE if AI-specific \
sub-processors addressed separately.
- dpa_has_ai_audit_rights: TRUE if DPA grants audit \
rights specifically over AI processing.

Section I — Compliance certifications:
- iso_42001_certified: TRUE if ISO 42001 certification \
claimed.
- nist_ai_rmf_referenced: TRUE if NIST AI RMF referenced.
- iso_23894_referenced: TRUE if ISO 23894 referenced.

Section J — Contradictions and red flags:
- training_claim_contradicts_inference_retention: TRUE \
if "we don't train on your data" contradicted by \
retaining inference data for improvement.
- opt_out_denied_for_ai_features: TRUE if customers \
cannot opt out of AI processing when using AI features.
- ai_use_without_disclosure: TRUE if vendor appears to \
use AI but documents don't disclose it. Flag for \
human review.
- customer_data_used_for_foundation_model_training: \
TRUE if customer data used for foundation model \
training (not just fine-tuning).
- is_ai_vendor_inferred: TRUE if is_ai_vendor was \
inferred from product descriptions rather than \
explicit AI disclosure.

Documents to analyse:
{docs_text}"""

    def analyse(
        self,
        vendor_name: str,
        documents: list[AgentDocument],
        intake_context: str | None = None,
    ) -> AgentResult:
        """
        Run AI Bandit analysis.
        Returns AgentResult with D6 signals.
        """
        if not self._should_trigger(
            documents, intake_context
        ):
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error="No AI-related documents found "
                      "and vendor not marked as AI vendor",
            )

        selected = self._select_documents(documents)
        if not selected:
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error="No suitable documents for "
                      "AI analysis",
            )

        self._progress(
            f"AI Bandit — analysing "
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
                f"AI Bandit failed for "
                f"{vendor_name}: {e}"
            )
            return AgentResult(
                agent_name=self.name,
                vendor_name=vendor_name,
                success=False,
                error=str(e),
            )

        # Build signals dict — pass through all extracted signals
        signals = self._build_signals(result)

        # Build framework evidence
        framework_evidence = {}
        if result.get("iso_42001_certified") is True:
            framework_evidence["iso_42001_certified"] = True

        # Build findings list
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
        Pass through all signals from RUBRIC_AI_POLICY.md.

        Uses exact signal names from the rubric so
        rubric.py finds them. None values are preserved
        (NULL = not addressed).
        """
        signals = {}
        for sig_name in _ALL_AI_SIGNALS:
            val = result.get(sig_name)
            # Normalise "unknown" to None
            if val == "unknown":
                val = None
            signals[sig_name] = val

        # Also keep legacy d6_ prefixed signals for backward
        # compatibility with the level-walk scoring
        signals["d6_ai_mentioned"] = (
            result.get("is_ai_vendor") is True
        )
        signals["d6_ai_disclosed_as_separate_purpose"] = (
            result.get("ai_in_customer_facing_service") is True
        )
        signals["d6_opt_out_exists"] = (
            result.get("opt_out_available") is True
        )
        signals["d6_opt_out_prominent"] = (
            result.get("opt_out_prominent") is True
        )
        signals["d6_opt_in_for_training"] = (
            result.get("opt_in_required") is True
        )
        signals["d6_legal_basis_identified"] = (
            result.get("legal_basis_stated") is True
        )
        signals["d6_customer_data_segregation"] = (
            result.get(
                "customer_data_segregated_from_training"
            ) is True
        )
        signals["d6_training_data_retention_schedule"] = (
            result.get("training_data_retention_stated") is True
        )
        signals["d6_dpa_ai_restriction_clause"] = (
            result.get(
                "dpa_prohibits_training_on_customer_data"
            ) is True
        )
        signals["d6_ai_act_art53_compliance"] = (
            result.get("eu_ai_act_addressed") is True
        )
        signals["d6_algorithmic_disgorgement_readiness"] = (
            result.get(
                "algorithmic_disgorgement_addressed"
            ) is True
        )
        signals["d6_bias_mitigation_documented"] = (
            result.get("bias_mitigation_documented") is True
        )
        signals["d6_update_cadence_stated"] = (
            result.get("model_updates_disclosed") is True
        )
        signals["d6_data_categories_specified"] = bool(
            result.get("third_party_ai_providers_listed")
            or result.get("training_data_sources_disclosed")
        )
        # Negative signal — trains without consent
        signals["d6_trains_without_consent"] = (
            result.get("trains_on_customer_data") is True
            and result.get("opt_out_available") is not True
            and result.get("opt_in_required") is not True
        )

        return signals
