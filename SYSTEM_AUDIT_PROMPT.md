# Bandit — Full System Audit
# Comprehensive review of everything built in v1.0–v1.4.
# Tests, security scan, workflow validation,
# documentation audit, and fix report.
#
# DO NOT add new features. This session is audit only.
# Fix what is broken. Document what cannot be fixed.
# Complete each phase fully before starting the next.

═══════════════════════════════════════════════════════════
PHASE 0 — Read everything first
═══════════════════════════════════════════════════════════

Before doing anything else, run these commands and
read the output carefully. This is your ground truth.

0A. Project structure
  find . -type f -name "*.py" \
    | grep -v __pycache__ \
    | grep -v ".egg-info" \
    | sort

0B. Current version
  grep "version" pyproject.toml

0C. Git log — what was built
  git log --oneline -30

0D. Read CHANGELOG.md fully

0E. Check for import errors across all Python files
  python3 -c "
  import subprocess, sys
  from pathlib import Path
  errors = []
  for f in sorted(Path('.').rglob('*.py')):
      if '__pycache__' in str(f): continue
      if '.egg-info' in str(f): continue
      result = subprocess.run(
          ['python3', '-m', 'py_compile', str(f)],
          capture_output=True, text=True
      )
      if result.returncode != 0:
          errors.append(f'{f}: {result.stderr.strip()}')
  if errors:
      print('SYNTAX ERRORS FOUND:')
      for e in errors: print(e)
  else:
      print('All Python files compile cleanly.')
  "

0F. Check all CLI commands load without error
  python3 -c "from cli.main import cli; print('CLI loads OK')"

Fix any import or syntax errors found before
proceeding to Phase 1.

═══════════════════════════════════════════════════════════
PHASE 1 — Automated tests
═══════════════════════════════════════════════════════════

1A. Install test dependencies
  pip install pytest pytest-cov --break-system-packages

1B. Check what test files already exist
  ls tests/

1C. Run existing tests
  python3 -m pytest tests/ -v --tb=short 2>&1

1D. For any test file that does not exist yet,
create it. Required test files:

── tests/test_rubric.py ────────────────────────────────
If missing or incomplete, write tests covering:

def test_risk_tier_high():
    # weighted_average < 2.5 → HIGH
    assert risk_tier_from_score(2.4) == "HIGH"

def test_risk_tier_medium():
    # 2.5 to 3.5 → MEDIUM
    assert risk_tier_from_score(3.0) == "MEDIUM"

def test_risk_tier_low():
    # > 3.5 → LOW
    assert risk_tier_from_score(3.6) == "LOW"

def test_risk_tier_boundary_high_medium():
    # 2.5 is MEDIUM not HIGH (boundary exclusive)
    assert risk_tier_from_score(2.5) == "MEDIUM"

def test_d8_excluded_without_dpa():
    # D8 excluded from weighted average when no DPA
    # Score should be calculated over 7 dimensions
    pass  # implement using rubric.py scoring engine

def test_red_flag_caps_score():
    # "appropriate measures" in D8 signals caps score <= 3
    pass

def test_score_1_all_signals_absent():
    # Empty evidence dict → score 1 on all dimensions
    pass

def test_score_5_all_signals_present():
    # All positive signals → score 5
    pass

── tests/test_signal_merge.py ──────────────────────────
If missing or incomplete:

def test_document_signal_never_downgrades():
    # Document signal False should not replace
    # policy signal True
    pass

def test_dpa_char_count_threshold():
    # DPA < 5000 chars → D8 excluded
    # DPA >= 5000 chars → D8 included
    pass

def test_document_supplements_policy():
    # Document signal adds to policy signals
    # without replacing them
    pass

── tests/test_intake.py ────────────────────────────────
If missing or incomplete:

def test_data_type_consistency_phi_clinical():
    # healthcare_clinical integration without phi
    # in data_types → should flag mismatch
    pass

def test_renewal_date_validation_valid():
    assert validate_renewal_date("06/2027") == "06/2027"

def test_renewal_date_validation_invalid():
    assert validate_renewal_date("2027-06") is None

def test_it_actions_generated_for_identity():
    # identity_access integration → SSO actions generated
    pass

── tests/test_vendor_cache.py ──────────────────────────
If missing or incomplete:

def test_save_and_retrieve_profile():
    # Save profile, retrieve by name, all fields match
    pass

def test_update_assessment_history():
    # Empty history → add entry → history has 1 item
    pass

def test_history_max_10_entries():
    # 10 existing entries → add one more → still 10
    pass

def test_delete_vendor():
    # Save vendor → delete → get returns None
    pass

── tests/test_resolver.py ──────────────────────────────
If missing or incomplete:

def test_resolver_local_only():
    # No Drive configured → resolve() returns local docs
    pass

def test_resolver_deduplicates():
    # Same filename in local and drive →
    # Drive version wins, only one doc returned
    pass

def test_resolver_missing_vendor():
    # Vendor with no profile → resolve() returns
    # empty result, no crash
    pass

── tests/test_portfolio.py ─────────────────────────────
If missing or incomplete:

def test_get_summary_empty():
    # No vendors → PortfolioSummary with zeros
    pass

def test_risk_distribution():
    # 2 HIGH, 1 MEDIUM, 1 LOW profiles →
    # distribution matches
    pass

def test_overdue_detection():
    # Vendor with next_due in the past → overdue=True
    pass

def test_offboarded_excluded():
    # Vendor with status=offboarded → not in dashboard
    pass

1E. Run all tests
  python3 -m pytest tests/ -v --tb=short

  All tests must pass. Fix any failures before
  proceeding to Phase 2.
  
  If a test cannot be fixed, mark it @pytest.mark.skip
  with a comment explaining why. Do not delete tests.

1F. Run with coverage
  python3 -m pytest tests/ --cov=core --cov-report=term-missing

  Report coverage percentage. Note any core modules
  with 0% coverage.

═══════════════════════════════════════════════════════════
PHASE 2 — CLI workflow validation
═══════════════════════════════════════════════════════════

Validate that every command loads and responds
correctly. Use --help to verify flags are wired up.
Do not run commands that require API keys or Drive.

2A. Core commands
  bandit --help
  bandit assess --help
  bandit batch --help
  bandit rubric --help
  bandit setup --help
  bandit setup --help | grep -E "stack|notify|drive|show|reset"
  bandit legal --help

2B. Vendor commands
  bandit vendor --help
  bandit vendor add --help
  bandit vendor show --help
  bandit vendor edit --help
  bandit vendor list --help

2C. Dashboard commands
  bandit dashboard --help
  bandit dashboard show --help
  bandit dashboard schedule --help
  bandit dashboard register --help
  bandit dashboard notify --help

2D. Top-level aliases
  bandit sync --help
  bandit schedule --help
  bandit register --help
  bandit notify --help

2E. Verify --json flag exists on these commands
  bandit dashboard show --help | grep json
  bandit schedule --help | grep json
  bandit notify --help | grep json
  bandit sync --help | grep json

2F. Check welcome screen
  bandit
  Verify all commands are listed.
  Verify WORKFLOWS section shows Drive sequence.
  Verify no commands reference --discover.

Report any command that fails to load or is missing
expected flags. Fix them.

═══════════════════════════════════════════════════════════
PHASE 3 — Security audit
═══════════════════════════════════════════════════════════

3A. Hardcoded secrets scan
  grep -rn \
    "api_key\|API_KEY\|sk-\|Bearer\|password\|secret\|token" \
    --include="*.py" --include="*.yml" --include="*.yaml" \
    . --exclude-dir=.git --exclude-dir=__pycache__

  Expected: No hardcoded secrets. API keys should
  only come from environment variables or config files.
  
  Grep for placeholder values too:
  grep -rn "YOUR_API_KEY\|YOUR_KEY\|PLACEHOLDER\|changeme" \
    --include="*.py" --include="*.yml" . --exclude-dir=.git

3B. SSRF protection check
  grep -rn "requests.get\|httpx.get\|urllib.request" \
    --include="*.py" . --exclude-dir=.git

  For each HTTP call found:
  - Is the URL user-controlled?
  - Is _is_safe_url() called before the request?
  - Is there a timeout?
  
  Check that core/tools/discover.py still has
  _is_safe_url() blocking:
  - 127.x, localhost
  - 10.x, 192.168.x, 172.16.x-31.x
  - 169.254.169.254 (cloud metadata)

3C. File path traversal check
  grep -rn "open(\|Path(" --include="*.py" . \
    --exclude-dir=.git --exclude-dir=__pycache__ \
    | grep -v "test_\|#"

  For any path that comes from user input:
  - Is path.resolve() used?
  - Is the resolved path checked against allowed dirs?

3D. Prompt injection check
  grep -rn "vendor_name\|domain\|company" \
    --include="*.py" . --exclude-dir=.git \
    | grep -i "prompt\|message\|content" \
    | grep -v "test_\|#"

  Wherever vendor_name is interpolated into LLM prompts:
  - Is it sanitised before injection?
  - Add sanitisation where missing:
    vendor_name = vendor_name.strip()[:200]
    vendor_name = re.sub(r'[^\w\s\-\.\(\)]', '', vendor_name)

3E. YAML safe loading check
  grep -rn "yaml.load\b" --include="*.py" . \
    --exclude-dir=.git

  Any yaml.load() without Loader=yaml.SafeLoader
  is a vulnerability. Change to yaml.safe_load().

3F. Temporary file handling check
  grep -rn "tempfile\|/tmp\|TemporaryDirectory" \
    --include="*.py" . --exclude-dir=.git

  Verify temp dirs are created with tempfile.mkdtemp()
  or used as context managers. Verify cleanup happens.

3G. Atomic write verification
  grep -rn "os.replace\|\.tmp" --include="*.py" . \
    --exclude-dir=.git

  Verify vendor-profiles.json, vendor-history.json,
  and .setup_progress.json all use atomic writes
  (write to .tmp then os.replace).

3H. Generate security summary

  SECURITY AUDIT RESULTS
  ══════════════════════════════════════
  Hardcoded secrets:     PASS / ISSUES: [list]
  SSRF protection:       PASS / ISSUES: [list]
  File path traversal:   PASS / ISSUES: [list]
  Prompt injection:      PASS / ISSUES: [list]
  YAML safe loading:     PASS / ISSUES: [list]
  Temp file handling:    PASS / ISSUES: [list]
  Atomic writes:         PASS / ISSUES: [list]

  Fix all ISSUES before proceeding to Phase 4.

═══════════════════════════════════════════════════════════
PHASE 4 — Documentation audit
═══════════════════════════════════════════════════════════

4A. Check all docs exist
  ls docs/
  
  Required files:
  - index.html          ✓ website
  - cli-reference.md    ✓ command reference
  - setup-guide.md      ✓ setup wizard guide
  - report-guide.md     ✓ how to read reports
  - document-sources.md ✓ document pipeline guide
  - google-drive-setup.md ✓ Drive integration
  - vendor-guide.md     ✓ vendor intelligence guide
  - how-bandit-works.md ✓ architecture explainer
  - legal-guide.md      ✓ Legal Bandit guide
  
  Report any missing files.

4B. Stale content scan
  grep -rn \
    "v1\.0 this is\|v1\.1 will enable\|COMING SOON\|Coming Soon\|last 5 entries\|--discover" \
    docs/ --include="*.md" --include="*.html"
  
  Expected: nothing found. Fix any matches.

4C. Version consistency check
  grep -rn "1\.[0-3]\.0\|v1\.[0-3]" \
    docs/ --include="*.md" \
    | grep -v "CHANGELOG\|changelog\|history"
  
  Docs should reference current version (1.4.0).
  Update any stale version references.

4D. Broken internal links check
  python3 -c "
  import re
  from pathlib import Path
  
  docs = Path('docs')
  md_files = list(docs.glob('*.md'))
  broken = []
  
  for f in md_files:
      text = f.read_text()
      # Find markdown links [text](target)
      links = re.findall(r'\[.*?\]\((.*?)\)', text)
      for link in links:
          # Skip external links and anchors
          if link.startswith('http') or link.startswith('#'):
              continue
          # Check internal file links
          target = docs / link
          if not target.exists():
              broken.append(f'{f.name} → {link}')
  
  if broken:
      print('BROKEN LINKS:')
      for b in broken: print(f'  {b}')
  else:
      print('No broken internal links found.')
  "

4E. Check website (docs/index.html)
  Check these specific things:
  
  grep -c "LIVE" docs/index.html
  # Should be >= 4 (v1.0, v1.1, v1.2, v1.3)
  
  grep "v1.4" docs/index.html
  # Should show v1.4 in roadmap as PLANNED
  
  grep -c "dispatch-section\|marquee" docs/index.html
  # Should be > 0 (dispatch console present)
  
  grep "bandit-raccoon" docs/index.html
  # Should reference the mascot PNG
  
  grep "DM Sans\|Press Start 2P\|JetBrains Mono" docs/index.html
  # Should have all three fonts

4F. README.md completeness check
  Check README.md has:
  - bandit sync documented
  - bandit dashboard documented
  - bandit schedule documented
  - bandit register documented
  - bandit notify documented
  - v1.4 in the roadmap section
  - Google Drive quick start sequence

  grep -E "bandit sync|bandit dashboard|bandit schedule|\
bandit register|bandit notify|v1.4|bandit setup --drive" \
    README.md

  Add any missing sections.

4G. CHANGELOG.md check
  head -30 CHANGELOG.md
  
  Should show [1.4.0] as the top entry.
  All versions 1.0 through 1.4 should be present.

═══════════════════════════════════════════════════════════
PHASE 5 — Code quality checks
═══════════════════════════════════════════════════════════

5A. Check for bare except clauses
  grep -rn "except:" --include="*.py" . \
    --exclude-dir=.git --exclude-dir=__pycache__
  
  Bare except catches SystemExit and KeyboardInterrupt.
  Change any bare except to except Exception.

5B. Check core/ has no print statements
  grep -rn "^[^#]*print(" core/ \
    --include="*.py" \
    --exclude-dir=__pycache__
  
  Expected: nothing in core/. All output belongs in cli/.
  Move any print() calls found to the appropriate cli/
  function via return value or callback.

5C. Check for TODO/FIXME/HACK comments
  grep -rn "TODO\|FIXME\|HACK\|XXX" \
    --include="*.py" . --exclude-dir=.git \
    --exclude-dir=__pycache__
  
  List all found. Fix critical ones. Document the rest.

5D. Check dataclass field defaults
  grep -rn "field(default_factory" \
    core/profiles/vendor_cache.py core/data/resolver.py \
    core/dashboard/
  
  Mutable defaults (lists, dicts) in dataclasses must
  use field(default_factory=list) not = [].
  Fix any found.

5E. Check pyproject.toml is complete
  cat pyproject.toml
  
  Verify:
  - version = "1.4.0"
  - All required dependencies present
  - Optional [drive] extras defined
  - CLI entry point defined

═══════════════════════════════════════════════════════════
PHASE 6 — End-to-end workflow simulation
═══════════════════════════════════════════════════════════

Simulate the full workflow without API keys or Drive.
Use mock/dry-run where real services are needed.

6A. Fresh install simulation
  pip install -e . --quiet
  bandit --version 2>/dev/null || bandit --help | head -3
  
  Verify install completes without errors.

6B. Config file validation
  cat bandit.config.yml 2>/dev/null \
    || echo "No config file — expected after setup"
  
  If config exists, validate YAML:
  python3 -c "
  import yaml
  with open('bandit.config.yml') as f:
      config = yaml.safe_load(f)
  print('Config valid. Top-level keys:', list(config.keys()))
  "

6C. Profile cache validation
  python3 -c "
  from core.profiles.vendor_cache import VendorProfileCache
  cache = VendorProfileCache()
  profiles = cache.list_all()
  print(f'Profiles loaded: {len(profiles)}')
  for p in profiles:
      print(f'  {p.vendor_name}: status={getattr(p, \"status\", \"active\")}')
  "

6D. Portfolio summary without Drive
  python3 -c "
  from core.dashboard.portfolio import get_summary
  s = get_summary()
  print(f'Total vendors: {s.total_vendors}')
  print(f'Risk distribution: HIGH={s.risk_distribution.high} MEDIUM={s.risk_distribution.medium} LOW={s.risk_distribution.low}')
  print(f'Drive vendors: {s.drive_vendors}')
  print('Portfolio module: OK')
  "

6E. Schedule without Drive
  python3 -c "
  from core.dashboard.schedule import get_schedule
  s = get_schedule()
  print(f'Schedule entries: {len(s.entries)}')
  print(f'Overdue: {s.overdue_count}')
  print('Schedule module: OK')
  "

6F. Register export
  python3 -c "
  from core.dashboard.register import build_register
  r = build_register()
  csv = r.to_csv()
  html = r.to_html()
  jsn = r.to_json()
  print(f'Register: {r.total_vendors} vendors')
  print(f'CSV length: {len(csv)} chars')
  print(f'HTML length: {len(html)} chars')
  print('Register module: OK')
  "

6G. Resolver without Drive
  python3 -c "
  from core.data.resolver import VendorDataResolver
  resolver = VendorDataResolver('TestVendor')
  result = resolver.resolve(include_documents=False)
  print(f'Resolver: vendor={result.vendor_name}')
  print(f'Drive available: {result.drive_available}')
  print('Resolver module: OK')
  "

6H. Notification sender config check
  python3 -c "
  from core.notifications.sender import send_all_pending
  # Just verify it imports and the function exists
  print('Notifications module: OK')
  "

Report any module that fails to import or throws
an unexpected error.

═══════════════════════════════════════════════════════════
PHASE 7 — Generate audit report
═══════════════════════════════════════════════════════════

After completing all phases, generate a summary
report. Write it to AUDIT.md in the repo root.

Content:

# Bandit System Audit — [date]

## Summary

| Phase | Status | Issues Found | Issues Fixed |
|-------|--------|-------------|-------------|
| Phase 0 — Syntax/imports | PASS/FAIL | N | N |
| Phase 1 — Tests | PASS/FAIL | N | N |
| Phase 2 — CLI validation | PASS/FAIL | N | N |
| Phase 3 — Security | PASS/FAIL | N | N |
| Phase 4 — Documentation | PASS/FAIL | N | N |
| Phase 5 — Code quality | PASS/FAIL | N | N |
| Phase 6 — E2E simulation | PASS/FAIL | N | N |

## Test coverage
[paste coverage output]

## Security findings
[list any issues found and whether fixed]

## Documentation gaps
[list any stale content or missing files]

## Known issues (not fixed this session)
[anything that needs follow-up]

## Version
Bandit v1.4.0 — audited [date]

═══════════════════════════════════════════════════════════
FINAL COMMIT
═══════════════════════════════════════════════════════════

git add -A
git commit -m "audit: full system review v1.4.0

Phase 0: syntax and import errors resolved
Phase 1: automated tests — N passing, N skipped
Phase 2: CLI validation — all commands load correctly
Phase 3: security — [summary of findings/fixes]
Phase 4: documentation — stale content removed,
         broken links fixed, all guides updated
Phase 5: code quality — bare excepts fixed,
         print() removed from core/, TODOs documented
Phase 6: e2e simulation — all modules import cleanly
Phase 7: AUDIT.md generated

See AUDIT.md for full results."

git push origin main
