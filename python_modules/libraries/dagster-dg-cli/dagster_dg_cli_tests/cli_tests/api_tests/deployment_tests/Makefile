.PHONY: rerecord test clean

rerecord:
	python ../_record.py deployment

test:
	pytest . --snapshot-update -v

clean:
	rm -rf recordings/
