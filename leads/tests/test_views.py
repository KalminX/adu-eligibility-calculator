"""
Integration tests for lead capture views, session interaction, and success flow.
"""

from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from leads.models import Lead
from calculator.eligibility import QUESTIONS


class LeadViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_answers = {q["id"]: "yes" for q in QUESTIONS}
        self.valid_answers["has_restrictions"] = "no"

    def test_contact_view_redirects_if_no_session_answers(self):
        response = self.client.get(reverse("leads:contact"))
        self.assertRedirects(response, reverse("calculator:questions"))

    def test_contact_view_renders_form_when_session_exists(self):
        session = self.client.session
        session["adu_answers"] = self.valid_answers
        session.save()

        response = self.client.get(reverse("leads:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connect With an ADU Specialist")
        self.assertContains(response, "Full Name")

    @patch("leads.views.send_lead_email_notification")
    @patch("leads.views.send_lead_whatsapp_notification")
    def test_contact_post_creates_lead_and_redirects(self, mock_wa, mock_email):
        mock_email.return_value = {"success": True, "simulated": False, "message_id": "test_msg_id"}
        mock_wa.return_value = {"success": True, "simulated": False, "message_id": "test_wa_id"}

        session = self.client.session
        session["adu_answers"] = self.valid_answers
        session.save()

        post_data = {
            "name": "Sarah Connor",
            "email": "sarah@example.com",
            "phone": "+1 (555) 432-1098",
            "company_site_hp": "",
        }

        response = self.client.post(reverse("leads:contact"), data=post_data)
        self.assertRedirects(response, reverse("leads:success"))

        # Verify lead created in DB
        lead = Lead.objects.filter(email="sarah@example.com").first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, "Sarah Connor")
        self.assertEqual(lead.eligibility_result, "Potentially Eligible")
        self.assertTrue(lead.email_sent)
        self.assertTrue(lead.whatsapp_sent)

        # Verify calls occurred
        mock_email.assert_called_once()
        mock_wa.assert_called_once()

    def test_success_view_renders_confirmation(self):
        lead = Lead.objects.create(
            name="Mark Taylor",
            email="mark@example.com",
            phone="555-123-4567",
            eligibility_result="Potentially Eligible",
        )
        session = self.client.session
        session["submitted_lead_id"] = lead.id
        session.save()

        response = self.client.get(reverse("leads:success"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You for Your Submission")
        self.assertContains(response, f"#ADU-{lead.id:05d}")
