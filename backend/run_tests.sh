#!/bin/bash
# Run backend tests

echo "Running AI Livestream Backend Tests..."
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# Run tests
pytest tests/ -v --tb=short "$@"
