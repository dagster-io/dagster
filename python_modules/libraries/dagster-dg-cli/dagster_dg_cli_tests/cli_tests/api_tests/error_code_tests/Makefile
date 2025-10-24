#!/usr/bin/env make

# Error code testing Makefile
# Provides shortcuts for common error testing tasks

.PHONY: test record record-all update-snapshots clean

# Run all error code tests
test:
	pytest . -v

# Record specific error scenario
record:
	@echo "Usage: make record SCENARIO=<scenario_name>"
	@echo "Example: make record SCENARIO=error_asset_not_found"
	@if [ -z "$(SCENARIO)" ]; then \
		echo "Error: SCENARIO parameter is required"; \
		exit 1; \
	fi
	dagster-dev dg-api-record error_code --recording $(SCENARIO)

# Record all error scenarios
record-all:
	dagster-dev dg-api-record error_code

# Update test snapshots
update-snapshots:
	pytest . --snapshot-update

# Clean generated files
clean:
	rm -rf __pycache__ .pytest_cache
	find recordings -name "*.json" -delete 2>/dev/null || true