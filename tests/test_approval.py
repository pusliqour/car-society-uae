import unittest

from csae.approval import ApprovalError, ApprovalService


class ApprovalServiceTests(unittest.TestCase):
    def test_submission_is_pending_until_owner_approves(self):
        committed = []

        class Store:
            def add_event(self, event):
                committed.append(event)
                return {"commit_url": "https://github.com/commit/abc", "event": event}

        service = ApprovalService(Store())
        text = """https://www.instagram.com/p/ABC123/
Club: Dubai Night Riders
Event: Mountain Drive
Date: 2026-11-14
Time: 20:00
Type: Drive
Emirate: Dubai
Location: Last Exit
Details: Meet at 19:30. Depart at 20:00."""
        pending = service.submit(1001, text)

        self.assertEqual(committed, [])
        self.assertIn("Mountain Drive", pending.preview)
        with self.assertRaises(ApprovalError):
            service.approve(2002, pending.token)
        result = service.approve(1001, pending.token)
        self.assertEqual(result["commit_url"], "https://github.com/commit/abc")
        self.assertEqual(len(committed), 1)
        with self.assertRaises(ApprovalError):
            service.approve(1001, pending.token)


if __name__ == "__main__":
    unittest.main()
