.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record asset

test:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/