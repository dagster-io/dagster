# Makefile

adhoc_pypi:
	@chmod +x scripts/increment_pypi_version.sh
	@./scripts/increment_pypi_version.sh

mirror_tutorial:
	@chmod +x scripts/mirror_tutorial.sh
	@./scripts/mirror_tutorial.sh

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
	@git checkout -b release-$$(./scripts/extract_version.sh)
	@git commit -m "[dagster-airlift] $$(./scripts/extract_version.sh)"
	@git push origin release-$$(./scripts/extract_version.sh)
	echo "Release branch created. Please create a PR and merge it to master."
	@echo "Returning to master branch..."
	@git checkout master