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
  train                 Train the ML models using the training pipeline
  lint                  Run ruff linting on all Python code
  lint-fix              Run ruff with --fix to automatically fix issues
  python-security-scan  Run security vulnerability scan on Python code
  python-service-tests  Run the comprehensive test suite for the ML service
  python-service-start  Start the FastAPI ML service
  install-deps          Install all dependencies for training and service
  clean                 Clean up generated files and caches
  help                  Show this help message

Examples:
  ./doit.sh train
  ./doit.sh python-service-tests unit
  ./doit.sh lint-fix
  ./doit.sh python-service-start

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
    
    ruff check 1-training/ 2-ml-service/ shared/ "$@"
    
    if [ $? -eq 0 ]; then
        print_success "Code linting passed"
    else
        print_error "Code linting found issues"
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
    
    ruff check --fix 1-training/ 2-ml-service/ shared/ "$@"
    
    if [ $? -eq 0 ]; then
        print_success "Code linting and fixes completed"
    else
        print_error "Code linting fixes failed"
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