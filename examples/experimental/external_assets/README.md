# external-assets/pipes experiment

## prerequisites

1. start a local kind cluster (on mac: `brew install kind` + `kind create cluster`)
2. `docker build -t pipes-materialize:latest -f Dockerfile.materialize .`
3. `docker build -t pipes-check:latest -f Dockerfile.check .`
4. `kind load docker-image pipes-materialize pipes-materialize`
5. `kind load docker-image pipes-check pipes-check`

## start local dagster cloud

```bash

pip install -e ".[dev]"

dagster dev

```
