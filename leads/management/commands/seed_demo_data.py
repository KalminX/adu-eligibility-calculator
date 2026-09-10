"""
Management command to seed realistic demo leads for portfolio demonstration.
Safe, explicit, and never executed automatically in production.
"""

from django.core.management.base import BaseCommand
from leads.models import Lead


class Command(BaseCommand):
    help = "Seeds 3 realistic demo leads with different eligibility outcomes for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo leads before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted_count, _ = Lead.objects.filter(email__endswith="@example.com").delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} demo leads."))

        demo_leads_data = [
            {
                "name": "Sarah Jenkins",
                "email": "sarah.jenkins@example.com",
                "phone": "+1 (415) 555-0192",
                "eligibility_result": "Potentially Eligible",
                "answers": {
                    "owns_property": True,
                    "located_in_california": True,
                    "is_residential": True,
                    "is_single_family": True,
                    "has_sufficient_space": True,
                    "has_existing_structure": True,
                    "has_restrictions": False,
                },
                "email_sent": True,
                "whatsapp_sent": True,
            },
            {
                "name": "Carlos Rodriguez",
                "email": "carlos.rodriguez@example.com",
                "phone": "+1 (310) 555-0481",
                "eligibility_result": "Needs Further Review",
                "answers": {
                    "owns_property": True,
                    "located_in_california": True,
                    "is_residential": True,
                    "is_single_family": False,  # Multi-family duplex
                    "has_sufficient_space": False,
                    "has_existing_structure": True,  # Garage conversion potential
                    "has_restrictions": True,  # Easement reported
                },
                "email_sent": True,
                "whatsapp_sent": False,
                "whatsapp_error": "Mock mode: Simulated development delivery.",
            },
            {
                "name": "David Kim",
                "email": "david.kim@example.com",
                "phone": "+1 (619) 555-0723",
                "eligibility_result": "Currently Unlikely to Qualify",
                "answers": {
                    "owns_property": False,  # Non-owner renter
                    "located_in_california": True,
                    "is_residential": True,
                    "is_single_family": True,
                    "has_sufficient_space": False,
                    "has_existing_structure": False,
                    "has_restrictions": False,
                },
                "email_sent": False,
                "email_error": "Mock mode: RESEND_API_KEY is not configured.",
                "whatsapp_sent": False,
            },
        ]

        created_count = 0
        for data in demo_leads_data:
            lead, created = Lead.objects.get_or_create(
                email=data["email"],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created Lead: {lead.name} -> {lead.eligibility_result}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Lead already exists: {lead.name}"))

        self.stdout.write(self.style.SUCCESS(f"Finished seeding demo leads ({created_count} added)."))
