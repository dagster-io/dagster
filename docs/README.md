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

The site uses [yarn](https://yarnpkg.com/) for package management. We recommend using `nvm` to install the long-term-support version of Node.

```sh
brew install nvm yarn vale
```

```sh
nvm install --lts
```

---

## Local development

To start the local development server:

```sh
yarn install
```

```bash
yarn start
```

This command starts a local development server and opens [http://localhost:3050](http://localhost:3050) in a browser window.

### Build

To build the site for production:

```bash
# build and copy api markdown files
yarn build-api-docs

# build and copy the sphinx objects.inv
yarn build-sphinx-object-inv

# build the static site
yarn build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service. This also checks for any broken links in the documentation.

**NOTE:** the `make sphinx_objects_inv` command needs to be run before creating a new release. We plan to automate this procedure in the future.

### Linters

The docs site also uses [Vale](https://vale.sh/) to check for issues in the documentation.

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

### Versioning

Previous versions of the docs site are made accessible through preview deployments in Vercel, for example:

* https://release-1-9-13.archive.dagster-docs.io/

Which is hosted on the `archive` subdomain of dagster-docs.io where `release-1-9-13` is the release branch in version control.

These versions are accessible through the navigation bar as external links, and a link to the "Latest docs" is presented on archived deployments. See the conditional logic using `VERCEL_ENV` in docusaurus.config.ts.

To validate the dropdown menu, you can run `VERCEL_ENV=preview yarn start`.

---

## Deployment

This site is built and deployed using Vercel.

The _build_ step in Vercel is overridden to build API documentation using the `scripts/vercel-sync-api-docs.sh` script; this should _not_ be used locally.

---

## Search

Algolia search is used for search results on the website, as configured in `docusaurus.config.ts`.

The following environment variables must be configured in Vercel:

- `ALGOLIA_APP_ID`
- `ALGOLIA_API_KEY`
- `ALGOLIA_INDEX_NAME`

These variables are not loaded when `process.env.ENV === 'development'`.
