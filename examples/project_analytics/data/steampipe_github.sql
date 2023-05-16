select
    full_name,
    forks_count,
    stargazers_count,
    subscribers_count,
    watchers_count
from github_repository
where full_name in (
    'dagster-io/dagster',
    'apache/airflow'
)
;