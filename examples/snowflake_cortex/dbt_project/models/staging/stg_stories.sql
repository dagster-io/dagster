{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'stories') }}
),

renamed as (
    select
        job_id as story_id,
        title,
        description,
        url,
        posted_by as author,
        posted_at,
        source,
        processed_at,
        -- Add metadata
        'hackernews' as source_system,
        current_timestamp() as dbt_loaded_at
    from source
)

select * from renamed
