# RUBRIC_SOC2

Bandit's authoritative extraction and scoring
reference for SOC 2 reports. Every signal the
Audit Bandit extracts from a SOC 2 must be
defined here with explicit yes/no criteria.
The LLM extracts signals. The rubric engine
scores. Two different models reading the same
report must produce the same signal dict —
otherwise the scoring is not deterministic.

This document governs Audit Bandit's SOC 2
extraction. Changes here require updating
Audit Bandit's prompt template and the rubric
engine's SOC 2 signal table together.

---

## What a SOC 2 Type II report actually is

A Type II report is an independent auditor's
examination of a service organisation's
controls over a specified period (usually 6
or 12 months). The report includes:

1. **Independent auditor's report** — the
   opinion letter itself. Qualified,
   unqualified, adverse, or disclaimer.

2. **Management's assertion** — the vendor's
   own statement about their controls.

3. **Description of the system** — what's in
   scope, what isn't, complementary user
   entity controls (CUECs), complementary
   sub-service organisation controls
   (CSOCs), and carve-outs.

4. **Trust Services Criteria** — Security,
   Availability, Confidentiality, Processing
   Integrity, Privacy. Only the categories
   explicitly listed are in scope.

5. **Description of controls and tests** —
   each control, how it was tested, and
   the results.

6. **Exceptions and management responses** —
   any failures found during testing and
   the vendor's remediation plan.

Understanding this structure matters because
the extraction rules below reference specific
sections. A SOC 2 Type I is a point-in-time
assessment, not an examination over a period
— it's materially weaker evidence and should
be treated differently.

---

## Critical architectural rules

### Agents do not score

SOC 2 evaluation extracts **signals** (yes/no).
Scoring is deterministic in the rubric engine.
Two different LLMs reading the same report
must produce the same signal set. If they do
not, the extraction criteria are too vague.

### Absence is not denial

"Privacy TSC is not listed as in scope" is
different from "Privacy TSC is explicitly
excluded." The first means Bandit doesn't
know about privacy controls; the second
means the vendor chose not to have them
audited. Track both distinctly.

### Scope narrowing is a finding, not a score

If the SOC 2 scope excludes the product being
evaluated, that's a flagged finding for the
report. It does not automatically lower the
score, but it caps how much evidence weight
the SOC 2 can contribute.

### Exceptions require management responses

A SOC 2 exception without a management response
is treated as a worse signal than one with a
response. A vague management response ("we
will improve") is treated as weaker than a
specific one ("deployed new control on
2026-02-14").

### Firms are named, not rated

The report extracts the auditing firm's name.
A separate file (SOC2_FIRMS.md) contains a
list of recognised firms. Agents mark whether
the firm is on the recognised list (neutral
fact) but never assign quality scores to firms.

---

## Extraction signals

Every signal has three mandatory properties:

- **Exact criteria** — what must appear in the
  document for the signal to be TRUE
- **False vs null distinction** — when FALSE
  means "explicitly not" vs when it means "not
  found"
- **Source reference** — document section the
  LLM must cite if marking TRUE

### Section A — Report type and currency

**`soc2_type2_present`**
- TRUE: The document is explicitly identified
  as a SOC 2 Type II report. Look for the
  phrase "SOC 2 Type II" or "Type 2" in the
  title, cover page, or auditor's report
  section. Type 2 is an examination over a
  period, not a point-in-time.
- FALSE: Document is a SOC 2 Type I, a SOC 1,
  a SOC 3, an internal report, or cannot be
  determined.
- Required reference: Title page or
  auditor's opinion heading.

**`soc2_type1_present`**
- TRUE: The document is identified as a SOC 2
  Type I report. Type I is point-in-time.
- FALSE: Not a Type I.
- Required reference: Title page or
  opinion heading.
- Notes: Type I is weaker evidence than Type
  II. Useful but not substitute.

**`soc3_present`**
- TRUE: The document is a SOC 3 (general-use
  summary report). Much less detailed than
  SOC 2.
- FALSE: Not SOC 3.
- Notes: SOC 3 can confirm a SOC 2 exists
  but lacks the detail needed for evaluation.

**`audit_period_start`**
- VALUE: YYYY-MM-DD format. The beginning of
  the examination period as stated in the
  auditor's opinion or management's assertion.
- NULL: If no explicit start date is found.
- Required reference: Opinion letter or
  assertion section.

**`audit_period_end`**
- VALUE: YYYY-MM-DD format. The end of the
  examination period.
- NULL: If no explicit end date is found.
- Required reference: Opinion letter or
  assertion section.

**`report_issuance_date`**
- VALUE: YYYY-MM-DD format. The date the
  auditor signed the report.
- NULL: If no issuance date found.
- Required reference: End of auditor's
  opinion letter.
- Notes: Issuance date and period end date
  are different. A report issued 6 months
  after period end is normal.

**`audit_period_months`**
- VALUE: Number of months covered by the
  audit period. Calculated from period start
  to period end.
- NULL: If period cannot be determined.
- Notes: 6-month audits are common for first
  audits; 12-month is standard for mature
  vendors. Anything under 3 months is
  suspicious.

**`bridge_letter_present`**
- TRUE: A bridge letter (also called gap
  letter or subsequent period letter) is
  included with the report. The bridge
  letter is issued by the same auditor and
  confirms no material changes have occurred
  since the audit period ended.
- FALSE: No bridge letter included.
- Notes: Expected if period ended >9 months
  ago. Absence with a stale report is a
  finding.

**`bridge_letter_period_end`**
- VALUE: YYYY-MM-DD format. The end date the
  bridge letter covers.
- NULL: If no bridge letter or no end date.

### Section B — Auditor identification

**`auditor_firm_name`**
- VALUE: Exact name of the firm that issued
  the report as stated in the auditor's
  opinion letter.
- NULL: If firm name cannot be identified.
- Required reference: Signature block of
  the auditor's opinion.

**`auditor_firm_recognised`**
- TRUE: The extracted firm name appears on
  the recognised firms list in SOC2_FIRMS.md.
  This is a factual check, not a quality
  judgement.
- FALSE: Firm not on the recognised list.
- Notes: FALSE does not mean the firm is
  bad. It means Bandit cannot verify it
  against a known list.

**`auditor_firm_location`**
- VALUE: Country or US state where the
  firm is located, if stated.
- NULL: If not stated.

**`auditor_aicpa_member_stated`**
- TRUE: The report explicitly states the
  firm is a member of the AICPA or is
  licensed to perform SOC examinations.
- FALSE: No such statement found.

### Section C — Opinion type

**`opinion_type`**
- VALUE: One of:
  - "unqualified" — auditor issued an
    unqualified or unmodified opinion
    (controls operated effectively)
  - "qualified" — auditor issued a
    qualified opinion (some specific
    limitation or deviation)
  - "adverse" — auditor issued an
    adverse opinion (controls did not
    operate effectively) (rare)
  - "disclaimer" — auditor disclaimed
    an opinion (could not form one)
    (very bad)
- NULL: If opinion type cannot be determined.
- Required reference: Conclusion paragraph of
  the auditor's opinion.
- Notes: Look for phrases "in our opinion"
  followed by "the controls were suitably
  designed and operated effectively"
  (unqualified) or "except for" qualifiers
  (qualified).

**`opinion_qualifier_description`**
- VALUE: If opinion is qualified, the
  specific description of what the
  qualification relates to.
- NULL: If opinion is unqualified or
  qualification not described.

### Section D — Trust Services Criteria scope

**`tsc_security_in_scope`**
- TRUE: Security is explicitly listed in
  the scope as an applicable trust service
  category. Look for "Common Criteria"
  (Security), which is mandatory for SOC 2.
- FALSE: Security not in scope (should not
  happen; Security is mandatory).

**`tsc_availability_in_scope`**
- TRUE: Availability is explicitly listed
  as an applicable trust service category.
- FALSE: Availability is not in scope.
- Notes: Availability is optional. Its
  absence is not a failure.

**`tsc_confidentiality_in_scope`**
- TRUE: Confidentiality is explicitly listed.
- FALSE: Not in scope.

**`tsc_processing_integrity_in_scope`**
- TRUE: Processing Integrity is explicitly
  listed.
- FALSE: Not in scope.

**`tsc_privacy_in_scope`**
- TRUE: Privacy is explicitly listed as an
  applicable trust service category.
- FALSE: Privacy is not in scope.
- Required reference: Scope section or
  management's assertion.
- Notes: Privacy TSC is newer and less
  commonly included. A vendor claiming GDPR
  compliance without Privacy TSC in their
  SOC 2 is making unaudited claims.

**`tsc_privacy_exceptions_found`**
- TRUE: Privacy TSC is in scope AND the
  report contains exceptions related to
  privacy controls specifically.
- FALSE: Either Privacy TSC not in scope,
  OR Privacy TSC in scope with no
  exceptions.

### Section E — Scope and carve-outs

**`scope_description_present`**
- TRUE: The report contains a "Description
  of the System" section that explicitly
  identifies what products, services, or
  systems are covered.
- FALSE: No scope description section found.

**`scope_products_listed`**
- VALUE: List of specific products or
  services explicitly named as in scope.
  Copy the exact names as they appear.
- NULL: If no specific products listed.
- Example: ["Google Cloud Storage",
  "BigQuery", "Cloud KMS"]

**`scope_explicit_exclusions`**
- VALUE: List of products, services, or
  systems the report explicitly excludes
  from scope. This is a critical field —
  vendors sometimes exclude specific
  systems to avoid audit coverage.
- NULL: If no explicit exclusions stated.
- Example: ["Workspace consumer products",
  "Beta features"]

**`scope_narrowing_concern`**
- TRUE: The scope excludes major products
  or appears unusually narrow. Mark TRUE
  if:
  - Scope excludes named products while
    the vendor's website advertises them
  - Scope is explicitly limited to a
    single product line
  - Scope has changed narrower since a
    prior report (if comparison available)
- FALSE: Scope covers what a customer
  would expect.
- NULL: Cannot determine from the report
  alone.

### Section F — Carve-outs and sub-service organisations

**`carve_out_method_used`**
- TRUE: The report uses carve-out method —
  sub-service organisations are explicitly
  excluded and tested separately.
- FALSE: Report uses inclusive method —
  sub-service organisation controls are
  tested as part of this audit.
- Required reference: Scope or description
  of system section.

**`sub_service_organisations_listed`**
- VALUE: List of sub-service organisations
  that are carved out.
- NULL: If no carve-outs or not listed.
- Example: ["AWS (infrastructure)",
  "Stripe (payments)"]

**`cuecs_documented`**
- TRUE: Complementary User Entity Controls
  (CUECs) are explicitly documented. These
  are controls the customer (you) must
  implement for the vendor's controls to
  be effective.
- FALSE: No CUEC section found.
- Notes: A SOC 2 without CUECs is unusual
  and may indicate incomplete reporting.

**`cuec_list`**
- VALUE: List of specific CUECs documented.
  Include the full description, not just
  the title.
- NULL: If no CUECs documented.
- Example: ["User entity is responsible
  for implementing appropriate access
  controls for users of the service",
  "User entity is responsible for
  reviewing access periodically"]

**`csocs_documented`**
- TRUE: Complementary Sub-service
  Organisation Controls (CSOCs) are
  explicitly documented. These are
  controls that carved-out sub-service
  organisations must implement.
- FALSE: Not documented.

### Section G — Exceptions and management responses

**`exceptions_found`**
- TRUE: The report contains at least one
  exception or control failure in the
  testing results section.
- FALSE: No exceptions found in testing
  results.
- Notes: Zero exceptions is not always
  good — it can also indicate weak
  testing. Exception details matter more
  than exception count.

**`exception_count`**
- VALUE: Total number of exceptions found
  in the report.
- NULL: If exceptions section cannot be
  determined.

**`exception_details`**
- VALUE: List of exception entries, each
  containing:
  ```
  {
    "control_id": "CC6.1",
    "description": "Access review not
      completed within required timeframe",
    "severity": "minor|moderate|severe",
    "management_response_present": true,
    "management_response_specific": true,
    "remediation_timeframe": "Q1 2026",
    "remediation_complete_at_issuance": false
  }
  ```
- NULL: If no exceptions.

**`all_exceptions_have_responses`**
- TRUE: Every exception in the report has
  an accompanying management response.
- FALSE: At least one exception lacks a
  management response.
- Notes: A management response missing
  is a serious finding.

**`management_responses_are_specific`**
- TRUE: Management responses contain
  specific commitments (date, action,
  owner) rather than vague language
  ("we will improve", "we are working
  on this").
- FALSE: At least one response is vague.
- Notes: Vague responses indicate weak
  remediation planning.

**`exceptions_in_privacy_controls`**
- TRUE: At least one exception relates to
  privacy controls (if Privacy TSC is in
  scope).
- FALSE: Either Privacy TSC not in scope,
  or no privacy-related exceptions.

**`exceptions_in_access_controls`**
- TRUE: At least one exception relates to
  access control (CC6.x series controls).
- FALSE: No access control exceptions.

**`exceptions_in_change_management`**
- TRUE: At least one exception relates to
  change management (CC8.x series).
- FALSE: No change management exceptions.

**`exceptions_in_incident_response`**
- TRUE: At least one exception relates to
  incident response or breach handling
  (CC7.x series).
- FALSE: No incident response exceptions.

### Section H — Testing methodology

**`testing_includes_inspection`**
- TRUE: Tests of controls include
  inspection of evidence (documents,
  logs, configurations).
- FALSE: Inspection not evidenced.

**`testing_includes_observation`**
- TRUE: Tests include observation of
  controls operating.
- FALSE: Observation not evidenced.

**`testing_includes_reperformance`**
- TRUE: Tests include reperformance
  (auditor re-executes the control).
- FALSE: Reperformance not evidenced.

**`testing_primarily_inquiry`**
- TRUE: The majority of tests appear to
  be inquiry-only (asking management,
  no independent verification).
- FALSE: Tests include substantive
  evidence-based procedures.
- Notes: Inquiry-only testing is weak.
  Flag for review.

### Section I — Specific control coverage

These signals map to Bandit's 8 dimensions.

**`sub_processor_controls_tested`**
- TRUE: Controls over sub-processor or
  third-party management were tested
  (e.g., CC9.2 "The entity assesses
  risks associated with vendors").
- FALSE: No sub-processor controls
  tested.

**`breach_notification_controls_tested`**
- TRUE: Controls over incident
  notification or breach response were
  tested.
- FALSE: No such controls tested.

**`data_deletion_controls_tested`**
- TRUE: Controls over data deletion or
  disposal were tested.
- FALSE: No such controls tested.

**`encryption_controls_tested`**
- TRUE: Controls over encryption of data
  at rest and in transit were tested.
- FALSE: No encryption controls tested.

**`access_review_controls_tested`**
- TRUE: Controls over periodic access
  review were tested.
- FALSE: No access review controls
  tested.

**`vendor_risk_controls_tested`**
- TRUE: Controls over vendor or third-
  party risk management were tested.
- FALSE: Not tested.

### Section J — Framework version

**`uses_2022_tsc_framework`**
- TRUE: Report uses the 2017 Trust
  Services Criteria (2022 revision) —
  current framework.
- FALSE: Uses older framework or cannot
  determine.

**`uses_outdated_framework`**
- TRUE: Report uses Trust Services
  Principles (pre-2017) or control
  objectives framework (superseded).
- FALSE: Uses current framework.

---

## Derived values

Values computed from the raw extraction,
handled by the rubric engine (not the LLM).

**`currency_status`**
Calculated from `audit_period_end` and
today's date:
- "current" — period end within 12 months
- "stale" — period end 12–18 months ago,
  no bridge letter
- "stale_bridged" — period end 12–18
  months ago, bridge letter present
- "outdated" — period end >18 months ago
- "unknown" — period end cannot be
  determined

**`confidence_score`**
Calculated from:
- Opinion type (unqualified = higher)
- Exception count and severity
- All exceptions have responses
- Responses are specific
- Privacy TSC included
- Firm is recognised
- Scope is not narrowed

Range: 0.0 to 1.0. Used as a weight
multiplier for framework modifiers.

---

## Evidence-to-signal mapping

Maps SOC 2 signals to Bandit's 8 dimensions.
The rubric engine uses this table.

### D2 Sub-processor Management

**Positive modifiers:**
- `sub_processor_controls_tested = TRUE`
  AND no exceptions in that area: +0.3
- `tsc_privacy_in_scope = TRUE` AND no
  privacy exceptions: +0.2
- `opinion_type = "unqualified"`: +0.1

**Negative modifiers:**
- Exceptions in sub-processor controls
  without specific management response:
  -0.3
- `carve_out_method_used = TRUE` with
  sub-processors that aren't independently
  audited: -0.1

### D5 Breach Notification

**Positive modifiers:**
- `breach_notification_controls_tested =
  TRUE` with no exceptions: +0.4
- `tsc_privacy_in_scope = TRUE`: +0.2
- `opinion_type = "unqualified"`: +0.1

**Negative modifiers:**
- `exceptions_in_incident_response =
  TRUE`: -0.5 (major concern)
- `exceptions_in_incident_response =
  TRUE` without management response:
  additional -0.2

### D7 Retention and Deletion

**Positive modifiers:**
- `data_deletion_controls_tested = TRUE`
  with no exceptions: +0.3
- `tsc_confidentiality_in_scope = TRUE`:
  +0.1

**Negative modifiers:**
- Exceptions in deletion controls: -0.3

### D8 DPA Completeness / Independent Verification

This is where SOC 2 has the most impact.

**Positive modifiers:**
- `soc2_type2_present = TRUE` with
  `opinion_type = "unqualified"` and
  `currency_status = "current"`: +0.5
- `tsc_privacy_in_scope = TRUE`: +0.3
- `all_exceptions_have_responses = TRUE`
  AND `management_responses_are_specific
  = TRUE`: +0.2
- `auditor_firm_recognised = TRUE`: +0.1

**Negative modifiers:**
- `opinion_type = "qualified"`: -0.3
- `opinion_type = "adverse"`: -1.0
- `opinion_type = "disclaimer"`: -1.5
- `currency_status = "outdated"`: no
  modifier applied (SOC 2 ignored for
  scoring)
- `currency_status = "stale"` (no bridge):
  modifier reduced by 50%
- `scope_narrowing_concern = TRUE`:
  modifier reduced by 50%
- `exception_count > 5`: -0.2

**Score ceilings:**
- `opinion_type = "adverse"` or
  "disclaimer": D8 capped at 2
- `currency_status = "outdated"`: no
  ceiling applied, but no positive
  modifier either
- `soc2_type1_present = TRUE` (Type I
  only, no Type II): modifier reduced
  by 60% (Type I is much weaker evidence)

---

## Red flags that generate explicit findings

These combinations create high-priority
findings in the report regardless of the
final score:

1. **Scope excludes the product being
   evaluated** — `scope_narrowing_concern =
   TRUE` combined with intake Q6 showing
   that product as a critical integration

2. **Exceptions without management
   responses** — `all_exceptions_have_
   responses = FALSE`

3. **Stale audit with no bridge letter** —
   `currency_status = "stale"` and
   `bridge_letter_present = FALSE`

4. **Qualified opinion in Privacy TSC** —
   `opinion_type = "qualified"` and
   `tsc_privacy_in_scope = TRUE` and
   `tsc_privacy_exceptions_found = TRUE`

5. **Major carve-out of core
   infrastructure** — `carve_out_method_
   used = TRUE` and sub-service
   organisation is the primary
   infrastructure

6. **Adverse or disclaimer opinion** —
   any `opinion_type` of "adverse" or
   "disclaimer"

7. **Inquiry-only testing** —
   `testing_primarily_inquiry = TRUE`

8. **DPA/SOC 2 conflict** — DPA claims
   a control that SOC 2 shows as an
   exception. Detected by cross-checking
   signals from Audit Bandit with signals
   from Legal Bandit.

---

## Absence vs denial tracking

For every signal, distinguish between
"explicitly stated in document" vs "not
found in document." The LLM must mark a
signal FALSE only if the document
explicitly contradicts or doesn't meet
the criteria. If a signal is simply not
addressed, return NULL not FALSE.

Report output uses this distinction:
- FALSE renders as ✗ (explicitly absent)
- NULL renders as ? (not addressed)
- TRUE renders as ✓ (explicitly present)

---

## Implementation notes for Audit Bandit

When rebuilding the Audit Bandit prompt
from this rubric:

1. Include the critical architectural
   rules from the top of this document
2. Build the JSON schema from the
   signals list above
3. For each signal, include the exact
   criteria and source reference
   requirement in the prompt
4. Require the LLM to return NULL for
   unaddressed signals, not FALSE
5. Never ask the LLM to recommend scores
6. Always require document section
   references for any TRUE signal

The signal dict returned by the LLM
becomes input to the rubric engine's
scoring table. No interpretation happens
between extraction and scoring.

---

## Changelog

**v1.0 — 2026-04-22**
Initial rubric. Covers report type,
currency, auditor, opinion, TSC scope,
carve-outs, exceptions, testing
methodology, control coverage, framework
version, and evidence-to-signal mapping
for all 8 Bandit dimensions.

**Future additions:**
- Industry-specific SOC 2 variants
  (healthcare HITRUST overlay, FedRAMP
  High vs Moderate, SOC for Supply
  Chain)
- Cross-firm calibration (if two firms
  commonly produce different exception
  rates)
- Subservice organisation audit
  correlation (checking if carve-out
  sub-processors have their own SOC 2s)
