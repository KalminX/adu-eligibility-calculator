"""
Django Admin configuration for Lead model.
"""

from django.contrib import admin
from django.utils.html import format_html
from calculator.eligibility import QUESTION_MAP
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """
    Rich administration interface for inspecting and managing ADU prospect leads.
    """

    list_display = (
        "name",
        "email",
        "phone",
        "eligibility_badge",
        "email_delivery_badge",
        "whatsapp_delivery_badge",
        "created_at",
    )

    list_filter = (
        "eligibility_result",
        "email_sent",
        "whatsapp_sent",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "answers_table",
        "email_sent",
        "email_error",
        "whatsapp_sent",
        "whatsapp_error",
    )

    fieldsets = (
        (
            "Prospect Contact Details",
            {
                "fields": (
                    "name",
                    "email",
                    "phone",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
        (
            "Evaluation & Questionnaire",
            {
                "fields": (
                    "eligibility_result",
                    "answers_table",
                ),
            },
        ),
        (
            "Integration & Notification Status",
            {
                "fields": (
                    "email_sent",
                    "email_error",
                    "whatsapp_sent",
                    "whatsapp_error",
                ),
            },
        ),
    )

    @admin.display(description="Eligibility Result")
    def eligibility_badge(self, obj: Lead):
        color = "#64748b"
        bg = "#f1f5f9"
        if obj.eligibility_result == "Potentially Eligible":
            color = "#166534"
            bg = "#dcfce7"
        elif obj.eligibility_result == "Needs Further Review":
            color = "#854d0e"
            bg = "#fef9c3"
        elif obj.eligibility_result == "Currently Unlikely to Qualify":
            color = "#991b1b"
            bg = "#fee2e2"

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            bg,
            color,
            obj.eligibility_result,
        )

    @admin.display(description="Email Sent", boolean=True)
    def email_delivery_badge(self, obj: Lead):
        return obj.email_sent

    @admin.display(description="WhatsApp Sent", boolean=True)
    def whatsapp_delivery_badge(self, obj: Lead):
        return obj.whatsapp_sent

    @admin.display(description="Submitted Responses")
    def answers_table(self, obj: Lead):
        if not obj.answers:
            return "No answers recorded."

        rows = []
        for q_id, is_yes in obj.answers.items():
            question_data = QUESTION_MAP.get(q_id, {})
            text = question_data.get("text", q_id)
            status_text = "Yes" if is_yes else "No"
            status_color = "#166534" if is_yes else "#991b1b"
            rows.append(
                f"<tr><td style='padding: 6px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 500;'>{text}</td>"
                f"<td style='padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: {status_color}; font-weight: bold;'>{status_text}</td></tr>"
            )

        html = (
            '<table style="width: 100%; max-width: 650px; border-collapse: collapse; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">'
            '<thead style="background: #f8fafc; font-size: 12px; color: #64748b; text-align: left;">'
            '<tr><th style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">Question</th><th style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">Response</th></tr>'
            "</thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
        )
        return format_html(html)
