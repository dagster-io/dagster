## Kitchen Sink

This is designed to be a testbed for testing specific migration scenarios.

First:

```bash
make dev_install
make setup_local_env
```

Then in one shell:

```
make run_airflow
```

Then in another shell:

```
make run_dagster
```
