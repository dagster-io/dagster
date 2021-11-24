# Test Driven Software Defined Asset Data Mart

This example shows how to test drive the creation of a Data Mart focussed on consumption of a software product.  It uses the 
[Software Defined Assets abstractions](https://docs.dagster.io/guides/dagster/software-defined-assets) available since Dagster v0.13.

## Scenario

ACME Corp builds a subscription bundle to other companies that entitles them to certain quantity of each of the software products created by ACME.  

Individual product teams at ACME store telemetry about usage their software products in a central Data Lake.
Subscription sales & customer information is stored in ACME's accounting system with daily snapshots also stored in the Data Lake.

ACME Executives are interested in the consumption of the software products - ie, how much of what customer's subscription's entitle them to use
are being used?  Customer consumption of over 100% is desirable since it suggests that future subscription will grow.  Consumption well below 100%
could suggest that future subscription revenues will decline should customers reduce their subscription to match their lower usage.

ACME's Data team is tasked with curating & maintaining a consumption Data Mart to simplify historical analysis & reporting across the company.
The Data team considers their Data Marts to be a product that they provide to other internal teams. 

This example project shows how Dagster can be used to create & document the Assets in that Data Mart and automate the ongoing operational work to 
maintain those data Assets.

Just as important, the `docs/decisions` folder documents the decisions that went into the creation of the data mart enabling new members of the Data team
to understand the historical context and decisions made.

We recommend that you read through those documents in order to build your understanding of what (and the reasons why) the code in this example does.

1. [Record architecture decisions](docs/decisions/0001-record-architecture-decisions.md)
2. [Software Defined Assets and Dagster](docs/decisions/0002-software-defined-assets-and-dagster.md)
3. [consumption_datamart uses a star schema](docs/decisions/0003-consumption_datamart-uses-a-star-schema.md)
4. [A local/test datawarehouse (based on SQLite3) mirrors production ](docs/decisions/0004-local-datawarehouse-mirrors-production.md)
5. [Each lake table is represented by a Dagster Asset](docs/decisions/0005-each_lake_table_is_represented_by_an_asset.md)


