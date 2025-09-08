# Titanic ML Predictor - Remix App

Full-stack Remix application for Titanic survival predictions with Firebase Authentication and ML service integration.

## Overview

This Remix app provides a web interface for the Titanic ML prediction service, featuring:
- Firebase Authentication (Google Sign-in)
- Real-time ML predictions via REST API
- JWT-based API security
- Firebase App Hosting deployment

## Prerequisites

- Node.js 20+
- Firebase CLI: `npm install -g firebase-tools`
- GCP CLI: `gcloud` installed and configured
- Firebase project with billing enabled

## Quick Start

```bash
# Install dependencies
npm install

# Development with staging environment
npm run dev:stg

# Development with production environment  
npm run dev:prd
```

## Firebase App Hosting Deployment

### Initial Setup

1. **Create Firebase Projects:**
   - Create staging project: `titanic-ml-predictor-stg`
   - Create production project: `titanic-ml-predictor-prd`

2. **Initialize App Hosting:**
   ```bash
   firebase init apphosting
   ```

3. **Configure Secrets in GCP:**
   ```bash
   # Create Firebase config secret (staging)
   echo '{"projectId":"titanic-ml-predictor-stg","appId":"...","apiKey":"..."}' | \
     gcloud secrets create firebase-config-stg --data-file=- --project=titanic-ml-predictor-stg
   
   # Create JWT private key secret
   echo 'your-jwt-private-key' | \
     gcloud secrets create jwt-private-key --data-file=- --project=titanic-ml-predictor-stg
   ```

4. **Grant App Hosting Access to Secrets:**
   ```bash
   # List backends
   firebase apphosting:backends:list --project=titanic-ml-predictor-stg
   
   # Grant access (replace 'app' with your backend ID)
   firebase apphosting:secrets:grantaccess firebase-config-stg --backend=app --project=titanic-ml-predictor-stg
   firebase apphosting:secrets:grantaccess jwt-private-key --backend=app --project=titanic-ml-predictor-stg
   ```

### apphosting.yaml Configuration

**Important:** Firebase App Hosting uses a single `env:` section. Secrets are referenced with `secret:` instead of `value:`.

```yaml
runConfig:
  cpu: 1
  memoryMiB: 512
  maxInstances: 4
  minInstances: 0
  concurrency: 5

env:
  # Regular environment variables
  - variable: FIREBASE_PROJECT_ID
    value: titanic-ml-predictor-stg
    availability:
      - BUILD
      - RUNTIME
      
  # Secret references (NOT in a separate secrets section)
  - variable: FIREBASE_CONFIG
    secret: firebase-config-stg  # References GCP secret
    availability:
      - BUILD
      - RUNTIME
      
  - variable: JWT_PRIVATE_KEY
    secret: jwt-private-key
    availability:
      - BUILD
      - RUNTIME
```

### Deployment

```bash
# Deploy to staging
firebase deploy --only apphosting --project=titanic-ml-predictor-stg

# Deploy to production
firebase deploy --only apphosting --project=titanic-ml-predictor-prd
```

## Environment Configuration

### Local Development (.env files)

Create `.env.stg` and `.env.prd` files:

```bash
# Firebase Configuration
FIREBASE_CONFIG={"projectId":"...","apiKey":"...","authDomain":"..."}

# ML Service
ML_SERVICE_URL=https://titanic-ml-service-stg-411470717307.us-central1.run.app

# JWT Configuration
JWT_PRIVATE_KEY=your-private-key
JWT_TTL=5m
```

### Production Secrets (GCP Secret Manager)

All sensitive data should be stored in GCP Secret Manager:
- `firebase-config-stg` / `firebase-config-prd` - Firebase configuration JSON
- `jwt-private-key` - JWT signing key

## Useful Commands

### Firebase App Hosting

```bash
# Backend Management
firebase apphosting:backends:list --project=PROJECT_ID
firebase apphosting:backends:get BACKEND_ID --project=PROJECT_ID

# Secret Access Management
firebase apphosting:secrets:grantaccess SECRET_NAME --backend=BACKEND_ID --project=PROJECT_ID
firebase apphosting:secrets:describe SECRET_NAME --project=PROJECT_ID

# Deployment History
firebase apphosting:rollouts:list --backend=BACKEND_ID --project=PROJECT_ID
```

### GCP Secret Manager

```bash
# List all secrets
gcloud secrets list --project=PROJECT_ID

# View secret value
gcloud secrets versions access latest --secret=SECRET_NAME --project=PROJECT_ID

# Update secret
echo 'new-value' | gcloud secrets versions add SECRET_NAME --data-file=- --project=PROJECT_ID

# Delete secret
gcloud secrets delete SECRET_NAME --project=PROJECT_ID
```

### Debugging

```bash
# View App Hosting logs
gcloud app logs tail --project=PROJECT_ID

# Check secret permissions
gcloud secrets get-iam-policy SECRET_NAME --project=PROJECT_ID

# Test Firebase configuration
firebase apps:sdkconfig web APP_ID --project=PROJECT_ID
```

## Troubleshooting

### Common Issues

1. **"Permission denied" for secrets:**
   - Run `firebase apphosting:secrets:grantaccess` for each secret
   - Verify with `gcloud secrets get-iam-policy SECRET_NAME`

2. **Environment variables not available:**
   - Ensure variables are in single `env:` section (not separate `secrets:` section)
   - Check `availability` includes `RUNTIME` for runtime variables

3. **Firebase Auth initialization fails:**
   - Verify `FIREBASE_CONFIG` secret contains complete JSON with `apiKey`
   - Check App Hosting has access to the secret

4. **Build failures:**
   - Review App Hosting logs: `gcloud app logs tail`
   - Verify all secrets exist: `gcloud secrets list`

## Project Structure

```
app/
├── routes/          # Remix routes
├── services/        # Business logic
├── components/      # React components
├── contexts/        # React contexts (Auth)
├── utils/          # Utilities
└── interfaces/     # TypeScript interfaces

apphosting.stg.yaml  # Staging App Hosting config
apphosting.prd.yaml  # Production App Hosting config
```

## Related Documentation

- [Firebase App Hosting](https://firebase.google.com/docs/app-hosting)
- [Remix Documentation](https://remix.run/docs)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)