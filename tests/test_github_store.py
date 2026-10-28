import base64
import json
import unittest

from csae.github_store import DuplicateEvent, GitHubEventStore


class GitHubEventStoreTests(unittest.TestCase):
    def setUp(self):
        self.existing = [{
            "id": "old-20261101",
            "title": "Old Event",
            "by": "Old Club",
            "type": "Meet",
            "emirate": "Dubai",
            "venue": "Old Venue",
            "date": "2026-11-01",
            "time": "18:00",
            "url": "https://www.instagram.com/p/OLD/",
            "note": "Existing event."
        }]

    def test_approved_event_is_committed_to_events_json(self):
        calls = []

        def transport(method, path, token, payload=None):
            calls.append((method, path, token, payload))
            if method == "GET":
                raw = json.dumps(self.existing).encode()
                return {"sha": "old-sha", "content": base64.b64encode(raw).decode()}
            return {"commit": {"html_url": "https://github.com/pusliqour/car-society-uae/commit/abc"}}

        event = {
            "id": "mountain-drive-20261114", "title": "Mountain Drive", "by": "Dubai Night Riders",
            "type": "Drive", "emirate": "Dubai", "venue": "Last Exit", "date": "2026-11-14",
            "time": "20:00", "url": "https://www.instagram.com/p/ABC123/", "note": "Meet then depart."
        }
        result = GitHubEventStore("pusliqour", "car-society-uae", lambda: "token", transport).add_event(event)

        self.assertEqual(result["commit_url"], "https://github.com/pusliqour/car-society-uae/commit/abc")
        self.assertEqual(calls[0][:3], ("GET", "/repos/pusliqour/car-society-uae/contents/data/events.json?ref=main", "token"))
        self.assertEqual(calls[1][0], "PUT")
        written = json.loads(base64.b64decode(calls[1][3]["content"]))
        self.assertEqual([item["id"] for item in written], ["old-20261101", "mountain-drive-20261114"])
        self.assertEqual(calls[1][3]["sha"], "old-sha")

    def test_duplicate_source_is_refused(self):
        def transport(method, path, token, payload=None):
            raw = json.dumps(self.existing).encode()
            return {"sha": "old-sha", "content": base64.b64encode(raw).decode()}

        duplicate = dict(self.existing[0], id="different-id")
        store = GitHubEventStore("pusliqour", "car-society-uae", lambda: "token", transport)
        with self.assertRaises(DuplicateEvent):
            store.add_event(duplicate)


if __name__ == "__main__":
    unittest.main()
