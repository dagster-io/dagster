# Dagster Docs

This is the home of the Dagster documentation. The documentation site is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

## Installing dependencies

To install Dagster docs dependencies, run the following command in this directory:

```
yarn install
```

## Building and running docs locally

To build and run Dagster docs locally for the first time:

```
yarn build-api-docs  # builds Sphinx API docs
yarn start           # rebuilds changed non-API docs and starts local docs server
```

After building API docs for the first time, you can use `yarn start` only to start the docs server and rebuild non-API docs. You do not need to run `yarn build-api-docs` every time you start the docs server.

> [!IMPORTANT] > `yarn start` (and `yarn build`) will not rebuild API docs. If you update docstrings in `python_modules` or RST files in `sphinx/sections`, you will need to rerun `yarn build-api-docs` to pick up the changes.

## Fixing docs formatting errors

To fix docs formatting errors:

```
yarn format
```

For more information, see the [Dagster docs contributing guide](https://docs.dagster.io/about/contributing-docs#building-and-running-docs-locally).
