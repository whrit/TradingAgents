#!/bin/bash
#
# Alpaca Integration Test Runner
# Runs comprehensive test suite with coverage reporting
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Test configuration
MIN_COVERAGE=90
UNIT_COVERAGE=95
INTEGRATION_COVERAGE=80

# Parse command line arguments
RUN_UNIT=1
RUN_INTEGRATION=0
RUN_E2E=0
VERBOSE=0
COVERAGE=1
PARALLEL=0

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all              Run all tests (unit, integration, e2e)"
    echo "  -u, --unit             Run unit tests only (default)"
    echo "  -i, --integration      Run integration tests"
    echo "  -e, --e2e              Run end-to-end tests"
    echo "  -v, --verbose          Verbose output"
    echo "  -n, --no-coverage      Skip coverage reporting"
    echo "  -p, --parallel         Run tests in parallel"
    echo "  -h, --help             Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            RUN_UNIT=1
            RUN_INTEGRATION=1
            RUN_E2E=1
            shift
            ;;
        -u|--unit)
            RUN_UNIT=1
            RUN_INTEGRATION=0
            RUN_E2E=0
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=1
            shift
            ;;
        -e|--e2e)
            RUN_E2E=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -n|--no-coverage)
            COVERAGE=0
            shift
            ;;
        -p|--parallel)
            PARALLEL=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Print banner
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Alpaca Integration Test Suite                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Please install: pip install pytest${NC}"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Prepare pytest arguments
PYTEST_ARGS=""

if [ $VERBOSE -eq 1 ]; then
    PYTEST_ARGS="$PYTEST_ARGS -vv"
else
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

if [ $COVERAGE -eq 1 ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src/alpaca --cov-report=html --cov-report=term-missing"
fi

if [ $PARALLEL -eq 1 ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

# Run unit tests
if [ $RUN_UNIT -eq 1 ]; then
    echo -e "${BLUE}→ Running unit tests...${NC}"

    if [ $COVERAGE -eq 1 ]; then
        pytest tests/alpaca/unit/ -m unit $PYTEST_ARGS --cov-fail-under=$UNIT_COVERAGE || {
            echo -e "${RED}✗ Unit tests failed!${NC}"
            exit 1
        }
    else
        pytest tests/alpaca/unit/ -m unit $PYTEST_ARGS || {
            echo -e "${RED}✗ Unit tests failed!${NC}"
            exit 1
        }
    fi

    echo -e "${GREEN}✓ Unit tests passed${NC}"
    echo ""
fi

# Run integration tests
if [ $RUN_INTEGRATION -eq 1 ]; then
    echo -e "${BLUE}→ Running integration tests...${NC}"

    # Check for paper trading credentials
    if [ -z "${ALPACA_PAPER_KEY:-}" ] || [ -z "${ALPACA_PAPER_SECRET:-}" ]; then
        echo -e "${YELLOW}⚠  Skipping integration tests (no paper trading credentials)${NC}"
        echo -e "${YELLOW}   Set ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET to run integration tests${NC}"
    else
        if [ $COVERAGE -eq 1 ]; then
            pytest tests/alpaca/integration/ -m integration $PYTEST_ARGS --cov-fail-under=$INTEGRATION_COVERAGE --maxfail=3 || {
                echo -e "${RED}✗ Integration tests failed!${NC}"
                exit 1
            }
        else
            pytest tests/alpaca/integration/ -m integration $PYTEST_ARGS --maxfail=3 || {
                echo -e "${RED}✗ Integration tests failed!${NC}"
                exit 1
            }
        fi

        echo -e "${GREEN}✓ Integration tests passed${NC}"
    fi
    echo ""
fi

# Run E2E tests
if [ $RUN_E2E -eq 1 ]; then
    echo -e "${BLUE}→ Running end-to-end tests...${NC}"

    # E2E tests only run on main branch or with explicit flag
    if [ "${CI_BRANCH:-}" = "main" ] || [ "${FORCE_E2E:-}" = "1" ]; then
        if [ -z "${ALPACA_PAPER_KEY:-}" ] || [ -z "${ALPACA_PAPER_SECRET:-}" ]; then
            echo -e "${YELLOW}⚠  Skipping E2E tests (no paper trading credentials)${NC}"
        else
            pytest tests/alpaca/e2e/ -m e2e $PYTEST_ARGS --maxfail=1 || {
                echo -e "${RED}✗ E2E tests failed!${NC}"
                exit 1
            }

            echo -e "${GREEN}✓ E2E tests passed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠  Skipping E2E tests (only run on main branch)${NC}"
        echo -e "${YELLOW}   Set FORCE_E2E=1 to run E2E tests${NC}"
    fi
    echo ""
fi

# Print coverage summary
if [ $COVERAGE -eq 1 ]; then
    echo -e "${BLUE}→ Coverage Summary${NC}"
    echo ""

    if [ -f "tests/alpaca/coverage.json" ]; then
        # Extract overall coverage percentage
        COVERAGE_PCT=$(python3 -c "import json; print(json.load(open('tests/alpaca/coverage.json'))['totals']['percent_covered'])")

        if (( $(echo "$COVERAGE_PCT >= $MIN_COVERAGE" | bc -l) )); then
            echo -e "${GREEN}✓ Coverage: ${COVERAGE_PCT}% (target: ${MIN_COVERAGE}%)${NC}"
        else
            echo -e "${RED}✗ Coverage: ${COVERAGE_PCT}% (target: ${MIN_COVERAGE}%)${NC}"
            exit 1
        fi
    fi

    echo -e "${BLUE}  Full report: tests/alpaca/htmlcov/index.html${NC}"
    echo ""
fi

# Print success message
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ All tests passed successfully!           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"

exit 0
