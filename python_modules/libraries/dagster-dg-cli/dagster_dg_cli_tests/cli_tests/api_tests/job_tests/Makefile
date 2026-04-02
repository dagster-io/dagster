.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record job

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
