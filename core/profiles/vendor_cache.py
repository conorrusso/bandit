"""
Bandit Vendor Profile Cache
============================
Persists detected vendor function profiles to ~/.bandit/vendor-profiles.json.
Allows reuse across assessments without re-running detection.
"""
from __future__ import annotations

import json
import pathlib
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Any

CACHE_PATH = pathlib.Path.home() / ".bandit" / "vendor-profiles.json"


@dataclass
class VendorProfile:
    """Persisted vendor function profile."""
    vendor_name: str
    vendor_slug: str
    functions: list[str]          # serialised as string values
    detection_method: str         # "known_vendor" | "domain_match" | "keyword" | "manual" | "unknown"
    vendor_country: str | None = None
    phi_processor: bool = False
    pci_processor: bool = False
    children_data: bool = False
    last_updated: str = ""
    notes: str | None = None

    def function_labels(self) -> list[str]:
        """Return human-readable function labels."""
        from core.profiles.vendor_functions import FUNCTION_LABELS, VendorFunction
        labels = []
        for f in self.functions:
            try:
                labels.append(FUNCTION_LABELS[VendorFunction(f)])
            except (ValueError, KeyError):
                labels.append(f)
        return labels


class VendorProfileCache:
    """Read/write vendor profiles to a JSON cache file."""

    def __init__(self, path: pathlib.Path = CACHE_PATH) -> None:
        self._path = path

    def get(self, vendor_name: str) -> VendorProfile | None:
        """Return cached profile for vendor_name, or None."""
        cache = self._read()
        key = vendor_name.lower().strip()
        entry = cache.get(key)
        if not entry:
            return None
        try:
            return VendorProfile(**entry)
        except (TypeError, KeyError):
            return None

    def save(self, vendor_name: str, profile: VendorProfile) -> None:
        """Persist a vendor profile."""
        cache = self._read()
        key = vendor_name.lower().strip()
        cache[key] = asdict(profile)
        self._write(cache)

    def list_all(self) -> list[VendorProfile]:
        """Return all cached profiles."""
        cache = self._read()
        profiles: list[VendorProfile] = []
        for entry in cache.values():
            try:
                profiles.append(VendorProfile(**entry))
            except (TypeError, KeyError):
                pass
        return sorted(profiles, key=lambda p: p.vendor_name.lower())

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, cache: dict) -> None:
        """Atomically write cache to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = pathlib.Path(tempfile.mktemp(dir=self._path.parent, suffix=".tmp"))
            tmp.write_text(json.dumps(cache, indent=2))
            tmp.replace(self._path)
        except OSError:
            pass


# Module-level singleton
profile_cache = VendorProfileCache()
