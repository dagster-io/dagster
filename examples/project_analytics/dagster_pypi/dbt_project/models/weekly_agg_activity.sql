with joined as (
    select * from {{ref('base_joined')}}
),

weekly as (

    select

    {{ date_trunc("week", "download_date") }} as download_day,
    project_name,
    sum(file_downloads_count) as total_file_downloads,
    max(project_version) as last_project_version,
    max(forks_count) as max_forks_count,
    max(stargazers_count) as max_stargazers_count,
    max(watchers_count) as max_watchers_count,
    max(subscribers_count) as max_subscribers_count

    from joined
    group by 1,2
)

select * from weekly
