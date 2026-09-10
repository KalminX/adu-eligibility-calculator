"""
Django settings for ADU Eligibility Calculator prototype.

Configured for local SQLite development and production PostgreSQL (Neon) via DATABASE_URL.
Deployable to Vercel with WhiteNoise static asset handling.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-development-placeholder-change-in-production-32-chars",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "t")

# Hosts configuration
allowed_hosts_raw = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_raw.split(",") if host.strip()]

# Ensure Vercel serverless domains, localhost, and test runner are always permitted
for host in [".vercel.app", ".now.sh", "localhost", "127.0.0.1", "testserver"]:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# CSRF Trusted Origins
csrf_trusted_raw = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in csrf_trusted_raw.split(",") if origin.strip()
]
for origin in ["https://*.vercel.app", "http://localhost:8000", "http://127.0.0.1:8000"]:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Project Apps
    "calculator.apps.CalculatorConfig",
    "leads.apps.LeadsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database Configuration
# Fallback to local SQLite if DATABASE_URL is empty; use PostgreSQL (e.g. Neon) if provided.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    is_postgres = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=is_postgres,
        )
    }
else:
    # In Vercel serverless, root filesystem is read-only; use /tmp for sqlite fallback if DATABASE_URL is missing
    sqlite_path = "/tmp/db.sqlite3" if os.getenv("VERCEL") else (BASE_DIR / "db.sqlite3")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# staticfiles_build/static matches Vercel static builder distDir "staticfiles_build" with route /static/$1
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"

# WhiteNoise storage: use CompressedStaticFilesStorage for robustness across dev, test, and prod
import sys

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
WHITENOISE_MANIFEST_STRICT = False

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security & Proxy Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# Third-Party Integrations Configuration

# 1. Email (Resend)
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
LEAD_NOTIFICATION_EMAIL = os.getenv("LEAD_NOTIFICATION_EMAIL", "admin@example.com")

# 2. WhatsApp (Meta Cloud API / Mock Mode)
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "False").lower() in ("true", "1", "yes", "t")
WHATSAPP_MODE = os.getenv("WHATSAPP_MODE", "mock").strip().lower()  # 'mock' or 'cloud_api'
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip()
WHATSAPP_RECIPIENT_PHONE = os.getenv("WHATSAPP_RECIPIENT_PHONE", "").strip()
WHATSAPP_GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v20.0").strip()

# 3. Cloudflare Turnstile Spam Protection
TURNSTILE_ENABLED = os.getenv("TURNSTILE_ENABLED", "False").lower() in ("true", "1", "yes", "t")
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "").strip()
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "").strip()

# Session configuration for calculator steps
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Staff & Admin Portal Authentication Configuration
LOGIN_URL = "/portal/login/"
LOGIN_REDIRECT_URL = "/portal/"
LOGOUT_REDIRECT_URL = "/portal/login/"
