"""Add the published phone number to places that already have a Google match."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_google_ratings import OUT, load_key, request

WORKERS = 3


def lookup_phone(place_id: str, key: str) -> str | None:
    details = request(
        f"https://places.googleapis.com/v1/places/{place_id}",
        key,
        "nationalPhoneNumber",
    )
    phone = details.get("nationalPhoneNumber")
    return phone if isinstance(phone, str) and phone.strip() else None


def main():
    key = load_key()
    saved = json.loads(OUT.read_text())
    pending = [
        (place_id, record["google_place_id"])
        for place_id, record in saved.items()
        if record.get("google_place_id") and "phone" not in record
    ]
    print(f"{len(pending)} numbers to fetch", flush=True)
    lock = Lock()
    done = 0

    def save():
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(saved, indent=2))
        tmp.replace(OUT)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(lookup_phone, google_id, key): place_id
            for place_id, google_id in pending
        }
        for future in as_completed(futures):
            place_id = futures[future]
            phone = future.result()
            with lock:
                saved[place_id]["phone"] = phone
                done += 1
                if done % 25 == 0 or done == len(pending):
                    save()
                    found = sum(1 for record in saved.values() if record.get("phone"))
                    print(f"{done}/{len(pending)} fetched, {found} numbers", flush=True)
    save()
    found = sum(1 for record in saved.values() if record.get("phone"))
    print(f"done: {found} numbers", flush=True)


if __name__ == "__main__":
    main()
