---
title: Dagster & Microsoft SQL Server
sidebar_label: Microsoft SQL Server
sidebar_position: 1
description: SQL Server-backed run storage, event log storage and schedule storage.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-mssql
pypi: https://pypi.org/project/dagster-mssql/
canonicalUrl: '/integrations/libraries/mssql'
slug: '/integrations/libraries/mssql'
sidebar_custom_props:
  logo: images/integrations/mssql.png
---

import DocCardList from '@theme/DocCardList';

<p>{frontMatter.description}</p>

Supports SQL Server 2017 and later, Azure SQL Database, and Azure SQL Managed Instance.

## Installation

<PackageInstallInstructions packageName="dagster-mssql" />

`dagster-mssql` connects through [pyodbc](https://github.com/mkleehammer/pyodbc), which dispatches to a locally installed ODBC driver. Install [Microsoft ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server) (or 17) on every host that runs Dagster: the webserver, the daemon, and each code location.

## Configuration

In `$DAGSTER_HOME/dagster.yaml`, either give a full URL:

```yaml
storage:
  mssql:
    mssql_url: 'mssql+pyodbc://user:password@host:1433/dagster?driver=ODBC+Driver+18+for+SQL+Server'
```

or configure the parts separately:

```yaml
storage:
  mssql:
    mssql_db:
      username: dagster
      password:
        env: DAGSTER_MSSQL_PASSWORD
      hostname: sqlserver.example.com
      db_name: dagster
      port: 1433
      driver: 'ODBC Driver 18 for SQL Server'
      params:
        Encrypt: 'yes'
```

Every field is a `StringSource` or `IntSource`, so any of them can be read from an environment variable. Anything under `params` is passed through to the ODBC driver, which is where `Encrypt`, `TrustServerCertificate`, `Authentication` (for Microsoft Entra ID) and `MultiSubnetFailover` belong.

Before pointing Dagster at a new database, enable read-committed snapshot on it. See the [reference](/integrations/libraries/mssql/reference) for that and the other SQL Server specifics.

<DocCardList />
