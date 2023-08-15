docs_black:
	black --fast \
    ../examples/docs_snippets

docs_ruff:
	ruff --fix ../examples/docs_snippets


apidoc-build:
	tox -e sphinx && python scripts/pack_json.py

apidoc-watch-build:
	watchmedo shell-command \
		--patterns='*.rst;conf.py;_ext/*.py' \
		--command='make apidoc-build' \
		--recursive \
		sphinx

next-dev-install:
	cd next; yarn install

next-watch-build:
	cd next; yarn dev

mdx-format: 
	cd next; yarn mdx-format

mdx-full-format: docs_black docs_ruff mdx-format
