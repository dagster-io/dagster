# Makefile

# Uploads the package to PyPI after bumping the latest version in setup.py.
adhoc_pypi:
	@chmod +x scripts/increment_pypi_version.sh
	@./scripts/increment_pypi_version.sh

# Mirrors the tutorial to the dagster-airlift-tutorial repo: https://github.com/dagster-io/airlift-tutorial
mirror_tutorial:
	@chmod +x scripts/mirror_tutorial.sh
	@./scripts/mirror_tutorial.sh

# Runs the full release process for dagster-airlift.
# - Enforces that we're on master
# - Bumps the version in setup.py
# - Pushes the changes to PyPI
# - Mirrors the tutorial to the dagster-airlift-tutorial repo
# - Creates a release branch
# - Pushes the release branch to origin
adhoc_release:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then \
		echo "Error: Not on master branch. Please switch to master before running this command."; \
		exit 1; \
	fi
	@echo "Releasing dagster-airlift..."
	@make adhoc_pypi
	@echo "Mirroring tutorial..."
	@make mirror_tutorial 
	@git add .
	@git checkout -b airlift-$$(./scripts/extract_pypi_version.sh)
	@git commit -m "[dagster-airlift] $$(./scripts/extract_pypi_version.sh)"
	@git push origin airlift-$$(./scripts/extract_pypi_version.sh)
	echo "Airlift release branch created. Please create a PR and merge it to master."
	@echo "Returning to master branch..."
	@git checkout master