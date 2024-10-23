SPHINXOPTS    ?= -j auto -W --keep-going -v
SPHINXBUILD   ?= sphinx-build 
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile install

install:
	pip install uv
	uv pip install -r requirements.txt
	uv pip install -e _ext/dagster-sphinx
	uv pip install -e _ext/sphinx-mdx-builder

mdx_copy:
	rm -rf ../docs-beta/docs/api/libraries
	find ../docs-beta/docs/api/*.mdx ! -name index.mdx -exec rm {} +
	cp -rf _build/mdx/sections/api/apidocs/* ../docs-beta/docs/api/
	
# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
