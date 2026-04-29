from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from tabs_scraper.models import TabsPermit


def _sample_permit() -> TabsPermit:
    return TabsPermit(
        event_id="TABS2024012754",
        address="340 Bucees Blvd, Melissa, TX 75454",
        event_created_at=date(2024, 3, 8),
        description="Bucees Blvd Retail\n\nNew Construction\n\n10,245 SF shell retail building",
        category="New Construction",
        raw_fields={"Project Name": "Bucees Blvd Retail", "Location County": "Collin"},
        source_url="https://www.tdlr.texas.gov/TABS/Project/TABS2024012754",
        scraped_at=datetime(2026, 4, 28, 23, 0, 0, tzinfo=UTC),
    )


def test_json_round_trip() -> None:
    permit = _sample_permit()
    assert permit.parser_version == "1.0.0"
    payload = permit.model_dump(mode="json")
    # JSON-mode serializes date/datetime to ISO strings
    assert payload["event_created_at"] == "2024-03-08"
    assert payload["scraped_at"].startswith("2026-04-28")
    # round-trips through json.dumps without TypeError
    json.dumps(payload)
    # and reconstructs cleanly
    restored = TabsPermit.model_validate(payload)
    assert restored == permit


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        TabsPermit(
            event_id="TABS2024012754",
            address="some address",
            # event_created_at omitted for testing
            description="d",
            category="c",
            source_url="https://example.com",
            scraped_at=datetime.now(UTC),
        )
