"""
Legal Bandit — Data Models
===========================
All data models used by the Legal Bandit agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProvisionStatus(str, Enum):
    PRESENT_SPECIFIC = "present_specific"
    PRESENT_VAGUE    = "present_vague"
    ABSENT           = "absent"
    NOT_APPLICABLE   = "not_applicable"


class ConflictSeverity(str, Enum):
    HIGH   = "high"    # D5 D6 D8 policy stronger than DPA
    MEDIUM = "medium"  # other dimensions
    LOW    = "low"     # minor discrepancies


class ChangeType(str, Enum):
    REQUIRED    = "required"     # must resolve before signing
    RECOMMENDED = "recommended"  # negotiate if possible
    ACCEPTABLE  = "acceptable"   # no action needed


@dataclass
class ProvisionAssessment:
    """Assessment of a single DPA/MSA provision."""
    provision_id: str         # "art28_3a", "breach_sla" etc
    provision_name: str       # "Processing on instructions"
    regulatory_ref: str       # "GDPR Art. 28(3)(a)"
    status: ProvisionStatus
    verbatim_quote: str | None  # exact text from document
    section_reference: str | None  # "§5.1", "Clause 8.2"
    sla_value: str | None     # "48 hours", "30 days" if applicable
    gaps: list[str] = field(default_factory=list)
    vague_phrases: list[str] = field(default_factory=list)
    change_type: ChangeType = ChangeType.ACCEPTABLE
    redline_recommendation: str | None = None
    enforcement_precedent: str | None = None


@dataclass
class PolicyContractConflict:
    """A case where policy claims more than DPA commits."""
    dimension: str            # "D5"
    signal_key: str           # "d5_specific_sla_hours"
    policy_claim: str         # what policy says
    contract_reality: str     # what DPA actually says (or absent)
    conflict_type: str        # "policy_unbacked" | "contradiction"
    severity: ConflictSeverity
    recommendation: str       # what to add to DPA


@dataclass
class DimensionContractScore:
    """Contract-based score for a dimension."""
    dimension: str            # "D5"
    policy_score: int         # score from policy alone
    contract_score: int       # score from contract assessment
    final_score: int          # what gets used
    final_source: str         # "contract" | "policy" | "merged"
    score_changed: bool       # did contract change the score
    score_direction: str      # "up" | "down" | "unchanged"
    evidence_summary: str     # brief explanation


@dataclass
class MSAAssessment:
    """Commercial data protection terms from MSA."""
    liability_cap_excludes_breaches: bool | None
    liability_cap_value: str | None
    indemnification_for_breaches: bool | None
    data_ownership_clause: bool | None
    governing_law: str | None
    dispute_resolution: str | None
    termination_for_cause_includes_breach: bool | None
    data_return_on_termination_days: int | None
    survival_clauses: list[str] = field(default_factory=list)
    verbatim_liability_clause: str | None = None
    verbatim_termination_clause: str | None = None
    concerns: list[str] = field(default_factory=list)


@dataclass
class SCCAssessment:
    """Standard Contractual Clauses assessment."""
    scc_version: str | None   # "EU 2021/914" or "2010"
    module: str | None        # "Module 2" or "Module 3"
    properly_executed: bool | None
    annex_1a_completed: bool | None  # parties
    annex_1b_completed: bool | None  # transfer description
    annex_2_completed: bool | None   # technical measures
    annex_3_completed: bool | None   # sub-processors
    tia_referenced: bool | None
    outdated: bool = False    # True if pre-2021 SCCs


@dataclass
class LegalBanditResult:
    """Full result from Legal Bandit assessment."""
    vendor_name: str
    assessment_date: str

    # Documents assessed
    dpa_assessed: bool
    msa_assessed: bool
    scc_assessed: bool
    dpa_source: str | None    # filename
    msa_source: str | None
    scc_source: str | None

    # DPA Art. 28 checklist
    provisions: list[ProvisionAssessment] = field(
        default_factory=list
    )

    # MSA commercial terms
    msa: MSAAssessment | None = None

    # SCC assessment
    sccs: SCCAssessment | None = None

    # Policy/contract conflicts
    conflicts: list[PolicyContractConflict] = field(
        default_factory=list
    )

    # Updated dimension scores
    dimension_scores: list[DimensionContractScore] = field(
        default_factory=list
    )

    # Summary counts
    required_changes: int = 0
    recommended_changes: int = 0
    acceptable_provisions: int = 0
    conflicts_count: int = 0

    # Whether to auto-escalate
    escalation_required: bool = False
    escalation_reasons: list[str] = field(
        default_factory=list
    )
