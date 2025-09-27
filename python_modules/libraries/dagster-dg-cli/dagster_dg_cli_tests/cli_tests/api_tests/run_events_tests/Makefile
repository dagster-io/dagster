.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record run-events

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/