"""
Security and failure isolation tests for ADU Eligibility Calculator.
Tests CSRF enforcement, honeypot defenses, admin access isolation,
and notification failure safety (ensuring lead persistence).
"""

from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from leads.models import Lead
from calculator.eligibility import QUESTIONS


class SecurityAndResilienceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_answers = {q["id"]: "yes" for q in QUESTIONS}
        self.valid_answers["has_restrictions"] = "no"

    def test_anonymous_user_can_access_all_public_routes(self):
        """Verify that public users are never required to log in."""
        # 1. Homepage
        res = self.client.get(reverse("calculator:index"))
        self.assertEqual(res.status_code, 200)

        # 2. Questions
        res = self.client.get(reverse("calculator:questions"))
        self.assertEqual(res.status_code, 200)

        # Set session for result and contact
        session = self.client.session
        session["adu_answers"] = self.valid_answers
        session.save()

        # 3. Result
        res = self.client.get(reverse("calculator:result"))
        self.assertEqual(res.status_code, 200)

        # 4. Contact
        res = self.client.get(reverse("leads:contact"))
        self.assertEqual(res.status_code, 200)

    def test_admin_requires_authentication(self):
        """Verify staff admin portal requires authentication."""
        response = self.client.get("/admin/leads/lead/")
        # Expect redirect to admin login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_honeypot_prevents_lead_creation(self):
        """Bots completing the honeypot field are rejected; no lead is created."""
        session = self.client.session
        session["adu_answers"] = self.valid_answers
        session.save()

        initial_count = Lead.objects.count()

        bot_payload = {
            "name": "Spam Lead",
            "email": "spam@example.com",
            "phone": "+1 555-999-8888",
            "company_site_hp": "http://spamsite.com/bot",  # Honeypot filled
        }

        response = self.client.post(reverse("leads:contact"), data=bot_payload)
        self.assertEqual(response.status_code, 200)  # Re-renders form with error
        self.assertEqual(Lead.objects.count(), initial_count)

    @patch("leads.views.send_lead_email_notification")
    @patch("leads.views.send_lead_whatsapp_notification")
    def test_notification_failure_does_not_lose_lead(self, mock_wa, mock_email):
        """
        CRITICAL ARCHITECTURAL REQUIREMENT:
        If email service or WhatsApp service raises an unhandled exception or fails,
        the Lead record MUST remain safely committed in the database, errors logged,
        and the public user cleanly redirected to the success page.
        """
        mock_email.side_effect = RuntimeError("Email API crash simulation")
        mock_wa.side_effect = RuntimeError("WhatsApp network down simulation")

        session = self.client.session
        session["adu_answers"] = self.valid_answers
        session.save()

        post_data = {
            "name": "Resilient Prospect",
            "email": "resilient@example.com",
            "phone": "+1 (555) 321-7654",
            "company_site_hp": "",
        }

        response = self.client.post(reverse("leads:contact"), data=post_data)
        
        # User still gets normal success redirect
        self.assertRedirects(response, reverse("leads:success"))

        # Database record exists
        lead = Lead.objects.filter(email="resilient@example.com").first()
        self.assertIsNotNone(lead, "Lead record MUST NOT be lost when external APIs crash")
        self.assertEqual(lead.name, "Resilient Prospect")
        self.assertFalse(lead.email_sent)
        self.assertFalse(lead.whatsapp_sent)
        self.assertIn("Email API crash simulation", lead.email_error)
        self.assertIn("WhatsApp network down simulation", lead.whatsapp_error)

    def test_csrf_protection_on_post(self):
        """Ensure CSRF protection is active on POST endpoints."""
        csrf_client = Client(enforce_csrf_checks=True)
        # Attempting POST without CSRF token
        response = csrf_client.post(reverse("calculator:questions"), data={})
        self.assertEqual(response.status_code, 403)
