# AGENT instructions for `docs`

This directory contains the Dagster documentation site which is built with
[Docusaurus](https://docusaurus.io/).

## Setup

- Run `yarn install` after cloning to install dependencies.

## Local development

- Launch a local dev server with `yarn start`. This will open the site at
  `http://localhost:3050`.

## Building docs

- To check for broken links and other build errors, first generate API docs with
  `yarn build-api-docs` then build the site with `yarn build`.
- Building API docs requires a Python environment. Run `make dev_install` as
  outlined in the Dagster contributing guide to set it up. Avoid this step unless necessary because it can be slow.

## Linting and formatting

- Run `yarn format` to apply Prettier formatting to docs files.

## Generated content

- Kinds tags in `docs/partials/_KindsTags.md` can be regenerated with `yarn build-kinds-tags`. Since this is handled during production builds, locally generated kinds tags will be overwritten by the production build process.

Refer to `README.md` in this directory for full details.
