.PHONY: rerecord test clean

rerecord:
	python ../_record.py sensor

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
