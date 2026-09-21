---
name: dagster-docs
description:
  Expert guidance for writing documentation for the Dagster docs website. ALWAYS use before creating or updating
  documentation in the docs directory.
---

## Overview

### Prerequisites

- Always ensure `docs/node_modules` exists before running any commands
  - **Check first**: Look for `docs/node_modules/` directory
  - **If missing**: Run `yarn install` in `/docs` to install dependencies
  - **Command**: `cd /docs; yarn install`

- Always ensure `docs/docs/api/**/*.mdx` files exist before running `yarn start`
  - **Check first:** Look for `docs/docs/api/**/*.mdx` files
  - **If missing:** Run `yarn build-api-docs` in the docs root
  - **Command:** `cd /docs; yarn build-api-docs`

### Related documentation

- **Audiences:** See `audiences.md` for descriptions of primary audiences.
- **Formatting and style:** See `docs/docs/about/contributing-docs/formatting-style.md` for formatting and style conventions.
- **Content model:** See `docs/docs/about/contributing-docs/content-model` for an explanation of the structure and types of content included in Dagster docs.

---

## Section-specific guidance

### `docs/docs/about`

#### Audiences

All

#### Guidance

`docs/docs/about/changelog.md` is automatically populated from `/CHANGES.md` through a custom React component. Do not edit `changelog.md` directly.

### `docs/docs/api`

#### Audiences

- Data pipeline builders
- Data platform owners

#### Guidance

`.mdx` files are generated from `.rst` files in
`docs/sphinx/sections/api` and should not be directly edited. Instead, update the `.rst` file or the docstrings in `/python_modules`.

### `docs/docs/dagster-basics-tutorial`

#### Audiences

- Data pipeline builders

### `docs/docs/deployment`

#### Audiences

- Data platform owners

### `docs/docs/examples`

#### Audiences

- Data pipeline builders

#### Examples

- `docs/docs/examples/full-pipelines/bluesky`

### `docs/docs/getting-started`

#### Audiences

- Data pipeline builders

### `docs/docs/guides`

#### Audiences

- Data pipeline builders

#### Guidance

Most subdirectories in `docs/docs/guides` correspond to phases in the data engineering lifecycle:

- **Build:** Creating data pipelines with core Dagster abstractions, particularly projects, assets, resources, and components.
- **Automate:** Automating data pipelines with declarative automation, schedules, and sensors.
- **Operate:** Managing pipeline operations with run configuration, environment variables and secrets, and concurrency.
- **Log and debug:** Understanding built-in structured event logs and raw compute logs, configuring custom loggers, capturing Python logs, and debugging assets during execution with `pdb`.
- **Observe:** Using alerts, the Dagster+ asset catalog, asset freshness policies, and Insights to observe data pipelines.
- **Test:** Testing assets and pipelines in Dagster to ensure data remains consistent and fresh.

The `docs/docs/guides/labs` subdirectory contains documentation of new features under active development. All pages in the Labs section should import the early access partial and reference it at the top of the page.

The `docs/docs/partials` subdirectory contains files with text that is referenced in multiple places throughout the documentation.

#### Examples

- `docs/docs/guides/build/assets/asset-selection-syntax`
- `docs/docs/guides/automate/declarative-automation`

### `docs/docs/integrations`

#### Audiences

- Data pipeline builders

#### Guidance

- `.mdx` files are generated from `.rst` files in `sphinx/sections/integrations` and should not be directly edited. Instead, update the corresponding `.rst` file. Docstrings for classes and modules in corresponding files in `python_modules/libraries` may also need to be updated.
- If an integration has a component implementation, the component documentation should be placed in the index page of the integration subdirectory

#### Examples

- `docs/docs/integrations/libraries/databricks`
- `docs/docs/integrations/libraries/fivetran`

### `docs/docs/migration`

#### Audiences

- Data pipeline builders
- Data platform owners

#### Guidance

- `docs/docs/migration/upgrading.md` is automatically populated by `/MIGRATION.md` through a custom React component. Do not edit `upgrading.md` directly.

---

## Verification

1. `yarn start` in `/docs` directory
2. Navigate to http://localhost:3050 and view changed pages
