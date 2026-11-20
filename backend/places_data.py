import json
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel


class Recommendation(BaseModel):
    place_id: str
    blurb: str


_MEDIA_PATH = Path(__file__).parent / "data" / "place_media.json"
_PLACE_MEDIA: Dict[str, List[str]] = {}
if _MEDIA_PATH.exists():
    with _MEDIA_PATH.open() as media_file:
        _PLACE_MEDIA = json.load(media_file)
else:
    logging.warning("Place photo file not found at %s", _MEDIA_PATH)

_RATINGS_PATH = Path(__file__).parent / "data" / "google_ratings.json"
_GOOGLE_RATINGS: Dict[str, dict] = {}
if _RATINGS_PATH.exists():
    with _RATINGS_PATH.open() as ratings_file:
        _GOOGLE_RATINGS = json.load(ratings_file)


def image_urls_for(place_id: str) -> List[str]:
    urls = _PLACE_MEDIA.get(place_id) or []
    return [url for url in urls if isinstance(url, str) and url.startswith("https://")][:3]


def maps_search_url(name: str, neighborhood: Optional[str]) -> str:
    query = f"{name}, {neighborhood or 'New York'}, NY"
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(query)


def maps_place_url(name: str, google_place_id: str) -> str:
    query = urllib.parse.urlencode({"api": "1", "query": name, "query_place_id": google_place_id})
    return "https://www.google.com/maps/search/?" + query


def google_reviews_url(google_place_id: str) -> str:
    return "https://search.google.com/local/reviews?placeid=" + urllib.parse.quote(google_place_id)


def _float_or_none(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_tags(tags) -> Optional[List[str]]:
    if tags is None:
        return None
    if isinstance(tags, list):
        cleaned = [str(tag).strip() for tag in tags if str(tag).strip()]
        return cleaned or None
    if isinstance(tags, str):
        inner = tags.strip().strip("{}")
        cleaned = [tag.strip() for tag in inner.split(",") if tag.strip()]
        return cleaned or None
    return None


def message_text(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text") or "")
            else:
                parts.append(getattr(block, "text", "") or "")
        return "".join(parts)
    return str(content)


_MARKER = re.compile(r"^[ \t>*#\d.)-]*\[\[(.+?)\]\][ \t*:]*", re.MULTILINE)


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower().replace("&", " and ")).strip()


def _strip_leading_name(blurb: str, name: str) -> str:
    # "**Name** in Area:" or "Name (Area) —" duplicates the heading the page already shows.
    pattern = (
        r"^\**\s*" + re.escape(name) + r"\s*\**"
        r"\s*(\([^)]*\)|in [^:—–\n]{1,40})?\s*\**\s*[:—–-]\s+"
    )
    return re.sub(pattern, "", blurb, count=1, flags=re.IGNORECASE)


def _match_place(marker: str, places: List[dict], used: set) -> Optional[dict]:
    wanted = _norm_name(marker)
    squashed = wanted.replace(" ", "")
    candidates = [place for place in places if place["id"] not in used]
    for place in candidates:
        if _norm_name(place.get("name") or "") == wanted:
            return place
    for place in candidates:
        name = _norm_name(place.get("name") or "")
        if name and wanted and (name.replace(" ", "") == squashed or wanted in name or name in wanted):
            return place
    return None


def split_recommendations(text: str, places: List[dict]) -> tuple[str, List[dict], str]:
    markers = list(_MARKER.finditer(text))
    if not markers:
        return text, [], ""

    used = set()
    picks = []
    outro = ""

    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        blurb = text[marker.end():end].strip()
        if _norm_name(marker.group(1)) == "end":
            outro = blurb
            continue
        place = _match_place(marker.group(1), places, used)
        if place is None or not blurb:
            continue
        used.add(place["id"])
        blurb = _strip_leading_name(blurb, place.get("name") or "")
        picks.append({"place_id": place["id"], "blurb": blurb})

    intro = text[:markers[0].start()].strip()
    return intro, picks[:3], outro


def markdown_response(intro: str, picks: List[dict], names: Dict[str, str], outro: str = "") -> str:
    parts = [intro.strip(), ""]
    for pick in picks:
        parts.append(f"**{names.get(pick['place_id'], pick['place_id'])}**")
        parts.append("")
        parts.append(pick["blurb"])
        parts.append("")
    if outro:
        parts.append(outro.strip())
    return "\n".join(parts).strip()


_STOPWORDS = {
    "the", "and", "for", "with", "where", "what", "that", "this", "some", "any", "can", "want",
    "looking", "place", "places", "spot", "spots", "good", "best", "great", "nice", "near", "around",
    "new", "york", "nyc", "get", "find", "somewhere", "you", "your", "are", "have", "has", "was",
}
_WORD = re.compile(r"[a-z0-9']+")


def _query_stems(query: str) -> List[str]:
    stems = []
    for word in _WORD.findall((query or "").lower()):
        if len(word) < 3 or word in _STOPWORDS:
            continue
        stem = word[:5] if len(word) > 5 else word
        if stem not in stems:
            stems.append(stem)
    return stems


def review_snippet(reviews: List[str], query: str, max_chars: int = 120) -> Optional[str]:
    reviews = [" ".join(review.split()) for review in reviews if review and review.strip()]
    if not reviews:
        return None
    stems = _query_stems(query)

    def hits(text: str) -> List[tuple]:
        return [
            (match.start(), stem)
            for match in _WORD.finditer(text.lower())
            for stem in stems
            if match.group().startswith(stem)
        ]

    found_by_review = [(review, hits(review)) for review in reviews]
    review_counts = {
        stem: sum(1 for _, found in found_by_review if any(s == stem for _, s in found))
        for stem in stems
    }

    def score(found: List[tuple]) -> float:
        return sum(1 + 1 / review_counts[stem] for stem in {stem for _, stem in found})

    best_review, best_hits = reviews[0], []
    for review, found in found_by_review:
        if score(found) > score(best_hits):
            best_review, best_hits = review, found

    if len(best_review) <= max_chars:
        return best_review

    start = 0
    if best_hits:
        def coverage(position: int) -> int:
            return len({stem for pos, stem in best_hits if position <= pos < position + max_chars - 10})
        start = max((max(0, pos - 30) for pos, _ in best_hits), key=coverage)
        start = max(0, min(start, len(best_review) - max_chars))
        if start:
            space = best_review.find(" ", start)
            start = space + 1 if 0 <= space < start + 20 else start
    end = min(len(best_review), start + max_chars)
    if end < len(best_review):
        space = best_review.rfind(" ", start, end)
        end = space if space > start else end

    excerpt = best_review[start:end].strip().rstrip(".,;:!-")
    return ("..." if start else "") + excerpt + ("..." if end < len(best_review) else "")


def google_rating_for(place_id: str) -> dict:
    record = _GOOGLE_RATINGS.get(place_id) or {}
    rating = record.get("rating")
    count = record.get("review_count")
    return {
        "google_rating": float(rating) if isinstance(rating, (int, float)) else None,
        "google_review_count": int(count) if isinstance(count, int) else None,
        "phone": record.get("phone") or None,
        "google_place_id": record.get("google_place_id") or None,
    }


def build_place_fields(doc: dict) -> dict:
    name = doc.get("name") or "Unknown"
    neighborhood = doc.get("neighborhood")
    google = google_rating_for(doc["id"])
    google_place_id = google.pop("google_place_id")
    maps_url = maps_place_url(name, google_place_id) if google_place_id else maps_search_url(name, neighborhood)
    reviews_url = google_reviews_url(google_place_id) if google_place_id else None
    return {
        "place_id": doc["id"],
        "name": name,
        "neighborhood": neighborhood,
        "latitude": _float_or_none(doc.get("latitude")),
        "longitude": _float_or_none(doc.get("longitude")),
        "tags": normalize_tags(doc.get("tags")),
        "description": doc.get("description"),
        "reviews": doc.get("reviews"),
        "emoji": doc.get("emoji"),
        "score": float(doc.get("score") or 0),
        "image_urls": image_urls_for(doc["id"]),
        "maps_url": maps_url,
        "reviews_url": reviews_url,
        **google,
    }
