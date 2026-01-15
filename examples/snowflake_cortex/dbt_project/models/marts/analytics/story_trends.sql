{{ config(materialized='table') }}

with daily_facts as (
    select * from {{ ref('fct_daily_stories') }}
),

entity_aggregates as (
    select * from {{ ref('int_entity_aggregates') }}
),

trends as (
    select
        df.story_date,
        df.total_stories,
        df.data_engineering_stories,
        df.positive_stories,
        df.neutral_stories,
        df.negative_stories,
        df.unique_authors,
        df.avg_content_length,
        -- Entity trends
        sum(ea.stories_with_entities) as stories_with_entities,
        sum(ea.stories_with_companies) as stories_with_companies,
        sum(ea.stories_with_skills) as stories_with_skills,
        -- Calculate trends (7-day moving average)
        avg(df.total_stories) over (
            order by df.story_date
            rows between 6 preceding and current row
        ) as avg_stories_7d,
        -- Calculate growth rate
        lag(df.total_stories) over (order by df.story_date) as prev_day_stories,
        case
            when lag(df.total_stories) over (order by df.story_date) > 0
            then (df.total_stories - lag(df.total_stories) over (order by df.story_date))::float
                 / lag(df.total_stories) over (order by df.story_date) * 100
            else null
        end as day_over_day_growth_pct,
        current_timestamp() as dbt_updated_at
    from daily_facts df
    left join entity_aggregates ea on df.story_date = ea.story_date
    group by
        df.story_date,
        df.total_stories,
        df.data_engineering_stories,
        df.positive_stories,
        df.neutral_stories,
        df.negative_stories,
        df.unique_authors,
        df.avg_content_length
)

select * from trends
