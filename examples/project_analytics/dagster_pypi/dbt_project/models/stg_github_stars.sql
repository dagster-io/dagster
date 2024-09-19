with base as (
    select * from {{source('dagster_pypi', 'github_stars')}}
)

select


full_name,

{{ dbt.split_part(string_text='full_name', delimiter_text="'/'", part_number=1) }} as owner,
{{ dbt.split_part(string_text='full_name', delimiter_text="'/'", part_number=2) }} as repo_name,
forks_count,
stargazers_count,
watchers_count,
subscribers_count,
cast(date as timestamp) as snapshot_date


from base


