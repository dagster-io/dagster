docs_dev_install:
	cd next; yarn; cd ..;

dev:
	cd next; yarn dev;

build:
	cd sphinx; make clean; make json SPHINXOPTS="-W --keep-going"; cd ..; python pack_json.py

snapshot:
	cd next; yarn snapshot; cd ..;

reindex_search:
	docker run -it --env-file=.env -e "CONFIG=$(cat ./config.json | jq -r tostring)" algolia/docsearch-scraper
