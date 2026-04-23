"""
AI Bandit — specialist D6 agent.

Performs deep analysis of AI/ML usage disclosures, model cards,
AI policies, and DPA AI clauses. Produces high-confidence D6
signals and findings for the GRC and Legal reports.
"""
from __future__ import annotations

import logging
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

SYSTEM_PROMPT = """You are an AI governance analyst \
specialising in vendor AI risk assessment for \
enterprise GRC teams. You evaluate AI policies, \
model cards, and contract AI clauses against GDPR \
Art. 22, EU AI Act, FTC enforcement precedents, \
and enterprise data protection requirements.

Return ONLY valid JSON — no markdown, no explanation, \
no code fences. Be precise and evidence-based. \
Do not infer or assume — only report what is \
explicitly stated in the provided text."""


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
        max_tokens: int = 4000,
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
        """Build the AI analysis prompt."""

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

        return f"""Analyse the following documents for \
{vendor_name} and assess their AI/ML data practices.
{intake_section}
Return ONLY this JSON object:

{{
  "is_ai_vendor": <true|false>,
  "ai_in_service": <true|false>,
  "trains_on_customer_data": <true|false|"unknown">,
  "opt_out_available": <true|false|"unknown">,
  "opt_out_prominent": <true|false|"unknown">,
  "opt_in_required": <true|false|"unknown">,
  "legal_basis_stated": <true|false>,
  "legal_basis_detail": "<string or null>",
  "data_categories_for_training": ["<category>"],
  "customer_data_segregated": <true|false|"unknown">,
  "ai_training_retention_stated": <true|false>,
  "dpa_has_ai_restriction_clause": <true|false>,
  "eu_ai_act_addressed": <true|false>,
  "eu_ai_act_risk_tier": "<minimal|limited|high|unacceptable|unknown>",
  "iso_42001_certified": <true|false>,
  "algorithmic_disgorgement_addressed": <true|false>,
  "bias_fairness_documented": <true|false>,
  "model_update_cadence_stated": <true|false>,
  "d6_score_recommendation": <1|2|3|4|5>,
  "d6_rationale": "<one paragraph>",
  "red_flags": ["<specific concern from text>"],
  "top_findings": [
    "<finding 1 — specific, cite document section>",
    "<finding 2>",
    "<finding 3>"
  ],
  "recommended_dpa_clause": "<specific clause language>",
  "questions_for_vendor": [
    "<targeted question 1>",
    "<targeted question 2>",
    "<targeted question 3>"
  ]
}}

D6 scoring guide:
5 — Explicit opt-in required, customer data segregated, \
legal basis stated, AI training retention defined, \
DPA has explicit AI restriction clause
4 — Opt-out available and prominent, legal basis \
stated, minimal use of customer data for training
3 — AI use disclosed, opt-out exists but not prominent, \
partial controls documented
2 — AI use disclosed but opt-out unclear, vague legal \
basis, customer data may be used for training
1 — No AI disclosure, customer data used for training \
without consent mechanism, or active opt-out denied

DOCUMENTS:
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

        # Build signals dict for rubric
        signals = self._build_signals(result)

        # Build framework evidence
        framework_evidence = {}
        if result.get("iso_42001_certified"):
            framework_evidence["iso_42001_certified"] = True

        # Score override if high confidence
        score_overrides = {}
        rec_score = result.get("d6_score_recommendation")
        if rec_score and isinstance(rec_score, int):
            score_overrides["D6"] = rec_score

        # Build findings list
        findings = result.get("top_findings", [])
        red_flags = result.get("red_flags", [])

        return AgentResult(
            agent_name=self.name,
            vendor_name=vendor_name,
            success=True,
            signals=signals,
            framework_evidence=framework_evidence,
            score_overrides=score_overrides,
            findings=findings + red_flags,
            raw_result=result,
            documents_analysed=[
                d.filename for d in selected
            ],
        )

    def _build_signals(self, result: dict) -> dict:
        """
        Translate LLM result into D6 signal keys
        that the rubric engine expects.
        """

        def _bool(val, default=False):
            if isinstance(val, bool):
                return val
            if val == "unknown":
                return default
            return default

        return {
            # D6 signals — mapped to existing rubric keys
            "d6_ai_mentioned":
                result.get("is_ai_vendor", False),
            "d6_ai_disclosed_as_separate_purpose":
                result.get("ai_in_service", False),
            "d6_opt_out_exists":
                _bool(result.get("opt_out_available")),
            "d6_opt_out_prominent":
                _bool(result.get("opt_out_prominent")),
            "d6_opt_in_for_training":
                _bool(result.get("opt_in_required")),
            "d6_legal_basis_identified":
                result.get("legal_basis_stated", False),
            "d6_customer_data_segregation":
                _bool(result.get(
                    "customer_data_segregated"
                )),
            "d6_training_data_retention_schedule":
                result.get(
                    "ai_training_retention_stated", False
                ),
            "d6_dpa_ai_restriction_clause":
                result.get(
                    "dpa_has_ai_restriction_clause", False
                ),
            "d6_ai_act_art53_compliance":
                result.get("eu_ai_act_addressed", False),
            "d6_algorithmic_disgorgement_readiness":
                result.get(
                    "algorithmic_disgorgement_addressed",
                    False
                ),
            "d6_bias_mitigation_documented":
                result.get("bias_fairness_documented", False),
            "d6_update_cadence_stated":
                result.get(
                    "model_update_cadence_stated", False
                ),
            "d6_data_categories_specified":
                bool(result.get(
                    "data_categories_for_training"
                )),
            # Negative signal — trains without consent
            "d6_trains_without_consent":
                (result.get("trains_on_customer_data") is True
                 and not _bool(result.get("opt_out_available"))
                 and not _bool(result.get("opt_in_required"))),
        }
