# Dagster Sphinx docs

We use Sphinx for our [API documentation](https://docs.dagster.io/api/).

This directory contains a full Sphinx installation with associated configuration files, the code for our [custom sphinx-mdx-builder extension](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/_ext/sphinx-mdx-builder), our [fork of the sphinx-click extension](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/_ext/sphinx-click), and source [reStructuredText files](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/api/apidocs) that are processed into .mdx files by the sphinx-mdx-builder extension.

## Building API docs locally

In the [docs directory](https://github.com/dagster-io/dagster/tree/master/docs), follow the [installation steps from the docs README](https://github.com/dagster-io/dagster/blob/master/docs/README.md#installation), then run:

```bash
yarn build-api-docs
```

```bash
yarn start
```

## Writing reStructuredText

The source [reStructuredText files](https://github.com/dagster-io/dagster/tree/master/docs/sphinx/sections/api/apidocs) reference Python modules, classes, and methods in the [python_modules](https://github.com/dagster-io/dagster/tree/master/python_modules) directory.

For formatting guidelines, see the [reStructuredText syntax documentation](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).