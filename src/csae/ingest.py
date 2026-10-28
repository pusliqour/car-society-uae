from dataclasses import dataclass
from datetime import date, time
import re
import unicodedata
from urllib.parse import urlparse


class InvalidSubmission(ValueError):
    """The Telegram message cannot be converted into a safe event draft."""


@dataclass(frozen=True)
class EventDraft:
    title: str
    club: str
    date: str
    time: str
    event_type: str
    emirate: str
    location: str
    summary: str
    source_url: str

    def to_site_event(self) -> dict:
        slug = unicodedata.normalize("NFKD", self.title).encode("ascii", "ignore").decode().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-") or "event"
        return {
            "id": f"{slug[:48]}-{self.date.replace('-', '')}",
            "title": self.title,
            "by": self.club,
            "type": self.event_type,
            "emirate": self.emirate,
            "venue": self.location,
            "date": self.date,
            "time": self.time,
            "url": self.source_url,
            "note": self.summary,
        }


_REQUIRED = {
    "club": "club",
    "event": "title",
    "date": "date",
    "time": "time",
    "type": "event_type",
    "emirate": "emirate",
    "location": "location",
}
_URL = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


def _shorten(value: str, limit: int = 180) -> str:
    value = _SPACE.sub(" ", value).strip()
    if len(value) <= limit:
        return value
    clipped = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (clipped or value[: limit - 1]).rstrip() + "…"


def parse_submission(text: str) -> EventDraft:
    if not isinstance(text, str) or not text.strip():
        raise InvalidSubmission("Send an Instagram link and labeled event details.")
    urls = _URL.findall(text)
    source_url = next((url.rstrip(".,)") for url in urls if urlparse(url).hostname in {"instagram.com", "www.instagram.com"}), "")
    if not source_url:
        raise InvalidSubmission("An instagram.com source link is required.")

    fields = {}
    for raw in text.splitlines():
        if ":" not in raw or raw.lstrip().lower().startswith(("http://", "https://")):
            continue
        key, value = raw.split(":", 1)
        key = key.strip().lower()
        if key in {*_REQUIRED, "details"}:
            fields[key] = value.strip()

    missing = [label.title() for label in _REQUIRED if not fields.get(label)]
    if missing:
        raise InvalidSubmission("Missing: " + ", ".join(missing))
    try:
        date.fromisoformat(fields["date"])
    except ValueError as exc:
        raise InvalidSubmission("Date must use YYYY-MM-DD.") from exc
    try:
        time.fromisoformat(fields["time"])
    except ValueError as exc:
        raise InvalidSubmission("Time must use 24-hour HH:MM.") from exc

    values = {target: _shorten(fields[label], 100) for label, target in _REQUIRED.items()}
    return EventDraft(
        **values,
        summary=_shorten(fields.get("details") or f"{values['event_type']} by {values['club']}.", 180),
        source_url=source_url,
    )
