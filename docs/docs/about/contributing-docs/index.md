---
title: Contributing documentation
description: TK
sidebar_position: 30
canonicalUrl: '/about/contributing-docs'
slug: '/about/contributing-docs'
---

To install required dependencies, run the following commands:

```bash
cd docs
yarn install
```

To build the non-API documentation, run:

```bash
yarn build
```

API documentation is built separately using Sphinx. Before starting the dev server for the first time, you need to build the API docs. If you change any docstrings in code or the contents of any `.rst` files, be sure to re-run the following command in the docs directory:

```bash
yarn build-api-docs
```

Then start the local development server:

```bash
yarn start
```

## API docs (rST) \{#api-docs}

API documentation lives in [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) files in the following places:

| Repo source                                                                                                                                    | Docs website location                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [`/docs/sphinx/sections/api`](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/api)                                      | [API section](https://docs.dagster.io/api)                                                                     |
| [`docs/sphinx/sections/integrations/libraries`](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/integrations/libraries) | [Integrations section](https://docs.dagster.io/integrations/libraries) (under specific integration subsection) |

These `rST` files reference modules, classes, and methods from Python files in the [`python_modules`](https://github.com/dagster-io/dagster/tree/master/python_modules) directory (mainly the `dagster`, `dagster-graphql`, `dagster-pipes`, and `libraries` directories). When the API docs are built, Sphinx populates them with the docstrings from those modules, classes, and methods.

When you make changes to the API, you may need to do some or all of the following:

- Add or update docstrings in Python files
- Update reStructuredText files to reference new modules, classes, or methods