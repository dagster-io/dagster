with github as (
    select * from {{ref('stg_github_stars')}}
),

pypi as (
    select * from {{ref('stg_pypi_downloads')}}
),

joined as (
    select

    github.owner,
    github.repo_name,
    github.forks_count,
    github.stargazers_count,
    github.watchers_count,
    github.subscribers_count,
    github.snapshot_date as github_snapshot_date,

    pypi.download_date,
    pypi.project_name,
    pypi.project_version,
    pypi.project_name
        ||'-'|| {{ dbt.split_part(string_text='project_name', delimiter_text="'.'", part_number=0) }}
        ||'-'|| {{ dbt.split_part(string_text='project_name', delimiter_text="'.'", part_number=1) }} as project_name_version,
    pypi.file_downloads_count


    from github
    left join pypi
        on github.repo_name = pypi.project_name
        and pypi.download_date = github.snapshot_date
)

select * from joined
