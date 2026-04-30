# Sample Output — Low Risk Assessment

**Bandit v1.5.2 | Rubric: v1.0.0**
*This is a fictional example for demonstration purposes. All vendor names and documents are invented.*

> The HTML version of this report is at `examples/sample-low-risk-output.html`.

---

## Assessment Metadata

```
Vendor:          Acme Cloud Services
Input:           Local documents (/tmp/bandit_samples/acme/)
Assessment date: 2026-04-30
Model:           claude-haiku-4-5-20251001
Rubric:          v1.0.0
```

---

## Dimension Scores

| Dim | Label | Score | Risk |
|-----|-------|-------|------|
| D1 | Data Minimization | 5 | Gold standard |
| D2 | Sub-processor Management | 2 | Minimum compliance |
| D3 | Data Subject Rights | 4 | Strong |
| D4 | Cross-Border Transfer Mechanisms | 4 | Strong |
| D5 | Breach Notification | 2 | Minimum compliance |
| D6 | AI/ML Data Usage | 3 | Minimum compliance |
| D7 | Retention & Deletion | 2 | Strong |
| D8 | DPA Completeness | 2 | Minimum compliance |

**Overall: MEDIUM — 3.1 / 5.0**

---

## Frameworks Detected

- ✓ SOC 2 Type II (Security)
- ✓ ISO 27001:2022

---

## Red Flags

- **[D5, D8]** No operational SLA beyond GDPR verbatim — breach notification stated as "without undue delay" only, no specific hour commitment in DPA
- **[—]** stale_audit_no_bridge — SOC 2 audit period ended 12–18 months ago with no bridge letter

---

## Key Findings by Dimension

### D1 — Data Minimization | Score: 5

Comprehensive data minimisation policy. All categories enumerated with specific legal basis per category (contract, legal obligation, legitimate interests). Special category data explicitly excluded unless separately agreed. Privacy by Design embedded in SDLC with DPIA screening. Retention schedule in appendix with specific periods per category.

### D2 — Sub-processor Management | Score: 2

Public sub-processor list maintained with named sub-processors. 30-day advance notice of new sub-processors. Contractual flowdown obligations in place. Gap: DPA does not explicitly grant right to object with contract termination option if objection upheld.

### D3 — Data Subject Rights | Score: 4

All GDPR Arts. 15–21 rights explicitly enumerated with individual explanations. 30-day response timeline stated, extendable 60 days with notice. Irish DPC complaint pathway provided. Gap: no CCPA rights or automated DSAR workflow.

### D4 — Cross-Border Transfer Mechanisms | Score: 4

Primary processing within EEA (Dublin, Frankfurt). EU Standard Contractual Clauses (2021) used for US sub-processors. Transfer Impact Assessments completed and available on request. Named sub-processor locations specified. Gap: no supplementary measures documented beyond SCCs; no monitoring process for adequacy changes.

### D5 — Breach Notification | Score: 2

Breach notification obligation stated in DPA. 48-hour Customer notification commitment. Gap: no operational SLA specifying response lead or breach categories. Red flag: DPA uses "without undue delay" rather than a specific-hour commitment for DPA notification, falling back on GDPR verbatim.

### D6 — AI/ML Data Usage | Score: 3

Policy explicitly states no AI used for decisions with legal or similarly significant effects (GDPR Art. 22 compliant). No customer data used for model training. Automated anomaly detection reviewed by humans. Gap: AI not disclosed as a separate processing purpose with its own legal basis entry.

### D7 — Retention & Deletion | Score: 2

Category-specific retention schedule (Appendix A) with periods from 30 days (backups) to 7 years (billing). Automated deletion with written confirmation available. 14-day deletion request processing. 30-day backup purge commitment. Gap: derived data and AI inference data retention not addressed; sub-processor deletion obligations not specified in DPA.

### D8 — DPA Completeness | Score: 2

Most GDPR Art. 28 provisions present: processing restrictions, confidentiality, sub-processor management, data subject rights assistance, deletion. Annex II lists technical measures. Gap: audit rights limited to one per year with 30-day notice; DPA does not specify breach categories or escalation matrix.

---

## Recommended Actions

- **GRC:** Flag specific gaps for contract negotiation.
- **Legal:** Negotiate DPA improvements — add breach SLA hours, sub-processor objection-with-termination right, derived data deletion.
- **Security:** Verify sub-processor list; confirm SOC 2 bridge letter or request most recent report.
