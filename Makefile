.PHONY: help install test run-analysis generate-data clean

# Default target
help:
	@echo "Netflix Ads Analytics Portfolio"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make test             - Run pytest test suite"
	@echo "  make run-analysis     - Run all analysis scripts"
	@echo "  make attribution      - Run attribution analysis only"
	@echo "  make optimization     - Run campaign optimization only"
	@echo "  make ab-test          - Run A/B test calculator only"
	@echo "  make generate-data    - Generate sample data files"
	@echo "  make clean            - Remove generated files and cache"
	@echo "  make check-env        - Verify Python environment"

# Install dependencies
install:
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Check Python environment
check-env:
	@python3 --version
	@python3 -c "import sys; print(f'Python: {sys.executable}')"
	@echo "✓ Python environment OK"

# Run all tests
test:
	@echo "Running tests..."
	pytest tests/ -v --tb=short
	@echo "✓ Tests passed"

# Run all analysis scripts
run-analysis: attribution optimization ab-test
	@echo "✓ All analyses complete"

# Attribution analysis
attribution:
	@echo "Running attribution analysis..."
	cd analysis && python3 attribution_analysis.py
	@echo "✓ Attribution analysis complete"
	@echo "  Output: attribution_results.json"

# Campaign optimization
optimization:
	@echo "Running campaign optimization..."
	cd analysis && python3 campaign_optimizer.py
	@echo "✓ Optimization analysis complete"
	@echo "  Output: campaign_optimization_results.json"

# A/B test calculator
ab-test:
	@echo "Running A/B test calculator..."
	cd analysis && python3 ab_test_calculator.py
	@echo "✓ A/B test analysis complete"
	@echo "  Output: ab_test_results.json"

# Generate sample data (if main scripts generate it)
generate-data:
	@echo "Sample data files already in data/"
	@ls -lh data/
	@echo "✓ Sample data ready"

# Clean up generated files and cache
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -f analysis/attribution_results.json
	rm -f analysis/campaign_optimization_results.json
	rm -f analysis/ab_test_results.json
	@echo "✓ Cleaned up"

# Development: run with verbose output
dev-attribution:
	cd analysis && python3 -u attribution_analysis.py

dev-optimization:
	cd analysis && python3 -u campaign_optimizer.py

dev-ab-test:
	cd analysis && python3 -u ab_test_calculator.py

# Development: run tests with coverage
test-coverage:
	pytest tests/ --cov=analysis --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

# Development: run linter (requires flake8)
lint:
	@echo "Running flake8..."
	flake8 analysis tests --max-line-length=100 --exclude=__pycache__

# Development: format code (requires black)
format:
	@echo "Formatting code with black..."
	black analysis tests

# Quick validation (no dependencies)
validate:
	@echo "Validating project structure..."
	@test -f README.md || { echo "❌ Missing README.md"; exit 1; }
	@test -d analysis || { echo "❌ Missing analysis/"; exit 1; }
	@test -d sql || { echo "❌ Missing sql/"; exit 1; }
	@test -d data || { echo "❌ Missing data/"; exit 1; }
	@test -d config || { echo "❌ Missing config/"; exit 1; }
	@test -d tests || { echo "❌ Missing tests/"; exit 1; }
	@test -d docs || { echo "❌ Missing docs/"; exit 1; }
	@echo "✓ Project structure valid"
	@echo ""
	@echo "Project components:"
	@echo "  Analysis scripts:  $(shell ls analysis/*.py | wc -l) Python files"
	@echo "  SQL models:        $(shell ls sql/*.sql | wc -l) SQL files"
	@echo "  Data samples:      $(shell ls data/*.csv | wc -l) CSV files"
	@echo "  Tests:             $(shell ls tests/*.py | wc -l) test files"
	@echo "  Documentation:     $(shell ls docs/*.md | wc -l) markdown files"
	@echo "  Config files:      $(shell ls config/*.yaml | wc -l) YAML files"

# Setup: create venv and install
setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Virtual environment created and dependencies installed"
	@echo "Run: source venv/bin/activate"

# CI/CD: Run full pipeline
ci: check-env validate test run-analysis
	@echo "✓ CI pipeline passed"

.PHONY: help install test run-analysis generate-data clean check-env attribution optimization ab-test dev-attribution dev-optimization dev-ab-test test-coverage lint format validate setup ci
