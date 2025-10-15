"""Simplified Multi-Partition Solution - Specifically for GitHub Issue #28915.
"""

from datetime import datetime

import pandas as pd
from dagster import (
    AssetExecutionContext,
    Backoff,
    DailyPartitionsDefinition,
    Definitions,
    MetadataValue,
    MonthlyPartitionsDefinition,
    RetryPolicy,
    asset,
    define_asset_job,
)

# ===============================
# 🔑 Core Solution: Shared Business Logic
# ===============================

class DataRecordProcessor:
    """Core data processor - This is the code you want to reuse!
    
    This class encapsulates your core business logic, avoiding code duplication.
    Different assets can use the same processing logic but apply different partition strategies.
    """
    
    @staticmethod
    def fetch_and_process_data(
        context: AssetExecutionContext,
        date_fields: list[str],
        partition_date: str,
        processing_mode: str = "default"
    ) -> pd.DataFrame:
        """Unified data fetching and processing logic.
        
        Args:
            context: Dagster execution context
            date_fields: List of date fields to process (e.g., ['last_updated'] or ['date_created', 'last_updated'])
            partition_date: Partition date
            processing_mode: Processing mode ('daily_update' or 'monthly_backfill')
        
        Returns:
            Processed DataFrame
        """
        context.log.info("Starting data processing...")
        context.log.info(f"Partition date: {partition_date}")
        context.log.info(f"Date fields: {date_fields}")
        context.log.info(f"Processing mode: {processing_mode}")
        
        try:
            # Validate inputs
            if not date_fields:
                raise ValueError("date_fields cannot be empty")
            if not partition_date:
                raise ValueError("partition_date cannot be empty")
                
            context.log.info("Input validation passed")
            
            # This is your core business logic - write it only once!
            # In real projects, this might include:
            # - Database queries
            # - API calls
            # - Data transformations
            # - Business rule applications
            
            # Adjust data volume based on processing mode (simulate different processing strategies)
            if processing_mode == "daily_update":
                # Daily incremental updates - less data
                num_records = 100
                context.log.info("Executing daily incremental update")
            elif processing_mode == "monthly_backfill":
                # Monthly backfill - more data
                num_records = 2000
                context.log.info("Executing monthly full backfill")
            else:
                num_records = 500
            
            # Simulate data generation (in real applications, this is your data fetching logic)
            data = {
                'record_id': range(1, num_records + 1),
                'business_value': [i * 10 for i in range(1, num_records + 1)],
                'date_created': pd.date_range('2024-01-01', periods=num_records, freq='H'),
                'last_updated': pd.date_range('2024-01-01', periods=num_records, freq='H'),
                'partition_date': [partition_date] * num_records,
                'processed_fields': [','.join(date_fields)] * num_records,
                'processing_mode': [processing_mode] * num_records,
            }
            
            df = pd.DataFrame(data)
            
            # Add processing statistics with proper MetadataValue types
            memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            context.add_output_metadata({
                'Records processed': MetadataValue.int(len(df)),
                'Partition date': MetadataValue.text(partition_date),
                'Processed fields': MetadataValue.text(', '.join(date_fields)),
                'Processing mode': MetadataValue.text(processing_mode),
                'Memory usage (MB)': MetadataValue.float(round(memory_usage_mb, 2)),
                'Data shape': MetadataValue.text(f"{df.shape[0]} rows x {df.shape[1]} columns"),
                'Processing timestamp': MetadataValue.text(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            })
            
            context.log.info(f"Successfully processed {len(df)} records")
            return df
            
        except Exception as e:
            context.log.error(f"Error processing data: {e!s}")
            # Log additional context for debugging
            context.log.error(f"Failed partition: {partition_date}")
            context.log.error(f"Failed mode: {processing_mode}")
            raise  # Re-raise the exception to trigger retry policy

# ===============================
# 🎯 Solution: Separate Asset Definitions
# ===============================

@asset(
    name="data_record_daily_updates",
    partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
    group_name="data_processing",
    description="Daily data updates - incremental processing based on last_updated field",
    compute_kind="python",
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=1,
        backoff=Backoff.EXPONENTIAL
    ),
    metadata={
        "owner": "data_team",
        "sla_minutes": 30,
        "criticality": "medium"
    }
)
def data_record_daily_updates(context: AssetExecutionContext) -> pd.DataFrame:
    """Daily data update asset.
    
    Corresponds to your original issue:
    - Uses last_updated field
    - Daily incremental processing
    - cron="0 0 * * *"
    """
    return DataRecordProcessor.fetch_and_process_data(
        context=context,
        date_fields=["last_updated"],  # Only focus on last_updated
        partition_date=context.partition_key,
        processing_mode="daily_update"
    )

@asset(
    name="data_record_monthly_backfill",
    partitions_def=MonthlyPartitionsDefinition(start_date="2024-01-01"),
    group_name="data_processing", 
    description="Monthly data backfill - complete processing based on date_created and last_updated fields",
    compute_kind="python",
    retry_policy=RetryPolicy(
        max_retries=2,
        delay=5,
        backoff=Backoff.LINEAR  # Linear backoff for longer-running processes
    ),
    metadata={
        "owner": "data_team",
        "sla_minutes": 120,  # Longer SLA for backfill operations
        "criticality": "high"
    }
)
def data_record_monthly_backfill(context: AssetExecutionContext) -> pd.DataFrame:
    """Monthly data backfill asset.
    
    Corresponds to your original issue:
    - Uses date_created and last_updated fields
    - Monthly complete backfill
    - cron="0 0 1 * *"
    """
    return DataRecordProcessor.fetch_and_process_data(
        context=context,
        date_fields=["date_created", "last_updated"],  # Focus on two date fields
        partition_date=context.partition_key,
        processing_mode="monthly_backfill"
    )

# ===============================
# 📋 Job Definitions
# ===============================

# Corresponds to your original data_updates_job
daily_updates_job = define_asset_job(
    name="data_updates_job",
    selection=[data_record_daily_updates],
    description="🔄 Daily data update job - runs incremental updates daily"
)

# Corresponds to your original data_fillup_job  
monthly_backfill_job = define_asset_job(
    name="data_fillup_job",
    selection=[data_record_monthly_backfill],
    description="📋 Monthly backfill job - runs complete backfill monthly"
)

# ===============================
# 🎛️ Dagster Definitions
# ===============================

defs = Definitions(
    assets=[
        data_record_daily_updates,
        data_record_monthly_backfill,
    ],
    jobs=[
        daily_updates_job,
        monthly_backfill_job,
    ]
)

# ===============================
# 📖 Solution Documentation
# ===============================

"""
This solution perfectly solves the problem described in GitHub Issue #28915!

ORIGINAL PROBLEM:
- A single asset cannot support multiple partition definitions
- Had to duplicate asset code to support different partition strategies
- Got error: "Executable asset has a different partitions definition than the one specified for the job"

OUR SOLUTION:
1. Code reuse: DataRecordProcessor.fetch_and_process_data() contains all core business logic
2. Clear separation: Two assets handle different use cases separately
3. Flexible configuration: Control processing behavior through parameters
4. Native partitioning: Each asset uses appropriate partition strategy
5. Robust error handling: Proper exception handling and retry policies
6. Rich metadata: Structured metadata with proper MetadataValue types

HOW TO USE:

1. Run Dagster UI:
   dagster dev -f simple_multi_partition_solution.py

2. View assets:
   - data_record_daily_updates: Daily incremental updates
   - data_record_monthly_backfill: Monthly complete backfill

3. Run jobs:
   - data_updates_job: Corresponds to your daily update needs
   - data_fillup_job: Corresponds to your backfill needs

CORE ADVANTAGES:
- Avoid code duplication through shared business logic
- Support different partition strategies natively
- Clear separation of responsibilities
- Robust error handling with retry policies
- Rich metadata and monitoring capabilities
- Easy to test and maintain
- Follows Dagster best practices from ops documentation

ENHANCED FEATURES (based on Dagster ops documentation):
- RetryPolicy with exponential/linear backoff
- Structured metadata using MetadataValue types
- Comprehensive error handling and logging
- Asset-level metadata for ownership and SLA tracking
- Input validation and error context

This solution allows you to:
- Maintain a single source of business logic
- Create specialized assets for different use cases
- Avoid complex multi-partition definitions
- Get better maintainability and observability
- Handle failures gracefully with automatic retries

Problem solved!
"""
