"""
WhatsApp notification service supporting Meta Cloud API and safe Mock mode.

When WHATSAPP_MODE=mock (or WHATSAPP_ENABLED=False):
- Formats message and safely logs simulation.
- Does not call external APIs.

When WHATSAPP_MODE=cloud_api:
- Sends formatted payload via Meta WhatsApp Business Cloud API.
- Never logs auth tokens or secrets.
"""

import logging
from typing import Any, Dict
from django.conf import settings
import requests
from calculator.eligibility import QUESTION_MAP

logger = logging.getLogger(__name__)


def build_whatsapp_message(lead: Any) -> str:
    """
    Constructs a concise, professional WhatsApp alert text for property leads.
    """
    answers = lead.answers or {}
    
    # Format key answers concisely
    ca_status = "In CA" if answers.get("located_in_california") else "Outside CA"
    own_status = "Owner" if answers.get("owns_property") else "Non-Owner"
    sf_status = "Single-Family" if answers.get("is_single_family") else "Multi-Family/Other"
    space_status = "Sufficient Space" if answers.get("has_sufficient_space") else "Space Limited"
    has_struct = "Has Garage/Structure" if answers.get("has_existing_structure") else "No Structure"
    restrictions = "Reported Restrictions" if answers.get("has_restrictions") else "No Restrictions"

    lines = [
        "NEW ADU ELIGIBILITY LEAD",
        "--------------------------------",
        f"Name: {lead.name}",
        f"Phone: {lead.phone}",
        f"Email: {lead.email}",
        f"Eligibility: {lead.eligibility_result}",
        "--------------------------------",
        "Key Questionnaire Data:",
        f"- Status: {own_status} | {ca_status} | {sf_status}",
        f"- Site: {space_status} | {has_struct}",
        f"- Constraints: {restrictions}",
        "--------------------------------",
        f"Lead ID: #{lead.id}",
    ]
    return "\n".join(lines)


def send_lead_whatsapp_notification(lead: Any) -> Dict[str, Any]:
    """
    Dispatches lead notification via Meta Cloud API or simulates in mock mode.
    Returns structured status dict:
    {
        "success": bool,
        "simulated": bool,
        "mode": str,
        "message_id": Optional[str],
        "error": Optional[str],
    }
    """
    enabled = getattr(settings, "WHATSAPP_ENABLED", False)
    mode = getattr(settings, "WHATSAPP_MODE", "mock").lower()
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "").strip()
    recipient_phone = getattr(settings, "WHATSAPP_RECIPIENT_PHONE", "").strip()
    api_version = getattr(settings, "WHATSAPP_GRAPH_API_VERSION", "v20.0").strip()

    message_text = build_whatsapp_message(lead)

    # Disabled mode
    if not enabled:
        logger.info(
            "[WHATSAPP SERVICE] WhatsApp notifications are disabled (WHATSAPP_ENABLED=False). Skipping Lead #%s.",
            lead.id,
        )
        return {
            "success": False,
            "simulated": True,
            "mode": "disabled",
            "message_id": None,
            "error": "WhatsApp notifications disabled in configuration (WHATSAPP_ENABLED=False).",
        }

    # Mock mode
    if mode == "mock":
        logger.info(
            "[WHATSAPP SERVICE: MOCK MODE] Simulated WhatsApp notification for Lead #%s to %s:\n%s",
            lead.id,
            recipient_phone or "(No recipient configured)",
            message_text,
        )
        return {
            "success": True,
            "simulated": True,
            "mode": "mock",
            "message_id": f"mock_wa_{lead.id}",
            "error": None,
        }

    # Cloud API mode requires credentials
    if mode == "cloud_api":
        if not (access_token and phone_number_id and recipient_phone):
            missing = []
            if not access_token:
                missing.append("WHATSAPP_ACCESS_TOKEN")
            if not phone_number_id:
                missing.append("WHATSAPP_PHONE_NUMBER_ID")
            if not recipient_phone:
                missing.append("WHATSAPP_RECIPIENT_PHONE")
            err_msg = f"Cloud API mode requires missing credentials: {', '.join(missing)}"
            logger.error("[WHATSAPP SERVICE] %s", err_msg)
            return {
                "success": False,
                "simulated": False,
                "mode": "cloud_api",
                "message_id": None,
                "error": err_msg,
            }

        endpoint = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text,
            },
        }

        try:
            # Sensitive access token is deliberately NOT logged
            logger.info(
                "[WHATSAPP SERVICE] Sending Meta Cloud API message to recipient phone via endpoint version %s",
                api_version,
            )
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201):
                data = response.json()
                msg_id = (
                    data.get("messages", [{}])[0].get("id")
                    if data.get("messages")
                    else "wa_ok"
                )
                logger.info(
                    "WhatsApp message delivered successfully for Lead #%s (Msg ID: %s)",
                    lead.id,
                    msg_id,
                )
                return {
                    "success": True,
                    "simulated": False,
                    "mode": "cloud_api",
                    "message_id": msg_id,
                    "error": None,
                }
            else:
                err_msg = f"Meta WhatsApp API error (HTTP {response.status_code}): {response.text}"
                logger.error("Failed to send WhatsApp message for Lead #%s: %s", lead.id, err_msg)
                return {
                    "success": False,
                    "simulated": False,
                    "mode": "cloud_api",
                    "message_id": None,
                    "error": err_msg,
                }
        except requests.RequestException as exc:
            err_msg = f"Network exception contacting Meta WhatsApp API: {str(exc)}"
            logger.error("Exception sending WhatsApp for Lead #%s: %s", lead.id, err_msg)
            return {
                "success": False,
                "simulated": False,
                "mode": "cloud_api",
                "message_id": None,
                "error": err_msg,
            }

    # Unknown mode
    err_msg = f"Unknown WHATSAPP_MODE: '{mode}'. Expected 'mock' or 'cloud_api'."
    logger.error("[WHATSAPP SERVICE] %s", err_msg)
    return {
        "success": False,
        "simulated": False,
        "mode": mode,
        "message_id": None,
        "error": err_msg,
    }
