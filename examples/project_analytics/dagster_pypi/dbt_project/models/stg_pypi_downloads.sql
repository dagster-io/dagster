with base as (
select * from {{source('dagster_pypi', 'pypi_downloads')}}
)


select

download_date,
project_name,
project_version,
file_downloads_count

from base
