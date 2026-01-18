{{ config(materialized='view') }}

with stories as (
    select * from {{ ref('stg_stories') }}
),

sentiment as (
    select * from {{ ref('stg_sentiment') }}
),

enriched as (
    select
        s.story_id,
        s.title,
        s.description,
        s.url,
        s.author,
        s.posted_at,
        s.source_system,
        s.dbt_loaded_at,
        -- Sentiment fields
        sent.sentiment_classification,
        sent.story_category,
        sent.is_data_engineering,
        sent.analyzed_at as sentiment_analyzed_at,
        -- Derived fields
        case
            when sent.is_data_engineering = 'data_engineering' then true
            else false
        end as is_de_story,
        date(s.posted_at) as story_date
    from stories s
    left join sentiment sent on s.story_id = sent.story_id
)

select * from enriched
