# The Privacy Lens — Privacy Risk Analyzer

> AI-powered vendor privacy policy analysis for compliance teams. Works with Claude, GPT-4o, Gemini, Mistral, and Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built for n8n](https://img.shields.io/badge/Built%20for-n8n-orange)](https://n8n.io)

---

## What It Does

The Privacy Lens automates the review of vendor privacy policies, Data Processing Agreements (DPAs), and AI vendor assessments. It scores each document across 8 risk dimensions (D1–D8) aligned to GDPR, CCPA, and the EU AI Act, then routes results to your existing tools (Google Drive, Jira, Slack).

**Workflows included:**
| File | Purpose |
|------|---------|
| `privacy-policy-analyzer.json` | Full privacy policy intake and scoring |
| `dpa-gap-checker.json` | DPA clause coverage vs. GDPR Art. 28 checklist |
| `ai-vendor-assessment.json` | Specialized scoring for AI/ML vendors (EU AI Act) |

---

## Prerequisites

- [n8n](https://n8n.io) v1.30+ (self-hosted or cloud)
- An AI provider API key — one of:
  - Anthropic (Claude)
  - OpenAI (GPT-4o)
  - Google (Gemini)
  - Mistral AI
  - Ollama (local, no key required)
- Optional: Google Drive, Jira, and/or Slack credentials for output routing

---

## Quick Start

### 1. Install n8n

```bash
# Using npm
npm install -g n8n
n8n start

# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8nio/n8n
```

### 2. Import a Workflow

1. Open n8n at `http://localhost:5678`
2. Click **Workflows → Import from File**
3. Select a JSON file from the `/workflows/` folder
4. Configure your credentials (see [integrations/](integrations/))

### 3. Set Your AI Provider

In each workflow, locate the **AI Model** node and set:
- `provider`: `anthropic` | `openai` | `google` | `mistral` | `ollama`
- `model`: e.g. `claude-opus-4-6`, `gpt-4o`, `gemini-1.5-pro`
- `apiKey`: your provider's API key (stored as an n8n credential)

The prompt in `/prompts/PT-1-privacy-policy-analysis.md` is provider-agnostic and works unchanged across all supported models.

### 4. Run Your First Analysis

Trigger the `privacy-policy-analyzer` workflow with:
```json
{
  "vendor_name": "Acme Corp",
  "policy_url": "https://acme.com/privacy",
  "policy_text": "..."
}
```

Output is a structured JSON risk report. See `/examples/` for sample outputs.

---

## Risk Scoring Framework

Policies are scored across 8 dimensions (D1–D8) on a 1–5 scale. An overall **Privacy Risk Score (PRS)** is calculated as a weighted average. See [`/frameworks/privacy-risk-scoring-rubric.md`](frameworks/privacy-risk-scoring-rubric.md) for full definitions and thresholds.

| Score Range | Risk Level | Recommended Action |
|-------------|------------|-------------------|
| 1.0 – 2.0 | Low | Approve with standard review |
| 2.1 – 3.5 | Medium | Legal review required |
| 3.6 – 4.5 | High | Negotiate DPA amendments |
| 4.6 – 5.0 | Critical | Do not proceed without DPO sign-off |

---

## Repository Structure

```
privacy-risk-analyzer/
├── workflows/
│   ├── privacy-policy-analyzer.json
│   ├── dpa-gap-checker.json
│   └── ai-vendor-assessment.json
├── prompts/
│   └── PT-1-privacy-policy-analysis.md
├── frameworks/
│   └── privacy-risk-scoring-rubric.md
├── integrations/
│   ├── n8n-setup.md
│   ├── google-drive-setup.md
│   ├── jira-setup.md
│   └── slack-setup.md
├── examples/
│   ├── sample-high-risk-output.md
│   └── sample-low-risk-output.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Community prompt contributions and additional workflow templates are very welcome.

## License

MIT — see [LICENSE](LICENSE).
