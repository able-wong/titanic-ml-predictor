# Staging Environment JWT Keys

These are the JWT keys for the **staging** environment (`titanic-ml-predictor-stg`).

## Files
- `jwt_private.pem` - RSA private key for signing JWTs (Keep secure!)
- `jwt_public.pem` - RSA public key for verifying JWTs

## Usage

### Generate JWT for testing:
```bash
JWT_PRIVATE_KEY=$(cat secrets/stg/jwt_private.pem) \
  python 2-ml-service/scripts/generate_jwt.py --user-id test_user
```

### Deploy to staging:
```bash
./doit.sh env-switch staging
./doit.sh cloud-deploy
```

## Security Notes
- These keys are for STAGING only
- Never commit these files to git (they're in .gitignore)
- Rotate keys periodically
- Keys are also stored in Google Secret Manager for production deployments