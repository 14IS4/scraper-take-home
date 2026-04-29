from __future__ import annotations

import re
from urllib.parse import urlparse

PRINT_URL_TEMPLATE = "https://www.tdlr.texas.gov/TABS/Search/Print/{project_id}"

PROJECT_ID_RE = re.compile(
    r"/TABS/(?:Project|Projects|Search/Print)/([A-Z0-9]+)/?$",
    re.IGNORECASE,
)


def to_print_url(url: str) -> str:
    match = PROJECT_ID_RE.search(urlparse(url).path)
    if not match:
        raise ValueError(f"Cannot extract TABS project ID from URL: {url}")
    return PRINT_URL_TEMPLATE.format(project_id=match.group(1).upper())
