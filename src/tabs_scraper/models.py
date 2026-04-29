from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from tabs_scraper.config import PARSER_VERSION


class TabsPermit(BaseModel):
    event_id: str
    address: str
    event_created_at: date
    description: str
    category: str
    # Keep all other fields for future replayability
    raw_fields: dict[str, str] = Field(default_factory=dict)
    # Metadata columns
    source_url: str
    scraped_at: datetime
    parser_version: str = PARSER_VERSION
