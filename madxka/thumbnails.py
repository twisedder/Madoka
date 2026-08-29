from __future__ import annotations

from typing import Any

from madxka.urls import thumb_url

THUMB_BATCH = 200
THUMB_SIZE = "420x420"
THUMB_FORMAT = "png"


def parse_thumb_rows(rows: list[Any]) -> dict[int, str | None]:
    out: dict[int, str | None] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        target_id = int(row.get("targetId") or 0)
        if not target_id:
            continue
        raw = row.get("imageUrl")
        out[target_id] = thumb_url(str(raw)) if raw else None
    return out
