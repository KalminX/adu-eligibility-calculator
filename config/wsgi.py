"""
WSGI config for ADU Eligibility Calculator project.

It exposes the WSGI callable as a module-level variable named ``application``.
Also exposes ``app`` for Vercel serverless functions deployment.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
app = application
