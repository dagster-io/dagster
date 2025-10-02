# Analytics Repository

The Analytics team's repository (`repo-analytics/`) demonstrates a traditional data engineering workflow focused on data ingestion, transformation, and analytics reporting. This repository serves as the foundation layer, providing clean, processed data that other teams can build upon.

## Repository Structure

The Analytics repository follows standard Dagster project organization patterns:

```
repo-analytics/
├── dagster_cloud.yaml          # Dagster+ deployment config
├── pyproject.toml             # Python dependencies
├── src/analytics/
│   ├── definitions.py         # Main definitions entry point
│   └── defs/
│       ├── raw_data.py        # Raw data ingestion assets
│       ├── analytics_models.py # Analytics transformations
│       └── io_managers.py     # Resource configurations
```

The repository uses the `defs/` folder pattern, allowing the team to organize their assets logically while ensuring automatic discovery by the definitions entry point.

## Raw Data Ingestion

The foundation of the analytics pipeline starts with raw data ingestion assets that simulate connecting to various business systems:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/defs/raw_data.py"
  language="python"
  startAfter="start_customer_data_asset"
  endBefore="end_customer_data_asset"
  title="raw_data.py - Customer Data Asset"
/>

The raw data assets (`customer_data`, `order_data`, `product_catalog`) simulate typical business data sources. In production, these would connect to actual systems like CRMs, e-commerce platforms, or inventory management systems using appropriate I/O managers and resources.

Each raw data asset is grouped under `"raw_data"` for clear organization in the Dagster UI, making it easy for users to understand the data lineage and identify source systems.

## Analytics Transformations

The Analytics team creates business-ready datasets through a series of transformation assets:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/defs/analytics_models.py"
  language="python"
  startAfter="start_customer_order_summary"
  endBefore="end_customer_order_summary"
  title="analytics_models.py - Customer Order Summary"
/>

The `customer_order_summary` asset demonstrates a typical analytics transformation pattern:

- **Data Joining**: Combines customer and order data to create a unified view
- **Aggregation**: Calculates key metrics like total orders, spending, and order patterns
- **Business Logic**: Transforms raw transactional data into analytics-ready formats

This asset serves as a foundation for both internal analytics reporting and as a dependency for the ML team's feature engineering pipeline.

## Cross-Team Asset Exposure

The Analytics repository produces assets that are designed to be consumed by other teams:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/defs/analytics_models.py"
  language="python"
  startAfter="start_product_performance"
  endBefore="end_product_performance"
  title="analytics_models.py - Product Performance Asset"
/>

The `product_performance` asset creates comprehensive product metrics that include:

- **Sales Metrics**: Orders, units sold, and revenue
- **Profitability Analysis**: Cost calculations and profit margins
- **Catalog Integration**: Links sales data with product catalog information

This asset is specifically designed to be consumed by the ML team for product recommendation and demand forecasting models.

## Asset Organization and Groups

The Analytics repository uses logical asset groups to organize functionality:

- **`raw_data` group**: Source data from external systems
- **`analytics` group**: Transformed business metrics and reports

This grouping strategy makes it easy for both the Analytics team and downstream consumers to understand the purpose and maturity level of different assets. The clear separation between raw and processed data also helps establish data governance boundaries.

## Shared Resource Configuration

All assets in the Analytics repository use the shared `FilesystemIOManager` configured in the definitions file:

<CodeExample
  path="docs_projects/project_multi_repo/repo-analytics/src/analytics/definitions.py"
  language="python"
  startAfter="start_shared_io_manager"
  endBefore="end_shared_io_manager"
  title="definitions.py - Shared I/O Manager"
/>

This shared storage configuration ensures that assets materialized by the Analytics team can be accessed by other code locations, particularly the ML team that depends on analytics outputs for their feature engineering pipeline.

## Next steps

Now that we understand the Analytics repository's data foundation layer, we can explore how the ML Platform team builds sophisticated machine learning workflows on top of this analytics data.

- Continue this tutorial with [ML Repository](/examples/full-pipelines/multi-repo/ml-repository)
