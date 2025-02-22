from dagster import job, asset

@asset(metadata={"location": "us-west1"})
def asset_us_west1():
    return "Data from US West 1"

@asset(metadata={"location": "europe-west1"})
def asset_europe_west1():
    return "Data from Europe West 1"

@asset(metadata={"location": "asia-southeast2"})
def asset_asia_southeast2():
    return "Data from Asia Southeast 2"

@job
def custom_pipeline():
    asset_us_west1()
    asset_europe_west1()
    asset_asia_southeast2()