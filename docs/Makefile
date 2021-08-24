docs_dev_install:
	cd next; yarn; cd ..;

dev:
	cd next; yarn dev;

build:
	cd sphinx; make clean; make json; cd ..; python pack_json.py

snapshot:
	cd next; yarn snapshot && yarn crag-snapshot; cd ..;

update_version:
	echo "Saving version $(version)"
	python update_version.py --version $(version)

reindex_search:
	docker run -it --env-file=.env -e "CONFIG=$(cat ./config.json | jq -r tostring)" algolia/docsearch-scraper
