import unittest

from csae.ingest import parse_submission


class IngestTests(unittest.TestCase):
    def test_parses_labeled_instagram_submission(self):
        draft = parse_submission(
            """https://www.instagram.com/p/ABC123/
Club: Dubai Night Riders
Event: Mountain Drive
Date: 2026-11-14
Time: 20:00
Type: Drive
Emirate: Dubai
Location: Last Exit
Details: Meet at 19:30. Depart at 20:00. Bring a full tank."""
        )

        self.assertEqual(draft.title, "Mountain Drive")
        self.assertEqual(draft.club, "Dubai Night Riders")
        self.assertEqual(draft.date, "2026-11-14")
        self.assertEqual(draft.time, "20:00")
        self.assertEqual(draft.event_type, "Drive")
        self.assertEqual(draft.emirate, "Dubai")
        self.assertEqual(draft.location, "Last Exit")
        self.assertEqual(draft.source_url, "https://www.instagram.com/p/ABC123/")
        self.assertEqual(draft.summary, "Meet at 19:30. Depart at 20:00. Bring a full tank.")

        event = draft.to_site_event()
        self.assertEqual(event["id"], "mountain-drive-20261114")
        self.assertEqual(event["by"], "Dubai Night Riders")
        self.assertEqual(event["venue"], "Last Exit")
        self.assertEqual(event["url"], "https://www.instagram.com/p/ABC123/")
        self.assertEqual(event["note"], "Meet at 19:30. Depart at 20:00. Bring a full tank.")


if __name__ == "__main__":
    unittest.main()
