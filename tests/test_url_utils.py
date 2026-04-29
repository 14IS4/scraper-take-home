from __future__ import annotations

import pytest

from tabs_scraper.url_utils import to_print_url


@pytest.mark.parametrize(
    ("input_url", "expected"),
    [
        (
            "https://www.tdlr.texas.gov/TABS/Project/TABS2024012754",
            "https://www.tdlr.texas.gov/TABS/Search/Print/TABS2024012754",
        ),
        (
            "https://www.tdlr.texas.gov/TABS/Projects/TABS2019009611",
            "https://www.tdlr.texas.gov/TABS/Search/Print/TABS2019009611",
        ),
        (
            "https://www.tdlr.texas.gov/TABS/Search/Print/EABPRJ99003417",
            "https://www.tdlr.texas.gov/TABS/Search/Print/EABPRJ99003417",
        ),
        (
            "https://www.tdlr.texas.gov/TABS/Project/TABS2024012754/",
            "https://www.tdlr.texas.gov/TABS/Search/Print/TABS2024012754",
        ),
        (
            "https://www.tdlr.texas.gov/TABS/Project/eabprj93000456",
            "https://www.tdlr.texas.gov/TABS/Search/Print/EABPRJ93000456",
        ),
    ],
)
def test_to_print_url_normalizes(input_url: str, expected: str) -> None:
    assert to_print_url(input_url) == expected


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://www.tdlr.texas.gov/TABS/Search/",
        "https://example.com/foo/bar",
        "not a url",
        "",
    ],
)
def test_to_print_url_rejects_invalid(bad_url: str) -> None:
    with pytest.raises(ValueError, match="Cannot extract TABS project ID"):
        to_print_url(bad_url)
