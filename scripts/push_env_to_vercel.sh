#!/usr/bin/env bash
# ==============================================================================
# Push Environment Variables to Vercel
# Reads .env securely, lists variable names (never values), and pushes to Vercel.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

TARGET_ENV="${1:-}"

if [ -z "$TARGET_ENV" ]; then
    echo "Usage: $0 [production|preview|development]"
    echo "Example: $0 production"
    exit 1
fi

case "$TARGET_ENV" in
    production|preview|development)
        ;;
    *)
        echo "[!] Error: Invalid environment '$TARGET_ENV'. Must be one of: production, preview, development."
        exit 1
        ;;
esac

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[!] Error: Local '$ENV_FILE' not found. Please create it first."
    exit 1
fi

# Ensure Vercel CLI is present and logged in
if ! command -v vercel &> /dev/null; then
    echo "[!] Error: Vercel CLI is not installed. Run ./scripts/setup_vercel.sh first."
    exit 1
fi

if ! vercel whoami &> /dev/null; then
    echo "[!] Error: Not logged into Vercel. Run 'vercel login' first."
    exit 1
fi

echo "=================================================="
echo " ADU Eligibility Calculator - Push Env to Vercel"
echo " Target Environment: $TARGET_ENV"
echo "=================================================="

# Variables to exclude (internal Vercel identifiers or empty)
EXCLUDE_KEYS="VERCEL_ORG_ID VERCEL_PROJECT_ID VERCEL_PROJECT_NAME"

VARS_TO_SYNC=()

# First pass: parse variable keys that are non-empty and non-excluded
while IFS= read -r line || [ -n "$line" ]; do
    # Strip leading and trailing whitespace
    trimmed=$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    
    # Skip empty lines or comment lines
    if [ -z "$trimmed" ] || [[ "$trimmed" =~ ^# ]]; then
        continue
    fi

    # Extract key and value safely
    key="${trimmed%%=*}"
    val="${trimmed#*=}"

    # Remove quotes if present
    val=$(echo "$val" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

    # Skip if key is in exclusion list
    if [[ " $EXCLUDE_KEYS " =~ " $key " ]]; then
        continue
    fi

    # Skip empty values
    if [ -z "$val" ]; then
        continue
    fi

    VARS_TO_SYNC+=("$key")
done < "$ENV_FILE"

if [ ${#VARS_TO_SYNC[@]} -eq 0 ]; then
    echo "[*] No valid non-empty environment variables found in $ENV_FILE to sync."
    exit 0
fi

echo ""
echo "The following environment variable NAMES will be pushed to Vercel ($TARGET_ENV):"
echo "--------------------------------------------------"
for var_name in "${VARS_TO_SYNC[@]}"; do
    echo "  - $var_name"
done
echo "--------------------------------------------------"
echo "NOTE: Variable VALUES are securely hidden and will never be printed."
echo ""

read -p "Are you sure you want to push these to Vercel ($TARGET_ENV)? [y/N]: " -r CONFIRM
echo ""
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[*] Operation aborted by user. No changes made."
    exit 0
fi

echo "[*] Pushing variables securely to Vercel..."

SUCCESS_COUNT=0
FAIL_COUNT=0

for key in "${VARS_TO_SYNC[@]}"; do
    # Read actual value directly without echoing
    val=$(grep "^${key}=" "$ENV_FILE" | head -n 1 | cut -d '=' -f2-)
    val=$(echo "$val" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

    echo -n "  Updating $key ... "

    # Remove existing key first if it exists to avoid conflicts, then add
    vercel env rm "$key" "$TARGET_ENV" --yes &> /dev/null || true
    
    # Pipe value via stdin to prevent exposure in process table (ps) or logs
    if printf '%s' "$val" | vercel env add "$key" "$TARGET_ENV" &> /dev/null; then
        echo "[OK]"
        ((SUCCESS_COUNT++))
    else
        echo "[FAILED]"
        ((FAIL_COUNT++))
    fi
done

echo ""
echo "=================================================="
echo " Sync Summary: $SUCCESS_COUNT pushed successfully, $FAIL_COUNT failed."
echo "=================================================="
