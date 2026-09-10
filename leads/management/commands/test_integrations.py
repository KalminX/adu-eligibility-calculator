"""
Management command to safely inspect integration status without exposing credentials.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = "Inspects third-party integration configuration status without leaking secrets."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== ADU Calculator Integration Status ==="))

        # 1. Database Check
        try:
            connection.ensure_connection()
            db_engine = connection.settings_dict.get("ENGINE", "Unknown")
            is_postgres = "postgresql" in db_engine or "psycopg" in db_engine
            db_type = "PostgreSQL (Production/Neon)" if is_postgres else "SQLite (Local Development)"
            self.stdout.write(f"Database:       {self.style.SUCCESS('CONNECTED')} [{db_type}]")
        except Exception as e:
            self.stdout.write(f"Database:       {self.style.ERROR(f'FAILED - {e}')}")

        # 2. Email Service (Resend)
        resend_key = getattr(settings, "RESEND_API_KEY", "").strip()
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Not set")
        lead_email = getattr(settings, "LEAD_NOTIFICATION_EMAIL", "Not set")

        if resend_key:
            email_status = self.style.SUCCESS("CONFIGURED (Live Resend API)")
        else:
            email_status = self.style.WARNING("MOCK / LOG ONLY (RESEND_API_KEY empty)")

        self.stdout.write(f"Email Service:  {email_status}")
        self.stdout.write(f"  - Provider:   {getattr(settings, 'EMAIL_PROVIDER', 'resend')}")
        self.stdout.write(f"  - Sender:     {from_email}")
        self.stdout.write(f"  - Recipient:  {lead_email}")

        # 3. WhatsApp Integration
        wa_enabled = getattr(settings, "WHATSAPP_ENABLED", False)
        wa_mode = getattr(settings, "WHATSAPP_MODE", "mock")
        wa_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "").strip()
        wa_phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "").strip()
        wa_recipient = getattr(settings, "WHATSAPP_RECIPIENT_PHONE", "").strip()
        wa_version = getattr(settings, "WHATSAPP_GRAPH_API_VERSION", "v20.0")

        if not wa_enabled:
            wa_status = self.style.WARNING("DISABLED (WHATSAPP_ENABLED=False)")
        elif wa_mode == "mock":
            wa_status = self.style.WARNING("MOCK MODE (Safe local simulation, no Meta API call)")
        elif wa_mode == "cloud_api":
            if wa_token and wa_phone_id and wa_recipient:
                wa_status = self.style.SUCCESS(f"CONFIGURED (Meta Cloud API {wa_version})")
            else:
                wa_status = self.style.ERROR("INCOMPLETE CREDENTIALS (cloud_api selected but keys missing)")
        else:
            wa_status = self.style.ERROR(f"UNKNOWN MODE: {wa_mode}")

        self.stdout.write(f"WhatsApp:       {wa_status}")
        self.stdout.write(f"  - Mode:       {wa_mode}")
        self.stdout.write(f"  - Recipient:  {wa_recipient or 'None configured'}")

        # 4. Turnstile Spam Protection
        turnstile_enabled = getattr(settings, "TURNSTILE_ENABLED", False)
        turnstile_site = getattr(settings, "TURNSTILE_SITE_KEY", "").strip()
        turnstile_secret = getattr(settings, "TURNSTILE_SECRET_KEY", "").strip()

        if turnstile_enabled:
            if turnstile_site and turnstile_secret:
                turnstile_status = self.style.SUCCESS("ENABLED (Site Key & Secret configured)")
            else:
                turnstile_status = self.style.WARNING("ENABLED but Site Key or Secret is missing")
        else:
            turnstile_status = self.style.NOTICE("DISABLED (Default development mode)")

        self.stdout.write(f"Turnstile:      {turnstile_status}")

        # 5. Security & Static Summary
        debug_mode = getattr(settings, "DEBUG", False)
        debug_status = self.style.WARNING("ON (Development)") if debug_mode else self.style.SUCCESS("OFF (Production)")
        self.stdout.write(f"Debug Mode:     {debug_status}")
        self.stdout.write(f"Static Serving: WhiteNoise configured")

        self.stdout.write(self.style.MIGRATE_HEADING("==========================================="))
