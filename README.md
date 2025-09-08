# Titanic ML Predictor

A production-ready machine learning system for predicting Titanic passenger survival, built with modern MLOps practices and FastAPI.

## 🎯 Overview

This project demonstrates a complete ML lifecycle from data preprocessing to production deployment:

- **Educational ML Pipeline**: Original single-script implementation showing core ML concepts
- **Shared Components**: Reusable preprocessing logic across training and inference
- **Production API**: High-performance FastAPI service with authentication, rate limiting, and monitoring
- **Automated CI/CD**: Comprehensive testing and quality assurance pipeline

## 📁 Project Structure

```
titanic-ml-predictor/
├── 📄 titanic_ml.py           # Original educational ML script (single file)
├── 📄 doit.sh                 # Development automation script
├── 📄 requirements.txt        # Consolidated Python dependencies
├── 📄 README.md              # This file - project overview
│
├── 🧠 1-training/            # ML model training pipeline  
│   ├── train.py              # Training script using shared preprocessor
│   └── README.md             # Training pipeline documentation
│
├── 🔧 shared/               # Reusable components
│   ├── __init__.py
│   └── preprocessor.py       # Shared data preprocessing logic
│
├── 🚀 2-ml-service/         # Production FastAPI service
│   ├── app/                  # FastAPI application
│   │   ├── api/             # API routes and middleware
│   │   ├── core/            # Configuration and exceptions
│   │   ├── services/        # ML service and health checks
│   │   └── utils/           # Validation and utilities
│   ├── tests/               # Comprehensive test suite
│   ├── main.py              # FastAPI application entry point
│   ├── config.example.yaml  # Configuration template
│   └── README.md            # Service-specific documentation
│
├── 📊 data/                 # Training data (CSV files)
│   ├── titanic passenger list.csv
│   └── Titanic-Dataset.csv
│
├── 🤖 models/              # Generated ML artifacts (from training)
│   ├── *.pkl               # Trained model files
│   └── *.json              # Model metadata and stats
│
└── 🔄 .github/workflows/   # CI/CD automation
    └── ci.yml              # GitHub Actions pipeline
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- Git
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (for deployment)
- [GitHub CLI](https://cli.github.com/) (for repository management)
- Virtual environment (recommended)

### Initial Setup

After cloning the repository, follow these steps to get the project fully operational:

#### 1. Basic Development Setup
```bash
# Clone repository
git clone https://github.com/able-wong/titanic-ml-predictor.git
cd titanic-ml-predictor

# Install dependencies (consolidated requirements)
pip install -r requirements.txt

# Train models (required before starting service)
./doit.sh train
```

#### 2. JWT Authentication Setup (Local Development)
Generate JWT keys for all environments (dev/staging/production):

```bash
# Generate keys for all environments (one-time setup)
./doit.sh generate-secrets

# Export dev keys to your shell session (needed each time)
eval "$(./doit.sh export-dev-secrets)"

# Start API service with JWT authentication
./doit.sh python-service-start

# Test the service (public endpoint)
curl http://localhost:8000/health

# Generate a JWT token for testing authenticated endpoints
python 2-ml-service/scripts/generate_jwt.py --user-id test_user

# Test authenticated endpoint (use the token from above)
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"pclass": 1, "sex": "female", "age": 29, "sibsp": 0, "parch": 0, "fare": 100, "embarked": "S"}' \
  http://localhost:8000/predict
```

**Benefits of this approach:**
- **Consistent keys** across development sessions
- **Same keys** used for staging/production (in separate environments)
- **No regeneration** needed between restarts

#### 3. Google Cloud Platform Setup (Production Deployment)

To deploy to Google Cloud Run, set up your GCP environment:

```bash
# 1. Initialize gcloud CLI and authenticate
gcloud init
gcloud auth login
gcloud auth application-default login

# 2. Create staging and production projects
gcloud projects create titanic-ml-predictor-stg --name="Titanic ML Staging"
gcloud projects create titanic-ml-predictor-prd --name="Titanic ML Production"

# 3. Enable billing and APIs for both projects
# (Follow GCP console prompts for billing)

# 4. Set up GCP services and artifact registry
./doit.sh env-switch staging
./doit.sh gcp-setup

./doit.sh env-switch prd
./doit.sh gcp-setup

# 5. Upload JWT secrets to both environments
./doit.sh env-switch staging
./doit.sh setup-secrets

./doit.sh env-switch prd  
./doit.sh setup-secrets
```

#### 4. Manual Deployment (Optional)
Test manual deployment before setting up CI/CD:

```bash
# Deploy to staging
./doit.sh env-switch staging
./doit.sh cloud-build
./doit.sh cloud-deploy

# Deploy to production  
./doit.sh env-switch prd
./doit.sh cloud-build
./doit.sh cloud-deploy
```

#### 5. GitHub Actions CI/CD Setup
For automated deployments via GitHub Actions:

```bash
# 1. Create service accounts and keys for both environments
./doit.sh github-actions-setup

# 2. Add GitHub repository secrets:
#    - Go to GitHub repo → Settings → Secrets and variables → Actions
#    - Add these secrets:
#      * GCP_SA_KEY_STG: Contents of github-actions-stg-key.json
#      * GCP_SA_KEY_PRD: Contents of github-actions-prd-key.json

# 3. Clean up local key files
rm github-actions-stg-key.json github-actions-prd-key.json

# 4. Create production branch for controlled releases
git checkout -b prd
git push -u origin prd
```

#### 6. CI/CD Workflow
Once setup is complete, the deployment workflow is:

- **Push to `main`** → Automatically deploys to **staging**
- **Push to `prd`** → Automatically deploys to **production**
- **Pull Requests** → Run full test suite without deployment

### Verification
After setup, verify everything works:

```bash
# Local development
./doit.sh python-service-tests  # All tests pass
./doit.sh python-service-start  # Service starts correctly

# Cloud deployment
./doit.sh cloud-status         # Shows service status and URL
curl $(./doit.sh cloud-status | grep "URL:" | awk '{print $2}')/health  # Health check responds
```

Your deployed services will be available at URLs like:
- **Staging**: `https://titanic-ml-service-<random-id>.us-central1.run.app`
- **Production**: `https://titanic-ml-service-<random-id>.us-central1.run.app`

## 🛠️ Development Commands (`doit.sh`)

The `doit.sh` script provides convenient automation for common development tasks:

```bash
# Training & Models
./doit.sh train                    # Train ML models using pipeline
./doit.sh clean                    # Clean generated files and caches

# Code Quality
./doit.sh lint                     # Run ruff linting
./doit.sh lint-fix                 # Auto-fix linting issues
./doit.sh python-security-scan     # Run security analysis with bandit

# Testing & Service
./doit.sh python-service-tests     # Run comprehensive test suite
./doit.sh python-service-start     # Start FastAPI development server

# Cloud Deployment
./doit.sh env-switch <staging|prd> # Switch between environments
./doit.sh gcp-setup                # Configure GCP services and registry
./doit.sh setup-secrets            # Upload JWT keys to Secret Manager
./doit.sh github-actions-setup     # Create CI/CD service accounts
./doit.sh cloud-build [tag]        # Build and push Docker image
./doit.sh cloud-deploy [tag]       # Deploy to Cloud Run
./doit.sh cloud-status             # Check service status and health

# Setup & Utilities
./doit.sh install-deps             # Install all project dependencies
./doit.sh help                     # Show all available commands
```

## 📊 Components

### 1. Educational Reference (`titanic_ml.py`)
- **Purpose**: Single-file ML implementation for learning
- **Features**: Complete pipeline from data loading to evaluation
- **Usage**: `python titanic_ml.py`

### 2. Training Pipeline (`1-training/`)
- **Purpose**: Reproducible model training with shared components
- **Features**: Uses shared preprocessor, generates models for API service
- **Usage**: `./doit.sh train` or `cd 1-training && python train.py`

### 3. Production API Service (`2-ml-service/`)
- **Purpose**: High-performance FastAPI service for real-time predictions
- **Features**: 
  - JWT authentication with RS256
  - Configurable rate limiting (memory/Redis)
  - Input validation and security
  - Comprehensive health monitoring
  - Structured logging and request tracing
  - Lazy loading for optimal cold start performance
- **Usage**: `./doit.sh python-service-start`
- **Documentation**: See [2-ml-service/README.md](2-ml-service/README.md)

### 4. Shared Components (`shared/`)
- **Purpose**: Reusable preprocessing logic
- **Features**: Consistent data transformation across training and inference
- **Components**: `TitanicPreprocessor` class with feature engineering

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Component-level testing with mocking
- **Integration Tests**: End-to-end API testing
- **Security Tests**: Input validation and injection prevention
- **Performance Tests**: Health monitoring and resource checks

### Running Tests
```bash
# All tests
./doit.sh python-service-tests

# Specific test types
cd 2-ml-service
python -m pytest tests/unit/      # Unit tests only
python -m pytest tests/integration/  # Integration tests only
python -m pytest tests/ --cov=app    # With coverage report
```

For detailed testing documentation, see [2-ml-service/tests/README.md](2-ml-service/tests/README.md).

## 🔧 Configuration

### Environment Configuration
The API service uses YAML configuration with environment variable overrides:

```bash
# Copy and customize configuration
cp 2-ml-service/config.example.yaml 2-ml-service/config.yaml

# Key environment variables
export ML_SERVICE_HOST="0.0.0.0"
export ML_SERVICE_PORT="8000"
export JWT_PRIVATE_KEY="your-private-key"
export RATE_LIMITING_BACKEND="memory"  # or "redis"
```

### Rate Limiting
- **Memory**: Default, no external dependencies
- **Redis**: Distributed rate limiting across instances
- **Configuration**: Separate limits for predictions, health checks, auth

## 🚦 CI/CD Pipeline

Automated GitHub Actions workflow provides:

- **Multi-Python Testing**: Python 3.11 and 3.12 matrix
- **Code Quality**: Ruff linting and formatting validation
- **Security Scanning**: Safety (vulnerabilities) and Bandit (security)
- **Complete Testing**: Unit, integration, and coverage reporting
- **Build Validation**: Service startup and configuration checks

## 📈 Performance

### API Service Performance
| Metric | Value | Description |
|--------|--------|-------------|
| **Cold Start** | ~0.17ms | Ultra-fast startup with lazy loading |
| **First Prediction** | ~1-2s | Models load on first request |
| **Warm Predictions** | ~50-100ms | Cached model performance |
| **Memory Usage** | Efficient | Lazy loading minimizes peak usage |

### Key Optimizations
- **Lazy Loading**: Models load only when needed
- **Request Caching**: Efficient model reuse
- **Structured Logging**: Minimal performance impact
- **Configurable Backends**: Memory vs Redis rate limiting

## 🛡️ Security Features

- **JWT Authentication**: RS256 with configurable expiration
- **Input Validation**: XSS and SQL injection prevention
- **Rate Limiting**: Configurable per-endpoint limits
- **Security Headers**: CORS and request ID middleware
- **Audit Logging**: Structured security event tracking

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Run** tests and linting (`./doit.sh lint && ./doit.sh python-service-tests`)
4. **Commit** changes (`git commit -m 'Add amazing feature'`)
5. **Push** to branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Development Guidelines
- Follow existing code patterns and conventions
- Write tests for new functionality
- Run `./doit.sh lint-fix` before committing
- Update documentation as needed

## 📋 Dependencies

All dependencies are consolidated in the project root `requirements.txt`:

- **FastAPI**: Modern, fast API framework
- **Scikit-learn**: Machine learning models
- **PyJWT + Cryptography**: JWT authentication
- **Slowapi + Redis**: Rate limiting
- **Structlog**: Structured logging
- **Psutil**: System resource monitoring
- **Pytest**: Comprehensive testing framework

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **API Documentation**: http://localhost:8000/docs (when service running)
- **Service Details**: [2-ml-service/README.md](2-ml-service/README.md)
- **Test Documentation**: [2-ml-service/tests/README.md](2-ml-service/tests/README.md)
- **GitHub Repository**: https://github.com/able-wong/titanic-ml-predictor