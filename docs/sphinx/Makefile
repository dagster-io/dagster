SPHINXOPTS    ?= -j auto -q
SPHINXBUILD   ?= sphinx-build
BUILDDIR      = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile watch install livehtml

install:
	pip install -r requirements.txt

watch: 
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

build: 
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

build-markdown: 
	@$(SPHINXBUILD) -M markdown "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

sync-docusaurus: build-markdown
	cp -r _build/markdown ../docs-next/docs/sphinx

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

