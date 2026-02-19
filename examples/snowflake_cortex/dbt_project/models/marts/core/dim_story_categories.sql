{{ config(materialized='table') }}

with enriched as (
    select * from {{ ref('int_story_enrichment') }}
),

categories as (
    select distinct
        story_category as category_name,
        case
            when story_category in ('technology', 'programming', 'ai_ml', 'devops') then 'Technical'
            when story_category in ('startup', 'business') then 'Business'
            when story_category in ('web_development', 'mobile') then 'Development'
            when story_category = 'security' then 'Security'
            when story_category = 'science' then 'Science'
            else 'Other'
        end as category_group,
        current_timestamp() as dbt_updated_at
    from enriched
    where story_category is not null
)

select * from categories
