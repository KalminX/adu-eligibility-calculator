"""
Views for the Custom Staff & Administrator Lead Management Portal.
Provides lead pipeline management, KPI analytics, notification audits,
manual resends, search & filtering, and CSV export without relying on default Django admin.
"""

import csv
import re
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from calculator.eligibility import QUESTIONS, QUESTION_MAP, normalize_bool
from .models import Lead
from .services.email import send_lead_email_notification
from .services.whatsapp import send_lead_whatsapp_notification


def staff_required(view_func):
    """
    Decorator requiring user to be logged in and possess staff permissions.
    Redirects unauthenticated users to /portal/login/.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/portal/login/?next={request.path}")
        if not request.user.is_staff:
            return render(
                request,
                "portal/access_denied.html",
                {
                    "message": "Your user account is authenticated but lacks staff authorization for this portal.",
                },
                status=403,
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def portal_login(request):
    """Custom, branded login interface for staff & administrators."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("portal:dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or "/portal/"

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect(next_url)
            else:
                messages.error(
                    request,
                    "Access restricted: Your account does not have staff permissions to access the management portal.",
                )
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "portal/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


def portal_logout(request):
    """Logs out the active staff user and redirects to portal login."""
    logout(request)
    messages.info(request, "You have been safely signed out of the staff portal.")
    return redirect("portal:login")


@staff_required
def portal_dashboard(request):
    """
    Primary Lead Management Portal Dashboard.
    Features KPI analytics, multi-criteria filtering, search, and paginated lead lists.
    """
    # 1. Base Queryset
    queryset = Lead.objects.all()

    # 2. Search Filter
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
        )

    # 3. Eligibility Filter
    eligibility_filter = request.GET.get("eligibility", "").strip()
    if eligibility_filter in ("Potentially Eligible", "Needs Further Review", "Currently Unlikely to Qualify"):
        queryset = queryset.filter(eligibility_result=eligibility_filter)

    # 4. Notification Status Filters
    email_filter = request.GET.get("email_status", "").strip()
    if email_filter == "sent":
        queryset = queryset.filter(email_sent=True)
    elif email_filter == "failed":
        queryset = queryset.filter(email_sent=False)

    wa_filter = request.GET.get("wa_status", "").strip()
    if wa_filter == "sent":
        queryset = queryset.filter(whatsapp_sent=True)
    elif wa_filter == "failed":
        queryset = queryset.filter(whatsapp_sent=False)

    # 5. Sorting
    sort = request.GET.get("sort", "newest")
    if sort == "oldest":
        queryset = queryset.order_by("created_at")
    else:
        queryset = queryset.order_by("-created_at")

    # 6. KPI Metrics Calculation (computed across all leads)
    all_leads = Lead.objects.all()
    total_count = all_leads.count()
    eligible_count = all_leads.filter(eligibility_result="Potentially Eligible").count()
    review_count = all_leads.filter(eligibility_result="Needs Further Review").count()
    unlikely_count = all_leads.filter(eligibility_result="Currently Unlikely to Qualify").count()
    email_delivered_count = all_leads.filter(email_sent=True).count()
    wa_delivered_count = all_leads.filter(whatsapp_sent=True).count()

    # 7. Pagination
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "portal/dashboard.html",
        {
            "page_obj": page_obj,
            "total_count": total_count,
            "eligible_count": eligible_count,
            "review_count": review_count,
            "unlikely_count": unlikely_count,
            "email_delivered_count": email_delivered_count,
            "wa_delivered_count": wa_delivered_count,
            "query": query,
            "eligibility_filter": eligibility_filter,
            "email_filter": email_filter,
            "wa_filter": wa_filter,
            "sort": sort,
        },
    )


@staff_required
def portal_lead_detail(request, lead_id: int):
    """
    Detailed inspection view for an individual prospective lead.
    Displays customer contact details, 7-question answers transcript, and notification dispatch logs.
    """
    lead = get_object_or_404(Lead, id=lead_id)

    # Clean question responses transcript
    formatted_responses = []
    answers_dict = lead.answers or {}
    for q in QUESTIONS:
        val = answers_dict.get(q["id"])
        is_yes = normalize_bool(val)
        formatted_responses.append(
            {
                "id": q["id"],
                "text": q["text"],
                "help_text": q["help_text"],
                "answer_text": "Yes" if is_yes else "No",
                "is_yes": is_yes,
            }
        )

    # Format phone digits for direct WhatsApp web link
    clean_digits = re.sub(r"\D", "", lead.phone)

    return render(
        request,
        "portal/lead_detail.html",
        {
            "lead": lead,
            "formatted_responses": formatted_responses,
            "clean_phone_digits": clean_digits,
        },
    )


@staff_required
def portal_resend_email(request, lead_id: int):
    """Triggers manual re-dispatch of the lead email notification."""
    if request.method != "POST":
        return HttpResponseForbidden("POST required.")

    lead = get_object_or_404(Lead, id=lead_id)
    result = send_lead_email_notification(lead)

    lead.email_sent = result.get("success", False)
    if result.get("error"):
        lead.email_error = result["error"]
    elif result.get("simulated"):
        lead.email_error = "Mock mode: Simulated development delivery."
    else:
        lead.email_error = ""

    lead.save(update_fields=["email_sent", "email_error"])

    if lead.email_sent:
        messages.success(request, f"Email notification successfully sent for Lead #{lead.id}.")
    elif result.get("simulated"):
        messages.info(request, f"Simulated email send logged for Lead #{lead.id} (RESEND_API_KEY mock mode).")
    else:
        messages.warning(request, f"Email send failed for Lead #{lead.id}: {result.get('error')}")

    return redirect("portal:lead_detail", lead_id=lead.id)


@staff_required
def portal_resend_whatsapp(request, lead_id: int):
    """Triggers manual re-dispatch of the lead WhatsApp notification."""
    if request.method != "POST":
        return HttpResponseForbidden("POST required.")

    lead = get_object_or_404(Lead, id=lead_id)
    result = send_lead_whatsapp_notification(lead)

    lead.whatsapp_sent = result.get("success", False)
    if result.get("error"):
        lead.whatsapp_error = result["error"]
    elif result.get("simulated"):
        lead.whatsapp_error = "Mock mode: Simulated development delivery."
    else:
        lead.whatsapp_error = ""

    lead.save(update_fields=["whatsapp_sent", "whatsapp_error"])

    if lead.whatsapp_sent and not result.get("simulated"):
        messages.success(request, f"WhatsApp message successfully sent via Meta Cloud API for Lead #{lead.id}.")
    elif result.get("simulated"):
        messages.info(request, f"WhatsApp message simulated for Lead #{lead.id} (Mock mode).")
    else:
        messages.warning(request, f"WhatsApp delivery failed for Lead #{lead.id}: {result.get('error')}")

    return redirect("portal:lead_detail", lead_id=lead.id)


@staff_required
def portal_lead_delete(request, lead_id: int):
    """Allows authorized staff to permanently delete a lead record."""
    if request.method != "POST":
        return HttpResponseForbidden("POST required.")

    lead = get_object_or_404(Lead, id=lead_id)
    lead_name = lead.name
    lead_ref = lead.id
    lead.delete()

    messages.success(request, f"Lead #{lead_ref} ({lead_name}) was successfully deleted.")
    return redirect("portal:dashboard")


@staff_required
def portal_export_csv(request):
    """Exports filtered leads as a downloadable CSV spreadsheet."""
    queryset = Lead.objects.all().order_by("-created_at")

    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
        )

    eligibility_filter = request.GET.get("eligibility", "").strip()
    if eligibility_filter:
        queryset = queryset.filter(eligibility_result=eligibility_filter)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="adu_leads_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Lead ID",
        "Full Name",
        "Email",
        "Phone",
        "Eligibility Result",
        "Email Sent",
        "WhatsApp Sent",
        "Submission Date (UTC)",
        "Owns Property",
        "In California",
        "Residential",
        "Single Family",
        "Sufficient Space",
        "Existing Structure",
        "Restrictions",
    ])

    for lead in queryset:
        ans = lead.answers or {}
        writer.writerow([
            lead.id,
            lead.name,
            lead.email,
            lead.phone,
            lead.eligibility_result,
            "Yes" if lead.email_sent else "No",
            "Yes" if lead.whatsapp_sent else "No",
            lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else "",
            "Yes" if ans.get("owns_property") else "No",
            "Yes" if ans.get("located_in_california") else "No",
            "Yes" if ans.get("is_residential") else "No",
            "Yes" if ans.get("is_single_family") else "No",
            "Yes" if ans.get("has_sufficient_space") else "No",
            "Yes" if ans.get("has_existing_structure") else "No",
            "Yes" if ans.get("has_restrictions") else "No",
        ])

    return response
