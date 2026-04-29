"""
Parses HTML into a flattened dictionary of <dt>/<dd> pairs.

Keeps the parser dumb: no field mapping, no type conversion. The pipeline
layer is responsible for turning this dict into a TabsPermit.

Edge cases:
- Multiple <dd> siblings after one <dt> are joined with ", ".
- <sup> tags fall through .get_text() as plain text (e.g. "10,245 ft 2").
- Internal whitespace (newlines, indentation) is collapsed.
- Duplicate <dt> labels are namespaced with their parent section's <h4>.
- <p>Not Assigned</p> placeholder sections are skipped.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

_BODY_SELECTOR = "div.project-details-print div.project-details-body"
_WHITESPACE_RE = re.compile(r"\s+")


def parse_print_html(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
    body = soup.select_one(_BODY_SELECTOR)
    if body is None:
        raise ValueError("Could not find div.project-details-body — page format may have changed")

    out: dict[str, str] = {}
    for section in body.find_all("div", recursive=False):
        if not isinstance(section, Tag):
            continue
        section_label = _section_label(section)
        for dt in section.find_all("dt"):
            key = _clean_text(dt.get_text())
            if not key:
                continue
            value = _collect_dd_value(dt)
            if value is None:
                continue
            out[_resolve_key(out, key, section_label)] = value
    return out


def _resolve_key(out: dict[str, str], key: str, section_label: str) -> str:
    """Return a non-colliding key, namespacing with section then a numeric suffix."""
    if key not in out:
        return key
    namespaced = f"{section_label} {key}".strip()
    if namespaced and namespaced != key and namespaced not in out:
        return namespaced
    suffix = 2
    while f"{namespaced} ({suffix})" in out:
        suffix += 1
    return f"{namespaced} ({suffix})"


def _section_label(section: Tag) -> str:
    h4 = section.find("h4")
    if h4 is None:
        return ""
    return _clean_text(h4.get_text())


def _collect_dd_value(dt: Tag) -> str | None:
    parts: list[str] = []
    for sibling in dt.find_next_siblings():
        if not isinstance(sibling, Tag):
            continue
        if sibling.name == "dt":
            break
        if sibling.name != "dd":
            continue
        text = _clean_text(sibling.get_text())
        if text:
            parts.append(text)
    if not parts:
        return None
    return ", ".join(parts)


def _clean_text(text: str) -> str:
    stripped = text.strip().rstrip(":").strip()
    return _WHITESPACE_RE.sub(" ", stripped)
