# Coding Assistant Instructions

## Project: Titanic ML Predictor
Production ML system with training pipeline and REST API for survival predictions.

## Architecture
```
1-training/     → Scikit-learn training pipeline → models/
2-ml-service/   → FastAPI service (JWT auth, rate limiting, lazy loading)
shared/         → Common preprocessing utilities
```

## Key Commands
```bash
# Use doit.sh for all operations
./doit.sh train                 # Generate models (required before service start)
./doit.sh python-service-start  # Start API (http://localhost:8000)
./doit.sh python-service-tests  # Run tests (83 tests)
./doit.sh lint-fix             # Fix code style with ruff
./doit.sh python-security-scan  # Security analysis

# GitHub operations - always use gh CLI
gh pr view <PR> --comments      # Pull PR comments
gh pr create --title "..." --body "..."
```

## Testing
```bash
# Generate JWT keys first
source scripts/generate_test_keys.sh
pytest tests/
```

## Important Rules
1. **Never hardcode secrets** - use env vars or config.yaml
2. **Always use gh CLI** for GitHub operations, not git commands for PRs/issues
3. **Run `./doit.sh train`** before starting service
4. **All `/predict` endpoints** require JWT authentication
5. **Use `./doit.sh lint-fix`** before committing