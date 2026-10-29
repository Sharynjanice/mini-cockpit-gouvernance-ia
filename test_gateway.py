import os
import tempfile
import unittest

os.environ["GATEWAY_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
import gateway  # noqa: E402


class GatewayTests(unittest.TestCase):
    def test_intern_can_read_calendar(self):
        self.assertIn("Point équipe", gateway.call("intern", "projet-alpha", "read_calendar", day="2026-11-03"))

    def test_intern_cannot_send_email(self):
        out = gateway.call("intern", "projet-alpha", "send_email", to="a@b.fr", subject="s", body="b")
        self.assertTrue(out.startswith("REFUSÉ"))

    def test_manager_can_send_email(self):
        out = gateway.call("manager", "projet-alpha", "send_email", to="a@b.fr", subject="s", body="b")
        self.assertIn("SIMULÉ", out)

    def test_unknown_role_refused(self):
        self.assertTrue(gateway.call("hacker", "projet-alpha", "read_notes", topic="x").startswith("REFUSÉ"))

    def test_budget_blocks_calls(self):
        gateway.record_usage("projet-beta", 2000, 1500)  # 3500 > 3000
        out = gateway.call("manager", "projet-beta", "read_notes", topic="conformite")
        self.assertIn("budget épuisé", out)

    def test_audit_logs_allowed_and_refused(self):
        gateway.call("intern", "projet-alpha", "send_email", to="a@b.fr", subject="s", body="b")
        with gateway.session() as db:
            n = db.execute("SELECT COUNT(*) FROM audit WHERE allowed = 0").fetchone()[0]
        self.assertGreaterEqual(n, 1)

    def test_unreachable_webhook_does_not_break(self):
        os.environ["N8N_WEBHOOK_URL"] = "http://127.0.0.1:9/inexistant"
        try:
            out = gateway.call("intern", "projet-alpha", "send_email", to="a@b.fr", subject="s", body="b")
        finally:
            del os.environ["N8N_WEBHOOK_URL"]
        self.assertTrue(out.startswith("REFUSÉ"))

    def test_usage_accumulates(self):
        before = gateway.used_tokens("projet-alpha")
        gateway.record_usage("projet-alpha", 100, 50)
        self.assertEqual(gateway.used_tokens("projet-alpha"), before + 150)


if __name__ == "__main__":
    unittest.main()