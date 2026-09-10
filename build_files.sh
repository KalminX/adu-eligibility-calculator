#!/usr/bin/env bash
# ==============================================================================
# Vercel Deployment Build Script (GitHub Integration)
# Installs Python dependencies and collects static assets into staticfiles_build/static
# Compatible with modern Vercel uv-managed Python environments (PEP 668) & standard pip
# ==============================================================================

set -e

echo "=================================================="
echo " Vercel Build: ADU Eligibility Calculator"
echo "=================================================="

# 1. Install production dependencies
echo "[1/2] Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv pip install -r requirements.txt --system
else
    echo "Using pip package manager..."
    python3 -m pip install -r requirements.txt --break-system-packages || python3 -m pip install -r requirements.txt
fi

# 2. Collect static files into staticfiles_build/static
echo "[2/2] Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "=================================================="
echo " Vercel Build Completed Successfully!"
echo "=================================================="
