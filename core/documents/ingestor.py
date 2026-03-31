"""
Bandit Document Ingestor
=========================
Orchestrates the full document pipeline.
Agents call this — not extractor/classifier directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.documents.extractor import (
    DocumentExtractor, ExtractionResult, SUPPORTED_EXTENSIONS
)
from core.documents.classifier import (
    DocumentClassifier, ClassificationResult, DocumentType
)


@dataclass
class IngestedDocument:
    file_path: str
    file_name: str
    doc_type: DocumentType
    type_confidence: float
    type_method: str
    text: str
    char_count: int
    page_count: int
    extraction_ok: bool
    error: str | None


@dataclass
class IngestManifest:
    folder_path: str
    documents: list[IngestedDocument] = field(default_factory=list)
    failed: list[IngestedDocument] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    unknown_type: list[IngestedDocument] = field(default_factory=list)

    @property
    def ready_count(self) -> int:
        return len([
            d for d in self.documents
            if d.extraction_ok and d.doc_type != DocumentType.UNKNOWN
        ])

    @property
    def total_count(self) -> int:
        return len(self.documents)


class DocumentIngestor:

    def __init__(self, llm_provider=None):
        self.extractor = DocumentExtractor()
        self.classifier = DocumentClassifier()
        self.llm_provider = llm_provider

    def ingest_folder(
        self,
        folder_path: str,
        recursive: bool = True,
    ) -> IngestManifest:

        path = Path(folder_path)
        if not path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        manifest = IngestManifest(folder_path=str(path))

        if recursive:
            all_files = list(path.rglob("*"))
        else:
            all_files = list(path.iterdir())

        files = [f for f in all_files if f.is_file()]

        for file_path in files:
            ext = file_path.suffix.lower()

            # Skip hidden files
            if file_path.name.startswith("."):
                continue

            # Skip unsupported formats silently
            if ext not in SUPPORTED_EXTENSIONS:
                if ext not in {
                    ".xlsx", ".csv", ".zip",
                    ".png", ".jpg", ".jpeg",
                    ".gif", ".mp4", ".mov", ".DS_Store"
                }:
                    manifest.skipped.append(
                        f"{file_path.name} — unsupported format {ext}"
                    )
                continue

            doc = self.ingest_file(str(file_path))
            manifest.documents.append(doc)

            if not doc.extraction_ok:
                manifest.failed.append(doc)
            elif doc.doc_type == DocumentType.UNKNOWN:
                manifest.unknown_type.append(doc)

        return manifest

    def ingest_file(
        self,
        file_path: str,
        doc_type: DocumentType = None,
    ) -> IngestedDocument:

        extraction = self.extractor.extract(file_path)

        if not extraction.extraction_ok:
            return IngestedDocument(
                file_path=file_path,
                file_name=extraction.file_name,
                doc_type=doc_type or DocumentType.UNKNOWN,
                type_confidence=0.0,
                type_method="none",
                text="",
                char_count=0,
                page_count=extraction.page_count,
                extraction_ok=False,
                error=extraction.error,
            )

        if doc_type:
            classification = ClassificationResult(
                doc_type=doc_type,
                confidence=1.0,
                method="user_specified",
                reasoning="Specified by user",
            )
        else:
            classification = self.classifier.classify(
                file_path=file_path,
                extracted_text=extraction.text,
                llm_provider=self.llm_provider,
            )

        return IngestedDocument(
            file_path=file_path,
            file_name=extraction.file_name,
            doc_type=classification.doc_type,
            type_confidence=classification.confidence,
            type_method=classification.method,
            text=extraction.text,
            char_count=extraction.char_count,
            page_count=extraction.page_count,
            extraction_ok=True,
            error=None,
        )

    def show_manifest(self, manifest: IngestManifest) -> None:
        """Print document manifest to terminal using Rich."""
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()

        console.print(
            f"\n[bold dark_orange]Documents found in "
            f"{manifest.folder_path}[/bold dark_orange]"
        )

        if not manifest.documents:
            console.print("[dim]No supported documents found.[/dim]")
            return

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("File", style="white")
        table.add_column("Type", style="dark_orange")
        table.add_column("Confidence", justify="right")
        table.add_column("Status", justify="right")

        for doc in manifest.documents:
            if not doc.extraction_ok:
                status = "[red]✗ Failed[/red]"
                doc_type_str = "—"
                confidence = "—"
            elif doc.doc_type == DocumentType.UNKNOWN:
                status = "[yellow]? Unknown[/yellow]"
                doc_type_str = "Unknown"
                confidence = f"{doc.type_confidence:.0%}"
            else:
                status = "[green]✓ Ready[/green]"
                doc_type_str = doc.doc_type.value.replace("_", " ").title()
                confidence = f"{doc.type_confidence:.0%}"

            table.add_row(doc.file_name, doc_type_str, confidence, status)

        console.print(table)

        ready = manifest.ready_count
        total = manifest.total_count
        failed = len(manifest.failed)
        unknown = len(manifest.unknown_type)

        parts = [f"[green]{ready} ready[/green]"]
        if failed:
            parts.append(f"[red]{failed} failed[/red]")
        if unknown:
            parts.append(f"[yellow]{unknown} unknown type[/yellow]")

        console.print("  " + " · ".join(parts) + "\n")

        for doc in manifest.failed:
            console.print(
                f"  [red]✗ {doc.file_name}[/red]: [dim]{doc.error}[/dim]"
            )

        for msg in manifest.skipped:
            console.print(f"  [dim]— {msg}[/dim]")
