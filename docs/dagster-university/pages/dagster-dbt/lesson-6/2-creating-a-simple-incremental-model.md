---
title: 'Lesson 6: Creating an incremental model'
module: 'dagster_dbt'
lesson: '6'
---

# Creating an incremental model

As mentioned, partitions don’t *replace* incremental models, but you’ll soon see how you can expand their functionality by partitioning them. In fact, we’ll first write an incremental dbt model and then show you how to use Dagster to partition it.

This model will be a series of stats about all New York taxi trips. It would be expensive to compute this every day because of the granularity of the metrics and the fact that some of the measures are computationally expensive to calculate. Therefore, this model will be incremental.

In your dbt project, create a new file called `daily_metrics.sql`  in the `analytics/models/marts` directory. Copy and paste the following code into the file:

```sql
{{
  config(
    materialized='incremental',
    unique_key='date_of_business'
  )
}}

with
    trips as (
        select *
        from {{ ref('stg_trips') }}
    ),
    daily_summary as (
        select
            date_trunc('day', pickup_datetime) as date_of_business,
            count(*) as trip_count,
            sum(duration) as total_duration,
            sum(duration) / count(*) as average_duration,
            sum(total_amount) as total_amount,
            sum(total_amount) / count(*) as average_amount,
            sum(case when duration > 30 then 1 else 0 end) / count(*) as pct_over_30_min
        from trips
        group by all
    )
select *
from daily_summary
{% if is_incremental() %}
    where date_of_business > (select max(date_of_business) from {{ this }})
{% endif %}
```

This is a standard incremental model that we won’t spend a lot of time going over, but let’s cover the incremental logic here:

```jsx
{% if is_incremental() %}
    where date_of_business > (select max(date_of_business) from {{ this }})
{% endif %}
```

This `where`  clause is the most common way to define incremental logic. It’s also one of the biggest reasons for the model’s brittleness. 

What we’d like to do is partition this model and tell dbt to insert only the records that match that partition. For example, if we're running the Dagster partition range of `01/01/24` to`01/22/24`, then dbt should only select and insert records for that date range. Soon, we’ll update this clause to do exactly that!