# ADU Eligibility Calculator

A production-oriented Django web application and lead-generation prototype designed to screen residential properties against California Accessory Dwelling Unit (ADU) guidelines, capture prospective owner leads, and dispatch real-time alerts via Email (Resend API) and WhatsApp (Meta Cloud API / Safe Mock Engine).

---

## 1. Project Overview

The **ADU Eligibility Calculator** ("ADU Advisor") provides homeowners and investors with an accessible 7-question preliminary screening tool to evaluate whether their property qualifies for detached, attached, or conversion ADU development under California statutory frameworks (such as SB 9, AB 68, AB 881).

Upon completing the questionnaire, prospects receive an instant feasibility evaluation (*Potentially Eligible*, *Needs Further Review*, or *Currently Unlikely to Qualify*) and can request a personalized consultation. Captured leads are committed to a transactional database, followed by automated notification dispatch to staff via Email and WhatsApp.

> **Demonstration Notice:** This application is a portfolio prototype demonstrating full-stack Django architecture, third-party API integration, resilience patterns, and serverless deployment. It is not formal legal, zoning, or architectural advice.

---

## 2. Key Features

- **Public Questionnaire (No Account Required):** 7 accessible Yes/No screening questions with responsive card selection and keyboard accessibility.
- **Deterministic Eligibility Engine:** Decoupled business logic (`calculator/eligibility.py`) evaluating lot area, zoning, ownership, and structural feasibility.
- **Session-Based State Management:** Preserves user inputs across assessment steps without sensitive query parameters.
- **Transactional Lead Capture:** Saves leads to the database *before* attempting notifications, ensuring zero prospect loss on third-party service outages.
- **Email Service (Resend):** Sends structured HTML and plaintext notifications with full question/answer transcripts. Includes mock fallback for local development.
- **WhatsApp Integration (Meta Cloud API & Mock Mode):** Formats concise operational alerts with safe fallback simulation when credentials are not configured.
- **Spam Defenses:** Hidden honeypot field rejecting automated bot submissions, plus ready support for Cloudflare Turnstile verification.
- **Django Admin Portal:** Searchable, filterable dashboard for staff to inspect leads, review raw answers, and audit notification logs.
- **Dual Database Architecture:** Zero-config SQLite for local development; automatic switch to PostgreSQL (Neon-ready) via `DATABASE_URL`.
- **Vercel Serverless Ready:** Pre-configured `vercel.json`, `build_files.sh`, and WhiteNoise static asset pipeline.

---

## 3. Tech Stack

- **Backend:** Python 3.13+, Django 5.2 (LTS compatible)
- **Database:** SQLite (local development) / PostgreSQL via `psycopg` & `dj-database-url` (Neon production)
- **Static Assets:** WhiteNoise 6.12+ with compressed static storage
- **Frontend:** Semantic Django Templates, Tailwind CSS (Utility classes), Lucide SVG icons (accessible, zero-CDN dependency)
- **Email:** Resend HTTP API (`requests`)
- **Messaging:** Meta WhatsApp Business Cloud API (Graph API v20.0) with local mock simulation
- **Deployment:** Vercel Python Serverless Runtime (`@vercel/python`, `@vercel/static-build`)

---

## 4. Architecture & Directory Structure

```
adu-eligibility-calculator/
├── .venv/                         # Isolated Python virtual environment (ignored)
├── .env                           # Local environment variables (ignored)
├── .env.example                   # Safe template for environment configuration
├── .gitignore                     # Git ignore rules for Python, Django, and secrets
├── README.md                      # Comprehensive project documentation
├── requirements.txt               # Pinned essential dependencies
├── manage.py                      # Django CLI utility
├── vercel.json                    # Vercel serverless build and routing configuration
├── build_files.sh                 # Vercel deployment preparation script
├── scripts/
│   ├── setup_vercel.sh            # Checks Vercel CLI and links project safely
│   ├── push_env_to_vercel.sh      # Pushes .env variables to Vercel without exposing secrets
│   └── test_integrations.py       # Standalone diagnostic tool for database & API payloads
├── config/
│   ├── __init__.py
│   ├── settings.py                # Dual DB settings, WhiteNoise, and integration configs
│   ├── urls.py                    # Root URL routing
│   ├── wsgi.py                    # WSGI entrypoint exposing `app` for Vercel
│   └── asgi.py
├── calculator/
│   ├── __init__.py
│   ├── apps.py
│   ├── eligibility.py             # Pure, deterministic assessment calculation logic
│   ├── forms.py                   # Questionnaire validation form
│   ├── urls.py                    # Routes: /, /calculator/questions/, /calculator/result/
│   ├── views.py                   # Public calculator views
│   └── tests.py                   # 100% test coverage for calculation rules & views
├── leads/
│   ├── __init__.py
│   ├── admin.py                   # Custom Django Admin with status badges & answers table
│   ├── apps.py
│   ├── forms.py                   # Lead contact form with honeypot & Turnstile validation
│   ├── models.py                  # Lead model with JSONField answers & notification status
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email.py               # Resend API service + development logger fallback
│   │   └── whatsapp.py            # Meta Cloud API service + mock simulator
│   ├── management/commands/
│   │   ├── test_integrations.py   # Safe config inspector (`python manage.py test_integrations`)
│   │   └── seed_demo_data.py      # Seeds realistic test leads (`python manage.py seed_demo_data`)
│   ├── tests/
│   │   ├── test_models.py
│   │   ├── test_forms.py
│   │   ├── test_views.py
│   │   ├── test_services.py
│   │   └── test_security.py       # Tests CSRF, honeypot, and notification failure resilience
│   ├── urls.py                    # Routes: /calculator/contact/, /calculator/success/
│   └── views.py                   # Transactional lead submission views
├── templates/
│   ├── base.html                  # Accessible layout, navigation, and footer
│   ├── calculator/
│   │   ├── index.html             # High-conversion landing page
│   │   ├── questions.html         # Accessible Yes/No card questionnaire
│   │   ├── result.html            # Feasibility report with factors and disclaimer
│   │   ├── lead_form.html         # Contact capture form with privacy consent
│   │   └── success.html           # Confirmation page with reference number
│   └── registration/
│       └── login.html             # Styled staff portal login
└── static/
    ├── css/app.css                # Custom utilities and honeypot positioning
    └── js/calculator.js           # Progressive enhancement for stepped card navigation
```

---

## 5. Local Setup Guide

### Step 1: Clone or Navigate to Directory
```bash
cd adu-eligibility-calculator
```

### Step 2: Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
The default `.env` is already configured for out-of-the-box local development:
- Uses **SQLite** automatically when `DATABASE_URL` is empty.
- Runs Email in **mock logging mode** when `RESEND_API_KEY` is empty.
- Runs WhatsApp in **mock simulation mode** (`WHATSAPP_MODE=mock`).

### Step 5: Run Database Migrations
```bash
python manage.py migrate
```

### Step 6: Create Staff Superuser
For local development, create a superuser non-interactively:
```bash
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=adminpassword123 \
python manage.py createsuperuser --noinput
```
*(Or run `python manage.py createsuperuser` to set custom credentials).*

### Step 7: (Optional) Seed Realistic Demo Leads
```bash
python manage.py seed_demo_data
```

### Step 8: Verify System Checks & Diagnostics
```bash
python manage.py check
python manage.py test_integrations
```

### Step 9: Start Local Development Server
```bash
python manage.py runserver
```
Visit:
- **Public Calculator:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Staff Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) (Login: `admin` / `adminpassword123`)

---

## 6. Database Configuration (Local SQLite vs. Neon PostgreSQL)

The application dynamically detects database configuration via `config/settings.py`:

- **Local Development:** When `DATABASE_URL` is empty or omitted, Django automatically provisions `db.sqlite3` in the project root.
- **Production (Neon PostgreSQL):** Provide your Neon connection string in `DATABASE_URL`.

### Obtaining a Free Neon PostgreSQL Database:
1. Sign up at [neon.tech](https://neon.tech) (free tier requires no credit card).
2. Create a project named `adu-calculator`.
3. In the Neon Dashboard, copy the **Connection String** (choose **PostgreSQL** or **Pooled connection**).
   Example format:
   ```
   postgresql://[user]:[password]@[endpoint].us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Place this string into your `.env` or Vercel environment settings:
   ```env
   DATABASE_URL=postgresql://[user]:[password]@[endpoint].us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Apply migrations to the Neon database:
   ```bash
   DATABASE_URL="your-neon-url" python manage.py migrate
   ```

---

## 7. Third-Party Integrations Setup

### A. Email Integration (Resend)
1. Sign up at [resend.com](https://resend.com).
2. Generate an API key under **API Keys**.
3. In `.env`, set:
   ```env
   EMAIL_PROVIDER=resend
   RESEND_API_KEY=re_your_api_key_here
   DEFAULT_FROM_EMAIL=onboarding@resend.dev  # Or your verified domain
   LEAD_NOTIFICATION_EMAIL=your-team@example.com
   ```
4. **Local Development Fallback:** If `RESEND_API_KEY` is left blank, the application will not crash or attempt external network calls. It formats the email payload, logs a simulation event, and safely records the status on the lead.

### B. WhatsApp Integration (Meta Cloud API vs. Mock)
To prevent build failures and allow local testing without Meta developer approvals, the application implements a dual-mode strategy:

- **Mock Mode (Default):**
  ```env
  WHATSAPP_ENABLED=True
  WHATSAPP_MODE=mock
  ```
  Generates the exact WhatsApp alert payload, logs the message preview safely to standard logging, and records `whatsapp_sent=True` (simulated). External networks are never contacted.

- **Live Production Mode (Meta WhatsApp Cloud API):**
  When Meta developer credentials become available:
  1. Create a Meta Developer App at [developers.facebook.com](https://developers.facebook.com) with WhatsApp product enabled.
  2. Obtain your **Phone Number ID**, **Access Token**, and **WhatsApp Business Account ID**.
  3. In `.env` (or Vercel):
     ```env
     WHATSAPP_ENABLED=True
     WHATSAPP_MODE=cloud_api
     WHATSAPP_ACCESS_TOKEN=EAAB...
     WHATSAPP_PHONE_NUMBER_ID=109283746501928
     WHATSAPP_BUSINESS_ACCOUNT_ID=981726354019283
     WHATSAPP_RECIPIENT_PHONE=+15551234567
     WHATSAPP_GRAPH_API_VERSION=v20.0
     ```

### C. Cloudflare Turnstile Spam Protection
1. Obtain site key and secret key from Cloudflare Dashboard > Turnstile.
2. In `.env`:
   ```env
   TURNSTILE_ENABLED=True
   TURNSTILE_SITE_KEY=0x4AAAA...
   TURNSTILE_SECRET_KEY=0x4AAAA...
   ```
   When `TURNSTILE_ENABLED=False`, Turnstile is completely bypassed and forms rely on the built-in honeypot field.

---

## 8. Deployment to Vercel (GitHub Integration & Vercel CLI)

### Method A: Smooth Deployment via GitHub (Recommended)
1. **Push your local repository to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit: ADU Eligibility Calculator prototype"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Import into Vercel:**
   - Log into [vercel.com](https://vercel.com) and click **"Add New Project"**.
   - Select **"Import Git Repository"** and choose your GitHub repo.
   - **Framework Preset:** Vercel automatically detects `vercel.json` (no manual build override needed).
   - **Build & Output Settings:** Managed by `vercel.json` and `build_files.sh` (`staticfiles_build`).

3. **Configure Environment Variables in Vercel:**
   Add the following under **Project Settings > Environment Variables**:
   - `DATABASE_URL`: `postgresql://[user]:[password]@[endpoint].neon.tech/neondb?sslmode=require`
   - `SECRET_KEY`: A strong, random production secret key
   - `ALLOWED_HOSTS`: `.vercel.app,yourcustomdomain.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app,https://yourcustomdomain.com`
   - `RESEND_API_KEY`: Your live API key from Resend
   - `DEFAULT_FROM_EMAIL`: `onboarding@resend.dev` (or verified domain)
   - `LEAD_NOTIFICATION_EMAIL`: `team@yourdomain.com`
   - `WHATSAPP_ENABLED`: `False` (or `True` if using Meta Cloud API)
   - `WHATSAPP_MODE`: `mock` (or `cloud_api`)

4. **Run Initial Database Migrations on Neon:**
   From your local terminal, point `DATABASE_URL` to Neon to initialize tables:
   ```bash
   DATABASE_URL="postgresql://user:pass@endpoint.neon.tech/neondb?sslmode=require" python manage.py migrate
   ```

5. **Automatic Continuous Deployment:**
   Every subsequent `git push origin main` triggers an automated build on Vercel, executes `build_files.sh`, bundles static files to Vercel's global CDN, and updates serverless functions with 0 downtime.

### Method B: Deployment via Vercel CLI
```bash
# 1. Verify Vercel CLI and link project safely
./scripts/setup_vercel.sh

# 2. Push environment variables securely
./scripts/push_env_to_vercel.sh production

# 3. Deploy to production
vercel --prod
```

---

## 9. Custom Staff & Admin Lead Management Portal

In addition to Django's standard `/admin/`, this prototype includes a **dedicated custom management portal** built with Tailwind CSS:

* **Portal URL:** `/portal/`
* **Login URL:** `/portal/login/`
* **Features:**
  * **Real-time KPI Cards:** Total inquiries, eligible count, review required count, unlikely count, and email/WhatsApp delivery metrics.
  * **Multi-Criteria Filter & Search:** Filter by lead name, email, phone, feasibility outcome, email delivery status, and date sorting.
  * **Lead Details & Questionnaire Transcript:** Complete customer overview with raw answers table for all 7 questions.
  * **One-Click Notification Re-dispatch:** Staff can manually trigger email (Resend) or WhatsApp dispatch directly from the lead detail view.
  * **CSV Data Export:** One-click download of filtered lead data for CRM / spreadsheet workflows.
  * **Role-Based Permissions:** Restricts access to staff (`is_staff=True`) and superusers; rejects unauthenticated or unauthorized users with a clean access control screen.

Credentials for local testing are provided in the git-ignored `logins.txt` file.

---

## 9. Automated Testing Suite

The repository includes a comprehensive, isolated test suite covering business logic, security boundaries, and edge cases. External network calls are strictly mocked.

To run all 42 tests:
```bash
python manage.py test
```

### Test Coverage Highlights:
- **Eligibility Engine (`calculator/tests.py`):** Tests every qualifying and disqualifying property combination (ownership, zoning, yard space, existing structures, California geography).
- **Form Validation (`leads/tests/test_forms.py`):** Verifies phone number formats, whitespace normalization, email lowercasing, and honeypot trapping.
- **Transactional Safety (`leads/tests/test_security.py`):** Verifies that if email or WhatsApp services crash or experience outages, the Lead record is safely preserved in the database.
- **CSRF & Authentication (`leads/tests/test_security.py`):** Ensures public routes remain anonymously accessible while staff admin endpoints reject unauthenticated requests.
- **Mock Services (`leads/tests/test_services.py`):** Audits simulated fallback responses when credentials are absent.

---

## 10. Security & Data Privacy

- **No Secrets in Code:** Zero hardcoded credentials. All secrets are loaded via environment variables.
- **No Secrets in Version Control:** `.env` is ignored by Git; `.env.example` contains only harmless placeholders.
- **Audit & Logging Safety:** Access tokens and database connection strings are filtered from application logs.
- **CSRF Enforcement:** Standard Django CSRF token verification across all POST requests.
- **Input Sanitization:** Server-side validation on all inputs; phone numbers and emails are normalized.
- **Honeypot Trap:** Transparent to assistive technology and human users, trapping automated spambots.
- **Privacy Notice:** Explicit consent disclaimer on the lead capture form notifying prospects that data is stored solely for consulting and never shared or sold.

---

## 11. Upwork Portfolio Summary

| Area | Implementation Highlights |
| :--- | :--- |
| **Framework** | Clean Django 5.2 architecture, modular apps (`calculator`, `leads`) |
| **Styling** | Modern Tailwind CSS layout without JavaScript frameworks (React/Vue not needed) |
| **UI Polish** | Accessible Lucide SVG icons; strict adherence to zero UI emojis |
| **Resilience** | Lead persistence guaranteed prior to external notification dispatch |
| **Deployability** | One-command Vercel readiness with Neon PostgreSQL and WhiteNoise |
