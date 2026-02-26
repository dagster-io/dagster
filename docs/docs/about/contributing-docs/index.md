---
title: Contributing documentation to Dagster
sidebar_label: Contributing documentation
description: Local dev instructions and style, formatting, and content structure guidelines for Dagster docs.
sidebar_position: 30
canonicalUrl: '/about/contributing-docs'
slug: '/about/contributing-docs'
---

The Dagster documentation site is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

## Overview

The open source docs can be found in the [dagster repository](https://github.com/dagster-io/dagster/tree/master/docs/docs).

- `./docs/` contains documentation Markdown files.
- `./src` contains custom React components, plugins, presets, styles, themes, and layouts.
- `/examples/docs_snippets/docs_snippets/` contains code examples for the documentation. Some code examples also live in `/examples/` and `/examples/docs_snippets/docs_snippets/`.

The docs are organized into the following sections:

| Docs section                                                               | Directory                                                    | Description                                                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [User guide](https://docs.dagster.io)                                      | `/docs/guides`                                               | Comprehensive documentation on building data pipelines with Dagster.                                                                                                                                                                                                 |
| Getting Started                                                            | `/docs/getting-started`                                      | An overview of Dagster, quickstart guides for Dagster+ and OSS users, installation instructions, a high-level introduction to Dagster concepts, and links to additional educational resources.                                                                       |
| [Dagster basics tutorial](https://docs.dagster.io/dagster-basics-tutorial) | `/docs/dagster-basics-tutorial`                              | A deeper introduction to core Dagster concepts through a working example.                                                                                                                                                                                            |
| About                                                                      | `/docs/about`                                                | About the Dagster community, releases, changelog, and telemetry. Also includes contributing guides for code and docs.                                                                                                                                                |
| [Examples](https://docs.dagster.io/examples)                               | `/docs/examples`                                             | Examples showcasing the use of Dagster to solve real-world problems.                                                                                                                                                                                                 |
| [Deployment](https://docs.dagster.io/deployment)                           | `/docs/deployment`                                           | Comprehensive documentation on deploying Dagster OSS and Dagster+, and deployment configuration.                                                                                                                                                                     |
| [Migration](https://docs.dagster.io/migration)                             | `/docs/migration`                                            | Documentation on upgrading Dagster and migrating to Dagster+, or from Dagster+ Serverless to Hybrid.                                                                                                                                                                 |
| [Integrations](https://docs.dagster.io/integrations/libraries)             | `/docs/integrations` and `docs/sphinx/sections/integrations` | Narrative and API documentation on integrating Dagster with external services and applications. For more information on updating integration library API docs, see the [API docs section](#api-docs).                                                                |
| [API](https://docs.dagster.io/api)                                         | `/docs/api` and `/docs/sphinx/sections/api`                  | API reference documentation that covers the `dagster` SDK, `dagster-create`, `dg`, `dagster`, and `dagster-cloud` CLIs, external assets REST API, and GraphQL API, as well as the API lifecycle stages. For more information, see the [API docs section](#api-docs). |

`sidebar.ts` and `docusaurus.config.ts` are the main configuration files for the documentation, and `vercel.json` contains server-side redirects.

For formatting guidelines, see the [Dagster documentation formatting and style guide](/about/contributing-docs/formatting-style).

### API docs (rST) \{#api-docs}

API documentation lives in [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) (`rST`) files in the following places:

| Repo source                                                                                                                                    | Docs website location                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [`/docs/sphinx/sections/api`](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/api)                                      | [API section](https://docs.dagster.io/api)                                                                     |
| [`docs/sphinx/sections/integrations/libraries`](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/integrations/libraries) | [Integrations section](https://docs.dagster.io/integrations/libraries) (under specific integration subsection) |

These `rST` files reference modules, classes, and methods from Python files in the [`python_modules`](https://github.com/dagster-io/dagster/tree/master/python_modules) directory (mainly the `dagster`, `dagster-graphql`, `dagster-pipes`, and `libraries` directories). When the API docs are built, Sphinx populates them with the docstrings from those modules, classes, and methods.

When you make changes to the API, you may need to do one or both of the following:

- Add or update docstrings in Python files
- Update reStructuredText files to reference new modules, classes, or methods

## Building and running docs locally

### Environment setup

In order to build and run the docs site locally, you need to build the API docs, which requires you to configure Python on your system. To do this, run `make dev_install` in the repository root as outlined in the [Dagster code contributing guide](/about/contributing).

Next, install Node. The documentation site uses [yarn](https://yarnpkg.com/) for package management. We recommend using `nvm` to install the long-term-support version of Node:

```bash
nvm install --lts
```

Finally, install Docusaurus and dependencies:

```bash
cd docs
yarn install
```

### Running the local development server

First, build the API docs:

```bash
yarn build-api-docs
```

Note that you will need to run `yarn build-api-docs` anytime you change docstrings or rst files.

To run the local development server:

```bash
yarn start
```

This command only rebuilds the changed pages and doesn't rebuild API docs. To fully rebuild non-API docs and check for broken links, run:

```bash
yarn build
```

### Linting

To check and fix formatting issues in the docs, run the following:

```bash
yarn format
```

## Kind tags

The [supported icons section](/guides/build/assets/metadata-and-tags/kind-tags#supported-icons) of the kind tags page is generated programmatically and stored in the `docs/partials/_KindsTags.md` partial with the following command:

```sh
yarn build-kinds-tags
```

:::note

Most of the time, you will not need to run this command locally, since it runs on the production build.

:::

## Versioning

Previous versions of the docs site, plus an "Upcoming release" version, are made accessible through preview deployments in Vercel.

For example, https://release-1-9-13.archive.dagster-docs.io/ is hosted on the `archive` subdomain of dagster-docs.io where `release-1-9-13` is the release branch in version control.

The "Upcoming release" version is also hosted on the `archive` subdomain. Its release branch is `master`.

These versions are accessible through the navigation bar as external links. See the conditional logic using `VERCEL_ENV` in docusaurus.config.ts.

To validate the dropdown menu, you can run `VERCEL_ENV=preview yarn start`.

## Production deployment

This site is built and deployed using Vercel.

The _build_ step in Vercel is overridden to build API documentation using the `scripts/vercel-sync-api-docs.sh` script; this is configured in the `vercel.json` file through the `buildCommand` property.

## Search

[Algolia](https://www.algolia.com/) search is used for the search bar at the top of the docs site. Algolia tuning is performed by Dagster employees with access to the Algolia admin console.

The following environment variables must be configured in Vercel:

- `ALGOLIA_APP_ID`
- `ALGOLIA_API_KEY`
- `ALGOLIA_INDEX_NAME`

You do not need to set these variables when building docs locally, since they are not loaded when `process.env.ENV === 'development'`.

## Ask Dagster AI

The Ask Dagster AI search interface is powered by [Scout](https://www.scoutos.com/) and configured by Dagster employees with access to the Scout admin console.
