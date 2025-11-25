#!/usr/bin/env python3
"""
Phase 3 Test Runner

Runs all integration, performance, and API tests for Phase 3 components.
Generates comprehensive test report.
"""

import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Run and report on test suites"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_test_suite(self, name: str, test_path: str, marker: str = None) -> bool:
        """Run a test suite and capture results"""
        print(f"\n{'='*80}")
        print(f"  Running: {name}")
        print(f"{'='*80}\n")

        cmd = ["pytest", test_path, "-v", "--tb=short"]
        if marker:
            cmd.extend(["-m", marker])

        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start

        self.results[name] = {
            "passed": result.returncode == 0,
            "duration": duration,
            "output": result.stdout + result.stderr
        }

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
        print(f"\n{status} ({duration:.2f}s)")

        return result.returncode == 0

    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = datetime.utcnow()

        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 22 + "PHASE 3 TEST SUITE" + " " * 38 + "║")
        print("╚" + "═" * 78 + "╝")

        # Run integration tests
        integration_passed = self.run_test_suite(
            "Integration Tests - Event Sourcing Flow",
            "tests/integration/test_event_sourcing_flow.py"
        )

        # Run performance tests
        performance_passed = self.run_test_suite(
            "Performance Tests - Load & Stress",
            "tests/performance/test_load_performance.py"
        )

        # Run API contract tests
        api_passed = self.run_test_suite(
            "API Contract Tests - Analytics",
            "tests/api/test_analytics_api.py"
        )

        self.end_time = datetime.utcnow()

        # Generate report
        self.print_summary()

        # Return overall success
        return integration_passed and performance_passed and api_passed

    def print_summary(self):
        """Print test summary report"""
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 26 + "TEST SUMMARY" + " " * 40 + "║")
        print("╚" + "═" * 78 + "╝\n")

        total_duration = (self.end_time - self.start_time).total_seconds()

        # Test results
        print("Test Suites:\n")
        passed_count = 0
        failed_count = 0

        for name, result in self.results.items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            duration = result["duration"]
            print(f"  {status}  {name} ({duration:.2f}s)")

            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1

        # Summary stats
        print(f"\n{'─'*80}\n")
        print(f"Total Suites: {len(self.results)}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Duration: {total_duration:.2f}s")

        # Overall result
        print(f"\n{'─'*80}\n")
        if failed_count == 0:
            print("🎉 ALL TESTS PASSED 🎉")
            print("\nPhase 3 implementation is verified and ready for production!")
        else:
            print("⚠️  SOME TESTS FAILED")
            print(f"\n{failed_count} test suite(s) need attention.")

        print(f"\n{'─'*80}\n")

        # Coverage info
        print("Test Coverage:\n")
        print("  ✓ Event Sourcing Flow (E2E)")
        print("  ✓ CRDT Synchronization")
        print("  ✓ Time-Travel Queries")
        print("  ✓ ML Pipeline Integration")
        print("  ✓ Analytics Dashboard")
        print("  ✓ Performance Benchmarks")
        print("  ✓ Load Testing")
        print("  ✓ Stress Testing")
        print("  ✓ Concurrent Operations")
        print("  ✓ API Contracts")
        print("  ✓ Response Formats")
        print("  ✓ Error Handling")

        print(f"\n{'─'*80}\n")


def run_quick_check():
    """Run quick smoke tests"""
    print("\n🚀 Running Quick Check...")

    cmd = [
        "pytest",
        "tests/integration/test_event_sourcing_flow.py::TestEventSourcingFlow::test_vehicle_lifecycle_with_events",
        "-v"
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0


def check_dependencies():
    """Check that required dependencies are installed"""
    print("\n🔍 Checking dependencies...")

    required = ["pytest", "fastapi", "sqlalchemy"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("\n✅ All dependencies installed")
    return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run Phase 3 test suite")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke tests only"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run API tests only"
    )

    args = parser.parse_args()

    # Check dependencies
    if args.check_deps:
        sys.exit(0 if check_dependencies() else 1)

    if not check_dependencies():
        sys.exit(1)

    # Quick check
    if args.quick:
        sys.exit(0 if run_quick_check() else 1)

    # Run specific test suites
    runner = TestRunner()
    runner.start_time = datetime.utcnow()

    if args.integration:
        passed = runner.run_test_suite(
            "Integration Tests",
            "tests/integration/test_event_sourcing_flow.py"
        )
        sys.exit(0 if passed else 1)

    if args.performance:
        passed = runner.run_test_suite(
            "Performance Tests",
            "tests/performance/test_load_performance.py"
        )
        sys.exit(0 if passed else 1)

    if args.api:
        passed = runner.run_test_suite(
            "API Tests",
            "tests/api/test_analytics_api.py"
        )
        sys.exit(0 if passed else 1)

    # Run all tests
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
