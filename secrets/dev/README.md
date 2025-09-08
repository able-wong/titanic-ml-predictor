# Development Environment JWT Keys

These are the JWT keys for **local development**.

## Files
- `jwt_private.pem` - RSA private key for signing JWTs (Keep secure!)
- `jwt_public.pem` - RSA public key for verifying JWTs

## Usage

### Export keys for local development:
```bash
# Option 1: Use doit.sh command (recommended)
eval "$(./doit.sh export-dev-secrets)"

# Option 2: Get help with export commands
./doit.sh use-dev-secrets

# Option 3: Manual export
export JWT_PRIVATE_KEY="$(cat secrets/dev/jwt_private.pem)"
export JWT_PUBLIC_KEY="$(cat secrets/dev/jwt_public.pem)"
```

### Start development server:
```bash
# Keys must be exported first (see above)
./doit.sh python-service-start
```

### Generate test JWT token:
```bash
# Keys must be exported first
python 2-ml-service/scripts/generate_jwt.py --user-id test_user
```

## Benefits
- **Consistent keys** across development sessions
- **No regeneration** needed between restarts
- **Same workflow** as staging/production environments
- **Persistent storage** in local files

## Security Notes
- These keys are for DEVELOPMENT only
- Never use dev keys in production
- Keys are gitignored (not committed to repository)
- Rotate keys periodically for security