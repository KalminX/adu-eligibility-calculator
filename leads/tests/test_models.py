"""
Unit tests for Lead model persistence, indexing, and defaults.
"""

from django.test import TestCase
from leads.models import Lead


class LeadModelTestCase(TestCase):
    def test_lead_creation_and_defaults(self):
        lead = Lead.objects.create(
            name="Alice Smith",
            email="alice@example.com",
            phone="+1 555-123-4567",
            eligibility_result="Potentially Eligible",
            answers={"owns_property": True},
        )
        self.assertIsNotNone(lead.id)
        self.assertFalse(lead.email_sent)
        self.assertFalse(lead.whatsapp_sent)
        self.assertEqual(lead.email_error, "")
        self.assertEqual(lead.whatsapp_error, "")
        self.assertIn("Alice Smith", str(lead))
        self.assertIn("alice@example.com", str(lead))

    def test_lead_ordering(self):
        lead1 = Lead.objects.create(name="First Lead", email="first@example.com", phone="555-0001")
        lead2 = Lead.objects.create(name="Second Lead", email="second@example.com", phone="555-0002")
        leads = list(Lead.objects.all())
        # Most recent first
        self.assertEqual(leads[0].id, lead2.id)
        self.assertEqual(leads[1].id, lead1.id)
