.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record log

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
