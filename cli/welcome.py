"""
Bandit welcome screen — shown when `bandit` is run with no arguments or --help.

Raccoon rendered in Unicode block characters using Rich 256-color styles.
Color mapping (per spec):
  Body/head fur   color(138)  warm grey
  Mask            color(232)  near black
  Eye whites      color(255)  bright white
  Pupils          color(232)  near black  (reads dark within white context)
  Muzzle/chin     color(251)  light grey
  Ear inner       color(217)  dusty pink
  Magnifying glass color(172) amber/gold
  Paper           color(231)  near white
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────────────
# Raccoon pixel grid
#
# Each character maps to one colored █ block (or a space for background).
# 14 pixels wide × 17 rows tall.
#
# Key:
#   ' '  background (space)
#   b    body/fur      color(138)
#   k    mask          color(232)
#   w    eye white     color(255)
#   p    pupil         color(232)  — dark dot within white eye
#   m    muzzle        color(251)
#   i    ear inner     color(217)
#   g    magnifier     color(172)
#   r    paper         color(231)
#   n    nose          color(232)
# ─────────────────────────────────────────────────────────────────────
_GRID = [
    "  bib   bib   ",   # ears with pink inner
    "  bbb   bbb   ",   # ear bases
    "  bbbbbbbbb   ",   # head top
    "  bkkkkkkkb   ",   # mask band — spans both eyes
    "  bkwwkwwkb   ",   # eye whites within mask (w = shine beside pupil)
    "  bkwpkwpkb   ",   # pupils (p dark within white)
    "  bkkkkkkkb   ",   # mask band bottom
    "   bmmmmmmb   ",   # muzzle
    "   bmmmbmmb   ",   # muzzle + mouth flanks
    "   bmmknmmb   ",   # nose (n) + mouth mark (k) to left
    "   bmmmmmmb   ",   # chin muzzle
    "  bbbbbbbbbb  ",   # chin / neck
    " gbbbbbbbbbr  ",   # body — glass left paw, paper right paw start
    "ggbbbbbbbbrrr ",   # glass circle + body + paper stack
    " gggbbbb rrrr ",   # glass handle emerges + paper
    "  gggb   rr   ",   # lower paw detail
    "   ggg        ",   # magnifier handle
    "    gg        ",   # handle tip
]

_PALETTE: dict[str, str] = {
    "b": "color(138)",
    "k": "color(232)",
    "w": "color(255)",
    "p": "color(232)",
    "m": "color(251)",
    "i": "color(217)",
    "g": "color(172)",
    "r": "color(231)",
    "n": "color(232)",
}


def _raccoon() -> Text:
    """Render the pixel grid as a Rich Text object."""
    art = Text()
    for row in _GRID:
        for ch in row:
            if ch == " ":
                art.append(" ")
            else:
                art.append("█", style=_PALETTE.get(ch, ""))
        art.append("\n")
    return art


# ─────────────────────────────────────────────────────────────────────
# Welcome screen
# ─────────────────────────────────────────────────────────────────────

def show_welcome(console: Console | None = None) -> None:
    if console is None:
        console = Console()

    # ── Header: raccoon LEFT, brand RIGHT ────────────────────────────
    brand = Text()
    brand.append("BANDIT\n", style="bold color(172)")
    brand.append("Vendor Risk Intelligence Suite\n", style="color(245)")
    brand.append("Every vendor has something to hide.\n\n", style="italic color(240)")
    brand.append("─" * 33 + "\n", style="color(238)")
    brand.append(f"v{VERSION}", style="color(240)")
    brand.append("  ·  ", style="color(238)")
    brand.append("MIT", style="color(240)")
    brand.append("  ·  ", style="color(238)")
    brand.append("Free forever\n", style="color(240)")
    brand.append("github.com/conorrusso/bandit", style="color(238)")

    header_grid = Table.grid(padding=(0, 3))
    header_grid.add_column()
    header_grid.add_column(vertical="middle")
    header_grid.add_row(_raccoon(), brand)

    console.print()
    console.print(header_grid)
    console.print()

    # ── COMMANDS ─────────────────────────────────────────────────────
    cmd_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    cmd_table.add_column(no_wrap=True)
    cmd_table.add_column(style="dim color(245)")

    def _cmd(base: str, arg: str, flag: str = "") -> Text:
        t = Text()
        t.append(base, style="color(220)")
        if arg:
            t.append(" ")
            t.append(arg, style="color(71)")
        if flag:
            t.append(" ")
            t.append(flag, style="color(220)")
        return t

    commands = [
        (_cmd("bandit assess", "<vendor>"),               "Run a full privacy risk assessment"),
        (_cmd("bandit assess", "<vendor>", "-v"),         "Verbose — see fetched pages and signals"),
        (_cmd("bandit assess", "<vendor>", "--json"),     "Output raw JSON"),
        (_cmd("bandit batch",  "<vendors.txt>"),          "Assess a full vendor list overnight"),
        (_cmd("bandit rubric", ""),                       "Show the scoring rubric summary"),
        (_cmd("bandit rubric", "", "--dim D5"),           "Show criteria for one dimension"),
    ]
    for cmd_text, desc in commands:
        cmd_table.add_row(cmd_text, desc)

    console.print(Panel(
        cmd_table,
        title="[bold color(172)]COMMANDS[/]",
        border_style="color(238)",
    ))

    # ── EXAMPLES ─────────────────────────────────────────────────────
    ex_lines = Text()
    examples = [
        'bandit assess "Salesforce"',
        'bandit assess hubspot.com --verbose',
        'bandit assess "Acme Corp" --json > acme.json',
        'bandit batch vendors.txt',
    ]
    for ex in examples:
        ex_lines.append("$ ", style="dim color(71)")
        ex_lines.append(ex + "\n", style="color(71)")

    console.print(Panel(
        ex_lines,
        title="[bold color(172)]EXAMPLES[/]",
        border_style="color(238)",
    ))

    # ── PROVIDERS ────────────────────────────────────────────────────
    prov_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    prov_table.add_column(min_width=20, no_wrap=True)
    prov_table.add_column(style="dim color(240)", no_wrap=True)
    prov_table.add_column()

    prov_table.add_row(
        Text("Claude  (default)", style="bold color(245)"),
        "export ANTHROPIC_API_KEY=sk-ant-...",
        "",
    )
    prov_table.add_row(
        Text("GPT-4o", style="bold color(245)"),
        "export OPENAI_API_KEY=sk-...   --provider openai",
        "",
    )

    badges = Text()
    badges.append(" FREE ",  style="bold color(255) on color(22)")
    badges.append("  ")
    badges.append(" LOCAL ", style="bold color(255) on color(18)")

    prov_table.add_row(
        Text("Ollama", style="bold color(245)"),
        "ollama pull llama3.1   --provider ollama",
        badges,
    )

    console.print(Panel(
        prov_table,
        title="[bold color(172)]PROVIDERS[/]",
        border_style="color(238)",
    ))

    # ── Cursor prompt ─────────────────────────────────────────────────
    console.print()
    prompt = Text()
    prompt.append("  Run ", style="color(245)")
    prompt.append("bandit assess <vendor>", style="color(220)")
    prompt.append(" to get started ", style="color(245)")
    prompt.append("▋", style="blink bold color(172)")
    console.print(prompt)
    console.print()
