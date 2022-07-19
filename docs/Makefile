apidoc-build:
	tox -e sphinx && python scripts/pack_json.py

apidoc-watch-build:
	watchmedo shell-command \
		--patterns='*.rst;conf.py' \
		--command='make apidoc-build' \
		--recursive \
		sphinx

next-dev-install:
	yarn --cwd=next install

next-watch-build:
	yarn --cwd=next dev

mdx-format:
	yarn --cwd=next mdx-format
