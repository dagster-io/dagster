.PHONY: rerecord test clean

rerecord:
	dagster-dev dg-api-record schedule

test:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/