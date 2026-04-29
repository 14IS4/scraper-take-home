from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from tabs_scraper.parser import parse_print_html

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "TABS2024012754.html"


def _load_fixture() -> str:
    return _FIXTURE_PATH.read_text()


@pytest.fixture(scope="module")
def parsed() -> dict[str, str]:
    return parse_print_html(_load_fixture())


def test_parses_required_source_labels(parsed: dict[str, str]) -> None:
    assert parsed["Project Number"] == "TABS2024012754"
    assert parsed["Project Name"] == "Bucees Blvd Retail"
    assert parsed["Type of Work"] == "New Construction"
    assert parsed["Start Date"] == "3/8/2024"
    assert parsed["Location Address"] == "340 Bucees Blvd, Melissa, TX 75454"
    assert parsed["Scope of Work"].startswith("10,245 SF shell retail building")


def test_address_joins_with_comma_space(parsed: dict[str, str]) -> None:
    assert parsed["Location Address"] == "340 Bucees Blvd, Melissa, TX 75454"
    assert parsed["Owner Address"] == "430 Churchill Ln, Pottsboro, Texas 75076"
    assert parsed["Design Firm Address"] == "218 Emily Ln, Van Alstyne, Texas 75495"


def test_raw_fields_includes_all_expected_keys(parsed: dict[str, str]) -> None:
    expected = {
        "Facility Name",
        "Location County",
        "Estimated Cost",
        "Owner Name",
        "Owner Address",
        "Owner Phone",
        "Current Status",
        "Square Footage",
        "Design Firm Name",
        "Design Firm Phone",
    }
    missing = expected - parsed.keys()
    assert not missing, f"missing keys: {missing}"
    assert len(parsed) >= 15, f"expected >= 15 fields, got {len(parsed)}: {sorted(parsed)}"


def test_duplicate_contact_name_namespaced_by_section(parsed: dict[str, str]) -> None:
    assert parsed["Contact Name"] == "Bruce Green"
    assert parsed["OWNER Contact Name"] == "Steve Palmer"


def test_current_status_whitespace_collapsed(parsed: dict[str, str]) -> None:
    assert parsed["Current Status"] == "Review Complete"


def test_square_footage_sup_falls_through_as_plain_text(parsed: dict[str, str]) -> None:
    assert parsed["Square Footage"] == "10,245 ft 2"


def test_start_date_parses_via_strptime(parsed: dict[str, str]) -> None:
    parsed_date = datetime.strptime(parsed["Start Date"], "%m/%d/%Y").date()
    assert parsed_date == date(2024, 3, 8)


def test_missing_dt_does_not_crash() -> None:
    html = (
        '<div class="project-details-print">'
        '<div class="project-details-body">'
        "<div><h4>X</h4><p>Not Assigned</p></div>"
        "</div></div>"
    )
    assert parse_print_html(html) == {}


def test_missing_body_raises_value_error() -> None:
    with pytest.raises(ValueError, match="project-details-body"):
        parse_print_html("<html><body><p>nothing here</p></body></html>")
