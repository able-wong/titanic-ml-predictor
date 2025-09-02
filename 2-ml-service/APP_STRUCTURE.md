# App Folder Structure - Organized for Developer Discoverability

## 📁 New Structure Overview

```
app/
├── api/                      # API Layer - HTTP/REST interface
│   ├── routes/              # All API endpoints organized by domain
│   │   ├── health.py        # /health endpoint
│   │   ├── predictions.py   # /predict endpoint  
│   │   └── models.py        # /models/info endpoint
│   └── middleware/          # Request/Response middleware
│       ├── auth.py          # JWT authentication & authorization
│       └── rate_limiter.py  # Rate limiting with slowapi
│
├── core/                    # Core Application Components
│   ├── config.py           # Configuration management (YAML loading)
│   ├── exceptions.py       # Custom exceptions & error handling
│   └── logging_config.py   # Structured logging setup
│
├── services/               # Business Logic & Services
│   ├── ml_service.py       # Original ML prediction service
│   ├── lazy_ml_service.py  # Optimized lazy-loading ML service
│   └── health_checker.py   # Health monitoring service
│
├── models/                 # Data Models & Schemas
│   ├── requests.py         # Request validation models (PassengerData)
│   └── responses.py        # Response models (PredictionResponse, etc.)
│
└── utils/                  # Utility Functions
    └── validation.py       # Input sanitization & validation utilities
```

## 🎯 Benefits of This Structure

### 1. **Clear Separation of Concerns**
- **API Layer** (`api/`): Handles HTTP concerns, routing, and middleware
- **Core** (`core/`): Application configuration and cross-cutting concerns
- **Services** (`services/`): Business logic and ML operations
- **Models** (`models/`): Data structures and validation schemas
- **Utils** (`utils/`): Reusable utility functions

### 2. **Easy Discovery**
Developers can immediately find what they're looking for:
- Need to add a new endpoint? → `api/routes/`
- Need to modify authentication? → `api/middleware/auth.py`
- Need to change ML logic? → `services/ml_service.py`
- Need to update data models? → `models/`

### 3. **Import Clarity**
```python
# Clear, hierarchical imports
from app.api.routes import health, predictions
from app.api.middleware.auth import get_current_user
from app.services.ml_service import MLService
from app.core.config import config_manager
from app.models.requests import PassengerData
from app.models.responses import PredictionResponse
from app.utils.validation import validate_passenger_input
```

### 4. **Scalability**
- Easy to add new routes without cluttering
- Services can be extended independently
- Middleware can be added without touching business logic
- Models can be versioned or extended

## 🔄 Migration from Flat Structure

### Before (Flat Structure):
```
app/
├── auth.py
├── config.py
├── exceptions.py
├── health.py
├── lazy_ml_service.py
├── logging_config.py
├── ml_service.py
├── models.py
├── rate_limiter.py
└── validation.py
```

### After (Organized Structure):
- Routes are now in `api/routes/` making API surface clear
- Middleware is grouped in `api/middleware/`
- Core infrastructure in `core/`
- Business logic in `services/`
- Data models split into request/response in `models/`
- Utilities in `utils/`

## 📝 Developer Guidelines

### Adding a New Endpoint:
1. Create a new file in `app/api/routes/`
2. Define your router with FastAPI
3. Import it in `app/api/routes/__init__.py`
4. Include the router in `main.py`

### Adding New Business Logic:
1. Create a service in `app/services/`
2. Keep it focused on business rules, not HTTP concerns
3. Import and use in your routes

### Adding New Models:
1. Request models go in `app/models/requests.py`
2. Response models go in `app/models/responses.py`
3. Shared schemas can go in a new `app/models/schemas.py`

### Adding Middleware:
1. Create in `app/api/middleware/`
2. Import and apply in `main.py`

## 🚀 Performance Considerations

The structure maintains the optimized performance characteristics:
- Lazy loading is preserved in `services/lazy_ml_service.py`
- Fast startup time (~0.17ms) is maintained
- Route organization doesn't impact performance
- Clear separation makes optimization easier to implement

## 🔧 Testing

Test structure mirrors the app structure:
```
tests/
├── unit/
│   ├── test_services/      # Test services
│   ├── test_utils/         # Test utilities
│   └── test_models/        # Test models
└── integration/
    └── test_api/           # Test API endpoints
```

This organized structure makes the codebase more maintainable, discoverable, and scalable while preserving all performance optimizations.