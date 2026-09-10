"""
Views for lead capture, notification orchestration, and success confirmation.
"""

import time
import logging
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from calculator.eligibility import calculate_eligibility
from .forms import LeadContactForm
from .models import Lead
from .services.email import send_lead_email_notification
from .services.whatsapp import send_lead_whatsapp_notification

logger = logging.getLogger(__name__)


def contact_view(request):
    """
    Renders lead capture form and processes contact submissions.
    Ensures transactional safety: saves lead in database before invoking external services.
    """
    answers = request.session.get("adu_answers")
    if not answers:
        return redirect("calculator:questions")

    result = calculate_eligibility(answers)

    # Basic submission throttling (10 seconds between repeated submissions)
    last_submission = request.session.get("last_submission_time", 0)
    current_time = time.time()
    if request.method == "POST" and (current_time - last_submission < 10):
        form = LeadContactForm(request.POST)
        form.add_error(
            None,
            "Please wait a few seconds before submitting another request.",
        )
        return render(
            request,
            "calculator/lead_form.html",
            {
                "form": form,
                "result": result,
                "turnstile_enabled": getattr(settings, "TURNSTILE_ENABLED", False),
                "turnstile_site_key": getattr(settings, "TURNSTILE_SITE_KEY", ""),
            },
        )

    if request.method == "POST":
        form = LeadContactForm(request.POST)
        if form.is_valid():
            # Step 1: Save Lead in database inside transaction
            with transaction.atomic():
                lead = Lead.objects.create(
                    name=form.cleaned_data["name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    eligibility_result=result.status,
                    answers=answers,
                )

            # Step 2: Attempt Email notification (safely isolated)
            try:
                email_result = send_lead_email_notification(lead)
                lead.email_sent = email_result.get("success", False)
                if email_result.get("error"):
                    lead.email_error = email_result["error"]
                elif email_result.get("simulated"):
                    lead.email_error = "Mock mode: Simulated development delivery."
            except Exception as exc:
                logger.exception("Unexpected exception in email service for Lead #%s", lead.id)
                lead.email_sent = False
                lead.email_error = f"Service exception: {str(exc)}"

            # Step 3: Attempt WhatsApp notification (safely isolated)
            try:
                whatsapp_result = send_lead_whatsapp_notification(lead)
                lead.whatsapp_sent = whatsapp_result.get("success", False)
                if whatsapp_result.get("error"):
                    lead.whatsapp_error = whatsapp_result["error"]
                elif whatsapp_result.get("simulated"):
                    lead.whatsapp_error = "Mock mode: Simulated development delivery."
            except Exception as exc:
                logger.exception("Unexpected exception in WhatsApp service for Lead #%s", lead.id)
                lead.whatsapp_sent = False
                lead.whatsapp_error = f"Service exception: {str(exc)}"

            # Step 4: Update notification status on lead
            lead.save(update_fields=["email_sent", "email_error", "whatsapp_sent", "whatsapp_error"])

            # Step 5: Update session and redirect
            request.session["submitted_lead_id"] = lead.id
            request.session["last_submission_time"] = current_time

            return redirect("leads:success")
    else:
        form = LeadContactForm()

    return render(
        request,
        "calculator/lead_form.html",
        {
            "form": form,
            "result": result,
            "turnstile_enabled": getattr(settings, "TURNSTILE_ENABLED", False),
            "turnstile_site_key": getattr(settings, "TURNSTILE_SITE_KEY", ""),
        },
    )


def success_view(request):
    """
    Renders confirmation page after successful lead submission.
    """
    lead_id = request.session.get("submitted_lead_id")
    lead = None
    if lead_id:
        lead = Lead.objects.filter(id=lead_id).first()

    return render(
        request,
        "calculator/success.html",
        {
            "lead": lead,
        },
    )
