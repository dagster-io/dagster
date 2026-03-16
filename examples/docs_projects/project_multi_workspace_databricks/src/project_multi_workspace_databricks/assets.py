"""Core assets for the multi-workspace Databricks demo.

This module defines assets for:
- Kafka event ingestion (ERP/CRM events like invoices, balances)
- Fivetran SaaS integrations
- Data processing and enrichment
"""

import dagster as dg

# ============================================================================
# KAFKA INGESTION ASSETS
# ============================================================================


# start_kafka_assets
@dg.asset(
    kinds={"kafka", "raw_data"},
    group_name="ingestion",
)
def raw_erp_events(context: dg.AssetExecutionContext) -> None:
    """Raw ERP events ingested from Kafka (invoices, orders, payments).

    Consumes event-based data from Kafka topics populated by ERP systems.
    Events include invoice creation, payment processing, and order updates.
    """
    # This is a placeholder - actual execution happens via the Kafka sensor
    # The sensor triggers runs that populate this asset
    pass


@dg.asset(
    kinds={"kafka", "raw_data"},
    group_name="ingestion",
)
def raw_crm_events(context: dg.AssetExecutionContext) -> None:
    """Raw CRM events ingested from Kafka (customer interactions, balances).

    Consumes event-based data from Kafka topics populated by CRM systems.
    Events include customer balance updates, support interactions, and account changes.
    """
    pass


# end_kafka_assets


@dg.op(
    config_schema={
        "batch_data": dg.Field(
            list,
            description="Batch of messages consumed from Kafka",
        ),
        "max_offset": dg.Field(
            int,
            description="Maximum offset in the batch",
        ),
    }
)
def process_kafka_events(context: dg.OpExecutionContext) -> None:
    """Process a batch of Kafka events.

    This op is triggered by the Kafka sensor and processes incoming events.
    """
    batch_data = context.op_config["batch_data"]
    max_offset = context.op_config["max_offset"]

    context.log.info(f"Processing {len(batch_data)} events (max_offset={max_offset})")

    for event in batch_data:
        context.log.info(f"Event: {event}")


# ============================================================================
# FIVETRAN SAAS INTEGRATIONS
# ============================================================================


@dg.asset(
    kinds={"fivetran", "saas"},
    group_name="ingestion",
)
def salesforce_data(context: dg.AssetExecutionContext) -> None:
    """Salesforce data synced via Fivetran.

    Includes accounts, opportunities, contacts, and leads from Salesforce CRM.
    """
    pass


@dg.asset(
    kinds={"fivetran", "saas"},
    group_name="ingestion",
)
def hubspot_data(context: dg.AssetExecutionContext) -> None:
    """HubSpot marketing and sales data synced via Fivetran.

    Includes marketing campaigns, email engagement, and lead scoring data.
    """
    pass


# ============================================================================
# DATABRICKS UNITY CATALOG FEDERATION
# ============================================================================


@dg.asset(
    kinds={"databricks", "sql_server"},
    group_name="legacy_data",
    deps=[],
)
def legacy_customer_data(context: dg.AssetExecutionContext) -> None:
    """Legacy customer data accessed via Databricks Lakehouse Federation.

    Connects to on-premise SQL Server databases through Unity Catalog federation.
    Contains historical customer records and legacy system data.
    """
    pass


@dg.asset(
    kinds={"databricks", "postgres"},
    group_name="legacy_data",
    deps=[],
)
def legacy_transaction_data(context: dg.AssetExecutionContext) -> None:
    """Legacy transaction data accessed via Databricks Lakehouse Federation.

    Connects to PostgreSQL databases through Unity Catalog federation.
    Contains historical transaction records and financial data.
    """
    pass


# ============================================================================
# DATA TRANSFORMATION & ENRICHMENT
# ============================================================================


@dg.asset(
    kinds={"databricks", "transformation"},
    group_name="transformation",
    deps=[raw_erp_events, raw_crm_events, legacy_customer_data],
)
def enriched_customer_profiles(context: dg.AssetExecutionContext) -> None:
    """Enriched customer profiles combining real-time events and legacy data.

    Joins Kafka event streams with legacy customer data to create comprehensive
    customer profiles including balance history, transaction patterns, and interactions.
    """
    pass


@dg.asset(
    kinds={"databricks", "transformation"},
    group_name="transformation",
    deps=[raw_erp_events, legacy_transaction_data, salesforce_data],
)
def order_fulfillment_status(context: dg.AssetExecutionContext) -> None:
    """Order fulfillment tracking combining ERP events and Salesforce data.

    Processes invoice and order events from Kafka and enriches with Salesforce
    opportunity data to track end-to-end order fulfillment across systems.
    """
    pass


# ============================================================================
# ANALYTICS & AGGREGATIONS
# ============================================================================


@dg.asset(
    kinds={"databricks", "analytics"},
    group_name="analytics",
    deps=[enriched_customer_profiles, order_fulfillment_status],
)
def customer_360_view(context: dg.AssetExecutionContext) -> None:
    """Complete 360-degree customer view for business intelligence.

    Aggregates data from all sources to provide a unified view of customer
    activity, preferences, transaction history, and predictive insights.

    Used by business intelligence tools and customer-facing applications.
    """
    pass


@dg.asset(
    kinds={"databricks", "analytics"},
    group_name="analytics",
    deps=[enriched_customer_profiles, hubspot_data],
)
def marketing_attribution(context: dg.AssetExecutionContext) -> None:
    """Marketing attribution model combining customer data and campaign performance.

    Links customer transactions and behavior to marketing touchpoints from HubSpot
    to measure campaign effectiveness and ROI.
    """
    pass
