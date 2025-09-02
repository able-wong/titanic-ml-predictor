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
- Virtual environment (recommended)

### Setup
```bash
# Clone repository
git clone https://github.com/able-wong/titanic-ml-predictor.git
cd titanic-ml-predictor

# Install dependencies (consolidated requirements)
pip install -r requirements.txt

# Train models
./doit.sh train

# Start API service
./doit.sh python-service-start
```

## 🛠️ Development Commands (`doit.sh`)

The `doit.sh` script provides convenient automation for common development tasks:

```bash
# Training & Models
./doit.sh train                    # Train ML models using pipeline
./doit.sh clean                    # Clean generated files and caches

# Code Quality
./doit.sh lint                     # Run ruff linting
./doit.sh lint-fix                # Auto-fix linting issues  

# Testing & Service
./doit.sh python-service-tests     # Run comprehensive test suite
./doit.sh python-service-start     # Start FastAPI development server

# Setup
./doit.sh install-deps             # Install all project dependencies
./doit.sh help                     # Show available commands
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