# Bandit v1.4 — Dashboard, Scheduling, Notifications,
# TPRM Register Export
#
# Architecture principles enforced throughout:
#
# 1. CORE/CLI SEPARATION — no print(), console.print(),
#    or rich output anywhere in core/. All output goes
#    through cli/ layer. Core functions return dataclasses
#    or dicts. CLI renders them. Future UI calls core
#    directly and renders its own way.
#
# 2. PROGRESS CALLBACKS — any long-running operation
#    accepts an optional on_progress callback instead of
#    printing directly. CLI passes a rich-based callback.
#    Future UI passes a websocket/queue callback.
#
# 3. JSON-FIRST — every new CLI command supports --json
#    flag that prints the raw dataclass as JSON to stdout.
#    This is the future UI's API surface.
#
# 4. DRIVE-AWARE RESOLVER — one unified class knows where
#    each vendor's data lives (local, Drive, or both) and
#    fetches from the right place. All v1.4 commands use
#    this resolver. No command handles Drive logic directly.
#
# Read existing files before writing anything.
# Complete each section fully before starting the next.
# Do not rewrite existing files — targeted additions only.
# Fix any errors before moving on.

═══════════════════════════════════════════════════════════
SECTION 1 — Unified data resolver
(core/data/resolver.py) — NEW FILE
═══════════════════════════════════════════════════════════

Create core/data/__init__.py (empty)

Create core/data/resolver.py

This is the single entry point for all data access in
Bandit. Every v1.4 command uses this instead of accessing
profiles, Drive, or local docs directly.

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import logging

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig

logger = logging.getLogger("bandit")


@dataclass
class DataSource:
    """Describes where a piece of data came from."""
    kind: str          # "local" | "drive" | "cache"
    path: Optional[str] = None
    folder_id: Optional[str] = None
    last_synced: Optional[str] = None


@dataclass
class ResolvedDocument:
    """A document fetched from any source."""
    filename: str
    content: bytes
    mime_type: str
    source: DataSource
    vendor_name: str


@dataclass
class ResolverResult:
    """Result of resolving all data for a vendor."""
    vendor_name: str
    profile_source: DataSource
    documents: list[ResolvedDocument] = field(
        default_factory=list
    )
    drive_available: bool = False
    drive_folder_id: Optional[str] = None
    errors: list[str] = field(default_factory=list)


class VendorDataResolver:
    """
    Unified data access layer for Bandit.

    Knows where each vendor's data lives and fetches
    from the right place transparently. CLI commands
    and future UI both use this — neither needs to
    know whether data comes from local or Drive.

    Usage:
        resolver = VendorDataResolver("Cyera")
        result = resolver.resolve()
        docs = result.documents       # from wherever
        profile = resolver.profile    # latest version

    Drive resolution:
        - If Drive configured and vendor has folder_id:
          fetches directly (no search, uses stored ID)
        - If Drive unavailable: falls back to local cache
        - Sync failures are logged, never raised
    """

    def __init__(
        self,
        vendor_name: str,
        local_docs_path: Optional[Path] = None,
        on_progress: Optional[Callable] = None,
    ):
        self.vendor_name = vendor_name
        self.local_docs_path = local_docs_path
        self.on_progress = on_progress
        self._config = BanditConfig()
        self._cache = VendorProfileCache()
        self._profile = None
        self._drive = None
        self._drive_configured = False
        self._init_drive()

    def _progress(self, msg: str, **kwargs) -> None:
        """Emit progress without printing."""
        if self.on_progress:
            self.on_progress({"message": msg, **kwargs})

    def _init_drive(self) -> None:
        """Initialise Drive client if configured."""
        try:
            drive_cfg = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
            )
            if drive_cfg.get("enabled"):
                from core.integrations.google_drive import (
                    GoogleDriveClient
                )
                self._drive = GoogleDriveClient()
                self._drive.authenticate()
                self._drive_configured = True
        except Exception as e:
            logger.debug(f"Drive not available: {e}")

    @property
    def profile(self):
        """
        Returns vendor profile, pulling from Drive
        if newer than local cache.
        """
        if self._profile is None:
            self._profile = self._resolve_profile()
        return self._profile

    def _resolve_profile(self):
        """
        Pull latest profile from Drive if available,
        fall back to local cache.
        """
        local = self._cache.get(self.vendor_name)

        if not self._drive_configured:
            return local

        try:
            root_id = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
                .get("root_folder_id")
            )
            if root_id:
                self._cache.sync_from_drive(
                    self._drive, root_id
                )
                return self._cache.get(self.vendor_name)
        except Exception as e:
            logger.warning(
                f"Drive profile sync failed, "
                f"using local cache: {e}"
            )

        return local

    @property
    def drive_folder_id(self) -> Optional[str]:
        """
        Returns Drive folder ID from vendor profile.
        Already stored — no search needed.
        """
        if self.profile:
            return self.profile.drive_folder_id
        return None

    def resolve(
        self,
        include_documents: bool = True,
    ) -> ResolverResult:
        """
        Resolve all data for this vendor.
        Returns ResolverResult with profile + documents.
        """
        profile_source = DataSource(kind="local")
        errors = []
        documents = []

        # Resolve profile source
        if self._drive_configured:
            profile_source = DataSource(
                kind="drive",
                last_synced=getattr(
                    self.profile, "drive_last_synced", None
                )
            )

        if include_documents:
            # Local documents
            if self.local_docs_path:
                self._progress(
                    "Loading local documents",
                    source="local"
                )
                try:
                    local_docs = self._load_local_docs()
                    documents.extend(local_docs)
                except Exception as e:
                    errors.append(f"Local docs error: {e}")

            # Drive documents
            if (self._drive_configured
                    and self.drive_folder_id):
                self._progress(
                    "Loading Drive documents",
                    source="drive"
                )
                try:
                    drive_docs = self._load_drive_docs()
                    documents.extend(drive_docs)
                except Exception as e:
                    errors.append(f"Drive docs error: {e}")
                    logger.warning(
                        f"Drive document fetch failed: {e}"
                    )

            # Deduplicate by filename
            documents = self._deduplicate(documents)

        return ResolverResult(
            vendor_name=self.vendor_name,
            profile_source=profile_source,
            documents=documents,
            drive_available=self._drive_configured,
            drive_folder_id=self.drive_folder_id,
            errors=errors,
        )

    def _load_local_docs(self) -> list[ResolvedDocument]:
        """Load documents from local path."""
        docs = []
        if not self.local_docs_path:
            return docs

        path = Path(self.local_docs_path)
        if not path.exists():
            return docs

        source = DataSource(
            kind="local",
            path=str(path)
        )

        for f in path.iterdir():
            if f.is_file() and f.suffix.lower() in (
                ".pdf", ".docx", ".doc",
                ".txt", ".json", ".html"
            ):
                try:
                    docs.append(ResolvedDocument(
                        filename=f.name,
                        content=f.read_bytes(),
                        mime_type=self._mime(f.suffix),
                        source=source,
                        vendor_name=self.vendor_name,
                    ))
                except Exception as e:
                    logger.warning(
                        f"Could not read {f.name}: {e}"
                    )
        return docs

    def _load_drive_docs(self) -> list[ResolvedDocument]:
        """Load documents from Drive folder."""
        if not self._drive or not self.drive_folder_id:
            return []

        docs = []
        source = DataSource(
            kind="drive",
            folder_id=self.drive_folder_id
        )

        try:
            files = self._drive.list_files_in_folder(
                self.drive_folder_id
            )
            for f in files:
                # Skip existing assessment reports
                if "privacy-assessment" in f["name"]:
                    continue
                try:
                    content = self._drive.download_file(
                        f["id"]
                    )
                    docs.append(ResolvedDocument(
                        filename=f["name"],
                        content=content,
                        mime_type=f.get(
                            "mimeType", "application/octet-stream"
                        ),
                        source=source,
                        vendor_name=self.vendor_name,
                    ))
                except Exception as e:
                    logger.warning(
                        f"Could not download "
                        f"{f['name']}: {e}"
                    )
        except Exception as e:
            logger.warning(
                f"Could not list Drive folder "
                f"{self.drive_folder_id}: {e}"
            )
        return docs

    def save_report(
        self,
        report_path: Path,
        also_save_to_drive: bool = True,
    ) -> None:
        """
        Save a completed report locally and optionally
        to Drive vendor folder.
        """
        # Drive save
        if (also_save_to_drive
                and self._drive_configured
                and self.drive_folder_id):
            try:
                self._drive.upload_file(
                    file_path=report_path,
                    folder_id=self.drive_folder_id,
                    file_name=report_path.name,
                )
            except Exception as e:
                logger.warning(
                    f"Could not save report to Drive: {e}"
                )

    def sync_profile_to_drive(self) -> bool:
        """
        Push updated local profile to Drive.
        Returns True if successful.
        """
        if not self._drive_configured:
            return False

        try:
            root_id = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
                .get("root_folder_id")
            )
            if root_id:
                return self._cache.sync_to_drive(
                    self._drive, root_id
                )
        except Exception as e:
            logger.warning(
                f"Profile Drive sync failed: {e}"
            )
        return False

    def _deduplicate(
        self,
        docs: list[ResolvedDocument]
    ) -> list[ResolvedDocument]:
        """
        Remove duplicate documents by filename.
        Drive version wins over local when both exist.
        """
        seen = {}
        for doc in docs:
            existing = seen.get(doc.filename)
            if not existing:
                seen[doc.filename] = doc
            elif doc.source.kind == "drive":
                seen[doc.filename] = doc
        return list(seen.values())

    @staticmethod
    def _mime(suffix: str) -> str:
        return {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-"
                     "officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".json": "application/json",
            ".html": "text/html",
        }.get(suffix.lower(), "application/octet-stream")


def get_all_vendor_resolvers(
    on_progress: Optional[Callable] = None,
) -> list[VendorDataResolver]:
    """
    Returns a resolver for every vendor in the
    local profile cache. Used by dashboard/schedule.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    return [
        VendorDataResolver(
            p.vendor_name,
            on_progress=on_progress
        )
        for p in profiles
    ]

═══════════════════════════════════════════════════════════
SECTION 2 — Portfolio data module
(core/dashboard/portfolio.py) — NEW FILE
═══════════════════════════════════════════════════════════

Create core/dashboard/__init__.py (empty)

Create core/dashboard/portfolio.py

Pure data. No print statements. Returns dataclasses.
CLI renders these. Future UI calls these directly.

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import json

from core.profiles.vendor_cache import VendorProfileCache
from core.data.resolver import VendorDataResolver


@dataclass
class VendorSummary:
    """Single vendor row in portfolio view."""
    vendor_name: str
    risk_tier: Optional[str]        # HIGH/MEDIUM/LOW
    weighted_average: Optional[float]
    last_assessed: Optional[str]
    next_due: Optional[str]
    overdue: bool
    days_overdue: Optional[int]
    intake_completed: bool
    open_findings: int
    drive_folder_id: Optional[str]
    data_source: str               # "local" | "drive" | "both"
    assessment_count: int


@dataclass
class RiskDistribution:
    high: int = 0
    medium: int = 0
    low: int = 0
    unassessed: int = 0

    @property
    def total(self) -> int:
        return self.high + self.medium + self.low + self.unassessed


@dataclass
class PortfolioSummary:
    """
    Complete portfolio picture.
    Returned by get_summary().
    CLI renders this. Future UI calls get_summary() directly.
    """
    total_vendors: int
    risk_distribution: RiskDistribution
    vendors_due: int
    vendors_overdue: int
    open_findings_total: int
    intake_completion_rate: float   # 0.0–1.0
    drive_vendors: int              # vendors with Drive folder
    local_only_vendors: int
    generated_at: str
    vendors: list[VendorSummary] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialise for --json flag or UI API."""
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def get_summary(
    risk_filter: Optional[str] = None,
    due_only: bool = False,
    overdue_only: bool = False,
) -> PortfolioSummary:
    """
    Build portfolio summary from all vendor profiles.
    Reads local profiles; Drive sync happens per-resolver.

    Args:
        risk_filter:  "HIGH" | "MEDIUM" | "LOW" | None
        due_only:     Only include vendors due/overdue
        overdue_only: Only include overdue vendors

    Returns:
        PortfolioSummary — fully populated dataclass.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    today = date.today()

    vendor_summaries = []
    dist = RiskDistribution()
    open_findings_total = 0
    intake_complete_count = 0
    drive_count = 0
    local_only_count = 0
    due_count = 0
    overdue_count = 0

    for profile in profiles:
        tier = profile.current_risk_tier
        avg = None
        history = profile.assessment_history or []

        if history:
            avg = history[0].get("weighted_average")

        # Risk distribution
        if not tier:
            dist.unassessed += 1
        elif tier == "HIGH":
            dist.high += 1
        elif tier == "MEDIUM":
            dist.medium += 1
        elif tier == "LOW":
            dist.low += 1

        # Due / overdue
        overdue = False
        days_overdue = None
        next_due = profile.next_due

        if next_due and next_due != "scan_only":
            try:
                due_date = datetime.strptime(
                    next_due, "%Y-%m-%d"
                ).date()
                if due_date < today:
                    overdue = True
                    days_overdue = (today - due_date).days
                    overdue_count += 1
                    due_count += 1
                elif due_date <= today:
                    due_count += 1
            except ValueError:
                pass
        elif not next_due and history:
            # Has been assessed but no next_due — flag
            due_count += 1

        # Intake
        if profile.intake_completed:
            intake_complete_count += 1

        # Data source
        has_drive = bool(profile.drive_folder_id)
        if has_drive:
            drive_count += 1
            data_source = "drive"
        else:
            local_only_count += 1
            data_source = "local"

        # Open findings (from last assessment if available)
        findings = getattr(profile, "open_findings", 0) or 0
        open_findings_total += findings

        summary = VendorSummary(
            vendor_name=profile.vendor_name,
            risk_tier=tier,
            weighted_average=avg,
            last_assessed=profile.last_assessed,
            next_due=next_due,
            overdue=overdue,
            days_overdue=days_overdue,
            intake_completed=profile.intake_completed,
            open_findings=findings,
            drive_folder_id=profile.drive_folder_id,
            data_source=data_source,
            assessment_count=len(history),
        )
        vendor_summaries.append(summary)

    # Apply filters
    if risk_filter:
        vendor_summaries = [
            v for v in vendor_summaries
            if (v.risk_tier or "").upper() == risk_filter.upper()
        ]
    if overdue_only:
        vendor_summaries = [
            v for v in vendor_summaries if v.overdue
        ]
    elif due_only:
        vendor_summaries = [
            v for v in vendor_summaries
            if v.overdue or v.next_due is None
        ]

    # Sort: overdue first, then by risk tier, then name
    tier_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}
    vendor_summaries.sort(key=lambda v: (
        0 if v.overdue else 1,
        tier_order.get(v.risk_tier, 3),
        v.vendor_name.lower(),
    ))

    total = len(profiles)
    intake_rate = (
        intake_complete_count / total if total > 0 else 0.0
    )

    return PortfolioSummary(
        total_vendors=total,
        risk_distribution=dist,
        vendors_due=due_count,
        vendors_overdue=overdue_count,
        open_findings_total=open_findings_total,
        intake_completion_rate=intake_rate,
        drive_vendors=drive_count,
        local_only_vendors=local_only_count,
        generated_at=datetime.now().isoformat(),
        vendors=vendor_summaries,
    )

═══════════════════════════════════════════════════════════
SECTION 3 — Schedule data module
(core/dashboard/schedule.py) — NEW FILE
═══════════════════════════════════════════════════════════

Create core/dashboard/schedule.py

Pure data. No print statements.

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
import json

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig


@dataclass
class ScheduleEntry:
    """Single vendor in the reassessment schedule."""
    vendor_name: str
    risk_tier: Optional[str]
    last_assessed: Optional[str]
    next_due: Optional[str]
    overdue: bool
    days_until_due: Optional[int]   # negative = overdue
    days_overdue: Optional[int]
    urgency: str    # "overdue" | "due_soon" | "upcoming" | "ok"
    recommended_depth: str  # "full" | "lightweight" | "scan"
    drive_folder_id: Optional[str]
    data_source: str


@dataclass
class ScheduleSummary:
    """
    Full reassessment schedule.
    Returned by get_schedule().
    """
    entries: list[ScheduleEntry]
    overdue_count: int
    due_within_30_days: int
    due_within_90_days: int
    generated_at: str

    def to_json(self) -> str:
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def get_schedule(
    due_only: bool = False,
    within_days: Optional[int] = None,
) -> ScheduleSummary:
    """
    Build reassessment schedule from all vendor profiles.

    Args:
        due_only:    Only include due/overdue vendors
        within_days: Only include vendors due within N days

    Returns:
        ScheduleSummary — sorted by urgency.
    """
    cache = VendorProfileCache()
    config = BanditConfig()
    profiles = cache.list_all()
    today = date.today()

    entries = []
    overdue_count = 0
    due_30 = 0
    due_90 = 0

    for profile in profiles:
        tier = profile.current_risk_tier
        next_due_str = profile.next_due

        overdue = False
        days_until = None
        days_overdue_val = None
        urgency = "ok"

        if next_due_str and next_due_str != "scan_only":
            try:
                due_date = datetime.strptime(
                    next_due_str, "%Y-%m-%d"
                ).date()
                delta = (due_date - today).days
                days_until = delta

                if delta < 0:
                    overdue = True
                    days_overdue_val = abs(delta)
                    urgency = "overdue"
                    overdue_count += 1
                elif delta <= 30:
                    urgency = "due_soon"
                    due_30 += 1
                    due_90 += 1
                elif delta <= 90:
                    urgency = "upcoming"
                    due_90 += 1
                else:
                    urgency = "ok"

            except ValueError:
                pass

        elif not next_due_str and profile.last_assessed:
            # Assessed but no next_due calculated
            urgency = "due_soon"
            due_30 += 1

        # Depth from config
        try:
            reassessment = config.get_reassessment(
                tier or "MEDIUM"
            )
            depth = reassessment.get("depth", "full")
        except Exception:
            depth = "full"

        entry = ScheduleEntry(
            vendor_name=profile.vendor_name,
            risk_tier=tier,
            last_assessed=profile.last_assessed,
            next_due=next_due_str,
            overdue=overdue,
            days_until_due=days_until,
            days_overdue=days_overdue_val,
            urgency=urgency,
            recommended_depth=depth,
            drive_folder_id=profile.drive_folder_id,
            data_source=(
                "drive" if profile.drive_folder_id
                else "local"
            ),
        )
        entries.append(entry)

    # Filter
    if due_only:
        entries = [
            e for e in entries
            if e.urgency in ("overdue", "due_soon")
        ]

    if within_days is not None:
        entries = [
            e for e in entries
            if (
                e.days_until_due is not None
                and e.days_until_due <= within_days
            ) or e.overdue
        ]

    # Sort: overdue first, then by days_until_due
    urgency_order = {
        "overdue": 0, "due_soon": 1,
        "upcoming": 2, "ok": 3
    }
    entries.sort(key=lambda e: (
        urgency_order.get(e.urgency, 4),
        e.days_until_due or 9999,
        e.vendor_name.lower(),
    ))

    return ScheduleSummary(
        entries=entries,
        overdue_count=overdue_count,
        due_within_30_days=due_30,
        due_within_90_days=due_90,
        generated_at=datetime.now().isoformat(),
    )

═══════════════════════════════════════════════════════════
SECTION 4 — TPRM register export
(core/dashboard/register.py) — NEW FILE
═══════════════════════════════════════════════════════════

Create core/dashboard/register.py

Builds structured vendor register from all profiles.
Pure data module — no print statements.
Supports CSV, JSON, and HTML output.

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import csv
import io
import json

from core.profiles.vendor_cache import VendorProfileCache


@dataclass
class RegisterRow:
    """Single row in the TPRM register."""
    vendor_name: str
    risk_tier: Optional[str]
    weighted_average: Optional[float]
    last_assessed: Optional[str]
    next_due: Optional[str]
    assessment_count: int
    intake_completed: bool
    data_types: list[str]
    criticality: Optional[str]
    annual_spend: Optional[str]
    renewal_date: Optional[str]
    integrations: list[str]
    ai_in_service: Optional[str]
    ai_trains_on_data: Optional[str]
    sole_source: Optional[bool]
    drive_folder_id: Optional[str]
    open_findings: int
    assessment_scope: Optional[str]


@dataclass
class RegisterExport:
    """
    Complete TPRM vendor register.
    Returned by build_register().
    CLI saves as file. Future UI renders as table.
    """
    rows: list[RegisterRow]
    total_vendors: int
    generated_at: str
    format: str     # "csv" | "json" | "html"

    def to_csv(self) -> str:
        """CSV string for export."""
        output = io.StringIO()
        if not self.rows:
            return ""

        fields = [
            "Vendor", "Risk Tier", "Score",
            "Last Assessed", "Next Due",
            "Assessments", "Intake Complete",
            "Criticality", "Annual Spend",
            "Renewal Date", "Data Types",
            "Integrations", "AI in Service",
            "AI Training", "Sole Source",
            "Open Findings", "Drive Folder",
        ]

        writer = csv.DictWriter(
            output, fieldnames=fields
        )
        writer.writeheader()

        for row in self.rows:
            writer.writerow({
                "Vendor": row.vendor_name,
                "Risk Tier": row.risk_tier or "Unassessed",
                "Score": row.weighted_average or "—",
                "Last Assessed": row.last_assessed or "Never",
                "Next Due": row.next_due or "—",
                "Assessments": row.assessment_count,
                "Intake Complete": "Yes" if row.intake_completed else "No",
                "Criticality": row.criticality or "—",
                "Annual Spend": row.annual_spend or "—",
                "Renewal Date": row.renewal_date or "—",
                "Data Types": ", ".join(row.data_types),
                "Integrations": ", ".join(row.integrations),
                "AI in Service": row.ai_in_service or "—",
                "AI Training": row.ai_trains_on_data or "—",
                "Sole Source": "Yes" if row.sole_source else "No",
                "Open Findings": row.open_findings,
                "Drive Folder": (
                    "Yes" if row.drive_folder_id else "No"
                ),
            })

        return output.getvalue()

    def to_json(self) -> str:
        """JSON string for export or UI API."""
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )

    def to_html(self) -> str:
        """Standalone HTML register file."""
        tier_color = {
            "HIGH": "#d04444",
            "MEDIUM": "#e8922c",
            "LOW": "#3aaa5c",
        }
        rows_html = ""
        for row in self.rows:
            color = tier_color.get(
                row.risk_tier or "", "#9a9288"
            )
            tier_badge = (
                f'<span style="background:{color};'
                f'color:white;padding:2px 8px;'
                f'border-radius:4px;font-size:11px;'
                f'font-weight:700">'
                f'{row.risk_tier or "Unassessed"}</span>'
            )
            rows_html += f"""<tr>
              <td>{row.vendor_name}</td>
              <td>{tier_badge}</td>
              <td>{row.weighted_average or '—'}</td>
              <td>{row.last_assessed or 'Never'}</td>
              <td>{row.next_due or '—'}</td>
              <td>{row.criticality or '—'}</td>
              <td>{row.annual_spend or '—'}</td>
              <td>{row.renewal_date or '—'}</td>
              <td>{'✓' if row.intake_completed else '—'}</td>
              <td>{row.open_findings}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>TPRM Register — {self.generated_at[:10]}</title>
<style>
body{{font-family:system-ui,sans-serif;padding:32px;
  background:#faf8f4;color:#1a1814}}
h1{{font-size:22px;margin-bottom:4px}}
.meta{{color:#9a9288;font-size:13px;margin-bottom:28px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#f0ede6;padding:10px 12px;text-align:left;
  font-weight:600;border-bottom:2px solid #e0d8cc;
  white-space:nowrap}}
td{{padding:10px 12px;border-bottom:1px solid #f0ede6}}
tr:hover td{{background:#f8f4ec}}
</style></head><body>
<h1>TPRM Vendor Register</h1>
<div class="meta">
  {self.total_vendors} vendors ·
  Generated {self.generated_at[:10]}
</div>
<table>
<thead><tr>
  <th>Vendor</th><th>Risk</th><th>Score</th>
  <th>Last Assessed</th><th>Next Due</th>
  <th>Criticality</th><th>Spend</th>
  <th>Renewal</th><th>Intake</th><th>Findings</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""


def build_register() -> RegisterExport:
    """
    Build TPRM register from all vendor profiles.
    Pure data — no output, no side effects.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    rows = []

    for profile in profiles:
        history = profile.assessment_history or []
        avg = history[0].get("weighted_average") if history else None
        scope = history[0].get("scope") if history else None

        integrations = [
            i.get("system_name", "")
            for i in (profile.integrations or [])
            if i.get("system_name")
        ]

        rows.append(RegisterRow(
            vendor_name=profile.vendor_name,
            risk_tier=profile.current_risk_tier,
            weighted_average=avg,
            last_assessed=profile.last_assessed,
            next_due=profile.next_due,
            assessment_count=len(history),
            intake_completed=profile.intake_completed,
            data_types=profile.data_types or [],
            criticality=profile.criticality,
            annual_spend=profile.annual_spend,
            renewal_date=profile.renewal_date,
            integrations=integrations,
            ai_in_service=profile.ai_in_service,
            ai_trains_on_data=profile.ai_trains_on_data,
            sole_source=profile.sole_source,
            drive_folder_id=profile.drive_folder_id,
            open_findings=getattr(
                profile, "open_findings", 0
            ) or 0,
            assessment_scope=scope,
        ))

    # Sort by risk tier then name
    tier_order = {
        "HIGH": 0, "MEDIUM": 1,
        "LOW": 2, None: 3
    }
    rows.sort(key=lambda r: (
        tier_order.get(r.risk_tier, 3),
        r.vendor_name.lower()
    ))

    return RegisterExport(
        rows=rows,
        total_vendors=len(rows),
        generated_at=datetime.now().isoformat(),
        format="json",
    )

═══════════════════════════════════════════════════════════
SECTION 5 — Notification sender
(core/notifications/) — NEW FILES
═══════════════════════════════════════════════════════════

Create core/notifications/__init__.py (empty)

Create core/notifications/sender.py

Reads pending_it_notification from vendor profiles.
Sends via Slack webhook or email.
Returns structured results — never prints.

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
import logging
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig

logger = logging.getLogger("bandit")


@dataclass
class SendResult:
    """Result of a single notification send attempt."""
    vendor_name: str
    channel: str        # "slack" | "email" | "both" | "none"
    success: bool
    error: Optional[str] = None
    sent_at: Optional[str] = None


@dataclass
class SendSummary:
    """Result of send_all_pending()."""
    sent: list[SendResult]
    failed: list[SendResult]
    skipped: int        # vendors with no pending notification
    total_processed: int

    def to_json(self) -> str:
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def _build_slack_payload(
    vendor_name: str,
    notification: dict,
) -> dict:
    """Build Slack block kit payload."""
    actions = notification.get("it_actions", [])
    integrations = notification.get("integrations", [])

    action_text = "\n".join(
        f"• {a}" for a in actions[:10]
    )
    if len(actions) > 10:
        action_text += f"\n• ... and {len(actions)-10} more"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🦝 New vendor onboarding: {vendor_name}",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{vendor_name}* has been added to "
                        f"Bandit. The following IT actions "
                        f"are required before this vendor "
                        f"goes live.\n\n"
                        f"*Integrations:* "
                        f"{', '.join(integrations) or 'None'}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Required IT Actions:*\n{action_text}"
                }
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": (
                        f"Sent by Bandit · "
                        f"{datetime.now().strftime('%Y-%m-%d')}"
                    )
                }]
            }
        ]
    }


def _send_slack(
    webhook_url: str,
    payload: dict,
) -> None:
    """Send Slack webhook. Raises on failure."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(
                f"Slack returned {resp.status}"
            )


def _send_email(
    to_address: str,
    vendor_name: str,
    notification: dict,
    smtp_config: dict,
) -> None:
    """Send email notification. Raises on failure."""
    actions = notification.get("it_actions", [])
    integrations = notification.get("integrations", [])

    subject = (
        f"Bandit: IT actions required for {vendor_name}"
    )

    body_lines = [
        f"{vendor_name} has been added to Bandit vendor "
        f"risk management.",
        "",
        f"Integrations: {', '.join(integrations) or 'None'}",
        "",
        "Required IT Actions:",
    ] + [f"  - {a}" for a in actions] + [
        "",
        "---",
        "Sent by Bandit · github.com/conorrusso/bandit",
    ]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = smtp_config.get(
        "from_address", "bandit@localhost"
    )
    msg["To"] = to_address
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    host = smtp_config.get("smtp_host", "localhost")
    port = smtp_config.get("smtp_port", 587)

    with smtplib.SMTP(host, port, timeout=10) as server:
        if smtp_config.get("use_tls", True):
            server.starttls()
        if smtp_config.get("username"):
            server.login(
                smtp_config["username"],
                smtp_config.get("password", "")
            )
        server.sendmail(
            msg["From"], [to_address], msg.as_string()
        )


def send_it_notification(
    vendor_name: str,
) -> SendResult:
    """
    Send IT notification for a single vendor.
    Reads pending_it_notification from vendor profile.
    Marks as sent in profile after successful send.
    Returns SendResult — never prints.
    """
    cache = VendorProfileCache()
    config = BanditConfig()
    profile = cache.get(vendor_name)

    if not profile:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="No vendor profile found",
        )

    notification = getattr(
        profile, "pending_it_notification", None
    )

    if not notification:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="No pending notification",
        )

    if notification.get("status") == "sent":
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="Already sent",
        )

    it_contact = config.get_it_contact()
    slack_webhook = it_contact.get("slack_webhook_url")
    email_address = it_contact.get("it_contact_email")

    if not slack_webhook and not email_address:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error=(
                "No notification channels configured. "
                "Run: bandit setup --notify"
            ),
        )

    channels_sent = []
    errors = []

    # Slack
    if slack_webhook:
        try:
            payload = _build_slack_payload(
                vendor_name, notification
            )
            _send_slack(slack_webhook, payload)
            channels_sent.append("slack")
        except Exception as e:
            errors.append(f"Slack: {e}")
            logger.warning(f"Slack send failed: {e}")

    # Email
    if email_address:
        try:
            smtp_cfg = it_contact.get("smtp", {})
            _send_email(
                email_address, vendor_name,
                notification, smtp_cfg
            )
            channels_sent.append("email")
        except Exception as e:
            errors.append(f"Email: {e}")
            logger.warning(f"Email send failed: {e}")

    success = len(channels_sent) > 0
    channel = (
        "both" if len(channels_sent) == 2
        else channels_sent[0] if channels_sent
        else "none"
    )

    if success:
        # Mark as sent in profile
        notification["status"] = "sent"
        notification["sent_at"] = datetime.now().isoformat()
        notification["sent_via"] = channels_sent
        profile.pending_it_notification = notification
        cache.save(vendor_name, profile)

    return SendResult(
        vendor_name=vendor_name,
        channel=channel,
        success=success,
        error="; ".join(errors) if errors else None,
        sent_at=(
            datetime.now().isoformat() if success else None
        ),
    )


def send_all_pending() -> SendSummary:
    """
    Send IT notifications for all vendors with
    pending notifications. Returns SendSummary.
    Never prints — caller renders results.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()

    sent = []
    failed = []
    skipped = 0

    for profile in profiles:
        notification = getattr(
            profile, "pending_it_notification", None
        )
        if (not notification
                or notification.get("status") == "sent"):
            skipped += 1
            continue

        result = send_it_notification(profile.vendor_name)
        if result.success:
            sent.append(result)
        else:
            failed.append(result)

    return SendSummary(
        sent=sent,
        failed=failed,
        skipped=skipped,
        total_processed=len(sent) + len(failed),
    )

═══════════════════════════════════════════════════════════
SECTION 6 — CLI commands
═══════════════════════════════════════════════════════════

Create cli/dashboard.py

import click
import json as json_module
from rich.console import Console
from rich.table import Table
from rich import box

from core.dashboard.portfolio import get_summary
from core.dashboard.schedule import get_schedule
from core.dashboard.register import build_register
from core.notifications.sender import (
    send_it_notification, send_all_pending
)

console = Console()


@click.group()
def dashboard():
    """Portfolio dashboard and reporting commands."""
    pass


# ── bandit dashboard ────────────────────────────────────

@dashboard.command("show")
@click.option("--risk", default=None,
    help="Filter by risk tier: HIGH/MEDIUM/LOW")
@click.option("--due", is_flag=True, default=False,
    help="Show only vendors due for reassessment")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def dashboard_show(risk, due, as_json):
    """Show portfolio risk dashboard."""
    summary = get_summary(
        risk_filter=risk,
        due_only=due,
    )

    if as_json:
        click.echo(summary.to_json())
        return

    # Header stats
    console.print()
    console.print(
        f"  [bold dark_orange]"
        f"Bandit Portfolio Dashboard"
        f"[/bold dark_orange]"
        f"  [dim]{summary.generated_at[:10]}[/dim]"
    )
    console.print()

    d = summary.risk_distribution
    console.print(
        f"  [bold]{summary.total_vendors}[/bold] vendors  "
        f"  [red]{d.high} HIGH[/red]  "
        f"[yellow]{d.medium} MEDIUM[/yellow]  "
        f"[green]{d.low} LOW[/green]  "
        f"[dim]{d.unassessed} unassessed[/dim]"
    )
    console.print(
        f"  [dim]"
        f"{summary.vendors_overdue} overdue  ·  "
        f"{summary.vendors_due} due  ·  "
        f"{summary.open_findings_total} open findings  ·  "
        f"Intake {int(summary.intake_completion_rate*100)}% complete  ·  "
        f"{summary.drive_vendors} vendors on Drive"
        f"[/dim]"
    )
    console.print()

    if not summary.vendors:
        console.print(
            "  [dim]No vendors match the filter.[/dim]\n"
        )
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Risk", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Last assessed", justify="right")
    table.add_column("Next due", justify="right")
    table.add_column("Findings", justify="right")
    table.add_column("Source", justify="center")
    table.add_column("Intake", justify="center")

    for v in summary.vendors:
        tier = v.risk_tier or "—"
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green" if tier == "LOW"
            else "dim"
        )
        score = (
            f"{v.weighted_average}/5.0"
            if v.weighted_average else "—"
        )
        next_due = v.next_due or "—"
        if v.overdue:
            next_due = (
                f"[red]{next_due} "
                f"({v.days_overdue}d)[/red]"
            )
        source_icon = "☁" if v.data_source == "drive" else "⊙"
        intake = "[green]✓[/green]" if v.intake_completed else "[dim]—[/dim]"

        table.add_row(
            v.vendor_name,
            f"[{color}]{tier}[/{color}]",
            score,
            v.last_assessed or "Never",
            next_due,
            str(v.open_findings),
            source_icon,
            intake,
        )

    console.print(table)
    console.print(
        f"  [dim]{len(summary.vendors)} vendors  "
        f"·  ☁ = Drive  ⊙ = local[/dim]\n"
    )


# ── bandit schedule ─────────────────────────────────────

@dashboard.command("schedule")
@click.option("--due", is_flag=True, default=False,
    help="Show only due/overdue vendors")
@click.option("--within", default=None, type=int,
    help="Show vendors due within N days")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def schedule_show(due, within, as_json):
    """Show reassessment schedule."""
    sched = get_schedule(
        due_only=due,
        within_days=within,
    )

    if as_json:
        click.echo(sched.to_json())
        return

    console.print()
    console.print(
        "  [bold dark_orange]"
        "Reassessment Schedule"
        "[/bold dark_orange]"
    )
    console.print(
        f"  [dim]"
        f"{sched.overdue_count} overdue  ·  "
        f"{sched.due_within_30_days} due within 30 days  ·  "
        f"{sched.due_within_90_days} due within 90 days"
        f"[/dim]"
    )
    console.print()

    if not sched.entries:
        console.print("  [dim]No vendors to show.[/dim]\n")
        return

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Vendor", style="bold")
    table.add_column("Risk", justify="center")
    table.add_column("Last assessed", justify="right")
    table.add_column("Next due", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Depth")
    table.add_column("Data")

    urgency_display = {
        "overdue": "[red]OVERDUE[/red]",
        "due_soon": "[yellow]DUE SOON[/yellow]",
        "upcoming": "[dim]UPCOMING[/dim]",
        "ok": "[green]OK[/green]",
    }

    for e in sched.entries:
        tier = e.risk_tier or "—"
        color = (
            "red" if tier == "HIGH"
            else "yellow" if tier == "MEDIUM"
            else "green" if tier == "LOW"
            else "dim"
        )

        next_due = e.next_due or "—"
        if e.overdue and e.days_overdue:
            next_due = (
                f"[red]{next_due} "
                f"({e.days_overdue}d ago)[/red]"
            )

        data_label = (
            "[blue]Drive[/blue]"
            if e.data_source == "drive"
            else "[dim]Local[/dim]"
        )

        table.add_row(
            e.vendor_name,
            f"[{color}]{tier}[/{color}]",
            e.last_assessed or "Never",
            next_due,
            urgency_display.get(e.urgency, e.urgency),
            e.recommended_depth,
            data_label,
        )

    console.print(table)
    console.print()


# ── bandit register ─────────────────────────────────────

@dashboard.command("register")
@click.option("--format", "fmt",
    type=click.Choice(["csv", "json", "html"]),
    default="csv", help="Output format")
@click.option("--out", default=None,
    help="Output file path (default: stdout for csv/json, "
         "register-YYYY-MM-DD.html for html)")
def register_export(fmt, out):
    """Export TPRM vendor register."""
    from datetime import date

    data = build_register()
    data.format = fmt

    if fmt == "csv":
        output = data.to_csv()
    elif fmt == "json":
        output = data.to_json()
    else:
        output = data.to_html()

    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(
            f"\n  [green]✓[/green] "
            f"Register saved to {out} "
            f"({data.total_vendors} vendors)\n"
        )
    elif fmt == "html":
        default_name = (
            f"bandit-register-{date.today()}.html"
        )
        with open(default_name, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(
            f"\n  [green]✓[/green] "
            f"Register saved to {default_name} "
            f"({data.total_vendors} vendors)\n"
        )
    else:
        click.echo(output)


# ── bandit notify ────────────────────────────────────────

@dashboard.command("notify")
@click.argument("vendor_name", required=False)
@click.option("--all", "send_all", is_flag=True,
    default=False,
    help="Send all pending notifications")
@click.option("--json", "as_json", is_flag=True,
    default=False, help="Output raw JSON")
def notify_send(vendor_name, send_all, as_json):
    """Send queued IT notifications."""
    if send_all:
        summary = send_all_pending()

        if as_json:
            click.echo(summary.to_json())
            return

        console.print()
        if summary.sent:
            for r in summary.sent:
                console.print(
                    f"  [green]✓[/green] "
                    f"{r.vendor_name} → {r.channel}"
                )
        if summary.failed:
            for r in summary.failed:
                console.print(
                    f"  [red]✗[/red] "
                    f"{r.vendor_name}: {r.error}"
                )
        console.print(
            f"\n  [dim]"
            f"Sent: {len(summary.sent)}  "
            f"Failed: {len(summary.failed)}  "
            f"Skipped (no pending): {summary.skipped}"
            f"[/dim]\n"
        )
        return

    if not vendor_name:
        console.print(
            "\n  Specify a vendor or use --all\n"
            "  bandit notify \"Cyera\"\n"
            "  bandit notify --all\n"
        )
        return

    result = send_it_notification(vendor_name)

    if as_json:
        import dataclasses
        click.echo(
            json_module.dumps(
                dataclasses.asdict(result),
                indent=2,
                default=str,
            )
        )
        return

    if result.success:
        console.print(
            f"\n  [green]✓[/green] "
            f"Notification sent for {vendor_name} "
            f"via {result.channel}\n"
        )
    else:
        console.print(
            f"\n  [red]✗[/red] "
            f"Failed for {vendor_name}: {result.error}\n"
        )

═══════════════════════════════════════════════════════════
SECTION 7 — Wire into cli/main.py
═══════════════════════════════════════════════════════════

Do NOT rewrite main.py. Add these targeted changes:

7A. Import and register dashboard group:

  from cli.dashboard import dashboard
  cli.add_command(dashboard)

7B. Add these top-level aliases so common commands
    work without the group prefix:

  # bandit schedule = bandit dashboard schedule
  @cli.command("schedule")
  @click.option("--due", is_flag=True, default=False)
  @click.option("--within", default=None, type=int)
  @click.option("--json", "as_json", is_flag=True, default=False)
  @click.pass_context
  def schedule_alias(ctx, due, within, as_json):
      """Reassessment schedule (alias for dashboard schedule)."""
      ctx.invoke(
          schedule_show,
          due=due,
          within=within,
          as_json=as_json,
      )

  # bandit notify = bandit dashboard notify
  @cli.command("notify")
  @click.argument("vendor_name", required=False)
  @click.option("--all", "send_all", is_flag=True, default=False)
  @click.option("--json", "as_json", is_flag=True, default=False)
  @click.pass_context
  def notify_alias(ctx, vendor_name, send_all, as_json):
      """Send IT notifications (alias for dashboard notify)."""
      ctx.invoke(
          notify_send,
          vendor_name=vendor_name,
          send_all=send_all,
          as_json=as_json,
      )

  # bandit register = bandit dashboard register
  @cli.command("register")
  @click.option("--format", "fmt",
      type=click.Choice(["csv", "json", "html"]),
      default="csv")
  @click.option("--out", default=None)
  @click.pass_context
  def register_alias(ctx, fmt, out):
      """Export TPRM register (alias for dashboard register)."""
      ctx.invoke(register_export, fmt=fmt, out=out)

7C. Update bandit assess to use VendorDataResolver

In the bandit assess command, replace the direct
Drive/local document loading with:

  from core.data.resolver import VendorDataResolver

  resolver = VendorDataResolver(
      vendor_name,
      local_docs_path=docs_path,
      on_progress=lambda p: (
          console.print(
              f"  [dim]{p['message']}[/dim]"
          ) if verbose else None
      ),
  )

  result = resolver.resolve()
  documents = result.documents
  # resolver.profile already has the latest vendor profile

  # After assessment completes:
  resolver.save_report(report_path)
  resolver.sync_profile_to_drive()

7D. Add bandit dashboard to welcome screen

In cli/welcome.py, add to the COMMANDS panel:
  bandit dashboard     Portfolio risk overview
  bandit schedule      Reassessment schedule
  bandit register      Export TPRM register
  bandit notify        Send IT notifications

═══════════════════════════════════════════════════════════
SECTION 8 — Update bandit setup --notify
(cli/setup.py)
═══════════════════════════════════════════════════════════

The --notify flag currently collects email and
Slack channel (display name). Extend it to also
collect the Slack webhook URL, since that's what
the sender actually needs:

When --notify runs, collect:
  IT team email address    → it_contact_email
  Slack channel name       → it_slack_channel (display)
  Slack webhook URL        → slack_webhook_url

Save to bandit.config.yml:
  notifications:
    it_contact_email: "it@company.com"
    it_slack_channel: "#it-helpdesk"
    slack_webhook_url: "https://hooks.slack.com/..."

Add instructions in the prompt:
  Slack webhook URL can be found at:
  api.slack.com/apps → Incoming Webhooks → Add webhook
  Leave blank to use email only.

Also update get_it_contact() in core/config.py to
return slack_webhook_url from config.

═══════════════════════════════════════════════════════════
SECTION 9 — CHANGELOG and version bump
═══════════════════════════════════════════════════════════

9A. pyproject.toml → version = "1.4.0"

9B. cli/report.py → APP_VERSION = "1.4.0"

9C. CHANGELOG.md — add at top:

## [1.4.0] — 2026-04-09

### Architecture
- core/data/resolver.py: VendorDataResolver — unified
  data access layer for all commands. Knows whether
  vendor data lives locally or in Drive and fetches
  from the right place transparently. drive_folder_id
  stored in vendor profile — no search needed.
- All core/ modules return dataclasses, never print.
  CLI renders. Future UI calls core directly.
- on_progress callback pattern throughout for
  streaming-compatible progress reporting.
- --json flag on all new commands for UI API surface.

### Added

Dashboard
- bandit dashboard show — portfolio risk overview
  Risk distribution, due vendors, open findings,
  intake completion rate, Drive vs local breakdown
- bandit dashboard schedule — reassessment schedule
  Sorted by urgency, shows days overdue, recommended
  depth per vendor, data source (Drive/local)
- bandit dashboard register — TPRM register export
  CSV, JSON, or HTML output with all vendor data
- bandit dashboard notify — send IT notifications

Top-level aliases (convenience):
- bandit schedule
- bandit register [--format csv|json|html] [--out FILE]
- bandit notify [vendor] [--all]

Data resolver:
- VendorDataResolver used by bandit assess — replaces
  direct Drive/local document loading
- Deduplicates documents across sources (Drive wins)
- Sync failures never block assessment

Notifications:
- Slack webhook support (Incoming Webhooks)
- Email support via SMTP
- bandit setup --notify extended: collects webhook URL
- Notifications marked sent in vendor profile
- bandit notify --all sends all pending

═══════════════════════════════════════════════════════════
SECTION 10 — Testing checklist
═══════════════════════════════════════════════════════════

Test in this order after all sections complete:

1. Dashboard
   bandit dashboard show
   bandit dashboard show --risk HIGH
   bandit dashboard show --due
   bandit dashboard show --json | python3 -m json.tool
   Verify: table renders, JSON is valid

2. Schedule
   bandit schedule
   bandit schedule --due
   bandit schedule --within 30
   bandit schedule --json | python3 -m json.tool
   Verify: urgency sorting correct, dates accurate

3. Register export
   bandit register                     # CSV to stdout
   bandit register --format json       # JSON to stdout
   bandit register --format html       # saves HTML file
   bandit register --out test.csv      # saves to path
   Verify: CSV opens in spreadsheet correctly

4. Notify
   bandit notify "Cyera"               # single vendor
   bandit notify --all                 # all pending
   bandit notify --all --json
   Verify: fails gracefully if no channel configured

5. Resolver
   bandit assess "Cyera" --drive --verbose
   Verify: uses resolver, shows "Loading Drive documents"
   Verify: deduplicates if same file in local + Drive

6. Top-level aliases
   bandit schedule
   bandit register
   bandit notify --all
   Verify: same output as dashboard subcommands

7. JSON API surface (for future UI)
   bandit dashboard show --json
   bandit schedule --json
   bandit notify --all --json
   All should produce valid, parseable JSON with no
   extra text mixed in.

═══════════════════════════════════════════════════════════
FINAL COMMIT
═══════════════════════════════════════════════════════════

git add -A
git commit -m "feat: v1.4 dashboard, scheduling, register,
notifications + unified data resolver

Architecture:
- core/data/resolver.py: VendorDataResolver — unified
  data access, Drive-aware, on_progress callbacks
- All core/ modules return dataclasses, never print
- --json flag on all commands for future UI API surface

Features:
- bandit dashboard show: portfolio risk overview
- bandit schedule: reassessment schedule with urgency
- bandit register: TPRM export (CSV/JSON/HTML)
- bandit notify: IT notification sender (Slack + email)
- Top-level aliases: schedule, register, notify
- bandit assess now uses VendorDataResolver

Notifications:
- Slack Incoming Webhook support
- SMTP email support
- bandit setup --notify extended with webhook URL
- Marked sent in vendor profile after successful send

pyproject.toml: version 1.4.0
CHANGELOG.md: v1.4.0 entry"

git push origin main
