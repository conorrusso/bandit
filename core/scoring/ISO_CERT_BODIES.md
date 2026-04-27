# ISO_CERT_BODIES

List of recognised ISO certification bodies
for ISO/IEC 27001, 27701, and 42001
certificates. Used by Audit Bandit to set
`iso_*_certification_body_accredited = TRUE`
when the extracted body name matches an
entry here.

---

## Important — what this list is and isn't

### What this is

A catalogue of certification bodies that
hold accreditation from a recognised
national accreditation body (NAB) which
itself is a member of the International
Accreditation Forum (IAF) Multilateral
Recognition Arrangement (MLA).

A body on this list has been independently
verified to have the competence to issue
ISO 27001/27701/42001 certificates.

### What this is not

This is not a quality ranking. Bodies are
either accredited or they aren't — there
is no tier system within this list.

### How it affects scoring

When a body from this list is identified:
- `iso_*_certification_body_accredited =
  TRUE`
- The certificate is treated as valid
  evidence
- Framework modifiers apply normally

When a body is not on this list:
- `iso_*_certification_body_accredited =
  FALSE`
- The certificate is treated as
  unverifiable
- No framework modifier applies — the
  certificate is essentially ignored for
  scoring

This is stricter than the SOC 2 firm
treatment because ISO accreditation is
a binary technical requirement, not a
quality reputation matter. An unaccredited
ISO certificate is not "lower quality" —
it's invalid.

---

## How accreditation works

ISO certification bodies are accredited by
national accreditation bodies (NABs).
National accreditation bodies are members
of the International Accreditation Forum
(IAF), which operates a Multilateral
Recognition Arrangement (MLA) ensuring
mutual recognition between countries.

The chain of trust:

```
IAF MLA
  ↓
National Accreditation Body
  (e.g., ANAB, UKAS, DAkkS)
  ↓
Certification Body
  (e.g., BSI, DNV, TÜV)
  ↓
Certified Organisation
  (e.g., the vendor)
```

If any link in this chain is broken, the
certificate is functionally worthless.

Accreditation is for specific scopes. A
certification body accredited for ISO 27001
may not be accredited for ISO 42001. The
body's own accreditation certificate
specifies what they can certify.

---

## Recognition criteria

A certification body is added to this list
if it meets ALL of the following:

1. Accredited by a national accreditation
   body that is a member of the IAF MLA
2. Has accreditation specifically for the
   ISO standards relevant to Bandit
   (27001, 27701, or 42001)
3. Is in good standing (not currently
   suspended)
4. Has issued certificates to enterprise
   software vendors

Bodies are added based on visible presence
in enterprise ISO certificates. The list
is not exhaustive.

---

## Bodies accredited for ISO 27001

Listed in approximate alphabetical order.
Each entry includes the body's name, common
aliases, and primary accreditation source.

### A2LA-accredited (US)

- **A-LIGN ISO Services**
  Aliases: "A-LIGN Compliance"
  Accreditation: A2LA
  Standards: 27001, 27701

### ANAB-accredited (US/International)

- **BSI Group America**
  Aliases: "BSI", "British Standards
  Institution"
  Accreditation: ANAB, UKAS
  Standards: 27001, 27701, 42001

- **Bureau Veritas Certification**
  Aliases: "Bureau Veritas", "BV"
  Accreditation: ANAB, UKAS, multiple
  Standards: 27001, 27701

- **DEKRA Certification**
  Aliases: "DEKRA"
  Accreditation: ANAB, DAkkS
  Standards: 27001, 27701

- **DNV Business Assurance**
  Aliases: "DNV", "Det Norske Veritas",
  "DNV GL"
  Accreditation: ANAB, multiple
  Standards: 27001, 27701, 42001

- **Eurofins Cyber Security**
  Aliases: "Eurofins"
  Accreditation: ANAB
  Standards: 27001

- **Intertek Group**
  Aliases: "Intertek"
  Accreditation: ANAB, UKAS
  Standards: 27001, 27701

- **LRQA**
  Aliases: "Lloyd's Register Quality
  Assurance", "Lloyd's Register"
  Accreditation: ANAB, UKAS
  Standards: 27001, 27701

- **NQA**
  Aliases: "National Quality Assurance"
  Accreditation: ANAB, UKAS
  Standards: 27001

- **NSF International Strategic
  Registrations**
  Aliases: "NSF-ISR", "NSF"
  Accreditation: ANAB
  Standards: 27001

- **Schellman Compliance LLC**
  Aliases: "Schellman & Co.",
  "Schellman ISO"
  Accreditation: ANAB
  Standards: 27001, 27701

- **SGS North America**
  Aliases: "SGS"
  Accreditation: ANAB, UKAS, multiple
  Standards: 27001, 27701, 42001

- **TÜV Rheinland of North America**
  Aliases: "TÜV Rheinland", "TUV
  Rheinland"
  Accreditation: ANAB, DAkkS
  Standards: 27001, 27701, 42001

- **TÜV SÜD America**
  Aliases: "TÜV SÜD", "TUV SUD"
  Accreditation: ANAB, DAkkS
  Standards: 27001, 27701

- **TÜV USA Inc.**
  Aliases: "TÜV USA"
  Accreditation: ANAB
  Standards: 27001

### UKAS-accredited (United Kingdom)

- **Alcumus ISOQAR**
  Aliases: "ISOQAR", "Alcumus"
  Accreditation: UKAS
  Standards: 27001

- **BSI**
  See above (ANAB section). UKAS is BSI's
  primary home accreditation.

- **Centre for Assessment**
  Aliases: "CfA"
  Accreditation: UKAS
  Standards: 27001

- **NQA**
  See above. UKAS-accredited as well.

- **QMS International**
  Accreditation: UKAS
  Standards: 27001

- **URS UKAS**
  Aliases: "United Registrar of Systems"
  Accreditation: UKAS
  Standards: 27001

### DAkkS-accredited (Germany)

- **DEKRA Certification**
  See above. DAkkS-accredited.

- **DQS GmbH**
  Aliases: "DQS"
  Accreditation: DAkkS, ANAB
  Standards: 27001, 27701

- **TÜV Rheinland**
  See above. DAkkS-accredited.

- **TÜV SÜD**
  See above. DAkkS-accredited.

### JAS-ANZ-accredited (Australia/NZ)

- **BSI Australia**
  Accreditation: JAS-ANZ
  Standards: 27001

- **DNV GL Australia**
  Accreditation: JAS-ANZ
  Standards: 27001

- **SAI Global**
  Accreditation: JAS-ANZ
  Standards: 27001, 27701

- **TÜV SÜD Australia**
  Accreditation: JAS-ANZ
  Standards: 27001

### Other recognised NABs

- **CNAS** (China) — China National
  Accreditation Service
- **JAB** (Japan) — Japan Accreditation
  Board
- **KAB** (Korea) — Korea Accreditation
  Board
- **HKAS** (Hong Kong) — Hong Kong
  Accreditation Service
- **SAC** (Singapore) — Singapore
  Accreditation Council
- **NABCB** (India) — National
  Accreditation Board for Certification
  Bodies

Bodies accredited by these NABs are
recognised through the IAF MLA. Specific
body names from these regions can be added
through community contribution.

---

## Bodies accredited for ISO 27701

ISO 27701 is the privacy extension to ISO
27001. Bodies must be specifically
accredited for 27701 — accreditation for
27001 alone does not extend automatically.

Bodies known to hold 27701 accreditation:

- BSI Group
- Bureau Veritas Certification
- DEKRA Certification
- DNV Business Assurance
- DQS GmbH
- Intertek Group
- LRQA
- SAI Global
- Schellman Compliance LLC
- SGS
- TÜV Rheinland
- TÜV SÜD

A vendor presenting an ISO 27701 certificate
from a body not on this list should be
flagged for additional verification.

---

## Bodies accredited for ISO 42001

ISO 42001 is the AI Management Systems
standard, published 2023. Accreditation is
still rolling out — fewer bodies are
currently accredited for 42001 than for
27001.

Known 42001-accredited bodies:

- BSI Group
- DNV Business Assurance
- DQS GmbH (limited regions)
- SGS
- TÜV Rheinland
- TÜV SÜD

This list is small and growing. A vendor
presenting an ISO 42001 certificate from
a body not currently accredited for 42001
should be flagged. The body may be
accredited for 27001 but not yet for
42001.

---

## Matching logic

When Audit Bandit extracts a certification
body name, the comparison should:

1. Normalise case (lowercase both sides)
2. Strip common legal suffixes:
   "GmbH", "Inc.", "Ltd.", "LLC",
   "Corporation", "Corp.", "AG", "S.A.",
   "Pty Ltd", "Group"
3. Strip "Certification", "Certification
   Services", "ISO Services" suffixes
4. Check exact match first
5. Check substring match second
   (e.g., "bsi" matches "BSI Group" or
   "BSI Group America")
6. Check known aliases
7. If certificate references the
   accreditation number, also verify the
   number format matches the claimed
   NAB pattern (e.g., ANAB numbers,
   UKAS numbers)

Special handling for hyphens, accents, and
special characters:
- "TÜV" / "TUV" / "T?V" — all match
- "DNV GL" / "DNV" — match
- Em-dash, en-dash, hyphen normalised

Do NOT do fuzzy matching beyond aliases.
A name that doesn't clearly match should
return FALSE.

---

## Verification beyond name matching

For higher-confidence verification, the
agent can also extract:

**`accreditation_number`** — the
certificate often states the accreditation
number issued by the NAB to the
certification body. Format examples:
- ANAB: "ANAB Cert No. XXXX"
- UKAS: "UKAS XXX"
- DAkkS: "D-ZM-XXXXX-XX-XX"
- JAS-ANZ: "Accreditation No. XXX"

If the accreditation number is present,
it can be cross-referenced against public
NAB registries. Bandit does not perform
this lookup automatically (would require
API integration with each NAB), but
captures the number for human review.

---

## What to do with unrecognised bodies

If `iso_*_certification_body_accredited =
FALSE`, the report should display:

```
ISO 27001 Certification
Body: [Name]
Status: Body not on Bandit's recognised
        accreditation list

Note: This certificate may not be from an
IAF-accredited body. Without IAF
recognition, this certificate provides
limited assurance value. Verify the body's
accreditation status with the issuing
national accreditation body before
accepting as evidence.

[For US: ANAB Directory of Accredited
Certification Bodies]
[For UK: UKAS Accredited Body Search]
```

This is firmer language than the SOC 2
unrecognised firm note because ISO
accreditation is a binary requirement,
not a reputation matter.

---

## Known unaccredited certificate sources
(do not use)

The following are not on the list and
should never be added:

- Self-issued certificates (the vendor
  certifying themselves)
- Certificates from unaccredited
  consultancies
- "Internal certifications" or "self-
  attestations" labelled as ISO
- Certificates from bodies that have had
  accreditation suspended or withdrawn

If Audit Bandit detects clear indicators
that a certificate is self-issued or from
an unaccredited source, set
`iso_certification_body_unaccredited =
TRUE` regardless of the body name match.

---

## How to contribute

This list is maintained in the open-source
repo. To add a body:

1. Verify the body is currently accredited
   by an IAF-MLA member NAB
2. Confirm the specific ISO standards the
   body is accredited for
3. Submit a pull request with:
   - Body name and aliases
   - Accreditation source
   - Specific standards covered
   - Optional: link to NAB directory entry

Contributions should be evidence-based.
Do not add a body based on reputation
alone.

---

## Periodic maintenance

Accreditation status changes. Bodies can:
- Lose accreditation through enforcement
- Have accreditation suspended
- Add or remove specific standards from
  scope
- Merge or be acquired
- Cease operations

This list should be reviewed annually
against current NAB directories. The
SOC2_FIRMS.md and this file follow the
same maintenance cadence.

---

## Changelog

**v1.0 — 2026-04-22**
Initial list. Approximately 30 bodies
covering the major NAB regions (ANAB,
UKAS, DAkkS, JAS-ANZ) for ISO 27001.
Subset of those bodies for 27701 and
42001 based on current accreditation
scope.

**Planned updates:**
- Annual review against NAB directories
- Community PRs for regional bodies
  (especially CNAS, JAB, KAB, NABCB)
- Tracking of 42001 accreditation
  expansion as more bodies obtain it
