"""
Contact form for capturing ADU prospective leads with spam defenses.
"""

import re
import logging
from django import forms
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

# Basic phone validation: allows standard international and domestic formats
# e.g., +1 (555) 123-4567, 555-123-4567, +44 20 7123 4567
PHONE_REGEX = re.compile(r"^[0-9+\-()\s.]{7,25}$")


class LeadContactForm(forms.Form):
    """
    Server-side validated form for prospect contact submission.
    Includes honeypot and optional Cloudflare Turnstile token validation.
    """

    name = forms.CharField(
        label="Full Name",
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Jane Doe",
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition",
                "autocomplete": "name",
            }
        ),
    )

    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "jane.doe@example.com",
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition",
                "autocomplete": "email",
            }
        ),
    )

    phone = forms.CharField(
        label="Phone Number",
        max_length=25,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "+1 (555) 000-0000",
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition",
                "autocomplete": "tel",
            }
        ),
    )

    # Honeypot field: must remain empty for humans. Hidden by inline styles and CSS.
    company_site_hp = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "aria-hidden": "true",
                "style": "display: none !important; position: absolute !important; left: -9999px !important;",
            }
        ),
    )

    # Turnstile token field passed via JavaScript when Turnstile is active
    cf_turnstile_response = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean_name(self) -> str:
        name = self.cleaned_data.get("name", "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Please provide your full legal or preferred name (at least 2 characters).")
        return name

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        return email

    def clean_phone(self) -> str:
        phone = self.cleaned_data.get("phone", "").strip()
        # Count actual digits
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 7:
            raise forms.ValidationError("Please enter a valid phone number with at least 7 digits.")
        if not PHONE_REGEX.match(phone):
            raise forms.ValidationError("Phone number format contains invalid characters.")
        return phone

    def clean_company_site_hp(self) -> str:
        hp_value = self.cleaned_data.get("company_site_hp", "").strip()
        if hp_value:
            logger.warning("Spam honeypot triggered with value: '%s'", hp_value)
            raise forms.ValidationError(
                "Security verification failed: The hidden anti-spam field was filled. Please leave this field empty."
            )
        return hp_value

    def clean(self) -> dict:
        cleaned_data = super().clean()

        # Cloudflare Turnstile Verification if enabled
        turnstile_enabled = getattr(settings, "TURNSTILE_ENABLED", False)
        if turnstile_enabled:
            secret_key = getattr(settings, "TURNSTILE_SECRET_KEY", "").strip()
            token = cleaned_data.get("cf_turnstile_response", "").strip()

            if not token:
                self.add_error(None, "Anti-spam verification failed. Please complete the security check.")
                return cleaned_data

            try:
                verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
                resp = requests.post(
                    verify_url,
                    data={
                        "secret": secret_key,
                        "response": token,
                    },
                    timeout=5,
                )
                result = resp.json()
                if not result.get("success"):
                    logger.warning("Turnstile verification failed: %s", result)
                    self.add_error(None, "Security verification failed. Please refresh and try again.")
            except requests.RequestException as exc:
                logger.error("Turnstile network error: %s", exc)
                # In development or transient failure, fallback safely
                if not settings.DEBUG:
                    self.add_error(None, "Security service temporarily unreachable.")

        return cleaned_data
