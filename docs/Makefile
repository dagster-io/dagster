docs_dev_install:
	cd next; yarn; cd ..;

dev:
	cd next; yarn dev;

build:
	cd sphinx && make clean && make json SPHINXOPTS="-W --keep-going" && cd .. && python pack_json.py

snapshot:
	cd next; yarn snapshot; cd ..;
