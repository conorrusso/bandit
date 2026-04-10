"""
Tests for the portfolio dashboard module.

get_summary() reads from VendorProfileCache, so tests use a temporary
cache file and patch the module-level cache to use it.
"""
import pathlib
import tempfile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import pytest

from core.profiles.vendor_cache import VendorProfile, VendorProfileCache
from core.dashboard.portfolio import get_summary, PortfolioSummary


def _make_profile(
    name: str,
    risk_tier: str | None = None,
    next_due: str | None = None,
    intake_completed: bool = False,
    drive_folder_id: str | None = None,
    status: str = "active",
    history: list | None = None,
) -> VendorProfile:
    p = VendorProfile(
        vendor_name=name,
        vendor_slug=name.lower().replace(" ", "-"),
        functions=[],
        detection_method="test",
        intake_completed=intake_completed,
        drive_folder_id=drive_folder_id,
    )
    p.current_risk_tier = risk_tier
    p.next_due = next_due
    p.assessment_history = history or []
    if history:
        p.last_assessed = history[0].get("assessment_date")
    if risk_tier and history is None:
        # Ensure a non-empty history so avg can be read
        p.assessment_history = [
            {"risk_tier": risk_tier, "weighted_average": 3.0,
             "assessment_date": "2026-01-01"}
        ]
    return p


def _patch_cache(profiles: list[VendorProfile]):
    """Return a mock VendorProfileCache that returns the given profiles."""
    mock_cache = MagicMock(spec=VendorProfileCache)
    mock_cache.list_all.return_value = profiles
    return mock_cache


class TestGetSummaryEmpty:
    def test_empty_cache_returns_zero_counts(self):
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache([]),
        ):
            summary = get_summary()
        assert summary.total_vendors == 0
        assert summary.risk_distribution.high == 0
        assert summary.risk_distribution.medium == 0
        assert summary.risk_distribution.low == 0
        assert summary.risk_distribution.unassessed == 0
        assert summary.vendors_overdue == 0
        assert summary.vendors == []

    def test_returns_portfolio_summary_type(self):
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache([]),
        ):
            summary = get_summary()
        assert isinstance(summary, PortfolioSummary)


class TestRiskDistribution:
    def test_risk_distribution_counts(self):
        profiles = [
            _make_profile("A", risk_tier="HIGH"),
            _make_profile("B", risk_tier="HIGH"),
            _make_profile("C", risk_tier="MEDIUM"),
            _make_profile("D", risk_tier="LOW"),
        ]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary()
        assert summary.risk_distribution.high == 2
        assert summary.risk_distribution.medium == 1
        assert summary.risk_distribution.low == 1
        assert summary.risk_distribution.unassessed == 0
        assert summary.total_vendors == 4

    def test_unassessed_vendor_counted_separately(self):
        profiles = [
            _make_profile("Assessed", risk_tier="HIGH"),
            _make_profile("Unassessed"),  # no risk tier
        ]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary()
        assert summary.risk_distribution.unassessed == 1
        assert summary.total_vendors == 2


class TestOverdueDetection:
    def test_past_due_date_is_overdue(self):
        past = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        profiles = [_make_profile("OldVendor", risk_tier="HIGH", next_due=past)]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary()
        assert summary.vendors_overdue == 1
        assert summary.vendors[0].overdue is True
        assert summary.vendors[0].days_overdue >= 30

    def test_future_due_date_not_overdue(self):
        future = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        profiles = [_make_profile("FreshVendor", risk_tier="LOW", next_due=future)]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary()
        assert summary.vendors_overdue == 0
        assert summary.vendors[0].overdue is False

    def test_no_next_due_with_history_counted_as_due(self):
        """Vendor that has been assessed but has no next_due is flagged."""
        p = _make_profile("NoNextDue", risk_tier="MEDIUM")
        p.next_due = None
        p.assessment_history = [
            {"risk_tier": "MEDIUM", "weighted_average": 3.0,
             "assessment_date": "2025-01-01"}
        ]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache([p]),
        ):
            summary = get_summary()
        assert summary.vendors_due >= 1


class TestFilters:
    def _profiles(self):
        return [
            _make_profile("H1", risk_tier="HIGH"),
            _make_profile("H2", risk_tier="HIGH"),
            _make_profile("M1", risk_tier="MEDIUM"),
            _make_profile("L1", risk_tier="LOW"),
        ]

    def test_risk_filter_high(self):
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(self._profiles()),
        ):
            summary = get_summary(risk_filter="HIGH")
        assert all(v.risk_tier == "HIGH" for v in summary.vendors)
        assert len(summary.vendors) == 2

    def test_overdue_only_filter(self):
        past = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        future = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        profiles = [
            _make_profile("Overdue", risk_tier="HIGH", next_due=past),
            _make_profile("Fine", risk_tier="LOW", next_due=future),
        ]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary(overdue_only=True)
        assert len(summary.vendors) == 1
        assert summary.vendors[0].vendor_name == "Overdue"


class TestDriveVendorCount:
    def test_drive_vendor_counted_correctly(self):
        profiles = [
            _make_profile("DriveVendor", drive_folder_id="abc123"),
            _make_profile("LocalVendor"),
        ]
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache(profiles),
        ):
            summary = get_summary()
        assert summary.drive_vendors == 1
        assert summary.local_only_vendors == 1


class TestToJson:
    def test_to_json_is_valid_json(self):
        import json
        with patch(
            "core.dashboard.portfolio.VendorProfileCache",
            return_value=_patch_cache([]),
        ):
            summary = get_summary()
        payload = json.loads(summary.to_json())
        assert "total_vendors" in payload
        assert "risk_distribution" in payload
