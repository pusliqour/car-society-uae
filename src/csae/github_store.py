import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .validate import validate_events


class GitHubStoreError(RuntimeError):
    pass


class DuplicateEvent(GitHubStoreError):
    pass


_API = "https://api.github.com"
_REQUIRED = {"id", "title", "by", "type", "emirate", "venue", "date", "time", "url", "note"}


def _http_transport(method, path, token, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    request = Request(
        _API + path,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "csae-calendar-bot",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        if exc.code in {409, 422}:
            raise GitHubStoreError("GitHub rejected the update because the event feed changed; retry approval.") from exc
        raise GitHubStoreError(f"GitHub returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise GitHubStoreError("GitHub connection failed.") from exc
    return json.loads(content) if content else {}


class GitHubEventStore:
    def __init__(self, owner, repo, token_provider, transport=None, branch="main"):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.token_provider = token_provider
        self.transport = transport or _http_transport
        self.path = f"/repos/{owner}/{repo}/contents/data/events.json"

    def _token(self):
        token = self.token_provider()
        if not token:
            raise GitHubStoreError("GITHUB_TOKEN is not configured.")
        return token

    def add_event(self, event):
        missing = sorted(_REQUIRED - set(event))
        if missing:
            raise GitHubStoreError("Event is missing fields: " + ", ".join(missing))
        token = self._token()
        current = self.transport("GET", f"{self.path}?ref={self.branch}", token)
        try:
            events = json.loads(base64.b64decode(current["content"]).decode())
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise GitHubStoreError("GitHub event feed is malformed.") from exc
        if not isinstance(events, list):
            raise GitHubStoreError("GitHub event feed must be an array.")
        if any(item.get("id") == event["id"] or item.get("url") == event["url"] for item in events):
            raise DuplicateEvent("This event ID or Instagram source is already in the calendar.")
        events.append(event)
        events.sort(key=lambda item: (item.get("date", ""), item.get("time", ""), item.get("id", "")))
        validate_events(events)
        encoded = base64.b64encode((json.dumps(events, indent=2, ensure_ascii=False) + "\n").encode()).decode()
        payload = {
            "message": f"data(events): add {event['title']}",
            "content": encoded,
            "sha": current["sha"],
            "branch": self.branch,
        }
        result = self.transport("PUT", self.path, token, payload)
        return {"commit_url": (result.get("commit") or {}).get("html_url", ""), "event": event}
