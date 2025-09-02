#!/bin/bash

# Generate test JWT keys for local development
# This script creates RSA key pairs and exports them as environment variables

set -e

echo "🔑 Generating test JWT keys..."

# Generate RSA key pair
openssl genrsa -out test_private.pem 2048 2>/dev/null
openssl rsa -in test_private.pem -pubout -out test_public.pem 2>/dev/null

# Read keys into variables
PRIVATE_KEY=$(cat test_private.pem)
PUBLIC_KEY=$(cat test_public.pem)

# Clean up key files
rm test_private.pem test_public.pem

# Export as environment variables
export JWT_PRIVATE_KEY="$PRIVATE_KEY"
export JWT_PUBLIC_KEY="$PUBLIC_KEY"

echo "✅ Test JWT keys generated and exported"
echo ""
echo "To use these keys in your current shell session, run:"
echo "  source scripts/generate_test_keys.sh"
echo ""
echo "Or export them manually:"
echo "  export JWT_PRIVATE_KEY=\"\$JWT_PRIVATE_KEY\""
echo "  export JWT_PUBLIC_KEY=\"\$JWT_PUBLIC_KEY\""