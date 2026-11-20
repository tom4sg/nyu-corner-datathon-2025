"""Build backend/data/place_media.json from datasets/media.csv.

Run from the repo root: python scripts/build_place_media.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

MAX_PHOTOS = 3

root = Path(__file__).resolve().parent.parent
media = defaultdict(list)

with (root / "datasets" / "media.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        urls = media[row["place_id"]]
        url = (row["media_url"] or "").strip()
        if url.startswith("https://") and url not in urls and len(urls) < MAX_PHOTOS:
            urls.append(url)

out = root / "backend" / "data" / "place_media.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(media, separators=(",", ":")))
print(f"Wrote {len(media)} places to {out}")
