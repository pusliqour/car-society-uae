from dataclasses import dataclass
import secrets
import time

from .ingest import EventDraft, parse_submission


class ApprovalError(RuntimeError):
    pass


@dataclass(frozen=True)
class PendingEvent:
    token: str
    chat_id: int
    draft: EventDraft
    preview: str
    expires_at: float


class ApprovalService:
    def __init__(self, event_store, ttl_seconds=86400, clock=None):
        self.event_store = event_store
        self.ttl_seconds = ttl_seconds
        self.clock = clock or time.time
        self.pending = {}

    def submit(self, chat_id, text):
        draft = parse_submission(text)
        token = secrets.token_urlsafe(9)
        preview = (
            f"{draft.title}\n"
            f"Club: {draft.club}\n"
            f"When: {draft.date} at {draft.time} GST\n"
            f"Type: {draft.event_type}\n"
            f"Where: {draft.location}, {draft.emirate}\n"
            f"Details: {draft.summary}\n"
            f"Source: {draft.source_url}"
        )
        pending = PendingEvent(token, int(chat_id), draft, preview, self.clock() + self.ttl_seconds)
        self.pending[token] = pending
        return pending

    def _owned(self, chat_id, token):
        pending = self.pending.get(token)
        if not pending:
            raise ApprovalError("This approval is missing or was already used.")
        if pending.chat_id != int(chat_id):
            raise ApprovalError("This approval belongs to another Telegram chat.")
        if pending.expires_at <= self.clock():
            self.pending.pop(token, None)
            raise ApprovalError("This approval expired; send the event again.")
        return pending

    def approve(self, chat_id, token):
        pending = self._owned(chat_id, token)
        result = self.event_store.add_event(pending.draft.to_site_event())
        self.pending.pop(token, None)
        return result

    def reject(self, chat_id, token):
        pending = self._owned(chat_id, token)
        self.pending.pop(token, None)
        return pending
