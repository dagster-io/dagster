# Dagster Docs

This is the home of the Dagster documentation. The documentation site is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

---

## Overview of the docs

- `./src` contains custom components, styles, themes, and layouts.
- `./content-templates` contains the templates for the documentation pages.
- `./docs/` is the source of truth for the documentation.
- `/examples/docs_beta_snippets/docs_beta_snippets/` contains code examples for the documentation. Some code examples also live in `/examples/` and `/examples/docs_snippets/docs_snippets/`.

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

The site uses `node` and [yarn](https://yarnpkg.com/) for package management. We recommend using `nvm` to install the long-term-support version of Node.

```
brew install nvm yarn
nvm install --lts
```

```
yarn install
```

The docs site also uses [Vale](https://vale.sh/) to check for issues in the documentation.

Install Vale with:

```bash
brew install vale
```

---

## Local development

To start the local development server:

```bash
yarn start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server. Access the website at [http://localhost:3050](http://localhost:3050).

### Linters

To check the documentation for different issues, use the following:

```bash
## Lints all content, applies lint autofixes and prettier changes
yarn lint

## Lints documentation content using Vale Server
## Checks for style guide adherence, grammar, spelling, etc.
yarn vale
yarn vale /path/to/file      ## check individual file
yarn vale --no-wrap          ## remove wrapping from output
```

---

## Build

To build the site for production:

```bash
# build and copy API markdown files
make mdx
make mdx_copy

# build and copy the Sphinx objects.inv
make sphinx_objects_inv

# build the static site
yarn build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service. This also checks for any broken links in the documentation.

**NOTE:** the `make sphinx_objects_inv` command needs to be run before creating a new release. We plan to automate this procedure in the future.

---

## Deployment

This site is built and deployed using Vercel.

### API documentation

API documentation is built in Vercel by overriding the _Build Command_ to the following:

```sh
yarn sync-api-docs && yarn build
```

This runs the `scripts/vercel-sync-api-docs.sh` script which builds the MDX files using the custom `sphinx-mdx-builder`, and copies the resulting MDX files to `docs/api/python-api`.

---

## Search

Algolia search is used for search results on the website, as configured in `docusaurus.config.ts`.

The following environment variables must be configured in Vercel:

- `ALGOLIA_APP_ID`
- `ALGOLIA_API_KEY`
- `ALGOLIA_INDEX_NAME`

These variables are not loaded when `process.env.ENV === 'development'`.
