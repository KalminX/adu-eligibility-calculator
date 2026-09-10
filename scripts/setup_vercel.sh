#!/usr/bin/env bash
# ==============================================================================
# Setup Vercel CLI & Link Project
# Safely checks Vercel CLI installation, authentication, and project linkage.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=================================================="
echo " ADU Eligibility Calculator - Vercel CLI Setup"
echo "=================================================="

# 1. Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo ""
    echo "[!] Vercel CLI is not installed on this system."
    echo ""
    echo "To install Vercel CLI, choose one of the following methods:"
    echo "  1) Using npm:   npm install -g vercel"
    echo "  2) Using pnpm:  pnpm add -g vercel"
    echo "  3) Using brew:  brew install vercel-cli"
    echo ""
    echo "After installation, re-run this script."
    exit 1
fi

VERCEL_VERSION=$(vercel --version)
echo "[+] Vercel CLI found: $VERCEL_VERSION"

# 2. Check if user is authenticated
echo "[*] Checking authentication status..."
if ! vercel whoami &> /dev/null; then
    echo ""
    echo "[!] You are not currently logged into Vercel."
    echo "Please authenticate by running:"
    echo "    vercel login"
    echo ""
    echo "Then rerun: ./scripts/setup_vercel.sh"
    exit 1
fi

CURRENT_USER=$(vercel whoami | head -n 1)
echo "[+] Authenticated as: $CURRENT_USER"

# 3. Check if project is already linked
if [ -d ".vercel" ] && [ -f ".vercel/project.json" ]; then
    echo "[+] Project is already linked to Vercel (.vercel/project.json exists)."
    echo ""
    echo "To inspect linked project configuration, run:"
    echo "    vercel project ls"
    exit 0
fi

# 4. Link project
echo ""
echo "[*] Project is not yet linked. Initializing link..."
PROJECT_NAME="adu-eligibility-calculator"
if [ -f ".env" ]; then
    ENV_NAME=$(grep "^VERCEL_PROJECT_NAME=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
    if [ -n "$ENV_NAME" ]; then
        PROJECT_NAME="$ENV_NAME"
    fi
fi

echo "Linking project with name '$PROJECT_NAME'..."
echo "Running 'vercel link'..."
vercel link --yes --project "$PROJECT_NAME"

echo ""
echo "[+] Project linkage complete!"
echo "Next steps:"
echo "  1) Push environment variables: ./scripts/push_env_to_vercel.sh production"
echo "  2) Deploy to Vercel: vercel --prod"
