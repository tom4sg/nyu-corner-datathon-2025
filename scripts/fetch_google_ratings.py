"""Match each venue to a Google place once and store the star rating.

Text Search stays on Pro fields, which are inside the free monthly cap at this
catalog size. Place Details is called only after a name-and-distance match,
and only for the rating and review count.
"""

import csv
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
PLACES = ROOT / "datasets" / "places.csv"
OUT = ROOT / "backend" / "data" / "google_ratings.json"
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
WORKERS = 3
_PACE = Lock()
_NEXT = 0.0


def pace():
    global _NEXT
    with _PACE:
        now = time.monotonic()
        wait = _NEXT - now
        _NEXT = max(now, _NEXT) + 0.25
    if wait > 0:
        time.sleep(wait)


def load_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("GOOGLE_PLACES_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GOOGLE_PLACES_API_KEY is missing from .env")


def norm(value: str) -> str:
    text = value.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def name_score(left: str, right: str) -> float:
    a, b = norm(left), norm(right)
    if not a or not b:
        return 0
    if a == b:
        return 1
    if a in b or b in a:
        return 0.9
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0
    return len(ta & tb) / len(ta | tb)


def meters(lat1, lon1, lat2, lon2) -> float:
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    hav = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(hav))


def request(url: str, key: str, mask: str, body: dict | None = None) -> dict:
    pace()
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(8):
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": mask,
            },
            method="POST" if body is not None else "GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")
            if key:
                detail = detail.replace(key, "[key]")
            last = f"{err.code} {detail[:300]}"
            if err.code not in (429, 500, 503):
                raise RuntimeError(last)
            time.sleep(65 if err.code == 429 else 1.5 * (attempt + 1))
        except urllib.error.URLError as err:
            last = str(err.reason)
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(last or "request failed")


def same_pin(name: str, gname: str, dist: float | None) -> bool:
    if dist is None or dist > 60:
        return False
    a, b = norm(name), norm(gname)
    if not a or not b:
        return False
    compact_a, compact_b = a.replace(" ", ""), b.replace(" ", "")
    if compact_a in compact_b or compact_b in compact_a:
        return True
    stop = {"the", "and", "bar", "cafe", "coffee"}
    for token in a.split():
        if len(token) >= 3 and token not in stop and token in b.split():
            return True
    return False


def choose(candidates: list, name: str, lat: float, lon: float):
    best = None
    best_rank = None
    for place in candidates:
        gname = ((place.get("displayName") or {}).get("text")) or ""
        score = name_score(name, gname)
        loc = place.get("location") or {}
        dist = None
        if loc.get("latitude") is not None and loc.get("longitude") is not None:
            dist = meters(lat, lon, float(loc["latitude"]), float(loc["longitude"]))
        pinned = same_pin(name, gname, dist)
        if score < 0.67 and not pinned:
            continue
        if dist is not None and not pinned and (dist > 1500 or (dist > 600 and score < 1)):
            continue
        elif dist is None and score < 0.9:
            continue
        rank = (1 if pinned else 0, score, -(dist if dist is not None else 9999))
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best = place
    return best


def lookup(row: dict, key: str) -> dict:
    name = row["name"]
    neighborhood = (row.get("neighborhood") or "").strip()
    if neighborhood.lower() == "nan":
        neighborhood = ""
    area = neighborhood or "New York"
    lat, lon = float(row["latitude"]), float(row["longitude"])
    found = request(
        SEARCH_URL,
        key,
        "places.id,places.displayName,places.location",
        {
            "textQuery": f"{name}, {area}, New York",
            "pageSize": 5,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 800,
                }
            },
        },
    )
    match = choose(found.get("places") or [], name, lat, lon)
    if not match:
        return {"google_place_id": None, "rating": None, "review_count": None}
    details = request(
        f"https://places.googleapis.com/v1/places/{match['id']}",
        key,
        "rating,userRatingCount",
    )
    return {
        "google_place_id": match["id"],
        "rating": details.get("rating"),
        "review_count": details.get("userRatingCount"),
    }


def main():
    key = load_key()
    saved = {}
    if OUT.exists():
        saved = json.loads(OUT.read_text())
    rows = list(csv.DictReader(PLACES.open()))
    pending = [row for row in rows if row["place_id"] not in saved]
    print(f"{len(rows)} places, {len(pending)} to fetch", flush=True)
    lock = Lock()
    done = 0

    def save():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(saved, indent=2))
        tmp.replace(OUT)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(lookup, row, key): row["place_id"] for row in pending}
        for future in as_completed(futures):
            place_id = futures[future]
            try:
                record = future.result()
            except RuntimeError as err:
                print(f"skip {place_id}: {err}", flush=True)
                continue
            with lock:
                saved[place_id] = record
                done += 1
                if done % 25 == 0 or done == len(pending):
                    save()
                    rated = sum(1 for item in saved.values() if item.get("rating") is not None)
                    print(f"{done}/{len(pending)} fetched, {rated} rated", flush=True)
    save()
    rated = sum(1 for item in saved.values() if item.get("rating") is not None)
    matched = sum(1 for item in saved.values() if item.get("google_place_id"))
    print(f"done: {matched} matched, {rated} with stars, {len(saved) - matched} missed", flush=True)


if __name__ == "__main__":
    main()
