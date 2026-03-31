"""
Bandit Drive Document Ingestor
================================
Bridges GoogleDriveClient with DocumentIngestor.
Downloads vendor documents from Google Drive and ingests them.
"""
from __future__ import annotations

import tempfile

from core.integrations.google_drive import GoogleDriveClient
from core.documents.ingestor import DocumentIngestor, IngestManifest


class DriveDocumentIngestor:

    def __init__(self, llm_provider=None):
        self.drive = GoogleDriveClient()
        self.ingestor = DocumentIngestor(llm_provider)

    def ingest_vendor_from_drive(
        self,
        vendor_name: str,
        drive_folder_id: str,
    ) -> IngestManifest:
        """Download vendor documents from Drive and ingest them.

        Uses a temp directory that is cleaned up after ingestion.
        """
        self.drive.authenticate()

        with tempfile.TemporaryDirectory(prefix="bandit_drive_") as tmp_dir:
            local_paths = self.drive.download_vendor_documents(
                vendor_name=vendor_name,
                parent_folder_id=drive_folder_id,
                temp_dir=tmp_dir,
            )

            if not local_paths:
                return IngestManifest(folder_path=f"Drive/{vendor_name}")

            manifest = IngestManifest(folder_path=f"Drive/{vendor_name}")
            for path in local_paths:
                doc = self.ingestor.ingest_file(path)
                manifest.documents.append(doc)
                if not doc.extraction_ok:
                    manifest.failed.append(doc)

            return manifest
