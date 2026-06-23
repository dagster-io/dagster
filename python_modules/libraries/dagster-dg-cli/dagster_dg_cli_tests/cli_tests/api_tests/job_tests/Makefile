.PHONY: rerecord test clean

rerecord:
	python ../_record.py job

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
