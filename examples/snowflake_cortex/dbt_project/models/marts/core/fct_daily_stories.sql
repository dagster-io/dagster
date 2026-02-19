{{ config(
    materialized='table',
    unique_key='story_date',
    on_schema_change='append_new_columns'
) }}

with enriched as (
    select * from {{ ref('int_story_enrichment') }}
),

daily_facts as (
    select
        story_date,
        count(*) as total_stories,
        count(distinct story_id) as unique_stories,
        count(distinct author) as unique_authors,
        count(case when is_de_story then 1 end) as data_engineering_stories,
        count(case when sentiment_classification = 'positive' then 1 end) as positive_stories,
        count(case when sentiment_classification = 'neutral' then 1 end) as neutral_stories,
        count(case when sentiment_classification = 'negative' then 1 end) as negative_stories,
        count(distinct story_category) as unique_categories,
        avg(length(coalesce(description, title))) as avg_content_length,
        current_timestamp() as dbt_updated_at
    from enriched
    group by story_date
)

select * from daily_facts
