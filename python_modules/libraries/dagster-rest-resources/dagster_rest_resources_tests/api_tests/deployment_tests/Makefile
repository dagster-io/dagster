.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record deployment

test:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
