---
title: Dagster & ADBC
sidebar_label: ADBC
sidebar_position: 1
description: The community-supported dagster-adbc package provides an ADBCResource for connecting to ADBC-compatible databases in Dagster.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-adbc
pypi: https://pypi.org/project/dagster-adbc/
sidebar_custom_props:
  logo: images/integrations/adbc.svg
  community: true
partnerlink: https://arrow.apache.org/adbc/current/index.html
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-adbc" />

Install the ADBC driver for your database. For example, using [`dbc`](https://github.com/columnar-tech/dbc):

```bash
uv pip install dbc
dbc install flightsql
```

## Example

```python
from dagster import Definitions, EnvVar, asset
from dagster_adbc import ADBCResource


@asset
def my_table(dremio: ADBCResource) -> None:
    with dremio.get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT * FROM my_table")
        table = cursor.fetch_arrow_table()


defs = Definitions(
    assets=[my_table],
    resources={
        "dremio": ADBCResource(
            driver="flightsql",
            uri="grpc+tcp://localhost:32010",
            db_kwargs={"username": "admin", "password": EnvVar("DREMIO_PASSWORD")},
        )
    },
)
```

## About ADBC

[Apache Arrow ADBC](https://arrow.apache.org/adbc/current/index.html) is a standard API for database access built on Apache Arrow.
