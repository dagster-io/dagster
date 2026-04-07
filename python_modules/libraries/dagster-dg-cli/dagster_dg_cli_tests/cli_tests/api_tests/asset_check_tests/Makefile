.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record asset-check

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
