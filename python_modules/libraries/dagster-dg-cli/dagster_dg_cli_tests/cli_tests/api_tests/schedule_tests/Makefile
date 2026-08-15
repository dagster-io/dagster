.PHONY: rerecord test clean

rerecord:
	python ../_record.py schedule

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
