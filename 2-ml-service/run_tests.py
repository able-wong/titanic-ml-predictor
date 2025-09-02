#!/usr/bin/env python3
"""
Test runner script for Titanic ML API.

Provides convenient commands for running different types of tests
with appropriate configuration and reporting.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True

def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|all|coverage]")
        print("\nOptions:")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests only") 
        print("  all         - Run all tests")
        print("  coverage    - Run all tests with detailed coverage report")
        print("  quick       - Run tests quickly (no coverage)")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if test_type == "unit":
        cmd = base_cmd + ["tests/unit/", "-m", "not slow"]
        success = run_command(cmd, "Unit Tests")
        
    elif test_type == "integration":
        cmd = base_cmd + ["tests/integration/"]
        success = run_command(cmd, "Integration Tests")
        
    elif test_type == "all":
        cmd = base_cmd + ["tests/"]
        success = run_command(cmd, "All Tests")
        
    elif test_type == "coverage":
        cmd = base_cmd + [
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ]
        success = run_command(cmd, "All Tests with Coverage")
        
        if success:
            print("\n📊 Coverage report generated:")
            print("  - Terminal: See output above")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml")
            
    elif test_type == "quick":
        cmd = base_cmd + ["tests/", "--no-cov", "-x"]
        success = run_command(cmd, "Quick Test Run")
        
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()