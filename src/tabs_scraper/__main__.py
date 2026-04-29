"""CLI entrypoint: `python -m tabs_scraper [--urls-file URLS] [--output PATH]`."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from tabs_scraper.config import DEFAULT_URLS_FILE, load_urls
from tabs_scraper.pipeline import run


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tabs_scraper",
        description="Scrape Texas TABS permits to JSON.",
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        default=DEFAULT_URLS_FILE,
        help=f"Newline-separated URL list (default: {DEFAULT_URLS_FILE})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/permits.json"),
        help="Destination JSON file with full payload (default: output/permits.json)",
    )
    parser.add_argument(
        "--strict-output",
        type=Path,
        default=Path("output/permits.strict.json"),
        help=(
            "Path used for strict output when --strict is set. "
            "(default: output/permits.strict.json)"
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Write only the assignment-schema JSON (event_id, address, "
            "event_created_at, description, category) to --strict-output. "
            "Suppresses the full --output file."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    urls = load_urls(args.urls_file)
    if not urls:
        logging.getLogger(__name__).error("no URLs found in %s", args.urls_file)
        return 2
    if args.strict:
        failures = asyncio.run(run(urls, strict_output_path=args.strict_output))
    else:
        failures = asyncio.run(run(urls, output_path=args.output))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
