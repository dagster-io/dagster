# Dagster Docs

This is the home of the Dagster documentation. The documentation site is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

---

## Overview of the docs

- `./src` contains custom components, styles, themes, and layouts.
- `./docs/` contains documentation Markdown files.
- `/examples/docs_snippets/docs_snippets/` contains code examples for the documentation. Some code examples also live in `/examples/` and `/examples/docs_snippets/docs_snippets/`.

The docs are organized into the following sections:

- Docs - includes content from [getting-started](./docs/getting-started/), [etl-pipeline-tutorial](./docs/etl-pipeline-tutorial/), [guides](./docs/guides/), and [about](./docs/about/)
- [Examples](./docs/examples/)
- [Integrations](./docs/integrations/)
- [Dagster+](./docs/dagster-plus/)
- [API reference](./docs/api/)

`sidebar.ts` and `docusaurus.config.ts` are the main configuration files for the documentation.

For formatting guidelines, see the [CONTRIBUTING](CONTRIBUTING.md) guide.

---

## Installation

The site uses [yarn](https://yarnpkg.com/) for package management. We recommend using `nvm` to install the long-term-support version of Node.

```bash
nvm install --lts
```

```bash
yarn install
```

---

## Local development

To start the local development server:

```bash
yarn start
```

This command starts a local development server and opens [http://localhost:3050](http://localhost:3050) in a browser window.

### Checking for build errors

To check for broken links and other build errors, you will need to build API docs, then build the full docs site:

```bash
# build and copy API markdown files; build and copy the sphinx `objects.inv` to static/
yarn build-api-docs

# build the static site
yarn build
```

Note that building API docs requires you to configure Python on your system. To do this, run `make dev_install` as outlined in the [Dagster contributing guide](https://docs.dagster.io/about/contributing).

### Linting

To check the documentation for formatting issues, run the following:

```bash
yarn format
```

---

## Generated content

Kinds tags are generated programmatically and stored in the `docs/partials/_KindsTags.md` partial with the following command:

```sh
yarn build-kinds-tags
```

**Note:** Most of the time, you will not need to run this command locally, since it runs on the production build.

---

## Versioning

Previous versions of the docs site, plus an "Upcoming release" version, are made accessible through preview deployments in Vercel.

For example, https://release-1-9-13.archive.dagster-docs.io/ is hosted on the `archive` subdomain of dagster-docs.io where `release-1-9-13` is the release branch in version control.

The "Upcoming release" version is also hosted on the `archive` subdomain. Its release branch is `master`.

These versions are accessible through the navigation bar as external links. See the conditional logic using `VERCEL_ENV` in docusaurus.config.ts.

To validate the dropdown menu, you can run `VERCEL_ENV=preview yarn start`.

---

## Production deployment

This site is built and deployed using Vercel.

The _build_ step in Vercel is overridden to build API documentation using the `scripts/vercel-sync-api-docs.sh` script; this is configured in the `vercel.json` file through the `buildCommand` property.

---

## Search

Algolia search is used for search results on the website, as configured in `docusaurus.config.ts`.

The following environment variables must be configured in Vercel:

- `ALGOLIA_APP_ID`
- `ALGOLIA_API_KEY`
- `ALGOLIA_INDEX_NAME`

These variables are not loaded when `process.env.ENV === 'development'`.

---

## API Documentation Control

This section documents current behavior (some of which is nonideal) and documents the todos to fix them.

### Documentation Pathways

#### Path 1: Explicit RST Directives (Primary Control)

The primary mechanism for controlling what appears in documentation is manual curation through RST files located in `sphinx/sections/api/apidocs/`. These files explicitly list symbols using Sphinx autodoc directives:

- `.. autodecorator::` - Documents decorators (e.g., `@asset`, `@op`, `@job`)
- `.. autofunction::` - Documents standalone functions
- `.. autoclass::` - Documents classes
- `.. click::` - Documents CLI commands from `click` commands and groups

**Key characteristic**: These directives currently do not inspect the `@public` annotation system. If a symbol is explicitly listed in an RST file, it will be documented regardless of whether it has the `@public` annotation.

#### Path 2: @public Annotation Filtering (Class Members Only)

The `@public` annotation system provides automatic filtering, but **only applies to class members** when using `autoclass` with the `:members:` option. The custom `dagster_sphinx` extension (in `sphinx/_ext/dagster-sphinx/`) filters class members based on the `is_public()` function from `dagster._annotations`.

### How Symbols Reach Documentation

1. **Top-level exports** (like `dagster.asset`):

   - Exported in module `__init__.py` files
   - Explicitly documented in RST files with appropriate autodoc directives
   - May or may not have `@public` annotation (not required)

2. **Class members**:

   - Must be marked with `@public` annotation to appear in documentation
   - Only filtered when parent class uses `:members:` option in RST files

3. **Special cases**:
   - `dagster_pipes` modules: All symbols considered public regardless of annotations
   - Explicitly documented symbols: RST directives override annotation requirements

### Docstring Validation Implications

For comprehensive docstring validation, check symbols that are:

1. **Explicitly documented in RST files** via any autodoc directive
2. **Marked with `@public` annotation** (for class members)
3. **Located in `dagster_pipes` modules** (special case)

The RST files serve as the **authoritative source** for what constitutes the public API surface, making them essential for determining validation scope.

### Architecture Files

- **RST Documentation**: `sphinx/sections/api/apidocs/**/*.rst`
- **Public Annotations**: `python_modules/dagster/dagster/_annotations.py`
- **Sphinx Extension**: `sphinx/_ext/dagster-sphinx/dagster_sphinx/__init__.py`
- **Build Configuration**: `sphinx/conf.py`
