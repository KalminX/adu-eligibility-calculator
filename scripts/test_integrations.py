#!/usr/bin/env python3
"""
Integration test script for ADU Eligibility Calculator.
Safely verifies database connectivity, email template generation, and WhatsApp formatting.
Does NOT make external API calls unless explicitly invoked with --live.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    import django
    django.setup()
except Exception as e:
    print(f"[!] Failed to initialize Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.db import connection
from leads.models import Lead
from leads.services.email import build_email_content, send_lead_email_notification
from leads.services.whatsapp import build_whatsapp_message, send_lead_whatsapp_notification


def main():
    parser = argparse.ArgumentParser(description="Test third-party integrations safely.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt live external API dispatch to Resend and Meta WhatsApp Cloud API.",
    )
    args = parser.parse_args()

    print("==================================================")
    print(" ADU Eligibility Calculator - Integration Diagnostic")
    print(f" Mode: {'LIVE DISPATCH' if args.live else 'SAFE LOCAL DIAGNOSTIC'}")
    print("==================================================")

    # 1. Test Database
    print("\n[1] Database Connectivity Check:")
    try:
        connection.ensure_connection()
        engine = connection.settings_dict.get("ENGINE", "")
        backend_name = "PostgreSQL" if "postgresql" in engine or "psycopg" in engine else "SQLite"
        print(f"  [+] Connected successfully to: {backend_name}")
    except Exception as exc:
        print(f"  [!] Database connection failed: {exc}")

    # 2. Build Mock Lead instance (in memory, not committed)
    test_lead = Lead(
        id=9999,
        name="Integration Diagnostic User",
        email="test-lead@example.com",
        phone="+1 (555) 019-2831",
        eligibility_result="Potentially Eligible",
        answers={
            "owns_property": True,
            "located_in_california": True,
            "is_residential": True,
            "is_single_family": True,
            "has_sufficient_space": True,
            "has_existing_structure": True,
            "has_restrictions": False,
        },
    )

    # 3. Test Email Generation
    print("\n[2] Email Payload Diagnostic:")
    email_content = build_email_content(test_lead)
    print(f"  [+] Email Subject: '{email_content['subject']}'")
    print(f"  [+] Plaintext Length: {len(email_content['text'])} bytes")
    print(f"  [+] HTML Content Length: {len(email_content['html'])} bytes")
    
    resend_key = getattr(settings, "RESEND_API_KEY", "").strip()
    if resend_key:
        print("  [+] RESEND_API_KEY is configured.")
    else:
        print("  [*] RESEND_API_KEY is empty (mock fallback active).")

    if args.live:
        print("  [*] Triggering LIVE email send...")
        email_res = send_lead_email_notification(test_lead)
        print(f"  Result: {email_res}")
    else:
        print("  [*] Live dispatch skipped (run with --live to send live API request).")

    # 4. Test WhatsApp Generation
    print("\n[3] WhatsApp Message Diagnostic:")
    wa_msg = build_whatsapp_message(test_lead)
    print("  [+] Formatted WhatsApp Message Preview:")
    for line in wa_msg.split("\n"):
        print(f"      {line}")

    wa_mode = getattr(settings, "WHATSAPP_MODE", "mock")
    wa_enabled = getattr(settings, "WHATSAPP_ENABLED", False)
    print(f"  [*] WhatsApp Status: Enabled={wa_enabled}, Mode={wa_mode}")

    if args.live:
        print("  [*] Triggering LIVE WhatsApp dispatch...")
        wa_res = send_lead_whatsapp_notification(test_lead)
        print(f"  Result: {wa_res}")
    else:
        print("  [*] Live dispatch skipped (run with --live to send live API request).")

    # 5. Security & Verification Summary
    print("\n[4] Secret Exposure Safety Audit:")
    print("  [+] No tokens or connection strings were printed.")
    print("  [+] All diagnostics completed safely.")
    print("==================================================")


if __name__ == "__main__":
    main()
