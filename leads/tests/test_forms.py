"""
Unit tests for LeadContactForm validation, phone checking, and honeypot.
"""

from django.test import TestCase
from leads.forms import LeadContactForm


class LeadContactFormTestCase(TestCase):
    def test_valid_contact_form(self):
        data = {
            "name": "Jane Doe",
            "email": "JANE.DOE@example.com",
            "phone": "+1 (555) 123-4567",
            "company_site_hp": "",
        }
        form = LeadContactForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "jane.doe@example.com")
        self.assertEqual(form.cleaned_data["name"], "Jane Doe")
        self.assertEqual(form.cleaned_data["phone"], "+1 (555) 123-4567")

    def test_whitespace_is_normalized(self):
        data = {
            "name": "  Bob Builder  ",
            "email": "  bob@example.com  ",
            "phone": "  (555) 987-6543  ",
            "company_site_hp": "",
        }
        form = LeadContactForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Bob Builder")
        self.assertEqual(form.cleaned_data["email"], "bob@example.com")
        self.assertEqual(form.cleaned_data["phone"], "(555) 987-6543")

    def test_phone_too_short_fails(self):
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "12345",  # Under 7 digits
        }
        form = LeadContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_honeypot_triggers_validation_error(self):
        data = {
            "name": "Spam Bot",
            "email": "bot@example.com",
            "phone": "+1 (555) 000-1111",
            "company_site_hp": "https://spam-site.com",  # Bot filled hidden field
        }
        form = LeadContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("company_site_hp", form.errors)

    def test_name_too_short_fails(self):
        data = {
            "name": "J",
            "email": "j@example.com",
            "phone": "+1 555-123-4567",
        }
        form = LeadContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
