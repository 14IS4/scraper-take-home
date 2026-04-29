from __future__ import annotations

from pathlib import Path

from tabs_scraper.config import load_urls


def test_load_urls_skips_blanks_and_comments(tmp_path: Path) -> None:
    f = tmp_path / "urls.txt"
    f.write_text(
        "\n"
        "# top comment\n"
        "https://www.tdlr.texas.gov/TABS/Project/A\n"
        "\n"
        "  # indented comment is also dropped (we strip before testing for #)\n"
        "https://www.tdlr.texas.gov/TABS/Project/B\n"
        "\n"
    )
    urls = load_urls(f)
    assert urls == [
        "https://www.tdlr.texas.gov/TABS/Project/A",
        "https://www.tdlr.texas.gov/TABS/Project/B",
    ]


def test_load_urls_dedupes_preserving_order(tmp_path: Path) -> None:
    f = tmp_path / "urls.txt"
    f.write_text(
        "https://www.tdlr.texas.gov/TABS/Project/A\n"
        "https://www.tdlr.texas.gov/TABS/Project/B\n"
        "https://www.tdlr.texas.gov/TABS/Project/A\n"
        "https://www.tdlr.texas.gov/TABS/Project/C\n"
    )
    assert load_urls(f) == [
        "https://www.tdlr.texas.gov/TABS/Project/A",
        "https://www.tdlr.texas.gov/TABS/Project/B",
        "https://www.tdlr.texas.gov/TABS/Project/C",
    ]


def test_load_urls_strips_whitespace(tmp_path: Path) -> None:
    f = tmp_path / "urls.txt"
    f.write_text("   https://www.tdlr.texas.gov/TABS/Project/A   \n")
    assert load_urls(f) == ["https://www.tdlr.texas.gov/TABS/Project/A"]
