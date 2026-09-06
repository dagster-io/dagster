.PHONY: rerecord test clean

rerecord:
	python ../_record.py secret

test:
	pytest . -v

snapshot:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
