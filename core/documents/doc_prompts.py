"""
Bandit Document Prompts
========================
Type-specific extraction prompts for each document type.
Each prompt knows what signals to extract for that document.
These are passed to the LLM extraction call in the ingestor.
"""
from __future__ import annotations

from core.documents.classifier import DocumentType


def get_extraction_prompt(
    doc_type: DocumentType,
    vendor_name: str,
    doc_text: str,
) -> str:

    base = (
        f"You are a privacy compliance analyst. "
        f"Carefully read this {doc_type.value.replace('_', ' ')} "
        f"document for {vendor_name}.\n\n"
        f"Extract ONLY the following signals as a JSON object. "
        f"Reply with ONLY valid JSON — no markdown, "
        f"no explanation, no code fences.\n\n"
    )

    prompts = {

        DocumentType.DPA: base + """
Extract these signals from the DPA:
{
  "d2_named_sub_processors": <true if sub-processors are named>,
  "d2_sub_processor_list_available": <true if list is accessible>,
  "d2_change_notification_period_days": <number or null>,
  "d2_objection_right": <true if controller can object>,
  "d2_audit_rights": <true if audit rights exist>,
  "d2_audit_rights_extend_to_subs": <true if extends to sub-processors>,
  "d2_flow_down_obligations": <true if obligations flow to subs>,
  "d4_transfer_mechanism_stated": <true if mechanism named>,
  "d4_scc_module_specified": <true if SCC module number specified>,
  "d4_tia_committed": <true if TIA is committed to>,
  "d5_breach_notification_sla_hours": <number or null>,
  "d5_notification_content_art33": <true if Art.33(3) content committed>,
  "d5_customer_notification_committed": <true if customer notification committed>,
  "d5_phased_reporting": <true if phased reporting addressed>,
  "d7_deletion_on_termination": <true if deletion on termination committed>,
  "d7_deletion_timeframe_days": <number or null>,
  "d7_return_option": <true if return of data is an option>,
  "d8_art28_subject_matter": <true if processing subject matter defined>,
  "d8_art28_duration": <true if processing duration defined>,
  "d8_art28_nature_purpose": <true if nature and purpose defined>,
  "d8_art28_data_types": <true if personal data types listed>,
  "d8_art28_data_subjects": <true if data subject categories listed>,
  "d8_art28_controller_obligations": <true if controller obligations listed>,
  "d8_art28_confidentiality": <true if confidentiality obligation present>,
  "d8_art28_security_measures": <true if security measures specified>,
  "d8_art28_security_measures_specific": <true if measures are specific not generic>,
  "d8_art28_sub_processor_approval": <true if prior approval required>,
  "d8_art28_audit_rights": <true if audit/inspection rights present>,
  "d8_art28_deletion_return": <true if deletion/return obligation present>,
  "d8_art28_assistance_dsars": <true if DSAR assistance committed>,
  "d3_dsar_procedure_documented": <true if DPA includes a process for handling data subject requests>,
  "d3_some_rights_listed": <true if data subject rights (access, deletion, etc.) are mentioned or committed to>,
  "d8_art28_assistance_security": <true if security assistance committed>,
  "d8_art28_assistance_breach": <true if breach notification assistance committed>,
  "d8_art28_assistance_dpia": <true if DPIA assistance committed>,
  "d8_governing_law": "<jurisdiction string or null>",
  "d8_hipaa_baa_provisions": <true if HIPAA BAA provisions present>,
  "red_flags": ["list any concerning phrases verbatim"]
}

DPA document:
""" + doc_text[:12000],

        DocumentType.BAA: base + """
Extract these signals from the BAA:
{
  "d5_breach_notification_sla_days": <number — HIPAA requires 60 days max>,
  "d5_individual_notification_committed": <true if notification to individuals>,
  "d5_hhs_notification_committed": <true if HHS notification committed>,
  "d5_media_notification_committed": <true if media notification for >500>,
  "d5_low_probability_safe_harbor": <true if low probability assessment referenced>,
  "d8_permitted_uses_phi_listed": <true if PHI permitted uses are listed>,
  "d8_safeguard_obligations": <true if HIPAA safeguard obligations present>,
  "d8_subcontractor_baa_requirement": <true if BAA flows to subcontractors>,
  "d8_return_destruction_phi": <true if PHI return or destruction committed>,
  "d8_hitech_compliance": <true if HITECH Act compliance referenced>,
  "d8_minimum_necessary": <true if minimum necessary standard referenced>,
  "d8_access_controls": <true if access controls for PHI specified>,
  "d1_phi_categories_listed": <true if specific PHI categories are listed>,
  "red_flags": ["list any concerning phrases verbatim"]
}

BAA document:
""" + doc_text[:12000],

        DocumentType.SOC2_TYPE2: base + """
Extract these signals from the SOC 2 Type II report:
{
  "audit_period_from": "<date string or null>",
  "audit_period_to": "<date string or null>",
  "audit_firm": "<auditor firm name or null>",
  "trust_service_criteria": ["list of TSC covered e.g. CC, A, C, P, PI"],
  "privacy_tsc_included": <true if Privacy TSC included>,
  "exceptions_noted": <true if auditor noted any exceptions>,
  "exceptions_list": ["list exception descriptions if any"],
  "d2_access_controls_attested": <true if CC6 logical access controls attested>,
  "d2_vendor_management_attested": <true if vendor/sub-processor management attested>,
  "d5_incident_response_attested": <true if CC7 incident response attested>,
  "d5_breach_procedures_attested": <true if breach notification procedures attested>,
  "d7_data_disposal_attested": <true if data disposal/retention attested>,
  "d8_change_management_attested": <true if change management attested>,
  "subservice_organizations": ["list any carved-out subservice organizations"],
  "report_type": "type2",
  "red_flags": ["list any exceptions or concerning findings verbatim"]
}

SOC 2 Type II report:
""" + doc_text[:12000],

        DocumentType.SOC1_TYPE2: base + """
Extract these signals from the SOC 1 Type II report:
{
  "audit_period_from": "<date string or null>",
  "audit_period_to": "<date string or null>",
  "audit_firm": "<auditor firm name or null>",
  "exceptions_noted": <true if auditor noted any exceptions>,
  "exceptions_list": ["list exception descriptions if any"],
  "financial_controls_attested": <true>,
  "d7_data_retention_controls": <true if data retention controls attested>,
  "d5_incident_procedures": <true if incident procedures mentioned>,
  "report_type": "soc1_type2",
  "red_flags": ["list any exceptions verbatim"]
}

SOC 1 Type II report:
""" + doc_text[:12000],

        DocumentType.ISO27001: base + """
Extract these signals from the ISO 27001 certificate:
{
  "standard": "<e.g. ISO/IEC 27001:2022>",
  "certification_scope": "<scope statement>",
  "certification_date": "<date or null>",
  "expiry_date": "<date or null>",
  "certification_body": "<accredited CB name>",
  "surveillance_audit_current": <true if surveillance audits up to date>,
  "iso27701_extension": <true if ISO 27701 also certified>,
  "iso42001_extension": <true if ISO 42001 also certified>,
  "red_flags": ["list any scope exclusions or limitations"]
}

ISO 27001 certificate:
""" + doc_text[:5000],

        DocumentType.ISO27701: base + """
Extract these signals from the ISO 27701 certificate:
{
  "standard": "ISO/IEC 27701",
  "certification_scope": "<scope statement>",
  "certification_date": "<date or null>",
  "expiry_date": "<date or null>",
  "certification_body": "<CB name>",
  "pims_scope": "<privacy information management scope>",
  "controller_certified": <true if controller scope included>,
  "processor_certified": <true if processor scope included>,
  "red_flags": []
}

ISO 27701 certificate:
""" + doc_text[:5000],

        DocumentType.ISO42001: base + """
Extract these signals from the ISO 42001 certificate:
{
  "standard": "ISO/IEC 42001",
  "certification_scope": "<AI system scope>",
  "certification_date": "<date or null>",
  "expiry_date": "<date or null>",
  "certification_body": "<CB name>",
  "ai_systems_in_scope": ["list AI systems covered"],
  "eu_ai_act_alignment": <true if EU AI Act alignment mentioned>,
  "red_flags": []
}

ISO 42001 certificate:
""" + doc_text[:5000],

        DocumentType.AI_POLICY: base + """
Extract these signals from the AI policy:
{
  "d6_ai_training_on_customer_data": <true if customer data used for training>,
  "d6_training_opt_out_available": <true if opt-out mechanism exists>,
  "d6_opt_out_mechanism_described": <true if how to opt out is explained>,
  "d6_ai_purpose_disclosed": <true if AI/ML purposes are disclosed>,
  "d6_ai_vendors_listed": <true if AI sub-vendors/models are named>,
  "d6_eu_ai_act_compliance_claimed": <true if EU AI Act compliance claimed>,
  "d6_high_risk_ai_disclosed": <true if high-risk AI uses are disclosed>,
  "d6_human_oversight_committed": <true if human oversight is committed>,
  "d6_prohibited_practices_addressed": <true if prohibited AI practices addressed>,
  "d6_model_governance": <true if model governance process described>,
  "d6_data_minimization_ai": <true if data minimization for AI stated>,
  "red_flags": ["list any concerning training or usage phrases verbatim"]
}

AI Policy document:
""" + doc_text[:10000],

        DocumentType.MODEL_CARD: base + """
Extract these signals from the model card:
{
  "d6_training_data_sources": ["list training data sources mentioned"],
  "d6_personal_data_in_training": <true if personal data used in training>,
  "d6_opt_out_for_training": <true if opt-out exists>,
  "d6_intended_use_cases": ["list intended uses"],
  "d6_prohibited_uses": ["list prohibited uses"],
  "d6_known_limitations": ["list limitations"],
  "d6_eu_ai_act_risk_level": "<prohibited|high|limited|minimal|null>",
  "red_flags": ["list any personal data training concerns verbatim"]
}

Model card:
""" + doc_text[:10000],

        DocumentType.MSA: base + """
Extract these signals from the MSA:
{
  "d5_breach_liability": <true if vendor has liability for breaches>,
  "d5_breach_indemnification": <true if indemnification for breaches>,
  "d7_data_on_termination": <true if data handling on termination addressed>,
  "d7_termination_deletion_timeframe": "<timeframe string or null>",
  "d8_data_ownership_clause": <true if data ownership clause present>,
  "d8_dpa_incorporated": <true if DPA is incorporated by reference>,
  "d8_governing_law": "<jurisdiction or null>",
  "d8_liability_cap": "<liability cap description or null>",
  "d3_dsar_cooperation": <true if vendor commits to DSAR cooperation>,
  "red_flags": ["list any concerning data or liability clauses verbatim"]
}

MSA document:
""" + doc_text[:12000],

        DocumentType.TIA: base + """
Extract these signals from the Transfer Impact Assessment:
{
  "d4_transfer_countries": ["list destination countries assessed"],
  "d4_scc_module": "<module number or null>",
  "d4_adequacy_decision_exists": <true if adequacy decision applies>,
  "d4_supplementary_measures": ["list supplementary measures"],
  "d4_surveillance_law_assessed": <true if destination country surveillance assessed>,
  "d4_effective_remedy_assessed": <true if effective remedy assessed>,
  "d4_tia_conclusion": "<transfer approved|conditional|refused|null>",
  "red_flags": ["list any high-risk findings verbatim"]
}

TIA document:
""" + doc_text[:10000],

        DocumentType.PCI_AOC: base + """
Extract these signals from the PCI AOC:
{
  "pci_dss_version": "<version number>",
  "assessment_date": "<date or null>",
  "qsa_firm": "<QSA firm name or null>",
  "merchant_service_provider_level": "<level or null>",
  "compliant": <true if compliant at time of assessment>,
  "d7_cardholder_data_retention_addressed": <true>,
  "d2_service_provider_responsibilities": <true if SP responsibilities listed>,
  "red_flags": ["list any non-compliant findings verbatim"]
}

PCI AOC document:
""" + doc_text[:8000],

        DocumentType.SUB_PROCESSOR_LIST: base + """
Extract these signals from the sub-processor list:
{
  "d2_sub_processors_named": <true>,
  "d2_sub_processor_count": <number or null>,
  "d2_countries_of_processing": ["list countries"],
  "d2_purposes_listed": <true if processing purposes are listed>,
  "d2_last_updated": "<date or null>",
  "d2_high_risk_countries": ["any sub-processors in high-risk countries"],
  "red_flags": ["list any high-risk sub-processor locations or names"]
}

Sub-processor list:
""" + doc_text[:8000],

        DocumentType.HITRUST: base + """
Extract these signals from the HITRUST report:
{
  "hitrust_version": "<CSF version>",
  "assessment_date": "<date or null>",
  "certification_date": "<date or null>",
  "expiry_date": "<date or null>",
  "scope": "<assessed scope>",
  "d5_incident_management_attested": <true>,
  "d8_hipaa_controls_attested": <true>,
  "d2_third_party_assurance_attested": <true>,
  "exceptions_noted": <true if any corrective actions noted>,
  "red_flags": ["list any corrective actions or findings"]
}

HITRUST document:
""" + doc_text[:10000],

        DocumentType.FEDRAMP_ATO: base + """
Extract these signals from the FedRAMP ATO:
{
  "impact_level": "<Low|Moderate|High>",
  "authorization_date": "<date or null>",
  "expiry_date": "<date or null>",
  "authorizing_agency": "<agency name or null>",
  "cloud_service_model": "<IaaS|PaaS|SaaS|null>",
  "continuous_monitoring": <true if ConMon in place>,
  "red_flags": []
}

FedRAMP ATO document:
""" + doc_text[:8000],

    }

    # Default prompt for unhandled types
    default = base + f"""
Extract all privacy and data protection relevant signals
as a flat JSON object with boolean or string values.
Focus on: data retention, breach notification, sub-processors,
transfer mechanisms, data subject rights, AI/ML usage,
DPA completeness.

Document:
""" + doc_text[:10000]

    return prompts.get(doc_type, default)
