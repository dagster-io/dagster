docs_dev_install:
	cd next; yarn;

dev:
	cd next; yarn dev;

build:
	cd sphinx; make clean; make json; cd ..; python pack_json.py

snapshot:
	cd next; yarn; yarn snapshot

update_version:
	echo "Saving version $(version)"
	python update_version.py --version $(version)
