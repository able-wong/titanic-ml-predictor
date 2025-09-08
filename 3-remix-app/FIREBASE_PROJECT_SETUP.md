# Firebase Project Setup Guide

## Prerequisites
- Firebase CLI installed (`npm install -g firebase-tools`)
- Access to GCP projects: `titanic-ml-predictor-stg` and `titanic-ml-predictor-prd`

## Step 1: Enable Firebase on Your GCP Projects

### For Staging Environment (titanic-ml-predictor-stg)

1. **Login to Firebase CLI:**
```bash
firebase login
```

2. **Add Firebase to your existing GCP project:**
```bash
firebase projects:addfirebase titanic-ml-predictor-stg
```

3. **Create a Web App in Firebase:**
```bash
firebase apps:create WEB "Titanic ML Predictor Web - Staging" --project titanic-ml-predictor-stg
```

4. **Get the Firebase configuration:**
```bash
firebase apps:sdkconfig WEB --project titanic-ml-predictor-stg
```

This will output something like:
```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "titanic-ml-predictor-stg.firebaseapp.com",
  projectId: "titanic-ml-predictor-stg",
  storageBucket: "titanic-ml-predictor-stg.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

5. **Enable Authentication:**
```bash
# Open Firebase Console
open https://console.firebase.google.com/project/titanic-ml-predictor-stg/authentication

# Or use gcloud to enable the service
gcloud services enable identitytoolkit.googleapis.com --project=titanic-ml-predictor-stg
```

In the Firebase Console:
- Go to Authentication > Sign-in method
- Enable "Google" provider
- Add your domain to Authorized domains if needed

## Step 2: Create Service Account for Server-Side Operations

```bash
# Create service account
gcloud iam service-accounts create firebase-admin \
  --display-name="Firebase Admin SDK" \
  --project=titanic-ml-predictor-stg

# Download service account key
gcloud iam service-accounts keys create firebase-service-account-stg.json \
  --iam-account=firebase-admin@titanic-ml-predictor-stg.iam.gserviceaccount.com \
  --project=titanic-ml-predictor-stg
```

## Step 3: Set Up Environment Variables

Create `.env` file in the `3-remix-app` directory:

```bash
# Copy the example
cp .env.example .env
```

Then fill in the values from the Firebase configuration you obtained above.

## Step 4: For Production Environment

Repeat the same steps with `titanic-ml-predictor-prd`:

```bash
# Add Firebase to production project
firebase projects:addfirebase titanic-ml-predictor-prd

# Create Web App
firebase apps:create WEB "Titanic ML Predictor Web - Production" --project titanic-ml-predictor-prd

# Get configuration
firebase apps:sdkconfig WEB --project titanic-ml-predictor-prd

# Enable Authentication
gcloud services enable identitytoolkit.googleapis.com --project=titanic-ml-predictor-prd

# Create service account
gcloud iam service-accounts create firebase-admin \
  --display-name="Firebase Admin SDK" \
  --project=titanic-ml-predictor-prd

# Download service account key
gcloud iam service-accounts keys create firebase-service-account-prd.json \
  --iam-account=firebase-admin@titanic-ml-predictor-prd.iam.gserviceaccount.com \
  --project=titanic-ml-predictor-prd
```

## Step 5: Initialize Firebase in the Project

```bash
cd 3-remix-app
firebase init
```

Select:
- Hosting (for Firebase App Hosting)
- Use existing project: titanic-ml-predictor-stg
- Public directory: build/client
- Configure as single-page app: No
- Set up automatic builds: No

## Project Aliases

Edit `.firebaserc`:
```json
{
  "projects": {
    "default": "titanic-ml-predictor-stg",
    "staging": "titanic-ml-predictor-stg",
    "production": "titanic-ml-predictor-prd"
  }
}
```

## Security Notes

1. **Never commit `.env` files or service account JSON files to git**
2. Store service account keys securely
3. Use different Firebase projects for staging and production
4. Restrict API keys in GCP Console if needed

## Quick Setup Script

Run this after obtaining your Firebase config:
```bash
./scripts/setup-firebase-env.sh
```