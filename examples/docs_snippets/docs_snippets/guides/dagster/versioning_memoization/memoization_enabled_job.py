from dagster import job, SourceHashVersionStrategy


@job(version_strategy=SourceHashVersionStrategy())
def the_job():
    ...