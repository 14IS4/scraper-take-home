"""Orchestrate the scrape: fetch -> parse -> transform -> write JSON.

The pipeline owns per-URL error containment: one bad page (fetch error,
unexpected HTML, missing required field) is logged and skipped, but does
not sink the rest of the batch. The client layer stays fail-fast; this
layer is where partial-success semantics live.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from tabs_scraper.client import fetch_one
from tabs_scraper.config import MAX_CONCURRENCY, PARSER_VERSION, REQUEST_TIMEOUT, USER_AGENT
from tabs_scraper.models import TabsPermit
from tabs_scraper.parser import parse_print_html

logger = logging.getLogger(__name__)

# Outputs specific fields for assignment
STRICT_FIELDS: tuple[str, ...] = (
    "event_id",
    "address",
    "event_created_at",
    "description",
    "category",
)

# TDLR <dt> labels we map into the permit schema. Centralized so the
# parser-key contract lives in one place.
SRC_PROJECT_NUMBER = "Project Number"
SRC_PROJECT_NAME = "Project Name"
SRC_LOCATION_ADDRESS = "Location Address"
SRC_START_DATE = "Start Date"
SRC_TYPE_OF_WORK = "Type of Work"
SRC_SCOPE_OF_WORK = "Scope of Work"

_DATE_FORMAT = "%m/%d/%Y"


def to_strict_dict(permit: TabsPermit) -> dict[str, Any]:
    """Return only the assignment-required fields — no provenance, no raw_fields."""
    return permit.model_dump(mode="json", include=set(STRICT_FIELDS))


def transform_to_permit(
    raw: dict[str, str],
    source_url: str,
    scraped_at: datetime,
) -> TabsPermit:
    """Map a parsed raw dict into a TabsPermit.

    Required source fields raise KeyError if missing — these are the contract
    with the assignment schema. Optional fields used in the description fall
    back to empty string and are dropped from the join.
    """
    description_parts = [
        raw.get(SRC_PROJECT_NAME, ""),
        raw.get(SRC_TYPE_OF_WORK, ""),
        raw.get(SRC_SCOPE_OF_WORK, ""),
    ]
    description = "\n\n".join(p for p in description_parts if p)

    event_created_at = datetime.strptime(raw[SRC_START_DATE], _DATE_FORMAT).date()

    return TabsPermit(
        event_id=raw[SRC_PROJECT_NUMBER],
        address=raw[SRC_LOCATION_ADDRESS],
        event_created_at=event_created_at,
        description=description,
        category=raw[SRC_TYPE_OF_WORK],
        raw_fields=dict(raw),
        source_url=source_url,
        scraped_at=scraped_at,
        parser_version=PARSER_VERSION,
    )


async def _fetch_all_safe(urls: list[str]) -> list[tuple[str, str | BaseException]]:
    """Fetch every URL, capturing exceptions per-URL instead of failing the batch."""
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers=headers,
        follow_redirects=True,
    ) as client:
        results = await asyncio.gather(
            *(fetch_one(client, u, sem) for u in urls),
            return_exceptions=True,
        )
    paired: list[tuple[str, str | BaseException]] = []
    for url, result in zip(urls, results, strict=True):
        if isinstance(result, BaseException):
            paired.append((url, result))
        else:
            _, html = result
            paired.append((url, html))
    return paired


def _write_json(payload: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


async def run(
    urls: list[str],
    output_path: Path | None = None,
    strict_output_path: Path | None = None,
) -> int:
    """Scrape all URLs and write JSON output.

    Exactly one of `output_path` (full payload incl. provenance + raw_fields)
    or `strict_output_path` (5 assignment-schema fields only) should be set.
    Both being set writes both files; neither set raises ValueError.

    Returns the number of failures (URLs that did not produce a permit).
    """
    if output_path is None and strict_output_path is None:
        raise ValueError("at least one of output_path or strict_output_path is required")

    logger.info("starting scrape: %d URL(s)", len(urls))
    fetch_results = await _fetch_all_safe(urls)

    permits: list[TabsPermit] = []
    failures = 0
    scraped_at = datetime.now(UTC)

    for source_url, payload in fetch_results:
        if isinstance(payload, BaseException):
            logger.error("fetch failed for %s: %s", source_url, payload)
            failures += 1
            continue
        try:
            raw = parse_print_html(payload)
            permit = transform_to_permit(raw, source_url, scraped_at)
        except Exception:
            logger.exception("parse/transform failed for %s", source_url)
            failures += 1
            continue
        permits.append(permit)
        logger.info("ok %s -> event_id=%s", source_url, permit.event_id)

    if output_path is not None:
        _write_json([p.model_dump(mode="json") for p in permits], output_path)
        logger.info(
            "wrote %d permit(s) to %s (%d failure(s))", len(permits), output_path, failures
        )

    if strict_output_path is not None:
        _write_json([to_strict_dict(p) for p in permits], strict_output_path)
        logger.info(
            "wrote %d strict permit(s) to %s (%d failure(s))",
            len(permits),
            strict_output_path,
            failures,
        )

    return failures
