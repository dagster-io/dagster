.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record asset
	dagster-dev dg-api-record deployment
	pytest . --snapshot-update -v

test:
	pytest . -v

clean:
	rm -rf asset_tests/recordings/
	rm -rf deployment_tests/recordings/
