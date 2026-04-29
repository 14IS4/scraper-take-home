from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from tabs_scraper.parser import parse_print_html
from tabs_scraper.pipeline import STRICT_FIELDS, to_strict_dict, transform_to_permit

_FIXTURE = Path(__file__).parent / "fixtures" / "TABS2024012754.html"
_SOURCE_URL = "https://www.tdlr.texas.gov/TABS/Project/TABS2024012754"
_SCRAPED_AT = datetime(2026, 4, 28, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def parsed() -> dict[str, str]:
    return parse_print_html(_FIXTURE.read_text())


def test_transform_maps_required_schema(parsed: dict[str, str]) -> None:
    permit = transform_to_permit(parsed, _SOURCE_URL, _SCRAPED_AT)
    assert permit.event_id == "TABS2024012754"
    assert permit.address == "340 Bucees Blvd, Melissa, TX 75454"
    assert permit.event_created_at == date(2024, 3, 8)
    assert permit.category == "New Construction"


def test_description_concatenates_three_fields(parsed: dict[str, str]) -> None:
    permit = transform_to_permit(parsed, _SOURCE_URL, _SCRAPED_AT)
    assert permit.description.startswith("Bucees Blvd Retail")
    assert "New Construction" in permit.description
    assert "10,245 SF shell retail building" in permit.description
    # double newline as separator between the three source fields
    assert permit.description.count("\n\n") == 2


def test_provenance_fields_set(parsed: dict[str, str]) -> None:
    permit = transform_to_permit(parsed, _SOURCE_URL, _SCRAPED_AT)
    assert permit.source_url == _SOURCE_URL
    assert permit.scraped_at == _SCRAPED_AT
    assert permit.parser_version == "1.0.0"


def test_raw_fields_preserves_full_page(parsed: dict[str, str]) -> None:
    permit = transform_to_permit(parsed, _SOURCE_URL, _SCRAPED_AT)
    # raw_fields keeps every label from the page so future schemas can replay
    # without re-scraping.
    for key in (
        "Project Number",
        "Facility Name",
        "Location County",
        "Estimated Cost",
        "Owner Name",
        "Design Firm Name",
        "Square Footage",
        "Current Status",
    ):
        assert key in permit.raw_fields, f"missing raw_field: {key}"


def test_missing_required_field_raises() -> None:
    incomplete = {
        "Project Name": "X",
        "Type of Work": "Y",
        "Start Date": "1/1/2024",
        # "Project Number" missing
        "Location Address": "addr",
    }
    with pytest.raises(KeyError, match="Project Number"):
        transform_to_permit(incomplete, _SOURCE_URL, _SCRAPED_AT)


def test_strict_dict_contains_only_assignment_fields(parsed: dict[str, str]) -> None:
    permit = transform_to_permit(parsed, _SOURCE_URL, _SCRAPED_AT)
    strict = to_strict_dict(permit)
    # Exact set, no provenance, no raw_fields
    assert set(strict.keys()) == set(STRICT_FIELDS)
    # Order matches the assignment spec
    assert tuple(strict.keys()) == STRICT_FIELDS
    # Date is serialized as ISO string for JSON compatibility
    assert strict["event_created_at"] == "2024-03-08"
    assert strict["event_id"] == "TABS2024012754"
    assert strict["category"] == "New Construction"


def test_bad_date_raises_value_error() -> None:
    bad = {
        "Project Number": "X",
        "Project Name": "X",
        "Type of Work": "Y",
        "Scope of Work": "Z",
        "Start Date": "not-a-date",
        "Location Address": "addr",
    }
    with pytest.raises(ValueError, match="not-a-date"):
        transform_to_permit(bad, _SOURCE_URL, _SCRAPED_AT)
