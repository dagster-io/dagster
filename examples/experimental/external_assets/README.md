# external-assets/pipes experiment

## prerequisites

1. start a local kind cluster (on mac: `brew install kind` + `kind create cluster`)
2. `docker build -t pipes-dogfood:latest .`
3. `kind load docker-image pipes-dogfood pipes-dogfood`

## start local dagster cloud

```bash

pip install -e ".[dev]"

dagster dev

```
