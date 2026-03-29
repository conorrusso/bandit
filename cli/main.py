"""
Bandit CLI

Usage
-----
  bandit assess "Acme Corp"
  bandit assess acme.com --verbose
  bandit assess https://acme.com/privacy --json
  bandit assess "Acme Corp" --model claude-sonnet-4-6

Environment
-----------
  ANTHROPIC_API_KEY   Required unless --api-key is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

from core.scoring.rubric import AssessmentResult, result_to_dict


def _load_dotenv() -> None:
    """Load .env from the repo root if present (no external dependencies)."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "config.env")
    env_path = os.path.normpath(env_path)
    if not os.path.isfile(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


# ─────────────────────────────────────────────────────────────────────
# Terminal formatting
# ─────────────────────────────────────────────────────────────────────

_BOLD = "\033[1m"
_RESET = "\033[0m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_GREEN = "\033[92m"
_DIM = "\033[2m"

_TIER_COLOUR = {"HIGH": _RED, "MEDIUM": _YELLOW, "LOW": _GREEN}


def _c(text: str, code: str) -> str:
    """Apply ANSI colour if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{code}{text}{_RESET}"
    return text


def _bar(score: int, total: int = 5) -> str:
    return "█" * score + "░" * (total - score)


# ─────────────────────────────────────────────────────────────────────
# Report formatter
# ─────────────────────────────────────────────────────────────────────

_W = 64  # report width


def _fmt_signal(slug: str) -> str:
    """Turn 'd1_purposes_stated' → 'purposes stated'."""
    parts = slug.split("_", 1)
    return parts[1].replace("_", " ") if len(parts) == 2 else slug.replace("_", " ")


def _print_report(assessment, *, verbose: bool = False) -> None:
    result = assessment.result
    sources = assessment.sources
    tier_col = _TIER_COLOUR.get(result.risk_tier, "")

    print()
    print("━" * _W)
    print(f"  {_c('BANDIT PRIVACY ASSESSMENT', _BOLD)}")
    print(f"  Vendor : {result.vendor}")
    print(
        f"  Risk   : "
        + _c(f"{result.risk_tier}  {result.weighted_average}/5.0", tier_col)
    )
    print(f"  Rubric : v{result.version}")
    print("━" * _W)

    # Sources
    print(f"\n{_c('PAGES ANALYSED  (' + str(len(sources)) + ')', _BOLD)}")
    print("─" * _W)
    if sources:
        for i, src in enumerate(sources, 1):
            via_note = _c(f"  [{src.via}]", _DIM)
            print(f"  {i}.  {src.url}")
            print(_c(f"       {src.chars:,} chars retrieved{via_note}", _DIM))
    else:
        print(_c("  No sources recorded.", _DIM))

    # Dimension scores
    print(f"\n{_c('DIMENSION SCORES', _BOLD)}")
    print("─" * _W)
    for dim_key, dr in result.dimensions.items():
        bar = _bar(dr.capped_score)
        cap = ""
        if dr.cap_reasons:
            cap = _c(f"  ↓ {dr.cap_reasons[0]}", _DIM)
        weight = f"×{dr.weight:.1f}" if dr.weight != 1.0 else "    "
        print(
            f"\n  {dim_key} {weight}  {_c(dr.name, _BOLD)}"
            f"  {bar} {dr.capped_score}/5  {dr.level_label}{cap}"
        )
        if dr.matched_signals:
            found = ", ".join(_fmt_signal(s) for s in dr.matched_signals)
            print(_c(f"    ✓  Found : {found}", _GREEN))
        else:
            print(_c(f"    ✗  Nothing found for this dimension", _DIM))
        if dr.missing_for_next:
            missing = [_fmt_signal(s) for s in dr.missing_for_next]
            shown = ", ".join(missing[:4])
            if len(missing) > 4:
                shown += f" (+{len(missing) - 4} more)"
            next_level = dr.capped_score + 1
            print(_c(f"    ↑  To reach {next_level}/5 : {shown}", _DIM))
        if dr.cap_reasons and verbose:
            for reason in dr.cap_reasons:
                print(_c(f"    ⬇  Capped : {reason}", _YELLOW))

    # Red flags
    if result.red_flags:
        print(f"\n\n{_c('RED FLAGS  (' + str(len(result.red_flags)) + ')', _BOLD)}")
        print("─" * _W)
        for rf in result.red_flags:
            dims = ", ".join(rf["dims"])
            match_text = textwrap.shorten(rf["match"], width=58, placeholder="…")
            print(_c(f'\n  ⚠  [{dims}]  {rf["label"]}', _YELLOW))
            print(_c(f'       Matched text: "{match_text}"', _DIM))

    # Framework certifications
    if result.framework_evidence:
        print(f"\n\n{_c('FRAMEWORKS DETECTED', _BOLD)}")
        print("─" * _W)
        for fw in result.framework_evidence:
            print(f"  ✓  {fw}")

    # Action guidance by tier
    print(f"\n\n{_c('RECOMMENDED ACTIONS', _BOLD)}")
    print("─" * _W)
    tier = result.risk_tier
    if tier == "HIGH":
        print("  GRC:       Escalate to security review. Do not proceed to contract.")
        print("  Legal:     Request an updated DPA before signing anything.")
        print("  Security:  Request SOC 2 Type II report directly from the vendor.")
    elif tier == "MEDIUM":
        print("  GRC:       Flag specific gaps for contract negotiation.")
        print("  Legal:     Negotiate DPA improvements on flagged dimensions.")
        print("  Security:  Verify sub-processor list and confirm breach SLAs.")
    else:
        print("  GRC:       Standard onboarding process applies.")
        print("  Legal:     Confirm executed DPA is on file and current.")
        print("  Security:  Annual review sufficient unless scope changes.")
    print()


# ─────────────────────────────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────────────────────────────

def _cmd_assess(args: argparse.Namespace) -> int:
    # Lazy imports so --help works without dependencies installed
    from core.agents.privacy_bandit import PrivacyBandit
    from core.llm.anthropic import AnthropicProvider

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass --api-key <key>.",
            file=sys.stderr,
        )
        return 1

    vendor = " ".join(args.vendor)
    provider = AnthropicProvider(model=args.model, api_key=api_key)
    bandit = PrivacyBandit(provider=provider)

    print(f"Assessing {vendor!r} …", file=sys.stderr)

    try:
        assessment = bandit.assess(vendor)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        output = result_to_dict(assessment.result)
        output["sources"] = [
            {"url": s.url, "chars": s.chars, "via": s.via}
            for s in assessment.sources
        ]
        print(json.dumps(output, indent=2))
    else:
        _print_report(assessment, verbose=args.verbose)

    return 0


# ─────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bandit",
        description="Bandit — Vendor Privacy Risk Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              bandit assess "Acme Corp"
              bandit assess acme.com --verbose
              bandit assess https://acme.com/privacy --json
              bandit assess "Acme Corp" --model claude-sonnet-4-6
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    assess = sub.add_parser(
        "assess",
        help="Assess a vendor's privacy practices",
        description=(
            "Discover, fetch, and score a vendor's privacy policy "
            "using the Bandit 8-dimension rubric."
        ),
    )
    assess.add_argument(
        "vendor",
        nargs="+",
        metavar="VENDOR",
        help=(
            "Vendor name, domain, or URL — e.g. 'Acme Corp', "
            "acme.com, https://acme.com/privacy"
        ),
    )
    assess.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        metavar="MODEL",
        help="Claude model ID (default: claude-haiku-4-5-20251001)",
    )
    assess.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
    )
    assess.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON instead of the formatted report",
    )
    assess.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show which signals are missing to reach the next dimension level",
    )
    assess.set_defaults(func=_cmd_assess)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
