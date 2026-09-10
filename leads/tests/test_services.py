"""
Unit tests for Email (Resend) and WhatsApp notification services.
Ensures external APIs are never called live during tests.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from leads.models import Lead
from leads.services.email import build_email_content, send_lead_email_notification
from leads.services.whatsapp import build_whatsapp_message, send_lead_whatsapp_notification


class NotificationServicesTestCase(TestCase):
    def setUp(self):
        self.lead = Lead.objects.create(
            id=101,
            name="Diana Prince",
            email="diana@example.com",
            phone="+1 (555) 901-2345",
            eligibility_result="Potentially Eligible",
            answers={
                "owns_property": True,
                "located_in_california": True,
                "is_residential": True,
                "is_single_family": True,
                "has_sufficient_space": True,
                "has_existing_structure": True,
                "has_restrictions": False,
            },
        )

    def test_email_payload_generation(self):
        content = build_email_content(self.lead)
        self.assertIn("Diana Prince", content["subject"])
        self.assertIn("diana@example.com", content["text"])
        self.assertIn("Do you own the property?", content["text"])
        self.assertIn("<table", content["html"])

    @override_settings(RESEND_API_KEY="")
    def test_email_mock_fallback_when_no_api_key(self):
        # When no key is configured, it must safely log without crashing
        result = send_lead_email_notification(self.lead)
        self.assertFalse(result["success"])
        self.assertTrue(result["simulated"])
        self.assertIn("RESEND_API_KEY is not configured", result["error"])

    @override_settings(RESEND_API_KEY="re_test_resend_key", DEFAULT_FROM_EMAIL="test@example.com", LEAD_NOTIFICATION_EMAIL="lead@example.com")
    @patch("resend.Emails.send")
    def test_email_live_path_success(self, mock_send):
        mock_send.return_value = {"id": "resend_msg_123"}

        result = send_lead_email_notification(self.lead)
        self.assertTrue(result["success"])
        self.assertFalse(result["simulated"])
        self.assertEqual(result["message_id"], "resend_msg_123")
        mock_send.assert_called_once()

    @override_settings(RESEND_API_KEY="re_test_resend_key")
    @patch("resend.Emails.send")
    def test_email_live_path_handles_api_failure(self, mock_send):
        mock_send.side_effect = Exception("Forbidden")

        result = send_lead_email_notification(self.lead)
        self.assertFalse(result["success"])
        self.assertIn("Resend API error", result["error"])

    @override_settings(RESEND_API_KEY="re_test_resend_key", RESEND_SANDBOX_EMAIL="noriabure@gmail.com")
    @patch("resend.Emails.send")
    def test_email_sandbox_reroute(self, mock_send):
        mock_send.side_effect = [
            Exception("You can only send testing emails to your own email address (noriabure@gmail.com)"),
            {"id": "sandbox_msg_456"},
        ]
        result = send_lead_email_notification(self.lead)
        self.assertTrue(result["success"])
        self.assertTrue(result["sandboxed"])
        self.assertEqual(result["delivered_to"], "noriabure@gmail.com")
        self.assertEqual(mock_send.call_count, 2)

    def test_whatsapp_message_formatting(self):
        msg = build_whatsapp_message(self.lead)
        self.assertIn("NEW ADU ELIGIBILITY LEAD", msg)
        self.assertIn("Diana Prince", msg)
        self.assertIn("Potentially Eligible", msg)
        self.assertIn("Lead ID: #101", msg)

    @override_settings(WHATSAPP_ENABLED=False)
    def test_whatsapp_disabled_behavior(self):
        result = send_lead_whatsapp_notification(self.lead)
        self.assertFalse(result["success"])
        self.assertEqual(result["mode"], "disabled")

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_MODE="mock")
    def test_whatsapp_mock_mode_behavior(self):
        result = send_lead_whatsapp_notification(self.lead)
        self.assertTrue(result["success"])
        self.assertTrue(result["simulated"])
        self.assertEqual(result["mode"], "mock")

    @override_settings(
        WHATSAPP_ENABLED=True,
        WHATSAPP_MODE="cloud_api",
        WHATSAPP_ACCESS_TOKEN="dummy-token",
        WHATSAPP_PHONE_NUMBER_ID="123456",
        WHATSAPP_RECIPIENT_PHONE="+15551234567",
        WHATSAPP_GRAPH_API_VERSION="v20.0",
    )
    @patch("requests.post")
    def test_whatsapp_cloud_api_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.123"}]}
        mock_post.return_value = mock_response

        result = send_lead_whatsapp_notification(self.lead)
        self.assertTrue(result["success"])
        self.assertFalse(result["simulated"])
        self.assertEqual(result["message_id"], "wamid.123")
