"""
Lead models for ADU Eligibility Calculator.
Stores prospect contact details, eligibility outcomes, and notification logs.
"""

from django.db import models


class Lead(models.Model):
    """
    Represents an ADU inquiry captured through the eligibility calculator.
    """

    ELIGIBILITY_CHOICES = [
        ("Potentially Eligible", "Potentially Eligible"),
        ("Needs Further Review", "Needs Further Review"),
        ("Currently Unlikely to Qualify", "Currently Unlikely to Qualify"),
    ]

    name = models.CharField(
        max_length=150,
        verbose_name="Full Name",
        help_text="Name submitted by the prospective property owner.",
    )
    email = models.EmailField(
        max_length=254,
        verbose_name="Email Address",
        db_index=True,
    )
    phone = models.CharField(
        max_length=30,
        verbose_name="Phone Number",
        db_index=True,
    )
    eligibility_result = models.CharField(
        max_length=60,
        choices=ELIGIBILITY_CHOICES,
        default="Needs Further Review",
        verbose_name="Eligibility Result",
        db_index=True,
    )
    answers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Questionnaire Answers",
        help_text="Raw responses to the 7 eligibility questions.",
    )

    # Notification tracking
    email_sent = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Email Sent",
    )
    email_error = models.TextField(
        blank=True,
        default="",
        verbose_name="Email Error Log",
    )
    whatsapp_sent = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="WhatsApp Sent",
    )
    whatsapp_error = models.TextField(
        blank=True,
        default="",
        verbose_name="WhatsApp Error Log",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=["-created_at"], name="lead_created_desc_idx"),
            models.Index(fields=["eligibility_result"], name="lead_eligibility_idx"),
            models.Index(fields=["email"], name="lead_email_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.eligibility_result}"
