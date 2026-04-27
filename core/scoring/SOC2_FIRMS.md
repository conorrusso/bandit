# SOC2_FIRMS

List of recognised audit firms for SOC 2
reports. Used by Audit Bandit to set
`auditor_firm_recognised = TRUE` when the
extracted firm name matches an entry here.

---

## Important — what this list is and isn't

### What this is

A neutral catalogue of audit firms that
commonly produce SOC 2 Type II reports
for enterprise software vendors. The
list confirms Bandit recognises a given
firm; it does not rate, rank, or judge
quality.

### What this is not

This is not a ranking. It is not a
quality endorsement. It is not a list of
"good" firms vs "bad" firms. Firms not on
this list are not inferior — Bandit just
can't verify them against a known set.

Ranking audit firms publicly would create
legal exposure (defamation risk) without
providing reliable information. Firm
quality varies by partner, team, and
engagement, not by firm brand.

### How it affects scoring

When a firm from this list is identified:
- `auditor_firm_recognised = TRUE`
- Small positive modifier on D8 (+0.1)

When a firm is not on this list:
- `auditor_firm_recognised = FALSE`
- No modifier applied (neutral)

This is deliberately a small signal. A
recognised firm is a soft positive, not a
quality guarantee.

---

## Recognition criteria

A firm is added to this list if it meets
ALL of the following:

1. AICPA member firm or equivalent
   accreditation in home jurisdiction
2. Licensed to perform SOC 2 examinations
3. Has published multiple SOC 2 reports
   for enterprise software vendors
4. Maintains a dedicated SOC 2 or IT audit
   practice (not just one-off engagements)

Firms are added based on visible presence
in enterprise SOC 2 reports. The list is
not exhaustive and does not claim to be.

---

## The Big Four

Global full-service accounting firms with
major SOC practices.

- Deloitte (Deloitte & Touche LLP)
- PwC (PricewaterhouseCoopers LLP)
- EY (Ernst & Young LLP)
- KPMG (KPMG LLP)

Known aliases to match:
- "Deloitte" / "Deloitte & Touche" /
  "Deloitte Risk & Financial Advisory"
- "PricewaterhouseCoopers" / "PwC" /
  "PricewaterhouseCoopers LLP"
- "Ernst & Young" / "EY" / "EY LLP" /
  "Ernst & Young LLP"
- "KPMG" / "KPMG LLP" / "KPMG Audit"

---

## Tier 2 — Large national and international firms

Large full-service accounting firms with
established SOC 2 practices.

- BDO (BDO USA LLP / BDO International)
- Grant Thornton (Grant Thornton LLP)
- RSM US LLP
- Crowe LLP
- Baker Tilly (Baker Tilly US, LLP)
- Moss Adams LLP
- Plante Moran
- CohnReznick LLP
- Eisner Advisory Group
- Marcum LLP

Known aliases:
- "BDO" — often appears as "BDO USA" in
  US reports, "BDO LLP" in UK
- "Grant Thornton" — may appear as
  "Grant Thornton International" for
  cross-border vendors
- "RSM" — "RSM US LLP" is the US member
  firm of RSM International

---

## Tier 3 — Specialised SOC 2 firms

Firms with a primary focus on SOC
examinations, cybersecurity, and IT
compliance.

- A-LIGN (A-LIGN Compliance and Security)
- Coalfire (Coalfire Systems Inc.)
- Schellman & Company LLC (Schellman)
- Linford & Company LLP
- Insight Assurance
- BARR Advisory
- Sensiba LLP
- Sensiba San Filippo LLP (legacy name)
- Aprio
- KirkpatrickPrice
- Prescient Assurance
- Ernst & Young Global
- Richey May & Co. LLP
- PKF O'Connor Davies
- Eide Bailly LLP
- Armanino LLP

Known aliases:
- "Schellman" — may appear as "Schellman
  & Co." or "Schellman & Company"
- "Coalfire" — may appear as "Coalfire
  Controls LLC" for the SOC audit entity

---

## Tier 4 — Regional and specialised

Regional CPA firms and specialists with
notable SOC 2 practice presence.

- Frazier & Deeter LLC
- HORNE LLP
- Dixon Hughes Goodman LLP (DHG; now
  part of FORVIS)
- FORVIS LLP (DHG + BKD merger)
- Cherry Bekaert LLP
- Wipfli LLP
- Rehmann
- Warren Averett
- Clark Nuber PS
- UHY Advisors

---

## International recognition

Firms based outside the US that commonly
audit US-facing vendors.

**United Kingdom:**
- BDO LLP (UK)
- Grant Thornton UK LLP
- PKF Littlejohn LLP
- Mazars (now Forvis Mazars)

**Europe:**
- Mazars (France / International)
- Baker Tilly Europe member firms
- Grant Thornton International member
  firms

**Canada:**
- MNP LLP
- Grant Thornton Canada (Raymond
  Chabot Grant Thornton in Quebec)

**Australia:**
- BDO Australia
- Grant Thornton Australia

**Asia-Pacific:**
- BDO member firms
- Grant Thornton member firms

---

## Matching logic

When Audit Bandit extracts an auditor
firm name, the comparison against this
list should:

1. Normalise case (lowercase both)
2. Strip common legal suffixes:
   "LLP", "LLC", "Inc.", "& Co.",
   "& Company", "PLLC", "PC"
3. Strip "Audit" or "Audit LLP" suffix
4. Check for exact match first
5. Check for substring match second
   (e.g., "deloitte" matches
   "Deloitte & Touche LLP")
6. Check known aliases list

Do NOT do fuzzy matching. A firm name
that doesn't exactly match a known entry
should return FALSE rather than a
questionable match.

---

## How to contribute

This list is maintained in the open-
source repo. To add a firm:

1. Verify the firm meets the recognition
   criteria above
2. Confirm the firm has published SOC 2
   reports (cite at least one public
   vendor)
3. Submit a pull request with the firm
   name added in the appropriate section

Contributions should be evidence-based.
Do not add firms based on reputation
alone or remove firms based on
disagreement with their work.

---

## What to do with unrecognised firms

If `auditor_firm_recognised = FALSE`,
the report should display a neutral
note:

```
Auditor: [Firm Name]
Note: Firm not on Bandit's recognised
list. This is neutral — the list is
not exhaustive. Verify the firm's
AICPA membership and state licensure
if you haven't already.
```

Do not imply the firm is low quality.
Do not imply the audit is invalid.
Just flag that Bandit cannot confirm
the firm against a known list.

---

## Excluded from this list

Firms are not included if they:

- Are no longer operating
- Have had their AICPA membership
  suspended or revoked
- Operate primarily outside the SOC
  examination space
- Have been subject to major SEC or
  PCAOB enforcement actions within
  the past 5 years

This exclusion is handled by simply
not adding or by removing entries.
It is never a public statement about
a firm's quality.

---

## Changelog

**v1.0 — 2026-04-22**
Initial list. Big 4, Tier 2 nationals,
Tier 3 specialists, Tier 4 regionals,
and international recognition. Approx.
40 firms covered, representing the
majority of SOC 2 reports in the
enterprise software market.

**Planned updates:**
- Periodic review (annually) for
  mergers, name changes, and new
  entrants
- Community PRs for regional firms
  not currently listed
