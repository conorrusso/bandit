# Bandit Setup Guide

`bandit setup` runs a wizard that tailors Bandit to your organisation's specific regulatory context. This guide explains what it does and how to get the most out of it.

---

## Why run bandit setup?

Without setup, Bandit uses default weights — a GDPR-focused, technology company baseline with D6 (AI/ML) and D8 (DPA) at ×1.5.

With setup, Bandit adjusts for your specific context:

- A **healthcare company** gets D5 (breach notification) and D3 (rights) weighted higher, plus HIPAA breach timeline checks
- An **EU-based company** gets D4 (transfer mechanisms) weighted higher and EU adequacy monitoring checks
- A **financial services company** gets D7 (retention), D5, and D8 weighted higher with PCI-DSS and SOX considerations
- A company handling **special categories of data** gets D1 and D3 weighted higher
- A company buying **AI vendors** gets D6 weighted higher across all assessments

The rubric logic doesn't change. The weights change. Same signals, different emphasis.

---

## Running setup

```bash
bandit setup
```

Takes about 5 minutes. The wizard asks 26 questions across 6 sections, shows you a weight preview and reassessment schedule, and writes `bandit.config.yml` in the current directory.

If you run `bandit assess` without a config, Bandit will prompt you to run setup before starting — you can set up inline or skip it and assess with default weights.

Run it once. Update it with `bandit setup --reset` when your regulatory context changes.

To see your current profile without re-running the wizard:

```bash
bandit setup --show
```

Progress is saved after every question. If setup is interrupted (Ctrl+C or crash), running `bandit setup` again will offer to resume from where you left off.

---

## Question by question

### Section 1 — Where you operate

**Q1: Where is your company headquartered?**

Options: US, EU/EEA, UK, Canada, APAC, Other.

If you select EU/EEA or UK: D4 (transfer mechanisms) weight increases by +1.0, D3 (data subject rights) by +0.5, and D8 (DPA) by +0.5. This reflects that EU/UK organisations face direct regulatory liability for cross-border transfer compliance.

**Q2: Where are your customers located?**

Multi-select. If you include EU/EEA or UK customers: same weight adjustments as Q1 (if not already applied). This catches US companies with EU customer bases who are in scope for GDPR as controllers.

**Q3: Where is your infrastructure hosted?**

Multi-select. If you select EU + US (cross-border): D4 weight increases by an additional +0.5 on top of any Q1/Q2 adjustment. Cross-border transfers are a distinct enforcement risk from simply having EU customers.

---

### Section 2 — Your industry

**Q4: Which industry best describes your company?**

Options: Technology, Healthcare, Financial Services, Education, Retail / E-commerce, Government / Public sector, Professional Services, Other.

Healthcare → D5 (breach) +1.0, D1 (minimization) +0.5, D3 (rights) +0.5
Financial Services → D7 (retention) +0.5, D5 +0.5, D8 (DPA) +0.5

---

### Section 3 — Your data

**Q5: Do any vendors handle Protected Health Information (PHI)?**

If yes: D5 (breach) +1.0, D1 (minimization) +0.5, D3 (rights) +0.5, D8 (DPA) +0.5. PHI triggers HIPAA breach notification requirements with a 60-day timeline (stricter than GDPR's 72 hours to the authority).

**Q6: Do any vendors handle payment card data (PCI)?**

If yes: D7 (retention) +0.5, D8 (DPA) +0.5, D5 (breach) +0.5. PCI-DSS has specific cardholder data deletion and breach notification requirements.

**Q7: Do any vendors process children's data?**

If yes: D1 (minimization) +0.5, D3 (rights) +0.5. COPPA and GDPR Art. 8 set higher standards for lawful basis and parental consent.

**Q8: Do any vendors process special-category data?**

Special categories include race, ethnic origin, health, biometric, religious, political, and sexual orientation data.

If yes: D1 (minimization) +0.5, D3 (rights) +0.5, D6 (AI/ML) +0.5. Special categories under GDPR Art. 9 require explicit consent or a specific Art. 9(2) exception — the bar is higher.

**Q9: Do you onboard AI/ML vendors that may train on your data?**

If yes: D6 (AI/ML usage) +0.5 across all assessments. EU AI Act and FTC disgorgement precedent make AI training clauses a priority risk.

**Q10: Approximately how many vendors will you assess per month?**

Informational only. Used to calibrate recommendation language.

---

### Section 4 — Regulatory obligations

**Q11: Which regulations apply to your organisation?**

Multi-select: GDPR, CCPA/CPRA, HIPAA, PCI DSS, UK GDPR, LGPD, PIPL, Other.

Used to inform contract recommendation language in reports. A HIPAA-scoped company sees HIPAA BAA language in D5 recommendations; a CCPA company sees CPRA service provider provisions in D8.

**Q12: Does your organisation have a designated DPO?**

If yes: Bandit assumes a higher maturity baseline and adjusts recommendation language accordingly.

---

### Section 5 — Risk appetite

**Q13: What is your organisation's risk appetite for vendor privacy risk?**

Options: Conservative (lower thresholds — escalate early), Moderate (follow risk tier), Liberal (escalate only on HIGH).

**Q14: At what risk tier should auto-escalation trigger?**

Options: HIGH tier only, HIGH or MEDIUM tier, Never (manual review only).

If you select HIGH only: an `auto_escalate` trigger is added for `tier: HIGH`.
If you select HIGH or MEDIUM: triggers are added for both tiers.

**Q15: Should AI training red flags trigger escalation regardless of overall score?**

If yes: any detection of AI training bundled under generic "improvement" language triggers escalation regardless of the vendor's overall tier.

---

### Section 6 — Team context & reassessment

**Q16: Who typically reviews vendor assessments?**

Options: GRC team, Legal / Privacy counsel, Security team, DPO, Individual / ad hoc, Shared responsibility.

---

#### HIGH risk vendors

**Q17a: Assessment depth for HIGH risk vendors?**

| Option | What it runs |
|--------|-------------|
| Full assessment | All 8 dimensions scored |
| Lightweight | D1, D6, D7 only |
| Privacy policy scan | Red flags only, no scoring |
| No automated assessment | Skip — manual review only |

Default: Full assessment.

**Q17b: How often do you reassess HIGH risk vendors?**

Preset options: every 6 months, every year (default), every 18 months, every 2 years, on policy change only, one time only. Or enter any custom number of days.

**Q17c: What triggers an out-of-cycle reassessment for HIGH risk vendors?**

Multi-select with defaults shown. Options: Policy change detected, Vendor breach reported, Regulatory change affecting this vendor, Contract renewal, Manual trigger only.

Defaults: Policy change, Vendor breach, Regulatory change.

---

#### MEDIUM risk vendors

**Q18a–Q18c:** Same three questions as HIGH. Default depth: Full. Default cadence: every 2 years. Default triggers: Policy change, Vendor breach.

---

#### LOW risk vendors

**Q19a–Q19c:** Same three questions. Default depth: Privacy policy scan. Default cadence: one time only. Default triggers: Vendor breach.

---

**Q26: What describes your current vendor assessment maturity?**

Options: Just starting, Have a process, Mature programme.

Used to calibrate recommendation language — early-stage teams get more prescriptive guidance; advanced teams get more concise output.

---

## Weight calculation summary

Base weights (default): D1=1.0, D2=1.0, D3=1.0, D4=1.0, D5=1.0, D6=1.5, D7=1.0, D8=1.5

Modifiers are additive and stacked across all applicable answers. Weights are clamped between 0.5 and 3.0.

Example — EU healthcare company processing PHI with a conservative risk appetite:

| Dim | Base | EU HQ | Healthcare | PHI | Final |
|-----|------|-------|------------|-----|-------|
| D1 | 1.0 | — | +0.5 | +0.5 | 2.0 |
| D3 | 1.0 | +0.5 | +0.5 | +0.5 | 2.5 |
| D4 | 1.0 | +1.0 | — | — | 2.0 |
| D5 | 1.0 | — | +1.0 | +1.0 | 3.0 |
| D8 | 1.5 | — | — | +0.5 | 2.0 |

---

## Editing the config directly

`bandit.config.yml` is human-readable YAML. Power users can edit it directly.

```yaml
profile:
  name: EU Healthcare
  industry: Healthcare
  hq_region: EU/EEA
  customer_regions:
    - EU/EEA
    - US
  infra_regions:
    - EU/EEA
    - US
  regulations:
    - GDPR
    - HIPAA
  risk_appetite: conservative
  dpo_present: true
  phi_in_scope: true
  pci_in_scope: false
  childrens_data: false
  special_categories: true
  ai_vendors: false
  review_team: GRC team
  maturity: mature programme
  weights:
    D1: 2.0
    D2: 1.0
    D3: 2.5
    D4: 2.0
    D5: 3.0
    D6: 1.5
    D7: 1.0
    D8: 2.0

reassessment:
  high:
    depth: full
    days: 365
    triggers:
      - policy_change
      - breach_reported
      - regulatory_change
  medium:
    depth: full
    days: 730
    triggers:
      - policy_change
      - breach_reported
  low:
    depth: scan
    days: 0
    triggers:
      - breach_reported

auto_escalate:
  - type: tier
    tier: HIGH
    label: Vendor risk tier is HIGH — requires DPO / security review
  - type: red_flag
    flag_label: AI training
    label: AI training on customer data detected with no opt-out mechanism
```

Valid values:

| Key | Valid values |
|-----|-------------|
| `hq_region` | `EU/EEA`, `UK`, `US`, `Canada`, `APAC`, `Other` |
| `industry` | `Technology`, `Healthcare`, `Financial Services`, `Education`, `Retail / E-commerce`, `Government / Public sector`, `Professional Services`, `Other` |
| `risk_appetite` | `conservative`, `moderate`, `liberal` |
| `reassessment[tier].depth` | `full`, `lightweight`, `scan`, `none` |
| `reassessment[tier].days` | Any positive integer, or `0` for one-time / on-change only |
| `reassessment[tier].triggers` | `policy_change`, `breach_reported`, `regulatory_change`, `contract_renewal` |
| `auto_escalate[].type` | `tier`, `score_below`, `red_flag`, `weighted_average_below` |
| `maturity` | `just starting`, `have a process`, `mature programme` |

---

## Per-vendor overrides

Some vendors need different settings than your global config — for example, a healthcare vendor assessed by a technology company that doesn't normally process PHI.

Per-vendor flag overrides are planned for v1.1. For now, the simplest approach is to run `bandit setup --reset` before assessing the vendor, then reset back after.
