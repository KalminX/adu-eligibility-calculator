"""
Tests for the custom Staff & Administrator Lead Management Portal.
Tests custom login UI, role permissions, KPI analytics, lead inspection,
resend actions, deletion, and CSV export.
"""

from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from leads.models import Lead

User = get_user_model()


class PortalStaffAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin_test@example.com",
            password="testpassword123",
        )
        self.staff_user = User.objects.create_user(
            username="staff_test",
            email="staff_test@example.com",
            password="testpassword123",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular_test",
            email="regular_test@example.com",
            password="testpassword123",
            is_staff=False,
        )
        self.lead = Lead.objects.create(
            name="Test Prospect",
            email="prospect@example.com",
            phone="+1 555-019-2831",
            eligibility_result="Potentially Eligible",
            answers={"owns_property": True, "located_in_california": True},
        )

    def test_unauthenticated_user_redirected_to_portal_login(self):
        response = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/portal/login/", response.url)

    def test_portal_login_page_renders_custom_template(self):
        response = self.client.get(reverse("portal:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Portal Sign In")
        self.assertContains(response, "logins.txt")

    def test_portal_login_with_valid_staff_credentials(self):
        response = self.client.post(
            reverse("portal:login"),
            data={"username": "staff_test", "password": "testpassword123"},
        )
        self.assertRedirects(response, reverse("portal:dashboard"))

    def test_portal_login_with_non_staff_credentials_rejected(self):
        response = self.client.post(
            reverse("portal:login"),
            data={"username": "regular_test", "password": "testpassword123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted")

    def test_portal_login_with_invalid_password_rejected(self):
        response = self.client.post(
            reverse("portal:login"),
            data={"username": "staff_test", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_portal_logout(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("portal:logout"))
        self.assertRedirects(response, reverse("portal:login"))

    def test_staff_user_can_access_dashboard(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ADU Lead Pipeline")
        self.assertContains(response, "Test Prospect")

    def test_dashboard_filtering_and_search(self):
        self.client.force_login(self.staff_user)
        # Search by prospect name
        response = self.client.get(reverse("portal:dashboard") + "?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Prospect")

        # Search for non-existent prospect
        response2 = self.client.get(reverse("portal:dashboard") + "?q=NonExistentPerson")
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "No Leads Found")

    def test_lead_detail_view(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("portal:lead_detail", kwargs={"lead_id": self.lead.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Prospect")
        self.assertContains(response, "Assessment Questionnaire Transcript")
        self.assertContains(response, "Trigger Email Dispatch")
        self.assertContains(response, "Trigger WhatsApp Dispatch")

    @patch("leads.portal_views.send_lead_email_notification")
    def test_manual_resend_email(self, mock_email):
        mock_email.return_value = {"success": True, "simulated": False, "message_id": "resend_ok"}
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("portal:resend_email", kwargs={"lead_id": self.lead.id})
        )
        self.assertRedirects(response, reverse("portal:lead_detail", kwargs={"lead_id": self.lead.id}))
        mock_email.assert_called_once()
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.email_sent)

    @patch("leads.portal_views.send_staff_email_to_lead")
    def test_staff_send_direct_email(self, mock_staff_email):
        mock_staff_email.return_value = {"success": True, "simulated": False, "message_id": "resend_staff_msg"}
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("portal:send_staff_email", kwargs={"lead_id": self.lead.id}),
            data={
                "subject": "Discussion on your setback allowances",
                "message": "Hi Prospect, let us schedule a discovery call.",
            },
        )
        self.assertRedirects(response, reverse("portal:lead_detail", kwargs={"lead_id": self.lead.id}))
        mock_staff_email.assert_called_once()
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.email_sent)

    @patch("leads.portal_views.send_lead_whatsapp_notification")
    def test_manual_resend_whatsapp(self, mock_wa):
        mock_wa.return_value = {"success": True, "simulated": True, "mode": "mock"}
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("portal:resend_whatsapp", kwargs={"lead_id": self.lead.id})
        )
        self.assertRedirects(response, reverse("portal:lead_detail", kwargs={"lead_id": self.lead.id}))
        mock_wa.assert_called_once()

    def test_lead_deletion(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("portal:lead_delete", kwargs={"lead_id": self.lead.id})
        )
        self.assertRedirects(response, reverse("portal:dashboard"))
        self.assertFalse(Lead.objects.filter(id=self.lead.id).exists())

    def test_csv_export(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("portal:export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=\"adu_leads_export.csv\"", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("Test Prospect", content)
        self.assertIn("prospect@example.com", content)
