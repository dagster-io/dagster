apidoc-build:
	tox -e sphinx && python scripts/pack_json.py

apidoc-watch-build:
	watchmedo shell-command \
		--patterns='*.rst;conf.py' \
		--command='make apidoc-build' \
		--recursive \
		sphinx

docs_dev_install:
	cd next; yarn; cd ..;

dev:
	cd next; yarn dev;

snapshot:
	cd next; yarn snapshot; cd ..;
