# Production Environment JWT Keys

These are the JWT keys for the **production** environment (`titanic-ml-predictor-prd`).

## Files
- `jwt_private.pem` - RSA private key for signing JWTs (Keep secure!)
- `jwt_public.pem` - RSA public key for verifying JWTs

## Usage

### Generate JWT for production:
```bash
JWT_PRIVATE_KEY=$(cat secrets/prd/jwt_private.pem) \
  python 2-ml-service/scripts/generate_jwt.py --user-id prod_user
```

### Deploy to production:
```bash
gcloud config configurations activate production
./doit.sh cloud-deploy
```

## Security Notes
- These keys are for PRODUCTION only
- Never commit these files to git (they're in .gitignore)
- Rotate keys periodically with proper versioning
- Keys are also stored in Google Secret Manager for production deployments
- Handle with extra care - this affects live users!