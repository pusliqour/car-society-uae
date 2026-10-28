import json
import re
from datetime import date, time
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {"id", "title", "by", "type", "emirate", "venue", "date", "url", "note"}


class ValidationError(ValueError):
    pass


def validate_events(events):
    if not isinstance(events, list):
        raise ValidationError("events.json must contain an array")
    ids = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValidationError(f"event {index} must be an object")
        missing = sorted(REQUIRED - set(event))
        if missing:
            raise ValidationError(f"event {index} is missing: {', '.join(missing)}")
        for field in REQUIRED:
            if not isinstance(event[field], str) or not event[field].strip():
                raise ValidationError(f"event {index} field {field} must be a non-empty string")
        if event["id"] in ids:
            raise ValidationError(f"duplicate event id: {event['id']}")
        ids.add(event["id"])
        date.fromisoformat(event["date"])
        if event.get("end"):
            date.fromisoformat(event["end"])
            if event["end"] < event["date"]:
                raise ValidationError(f"event {event['id']} ends before it starts")
        if event.get("time"):
            time.fromisoformat(event["time"])
        parsed = urlparse(event["url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValidationError(f"event {event['id']} must have an HTTPS URL")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", event["id"]):
            raise ValidationError(f"event {event['id']} has an invalid id")
    return events


def main():
    path = Path("data/events.json")
    validate_events(json.loads(path.read_text()))
    print(f"OK: {len(json.loads(path.read_text()))} events")


if __name__ == "__main__":
    main()
