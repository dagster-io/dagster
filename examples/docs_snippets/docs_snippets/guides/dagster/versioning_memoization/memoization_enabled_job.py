from dagster import SourceHashVersionStrategy, job


@job(version_strategy=SourceHashVersionStrategy())
def the_job():
    ...
