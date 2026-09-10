#!/usr/bin/env bash
# ==============================================================================
# Vercel Deployment Build Script (GitHub Integration)
# Installs Python dependencies and collects static assets into staticfiles_build/static
# ==============================================================================

set -e

echo "=================================================="
echo " Vercel Build: ADU Eligibility Calculator"
echo "=================================================="

# 1. Upgrade pip
echo "[1/3] Upgrading pip..."
python3 -m pip install --upgrade pip

# 2. Install production dependencies
echo "[2/3] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# 3. Collect static files into staticfiles_build/static
echo "[3/3] Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "=================================================="
echo " Vercel Build Completed Successfully!"
echo "=================================================="
