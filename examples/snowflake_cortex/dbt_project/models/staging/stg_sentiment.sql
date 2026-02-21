{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'story_sentiment') }}
),

renamed as (
    select
        job_id as story_id,
        title,
        description,
        url,
        posted_by as author,
        posted_at,
        sentiment_classification,
        story_category,
        is_data_engineering,
        analyzed_at,
        current_timestamp() as dbt_loaded_at
    from source
)

select * from renamed
