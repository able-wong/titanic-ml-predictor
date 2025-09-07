#!/bin/bash

# Environment switcher script
# Usage: ./scripts/switch-env.sh [staging|production]

ENV=${1:-staging}

case $ENV in
  staging|stg)
    echo "🔄 Switching to staging environment..."
    ln -sf .env.stg .env
    firebase use staging
    echo "✅ Switched to staging environment"
    echo "📍 Project: titanic-ml-predictor-stg"
    ;;
  production|prd|prod)
    echo "🔄 Switching to production environment..."
    ln -sf .env.prd .env
    firebase use production
    echo "✅ Switched to production environment"
    echo "📍 Project: titanic-ml-predictor-prd"
    ;;
  *)
    echo "❌ Unknown environment: $ENV"
    echo "Usage: $0 [staging|production]"
    exit 1
    ;;
esac

echo ""
echo "🔍 Current environment configuration:"
echo "Active .env file: $(readlink .env || echo '.env (direct file)')"
echo "Firebase project: $(firebase use 2>/dev/null | grep 'Active project' || echo 'Not set')"