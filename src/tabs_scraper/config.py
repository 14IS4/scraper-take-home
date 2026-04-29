from __future__ import annotations

from pathlib import Path

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 30.0
DEFAULT_URLS_FILE = Path("urls.txt")
PARSER_VERSION = "1.0.0"

USER_AGENT = "Mercator-TABS-Scraper/1.0 (contact: kendrick@horeft.is)"


def load_urls(path: Path) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in seen:
            continue
        seen.add(line)
        urls.append(line)
    return urls
