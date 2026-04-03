"""
Legal Bandit — Extraction Prompts
===================================
LLM prompts that extract structured data WITH verbatim quotes
from legal documents (DPA, MSA, SCCs).
"""
from __future__ import annotations


def get_dpa_legal_prompt(vendor_name: str, dpa_text: str) -> str:
    return f"""You are a senior privacy lawyer conducting
a contract review for a client onboarding {vendor_name}
as a data processor.

Review this DPA against GDPR Art. 28(3)(a)-(h) requirements.
For each provision extract the EXACT verbatim text from
the document. If a provision is absent say null.

Reply with ONLY valid JSON — no markdown, no explanation:

{{
  "art28_3a_instructions": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<e.g. §5.1 or null>",
    "gaps": ["list specific gaps"],
    "vague_phrases": ["list vague unenforceable phrases"]
  }},
  "art28_3b_confidentiality": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "gaps": [],
    "vague_phrases": []
  }},
  "art28_3c_security": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "named_standards": ["ISO 27001", "SOC 2"],
    "gaps": ["no specific standard named"],
    "vague_phrases": ["appropriate measures"]
  }},
  "art28_3d_sub_processors": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "prior_consent_required": <true|false|null>,
    "objection_right": <true|false|null>,
    "termination_option_on_objection": <true|false|null>,
    "flow_down_obligations": <true|false|null>,
    "notification_period_days": <number or null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "art28_3e_dsar_assistance": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "forwarding_timeframe_days": <number or null>,
    "assistance_scope_defined": <true|false|null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "art28_3f_dpia_assistance": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "gaps": [],
    "vague_phrases": []
  }},
  "art28_3g_deletion_return": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "deletion_timeframe_days": <number or null>,
    "return_option": <true|false|null>,
    "certification_provided": <true|false|null>,
    "backups_addressed": <true|false|null>,
    "sub_processor_deletion": <true|false|null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "art28_3h_audit_rights": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "audit_frequency_stated": <true|false|null>,
    "notice_period_days": <number or null>,
    "extends_to_sub_processors": <true|false|null>,
    "remote_audit_accepted": <true|false|null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "breach_notification": {{
    "present": <true|false>,
    "specific": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "sla_hours": <number or null>,
    "art33_3_content_committed": <true|false|null>,
    "customer_notification_committed": <true|false|null>,
    "suspected_incidents_covered": <true|false|null>,
    "forensic_preservation_committed": <true|false|null>,
    "phased_reporting": <true|false|null>,
    "gaps": [],
    "vague_phrases": ["promptly", "without undue delay"]
  }},
  "ai_ml_restriction": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "explicit_restriction": <true|false|null>,
    "opt_out_mechanism": <true|false|null>,
    "retroactive_deletion": <true|false|null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "international_transfers": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "mechanism_named": <true|false|null>,
    "scc_module_specified": <true|false|null>,
    "scc_module_number": "<Module 2|Module 3|null>",
    "tia_committed": <true|false|null>,
    "gaps": [],
    "vague_phrases": []
  }},
  "governing_law": "<jurisdiction string or null>",
  "dpa_version_controlled": <true|false|null>,
  "processing_annex_exists": <true|false|null>,
  "toms_annex_exists": <true|false|null>,
  "overall_quality": "<bespoke|template_adapted|verbatim_template>",
  "red_flags": ["list any seriously concerning clauses verbatim"]
}}

DPA TEXT:
{dpa_text[:15000]}"""


def get_msa_legal_prompt(vendor_name: str, msa_text: str) -> str:
    return f"""You are a senior commercial lawyer reviewing
a Master Services Agreement with {vendor_name} for
data protection relevant provisions.

Extract EXACT verbatim text for each clause.

Reply with ONLY valid JSON:

{{
  "liability_cap": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "cap_value": "<e.g. 12 months fees, £1M or null>",
    "excludes_data_breaches": <true|false|null>,
    "excludes_gdpr_fines": <true|false|null>
  }},
  "indemnification": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "covers_data_breaches": <true|false|null>,
    "covers_regulatory_fines": <true|false|null>
  }},
  "data_ownership": {{
    "present": <true|false>,
    "verbatim_quote": "<exact text or null>",
    "controller_owns_data": <true|false|null>
  }},
  "termination": {{
    "verbatim_quote": "<exact text or null>",
    "section_reference": "<or null>",
    "for_cause_includes_breach": <true|false|null>,
    "data_return_days": <number or null>,
    "data_deletion_days": <number or null>,
    "survival_clauses": ["list obligations that survive"]
  }},
  "governing_law": "<jurisdiction or null>",
  "dispute_resolution": "<ICC arbitration, LCIA, courts etc or null>",
  "dpa_incorporated_by_reference": <true|false|null>,
  "concerns": ["list any concerning clauses for data protection"]
}}

MSA TEXT:
{msa_text[:15000]}"""


def get_scc_legal_prompt(vendor_name: str, scc_text: str) -> str:
    return f"""Review these Standard Contractual Clauses
for {vendor_name}.

Reply with ONLY valid JSON:

{{
  "scc_version": "<EU 2021/914 or 2010/87/EU or other>",
  "module": "<Module 1|Module 2|Module 3|Module 4|null>",
  "properly_executed": <true|false>,
  "annex_1a_completed": <true|false>,
  "annex_1b_completed": <true|false>,
  "annex_2_completed": <true|false>,
  "annex_3_completed": <true|false|null>,
  "tia_referenced": <true|false>,
  "outdated": <true if pre-2021 SCCs>,
  "concerns": ["list any issues"]
}}

SCC TEXT:
{scc_text[:10000]}"""
