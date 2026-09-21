.PHONY: rerecord test clean

rerecord:
	python ./_record.py asset
	python ./_record.py deployment
	pytest . --snapshot-update -v

test:
	pytest . -v

clean:
	rm -rf asset_tests/recordings/
	rm -rf deployment_tests/recordings/
