# Bandit — Auto-create profiles on sync +
# bandit workflow command
#
# Two additions. Complete each fully before the next.
# Do not modify any existing commands beyond what
# is specified here.

═══════════════════════════════════════════════════════════
CHANGE 1 — bandit sync auto-creates minimal profiles
═══════════════════════════════════════════════════════════

In cli/main.py in the sync command, find the block
that handles unmatched Drive folders (the suggestions
list). Currently it just prints a hint.

Change it so unmatched Drive folders automatically
get a minimal local profile created — no prompts,
no questions, just enough to show up in the dashboard
as unassessed with their Drive folder linked.

Find this block:

  if suggestions:
      console.print()
      console.print(
          "  [dim]Drive folders with no local "
          "profile:[/dim]"
      )
      for s in suggestions:
          console.print(
              f"  [yellow]?[/yellow]  {s}"
              f"  [dim]→ bandit vendor add "
              f'"{s}"[/dim]'
          )

Replace with:

  if suggestions:
      console.print()
      console.print(
          "  [dim]Creating minimal profiles for "
          "new Drive folders...[/dim]"
      )

      for folder_name in suggestions:
          # Find the folder_id from the folders list
          folder_id = next(
              (f["id"] for f in folders
               if f["name"] == folder_name),
              None
          )

          try:
              from core.profiles.auto_detect import (
                  VendorAutoDetector
              )
              detector = VendorAutoDetector()
              detect_result = detector.detect(folder_name)

              # Build minimal profile
              from core.profiles.vendor_cache import (
                  VendorProfile
              )
              from datetime import datetime

              profile = VendorProfile(
                  vendor_name=folder_name,
                  vendor_slug=folder_name.lower()
                      .strip()
                      .replace(" ", "-")
                      .replace("(", "")
                      .replace(")", ""),
                  functions=getattr(
                      detect_result, "functions", []
                  ) if detect_result else [],
                  detection_method="drive_discovery",
                  vendor_country=None,
                  phi_processor=False,
                  pci_processor=False,
                  children_data=False,
                  last_updated=datetime.now()
                      .strftime("%Y-%m-%d"),
                  drive_folder_id=folder_id,
                  drive_folder_name=folder_name,
                  intake_completed=False,
              )

              cache.save(folder_name, profile)

              console.print(
                  f"  [green]✓[/green]  "
                  f"[bold]{folder_name}[/bold]"
                  f"  [dim]added — run "
                  f"bandit workflow to complete "
                  f"intake and assess[/dim]"
              )

          except Exception as e:
              console.print(
                  f"  [yellow]?[/yellow]  "
                  f"[bold]{folder_name}[/bold]"
                  f"  [dim]could not auto-create: "
                  f"{e}[/dim]"
              )

      # Refresh resolvers to include newly created profiles
      if not vendor_name:
          resolvers = get_all_vendor_resolvers()

The sync output should now look like:

  ✓  Cloudflare  added — run bandit workflow to
                 complete intake and assess
  ✓  Datadog     added — run bandit workflow to
                 complete intake and assess
  ...

And bandit dashboard will show them immediately
as unassessed (—) with ☁ source.

═══════════════════════════════════════════════════════════
CHANGE 2 — bandit workflow command
(cli/workflow.py) — NEW FILE
═══════════════════════════════════════════════════════════

Create cli/workflow.py

This is the vendor onboarding workflow. It:
1. Finds all vendors with incomplete intake
2. Walks through intake for each one
3. Offers to batch assess them all after

import click
import sys
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from rich import box
from rich.table import Table
from rich.panel import Panel

from core.profiles.vendor_cache import VendorProfileCache
from core.profiles.intake import IntakeWizard
from core.config import BanditConfig

console = Console()


@click.command("workflow")
@click.option("--drive", is_flag=True, default=False,
    help="Use Drive documents when assessing")
@click.option("--assess/--no-assess",
    default=True,
    help="Offer to assess after intake "
         "(default: yes)")
@click.option("--vendor", default=None,
    help="Run workflow for a single vendor only")
def workflow(drive, assess, vendor):
    """
    Vendor onboarding workflow.

    Finds vendors missing intake data, walks through
    the 12-question profile for each one, then
    batches assessments with Drive documents.

    Works for two scenarios:

    NEW VENDOR PROCUREMENT — run before you sign.
    Intake captures what data they will access.
    Assessment generates a Legal Bandit redline
    brief you can use in contract negotiations.

    EXISTING VENDORS — catches up vendors that were
    added via bandit sync without intake data.

    Examples:
      bandit workflow --drive
      bandit workflow --vendor "Cloudflare" --drive
    """
    cache = VendorProfileCache()
    config = BanditConfig()

    # ── Find vendors needing intake ───────────────

    if vendor:
        profile = cache.get(vendor)
        if not profile:
            console.print(
                f"\n  No profile found for "
                f"[bold]{vendor}[/bold].\n"
                f"  Run bandit sync first.\n"
            )
            return
        pending = [profile]
    else:
        all_profiles = cache.list_all()
        pending = [
            p for p in all_profiles
            if not p.intake_completed
        ]

    if not pending:
        console.print(
            "\n  [green]✓[/green]  "
            "All vendors have intake data.\n"
            "  Run [bold]bandit dashboard[/bold] "
            "to see your portfolio.\n"
        )
        return

    # ── Show what we found ────────────────────────

    console.print()
    console.print(Panel(
        f"[bold dark_orange]Bandit Vendor Workflow[/bold dark_orange]\n"
        f"[dim]Intake + assessment for "
        f"{len(pending)} vendor(s)[/dim]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Drive folder", justify="center")
    table.add_column("Last assessed", justify="right")
    table.add_column("Status")

    for p in pending:
        has_drive = "[green]☁[/green]" if p.drive_folder_id else "[dim]—[/dim]"
        last = p.last_assessed or "Never"
        status = (
            "[dim]Needs intake[/dim]"
            if not p.intake_completed
            else "[yellow]Needs assessment[/yellow]"
        )
        table.add_row(
            p.vendor_name,
            has_drive,
            last,
            status,
        )

    console.print(table)

    if not Confirm.ask(
        f"  Start intake for "
        f"{len(pending)} vendor(s)?",
        default=True
    ):
        console.print(
            "\n  [dim]Workflow cancelled.[/dim]\n"
        )
        return

    # ── Run intake for each vendor ────────────────

    completed = []
    skipped = []

    for i, profile in enumerate(pending, 1):
        console.print()
        console.print(
            f"  [bold dark_orange]"
            f"{'━' * 44}[/bold dark_orange]"
        )
        console.print(
            f"  [bold dark_orange]"
            f"Vendor {i} of {len(pending)} — "
            f"{profile.vendor_name}"
            f"[/bold dark_orange]"
        )
        console.print(
            f"  [bold dark_orange]"
            f"{'━' * 44}[/bold dark_orange]"
        )

        # Option to skip this vendor
        action = _ask_vendor_action(
            profile.vendor_name, i, len(pending)
        )

        if action == "skip":
            skipped.append(profile.vendor_name)
            continue

        # Run intake wizard
        wizard = IntakeWizard(profile.vendor_name)

        # Pre-fill any existing answers if re-running
        if profile.intake_completed:
            wizard.answers = {
                "data_types": profile.data_types or [],
                "data_volume": profile.data_volume,
                "environment_access": profile.environment_access,
                "access_level": profile.access_level,
                "sole_source": profile.sole_source,
                "integrations": profile.integrations or [],
                "sso_required": profile.sso_required,
                "ai_in_service": profile.ai_in_service,
                "ai_trains_on_data": profile.ai_trains_on_data,
                "criticality": profile.criticality,
                "annual_spend": profile.annual_spend,
                "renewal_date": profile.renewal_date,
            }

        answers = wizard.run()

        if answers is None:
            # Ctrl+C — offer to continue with next
            console.print()
            if i < len(pending):
                if not Confirm.ask(
                    "  Continue with next vendor?",
                    default=True
                ):
                    break
            skipped.append(profile.vendor_name)
            continue

        # Build IT action items
        it_actions = wizard.build_it_actions()

        # Apply answers to profile
        profile.intake_completed = True
        profile.intake_date = datetime.now().strftime(
            "%Y-%m-%d"
        )
        profile.data_types = answers.get("data_types", [])
        profile.data_volume = answers.get("data_volume")
        profile.environment_access = answers.get(
            "environment_access"
        )
        profile.access_level = answers.get("access_level")
        profile.sole_source = answers.get("sole_source")
        profile.integrations = answers.get("integrations", [])
        profile.sso_required = answers.get("sso_required")
        profile.ai_in_service = answers.get("ai_in_service")
        profile.ai_trains_on_data = answers.get(
            "ai_trains_on_data"
        )
        profile.criticality = answers.get("criticality")
        profile.annual_spend = answers.get("annual_spend")
        profile.renewal_date = answers.get("renewal_date")
        profile.last_updated = datetime.now().strftime(
            "%Y-%m-%d"
        )

        # IT notification queue
        if it_actions:
            profile.pending_it_notification = {
                "status": "pending",
                "created": datetime.now().strftime(
                    "%Y-%m-%d"
                ),
                "integrations": [
                    i["system_name"]
                    for i in answers.get("integrations", [])
                ],
                "it_actions": it_actions,
            }

        cache.save(profile.vendor_name, profile)
        wizard.show_summary()
        completed.append(profile.vendor_name)

        # Sync profile to Drive if configured
        try:
            drive_cfg = (
                config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
            )
            if drive_cfg.get("enabled") and drive_cfg.get(
                "root_folder_id"
            ):
                from core.integrations.google_drive import (
                    GoogleDriveClient
                )
                from core.data.resolver import (
                    VendorDataResolver
                )
                resolver = VendorDataResolver(
                    profile.vendor_name
                )
                resolver.sync_profile_to_drive()
        except Exception:
            pass  # Non-blocking

    # ── Intake summary ────────────────────────────

    console.print()
    console.print(
        f"  [bold]Intake complete[/bold]  "
        f"[green]{len(completed)} done[/green]"
        + (
            f"  [dim]{len(skipped)} skipped[/dim]"
            if skipped else ""
        )
    )

    if not completed or not assess:
        _show_next_steps(completed, drive)
        return

    # ── Offer batch assessment ────────────────────

    console.print()
    drive_note = (
        " with Drive documents"
        if drive else " (public policy only)"
    )

    if not Confirm.ask(
        f"  Assess all {len(completed)} vendor(s)"
        f"{drive_note} now?",
        default=True
    ):
        _show_next_steps(completed, drive)
        return

    console.print()

    # Run assessments in sequence
    assessment_results = []

    for i, vendor_name in enumerate(completed, 1):
        console.print(
            f"  [{i}/{len(completed)}] "
            f"Assessing [bold]{vendor_name}[/bold]..."
        )

        try:
            # Import and run assessment
            from core.agents.privacy_bandit import (
                PrivacyBandit
            )
            from core.data.resolver import (
                VendorDataResolver
            )

            resolver = VendorDataResolver(vendor_name)
            resolved = resolver.resolve(
                include_documents=drive
            )

            bandit = PrivacyBandit()
            result = bandit.assess(
                vendor_name,
                documents=resolved.documents if drive else [],
                on_progress=None,
            )

            # Write report
            from cli.report import generate_report
            report_path = generate_report(
                vendor_name, result
            )

            # Save to Drive
            if drive:
                resolver.save_report(report_path)

            # Update assessment history
            from core.profiles.vendor_cache import (
                VendorProfileCache
            )
            VendorProfileCache().update_assessment_history(
                vendor_name, result
            )

            tier = getattr(result, "risk_tier", "?")
            avg = getattr(result, "weighted_average", 0)
            color = (
                "red" if tier == "HIGH"
                else "yellow" if tier == "MEDIUM"
                else "green"
            )

            console.print(
                f"  [{i}/{len(completed)}] "
                f"[bold]{vendor_name}[/bold]  "
                f"[{color}]{tier}[/{color}]  "
                f"{avg:.1f}/5.0  "
                f"[dim]✓ report saved[/dim]"
            )

            assessment_results.append({
                "vendor": vendor_name,
                "tier": tier,
                "score": avg,
                "success": True,
            })

        except Exception as e:
            console.print(
                f"  [{i}/{len(completed)}] "
                f"[bold]{vendor_name}[/bold]  "
                f"[red]Failed: {e}[/red]"
            )
            assessment_results.append({
                "vendor": vendor_name,
                "tier": None,
                "score": None,
                "success": False,
                "error": str(e),
            })

    # ── Final summary ─────────────────────────────

    console.print()
    console.print(
        f"  [bold dark_orange]"
        f"Workflow complete"
        f"[/bold dark_orange]"
    )
    console.print()

    succeeded = [r for r in assessment_results if r["success"]]
    failed = [r for r in assessment_results if not r["success"]]

    for r in succeeded:
        tier = r["tier"]
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green"
        )
        console.print(
            f"  [green]✓[/green]  "
            f"[bold]{r['vendor']}[/bold]  "
            f"[{color}]{tier}[/{color}]  "
            f"{r['score']:.1f}/5.0"
        )

    for r in failed:
        console.print(
            f"  [red]✗[/red]  "
            f"[bold]{r['vendor']}[/bold]  "
            f"[red]{r.get('error', 'Failed')}[/red]"
        )

    if failed:
        console.print(
            f"\n  [dim]{len(failed)} vendors failed. "
            f"Run bandit assess \"VendorName\" --drive "
            f"individually to retry.[/dim]"
        )

    console.print(
        f"\n  [dim]Run bandit dashboard to see "
        f"your full portfolio.[/dim]\n"
    )


def _ask_vendor_action(
    vendor_name: str,
    current: int,
    total: int,
) -> str:
    """Ask user what to do with this vendor."""
    console.print()
    console.print(
        f"  [dim]Vendor {current} of {total}[/dim]"
    )
    console.print(
        f"  1. Run intake for "
        f"[bold]{vendor_name}[/bold]"
    )
    console.print(f"  2. Skip {vendor_name}")
    console.print()

    while True:
        raw = click.prompt(
            "  Choice",
            default="1"
        ).strip()
        if raw == "1":
            return "intake"
        elif raw == "2":
            return "skip"
        else:
            console.print("  [red]Enter 1 or 2[/red]")


def _show_next_steps(
    completed: list[str],
    drive: bool,
) -> None:
    """Show next steps after workflow."""
    console.print()
    if completed:
        drive_flag = " --drive" if drive else ""
        console.print(
            "  [dim]To assess individually:[/dim]"
        )
        for v in completed[:3]:
            console.print(
                f"  [dim]bandit assess "
                f'"{v}"{drive_flag}[/dim]'
            )
        if len(completed) > 3:
            console.print(
                f"  [dim]... and "
                f"{len(completed) - 3} more[/dim]"
            )
    console.print(
        "\n  [dim]bandit dashboard[/dim]\n"
    )

═══════════════════════════════════════════════════════════
CHANGE 3 — Wire workflow into cli/main.py
═══════════════════════════════════════════════════════════

In cli/main.py, add:

  from cli.workflow import workflow
  cli.add_command(workflow)

═══════════════════════════════════════════════════════════
CHANGE 4 — Update welcome screen
═══════════════════════════════════════════════════════════

In cli/welcome.py, add to COMMANDS panel:
  bandit workflow      Onboard vendors — intake + assess
  bandit workflow --drive   With Drive documents

Update the WORKFLOWS panel. Change the Drive
first-time sequence to:

  First time with Google Drive:
    1. bandit setup --drive
    2. bandit sync            (auto-creates profiles)
    3. bandit workflow --drive (intake + assess all)
    4. bandit dashboard

  New vendor during procurement:
    1. bandit vendor add "VendorName"
    2. bandit workflow --vendor "VendorName" --drive
    (generates redline brief before you sign)

  Regular use:
    bandit sync               keep Drive in sync
    bandit dashboard          portfolio overview
    bandit schedule --due     what needs reassessment

═══════════════════════════════════════════════════════════
CHANGE 5 — Update docs
═══════════════════════════════════════════════════════════

5A. docs/cli-reference.md — add bandit workflow:

  ## bandit workflow

  Vendor onboarding workflow. Finds all vendors with
  incomplete intake, walks through the 12-question
  profile for each one, then offers to batch assess.

  Works for two scenarios:

  NEW VENDOR PROCUREMENT
  Run before you sign. Intake captures what data they
  will access. Assessment generates a Legal Bandit
  redline brief you can use in contract negotiations.

  EXISTING VENDORS
  Catches up vendors added via bandit sync that don't
  have intake data yet.

  Options:
    --drive           Use Drive documents when assessing
    --no-assess       Run intake only, skip assessments
    --vendor NAME     Run for a single vendor only

  Examples:
    bandit workflow --drive
    bandit workflow --vendor "Cloudflare" --drive
    bandit workflow --no-assess

5B. docs/vendor-guide.md — add section:

  ## Batch onboarding with bandit workflow

  When you have multiple vendors to onboard at once:

    bandit sync              # auto-creates profiles
    bandit workflow --drive  # intake + assess all

  For a single new vendor during procurement:

    bandit vendor add "VendorName"
    bandit workflow --vendor "VendorName" --drive

  The workflow:
  1. Shows all vendors missing intake data
  2. Asks if you want to proceed
  3. Walks through 12 questions per vendor
  4. Lets you skip any vendor
  5. Offers to assess all completed vendors at once
  6. Shows risk tiers and saves reports to Drive

  The Legal Bandit redline brief is generated
  automatically when Drive documents include a DPA
  or MSA. Use it as a negotiating tool before signing.

5C. docs/google-drive-setup.md — update setup sequence:

  ## Setup sequence

  First time:
    bandit setup --drive     # configure credentials
    bandit sync              # discovers folders,
                             # auto-creates profiles
    bandit workflow --drive  # intake + assess all
    bandit dashboard         # view portfolio

  Adding a new vendor:
    # Option A — vendor already has a Drive folder:
    bandit sync              # auto-discovers it
    bandit workflow --vendor "VendorName" --drive

    # Option B — new vendor, no Drive folder yet:
    bandit vendor add "VendorName"  # creates folder
    bandit workflow --vendor "VendorName" --drive

═══════════════════════════════════════════════════════════
VERIFY
═══════════════════════════════════════════════════════════

After all changes:

1. bandit sync
   New Drive folders should be auto-created as
   minimal profiles instead of showing as ?

2. bandit workflow --help
   Should show the command with all flags

3. bandit workflow --no-assess
   Should run intake only, no assessment prompt

4. bandit
   Welcome screen should show workflow in COMMANDS
   and updated WORKFLOWS panel

5. python3 -c "from cli.workflow import workflow; print('OK')"
   Should import without error

═══════════════════════════════════════════════════════════
COMMIT
═══════════════════════════════════════════════════════════

git add -A
git commit -m "feat: bandit sync auto-creates profiles +
bandit workflow onboarding command

bandit sync:
- New Drive folders auto-create minimal local profiles
- No prompts — just adds them so they appear in dashboard
- Hint to run bandit workflow to complete intake

bandit workflow:
- Finds all vendors with incomplete intake
- 12-question intake per vendor with skip option
- Batch assessment after intake completes
- Works for new vendor procurement (pre-signing)
  and existing vendor catch-up
- --drive flag uses Drive documents
- --vendor flag for single vendor
- --no-assess flag for intake only
- Reports saved to Drive, history written to profile
- Legal Bandit redline brief generated when DPA/MSA
  available in Drive

Welcome screen and all docs updated."

git push origin main
