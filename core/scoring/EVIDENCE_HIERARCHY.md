# Evidence Hierarchy

Bandit's foundational rule for how different types
of vendor evidence are weighted, merged, and
scored. This document is the source of truth —
every agent, rubric, and scoring decision must
follow these rules.

---

## The core principle

**Stronger evidence wins for positive claims.
Weaker evidence wins for scoring caps.**

Translated:
- If the DPA says "no breach notification" and the
  SOC 2 was tested clean for breach controls, the
  DPA's absence is what Bandit reports — because
  the audit doesn't fix a missing contractual
  commitment
- If the privacy policy promises 24-hour breach
  notification but the DPA only says "prompt," the
  policy's claim doesn't lift the score — the DPA
  is what's enforceable

The logic: an enforceable commitment beats an
attested control beats a tested control beats a
self-claimed control beats a public promise.

Except when it doesn't — sometimes a tested
control is stronger evidence than a written
commitment that was never verified. The rules
below spell out when each wins.

---

## Evidence types recognised by Bandit

Six distinct evidence types, each with its own
characteristics, reliability, and scoring weight.

### Tier 1 — Independent third-party verification

**What it is:** A qualified independent party
tested the vendor's controls and issued an
opinion.

**Examples:**
- SOC 2 Type II report
- ISO 27001 / 27701 / 42001 certificate
- HITRUST CSF assessment
- FedRAMP authorisation
- Penetration test by qualified firm

**Why it's weighted highly:**
The vendor did not produce this evidence
themselves. A qualified third party applied a
standard framework and issued findings. The
vendor cannot unilaterally claim controls work
— someone had to test and sign off.

**Scoring weight:** 2.0 base, up to 2.5 for
clean reports with Privacy TSC

**Limitations:**
- Scope is vendor-chosen (they pick what to audit)
- Period is historical (always looks backward)
- Firm quality varies (see RUBRIC_SOC2.md)
- Exceptions matter more than the opinion letter

### Tier 2 — Contractual commitments

**What it is:** Legally binding commitments the
vendor has made to you in a signed agreement.

**Examples:**
- Data Processing Agreement (DPA)
- Master Service Agreement (MSA)
- Business Associate Agreement (BAA)
- Standard Contractual Clauses (SCCs)
- Addendums with specific protections

**Why it's weighted highly:**
The vendor signed this. They can be sued over
it. Unlike audit reports (which describe what
was), contract commitments describe what must
be going forward.

**Scoring weight:** 1.5 base

**Limitations:**
- Vague language is unenforceable ("appropriate",
  "reasonable", "commercially reasonable efforts")
- Commitments without measurable SLAs may not be
  meaningful
- Standard DPAs often have less protection than
  customer-negotiated versions

### Tier 3 — Third-party questionnaire responses

**What it is:** Vendor's answers to a standardised
questionnaire, ideally with attached evidence.

**Examples:**
- SIG Lite / SIG Core (Shared Assessments)
- CSA CAIQ (Cloud Security Alliance)
- VSA (Vendor Security Alliance)
- HECVAT (education)
- NIST 800-171 self-assessment

**Why it's weighted moderately:**
It's self-attested but structured. The vendor
is answering specific questions under a common
framework. If they attach evidence for their
answers, the weight increases.

**Scoring weight:**
- Answer with evidence attached: 1.2
- Answer without evidence: 1.0
- "Partial" or "In Progress": 0.7 (counts as
  not yet)
- "NA" with explanation: neutral
- "NA" without explanation: -0.2 (possible dodge)

**Limitations:**
- Vendor chose which questions to answer
- "Yes" without evidence is just a claim
- Completion date matters — stale questionnaires
  are nearly useless
- Contradictions with other evidence must be
  flagged, not averaged

### Tier 4 — Vendor policies and public commitments

**What it is:** Written statements the vendor
publishes or shares that describe their
practices.

**Examples:**
- Privacy policy (public)
- Terms of Service (public)
- AI policy / Responsible AI statement
- Security policy
- Sub-processor list (usually public)
- Model cards

**Why it's weighted modestly:**
These are promises to the public or customers.
They're not legally binding the way contracts
are, but they do create reputational and
regulatory risk if violated. Regulators
(FTC, CNIL, ICO) have enforcement precedents
against companies that violate their own
stated policies.

**Scoring weight:** 1.0 base

**Limitations:**
- Vendor can update unilaterally
- Often written by legal to minimise commitment
- Absence of a commitment is not evidence
  of its opposite

### Tier 5 — Intake / procurement context

**What it is:** What the customer (you) told
Bandit about the vendor relationship during
intake.

**Examples:**
- Q1 data types the vendor will access
- Q3 production vs sandbox
- Q4 blast radius
- Q6 integrations
- Q7 AI vendor flag

**Why it's not scored directly:**
Intake is context, not evidence. It doesn't
raise or lower a vendor's score. It shapes
the dimension weights and tells the agents
what to focus on.

**Effect:** Weight modifier on dimensions, not
a score input.

### Tier 6 — Public sources (lowest tier)

**What it is:** Anything from outside the
vendor's own documentation.

**Examples:**
- News reports of breaches
- Regulatory enforcement actions
- Public court filings
- Former employee reports

**Why it's weighted low:**
Unverified, potentially outdated, often
adversarial framing. Can flag concerns but
should never directly lower a score without
corroborating evidence.

**Scoring weight:** 0 (context only, no direct
scoring). Used for red flag detection, not
scoring.

**Current state:** Not yet implemented in
Bandit. Placeholder for future versions.

---

## How signals merge across evidence types

When multiple evidence types address the same
claim, Bandit follows these rules:

### Rule 1 — Strongest positive evidence wins

When two evidence types both support a positive
signal, Bandit uses the stronger one.

Example — breach notification:
```
Privacy Policy:   "we notify promptly"        → weak positive
DPA §7.2:        "notify within 24 hours"    → strong positive
SOC 2:           control tested, 0 exceptions → tested positive

Result: d5_notification_timeline_stated = TRUE
        source = "DPA §7.2"
        evidence_type = "contract_commitment"
```

The SOC 2 tested control reinforces the DPA
commitment but doesn't replace it — the DPA
is what's enforceable.

### Rule 2 — Weakest evidence wins for score caps

When evidence types conflict, the weakest
evidence determines the score ceiling. A
vendor cannot get credit for a strong SOC 2
if their DPA has a missing commitment.

Example — retention:
```
Privacy Policy: "we delete data within 30 days"    → public promise
DPA:           no deletion timeline specified       → contract gap
SOC 2:         no deletion controls tested          → audit silent

Result: d7_deletion_timeline_committed = FALSE
        d7_score capped at 2
        Red flag: "Policy claims 30-day deletion
        but DPA has no matching commitment —
        policy statement is not contractually
        enforceable."
```

### Rule 3 — Conflicts are flagged, not averaged

When evidence types contradict each other,
Bandit does not average or silently pick one.
Conflicts become first-class findings in the
report.

Example — AI training:
```
Privacy Policy: "we do not train on customer data"
DPA:           silent on AI training
SIG response:  "Yes, we use customer data for
                model improvement with opt-out"

Result: CONFLICT flagged
        Report section: "Policy/Questionnaire
        Conflict — Privacy policy states no
        AI training; SIG response indicates
        training with opt-out. Clarification
        required before signing."
```

### Rule 4 — Tier 3 with evidence > Tier 3 without

A questionnaire answer with attached evidence
is stronger than one without, even at the
same tier.

```
SIG Q47: "Do you have a documented IR plan?"
  Vendor A: "Yes"                     → weak
  Vendor B: "Yes" + IR plan attached  → strong
  Vendor C: "Yes" + IR plan + last
            tabletop exercise date    → stronger
```

### Rule 5 — Currency matters more than type

A stale evidence of any type is less valuable
than a current evidence of a lower type.

```
SOC 2 Type II, period ending 2 years ago   → weighted 0.7x
Current privacy policy published last month → full weight
Fresh SIG completed last quarter            → full weight
```

Currency thresholds:
- SOC 2: <12 months = current, 12-18 months =
  stale (needs bridge letter), >18 months =
  outdated
- ISO cert: within 3-year validity with
  surveillance audits = current
- Questionnaire: <12 months = current,
  12-24 months = stale, >24 months = outdated
- Pentest: <12 months = current, >12 = stale
- Privacy policy: published date vs most
  recent material change; stale if >24 months

---

## Evidence source tracking

Every signal Bandit extracts must include where
it came from. The signal dict structure:

```python
signal = {
    "value": True,                    # Does the
                                      # signal hold?
    "source": "DPA §7.2",             # Where in
                                      # the document
    "document": "Cloud Data Processing
                 Addendum.pdf",       # Which doc
    "evidence_type": "contract_commitment",
    "confidence": 0.95,               # How certain
                                      # the agent is
    "quote": "Google will notify within 24 hours...",
}
```

The report displays evidence type per signal
so GRC practitioners can see at a glance
whether a claim is tested, committed,
attested, or just stated.

---

## Dimension weight modifiers by evidence type

Framework modifiers applied to dimensions based
on what evidence was provided:

### D2 Sub-processor Management

- Sub-processor list published (public policy):
  base
- DPA commitment on sub-processor notification:
  +0.3
- SIG/CAIQ sub-processor questions answered with
  evidence: +0.2
- SOC 2 tested sub-processor controls, no
  exceptions: +0.4
- ISO 27001 scope includes sub-processor
  management: +0.2

### D5 Breach Notification

- Privacy policy mentions notification: +0.1
- DPA specifies timeline (even if vague): +0.3
- DPA specifies 24hr or 72hr timeline: +0.5
- SIG breach notification answered with IR plan
  attached: +0.3
- SOC 2 tested breach controls, no exceptions:
  +0.5
- SOC 2 Privacy TSC clean: +0.7

### D6 AI/ML Data Usage

- Privacy policy addresses AI: +0.2
- AI policy document exists: +0.4
- Model card with training data disclosure: +0.5
- DPA has AI restriction clause: +0.6
- ISO 42001 certified: +0.5

### D7 Retention and Deletion

- Privacy policy states retention: +0.1
- DPA specifies deletion timeline: +0.4
- SIG retention/deletion answered with policy
  attached: +0.2
- SOC 2 tested deletion controls: +0.4

### D8 DPA Completeness

- DPA contains Art. 28 provisions: base
- DPA has processing annex: +0.2
- DPA has TOMs annex: +0.2
- DPA has measurable SLAs: +0.3
- SIG responses corroborate DPA terms: +0.2
- SOC 2 Type II with Privacy TSC, clean: +0.5
- ISO 27701 certified: +0.4

Note: modifiers are additive per dimension but
capped at a max of +1.0 to prevent a single
vendor from over-scoring through volume of
evidence.

---

## Score caps from weak evidence

Some evidence gaps create hard score ceilings
regardless of other positive evidence.

### Missing DPA

- D8 capped at 2 if no DPA provided
- D2, D5, D7 capped at 3 (policy can claim but
  can't commit without DPA)

### Stale audit evidence

- If SOC 2 is >18 months old with no bridge
  letter, no SOC 2 framework modifier applies
- Score reflects only current evidence

### Vague contract language

- If DPA uses "appropriate measures" without
  specifics, that provision's contribution is
  capped at +0.2 not full weight
- D5 specifically: "prompt notification"
  without a timeline caps D5 at 3

### Policy/DPA conflict

- When privacy policy promises something the
  DPA doesn't back, the score is capped at
  the DPA level, not the policy level
- Flagged as conflict in report

### AI training without opt-out

- If vendor uses customer data for AI training
  with no opt-out mechanism, D6 capped at 2
  regardless of other AI evidence quality

### Questionnaire contradicts audit

- If SIG response claims a control that the
  SOC 2 shows as an exception, both are
  flagged and the SOC 2 (tested) wins for
  scoring

---

## Rules for agents

Every specialist agent must follow these rules:

### Agent responsibilities

1. **Extract signals, not scores.** The agent
   answers yes/no questions about what the
   document contains. The rubric engine scores.

2. **Track source for every signal.** Every
   True signal must include document name and
   section reference.

3. **Flag, don't resolve, conflicts.** If
   evidence contradicts, both signals go into
   the merge layer. Agents do not pick a winner.

4. **Acknowledge absence.** A document not
   mentioning something is different from a
   document stating the opposite. Signals must
   distinguish "absent" from "explicitly denied."

5. **Include evidence type classification.**
   Every signal the agent produces must be
   tagged with which tier it came from
   (tested / committed / attested / stated).

### Agent prompt structure

Every agent prompt must:

1. State the evidence tier being analysed
2. Provide the extraction criteria as yes/no
   questions (no interpretation)
3. Demand document section references for
   positive signals
4. Prohibit the agent from producing scores
5. Require the agent to flag absences vs
   denials distinctly

---

## How this affects report rendering

The HTML report must distinguish evidence
sources visually so GRC practitioners can
evaluate quality at a glance:

### Per dimension

Show evidence type badges:
- 🟢 Tested (SOC 2 / ISO / pentest)
- 🔵 Committed (DPA / MSA / BAA)
- 🟡 Attested (questionnaire with evidence)
- ⚪ Claimed (policy / public statement)

### Evidence inventory section

New section showing what evidence types are
available for this vendor:

```
Evidence Inventory
─────────────────
🟢 Audit Evidence
   SOC 2 Type II · 2025-10-01 to 2026-03-31 ·
   Privacy TSC included · 0 exceptions
   ISO 27001 · valid to 2027-08 · 3rd
   surveillance audit
   ISO 42001 · valid to 2027-11 · initial cert

🔵 Contractual Commitments
   DPA · Google Cloud Data Processing Addendum ·
   Art. 28 provisions present, TOMs annex
   missing
   MSA · Standard Google Cloud MSA · commercial
   data protection terms reviewed

🟡 Self-Attested Evidence
   SIG Lite · completed 2026-02-01 · signed ·
   95 of 135 questions answered
   CAIQ v4.0.3 · published on CSA STAR ·
   last updated 2026-01-15

⚪ Public Commitments
   Privacy Policy · last updated 2025-11-10 ·
   5,961 chars
   Terms of Service · last updated 2025-11-10
   AI Policy · published 2025-08-01
```

---

## Reserved field names

These signal keys are reserved for the
evidence merging system and must not be used
by agents for other purposes:

- `source` — document and section reference
- `evidence_type` — tier classification
- `confidence` — agent's extraction confidence
- `quote` — verbatim text supporting the signal
- `document` — source filename
- `conflict_with` — list of conflicting signals
- `superseded_by` — stronger evidence that
  overrides this
- `currency` — freshness of the underlying
  evidence

---

## Version and changelog

**v1.0 — 2026-04-22**
Initial evidence hierarchy. Covers Tier 1-6,
merge rules, score caps, and agent
responsibilities. To be used as foundational
reference for RUBRIC_SOC2.md, RUBRIC_AI_POLICY.md,
RUBRIC_ISO.md, and RUBRIC_QUESTIONNAIRE.md.

Future versions will add:
- Tier 6 implementation (public sources)
- Cross-evidence validation agent
- Evidence ageing rules per industry
- Jurisdiction-specific weight modifiers
