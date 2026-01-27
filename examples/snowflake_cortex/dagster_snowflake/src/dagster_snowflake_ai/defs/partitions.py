"""Partition definitions for Dagster.

Partitions enable incremental processing by dividing data into time-based chunks.
This allows Dagster to:
- Process only new data for each partition
- Retry failed partitions independently
- Track data freshness per partition
- Optimize warehouse costs by processing smaller chunks

Usage with Resources:
- Use context.partition_key to get the current partition date
- Filter SQL queries by partition date for incremental processing
- Use MERGE statements to handle updates and inserts efficiently
"""

import dagster as dg

# Daily partitions starting from 2024-01-01
# Format: YYYY-MM-DD (e.g., "2024-01-15")
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")

# Example: Weekly partitions for reporting (optional)
# weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2024-01-01")
