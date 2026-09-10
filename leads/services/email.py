"""
Email notification service using Resend API and official SDK.
Supports automated registrant confirmation emails, direct staff correspondence,
and graceful sandbox routing for testing with onboarding@resend.dev.
"""

import logging
from typing import Any, Dict, Optional
from django.conf import settings
import requests

try:
    import resend
except ImportError:
    resend = None

from calculator.eligibility import QUESTION_MAP

logger = logging.getLogger(__name__)


def build_registrant_email_content(lead: Any) -> Dict[str, str]:
    """
    Builds the personalized assessment results email delivered to the prospective
    property owner (the registrant) who completed the calculator.
    """
    first_name = lead.name.split()[0] if lead.name else "Property Owner"
    status = lead.eligibility_result

    # Status color & messaging
    if status == "Potentially Eligible":
        status_bg = "#ecfdf5"
        status_border = "#a7f3d0"
        status_text_color = "#065f46"
        status_description = (
            "Based on your responses, your property aligns with California ADU laws "
            "(AB 68, SB 9, SB 13). You may qualify for detached, attached, or conversion ADUs."
        )
    elif status == "Needs Further Review":
        status_bg = "#fffbeb"
        status_border = "#fde68a"
        status_text_color = "#92400e"
        status_description = (
            "Your property shows strong ADU potential, but specific factors (such as parcel easements "
            "or multi-family zoning) require individualized site review with local municipal codes."
        )
    else:
        status_bg = "#fff1f2"
        status_border = "#fecdd3"
        status_text_color = "#9f1239"
        status_description = (
            "Your responses identified key constraints (such as non-ownership or limited setback space). "
            "Our advisory team can discuss variances, alternative accessory structures, or junior ADU options."
        )

    # Format 7 answers
    answers_text = []
    answers_html = []
    for q_id, is_yes in (lead.answers or {}).items():
        question_text = QUESTION_MAP.get(q_id, {}).get("text", q_id)
        answer_str = "Yes" if is_yes else "No"
        answers_text.append(f"  - {question_text}: {answer_str}")
        answer_badge = (
            f"<span style='background:#dcfce7;color:#166534;padding:2px 8px;border-radius:9999px;font-weight:bold;font-size:12px;'>Yes</span>"
            if is_yes
            else f"<span style='background:#f1f5f9;color:#475569;padding:2px 8px;border-radius:9999px;font-weight:bold;font-size:12px;'>No</span>"
        )
        answers_html.append(
            f"<tr><td style='padding:10px 14px;border-bottom:1px solid #f1f5f9;color:#334155;font-size:13px;'>{question_text}</td>"
            f"<td style='padding:10px 14px;border-bottom:1px solid #f1f5f9;text-align:right;'>{answer_badge}</td></tr>"
        )

    answers_text_block = "\n".join(answers_text) or "  (No question data provided)"
    answers_html_block = "".join(answers_html) or "<tr><td colspan='2' style='padding:12px;'>No question data</td></tr>"

    subject = f"Your California ADU Feasibility Results - {status}"

    plain_text = f"""
Hello {first_name},

Thank you for completing the ADU Eligibility Assessment for your property.

YOUR PRELIMINARY FEASIBILITY OUTCOME:
{status.upper()}
{status_description}

YOUR QUESTIONNAIRE SUMMARY:
{answers_text_block}

WHAT HAPPENS NEXT:
1. Municipal Zoning & Setback Check: Our advisory team will review local jurisdiction ordinances for your parcel.
2. Buildable Envelope & Unit Sizing: We analyze maximum allowed square footage and configuration options.
3. Feasibility Consultation: We will follow up at {lead.phone} or reply to this email to discuss preliminary cost estimates and timelines.

Have questions or want to expedite your site evaluation?
Reply directly to this email or reach our advisory team.

Best regards,
California ADU Advisory Team
Inquiry Ref: #ADU-{lead.id:05d}
""".strip()

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#f8fafc;margin:0;padding:24px 12px;color:#1e293b;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
    
    <!-- Brand Header -->
    <div style="background-color:#0f172a;padding:24px;text-align:center;color:#ffffff;">
      <h1 style="margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px;">ADU Feasibility Assessment</h1>
      <p style="margin:6px 0 0 0;font-size:13px;color:#94a3b8;">Preliminary Zoning & Qualification Report</p>
    </div>

    <!-- Main Content -->
    <div style="padding:28px 24px;">
      
      <!-- Greeting -->
      <p style="font-size:15px;color:#334155;margin-top:0;line-height:1.6;">
        Hello <strong>{first_name}</strong>,
      </p>
      <p style="font-size:14px;color:#475569;line-height:1.6;margin-bottom:24px;">
        Thank you for completing our preliminary ADU evaluation. Below is your official feasibility assessment summary based on California state building regulations and your property parameters.
      </p>

      <!-- Outcome Banner -->
      <div style="background-color:{status_bg};border:1px solid {status_border};border-radius:10px;padding:18px 20px;margin-bottom:24px;">
        <span style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:{status_text_color};display:block;margin-bottom:4px;">
          Preliminary Feasibility Status
        </span>
        <h2 style="margin:0 0 8px 0;font-size:20px;font-weight:800;color:{status_text_color};">
          {status}
        </h2>
        <p style="margin:0;font-size:13px;color:#334155;line-height:1.5;">
          {status_description}
        </p>
      </div>

      <!-- Questionnaire Responses Table -->
      <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#475569;margin:24px 0 10px 0;border-bottom:1px solid #e2e8f0;padding-bottom:8px;">
        Your Questionnaire Responses
      </h3>
      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;background:#ffffff;border:1px solid #f1f5f9;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#f8fafc;text-align:left;">
            <th style="padding:8px 14px;font-size:12px;color:#64748b;font-weight:600;">Question</th>
            <th style="padding:8px 14px;font-size:12px;color:#64748b;font-weight:600;text-align:right;">Answer</th>
          </tr>
        </thead>
        <tbody>
          {answers_html_block}
        </tbody>
      </table>

      <!-- Next Steps Box -->
      <div style="background-color:#f8fafc;border-radius:10px;padding:18px;border:1px solid #e2e8f0;margin-bottom:24px;">
        <h4 style="margin:0 0 10px 0;font-size:13px;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:0.5px;">
          What Happens Next
        </h4>
        <ol style="margin:0;padding-left:20px;font-size:13px;color:#475569;line-height:1.6;">
          <li style="margin-bottom:6px;"><strong>Zoning & Setback Verification:</strong> We cross-reference municipal requirements (rear/side yard setback allowances, height limits).</li>
          <li style="margin-bottom:6px;"><strong>Configuration Analysis:</strong> We evaluate detached new-build vs. garage conversion square footage.</li>
          <li><strong>Advisory Follow-Up:</strong> A specialist will follow up at <strong>{lead.phone}</strong> or by email to share initial budget estimates.</li>
        </ol>
      </div>

      <!-- Contact CTA -->
      <div style="text-align:center;padding:10px 0;">
        <p style="font-size:13px;color:#64748b;margin:0 0 12px 0;">
          Want to discuss your parcel immediately? Reply directly to this email or speak with our planning desk.
        </p>
      </div>

    </div>

    <!-- Footer -->
    <div style="background-color:#f1f5f9;padding:16px 24px;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;text-align:center;">
      Inquiry Reference: <span style="font-family:monospace;font-weight:bold;color:#0f172a;">#ADU-{lead.id:05d}</span> &bull; California ADU Eligibility Calculator
    </div>

  </div>
</body>
</html>
"""

    return {
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }


def build_staff_direct_email_content(lead: Any, subject: str, message_body: str, sender_name: str) -> Dict[str, str]:
    """
    Builds the email sent directly by a staff advisor to a prospective property owner.
    """
    formatted_body_html = "<br>".join(message_body.split("\n"))

    plain_text = f"""
Hello {lead.name},

{message_body}

--------------------------------------------------
Inquiry Ref: #ADU-{lead.id:05d}
Sent by: {sender_name} (ADU Advisory Team)
Property Status: {lead.eligibility_result}
==================================================
""".strip()

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#f8fafc;margin:0;padding:24px 12px;color:#1e293b;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
    
    <!-- Brand Header -->
    <div style="background-color:#0f172a;padding:20px 24px;color:#ffffff;">
      <h2 style="margin:0;font-size:18px;font-weight:700;">ADU Advisor Correspondence</h2>
      <p style="margin:4px 0 0 0;font-size:12px;color:#94a3b8;">Direct message regarding your ADU inquiry (#ADU-{lead.id:05d})</p>
    </div>

    <!-- Message Body -->
    <div style="padding:28px 24px;">
      <p style="font-size:15px;color:#334155;margin-top:0;">
        Hello <strong>{lead.name}</strong>,
      </p>

      <div style="font-size:14px;color:#334155;line-height:1.7;margin:20px 0;padding:16px 20px;background:#f8fafc;border-left:4px solid #2563eb;border-radius:4px;">
        {formatted_body_html}
      </div>

      <div style="margin-top:28px;padding-top:16px;border-top:1px solid #e2e8f0;font-size:13px;color:#475569;">
        <strong>{sender_name}</strong><br>
        <span style="color:#64748b;">ADU Advisory Team</span>
      </div>
    </div>

    <!-- Footer -->
    <div style="background-color:#f1f5f9;padding:14px 24px;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;text-align:center;">
      Inquiry Reference: #ADU-{lead.id:05d} &bull; Property Feasibility: {lead.eligibility_result}
    </div>

  </div>
</body>
</html>
"""

    return {
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }


def build_email_content(lead: Any) -> Dict[str, str]:
    """
    Builds lead notification email representation (preserved for backward compatibility).
    """
    timestamp_str = (
        lead.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if lead.created_at
        else "Just now"
    )

    answers_text = []
    answers_html = []
    for q_id, is_yes in (lead.answers or {}).items():
        question_text = QUESTION_MAP.get(q_id, {}).get("text", q_id)
        answer_str = "Yes" if is_yes else "No"
        answers_text.append(f"  - {question_text}: {answer_str}")
        answers_html.append(
            f"<tr><td style='padding: 6px 12px; border-bottom: 1px solid #e2e8f0;'><strong>{question_text}</strong></td>"
            f"<td style='padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: {'#166534' if is_yes else '#991b1b'};'><strong>{answer_str}</strong></td></tr>"
        )

    answers_text_block = "\n".join(answers_text) or "  (No question data provided)"
    answers_html_block = "".join(answers_html) or "<tr><td colspan='2'>No question data</td></tr>"

    subject = f"New ADU Lead: {lead.name} ({lead.eligibility_result})"

    plain_text = f"""
==================================================
NEW ADU ELIGIBILITY LEAD
==================================================

CONTACT INFORMATION:
- Name:  {lead.name}
- Email: {lead.email}
- Phone: {lead.phone}

EVALUATION RESULT:
- Status: {lead.eligibility_result}
- Time:   {timestamp_str}

QUESTIONNAIRE RESPONSES:
{answers_text_block}

--------------------------------------------------
Lead ID: #{lead.id}
Generated by ADU Eligibility Calculator
==================================================
""".strip()

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <div style="background-color: #0f172a; padding: 20px; color: #ffffff;">
      <h2 style="margin: 0; font-size: 20px;">New ADU Eligibility Lead</h2>
      <p style="margin: 4px 0 0 0; font-size: 14px; color: #94a3b8;">Captured from public assessment tool</p>
    </div>
    <div style="padding: 24px;">
      <h3 style="font-size: 16px; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Prospect Details</h3>
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
        <tr><td style="padding: 6px 0; color: #64748b; width: 120px;">Full Name:</td><td><strong>{lead.name}</strong></td></tr>
        <tr><td style="padding: 6px 0; color: #64748b;">Email:</td><td><a href="mailto:{lead.email}" style="color: #2563eb;">{lead.email}</a></td></tr>
        <tr><td style="padding: 6px 0; color: #64748b;">Phone:</td><td><a href="tel:{lead.phone}" style="color: #2563eb;">{lead.phone}</a></td></tr>
        <tr><td style="padding: 6px 0; color: #64748b;">Eligibility Result:</td><td><span style="background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{lead.eligibility_result}</span></td></tr>
        <tr><td style="padding: 6px 0; color: #64748b;">Submitted At:</td><td>{timestamp_str}</td></tr>
      </table>
      <h3 style="font-size: 16px; margin-top: 24px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Questionnaire Responses</h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
          <tr style="background: #f1f5f9; text-align: left;">
            <th style="padding: 8px 12px;">Question</th>
            <th style="padding: 8px 12px;">Answer</th>
          </tr>
        </thead>
        <tbody>
          {answers_html_block}
        </tbody>
      </table>
    </div>
    <div style="background-color: #f8fafc; padding: 16px 24px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
      Lead ID #{lead.id} &bull; ADU Advisor Prototype
    </div>
  </div>
</body>
</html>
"""

    return {
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }


def dispatch_resend_email(
    to_email: str,
    subject: str,
    text: str,
    html: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core email dispatcher using Resend API.
    Supports official SDK (resend.Emails.send) and requests fallback.
    Automatically handles Resend sandbox restrictions by safely routing to the verified
    test address (settings.RESEND_SANDBOX_EMAIL) when using onboarding@resend.dev.
    """
    api_key = getattr(settings, "RESEND_API_KEY", "").strip()
    if not from_email:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "onboarding@resend.dev")

    # Safe development mock fallback when no key is set
    if not api_key:
        logger.info(
            "[EMAIL SERVICE] RESEND_API_KEY not configured. Email to %s mocked in development.",
            to_email,
        )
        return {
            "success": False,
            "simulated": True,
            "sandboxed": False,
            "message_id": None,
            "error": "RESEND_API_KEY is not configured (simulated in development).",
            "delivered_to": to_email,
        }

    sandbox_email = getattr(settings, "RESEND_SANDBOX_EMAIL", "noriabure@gmail.com").strip()

    # Step 1: Try sending via official Resend SDK if available
    if resend:
        resend.api_key = api_key
        try:
            r = resend.Emails.send({
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": text,
                "html": html,
            })
            msg_id = r.get("id") if isinstance(r, dict) else getattr(r, "id", "resend_ok")
            logger.info("Email delivered via Resend SDK to %s (ID: %s)", to_email, msg_id)
            return {
                "success": True,
                "simulated": False,
                "sandboxed": False,
                "message_id": msg_id,
                "error": None,
                "delivered_to": to_email,
            }
        except Exception as exc:
            err_str = str(exc)
            # Check for Resend free tier sandbox restriction:
            # "You can only send testing emails to your own email address..."
            is_sandbox_issue = (
                "only send testing emails" in err_str
                or "Invalid `to` field" in err_str
                or "testing email address" in err_str
            )

            if is_sandbox_issue and sandbox_email and to_email != sandbox_email:
                logger.warning(
                    "Resend sandbox restriction detected. Rerouting email to verified account %s (Target: %s)",
                    sandbox_email,
                    to_email,
                )
                sandbox_banner_html = f"""
                <div style="background-color:#fef3c7;border:1px solid #f59e0b;padding:12px 16px;border-radius:8px;margin-bottom:20px;font-size:12px;color:#92400e;line-height:1.5;">
                  <strong>Resend Sandbox Notice:</strong> In production with a custom verified domain, this email delivers directly to <code>{to_email}</code>. During development with <code>{from_email}</code>, Resend delivered this copy to your account email (<code>{sandbox_email}</code>).
                </div>
                """
                sandbox_banner_text = f"[Resend Sandbox Notice: Intended recipient: {to_email}. Delivered to account {sandbox_email} under onboarding@resend.dev policy.]\n\n"
                try:
                    r_sandbox = resend.Emails.send({
                        "from": from_email,
                        "to": [sandbox_email],
                        "subject": f"[Sandbox for {to_email}] {subject}",
                        "text": sandbox_banner_text + text,
                        "html": sandbox_banner_html + html,
                    })
                    msg_id = (
                        r_sandbox.get("id")
                        if isinstance(r_sandbox, dict)
                        else getattr(r_sandbox, "id", "resend_sandbox_ok")
                    )
                    logger.info("Sandbox email successfully delivered to %s (ID: %s)", sandbox_email, msg_id)
                    return {
                        "success": True,
                        "simulated": False,
                        "sandboxed": True,
                        "message_id": msg_id,
                        "error": None,
                        "delivered_to": sandbox_email,
                        "intended_recipient": to_email,
                    }
                except Exception as sandbox_exc:
                    logger.error("Failed even on sandbox email reroute: %s", sandbox_exc)
                    return {
                        "success": False,
                        "simulated": False,
                        "sandboxed": False,
                        "message_id": None,
                        "error": f"Resend SDK error: {str(sandbox_exc)}",
                        "delivered_to": to_email,
                    }

            # If not a sandbox issue, report real error
            logger.error("Failed to send email via Resend SDK to %s: %s", to_email, err_str)
            return {
                "success": False,
                "simulated": False,
                "sandboxed": False,
                "message_id": None,
                "error": f"Resend API error: {err_str}",
                "delivered_to": to_email,
            }

    # Step 2: Fallback to direct requests HTTP API
    endpoint = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ADU-Eligibility-Calculator/1.0",
    }
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": text,
        "html": html,
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            data = response.json()
            msg_id = data.get("id", "resend_ok")
            return {
                "success": True,
                "simulated": False,
                "sandboxed": False,
                "message_id": msg_id,
                "error": None,
                "delivered_to": to_email,
            }
        else:
            err_msg = f"Resend API error (HTTP {response.status_code}): {response.text}"
            logger.error("Failed to send email to %s: %s", to_email, err_msg)
            return {
                "success": False,
                "simulated": False,
                "sandboxed": False,
                "message_id": None,
                "error": err_msg,
                "delivered_to": to_email,
            }
    except requests.RequestException as exc:
        err_msg = f"Network exception connecting to Resend: {str(exc)}"
        logger.error("Exception sending email to %s: %s", to_email, err_msg)
        return {
            "success": False,
            "simulated": False,
            "sandboxed": False,
            "message_id": None,
            "error": err_msg,
            "delivered_to": to_email,
        }


def send_lead_email_notification(lead: Any) -> Dict[str, Any]:
    """
    Sends the official confirmation assessment report directly to the registrant (lead.email).
    Invoked when a prospective client completes the calculator or when staff re-dispatches.
    """
    content = build_registrant_email_content(lead)
    target_email = lead.email or getattr(settings, "LEAD_NOTIFICATION_EMAIL", "admin@example.com")

    return dispatch_resend_email(
        to_email=target_email,
        subject=content["subject"],
        text=content["text"],
        html=content["html"],
    )


def send_staff_email_to_lead(
    lead: Any,
    subject: str,
    message_body: str,
    sender_name: str = "ADU Advisory Team",
) -> Dict[str, Any]:
    """
    Sends a direct, personalized email composed by a staff member to a lead.
    """
    content = build_staff_direct_email_content(
        lead=lead,
        subject=subject,
        message_body=message_body,
        sender_name=sender_name,
    )

    return dispatch_resend_email(
        to_email=lead.email,
        subject=content["subject"],
        text=content["text"],
        html=content["html"],
    )
