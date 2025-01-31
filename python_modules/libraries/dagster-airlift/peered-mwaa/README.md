## Peered MWAA

This package provides functionality for peering with a running Amazon Managed Workflows for Apache Airflow (MWAA) environment.

### Development Setup

First, install the package and set up the local environment:

```bash
make dev_install
make setup_local_env
```

### Testing

The package includes both unit tests and integration tests for testing MWAA peering functionality.

To run tests:

```bash
pytest peered_mwaa_tests/
```