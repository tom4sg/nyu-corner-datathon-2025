"""Add website and today's hours to places that already have a Google match.

Place Details stays on the same Enterprise fields as phone and stars. Ratings
and phone numbers already on the record are left alone.
"""

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_google_ratings import OUT, load_key, request

WORKERS = 3
MASK = "websiteUri,currentOpeningHours,regularOpeningHours"
NY = ZoneInfo("America/New_York")
DONE = ("website", "hours", "open_now")


def compact_hours(text: str) -> str | None:
    cleaned = " ".join(text.replace("—", "–").replace(" - ", " – ").split())
    cleaned = re.sub(r"(\d{1,2}):00(?=\s*[AP]M\b)", r"\1", cleaned, flags=re.I)
    return cleaned or None


def hours_for_today(details: dict) -> tuple[str | None, bool | None]:
    current = details.get("currentOpeningHours")
    regular = details.get("regularOpeningHours")
    current = current if isinstance(current, dict) else {}
    regular = regular if isinstance(regular, dict) else {}
    block = current or regular
    open_now = current.get("openNow") if isinstance(current.get("openNow"), bool) else None
    today = datetime.now(NY).strftime("%A").lower()
    for line in block.get("weekdayDescriptions") or []:
        if not isinstance(line, str) or ":" not in line:
            continue
        day, rest = line.split(":", 1)
        if day.strip().lower() == today:
            return compact_hours(rest), open_now
    return None, open_now


def lookup(google_id: str, key: str) -> tuple[str | None, str | None, bool | None]:
    details = request(
        f"https://places.googleapis.com/v1/places/{google_id}",
        key,
        MASK,
    )
    website = details.get("websiteUri")
    website = website.strip() if isinstance(website, str) and website.strip() else None
    hours, open_now = hours_for_today(details)
    return website, hours, open_now


def main():
    key = load_key()
    saved = json.loads(OUT.read_text())
    pending = [
        (place_id, record["google_place_id"])
        for place_id, record in saved.items()
        if record.get("google_place_id") and any(name not in record for name in DONE)
    ]
    print(f"{len(pending)} places to fetch", flush=True)
    lock = Lock()
    done = 0

    def save():
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(saved, indent=2))
        tmp.replace(OUT)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(lookup, google_id, key): place_id
            for place_id, google_id in pending
        }
        for future in as_completed(futures):
            place_id = futures[future]
            try:
                website, hours, open_now = future.result()
            except RuntimeError as err:
                message = str(err)
                if message.startswith("404"):
                    website, hours, open_now = None, None, None
                    print(f"missing {place_id}", flush=True)
                else:
                    raise
            with lock:
                saved[place_id]["website"] = website
                saved[place_id]["hours"] = hours
                saved[place_id]["open_now"] = open_now
                done += 1
                if done % 25 == 0 or done == len(pending):
                    save()
                    websites = sum(1 for record in saved.values() if record.get("website"))
                    hours_found = sum(1 for record in saved.values() if record.get("hours"))
                    print(
                        f"{done}/{len(pending)} fetched, {websites} websites, {hours_found} hours",
                        flush=True,
                    )
    save()
    websites = sum(1 for record in saved.values() if record.get("website"))
    hours_found = sum(1 for record in saved.values() if record.get("hours"))
    print(f"done: {websites} websites, {hours_found} hours", flush=True)


if __name__ == "__main__":
    main()
