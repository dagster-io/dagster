{{ config(materialized='view') }}

with entities as (
    select * from {{ source('raw', 'extracted_entities') }}
),

sentiment as (
    select * from {{ ref('stg_sentiment') }}
),

aggregated as (
    select
        date(sent.posted_at) as story_date,
        sent.story_category,
        sent.sentiment_classification,
        count(*) as story_count,
        count(distinct e.job_id) as stories_with_entities,
        count(case when e.company_names is not null and e.company_names != '' then 1 end) as stories_with_companies,
        count(case when e.required_skills is not null and e.required_skills != '' then 1 end) as stories_with_skills,
        count(case when e.compensation_info is not null and e.compensation_info != '' then 1 end) as stories_with_compensation
    from sentiment sent
    left join entities e on sent.story_id = e.job_id
    group by
        date(sent.posted_at),
        sent.story_category,
        sent.sentiment_classification
)

select * from aggregated
