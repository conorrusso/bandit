# Document Sources Guide

Bandit v1.0 assessed public privacy policies only.
Bandit v1.1 adds support for uploading vendor documents — DPAs, MSAs, SOC 2 reports, BAAs, AI policies, and more.

This unlocks full scoring across all 8 dimensions.

---

## Why documents matter

A privacy policy tells you what a vendor claims.
A DPA tells you what they've committed to contractually.
A SOC 2 report tells you what an auditor independently verified.

These are completely different levels of assurance.

Without the DPA:
- D8 (DPA Completeness) cannot be scored at all
- D2 (Sub-processors) is only partially assessed
- D4 (Transfer Mechanisms) may miss SCC details
- D5 (Breach Notification) misses contractual SLAs

With the DPA:
- D8 fully scored against the GDPR Art. 28(3)(a)-(h) checklist
- D2 complete — sub-processor list, flow-down, audit rights
- D4 complete — SCC module, TIA commitment
- D5 complete — contractual SLA in hours

---

## What each document unlocks

```
Document                  Dimensions unlocked
──────────────────────────────────────────────────────────
Public privacy policy     D1 D3 D6 D7 fully
                          D2 D4 D5 partially
                          D8 not assessed

DPA                       D8 fully (Art.28 checklist)
                          D2 D4 D5 complete scoring

MSA                       D5 (contractual breach liability)
                          D7 (data on termination)
                          D8 (DPA incorporated by reference)

BAA (healthcare)          D5 (HIPAA 60-day timeline)
                          D8 (HIPAA §164.504 provisions)
                          D1 (PHI categories and uses)

SOC 2 Type II             D2 (CC6 logical access attested)
                          D5 (CC7 incident response attested)
                          D7 (data disposal attested)
                          D8 (change management attested)

SOC 1 Type II             D7 (financial data retention)
                          D5 (incident procedures)

ISO 27001 certificate     Framework evidence modifier
                          (+1 to relevant dimensions)

ISO 27701 certificate     Framework evidence modifier
                          (+1 privacy-specific dimensions)

ISO 42001 certificate     D6 (AI management attested)

AI Policy                 D6 fully (training, opt-out,
                          EU AI Act, human oversight)

Model Card                D6 (training data sources,
                          personal data in training,
                          opt-out mechanism)

Sub-processor List        D2 (named processors, countries,
                          last updated date)

TIA                       D4 (transfer mechanism,
                          supplementary measures,
                          surveillance law assessed)

PCI AOC                   Financial profile: PCI compliance
                          D7 (cardholder data retention)

HITRUST                   Healthcare profile: framework
                          evidence modifier

FedRAMP ATO               Government profile: authorization
                          level and scope
```

---

## Supported file formats

```
Format    Extension    Notes
──────────────────────────────────────────────────────────
PDF       .pdf         Most compliance docs. Must have
                       text layer — scanned PDFs cannot
                       be read (OCR coming in v1.2)
Word      .docx .doc   Many DPAs come as Word docs.
                       Tables extracted (DPA checklists)
HTML      .html .htm   Privacy policies, web pages
Text      .txt .md     Plain text policies, guidelines
JSON      .json        Model cards, structured data
```

Not supported: `.xlsx` `.csv` `.zip` `.png` `.jpg` (images)

---

## How document type detection works

Bandit identifies document types in three passes:

**Pass 1 — Filename (instant, free)**
Looks for keywords in the filename:
```
dpa                       → DPA
soc2, soc-2               → SOC 2 Type II
iso27001, 27001           → ISO 27001
baa, business-associate   → BAA
ai-policy, responsible-ai → AI Policy
sub-processor, subprocessors → Sub-processor List
```

**Pass 2 — Content keywords (fast, free)**
Scans first 3,000 characters for known phrases:
```
"article 28", "processor shall"     → DPA
"trust service criteria", "aicpa"   → SOC 2
"business associate", "protected health" → BAA
"responsible ai", "training data"   → AI Policy
```

**Pass 3 — AI classification (only if passes 1 & 2 fail)**
Sends first 2,000 chars to your configured LLM.
Costs approximately 200 tokens.
Used rarely — most documents are identified in passes 1 or 2.

You can override automatic detection with a renamed file — for example, renaming `agreement.pdf` to `dpa.pdf` ensures it is classified as a DPA in pass 1.

---

## How signal merging works

When multiple documents are assessed, signals are merged into a unified evidence set:

1. Public privacy policy signals extracted first
2. Each document's signals extracted separately
3. Signals merged using this logic:
   - If signal not in policy → add from document
   - If signal in policy and document confirms → keep
   - If signal in document is stronger → upgrade
   - If document contradicts policy → flag both, use stronger commitment

**Example:**
```
Privacy policy says: breach notification "promptly"
DPA says: breach notification within 48 hours

Result: D5 signal d5_breach_sla_hours = 48
Source: dpa.pdf §8.2 (stronger commitment wins)
```

The HTML report shows the source of every signal so you know exactly which document provided each piece of evidence.

---

## Local folder setup

Create a folder on your machine:

```
vendor-docs/
├── Salesforce/
│   ├── dpa.pdf
│   ├── msa.pdf
│   └── soc2-2025.pdf
├── HubSpot/
│   └── dpa.pdf
└── NetSuite/
    ├── dpa.pdf
    └── soc1-2025.pdf
```

File names don't matter — Bandit auto-detects types.

**Single vendor:**
```bash
bandit assess "Salesforce" --docs ./vendor-docs/Salesforce/
```

**Batch — auto-matches vendor name to subfolder:**
```bash
bandit batch vendors.txt --docs-root ./vendor-docs/
```

**Pre-specify per vendor in vendors.txt:**
```
Salesforce,,customer_data,./docs/salesforce/
NetSuite,,financial_processing,./docs/netsuite/
HubSpot
```

---

## Google Drive setup

See [docs/google-drive-setup.md](google-drive-setup.md) for full instructions.

```bash
# One-time setup
bandit setup --drive

# Use Drive for assessment
bandit assess "Salesforce" --drive

# Use Drive for batch
bandit batch vendors.txt --drive
```

---

## When to use local vs Drive

| | Local folder | Google Drive |
|--|--|--|
| Setup | None — just create folders | One-time OAuth setup |
| Best for | Quick assessments, offline, Ollama | Teams, scheduled batches |
| Air-gapped | Yes (with Ollama) | No |
| Auto-discover | Manual folder path | Automatic by vendor name |
| Save reports | Local ./reports/ | Back to Drive vendor folder |
| Team access | No | Yes |

Both options feed into the same pipeline. The scoring is identical regardless of source.

---

## Scanned PDFs

PDFs without a text layer cannot be read by Bandit. This includes PDFs that are photographs of documents or PDFs created by scanning physical paper.

Bandit detects this and shows:
```
✗ soc2-report.pdf — Scanned PDF detected.
  Text extraction failed. Use a text-based PDF.
```

To fix: ask your vendor for a native PDF version (not a scan). Most vendors have text-based versions of their compliance documents.

OCR support for scanned PDFs is planned for v1.2.

---

## Document manifest

Before running the assessment, Bandit shows a manifest of all documents found:

```
Documents found in ./vendor-docs/Salesforce/

dpa.pdf               DPA              94%    ✓ Ready
msa.pdf               MSA              88%    ✓ Ready
soc2-2025.pdf         SOC 2 Type II    91%    ✓ Ready
old-scan.pdf          —                —      ✗ Failed

3 ready · 1 failed

✗ old-scan.pdf: Scanned PDF — text extraction failed
```

If a document fails or is unknown type, assessment continues with the remaining documents. A single bad file never blocks the assessment.
