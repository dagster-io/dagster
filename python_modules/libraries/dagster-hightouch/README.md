[![Pypi Publish](https://github.com/hightouchio/dagster-hightouch/actions/workflows/pypi-publish.yml/badge.svg?branch=main)](https://github.com/hightouchio/dagster-hightouch/actions/workflows/pypi-publish.yml)

## Dagster-Hightouch

A Dagster library for triggering syncs in Hightouch.

TODO: Write a README.

```
run_ht_sync_accounts = hightouch_sync_op.configured(
    {"sync_id": 1234}, name="hightouch_sfdc_contacts"
)
```