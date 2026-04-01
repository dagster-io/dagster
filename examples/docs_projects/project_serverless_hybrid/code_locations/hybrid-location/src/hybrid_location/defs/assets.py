import dagster as dg


@dg.asset(
    kinds={"snowflake", "python"},
    description="Ingests large datasets from Snowflake data warehouse",
)
def raw_customer_transactions(
    context: dg.AssetExecutionContext,
) -> dg.MaterializeResult:
    """Load raw transaction data from Snowflake."""
    context.log.info("Ingesting transactions from Snowflake on hybrid agent...")
    return dg.MaterializeResult(metadata={"num_transactions": 500_000})


@dg.asset(
    kinds={"python", "pandas"},
    description="Performs complex transformations on transaction data",
    deps=[raw_customer_transactions],
)
def transformed_transactions(
    context: dg.AssetExecutionContext,
) -> dg.MaterializeResult:
    """Apply business rules and transformations to raw transactions."""
    context.log.info("Transforming transactions...")
    return dg.MaterializeResult(metadata={"num_transformed": 495_000})


@dg.asset(
    kinds={"python", "machine-learning"},
    description="Trains ML model for fraud detection on transaction data",
    deps=[transformed_transactions],
)
def fraud_detection_model(
    context: dg.AssetExecutionContext,
) -> dg.MaterializeResult:
    """Train fraud detection model using transaction patterns."""
    context.log.info("Training fraud detection model...")
    return dg.MaterializeResult(metadata={"accuracy": 0.95})


@dg.asset(
    kinds={"snowflake", "python"},
    description="Applies fraud model to transactions and writes results to Snowflake",
    deps=[fraud_detection_model, transformed_transactions],
)
def fraud_scores(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Score transactions for fraud probability and store in data warehouse."""
    context.log.info("Scoring transactions for fraud...")
    return dg.MaterializeResult(metadata={"num_scored": 495_000})


@dg.asset(
    kinds={"snowflake", "reporting"},
    description="Generates daily fraud analytics reports",
    deps=[fraud_scores],
)
def daily_fraud_report(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Create aggregated fraud analytics for business intelligence."""
    context.log.info("Generating daily fraud report...")
    return dg.MaterializeResult(metadata={"flagged_transactions": 127})
