"""
Bandit CLI

Run with no arguments or --help to see the welcome screen.

Usage
-----
  bandit assess "Acme Corp"
  bandit assess acme.com -v
  bandit assess https://acme.com/privacy --json
  bandit rubric
  bandit rubric --dim D6
  bandit batch vendors.txt

Environment
-----------
  ANTHROPIC_API_KEY   Required for assess/batch (unless --api-key is passed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from core.scoring.rubric import result_to_dict


def _load_dotenv() -> None:
    """Load config.env from repo root if present (no external dependencies)."""
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
# Command handlers
# ─────────────────────────────────────────────────────────────────────

def _cmd_assess(args: argparse.Namespace) -> int:
    from cli.terminal import assessment_progress, console, print_assessment
    from core.agents.privacy_bandit import PrivacyBandit
    from core.llm.anthropic import AnthropicProvider

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[bold red]Error:[/] ANTHROPIC_API_KEY not set.\n"
            "Set the environment variable or pass [color(220)]--api-key <key>[/]."
        )
        return 1

    vendor = " ".join(args.vendor)
    provider = AnthropicProvider(model=args.model, api_key=api_key)

    with assessment_progress() as update:
        bandit = PrivacyBandit(provider=provider, on_progress=update)
        try:
            assessment = bandit.assess(vendor)
        except Exception as exc:
            console.print(f"[bold red]Error:[/] {exc}")
            return 1

    if args.json:
        output = result_to_dict(assessment.result)
        output["sources"] = [
            {"url": s.url, "chars": s.chars, "via": s.via}
            for s in assessment.sources
        ]
        print(json.dumps(output, indent=2))
    else:
        print_assessment(assessment, verbose=args.verbose)

    return 0


def _cmd_rubric(args: argparse.Namespace) -> int:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from core.scoring.rubric import RUBRIC

    con = Console()

    if args.dim:
        dim_key = args.dim.upper()
        if dim_key not in RUBRIC:
            con.print(f"[red]Unknown dimension: {dim_key}[/]  Valid: {', '.join(RUBRIC)}")
            return 1
        dim = RUBRIC[dim_key]
        t = Table(box=None, show_header=False, padding=(0, 2))
        t.add_column(style="bold color(172)", no_wrap=True)
        t.add_column(style="color(245)")
        for level in sorted(dim["levels"].keys(), reverse=True):
            ld = dim["levels"][level]
            signals = ", ".join(ld["required_signals"]) or "(none)"
            t.add_row(
                f"{level}  {ld['label']}",
                f"{ld['description']}\n[dim]Signals: {signals}[/]",
            )
        con.print(Panel(
            t,
            title=f"[bold color(172)]{dim_key} — {dim['name']}[/]",
            border_style="color(238)",
        ))
    else:
        t = Table(box=None, show_header=True, padding=(0, 2))
        t.add_column("Dim", style="bold color(172)", no_wrap=True)
        t.add_column("Name", style="color(245)")
        t.add_column("Weight", style="color(240)", justify="right")
        t.add_column("Regulatory basis", style="dim color(238)")
        for dim_key, dim in RUBRIC.items():
            t.add_row(
                dim_key,
                dim["name"],
                str(dim["weight"]),
                dim["regulatory_basis"][0],
            )
        con.print(Panel(
            t,
            title="[bold color(172)]BANDIT RUBRIC — 8 Dimensions[/]",
            border_style="color(238)",
        ))

    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    from rich.console import Console
    Console().print("[color(220)]bandit batch[/] [dim]— coming soon[/]")
    return 0


# ─────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bandit",
        description="Bandit — Vendor Privacy Risk Intelligence",
        add_help=False,  # we handle --help ourselves
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        default=False,
        help="Show this help message",
    )

    sub = parser.add_subparsers(dest="command")

    # assess
    assess = sub.add_parser("assess", help="Assess a vendor's privacy practices")
    assess.add_argument(
        "vendor", nargs="+", metavar="VENDOR",
        help="Vendor name, domain, or URL",
    )
    assess.add_argument(
        "--model", default="claude-haiku-4-5-20251001", metavar="MODEL",
        help="Claude model ID (default: claude-haiku-4-5-20251001)",
    )
    assess.add_argument(
        "--api-key", default=None, metavar="KEY",
        help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
    )
    assess.add_argument(
        "--json", action="store_true",
        help="Emit raw JSON instead of the formatted report",
    )
    assess.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show cap reasons and extra detail",
    )
    assess.set_defaults(func=_cmd_assess)

    # rubric
    rubric = sub.add_parser("rubric", help="Show the scoring rubric")
    rubric.add_argument(
        "--dim", default=None, metavar="DIM",
        help="Show detail for one dimension, e.g. --dim D5",
    )
    rubric.set_defaults(func=_cmd_rubric)

    # batch
    batch = sub.add_parser("batch", help="Assess a list of vendors (coming soon)")
    batch.add_argument("file", nargs="?", metavar="FILE")
    batch.set_defaults(func=_cmd_batch)

    return parser


def main() -> None:
    # Show welcome screen when called with no args or --help at top level
    if len(sys.argv) == 1 or sys.argv[1:] in (["-h"], ["--help"]):
        from cli.welcome import show_welcome
        from rich.console import Console
        show_welcome(Console())
        sys.exit(0)

    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        from cli.welcome import show_welcome
        from rich.console import Console
        show_welcome(Console())
        sys.exit(0)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
