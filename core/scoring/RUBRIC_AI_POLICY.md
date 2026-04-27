# RUBRIC_AI_POLICY

Bandit's authoritative extraction and scoring
reference for AI policies, model cards, DPA
AI clauses, and AI transparency statements.
Every signal AI Bandit extracts from AI-
related documents must be defined here with
explicit yes/no criteria.

The LLM extracts signals. The rubric engine
scores. Two different models reading the same
AI policy must produce the same signal dict —
otherwise the scoring is not deterministic.

This document governs AI Bandit's extraction.
Changes here require updating AI Bandit's
prompt template and the rubric engine's D6
signal table together.

---

## Why AI policies are different from other evidence

Four structural differences matter when
designing extraction rules for AI policies:

### 1. The language is newer and less standardised

Unlike SOC 2 which has a 20+ year framework
history, AI policies emerged rapidly after
2022. Terminology varies wildly between
vendors. "Model training" means different
things at different companies. "AI features"
may or may not include generative AI. An
extraction rubric for AI policies has to
work across inconsistent vocabulary.

### 2. Vendors often conflate three distinct uses

When a vendor says "we use your data for AI,"
they could mean:
- **Training** — customer data becomes part
  of the model's weights
- **Fine-tuning** — customer data adjusts a
  base model for that customer's context
- **Inference/runtime** — customer data is
  sent to a model to generate output, but
  not stored or used to update the model
- **Model improvement** — aggregated or
  anonymised customer data informs future
  model development

These four have very different privacy
implications and the extraction must
distinguish them. A vendor that says "we
don't train on your data" but uses it for
"model improvement" is making a meaningful
distinction that matters for risk.

### 3. Opt-out is easier to claim than to deliver

"Opt-out available" can mean:
- A self-service toggle in the product
- A form you submit
- An email to support
- A contractual request during renewal
- Only available to enterprise customers
- Only available at the account level, not
  the data level

The accessibility of opt-out matters more
than its existence. An opt-out that requires
a legal review and DPA amendment is
functionally different from a checkbox in
settings.

### 4. Retroactive vs forward-looking

Opt-out typically only applies going forward.
Data already ingested into training sets,
fine-tuned model weights, or inference logs
may be impossible to remove. An evaluation
rubric must surface this because it's rarely
explicitly addressed in AI policies.

---

## Critical architectural rules

### Agents do not score

The LLM extracts yes/no signals. The rubric
engine scores deterministically. An AI Bandit
that recommends a D6 score fails the
architectural principle because two different
models will produce different scores.

### Training and inference are always distinguished

Every signal that relates to customer data
use must specify whether it addresses
training, fine-tuning, inference, or model
improvement. A single "used_for_ai" signal is
not acceptable.

### Opt-out accessibility is graded

Binary "opt-out exists" is insufficient.
Extraction must capture the accessibility
tier: self-service, form-based, support
request, or contract negotiation.

### EU AI Act tier is vendor-claimed

The EU AI Act categorises AI systems into
risk tiers (minimal, limited, high, or
unacceptable). Extraction captures what the
vendor claims about their tier. Bandit does
not independently classify — that requires
human judgement. Flag when the claimed tier
looks inconsistent with the described use
case.

### Absence of AI disclosure is itself a signal

A vendor that uses AI in their product but
doesn't publish an AI policy is a concern.
Silence is not neutral in this domain.

---

## Extraction signals

Every signal has three mandatory properties:

- **Exact criteria** — what must appear in
  the document for the signal to be TRUE
- **False vs null distinction** — when FALSE
  means "explicitly not" vs when it means
  "not addressed"
- **Source reference** — document section
  the LLM must cite if marking TRUE

### Section A — AI presence and scope

**`is_ai_vendor`**
- TRUE: The document explicitly states that
  the vendor uses artificial intelligence,
  machine learning, generative AI, large
  language models, or similar technology in
  their product or service.
- FALSE: The document explicitly states no
  AI is used, OR the document is clearly
  not AI-related (e.g., a general privacy
  policy with no AI section).
- NULL: AI is not mentioned either way.
- Required reference: Section heading or
  paragraph where AI is described.

**`ai_in_customer_facing_service`**
- TRUE: The document describes AI features
  that customers directly interact with
  (chatbots, assistants, recommendations,
  content generation, etc.).
- FALSE: AI is used only internally (for
  the vendor's operations, not in customer-
  facing features).
- NULL: Not specified.

**`ai_in_backend_processing`**
- TRUE: The document describes AI used for
  backend processing that affects customer
  data (fraud detection, anomaly detection,
  automated decisions, etc.).
- FALSE: No backend AI processing described.
- NULL: Not specified.

**`generative_ai_present`**
- TRUE: The document specifically mentions
  generative AI, large language models, text
  generation, image generation, or similar
  generative capabilities.
- FALSE: AI is used but explicitly stated to
  be non-generative (classification,
  prediction, recommendation only).
- NULL: Not specified.

**`third_party_ai_used`**
- TRUE: The document states the vendor uses
  third-party AI services (OpenAI, Anthropic,
  Google, AWS Bedrock, Azure OpenAI, etc.)
  as part of their offering.
- FALSE: The document states only
  proprietary models are used.
- NULL: Not specified.

**`third_party_ai_providers_listed`**
- VALUE: List of third-party AI providers
  explicitly named in the document.
- NULL: If third_party_ai_used is FALSE or
  NULL, or if no providers are named.
- Example: ["OpenAI", "Anthropic", "AWS
  Bedrock"]

### Section B — Training use of customer data

**`trains_on_customer_data`**
- TRUE: The document explicitly states that
  customer data is used to train AI or ML
  models. "Training" means the data
  influences the model's weights.
- FALSE: The document explicitly states
  customer data is NOT used for training.
  Look for "we do not train our models on
  your data" or equivalent.
- NULL: Not addressed.
- Required reference: Section discussing
  data use for AI.

**`fine_tunes_on_customer_data`**
- TRUE: The document explicitly states
  customer data is used for fine-tuning
  models (either per-customer or general).
- FALSE: Explicitly stated no fine-tuning
  on customer data.
- NULL: Not addressed.
- Notes: Fine-tuning is weaker than
  training but stronger than inference-only.

**`uses_customer_data_for_inference`**
- TRUE: The document states customer data
  is sent to AI models for inference (the
  data is processed to generate output but
  not used to update the model).
- FALSE: Explicitly stated no inference use.
- NULL: Not addressed.
- Notes: Inference-only use is typical for
  vendors using third-party AI like OpenAI
  or Anthropic.

**`inference_data_retained`**
- TRUE: The document states that data sent
  for inference is retained (for model
  improvement, debugging, logs, etc.).
- FALSE: Explicitly stated inference data
  is not retained.
- NULL: Not addressed.
- Notes: A vendor that says "we don't train
  on your data" but retains inference data
  is making a distinction worth surfacing.

**`uses_customer_data_for_model_improvement`**
- TRUE: The document states customer data
  (aggregated, anonymised, or otherwise) is
  used for model improvement, service
  improvement, or research.
- FALSE: Explicitly stated not used for
  improvement.
- NULL: Not addressed.
- Notes: "Model improvement" is a common
  middle ground — vendors claim not to
  train but still use data to evaluate and
  iterate.

**`customer_data_segregated_from_training`**
- TRUE: The document explicitly states
  customer data is kept separate from
  training data pools, either through
  technical segregation or contractual
  commitment.
- FALSE: No segregation stated.
- NULL: Not addressed.
- Notes: A strong positive signal. Look for
  phrases like "your data is never added to
  our training pool" or "customer data is
  isolated from our model development."

### Section C — Opt-out mechanics

**`opt_out_available`**
- TRUE: The document describes any method
  for opting out of customer data use for
  AI purposes (training, fine-tuning, or
  improvement).
- FALSE: The document states no opt-out is
  available, OR the document describes
  mandatory AI processing with no exception.
- NULL: Opt-out is not addressed.

**`opt_out_accessibility`**
- VALUE: The accessibility tier of the
  opt-out mechanism. One of:
  - "self_service" — toggle, checkbox, or
    setting available in the product itself
  - "form_based" — requires filling out an
    online form outside the product
  - "support_request" — requires contacting
    support via email or ticket
  - "contract_negotiation" — requires
    working with sales or legal, typically
    only available to enterprise customers
  - "none" — no opt-out available
- NULL: If opt-out is not described or
  accessibility cannot be determined.
- Notes: Lower accessibility = higher
  friction = weaker privacy protection.

**`opt_out_prominent`**
- TRUE: The opt-out is described prominently
  (in the main body of the AI or privacy
  policy, not buried in footnotes or FAQ).
- FALSE: The opt-out is mentioned but not
  prominently.
- NULL: No opt-out described.

**`opt_out_retroactive`**
- TRUE: The document explicitly states that
  opt-out applies retroactively (data
  already used will be removed from
  training sets or model outputs).
- FALSE: The document explicitly states
  opt-out is forward-looking only.
- NULL: Not addressed.
- Notes: A major gap if forward-only without
  acknowledgement.

**`opt_in_required`**
- TRUE: The document states that customer
  data is NOT used for AI training/
  improvement unless the customer
  affirmatively opts in.
- FALSE: AI use is the default; opt-out is
  the only control.
- NULL: Not addressed.
- Notes: Opt-in is materially stronger than
  opt-out. Rare in current practice.

**`opt_out_granularity`**
- VALUE: The granularity at which opt-out
  applies. One of:
  - "account_level" — opt-out applies to
    the entire account
  - "data_type_level" — opt-out can apply
    to specific data types
  - "field_level" — opt-out can apply at
    the field or record level
  - "none" — no opt-out available
- NULL: If not addressed.

### Section D — Legal basis and EU AI Act

**`legal_basis_stated`**
- TRUE: The document states a legal basis
  for AI processing under GDPR or similar
  frameworks (consent, legitimate interest,
  contract, legal obligation, etc.).
- FALSE: No legal basis is provided.
- NULL: Not addressed.

**`legal_basis_description`**
- VALUE: Exact legal basis stated (e.g.,
  "consent under Art. 6(1)(a)",
  "legitimate interests under Art. 6(1)(f)",
  "contractual necessity under Art. 6(1)(b)").
- NULL: If legal_basis_stated is FALSE or
  NULL.
- Notes: "Legitimate interests" alone without
  balancing test is weak.

**`legitimate_interests_balancing_performed`**
- TRUE: The document references a legitimate
  interests assessment (LIA) or balancing
  test being performed.
- FALSE: Legitimate interests claimed
  without evidence of balancing.
- NULL: Not relevant (different legal basis)
  or not addressed.

**`special_category_data_addressed`**
- TRUE: The document addresses GDPR Art. 9
  special category data (health, biometric,
  political opinion, etc.) in the context
  of AI processing.
- FALSE: Special category data not
  addressed despite being relevant.
- NULL: Not relevant (no special category
  data processed).

**`eu_ai_act_addressed`**
- TRUE: The document explicitly references
  the EU AI Act, Regulation (EU) 2024/1689,
  or specific AI Act provisions.
- FALSE: No EU AI Act reference despite
  serving EU customers.
- NULL: EU AI Act not relevant or not
  addressed.

**`eu_ai_act_claimed_tier`**
- VALUE: The risk tier the vendor claims
  under the EU AI Act. One of:
  - "minimal" — no specific AI Act
    obligations
  - "limited" — transparency obligations
    apply (e.g., chatbots must disclose)
  - "high" — high-risk AI system, full
    compliance regime required
  - "unacceptable" — prohibited (should
    never be claimed)
  - "not_stated" — vendor has not stated
    a tier
- NULL: If eu_ai_act_addressed is FALSE
  or NULL.

**`eu_ai_act_tier_plausible`**
- TRUE: The claimed tier is consistent with
  the described use case. Mark TRUE only
  if the tier claim matches what AI systems
  of this type would reasonably be.
- FALSE: The claimed tier appears
  implausible. For example, a biometric
  identification system claiming "minimal"
  tier, or an HR decision-making system
  claiming "limited" when it's likely "high"
  risk under Annex III.
- NULL: Not enough information to judge.
- Notes: This is the one place the LLM
  exercises judgement. Flag implausibility
  for human review, not as a score
  deduction.

### Section E — Data governance and retention

**`training_data_retention_stated`**
- TRUE: The document specifies how long
  customer data is retained when used for
  AI training, fine-tuning, or improvement.
- FALSE: No retention specified.
- NULL: Training not used.

**`training_data_retention_period`**
- VALUE: The stated retention period (e.g.,
  "30 days", "indefinitely until opt-out",
  "for the life of the service").
- NULL: If not stated.

**`inference_logs_retention_stated`**
- TRUE: The document specifies how long
  inference logs are retained.
- FALSE: Not specified.
- NULL: Not addressed.

**`data_used_in_training_segregated_from_weights`**
- TRUE: The document addresses whether data
  used in training can be removed from
  model weights (acknowledging the technical
  challenge).
- FALSE: No acknowledgement of this issue.
- NULL: Not relevant.
- Notes: Honest vendors acknowledge that
  once data is in model weights, removal is
  essentially impossible. Vendors that
  promise removal from weights are either
  using simple models or making unsupportable
  claims.

**`model_deletion_on_contract_termination`**
- TRUE: The document commits to deleting
  any models fine-tuned on customer data
  upon contract termination.
- FALSE: No such commitment.
- NULL: Not relevant (no fine-tuning).

**`algorithmic_disgorgement_addressed`**
- TRUE: The document addresses the
  possibility of algorithmic disgorgement
  (FTC precedent for destroying models
  built on improperly obtained data).
- FALSE: Not addressed despite relevance.
- NULL: Not addressed.
- Notes: Rare but a strong positive signal
  for sophisticated AI governance.

### Section F — Fairness, bias, and oversight

**`bias_mitigation_documented`**
- TRUE: The document describes specific
  bias testing or mitigation procedures.
- FALSE: No bias documentation.
- NULL: Not addressed.

**`fairness_evaluation_documented`**
- TRUE: The document describes fairness
  evaluation metrics or procedures.
- FALSE: Not documented.
- NULL: Not addressed.

**`human_in_the_loop_described`**
- TRUE: The document describes human
  oversight or human-in-the-loop processes
  for AI decisions.
- FALSE: Not described.
- NULL: Not relevant (automated decisions
  don't affect customers in material ways).

**`ai_decisions_contestable`**
- TRUE: The document describes a mechanism
  for customers or data subjects to contest
  AI-driven decisions (GDPR Art. 22 right).
- FALSE: Not described.
- NULL: No automated decisions made.

**`automated_decision_making_disclosed`**
- TRUE: The document identifies specific
  decisions that are fully automated versus
  those with human involvement.
- FALSE: Not disclosed.
- NULL: No automated decisions.

### Section G — Transparency documentation

**`model_card_available`**
- TRUE: The document references or includes
  a model card describing the specific AI
  models used.
- FALSE: Not available.
- NULL: Not relevant (no proprietary models).

**`training_data_sources_disclosed`**
- TRUE: The document discloses where
  training data came from (proprietary
  collection, public datasets, licensed
  data, etc.).
- FALSE: Training data sources not
  disclosed.
- NULL: Not relevant (no proprietary
  training).

**`training_data_provenance_documented`**
- TRUE: The document documents the
  provenance chain of training data,
  including consent basis for any personal
  data in training sets.
- FALSE: No provenance documentation.
- NULL: Not relevant.

**`model_updates_disclosed`**
- TRUE: The document states that material
  model updates will be disclosed to
  customers.
- FALSE: No update disclosure commitment.
- NULL: Not relevant.

**`ai_transparency_report_available`**
- TRUE: The document references an AI
  transparency report or annual AI
  accountability report.
- FALSE: Not available.
- NULL: Not addressed.

### Section H — Contractual AI commitments (DPA)

These signals are specifically extracted
from the DPA when AI Bandit reads it.
Note: Legal Bandit also reads the DPA.
AI Bandit's role is specifically for D6
signals. Do not duplicate Legal Bandit's
general DPA analysis.

**`dpa_has_ai_clause`**
- TRUE: The DPA contains a section
  specifically addressing AI or ML
  processing.
- FALSE: DPA does not address AI.
- NULL: No DPA provided.

**`dpa_prohibits_training_on_customer_data`**
- TRUE: The DPA includes a clause
  prohibiting the use of customer data
  for training or improving AI models
  without further written agreement.
- FALSE: DPA is silent or explicitly
  permits training use.
- NULL: No DPA.

**`dpa_requires_consent_for_ai_processing`**
- TRUE: The DPA requires customer consent
  before any AI processing of customer
  data.
- FALSE: AI processing is permitted under
  the general terms without additional
  consent.
- NULL: No DPA.

**`dpa_addresses_ai_subprocessors`**
- TRUE: The DPA addresses AI-specific sub-
  processors (e.g., OpenAI, Anthropic)
  separately from general sub-processors.
- FALSE: AI sub-processors are not
  separately addressed.
- NULL: No DPA or no AI sub-processors.

**`dpa_has_ai_audit_rights`**
- TRUE: The DPA grants customer audit
  rights specifically over AI processing.
- FALSE: No AI-specific audit rights.
- NULL: No DPA.

### Section I — Compliance certifications

**`iso_42001_certified`**
- TRUE: The document claims ISO 42001
  (AI Management Systems) certification.
- FALSE: Not claimed.
- NULL: Not addressed.
- Notes: Cross-referenced with Audit
  Bandit's ISO 42001 extraction from
  certificates.

**`nist_ai_rmf_referenced`**
- TRUE: The document references NIST AI
  Risk Management Framework (AI RMF) as
  a governance standard.
- FALSE: Not referenced.
- NULL: Not addressed.

**`iso_23894_referenced`**
- TRUE: The document references ISO/IEC
  23894 (AI risk management guidance).
- FALSE: Not referenced.
- NULL: Not addressed.

### Section J — AI contradictions and red flags

**`training_claim_contradicts_inference_retention`**
- TRUE: The document claims "we don't
  train on your data" but also states
  that inference data is retained for
  extended periods or used for
  improvement.
- FALSE: No such contradiction.
- NULL: Not applicable.
- Notes: Common vendor pattern that
  deserves explicit flagging.

**`opt_out_denied_for_ai_features`**
- TRUE: The document states that customers
  cannot opt out of AI processing if they
  use AI features of the product.
- FALSE: Opt-out is available even for AI
  features.
- NULL: Not addressed.

**`ai_use_without_disclosure`**
- TRUE: Through external knowledge (product
  descriptions, marketing), the vendor
  appears to use AI but the provided
  documents do not disclose AI use.
- FALSE: AI use is disclosed.
- NULL: Cannot determine.
- Notes: This is the one signal the LLM
  may exercise judgement on. Flag for
  human review.

**`customer_data_used_for_foundation_model_training`**
- TRUE: The document states customer data
  is used to train foundation models (not
  just fine-tuning).
- FALSE: Foundation model training on
  customer data is excluded.
- NULL: Not addressed.
- Notes: Materially different from fine-
  tuning. Foundation model training is
  typically irreversible.

---

## Derived values

Computed by the rubric engine from raw
extraction, not by the LLM.

**`ai_risk_level`**
Derived from combinations of signals:
- "minimal" — not AI vendor OR AI vendor
  with opt-in required
- "low" — AI vendor with self-service
  opt-out and no training on customer data
- "moderate" — AI vendor with form-based
  opt-out, or inference retention
- "elevated" — AI vendor with training on
  customer data, opt-out available but
  friction
- "high" — AI vendor with training on
  customer data, no clear opt-out, no
  legal basis
- "critical" — AI vendor with training,
  no opt-out, no legal basis, uses in
  ways claimed tier doesn't match

**`ai_governance_maturity`**
Derived score based on:
- Model card availability
- Training data provenance documentation
- Bias and fairness testing
- Human oversight documentation
- Contestability mechanism
- ISO 42001 or equivalent certification

Range: 0.0 to 1.0. Used for display only,
not scoring.

**`ai_transparency_score`**
Derived from signals related to disclosure:
- Training data sources disclosed
- Third-party AI providers listed
- Model updates disclosed
- Transparency report available

Range: 0.0 to 1.0. Display only.

---

## Evidence-to-signal mapping

Maps AI signals to D6 (AI/ML Data Usage).

### D6 AI/ML Data Usage — positive modifiers

**Strong positives (each contributes):**
- `opt_in_required = TRUE`: +0.6
  (strongest possible privacy protection
  for AI)
- `customer_data_segregated_from_training
  = TRUE`: +0.5
- `dpa_prohibits_training_on_customer_data
  = TRUE`: +0.5
- `trains_on_customer_data = FALSE`
  (explicitly, not null): +0.4
- `iso_42001_certified = TRUE`: +0.4

**Moderate positives:**
- `opt_out_available = TRUE` AND
  `opt_out_accessibility = "self_service"`:
  +0.3
- `opt_out_retroactive = TRUE`: +0.3
- `legal_basis_stated = TRUE`: +0.2
- `bias_mitigation_documented = TRUE`:
  +0.2
- `human_in_the_loop_described = TRUE`:
  +0.2
- `ai_decisions_contestable = TRUE`: +0.2

**Weak positives (+0.1 each, cumulative):**
- `eu_ai_act_addressed = TRUE`
- `training_data_sources_disclosed = TRUE`
- `model_card_available = TRUE`
- `algorithmic_disgorgement_addressed =
  TRUE`
- `nist_ai_rmf_referenced = TRUE`

### D6 AI/ML Data Usage — negative modifiers

**Strong negatives:**
- `trains_on_customer_data = TRUE` AND
  `opt_out_available = FALSE`: -0.8
- `customer_data_used_for_foundation_
  model_training = TRUE`: -0.6
- `opt_out_denied_for_ai_features = TRUE`:
  -0.5
- `training_claim_contradicts_inference_
  retention = TRUE`: -0.3

**Moderate negatives:**
- `trains_on_customer_data = TRUE` AND
  opt-out exists but accessibility =
  "contract_negotiation": -0.4
- `legal_basis_stated = FALSE` when AI
  processing of personal data occurs: -0.3
- `eu_ai_act_claimed_tier = "minimal"`
  AND `eu_ai_act_tier_plausible = FALSE`:
  -0.3
- `opt_out_retroactive = FALSE`
  (explicitly forward-only): -0.2

### D6 — Score ceilings (hard caps)

These combinations cap D6 at specific
levels regardless of other positives:

- `trains_on_customer_data = TRUE` AND
  `opt_out_available = FALSE` AND
  `opt_in_required = FALSE`: **D6 capped
  at 1**
- `is_ai_vendor = TRUE` AND all AI
  signals are NULL (no AI policy
  published despite clearly being an
  AI vendor): **D6 capped at 2**
- `customer_data_used_for_foundation_
  model_training = TRUE` AND no opt-out:
  **D6 capped at 2**
- `training_claim_contradicts_inference_
  retention = TRUE`: **D6 capped at 3**

---

## Red flags that generate explicit findings

These combinations create high-priority
findings in the report regardless of the
final score:

1. **AI vendor with no policy** — Vendor's
   marketing or product clearly involves AI
   but no AI policy document exists or is
   provided.

2. **Training without opt-out** —
   `trains_on_customer_data = TRUE` AND
   `opt_out_available = FALSE`.

3. **Policy/DPA conflict on AI** — Privacy
   policy says one thing about AI, DPA
   says another. For example, policy
   mentions AI features but DPA has no
   AI clause restricting training use.

4. **Claimed tier implausible** —
   `eu_ai_act_tier_plausible = FALSE`.
   Specific: vendor claims "minimal" or
   "limited" for what looks like a "high"
   risk system under Annex III.

5. **Training claim / inference retention
   contradiction** — Vendor says "we
   don't train on your data" but retains
   inference data for model improvement.

6. **Foundation model training** —
   Customer data used to train foundation
   models (essentially irreversible) with
   no opt-in requirement.

7. **Opt-out is forward-only, not
   acknowledged** — Opt-out available but
   document doesn't acknowledge that data
   already in training sets cannot be
   removed.

8. **Legal basis gap** — AI processing of
   personal data with no stated legal
   basis under GDPR.

9. **Third-party AI without sub-processor
   disclosure** — Vendor uses third-party
   AI (OpenAI, Anthropic, etc.) but does
   not list them in sub-processor
   documentation.

---

## Absence vs denial tracking

Same as RUBRIC_SOC2.md. For every signal:
- TRUE: Explicitly stated in document
- FALSE: Explicitly contradicted or denied
  in document
- NULL: Not addressed in document

Report output:
- TRUE renders as ✓
- FALSE renders as ✗ (explicitly absent)
- NULL renders as ? (not addressed)

The distinction matters most for AI
policies because silence is often more
damaging than negative statements.
Example: a vendor that doesn't address
training on customer data is worse than
one that explicitly states they train on
it, because at least the latter is being
honest.

---

## Special handling — implied signals

Two signals may be inferred from other
content and should be flagged as
inferred, not extracted:

**`is_ai_vendor` (inferred)**
If the document describes features that
clearly involve AI (chatbots, smart
recommendations, predictive features)
without using the word "AI", the LLM may
mark `is_ai_vendor = TRUE` but must set
a separate flag `is_ai_vendor_inferred =
TRUE`.

**`trains_on_customer_data` (inferred
from sub-processors)**
If the document lists OpenAI, Anthropic,
or similar as sub-processors but does
not address training use, the LLM should
mark as NULL (not FALSE). Do not infer
training status from sub-processor lists
alone.

Inferred signals get lower confidence
scores and are flagged in the report.

---

## Implementation notes for AI Bandit

When rebuilding AI Bandit's prompt from
this rubric:

1. Include the critical architectural
   rules from the top of this document

2. Group signals by the sections above
   (A–J) so the LLM processes them in
   order

3. For each signal, provide the exact
   criteria and require a source
   reference for TRUE

4. Require the LLM to return NULL for
   unaddressed signals, not FALSE

5. Never ask the LLM to recommend scores

6. For the plausibility checks
   (`eu_ai_act_tier_plausible`,
   `ai_use_without_disclosure`),
   explicitly allow the LLM to exercise
   judgement but require justification

7. Include handling for multi-document
   analysis — AI policy, DPA, and model
   card together may yield different
   signals than any one alone

The signal dict returned by the LLM
becomes input to the rubric engine's D6
scoring table. No interpretation happens
between extraction and scoring.

---

## Changelog

**v1.0 — 2026-04-22**
Initial AI policy rubric. Covers 60+
signals across AI presence, training vs
inference distinction, opt-out mechanics,
legal basis, EU AI Act, data governance,
fairness and oversight, transparency,
DPA commitments, and compliance
certifications.

**Future additions:**
- Specific handling for AI agent and
  autonomous system use cases
- Enhanced EU AI Act Annex III use case
  classification guidance
- Cross-reference to AI supply chain
  (training data licensing, model
  provenance)
- Jurisdictional variants (Chinese AI
  governance, UK AI Safety Institute,
  Singapore Model AI Governance)
