#!/usr/bin/env python3
"""
Comprehensive test runner for Counter-Strike AG2 Agent system.

This script provides easy access to different test categories and scenarios.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle output."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest pytest-cov")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Counter-Strike AG2 Agent tests (streamlined)")
    parser.add_argument("--category", choices=[
        "all", "core", "agents", "integration", "rag"
    ], default="all", help="Test category to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--html-cov", action="store_true", help="Generate HTML coverage report")
    
    args = parser.parse_args()
    
    # Set environment for testing
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    if args.verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-q")
    
    # Coverage options
    if args.coverage or args.html_cov:
        base_cmd.extend([
            "--cov=counter_strike_ag2_agent",
            "--cov-report=term-missing"
        ])
        if args.html_cov:
            base_cmd.append("--cov-report=html")
    
    success = True
    
    if args.category == "all":
        print("Running all streamlined tests...")
        cmd = base_cmd + ["tests/"]
        success = run_command(cmd, "All Essential Tests")
        
    elif args.category == "core":
        print("Running core functionality tests...")
        cmd = base_cmd + ["tests/test_core.py"]
        success = run_command(cmd, "Core Functionality Tests")
        
    elif args.category == "agents":
        print("Running AG2 agent tests...")
        cmd = base_cmd + ["tests/test_agents.py", "tests/test_agents_essential.py"]
        success = run_command(cmd, "AG2 Agent Tests")
        
    elif args.category == "integration":
        print("Running integration tests...")
        cmd = base_cmd + ["tests/test_integration_essential.py"]
        success = run_command(cmd, "Integration Tests")
        
    elif args.category == "rag":
        print("Running RAG tests...")
        cmd = base_cmd + ["tests/test_rag.py"]
        success = run_command(cmd, "RAG Helper Tests")
    
    # Additional useful test runs
    if args.category == "all" and success:
        print("\n" + "="*60)
        print("Running additional test scenarios...")
        print("="*60)
        
        # Test error handling
        cmd = base_cmd + ["-k", "error or fallback or exception", "-v"]
        run_command(cmd, "Error Handling Tests")
        
        # Test edge cases
        cmd = base_cmd + ["-k", "edge_case or boundary", "-v"]
        run_command(cmd, "Edge Case Tests")
    
    if args.html_cov and (args.coverage or args.html_cov):
        print(f"\nHTML coverage report generated in: {Path.cwd() / 'htmlcov' / 'index.html'}")
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())