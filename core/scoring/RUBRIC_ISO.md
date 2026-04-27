# RUBRIC_ISO

Bandit's authoritative extraction and scoring
reference for ISO certificates and audit
reports. Covers ISO/IEC 27001 (information
security management), ISO/IEC 27701 (privacy
information management extension), and
ISO/IEC 42001 (AI management systems).

The LLM extracts signals. The rubric engine
scores. Two different models reading the same
ISO certificate must produce the same signal
dict.

This document governs Audit Bandit's ISO
extraction. Changes here require updating
Audit Bandit's prompt template and the rubric
engine's ISO signal table together.

---

## Why ISO certificates are different from SOC 2

Four structural differences shape how
extraction works:

### 1. Two document types per certification

ISO certifications produce two separate
documents:
- **Certificate** — a one-page document
  stating that the organisation meets the
  standard. Issued by a certification body.
- **Statement of Applicability (SoA)** /
  **Audit report** — a longer document
  detailing scope, controls, and findings.
  Often confidential, rarely shared with
  customers.

Vendors typically share only the certificate.
The certificate alone tells you currency,
scope statement, and certification body, but
not whether there were any minor non-
conformities or how the controls operate
in practice.

### 2. Three-year validity with surveillance audits

Unlike SOC 2's annual cycle, ISO certificates
have a three-year cycle:
- **Year 1** — Initial certification audit
  (full audit, certificate issued)
- **Year 2** — First surveillance audit
- **Year 3** — Second surveillance audit
- **Year 4** — Recertification audit
  (full audit, new certificate)

A certificate within the three-year window
plus annual surveillance audits is current.
Surveillance audits are smaller in scope than
the initial or recertification audit.

### 3. Certification body accreditation matters

ISO certificates are issued by certification
bodies that themselves must be accredited by
a national accreditation body:
- **ANAB** (United States) —
  ANSI National Accreditation Board
- **UKAS** (United Kingdom) —
  United Kingdom Accreditation Service
- **DAkkS** (Germany)
- **JAS-ANZ** (Australia/New Zealand)
- **A2LA** (US, secondary)

A certificate from an unaccredited
certification body is functionally worthless.
A certificate from a body accredited by the
IAF (International Accreditation Forum) is
internationally recognised.

### 4. Scope is everything

ISO certificate scope statements are short
and dense. A scope of "the design,
development, and operation of [Service X]
including supporting infrastructure and
business operations" is broad and reassuring.
A scope of "the operation of the customer
support help desk" is functionally narrow
and may not cover what the customer is
buying.

Vendors sometimes have ISO certificates
covering only one division, business unit,
or product line. The scope must match what
the customer is buying.

---

## Critical architectural rules

### Agents do not score

The LLM extracts signals. The rubric scores.

### Three certificates, separate signals

Every signal includes an explicit
certification target (27001, 27701, or
42001). Don't assume.

### Currency requires both certificate date
and surveillance audit acknowledgement

A 2-year-old certificate without a
surveillance audit reference is stale. The
extraction must surface this.

### Scope statements are extracted verbatim

Don't paraphrase or summarise. The exact
scope statement from the certificate is
captured for human review.

### Certification body accreditation is verified

When the body is named, check whether they
are accredited (a static list maintained
in `ISO_CERT_BODIES.md`).

---

## Extraction signals

### Section A — Certificate identification

**`iso_27001_present`**
- TRUE: A document explicitly identifies
  itself as an ISO/IEC 27001 certificate or
  audit report. Look for "ISO/IEC 27001",
  "ISO 27001:2022", "ISO 27001:2013", or
  similar.
- FALSE: Document is not ISO 27001.
- NULL: Not applicable.

**`iso_27701_present`**
- TRUE: Document is an ISO/IEC 27701
  certificate or report. Look for
  "ISO/IEC 27701", "ISO 27701:2019".
- FALSE: Not present.
- NULL: Not applicable.

**`iso_42001_present`**
- TRUE: Document is an ISO/IEC 42001
  certificate or report. Look for
  "ISO/IEC 42001", "ISO 42001:2023".
- FALSE: Not present.
- NULL: Not applicable.

**`iso_27001_version`**
- VALUE: The version year of the standard
  the certificate references. One of:
  - "2022" — current version
  - "2013" — superseded version (still in
    transition until October 2025)
  - "older" — pre-2013, severely outdated
- NULL: Version not stated.
- Notes: Vendors transitioning from 2013 to
  2022 should be noted but not penalised
  during the transition window.

**`iso_27001_2013_post_transition`**
- TRUE: Certificate is on ISO 27001:2013
  AND the issue date or surveillance audit
  date is after 31 October 2025 (transition
  deadline).
- FALSE: Certificate is on 2022 OR pre-
  transition.
- NULL: Not applicable.
- Notes: After 31 October 2025, all valid
  certificates must be on the 2022 version.
  A 2013 certificate dated after this is
  effectively expired.

### Section B — Certificate currency

**`iso_27001_issue_date`**
- VALUE: YYYY-MM-DD format. The date the
  certificate was originally issued or
  most recently recertified.
- NULL: Not stated.
- Required reference: Certificate face.

**`iso_27001_expiry_date`**
- VALUE: YYYY-MM-DD format. The date the
  certificate expires (typically 3 years
  from issuance).
- NULL: Not stated.
- Required reference: Certificate face.

**`iso_27001_certificate_age_months`**
- VALUE: Months between certificate issue
  date and today.
- NULL: If issue date unknown.

**`iso_27001_surveillance_audit_referenced`**
- TRUE: Document references a recent
  surveillance audit (annual). Look for
  "surveillance audit", "annual audit",
  "ongoing audit" with a date.
- FALSE: No surveillance audit referenced.
- NULL: Not applicable.

**`iso_27001_surveillance_audit_date`**
- VALUE: YYYY-MM-DD of most recent
  surveillance audit, if mentioned.
- NULL: If not stated.

**`iso_27001_audit_type`**
- VALUE: One of:
  - "initial" — first certification audit
  - "surveillance" — annual surveillance
  - "recertification" — full audit after
    3 years
- NULL: Not stated.

**`iso_27001_currency_status`**
- DERIVED — calculated by the rubric, not
  extracted by the LLM. See "Derived
  values" below.

(Same set of signals exists for 27701 and
42001. Replace `iso_27001_` with
`iso_27701_` or `iso_42001_` and apply
the same rules.)

### Section C — Certification body identification

**`iso_27001_certification_body_name`**
- VALUE: The exact name of the certification
  body that issued the certificate.
- NULL: If not stated.
- Required reference: Certificate face.
- Examples: "BSI Group", "DNV", "TÜV
  Rheinland", "Bureau Veritas",
  "SGS", "Schellman & Co. (ISO division)",
  "A-LIGN ISO Services", "Coalfire ISO".

**`iso_27001_certification_body_accredited`**
- TRUE: The certification body is on the
  recognised accredited bodies list in
  `ISO_CERT_BODIES.md`.
- FALSE: Body not on the list, or no body
  named, or body explicitly identified as
  unaccredited.
- NULL: Body name not extracted.
- Notes: A certificate from an unaccredited
  body provides minimal assurance.

**`iso_27001_accreditation_number_stated`**
- TRUE: The certificate or document states
  the accreditation number issued by the
  national accreditation body (e.g., ANAB
  Cert # XXXX, UKAS # XXXX).
- FALSE: No accreditation number stated.
- NULL: Cannot determine.

**`iso_27001_iaf_recognition`**
- TRUE: The certification body is part of
  the IAF (International Accreditation
  Forum) MLA (Multilateral Recognition
  Arrangement). Determined by the
  recognised list.
- FALSE: Not IAF-recognised.
- NULL: Cannot determine.

(Repeat for 27701 and 42001.)

### Section D — Scope of certification

**`iso_27001_scope_statement`**
- VALUE: The exact verbatim scope statement
  from the certificate. Copy as-is, do not
  paraphrase.
- NULL: If no scope statement found.
- Required reference: Scope or
  "Certification covers" section.

**`iso_27001_scope_includes_primary_service`**
- TRUE: The scope statement explicitly
  covers the vendor's primary
  customer-facing service or product. This
  is determined by comparing the scope
  against intake context.
- FALSE: The scope explicitly excludes the
  primary service or covers only ancillary
  functions.
- NULL: Cannot determine without intake
  context.

**`iso_27001_scope_explicit_exclusions`**
- VALUE: List of products, services, or
  business units explicitly excluded from
  scope.
- NULL: If no exclusions stated.

**`iso_27001_scope_geographic_coverage`**
- VALUE: List of geographic regions, data
  centres, or jurisdictions explicitly in
  scope.
- NULL: If not specified.

**`iso_27001_scope_business_unit_only`**
- TRUE: The scope is limited to a specific
  business unit, division, or subsidiary
  rather than the whole organisation.
- FALSE: Scope is organisation-wide.
- NULL: Cannot determine.
- Notes: A subsidiary-only certificate may
  not cover the customer-facing service.

**`iso_27001_scope_narrowing_concern`**
- TRUE: The scope appears unusually narrow.
  Mark TRUE if:
  - Scope covers only specific data centres
    while service operates from many
  - Scope covers only specific functions
    (e.g., "help desk operations") while
    customer is buying broader service
  - Scope covers a subsidiary while contract
    is with parent
- FALSE: Scope appears comprehensive for
  the service being evaluated.
- NULL: Cannot determine without intake
  context.

(Repeat for 27701 and 42001.)

### Section E — Statement of Applicability and controls

These signals apply when an SoA or audit
report is provided in addition to the
certificate.

**`iso_27001_soa_provided`**
- TRUE: A Statement of Applicability is
  included with the certificate.
- FALSE: Only the certificate is provided.
- NULL: Not applicable.

**`iso_27001_controls_excluded`**
- VALUE: List of Annex A controls explicitly
  excluded from the SoA, if SoA is provided.
- NULL: If no SoA or no exclusions.
- Notes: ISO 27001 allows controls to be
  excluded with justification. Excessive
  exclusions are a concern.

**`iso_27001_excluded_controls_count`**
- VALUE: Number of Annex A controls
  excluded from the SoA.
- NULL: If no SoA.
- Notes: ISO 27001:2022 has 93 controls.
  Exclusions of 10+ controls warrant
  scrutiny.

**`iso_27001_excluded_controls_justified`**
- TRUE: Each exclusion has a documented
  justification in the SoA.
- FALSE: Exclusions lack justifications.
- NULL: No SoA provided.

**`iso_27001_audit_findings_stated`**
- TRUE: The audit report contains stated
  findings (minor non-conformities, major
  non-conformities, observations, or
  opportunities for improvement).
- FALSE: No findings reported.
- NULL: No audit report provided.

**`iso_27001_major_nonconformities`**
- VALUE: Number of major non-conformities,
  if reported. ISO certificates cannot be
  issued or maintained with open major
  non-conformities — they must be resolved
  before certification.
- NULL: If no audit report or not reported.
- Notes: Major non-conformities at the
  time of audit followed by closure is
  positive (the system caught and fixed
  problems). Open major non-conformities
  would mean no valid certificate.

**`iso_27001_minor_nonconformities`**
- VALUE: Number of minor non-conformities.
- NULL: If not reported.

**`iso_27001_observations`**
- VALUE: Number of observations or
  opportunities for improvement.
- NULL: If not reported.

(Repeat for 27701 and 42001.)

### Section F — Specific control coverage (when SoA available)

**`iso_27001_data_protection_controls_implemented`**
- TRUE: Annex A controls related to data
  protection (A.5.34, A.8.10–8.12) are
  implemented per the SoA.
- FALSE: Controls excluded or not
  implemented.
- NULL: No SoA.

**`iso_27001_supplier_controls_implemented`**
- TRUE: Supplier relationship controls
  (A.5.19–5.22) are implemented per the
  SoA.
- FALSE: Excluded or not implemented.
- NULL: No SoA.

**`iso_27001_incident_management_controls_implemented`**
- TRUE: Information security incident
  management controls (A.5.24–5.28) are
  implemented per the SoA.
- FALSE: Excluded or not implemented.
- NULL: No SoA.

**`iso_27001_compliance_controls_implemented`**
- TRUE: Compliance controls (A.5.31–5.36)
  are implemented per the SoA.
- FALSE: Excluded or not implemented.
- NULL: No SoA.

### Section G — ISO 27701 specific signals

ISO 27701 extends ISO 27001 with privacy-
specific controls.

**`iso_27701_extends_27001`**
- TRUE: The 27701 certificate or report
  references the underlying 27001 ISMS.
- FALSE: 27701 is claimed without underlying
  27001 certification.
- NULL: Not applicable.
- Notes: 27701 cannot be obtained without
  27001. A standalone 27701 claim is
  invalid.

**`iso_27701_role_pii_controller`**
- TRUE: The vendor is certified as a PII
  controller under 27701.
- FALSE: Not certified as controller.
- NULL: Not addressed.

**`iso_27701_role_pii_processor`**
- TRUE: The vendor is certified as a PII
  processor under 27701.
- FALSE: Not certified as processor.
- NULL: Not addressed.

**`iso_27701_gdpr_mapped`**
- TRUE: The certification explicitly maps
  controls to GDPR requirements (Annex D
  of 27701).
- FALSE: GDPR mapping not addressed.
- NULL: No SoA.

**`iso_27701_ccpa_mapped`**
- TRUE: The certification maps controls to
  CCPA or other US privacy frameworks.
- FALSE: Not addressed.
- NULL: No SoA.

### Section H — ISO 42001 specific signals

ISO 42001 (AI Management Systems) is the
newest standard.

**`iso_42001_aims_implemented`**
- TRUE: The certificate confirms an AI
  Management System (AIMS) is implemented.
- FALSE: Not confirmed.
- NULL: Not applicable.

**`iso_42001_ai_risk_assessment_documented`**
- TRUE: The SoA or audit report references
  AI-specific risk assessments.
- FALSE: Not referenced.
- NULL: No SoA.

**`iso_42001_ai_lifecycle_controls`**
- TRUE: AI lifecycle controls (data,
  development, deployment, monitoring) are
  documented.
- FALSE: Not documented.
- NULL: No SoA.

**`iso_42001_data_governance_for_ai`**
- TRUE: Data governance specifically for
  AI training and inference is addressed.
- FALSE: Not addressed.
- NULL: No SoA.

**`iso_42001_third_party_ai_governance`**
- TRUE: The AIMS addresses governance of
  third-party AI services used by the
  organisation.
- FALSE: Not addressed.
- NULL: No SoA.

### Section I — Cross-certificate consistency

**`iso_certificates_organisation_consistent`**
- TRUE: When multiple ISO certificates are
  provided (e.g., 27001 + 27701), they all
  cover the same legal entity.
- FALSE: Certificates cover different
  legal entities (e.g., 27001 covers the
  parent, 27701 covers a subsidiary).
- NULL: Only one certificate provided.

**`iso_certificates_scope_aligned`**
- TRUE: When multiple ISO certificates are
  provided, their scope statements align
  (cover the same services and locations).
- FALSE: Scopes differ in ways that
  matter.
- NULL: Only one certificate.

### Section J — Red flags and contradictions

**`iso_certificate_expired`**
- TRUE: The expiry date has passed AND
  no recertification is referenced.
- FALSE: Certificate is current.
- NULL: Cannot determine.

**`iso_certificate_no_surveillance_audit`**
- TRUE: The certificate is more than 12
  months old AND no surveillance audit
  is referenced.
- FALSE: Surveillance audit referenced
  or certificate less than 12 months old.
- NULL: Issue date unknown.

**`iso_certification_body_unaccredited`**
- TRUE: The certification body is named
  but is not on the recognised
  accreditation list.
- FALSE: Body is recognised.
- NULL: Body not named.

**`iso_27701_without_27001`**
- TRUE: ISO 27701 is claimed without
  underlying ISO 27001 certification.
- FALSE: Both present or 27701 not
  claimed.

**`iso_scope_excludes_customer_service`**
- TRUE: The certificate scope explicitly
  excludes the customer-facing service
  the customer is buying.
- FALSE: Scope includes the service.
- NULL: Cannot determine without intake
  context.

**`iso_certificate_image_only`**
- TRUE: The provided document is only an
  image of the certificate (no machine-
  readable text), making verification
  difficult.
- FALSE: Document is text-extractable.
- NULL: Not applicable.
- Notes: Image-only certificates are
  legitimate but harder to verify. Flag
  for human review.

---

## Derived values

Calculated by the rubric engine, not the
LLM.

**`iso_27001_currency_status`**
Derived from `iso_27001_issue_date`,
`iso_27001_expiry_date`, and
`iso_27001_surveillance_audit_referenced`:

- "current_recent" — Issued or recertified
  within last 18 months
- "current_with_surveillance" —
  Issued 18 months to 3 years ago AND
  surveillance audit referenced within
  last 12 months
- "current_no_surveillance" —
  Issued 18 months to 3 years ago AND
  no surveillance audit reference (concern)
- "expiring_soon" — Within 6 months of
  expiry
- "expired" — Past expiry date with no
  recertification reference
- "unknown" — Insufficient date
  information

(Repeat logic for 27701 and 42001.)

**`iso_27001_overall_assurance`**
Composite derived value:
- "high" — Current, accredited body, broad
  scope, no exclusions, surveillance
  audits referenced
- "moderate" — Current, accredited body,
  some scope or control exclusions
- "low" — Stale, narrow scope, or
  unaccredited body
- "minimal" — Expired, unaccredited, or
  scope excludes customer service
- "none" — No 27001 certificate

---

## Evidence-to-signal mapping

Maps ISO signals to Bandit's dimensions.

### D2 Sub-processor Management

**Positive modifiers:**
- `iso_27001_supplier_controls_implemented
  = TRUE` (when SoA available): +0.3
- `iso_27001_present = TRUE` AND
  `iso_27001_currency_status = "current"`:
  +0.2

**No negative modifiers** unless certificate
expired without renewal.

### D5 Breach Notification

**Positive modifiers:**
- `iso_27001_incident_management_controls_
  implemented = TRUE` (when SoA available):
  +0.4
- `iso_27001_present = TRUE` AND current:
  +0.2

### D7 Retention and Deletion

**Positive modifiers:**
- `iso_27001_data_protection_controls_
  implemented = TRUE`: +0.3
- `iso_27701_present = TRUE` AND current:
  +0.4

### D8 DPA Completeness / Independent
verification

**Strong positives:**
- `iso_27001_present = TRUE` AND
  `iso_27001_currency_status =
  "current_recent"` AND
  `iso_27001_certification_body_accredited
  = TRUE` AND
  `iso_27001_scope_includes_primary_service
  = TRUE`: +0.4

- `iso_27701_present = TRUE` AND
  `iso_27701_extends_27001 = TRUE` AND
  current AND accredited: +0.5

- `iso_42001_present = TRUE` AND current
  AND accredited: +0.3 (also affects D6)

**Moderate positives:**
- `iso_27001_audit_findings_stated = TRUE`
  AND `iso_27001_major_nonconformities =
  0`: +0.2 (transparent reporting,
  problems addressed)

**Negative modifiers:**
- `iso_certification_body_unaccredited =
  TRUE`: certificate is ignored entirely,
  no modifier applied
- `iso_27701_without_27001 = TRUE`:
  certificate is invalid, ignored
- `iso_certificate_expired = TRUE`:
  ignored
- `iso_27001_2013_post_transition = TRUE`:
  ignored (effectively expired post-
  October 2025)
- `iso_scope_excludes_customer_service =
  TRUE`: modifier reduced by 75%
- `iso_27001_scope_narrowing_concern =
  TRUE`: modifier reduced by 50%

### D6 AI/ML Data Usage

**Positive modifiers:**
- `iso_42001_present = TRUE` AND current:
  +0.4
- `iso_42001_ai_risk_assessment_documented
  = TRUE`: +0.2
- `iso_42001_data_governance_for_ai =
  TRUE`: +0.2

(See RUBRIC_AI_POLICY.md for D6 framework
modifiers.)

---

## Red flags that generate explicit findings

1. **Expired certificate** — Past expiry
   date with no recertification reference.

2. **Stale certificate without surveillance
   audit** — More than 12 months old with
   no surveillance audit reference.

3. **Unaccredited certification body** —
   Body named but not on recognised list.

4. **27701 without 27001** — Privacy
   extension claimed without the underlying
   ISMS certificate.

5. **Scope excludes customer service** —
   Certificate scope does not cover what
   the customer is buying.

6. **Scope narrowed to subsidiary** —
   Certificate covers a business unit or
   subsidiary while the contract is with
   the parent.

7. **2013 version after transition** —
   ISO 27001:2013 certificate dated after
   31 October 2025 (effectively expired).

8. **Cross-certificate inconsistency** —
   Multiple ISO certificates cover
   different legal entities or different
   scopes.

9. **Image-only certificate** — Only a
   scanned image provided, making
   verification difficult.

10. **Recent certification without
    surveillance** — Certificate from a
    new certification body with no track
    record visible.

---

## Absence vs denial tracking

Same as RUBRIC_SOC2 and RUBRIC_AI_POLICY:
- TRUE: Explicitly stated
- FALSE: Explicitly contradicted
- NULL: Not addressed

For ISO certificates, NULL is common because
many fields rely on the SoA being provided.
A vendor that shares only the certificate
will yield many NULL signals — that's
expected and not a negative.

The distinction matters most for scope
signals. A scope statement that's missing
is different from a scope statement that
explicitly excludes customer-facing services.

---

## Implementation notes for Audit Bandit

When rebuilding Audit Bandit's prompt to
include ISO extraction:

1. The prompt must handle multiple ISO
   certificates simultaneously. A vendor
   may provide 27001 + 27701 + 42001 in
   one bundle or separately.

2. For each certificate type detected,
   apply the full signal set with
   appropriate prefix (`iso_27001_`,
   `iso_27701_`, `iso_42001_`).

3. The certification body recognition
   check requires loading
   `ISO_CERT_BODIES.md` content into the
   prompt context.

4. The scope evaluation requires the
   intake context — without it, the
   `iso_27001_scope_includes_primary_service`
   signal cannot be set. Pass intake
   context to the agent.

5. For image-only certificates, set
   `iso_certificate_image_only = TRUE`
   and extract what fields are
   accessible. Do not refuse extraction
   — partial signals are still useful.

6. Cross-certificate consistency checks
   only run when multiple certificates
   are present.

---

## Changelog

**v1.0 — 2026-04-22**
Initial ISO rubric. Covers ISO 27001,
27701, and 42001 signal extraction across
certificate identification, currency,
certification body, scope, controls,
cross-certificate consistency, and red
flags. Approximately 80 signals total
(divided across the three certifications).

**Future additions:**
- ISO 27017 (cloud security) and 27018
  (cloud privacy) handling
- Industry-specific extensions (HIPAA-
  aligned 27001, PCI-related 27001)
- TISAX (German automotive) handling
- C5 (German cloud) handling
- Country-specific equivalents (China
  GB/T, Russia GOST)
