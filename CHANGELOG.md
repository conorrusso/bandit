# Changelog

All notable changes to Bandit are documented here.

Format: `Added` new features · `Changed` behaviour or UX · `Fixed` bugs · `Removed` deleted code · `Security` vulnerability fixes

---

## [Unreleased]

---

## 2026-03-29

### Security — `53e54e6`
- **Atomic file writes** — history, cache, and setup progress files now write to a `.tmp` then atomically rename via `os.replace()`. Previously a crash or concurrent run mid-write could leave a truncated or empty JSON file, silently corrupting vendor history, the domain cache, or setup progress.
- **SSRF prevention** — added `_is_safe_url()` in `core/tools/discover.py` that blocks requests to loopback addresses (`127.x`, `localhost`), RFC-1918 private ranges (`10.x`, `192.168.x`, `172.x`), and cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`). Applied at `head_request()` and `_tiny_get()`, which all network fetches flow through.
- **Exception narrowing** — `_load_history()` and `_load_cache()` changed from bare `except Exception` to `except (OSError, json.JSONDecodeError)`. `_save_cache()` gained a missing `try/except OSError` — previously an unhandled `OSError` (e.g. disk full) would crash an in-progress assessment.

### Removed — `8c0610c`
- Deleted `legacy/` directory (11 files, 2,418 lines) — the original n8n workflow prototype. Superseded entirely by the Bandit CLI. Local backup retained.

### Fixed — `a307d8e`
- `LICENSE`: copyright holder updated from `The Privacy Lens Contributors` to `Bandit Contributors`.
- `legacy/n8n/bandit-privacy.json`: CSS header string `◄ THE PRIVACY LENS ►` updated to `◄ BANDIT ►`.

### Changed — `3b2b3db`
- `bandit setup` section 6 fully rewritten to match spec:
  - `_ask_cadence()` — shows preset options per tier (HIGH: 6 months–2 years, MEDIUM: 1–5 years, LOW: 1 year–never) plus free-text custom day input. Defaults: HIGH=1 year, MEDIUM=2 years, LOW=one-time.
  - `_ask_triggers()` — shows all trigger options with `◉`/`◯` indicating per-tier defaults (HIGH: policy + breach + regulatory; MEDIUM: policy + breach; LOW: breach only). Enter accepts defaults; entering numbers replaces selection entirely; "Manual trigger only" returns empty list.
  - `_days_label()` — converts day counts to human-readable strings (`365` → `Every year`, `912` → `Every ~2 years`, `0` → `One time / on change`).
  - Confirmation screen now shows a reassessment schedule table with human-readable cadence and grouped trigger display.
  - `bandit setup --show` updated with same depth labels and cadence display.

### Added — `4db4088`
- Per-tier reassessment cadence replacing the single `reassess_cycle` setting. For each of HIGH, MEDIUM, LOW: configurable depth (`full` / `lightweight` / `scan` / `none`), cadence in days, and out-of-cycle triggers.
- `core/config.py`: `get_reassessment_config()` returns per-tier config with defaults. `write_config()` accepts `reassessment=` param and writes a top-level `reassessment:` YAML block. `_load_yaml_simple()` extended to handle 3-level nesting.
- `cli/report.py`: GRC section now reads config-driven cadence, shows assessment depth, re-assess date with cadence annotation, and active out-of-cycle triggers.
- `cli/main.py`: `--force` flag. Vendor history persisted to `~/.bandit/vendor-history.json` after each assessment. Cadence check warns and exits early if reassessment is not due; skips entirely for `depth: none`; bypassed with `--force`.

### Added — `ac42d6e`
- Setup wizard progress saved after every question to `~/.bandit/.setup_progress.json`. On next run, wizard offers to resume from last completed question or start over.
- `Ctrl+C` during setup prints `Setup paused at Q{n}/26. Run bandit setup to resume.` instead of crashing.
- `--reset` clears saved progress alongside the config file.

### Fixed — `6665672`
- Setup wizard crash on Q17 when user selected "Annual" or "On-change only" — `int("Annual")` raised `ValueError`. Fixed with index-based option map instead of string parsing. Same pattern applied to `risk_appetite` and `maturity` questions.

### Added — `2f905ca`
- Assessment scope honesty: D8 (DPA Completeness) excluded from the weighted average when only the public privacy policy is available. D2, D4, D5 flagged as partially assessed. Scope bar shown in HTML report header. `--dpa` placeholder flag added to `bandit assess`.

### Added — `f62a335`
- `bandit setup` — 26-question wizard that calculates dimension weights based on regulatory environment and data risk profile. Saves to `bandit.config.yml`. Supports `--reset` and `--show`. Profile label and modified weights displayed in terminal and HTML report header.
- `core/config.py` — `load_config()`, `get_weights()`, `calculate_weights()`, `is_auto_escalate()`, `get_profile_label()`, `write_config()`.

---

## 2026-03-29 (earlier)

### Added — `fcad860`
- v1.0 CLI: `bandit assess`, `bandit rubric`, `bandit batch`. HTML reports saved to `./reports/`. Input auto-detection (company name / domain / URL). `--json`, `--verbose`, `--no-report` flags. Batch mode with `--out` directory and progress bar.

### Added — `6bd00d0`
- Rich welcome screen (`bandit` with no args). `bandit rubric` command with per-dimension detail view (`--dim D5`). Terminal renderer with colour-coded scores, scope indicators, and escalation banners.

### Added — `f8849cb`
- HTML report: sources footer, matched signals per dimension, per-dimension detail sections with evidence, gaps, red flags, contract recommendations, team summary panels (GRC / Legal / Security), vendor email template.

---

## 2026-03-28

### Added — `d860d5ef`
- Privacy Bandit agent — full LLM → extract → score pipeline. Anthropic Claude integration via `AnthropicProvider`. 8-dimension rubric scoring engine with red flags, signal matching, and weighted average.

### Added — `4243769`
- Auto-load `config.env` for `ANTHROPIC_API_KEY` — no export required.

### Fixed — `3e3e7ab`
- JS-rendered page fallback via Jina Reader when direct fetch returns insufficient content.

---

## 2026-03-27

### Added — `a46e5dc`
- v1.0 architecture: Python agent core, staged discovery engine (DuckDuckGo → HEAD probe → AI fallback → homepage scrape), rubric engine, Click CLI scaffold, Rich terminal output.

---

## 2026-03-26

### Changed — `b6d84ab`
- Project renamed from **The Privacy Lens** to **Bandit** across all files, docs, and workflows.

### Added — `10640aa`
- Landing page (`docs/index.html`) deployed to GitHub Pages. `CLAUDE.md` deploy instructions.
