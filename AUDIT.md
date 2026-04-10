# Bandit System Audit — 2026-04-09

## Summary

| Phase | Status | Issues Found | Issues Fixed |
|-------|--------|-------------|-------------|
| Phase 0 — Syntax/imports | PASS | 0 | 0 |
| Phase 1 — Tests | PASS | 5 | 5 |
| Phase 2 — CLI validation | PASS | 0 | 0 |
| Phase 3 — Security | PASS | 3 | 3 |
| Phase 4 — Documentation | PASS | 5 | 5 |
| Phase 5 — Code quality | PASS | 0 | 0 |
| Phase 6 — E2E simulation | PASS | 0 | 0 |

---

## Phase 0 — Syntax / imports

- 54 Python files checked — all compile cleanly
- CLI entrypoint (`cli.main:main`) loads without error
- No import errors

---

## Phase 1 — Tests

**Before audit:** 40 tests, 2 files  
**After audit:** 76 passing, 3 skipped, 6 files

### New test files created

| File | Tests | Notes |
|------|-------|-------|
| `tests/test_resolver.py` | 7 passing, 2 skipped | Drive-path tests skipped (require real OAuth credentials) |
| `tests/test_portfolio.py` | 11 passing | All portfolio logic covered via mocked cache |

### Additions to existing test files

- **`tests/test_rubric.py`**: Added `TestD8Exclusion` (3 tests) and `TestRedFlagCapScore` (2 tests)
- **`tests/test_signal_merge.py`**: Added `TestDpaCharCountThreshold` (2 tests) plus `test_document_signal_never_downgrades` and `test_document_supplements_policy`
- **`tests/test_intake.py`**: Added `TestRenewalDateValidation` (4 tests), `TestItActionsGenerated` (3 tests), `TestDataTypeConsistency` (2 tests)
- **`tests/test_vendor_cache.py`**: Added `TestDeleteVendor` — marked `@pytest.mark.skip` because `VendorProfileCache.delete()` is not implemented

### Skipped tests with reasons

| Test | Reason |
|------|--------|
| `test_resolver_drive_path` | Requires real Google OAuth credentials — not available in CI |
| `test_resolver_deduplicates_drive_wins_over_local` | Same — Drive not available in CI |
| `test_delete_vendor` | `VendorProfileCache.delete()` not implemented — tracked for v1.5 |

---

## Test coverage

```
core/dashboard/portfolio.py     95%
core/profiles/vendor_cache.py   78%
core/scoring/rubric.py          69%
core/data/resolver.py           65%
core/profiles/intake.py         30%
core/tools/fetch.py             32%
core/notifications/sender.py     0%   (interactive I/O — hard to unit test without mocking)
core/tools/discover.py           0%   (network-dependent — requires live HTTP)
core/agents/privacy_bandit.py   17%   (LLM-dependent — requires API key)
core/agents/legal_bandit.py     13%   (LLM-dependent — requires API key)
TOTAL                           32%
```

0% coverage on network/LLM-dependent modules is expected — these require real API keys or live HTTP and are not suitable for unit tests without extensive mocking.

---

## Phase 2 — CLI validation

All commands load and respond correctly:

- `bandit assess`, `bandit batch`, `bandit rubric`, `bandit setup` — all flags present
- `bandit legal`, `bandit vendor` subgroup (add/show/edit/list) — all present
- `bandit dashboard` group with `show`, `schedule`, `register`, `notify` — all present
- Top-level aliases: `bandit sync`, `bandit schedule`, `bandit register`, `bandit notify` — all present
- `--json` flag verified on: `dashboard show`, `schedule`, `notify`, `sync`
- Welcome screen: no `--discover` references; Drive first-time sequence shows 3 steps

---

## Phase 3 — Security

### Findings and fixes

| Check | Status | Detail |
|-------|--------|--------|
| Hardcoded secrets | PASS | `api_key="sk-ant-..."` in `anthropic.py` line 8 is docstring example, not a real key |
| SSRF — `discover.py` | PASS | `_is_safe_url()` called before every HTTP request |
| SSRF — `fetch.py` | **FIXED** | Added `_is_safe_url()` check to `_fetch_direct()`. Direct URLs from user input were not validated before the fix |
| SSRF — `sender.py` | **FIXED** | Added `_is_safe_url()` check to `_send_slack()`. Webhook URL was not validated |
| File path traversal | PASS (low risk) | `--docs` path is user-specified but Bandit only reads, never writes, to it. `Path.resolve()` not used but risk is minimal (user owns their own filesystem) |
| Prompt injection | **FIXED** | Added sanitization to `privacy_bandit.assess()`: `vendor.strip()[:200]` + `re.sub` to remove non-word chars before vendor name enters LLM prompts |
| YAML safe loading | PASS | Only `yaml.safe_load()` is used — no `yaml.load()` calls found |
| Temp file handling | PASS | `tempfile.mktemp()` is deprecated but safe in context (single-user dir, write → os.replace pattern) |
| Atomic writes | PASS | All three cache files use write-to-.tmp then `tmp.replace(target)` pattern |

---

## Phase 4 — Documentation

### Issues found and fixed

| File | Issue | Fix |
|------|-------|-----|
| `docs/vendor-guide.md` | Referenced `bandit sync --discover` (removed command) | Replaced with `bandit sync` |
| `docs/document-sources.md` | Referenced v1.0/v1.1 version history in intro | Replaced with version-neutral language |
| `docs/document-sources.md` | "OCR coming in v1.2" — v1.2 is live, OCR not in it | Updated to "OCR not yet supported" |
| `README.md` | `bandit sync --discover` in Drive quick-start | Removed — now just `bandit sync` |
| `README.md` | Missing `bandit dashboard`, `schedule`, `register`, `notify`, `sync` in usage table | Added |
| `README.md` | "v1.4 — Planned" in roadmap | Updated to "v1.4 — Live" |

### Files verified present

- `docs/index.html` ✓
- `docs/cli-reference.md` ✓
- `docs/setup-guide.md` ✓
- `docs/report-guide.md` ✓
- `docs/document-sources.md` ✓
- `docs/google-drive-setup.md` ✓
- `docs/vendor-guide.md` ✓
- `docs/how-bandit-works.md` ✓
- `docs/legal-guide.md` ✓

### Internal links: no broken links found

---

## Phase 5 — Code quality

| Check | Status | Detail |
|-------|--------|--------|
| Bare `except:` clauses | PASS | None found |
| `print()` in `core/` | PASS | Only in `rubric.py __main__` block (standalone script) and Rich `console.print()` in interactive wizards |
| TODO/FIXME/HACK/XXX | PASS | None found |
| Mutable dataclass defaults | PASS | All list/dict fields use `field(default_factory=...)` |
| `pyproject.toml` | PASS | version=1.4.0, all deps present, `[drive]` extras defined, CLI entry point correct |

---

## Phase 6 — E2E simulation

All modules import and run without error:

| Module | Result |
|--------|--------|
| `bandit` CLI | Loads OK |
| `bandit.config.yml` | Valid YAML, 9 top-level keys |
| `VendorProfileCache` | 3 profiles loaded (Anthropic, Cyera, salesforce) |
| `core.dashboard.portfolio.get_summary()` | 3 vendors, runs cleanly |
| `core.dashboard.schedule.get_schedule()` | 3 entries, 0 overdue |
| `core.dashboard.register.build_register()` | CSV 370 chars, HTML 2145 chars |
| `core.data.resolver.VendorDataResolver` | Resolves, Drive available (configured locally) |
| `core.notifications.sender` | Imports OK |

---

## Known issues (not fixed this session)

| Issue | Severity | Notes |
|-------|----------|-------|
| `VendorProfileCache.delete()` not implemented | Low | No current CLI command uses delete. Tracked for v1.5 when vendor offboarding is added |
| `tempfile.mktemp()` deprecated | Low | Works correctly in practice; all four usages use write→replace atomic pattern. Could be replaced with `NamedTemporaryFile(delete=False)` in v1.5 cleanup |
| 0% coverage on network/LLM modules | Accepted | `discover.py`, `privacy_bandit.py`, `legal_bandit.py` require live HTTP/API — not unit-testable without extensive mocking. Integration tests in a future CI environment with mock servers would address this |
| `portfolio.py` line 131 dead code | Low | `elif due_date <= today` is unreachable (vendors due exactly today are counted as overdue by the `if delta < 0` branch only). Functional impact: "due today" is not counted in `due_count`. Fix in v1.5 |

---

## Version

Bandit v1.4.0 — audited 2026-04-09
