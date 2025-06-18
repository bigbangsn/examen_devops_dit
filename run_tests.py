"""
Script to run tests with coverage reporting.
"""

import subprocess
import sys

def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    print("Running tests with coverage...")
    
    # Run pytest with coverage
    result = subprocess.run(
        ["pytest", "--cov=taskmanager", "--cov-report=term", "--cov-report=html"],
        capture_output=True,
        text=True
    )
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Return exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())