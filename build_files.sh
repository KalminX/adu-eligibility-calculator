#!/usr/bin/env bash
# ==============================================================================
# Vercel Deployment Build Script (GitHub Integration)
# Installs Python 3.12 dependencies and collects static assets into staticfiles_build/static
# Compatible with modern Vercel uv package manager and standard environments
# ==============================================================================

set -e

echo "=================================================="
echo " Vercel Build: ADU Eligibility Calculator"
echo "=================================================="

# Check if uv package manager is available (modern Vercel builders)
if command -v uv &> /dev/null; then
    echo "[1/2] Installing Python 3.12 via uv..."
    uv python install 3.12
    
    echo "Creating Python 3.12 build virtualenv..."
    uv venv --python 3.12 .vercel_build_env
    
    # Activate Python 3.12 build virtualenv
    source .vercel_build_env/bin/activate
    
    echo "Installing requirements with uv..."
    uv pip install -r requirements.txt
    
    echo "[2/2] Collecting static files with Django..."
    python manage.py collectstatic --noinput --clear
    
    deactivate
    rm -rf .vercel_build_env
else
    echo "[1/2] Installing dependencies via pip..."
    python3 -m pip install -r requirements.txt --break-system-packages || python3 -m pip install -r requirements.txt
    
    echo "[2/2] Collecting static files with Django..."
    python3 manage.py collectstatic --noinput --clear
fi

echo "=================================================="
echo " Vercel Build Completed Successfully!"
echo "=================================================="
