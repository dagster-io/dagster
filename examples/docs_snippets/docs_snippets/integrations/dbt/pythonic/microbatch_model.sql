{{ config(
    materialized='incremental',
    incremental_strategy='microbatch',
    event_time='event_time',
    batch_size='day',
    begin='2023-01-01'
) }}

select
    event_id,
    event_time,
    user_id,
    event_type
from {{ source('app', 'events') }}
