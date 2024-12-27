generate:
	antlr4 -Dlanguage=Python3 -visitor AssetSelection.g4 -o generated
	python fix_imports.py
	ruff format
	cd ../../../../../../js_modules/dagster-ui/packages/ui-core && yarn generate-asset-selection
