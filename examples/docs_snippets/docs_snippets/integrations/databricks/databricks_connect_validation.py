from pyspark.sql import SparkSession

import dagster as dg


@dg.asset(
    group_name="customer_data_pipeline",
    description="Raw customer records in Unity Catalog from upstream ingestion.",
    kinds={"databricks"},
)
def raw_customer_table(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    context.log.info("Raw customer table available at catalog.schema.customers_raw")
    return dg.MaterializeResult(
        metadata={
            "table": dg.MetadataValue.text("catalog.schema.customers_raw"),
        }
    )


@dg.asset(
    group_name="customer_data_pipeline",
    description=(
        "Validates row counts and null rates on raw customer data using Spark on Databricks. "
        "Blocks downstream assets if data quality thresholds are not met."
    ),
    kinds={"databricks", "spark"},
    deps=[raw_customer_table],
)
def validated_customer_data(
    context: dg.AssetExecutionContext,
    spark: dg.ResourceParam[SparkSession],
) -> dg.MaterializeResult:
    df = spark.sql(
        "SELECT COUNT(*) AS cnt, "
        "SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) AS nulls "
        "FROM catalog.schema.customers_raw"
    )
    row = df.collect()[0]
    row_count = int(row["cnt"])
    null_rate = float(row["nulls"]) / row_count if row_count > 0 else 0.0

    if row_count < 1_000:
        raise ValueError(f"Row count {row_count:,} is below minimum threshold of 1,000")
    if null_rate > 0.05:
        raise ValueError(f"Null rate {null_rate:.1%} exceeds maximum of 5%")

    context.log.info(
        f"Validation passed: {row_count:,} rows, {null_rate:.1%} null rate"
    )
    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(row_count),
            "null_rate": dg.MetadataValue.float(null_rate),
            "validation": dg.MetadataValue.text("passed"),
        }
    )


@dg.asset(
    group_name="customer_data_pipeline",
    description="Customer summary report — only runs after validation passes.",
    deps=[validated_customer_data],
)
def customer_summary_report(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    context.log.info("Generating customer summary report from validated data.")
    return dg.MaterializeResult(
        metadata={
            "report": dg.MetadataValue.text("customer_summary_latest"),
            "status": dg.MetadataValue.text("generated"),
        }
    )
