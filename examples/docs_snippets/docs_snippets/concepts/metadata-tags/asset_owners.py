from dagster import asset


@asset(owners=["richard.hendricks@hooli.com", "team:data-eng"])
def leads(): ...
