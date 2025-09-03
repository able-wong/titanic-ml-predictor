#!/bin/bash

# doit.sh - Development automation script for Titanic ML Project
# 
# This script provides convenient commands for common development tasks
# across the training pipeline and ML service components.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

# Command implementations
cmd_help() {
    cat << EOF
🚀 Titanic ML Project - Development Commands

Usage: ./doit.sh <command> [options]

Available Commands:
  train                    Train the ML models using the training pipeline
  lint                     Run ruff linting and formatting checks on all Python code
  lint-fix                 Run ruff with --fix and apply formatting to automatically fix issues
  python-security-scan     Run security vulnerability scan on Python code
  python-service-tests     Run the comprehensive test suite for the ML service
  python-service-start     Start the FastAPI ML service
  docker-build             Build Docker container for the ML service
  docker-start             Start Docker container for the ML service
  env-switch               Switch between staging/production environments
  setup-secrets            Upload JWT keys to Google Secret Manager
  gcp-setup                Configure Google Cloud Platform for Cloud Run deployment
  cloud-build [tag]        Build Docker image locally and push to Artifact Registry
  cloud-deploy [tag]       Deploy ML service from Artifact Registry
  update-service-secrets   Update Cloud Run to use latest secrets
  cloud-logs               View Cloud Run service logs
  cloud-status             Check Cloud Run service status and information
  install-deps             Install all dependencies for training and service
  clean                    Clean up generated files and caches
  help                     Show this help message

Examples:
  # Local development
  ./doit.sh train
  ./doit.sh python-service-tests unit
  ./doit.sh lint-fix
  ./doit.sh python-service-start
  
  # Cloud deployment workflow
  ./doit.sh env-switch staging
  ./doit.sh setup-secrets
  ./doit.sh cloud-build v1.0.0
  ./doit.sh cloud-deploy v1.0.0
  
  # Update secrets without redeploying
  ./doit.sh setup-secrets
  ./doit.sh update-service-secrets

EOF
}

cmd_train() {
    print_header "Training ML Models"
    print_info "Running training pipeline..."
    
    cd "$PROJECT_ROOT/1-training"
    python train.py "$@"
    
    if [ $? -eq 0 ]; then
        print_success "Model training completed successfully"
    else
        print_error "Model training failed"
        exit 1
    fi
}

cmd_lint() {
    print_header "Running Code Linting"
    print_info "Checking code with ruff..."
    
    cd "$PROJECT_ROOT"
    
    # Check if ruff is installed
    if ! command -v ruff &> /dev/null; then
        print_error "ruff is not installed. Run './doit.sh install-deps' first."
        exit 1
    fi
    
    # Run linting checks
    ruff check 1-training/ 2-ml-service/ shared/ "$@"
    lint_exit_code=$?
    
    # Run formatting checks
    print_info "Checking code formatting with ruff..."
    ruff format --check 1-training/ 2-ml-service/ shared/ "$@"
    format_exit_code=$?
    
    if [ $lint_exit_code -eq 0 ] && [ $format_exit_code -eq 0 ]; then
        print_success "Code linting and formatting checks passed"
    else
        print_error "Code linting or formatting checks found issues"
        exit 1
    fi
}

cmd_lint_fix() {
    print_header "Running Code Linting with Auto-fix"
    print_info "Fixing code issues with ruff..."
    
    cd "$PROJECT_ROOT"
    
    # Check if ruff is installed
    if ! command -v ruff &> /dev/null; then
        print_error "ruff is not installed. Run './doit.sh install-deps' first."
        exit 1
    fi
    
    # Fix linting issues
    ruff check --fix 1-training/ 2-ml-service/ shared/ "$@"
    lint_exit_code=$?
    
    # Apply code formatting
    print_info "Applying code formatting with ruff..."
    ruff format 1-training/ 2-ml-service/ shared/ "$@"
    format_exit_code=$?
    
    if [ $lint_exit_code -eq 0 ] && [ $format_exit_code -eq 0 ]; then
        print_success "Code linting fixes and formatting completed"
    else
        print_error "Code linting fixes or formatting failed"
        exit 1
    fi
}

cmd_python_security_scan() {
    print_header "Running Python Security Scan"
    print_info "Scanning Python code for security vulnerabilities..."
    
    cd "$PROJECT_ROOT"
    
    # Check if bandit is installed
    if ! command -v bandit &> /dev/null; then
        print_info "Installing bandit security scanner..."
        pip install bandit
    fi
    
    # Run safety check for known vulnerabilities in dependencies
    print_info "Checking dependencies for known vulnerabilities with safety..."
    if command -v safety &> /dev/null; then
        safety check --json || print_warning "Some dependency vulnerabilities found"
    else
        print_info "Installing safety scanner..."
        pip install safety
        safety check --json || print_warning "Some dependency vulnerabilities found"
    fi
    
    # Run bandit security linter on Python code
    print_info "Running bandit security analysis on Python code..."
    
    bandit_exit_code=0
    bandit -r 1-training/ 2-ml-service/ shared/ -f json > bandit_report.json || bandit_exit_code=$?
    
    if [ $bandit_exit_code -eq 0 ]; then
        print_success "No security issues found in Python code"
    else
        print_warning "Security issues found - check bandit_report.json for details"
        # Show summary but don't fail the build
        if command -v jq &> /dev/null; then
            echo ""
            print_info "Security Issues Summary:"
            jq -r '.results[] | "⚠️  \(.filename):\(.line_number) - \(.issue_text)"' bandit_report.json || true
        fi
    fi
    
    print_success "Python security scan completed"
}

cmd_python_service_tests() {
    print_header "Running ML Service Tests"
    print_info "Running test suite..."
    
    cd "$PROJECT_ROOT/2-ml-service"
    python run_tests.py "${1:-all}"
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

cmd_python_service_start() {
    print_header "Starting ML Service"
    print_info "Starting FastAPI ML service..."
    
    cd "$PROJECT_ROOT/2-ml-service"
    python main.py "$@"
}

cmd_docker_build() {
    print_header "Building Docker Container"
    print_info "Building Docker image for ML service..."
    
    cd "$PROJECT_ROOT"
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in project root"
        exit 1
    fi
    
    # Build the Docker image
    docker build -t titanic-ml-service:latest .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully: titanic-ml-service:latest"
    else
        print_error "Docker build failed"
        exit 1
    fi
}

cmd_docker_start() {
    print_header "Starting Docker Container"
    print_info "Starting Docker container for ML service..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing container if running
    if docker ps -aq -f name=titanic-ml-service | grep -q .; then
        print_info "Stopping existing container..."
        docker stop titanic-ml-service 2>/dev/null || true
        docker rm titanic-ml-service 2>/dev/null || true
    fi
    
    # Start new container
    print_info "Starting container on port 8000..."
    docker run -d \
        --name titanic-ml-service \
        -p 8000:8080 \
        -e ML_SERVICE_ENVIRONMENT=production \
        -e PORT=8080 \
        titanic-ml-service:latest
    
    if [ $? -eq 0 ]; then
        print_success "Docker container started successfully"
        print_info "Service available at: http://localhost:8000"
        print_info "API documentation at: http://localhost:8000/docs"
        print_info ""
        print_info "Container management commands:"
        print_info "  docker logs titanic-ml-service     - View logs"
        print_info "  docker stop titanic-ml-service     - Stop container"
        print_info "  docker rm titanic-ml-service       - Remove container"
    else
        print_error "Failed to start Docker container"
        exit 1
    fi
}

cmd_install_deps() {
    print_header "Installing Dependencies"
    
    cd "$PROJECT_ROOT"
    
    # Install all dependencies from consolidated requirements.txt
    print_info "Installing project dependencies from consolidated requirements.txt..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Project dependencies installed"
    else
        print_error "No requirements.txt found in project root"
        exit 1
    fi
    
    # Install development tools (ruff is now included in requirements.txt as optional)
    print_info "Installing additional development tools..."
    pip install ruff
    print_success "Development tools installed"
    
    print_success "All dependencies installed successfully"
}

cmd_env_switch() {
    print_header "Switch Environment"
    
    if [ $# -eq 0 ]; then
        # Show current environment and available options
        CURRENT_CONFIG=$(gcloud config configurations list --filter="is_active=true" --format="value(name)")
        CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
        
        print_info "Current configuration: $CURRENT_CONFIG"
        print_info "Current project: $CURRENT_PROJECT"
        print_info ""
        print_info "Available environments:"
        print_info "  staging    - Switch to staging environment (titanic-ml-predictor-stg)"
        print_info "  production - Switch to production environment (titanic-ml-predictor-prd)"
        print_info ""
        print_info "Usage: ./doit.sh env-switch [staging|production]"
        return 0
    fi
    
    ENV=$1
    case "$ENV" in
        "staging"|"stg")
            print_info "Switching to STAGING environment..."
            gcloud config configurations activate staging
            print_success "✅ Switched to staging (titanic-ml-predictor-stg)"
            ;;
        "production"|"prod"|"prd")
            print_warning "Switching to PRODUCTION environment..."
            gcloud config configurations activate production
            print_warning "⚠️  Switched to production (titanic-ml-predictor-prd) - Handle with care!"
            ;;
        *)
            print_error "Unknown environment: $ENV"
            print_info "Use: staging or production"
            exit 1
            ;;
    esac
    
    # Show current settings
    print_info ""
    print_info "Active configuration:"
    gcloud config list --format="table(core.account,core.project,run.region)"
}

cmd_setup_secrets() {
    print_header "Setup Secrets in Secret Manager"
    print_info "Uploading JWT keys to Google Secret Manager..."
    
    cd "$PROJECT_ROOT"
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured. Use './doit.sh env-switch' first."
        exit 1
    fi
    
    # Determine environment and key directory
    ENV=""
    KEY_DIR=""
    if [[ "$PROJECT_ID" == *"-stg" ]]; then
        ENV="staging"
        KEY_DIR="secrets/stg"
        print_info "🔧 Environment: STAGING"
    elif [[ "$PROJECT_ID" == *"-prd" ]]; then
        ENV="production"
        KEY_DIR="secrets/prd"
        print_warning "⚠️  Environment: PRODUCTION"
    else
        print_error "Unknown project type. Expected -stg or -prd suffix."
        exit 1
    fi
    
    # Check if JWT keys exist
    if [ ! -f "$KEY_DIR/jwt_private.pem" ] || [ ! -f "$KEY_DIR/jwt_public.pem" ]; then
        print_error "JWT keys not found in $KEY_DIR"
        print_info "Generate keys first or check the secrets directory"
        exit 1
    fi
    
    print_info "Using keys from: $KEY_DIR"
    
    # Create or update JWT private key secret
    print_info "Uploading JWT private key..."
    if gcloud secrets describe jwt-private-key --project=$PROJECT_ID >/dev/null 2>&1; then
        print_info "Secret 'jwt-private-key' exists, adding new version..."
        gcloud secrets versions add jwt-private-key \
            --data-file=$KEY_DIR/jwt_private.pem \
            --project=$PROJECT_ID
    else
        print_info "Creating secret 'jwt-private-key'..."
        gcloud secrets create jwt-private-key \
            --data-file=$KEY_DIR/jwt_private.pem \
            --replication-policy=automatic \
            --project=$PROJECT_ID
    fi
    
    # Create or update JWT public key secret
    print_info "Uploading JWT public key..."
    if gcloud secrets describe jwt-public-key --project=$PROJECT_ID >/dev/null 2>&1; then
        print_info "Secret 'jwt-public-key' exists, adding new version..."
        gcloud secrets versions add jwt-public-key \
            --data-file=$KEY_DIR/jwt_public.pem \
            --project=$PROJECT_ID
    else
        print_info "Creating secret 'jwt-public-key'..."
        gcloud secrets create jwt-public-key \
            --data-file=$KEY_DIR/jwt_public.pem \
            --replication-policy=automatic \
            --project=$PROJECT_ID
    fi
    
    # Grant Secret Manager access to Cloud Run service account
    print_info "Granting Secret Manager access to Cloud Run..."
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    
    gcloud secrets add-iam-policy-binding jwt-private-key \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID --quiet
    
    gcloud secrets add-iam-policy-binding jwt-public-key \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID --quiet
    
    print_success "✅ Secrets uploaded to Secret Manager successfully"
    print_info ""
    print_info "Secrets created/updated:"
    print_info "  - jwt-private-key"
    print_info "  - jwt-public-key"
    print_info ""
    print_info "Next step: Deploy with './doit.sh cloud-deploy'"
}

cmd_gcp_setup() {
    print_header "Setting up Google Cloud Platform"
    print_info "Configuring GCP services for Cloud Run deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured. Run 'gcloud config set project YOUR_PROJECT_ID' first."
        exit 1
    fi
    
    print_info "Using GCP project: $PROJECT_ID"
    
    # Enable required APIs
    print_info "Enabling Cloud Build and Cloud Run APIs..."
    gcloud services enable cloudbuild.googleapis.com --quiet
    gcloud services enable run.googleapis.com --quiet
    gcloud services enable artifactregistry.googleapis.com --quiet
    gcloud services enable secretmanager.googleapis.com --quiet
    
    # Get current region
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    if [ -z "$REGION" ]; then
        REGION="us-central1"
        print_info "No region configured. Using default: $REGION"
        gcloud config set run/region $REGION
    fi
    
    # Create Artifact Registry repository if it doesn't exist
    print_info "Creating Artifact Registry repository..."
    gcloud artifacts repositories create titanic \
        --repository-format=docker \
        --location=$REGION \
        --description="Titanic ML Service container images" \
        --quiet 2>/dev/null || print_info "Repository 'titanic' already exists"
    
    # Configure Docker authentication
    print_info "Configuring Docker authentication for Artifact Registry..."
    gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
    
    if [ $? -eq 0 ]; then
        print_success "GCP setup completed successfully"
        print_info "Project: $PROJECT_ID"
        print_info "Region: $REGION" 
        print_info "Artifact Registry: $REGION-docker.pkg.dev/$PROJECT_ID/titanic"
    else
        print_error "GCP setup failed"
        exit 1
    fi
}

cmd_cloud_build() {
    print_header "Building Docker Image"
    print_info "Building and pushing Docker image to Artifact Registry..."
    
    cd "$PROJECT_ROOT"
    
    # Get current project and region
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured. Use './doit.sh env-switch' first."
        exit 1
    fi
    
    if [ -z "$REGION" ]; then
        REGION="us-central1"
    fi
    
    # Determine environment
    ENV=""
    if [[ "$PROJECT_ID" == *"-stg" ]]; then
        ENV="staging"
        print_info "🔧 Environment: STAGING"
    elif [[ "$PROJECT_ID" == *"-prd" ]]; then
        ENV="production"
        print_warning "⚠️  Environment: PRODUCTION"
        
        # Production safety checks
        CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
        if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "prd" ] && [ "$CURRENT_BRANCH" != "prod" ] && [ "$CURRENT_BRANCH" != "production" ]; then
            print_error "Production builds must be from main or prd branch"
            print_info "Current branch: $CURRENT_BRANCH"
            print_info "Switch to main branch: git checkout main"
            exit 1
        fi
        
        # Check for uncommitted changes
        if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
            print_error "Uncommitted changes detected"
            print_info "Production builds require a clean working directory"
            print_info "Commit or stash your changes first:"
            print_info "  git add . && git commit -m 'message'"
            print_info "  or: git stash"
            exit 1
        fi
        
        print_success "✅ Production safety checks passed"
        print_info "Branch: $CURRENT_BRANCH"
    fi
    
    # Parse arguments more robustly
    TAG=""
    BUILD_METHOD="local"  # default to local build
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --cloud)
                BUILD_METHOD="cloud"
                ;;
            --local)
                BUILD_METHOD="local"
                ;;
            --*)
                print_warning "Unknown flag: $1"
                ;;
            *)
                if [ -z "$TAG" ]; then
                    TAG="$1"
                else
                    print_warning "Ignoring extra argument: $1"
                fi
                ;;
        esac
        shift
    done
    
    # Generate default tag if none provided
    if [ -z "$TAG" ]; then
        # Use first 10 chars of git commit hash as default tag
        FULL_SHA=$(git rev-parse HEAD 2>/dev/null)
        if [ -n "$FULL_SHA" ]; then
            TAG="${FULL_SHA:0:10}"
        else
            TAG="latest"
            print_warning "Not a git repository, using 'latest' as tag"
        fi
    fi
    
    # Build image URL
    IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/titanic/ml-service:$TAG"
    LATEST_URL="$REGION-docker.pkg.dev/$PROJECT_ID/titanic/ml-service:latest"
    
    print_info "Project: $PROJECT_ID"
    print_info "Region: $REGION"
    print_info "Image tag: $TAG"
    print_info "Image URL: $IMAGE_URL"
    
    # Option 1: Use Cloud Build (when --cloud flag is specified)
    if [ "$BUILD_METHOD" = "cloud" ]; then
        print_info "Building with Cloud Build (this may take a few minutes)..."
        gcloud builds submit \
            --tag $IMAGE_URL \
            --project $PROJECT_ID \
            --region $REGION \
            --timeout=20m
        
        if [ $? -eq 0 ]; then
            # Also tag as latest
            print_info "Tagging as latest..."
            gcloud artifacts docker tags add \
                $IMAGE_URL \
                $LATEST_URL \
                --project=$PROJECT_ID \
                --location=$REGION
        else
            print_error "Cloud Build failed"
            exit 1
        fi
    else
        # Option 2: Build locally and push (default, proper Docker workflow)
        print_info "Building Docker image locally for Linux/AMD64..."
        docker build --platform linux/amd64 -t $IMAGE_URL -t $LATEST_URL .
        
        if [ $? -eq 0 ]; then
            print_success "Docker image built successfully"
            print_info "Pushing image to Artifact Registry..."
            docker push $IMAGE_URL
            docker push $LATEST_URL
        else
            print_error "Docker build failed"
            exit 1
        fi
    fi
    
    if [ $? -eq 0 ]; then
        print_success "✅ Image built and pushed successfully"
        print_info ""
        print_info "Image URLs:"
        print_info "  Tagged: $IMAGE_URL"
        print_info "  Latest: $LATEST_URL"
        print_info ""
        print_info "Next step: Deploy with './doit.sh cloud-deploy' or './doit.sh cloud-deploy $TAG'"
    else
        print_error "Failed to push image"
        exit 1
    fi
}

cmd_cloud_deploy() {
    print_header "Deploying to Cloud Run"
    print_info "Deploying ML service from Artifact Registry..."
    
    cd "$PROJECT_ROOT"
    
    # Get current project and region
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured. Use './doit.sh env-switch' first."
        exit 1
    fi
    
    if [ -z "$REGION" ]; then
        REGION="us-central1"
        print_warning "No region configured. Using default: $REGION"
    fi
    
    # Determine environment
    ENV=""
    if [[ "$PROJECT_ID" == *"-stg" ]]; then
        ENV="staging"
        print_info "🔧 Environment: STAGING"
    elif [[ "$PROJECT_ID" == *"-prd" ]]; then
        ENV="production"
        print_warning "⚠️  Environment: PRODUCTION - Deploying to live environment!"
    fi
    
    # Determine image tag to deploy
    if [ -n "$1" ]; then
        TAG="$1"
    else
        TAG="latest"
    fi
    
    IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/titanic/ml-service:$TAG"
    
    print_info "Deploying to project: $PROJECT_ID"
    print_info "Region: $REGION"
    print_info "Image: $IMAGE_URL"
    
    # Check if secrets exist in Secret Manager
    if gcloud secrets describe jwt-private-key --project=$PROJECT_ID >/dev/null 2>&1; then
        print_info "Using secrets from Secret Manager"
        SECRET_ARGS="--set-secrets JWT_PRIVATE_KEY=jwt-private-key:latest,JWT_PUBLIC_KEY=jwt-public-key:latest"
    else
        print_warning "Secrets not found in Secret Manager"
        print_info "Run './doit.sh setup-secrets' to upload JWT keys to Secret Manager"
        print_info "Deploying without secrets (service will fail to start properly)"
        SECRET_ARGS=""
    fi
    
    # Deploy to Cloud Run
    print_info "Deploying service (this may take a minute)..."
    gcloud run deploy titanic-ml-service \
        --image $IMAGE_URL \
        --region $REGION \
        --allow-unauthenticated \
        $SECRET_ARGS \
        --set-env-vars "ML_SERVICE_ENVIRONMENT=${ENV:-development}" \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10 \
        --timeout 300 \
        --port 8080 \
        --project $PROJECT_ID
    
    if [ $? -eq 0 ]; then
        SERVICE_URL=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(status.url)')
        print_success "Deployment completed successfully"
        print_info ""
        print_info "🚀 Service URL: $SERVICE_URL"
        print_info "📊 Health Check: $SERVICE_URL/health"
        print_info "📚 API Docs: $SERVICE_URL/docs"
        print_info "🔐 Protected Endpoint: $SERVICE_URL/predict (JWT required)"
        if [ "$ENV" = "production" ]; then
            print_warning "⚠️  This is PRODUCTION - Handle with care!"
        fi
        print_info ""
        print_info "Deployed version: $TAG"
        print_info "Test with: curl $SERVICE_URL"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

cmd_update_service_secrets() {
    print_header "Update Service Secrets"
    print_info "Updating Cloud Run service to use latest secrets from Secret Manager..."
    
    cd "$PROJECT_ROOT"
    
    # Get current project and region
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured. Use './doit.sh env-switch' first."
        exit 1
    fi
    
    if [ -z "$REGION" ]; then
        REGION="us-central1"
    fi
    
    # Check if service exists
    if ! gcloud run services describe titanic-ml-service --region=$REGION --project=$PROJECT_ID --quiet >/dev/null 2>&1; then
        print_error "Service 'titanic-ml-service' not found"
        print_info "Deploy first with: ./doit.sh cloud-deploy"
        exit 1
    fi
    
    # Check if secrets exist in Secret Manager
    if ! gcloud secrets describe jwt-private-key --project=$PROJECT_ID >/dev/null 2>&1; then
        print_error "Secrets not found in Secret Manager"
        print_info "Run './doit.sh setup-secrets' first to upload JWT keys"
        exit 1
    fi
    
    print_info "Project: $PROJECT_ID"
    print_info "Region: $REGION"
    print_info "Service: titanic-ml-service"
    
    # Update service to use latest secret versions
    print_info "Updating service to use latest secret versions..."
    gcloud run services update titanic-ml-service \
        --update-secrets JWT_PRIVATE_KEY=jwt-private-key:latest,JWT_PUBLIC_KEY=jwt-public-key:latest \
        --region $REGION \
        --project $PROJECT_ID
    
    if [ $? -eq 0 ]; then
        print_success "✅ Service secrets updated successfully"
        print_info ""
        print_info "The service will automatically use the latest versions of:"
        print_info "  - jwt-private-key"
        print_info "  - jwt-public-key"
        print_info ""
        print_info "Note: The service will restart to pick up the new secrets"
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(status.url)')
        print_info ""
        print_info "Service URL: $SERVICE_URL"
        print_info "Test with: curl $SERVICE_URL/health"
    else
        print_error "Failed to update service secrets"
        exit 1
    fi
}

cmd_cloud_logs() {
    print_header "Cloud Run Service Logs"
    print_info "Viewing logs for Titanic ML service..."
    
    # Get current region
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    if [ -z "$REGION" ]; then
        REGION="us-central1"
        print_info "No region configured. Using default: $REGION"
    fi
    
    # Check if service exists
    if ! gcloud run services describe titanic-ml-service --region=$REGION --quiet >/dev/null 2>&1; then
        print_error "Service 'titanic-ml-service' not found in region $REGION"
        print_info "Deploy first with: ./doit.sh cloud-deploy"
        exit 1
    fi
    
    print_info "Showing logs from region: $REGION"
    print_info "Press Ctrl+C to exit log streaming"
    print_info ""
    
    # Stream logs with filtering for the ML service
    gcloud logs tail "projects/$(gcloud config get-value project)/logs/run.googleapis.com%2Frequests" \
        --filter="resource.labels.service_name=titanic-ml-service AND resource.labels.location=$REGION" \
        --format="table(timestamp,severity,textPayload)" \
        "$@"
}

cmd_cloud_status() {
    print_header "Cloud Run Service Status"
    print_info "Checking status of Titanic ML service..."
    
    # Get current project and region
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    REGION=$(gcloud config get-value run/region 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project configured."
        exit 1
    fi
    
    if [ -z "$REGION" ]; then
        REGION="us-central1"
        print_info "No region configured. Using default: $REGION"
    fi
    
    print_info "Project: $PROJECT_ID"
    print_info "Region: $REGION"
    print_info ""
    
    # Check if service exists
    if ! gcloud run services describe titanic-ml-service --region=$REGION --quiet >/dev/null 2>&1; then
        print_warning "Service 'titanic-ml-service' not deployed yet"
        print_info "Deploy with: ./doit.sh cloud-deploy"
        exit 0
    fi
    
    # Get service information
    SERVICE_URL=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(status.url)')
    SERVICE_STATUS=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(status.conditions[0].status)')
    LAST_DEPLOYED=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(metadata.annotations."serving.knative.dev/lastModifier")')
    CPU=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(spec.template.spec.containers[0].resources.limits.cpu)')
    MEMORY=$(gcloud run services describe titanic-ml-service --region=$REGION --format='value(spec.template.spec.containers[0].resources.limits.memory)')
    
    # Display status
    if [ "$SERVICE_STATUS" = "True" ]; then
        print_success "✅ Service is running and healthy"
    else
        print_warning "⚠️ Service status: $SERVICE_STATUS"
    fi
    
    print_info ""
    print_info "📊 Service Details:"
    print_info "  URL: $SERVICE_URL"
    print_info "  CPU: ${CPU:-1 vCPU}"
    print_info "  Memory: ${MEMORY:-1Gi}"
    print_info "  Last deployed by: ${LAST_DEPLOYED:-Unknown}"
    print_info ""
    print_info "🔗 Quick Links:"
    print_info "  Health Check: $SERVICE_URL/health"
    print_info "  API Documentation: $SERVICE_URL/docs"
    print_info "  Model Information: $SERVICE_URL/models/info"
    print_info ""
    print_info "🧪 Test Commands:"
    print_info "  curl $SERVICE_URL"
    print_info "  curl $SERVICE_URL/health"
    
    # Test health endpoint
    print_info ""
    print_info "🏥 Testing health endpoint..."
    if curl -s --max-time 10 "$SERVICE_URL/health" >/dev/null; then
        print_success "Health endpoint responding"
    else
        print_warning "Health endpoint not responding (service may be cold starting)"
    fi
}

cmd_clean() {
    print_header "Cleaning Project"
    print_info "Removing generated files and caches..."
    
    cd "$PROJECT_ROOT"
    
    # Remove Python cache files
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove coverage files
    find . -name ".coverage" -delete 2>/dev/null || true
    find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Remove temporary files
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true
    
    print_success "Project cleaned successfully"
}


# Main command dispatcher
main() {
    if [ $# -eq 0 ]; then
        print_error "No command provided"
        cmd_help
        exit 1
    fi
    
    case "$1" in
        "help"|"-h"|"--help")
            cmd_help
            ;;
        "train")
            shift
            cmd_train "$@"
            ;;
        "lint")
            shift
            cmd_lint "$@"
            ;;
        "lint-fix")
            shift
            cmd_lint_fix "$@"
            ;;
        "python-security-scan")
            shift
            cmd_python_security_scan "$@"
            ;;
        "python-service-tests")
            shift
            cmd_python_service_tests "$@"
            ;;
        "python-service-start")
            shift
            cmd_python_service_start "$@"
            ;;
        "docker-build")
            shift
            cmd_docker_build "$@"
            ;;
        "docker-start")
            shift
            cmd_docker_start "$@"
            ;;
        "env-switch")
            shift
            cmd_env_switch "$@"
            ;;
        "setup-secrets")
            shift
            cmd_setup_secrets "$@"
            ;;
        "gcp-setup")
            shift
            cmd_gcp_setup "$@"
            ;;
        "cloud-build")
            shift
            cmd_cloud_build "$@"
            ;;
        "cloud-deploy")
            shift
            cmd_cloud_deploy "$@"
            ;;
        "update-service-secrets")
            shift
            cmd_update_service_secrets "$@"
            ;;
        "cloud-logs")
            shift
            cmd_cloud_logs "$@"
            ;;
        "cloud-status")
            shift
            cmd_cloud_status "$@"
            ;;
        "install-deps")
            shift
            cmd_install_deps "$@"
            ;;
        "clean")
            shift
            cmd_clean "$@"
            ;;
        *)
            print_error "Unknown command: $1"
            cmd_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"