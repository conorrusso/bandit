# Sample Output — High Risk Assessment

**Bandit v1.5.2 | Rubric: v1.0.0**
*This is a fictional example for demonstration purposes. All vendor names and documents are invented.*

> The HTML version of this report is at `examples/sample-high-risk-output.html`.

---

## Assessment Metadata

```
Vendor:          FictiSoft Analytics
Input:           Local documents (/tmp/bandit_samples/fictisoft/)
Assessment date: 2026-04-30
Model:           claude-haiku-4-5-20251001
Rubric:          v1.0.0
```

---

## Dimension Scores

| Dim | Label | Score | Risk |
|-----|-------|-------|------|
| D1 | Data Minimization | 2 | Deficient |
| D2 | Sub-processor Management | 2 | Absent |
| D3 | Data Subject Rights | 3 | Minimum compliance |
| D4 | Cross-Border Transfer Mechanisms | 2 | Deficient |
| D5 | Breach Notification | 2 | Deficient |
| D6 | AI/ML Data Usage | 1 | Absent |
| D7 | Retention & Deletion | 1 | Deficient |
| D8 | DPA Completeness | N/A | Requires DPA |

**Overall: HIGH — 1.9 / 5.0**

---

## Red Flags

- **[D5]** No specific breach notification commitment — vague "in accordance with applicable law"
- **[D4, D8]** Outdated transfer mechanism — sole reliance on invalidated EU-US Privacy Shield
- **[—]** training_without_optout — vendor trains on customer data with no opt-out mechanism
- **[—]** training_inference_contradiction — claims not to train but retains inference data for model improvement
- **[—]** implausible_ai_act_tier — claimed EU AI Act risk tier implausible for described employment-scoring use case
- **[—]** no_legal_basis_for_ai — AI processing of personal data with no stated legal basis under GDPR

---

## Key Findings by Dimension

### D1 — Data Minimization | Score: 2

Policy claims to collect "any information that is useful for providing our services" with no enumerated categories. Sensitive data including health, financial, and location data collected without explicit legal basis. "Including but not limited to" language used throughout.

### D2 — Sub-processor Management | Score: 2

DPA does not maintain a sub-processor list and explicitly states this. No advance-notice obligation for new sub-processors. No equivalent-protection requirement imposed on sub-processors.

### D3 — Data Subject Rights | Score: 3

Access and deletion rights mentioned but many GDPR rights (portability, restriction, rectification) absent. No response timeline stated beyond "reasonable timeframe." No DPA supervisory authority complaint pathway.

### D4 — Cross-Border Transfer Mechanisms | Score: 2

Policy references EU-US Privacy Shield, invalidated by CJEU Schrems II in 2020. No SCCs, BCRs, or EU-US Data Privacy Framework mentioned. Data may be transferred to countries without adequate protection.

### D5 — Breach Notification | Score: 2

Breach notification mentioned but no 72-hour DPA notification commitment. No timeline for individual notification. No breach register or escalation procedure described.

### D6 — AI/ML Data Usage | Score: 1

Policy confirms AI-driven profiling for employment and credit decisions. Users explicitly waive right to human review — unlawful under GDPR Art. 22(3). Customer data used for model training with no opt-out.

### D7 — Retention & Deletion | Score: 1

No specific retention periods. Data retained "as long as reasonably necessary for business purposes." Deletion window is 180 days with broad business records exceptions that may override deletion requests.

### D8 — DPA Completeness | Score: N/A

DPA provided but highly deficient — no sub-processor list, no audit rights, no specific security measures, no breach timeline commitment, no deletion confirmation obligation.

---

## Recommended Actions

- **GRC:** Escalate to security review. Do not proceed to contract.
- **Legal:** Request an updated DPA before signing anything.
- **Security:** Request SOC 2 Type II report directly from the vendor.
