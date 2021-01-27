build:
	cd sphinx; make clean; make json; cd ..; python pack_json.py

update_version:
	echo "Saving version $(version)"
	python update_version.py --version $(version)