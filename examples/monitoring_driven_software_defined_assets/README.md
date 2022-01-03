# Monitoring Driven Software Defined Asset Data Mart

This example shows how to use monitoring to drive the creation of a [Data Mart](https://en.wikipedia.org/wiki/Data_mart) focussed 
on consumption of software products.  It uses the [Software Defined Assets abstractions](https://docs.dagster.io/guides/dagster/software-defined-assets) 
available since Dagster v0.13.

## Scenario

### Background context

ACME Corp builds and sells set of software products to other companies.  These products are sold via subscription entitlements - 
ie, Company A might purchase an entitlement to use 100 units of Product X for 12 months. 

ACME's Data team is tasked with curating & maintaining a consumption Data Mart to simplify historical analysis & reporting
across the company.  The Data team considers their Data Marts to be a product that they provide to other internal teams.

Information about entitlements is processed by ACME's accounting system.  Daily snapshots about subscription sales & customer information 
are written to ACME's Data Lake.

Individual product teams at ACME store telemetry (including daily usage) for their software products in ACME's Data Lake.

```
┌──────────────────────┐                ┌──────────┐  ┌────────────┐
│ ACME invoice system  │                │ Prod X   │  │ Product Y  │
│                      │                └──────┬───┘  └────┬───────┘
└──────────┬───────────┘                       │           │
           │                                   │           │
 ┌─────────▼───────────┐                   ┌───▼───────────▼─────┐
 │ Daily dump of       │                   │                     │
 │  invoice info       │                   │  Daily telemetry    │
 └───────────────────┬─┘                   └────────┬────────────┘
                     │                              │
          ┌──────────▼─────────────┐    ┌───────────▼────────────┐
          │    Entitlement         │    │      Usage             │
          │    information         │    │      information       │
          └────────────────────┬───┘    └────┬───────────────────┘
                               │             │
                   ┌───────────▼─────────────▼────────────┐
                   │         Consumption DataMart         │
                   └──────────────────────────────────────┘
```

ACME Executives are interested in the consumption of the software products - ie, how much of what customers are entitled to use is
actually being used?  Customer consumption of over 100% is desirable since it suggests that future subscription will grow.  
Consumption well below 100% could suggest that future subscription revenues will decline should customers reduce their subscription 
to match their lower usage.

Reports will run queries against ACME's central instance of the Consumption Data Mart.

### Implementation 

This example project shows how Dagster can be used to create & document the Assets in that Data Mart and automate the ongoing 
operational work to maintain those data Assets.

Just as important, the `docs/decisions` folder documents the decisions that went into the creation of the data mart enabling 
new members of the Data team to understand the historical context and decisions made.

We recommend that you read through those documents in order to build your understanding of what (and the reasons why) the code 
in this example does.

1. [Record architecture decisions](docs/decisions/0001-record-architecture-decisions.md)
2. [Software Defined Assets and Dagster](docs/decisions/0002-software-defined-assets-and-dagster.md)
3. [Start by monitoring Asset quality](docs/decisions/0003-start_by_monitorng_asset_quality.md)
4. [consumption_datamart uses a star schema](docs/decisions/0004-consumption_datamart-uses-a-star-schema.md)
5. [A local/test datawarehouse (based on SQLite3) mirrors production ](docs/decisions/0005-local-datawarehouse-mirrors-production.md)
6. [Each lake table is represented by a Dagster Asset](docs/decisions/0006-each_lake_table_is_represented_by_an_asset.md)
7. [Assets are represented by strongly typed dataframes](docs/decisions/0007-assets_are_represented_by_strongly_typed_dataframes.md)
8. [Assets track data warnings](docs/decisions/0008-assets_track_data_warnings.md)


